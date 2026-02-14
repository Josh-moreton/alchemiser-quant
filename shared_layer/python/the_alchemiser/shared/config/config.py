"""Business Unit: utilities; Status: current.

Typed configuration loader for The Alchemiser.

This module provides centralized configuration management via Pydantic BaseSettings,
supporting environment variables, .env files, and per-stage profiles.
"""

from __future__ import annotations

import json
import logging
import os
from importlib import resources as importlib_resources

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from ..constants import DEFAULT_AWS_REGION
from .strategy_profiles import (
    DEV_DSL_ALLOCATIONS,
    DEV_DSL_FILES,
    PROD_DSL_ALLOCATIONS,
    PROD_DSL_FILES,
)


class LoggingSettings(BaseModel):
    """Logging configuration - minimal, as we use CloudWatch Insights filtering.

    All logs are emitted at DEBUG level to CloudWatch. Filter at query time:
        fields @timestamp, level, event
        | filter level in ["info", "warning", "error"]
    """

    # Placeholder - logging config is now handled by shared.logging module


class MarginSafetyConfig(BaseModel):
    """Margin safety configuration for risk management.

    Professional-grade margin controls to prevent margin calls:

    Margin Utilization:
        margin_utilization = initial_margin / equity * 100

    Maintenance Margin Buffer:
        buffer = (equity - maintenance_margin) / maintenance_margin * 100
        Higher buffer = more safety from margin call

    Example configurations:
        Conservative: max_utilization=50%, min_buffer=50%, max_deployment=120%
        Moderate:     max_utilization=60%, min_buffer=35%, max_deployment=140%
        Aggressive:   max_utilization=75%, min_buffer=25%, max_deployment=150%
    """

    # Maximum margin utilization allowed (initial_margin / equity * 100)
    # At 75%, you're using 75% of your equity as margin
    # Higher = more leverage risk, lower = more conservative
    max_margin_utilization_pct: float = 75.0

    # Warning threshold for margin utilization - triggers alerts
    # When utilization exceeds this, a warning is logged/sent
    margin_warning_threshold_pct: float = 60.0

    # Minimum buffer above maintenance margin required
    # buffer = (equity - maintenance_margin) / maintenance_margin * 100
    # At 10%, you have 10% cushion before margin call
    # Alpaca requires maintenance margin to be met or positions are liquidated
    # Note: With 110% equity deployment, expect ~12% buffer which is safe
    min_maintenance_margin_buffer_pct: float = 10.0

    # Hard cap on equity_deployment_pct regardless of buying power
    # Even if Alpaca gives you 4x buying power, limit leverage exposure
    # 1.5 = max 150% of equity can be deployed
    max_equity_deployment_pct: float = 1.50

    # Whether to use RegT (overnight) buying power vs day-trade buying power
    # True = conservative overnight requirements
    # False = allows higher intraday leverage but positions must be closed same-day
    use_overnight_buying_power: bool = True

    # If True, block trades when margin data is unavailable
    # If False, fall back to cash-only mode when margin data missing
    require_margin_data_for_leverage: bool = True


class AlpacaSettings(BaseModel):
    """Connection settings for the Alpaca trading API."""

    endpoint: str = "https://api.alpaca.markets"
    paper_endpoint: str = "https://paper-api.alpaca.markets/v2"
    paper_trading: bool = True

    # Margin Safety Configuration
    margin_safety: MarginSafetyConfig = Field(default_factory=MarginSafetyConfig)

    # Capital Deployment Configuration
    # ================================
    # equity_deployment_pct: What percentage of portfolio EQUITY to deploy.
    # Equity = net liquidation value = cash + positions market value
    #
    # This is the correct mental model:
    # - You put $10,000 in the account, equity = $10,000
    # - With 0.95 deployment, you deploy $9,500 (keep 5% cash reserve)
    # - With 1.10 deployment, you deploy $11,000 (use 10% margin on top of equity)
    #
    # Values:
    # - 0.95 (95%)  = Keep 5% cash reserve, conservative
    # - 1.00 (100%) = Deploy all equity, no reserve, no margin
    # - 1.10 (110%) = Use margin for 10% extra on top of equity
    # - 1.50 (150%) = Use margin for 50% extra (capped by margin_safety.max_equity_deployment_pct)
    #
    # Safety: The planner validates this against:
    # - margin_safety.max_equity_deployment_pct (hard cap)
    # - margin_safety.max_margin_utilization_pct (utilization limit)
    # - margin_safety.min_maintenance_margin_buffer_pct (margin call prevention)
    # - Available buying_power from Alpaca (actual limit)
    #
    # Set via environment variable: ALPACA__EQUITY_DEPLOYMENT_PCT=1.10
    equity_deployment_pct: float = 1.0  # Default: 100% of equity (no leverage)

    # Legacy aliases for backward compatibility - will be removed in future
    # capital_deployment_pct is the old name for equity_deployment_pct
    capital_deployment_pct: float | None = None
    # If set, overrides with (1.0 - cash_reserve_pct)
    cash_reserve_pct: float | None = None

    slippage_bps: int = 5
    enable_websocket_orders: bool = True
    # Credentials - loaded from environment variables via nested delimiter
    # ALPACA__KEY and ALPACA__SECRET map to alpaca.key and alpaca.secret
    # with env_nested_delimiter="__" in Settings.model_config
    key: str | None = None
    secret: str | None = None

    @property
    def effective_deployment_pct(self) -> float:
        """Get the effective equity deployment percentage.

        Handles backward compatibility with legacy settings.
        Caps at margin_safety.max_equity_deployment_pct.

        Resolution order:
        1. cash_reserve_pct (legacy) -> converts to 1.0 - value
        2. capital_deployment_pct (legacy alias)
        3. equity_deployment_pct (current)

        Returns:
            Deployment multiplier (e.g., 1.10 for 110% of equity)

        """
        raw_pct: float
        if self.cash_reserve_pct is not None:
            # Legacy mode: convert cash_reserve_pct to deployment_pct
            # cash_reserve_pct=0.05 means 95% deployment
            # cash_reserve_pct=-0.10 means 110% deployment
            raw_pct = 1.0 - self.cash_reserve_pct
        elif self.capital_deployment_pct is not None:
            # Legacy alias
            raw_pct = self.capital_deployment_pct
        else:
            raw_pct = self.equity_deployment_pct

        # Cap at safety maximum
        return min(raw_pct, self.margin_safety.max_equity_deployment_pct)

    @property
    def is_leverage_enabled(self) -> bool:
        """Check if leverage mode is enabled (deployment > 100%).

        Returns:
            True if deploying more than 100% of equity

        """
        return self.effective_deployment_pct > 1.0


class AwsSettings(BaseModel):
    """AWS deployment configuration."""

    region: str = DEFAULT_AWS_REGION
    account_id: str = ""
    repo_name: str = ""
    lambda_arn: str = ""
    image_tag: str = "latest"


class AlertsSettings(BaseModel):
    """Settings controlling alert generation and delivery."""

    alert_config_s3: str = ""
    cooldown_minutes: int = 30


class StrategySettings(BaseModel):
    """High level configuration for strategy orchestration."""

    default_strategy_allocations: dict[str, float] = Field(
        default_factory=lambda: {"nuclear": 0.3, "tecl": 0.5, "klm": 0.2}
    )
    # DSL multi-file support
    dsl_files: list[str] = Field(
        default_factory=list, description="List of DSL .clj strategy files"
    )
    dsl_allocations: dict[str, float] = Field(
        default_factory=dict,
        description="Per-DSL-file allocation weights that should sum to ~1.0",
    )
    poll_timeout: int = 30
    poll_interval: float = 2.0

    # ---- Validators to make env var formats robust ----
    @staticmethod
    def _try_parse_json_files(s: str) -> list[str] | None:
        """Try to parse files from JSON string format.

        Args:
            s: JSON string like '["A.clj","B.clj"]'

        Returns:
            Parsed list[str] or None if parsing fails

        """
        if not (s.startswith("[") and s.endswith("]")):
            return None

        try:
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
        except ValueError as exc:  # pragma: no cover - defensive logging
            logging.debug("Failed to parse DSL files as JSON: %s", exc)

        return None

    @staticmethod
    def _parse_csv_files(s: str) -> list[str]:
        """Parse files from CSV format.

        Args:
            s: CSV string like 'A.clj,B.clj' (supports newlines)

        Returns:
            Parsed list[str]

        """
        parts = [p.strip().strip("\"'") for p in s.replace("\n", ",").split(",")]
        return [p for p in parts if p]

    @field_validator("dsl_files", mode="before")
    @classmethod
    def _parse_dsl_files(cls, v: object) -> object:
        r"""Accept list[str] or string formats.

        Supported input when coming from env vars:
        - JSON array string: "[\"A.clj\",\"B.clj\"]"
        - Comma or newline separated string: "A.clj,B.clj" or lines
        Returns a list[str].
        """
        if isinstance(v, list):
            return [str(x) for x in v]

        if isinstance(v, str):
            s = v.strip()
            # Try JSON first, then fall back to CSV
            json_result = cls._try_parse_json_files(s)
            if json_result is not None:
                return json_result
            return cls._parse_csv_files(s)

        return v

    @staticmethod
    def _try_parse_json_allocations(s: str) -> dict[str, float] | None:
        """Try to parse allocations from JSON string format.

        Args:
            s: JSON string like '{"A.clj":0.6,"B.clj":0.4}'

        Returns:
            Parsed dict[str, float] or None if parsing fails

        """
        if not (s.startswith("{") and s.endswith("}")):
            return None

        try:
            parsed = json.loads(s)
            if isinstance(parsed, dict):
                return {str(k): float(vv) for k, vv in parsed.items()}
        except (
            ValueError,
            TypeError,
        ) as exc:  # pragma: no cover - defensive logging
            logging.debug("Failed to parse DSL allocations as JSON: %s", exc)

        return None

    @staticmethod
    def _parse_csv_allocations(s: str) -> dict[str, float]:
        """Parse allocations from CSV key=value format.

        Args:
            s: CSV string like 'A.clj=0.6,B.clj=0.4' (supports newlines)

        Returns:
            Parsed dict[str, float]

        """
        items: dict[str, float] = {}
        for token in s.replace("\n", ",").split(","):
            token = token.strip()
            if not token:
                continue
            if "=" not in token:
                continue

            k, val = token.split("=", 1)
            k = k.strip().strip("\"'")
            try:
                items[k] = float(val.strip())
            except ValueError:
                continue

        return items

    @field_validator("dsl_allocations", mode="before")
    @classmethod
    def _parse_dsl_allocations(cls, v: object) -> object:
        r"""Accept dict[str,float] or string formats.

        Supported input when coming from env vars:
        - JSON object string: "{\"A.clj\":0.6,\"B.clj\":0.4}"
        - CSV pairs: "A.clj=0.6,B.clj=0.4" (also supports newlines)
        Returns a dict[str, float].
        """
        if isinstance(v, dict):
            return {str(k): float(vv) for k, vv in v.items()}

        if isinstance(v, str):
            s = v.strip()
            # Try JSON first, then fall back to CSV
            json_result = cls._try_parse_json_allocations(s)
            if json_result is not None:
                return json_result
            return cls._parse_csv_allocations(s)

        return v

    @staticmethod
    def _load_packaged_strategy_config(
        package: str, filename: str
    ) -> tuple[list[str], dict[str, float]] | None:
        """Load strategy configuration from packaged JSON file.

        Args:
            package: Package name (e.g., 'the_alchemiser.shared.config')
            filename: Config filename (e.g., 'strategy.dev.json')

        Returns:
            Tuple of (files, allocations) or None if loading fails

        """
        try:
            cfg_path = importlib_resources.files(package).joinpath(filename)
            with cfg_path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            files_raw = data.get("files", [])
            allocs_raw = data.get("allocations", {})
            files = [str(x) for x in files_raw] if isinstance(files_raw, list) else []
            allocs = (
                {str(k): float(v) for k, v in allocs_raw.items()}
                if isinstance(allocs_raw, dict)
                else {}
            )

            if files and allocs:
                return files, allocs
            return None
        except (
            json.JSONDecodeError,
            OSError,
        ) as exc:  # pragma: no cover - defensive logging
            logging.debug("Strategy config file load failed (%s): %s", filename, exc)
            return None

    @staticmethod
    def _get_stage_profile() -> tuple[list[str], dict[str, float]]:
        """Get DSL files and allocations for the current stage.

        Resolution order:
        1) Per-stage JSON file bundled with the package (recommended):
           the_alchemiser/shared/config/strategy.<stage>.json
        2) Fallback to in-code defaults (DEV_DSL_* / PROD_DSL_*)

        Returns:
            Tuple of (dsl_files, dsl_allocations) for the environment stage

        """
        stage = (os.getenv("APP__STAGE") or os.getenv("STAGE") or "dev").lower()
        filename = "strategy.prod.json" if stage == "prod" else "strategy.dev.json"
        package = "the_alchemiser.shared.config"

        # Try packaged JSON config first
        result = StrategySettings._load_packaged_strategy_config(package, filename)
        if result is not None:
            return result

        # Fallback to existing in-code profiles
        if stage == "prod":
            return list(PROD_DSL_FILES), dict(PROD_DSL_ALLOCATIONS)
        return list(DEV_DSL_FILES), dict(DEV_DSL_ALLOCATIONS)

    def _derive_files_from_allocations(self) -> None:
        """Derive dsl_files from dsl_allocations keys."""
        self.dsl_files = list(self.dsl_allocations.keys())

    def _derive_allocations_from_files(self) -> None:
        """Create equal-weight allocations from dsl_files."""
        n = len(self.dsl_files) or 1
        w = 1.0 / n
        self.dsl_allocations = dict.fromkeys(self.dsl_files, w)

    @model_validator(mode="after")
    def _apply_env_profile(self) -> StrategySettings:
        """Backfill DSL defaults based on stage iff fields are empty.

        Order of precedence (highest to lowest):
        - Values provided explicitly in env/.env (already parsed above)
        - Stage profile defaults selected by APP__STAGE/Stage env
        - Fallbacks: derive from the other field or equal weights
        """
        if not self.dsl_files and not self.dsl_allocations:
            self.dsl_files, self.dsl_allocations = self._get_stage_profile()
        elif not self.dsl_files and self.dsl_allocations:
            self._derive_files_from_allocations()
        elif self.dsl_files and not self.dsl_allocations:
            self._derive_allocations_from_files()
        return self


class DataSettings(BaseModel):
    """Data provider tuning parameters."""

    cache_duration: int = 300
    default_symbol: str = "AAPL"


class TrackingSettings(BaseModel):
    """Locations and limits for strategy tracking artefacts.

    Note: Default S3 bucket is 'the-alchemiser-s3' but can be overridden via
    environment variables (TRACKING__S3_BUCKET) for different deployments.
    """

    s3_bucket: str = "the-alchemiser-s3"  # Overrideable via env vars
    strategy_orders_path: str = "strategy_orders/"
    strategy_positions_path: str = "strategy_positions/"
    strategy_pnl_history_path: str = "strategy_pnl_history/"
    order_history_limit: int = 1000


class TradeLedgerSettings(BaseModel):
    """Trade ledger persistence configuration."""

    table_name: str = Field(default="", description="DynamoDB table name for trade ledger storage")


class RebalancePlanSettings(BaseModel):
    """Rebalance plan persistence configuration for auditability."""

    table_name: str = Field(
        default="", description="DynamoDB table name for rebalance plan storage"
    )
    ttl_days: int = Field(default=90, description="TTL in days for automatic cleanup")


class ExecutionSettings(BaseModel):
    """Trading execution parameters and safe defaults.

    Note: Slippage uses float for basis points as sub-bp precision is sufficient
    for execution tolerances. Decimal would be excessive for this use case.
    """

    max_slippage_bps: float = 20.0
    aggressive_timeout_seconds: float = 2.5
    max_repegs: int = 2
    enable_premarket_assessment: bool = True
    market_open_fast_execution: bool = True
    tight_spread_threshold: float = 3.0
    wide_spread_threshold: float = 5.0
    leveraged_etf_symbols: list[str] = Field(
        default_factory=lambda: ["TQQQ", "SPXL", "TECL", "UVXY", "LABU", "LABD", "SOXL"]
    )
    high_volume_etfs: list[str] = Field(
        default_factory=lambda: ["SPY", "QQQ", "TLT", "XLF", "XLK", "XLP", "XLY", "VOX"]
    )
    # Control whether partial execution outcomes should be treated as workflow failures
    treat_partial_execution_as_failure: bool = True


class OrchestrationSettings(BaseModel):
    """Orchestration transport configuration."""

    use_http_domain_workflow: bool = False
    strategy_endpoint: str = "http://localhost:8001/signals"
    portfolio_endpoint: str = "http://localhost:8002/rebalance"
    execution_endpoint: str = "http://localhost:8003/executions"
    http_max_retries: int = 3
    http_retry_backoff_seconds: float = 0.5


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    logging: LoggingSettings = LoggingSettings()
    alpaca: AlpacaSettings = AlpacaSettings()
    aws: AwsSettings = AwsSettings()
    alerts: AlertsSettings = AlertsSettings()
    strategy: StrategySettings = StrategySettings()
    orchestration: OrchestrationSettings = OrchestrationSettings()
    data: DataSettings = DataSettings()
    tracking: TrackingSettings = TrackingSettings()
    trade_ledger: TradeLedgerSettings = TradeLedgerSettings()
    rebalance_plan: RebalancePlanSettings = RebalancePlanSettings()
    execution: ExecutionSettings = ExecutionSettings()

    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        _settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Order the precedence of configuration sources."""
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )


def load_settings() -> Settings:
    """Load settings from environment variables and .env file.

    Pydantic BaseSettings automatically handles environment variables with precedence.
    .env values serve as defaults, environment variables override them.
    """
    return Settings()
