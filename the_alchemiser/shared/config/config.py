"""Business Unit: utilities; Status: current."""

from __future__ import annotations

import logging
import os

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

"""Typed configuration loader for The Alchemiser."""


class LoggingSettings(BaseModel):
    """Logging configuration options."""

    level: str = "INFO"
    enable_s3_logging: bool = False  # Explicit opt-in for S3 logging
    s3_log_uri: str = ""  # S3 URI for log files when S3 logging is enabled
    console_level: str | None = None
    local_log_file: str | None = None


class AlpacaSettings(BaseModel):
    """Connection settings for the Alpaca trading API."""

    endpoint: str = "https://api.alpaca.markets"
    paper_endpoint: str = "https://paper-api.alpaca.markets/v2"
    paper_trading: bool = True
    cash_reserve_pct: float = (
        0.01  # Default is 1% cash reserve; adjust as needed to avoid buying power issues
    )
    slippage_bps: int = 5
    enable_websocket_orders: bool = True
    # Credentials - typically loaded from .env file or environment variables
    key: str | None = Field(default=None, alias="ALPACA_KEY")
    secret: str | None = Field(default=None, alias="ALPACA_SECRET")


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
        
        import json
        
        try:
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
        except Exception as exc:  # pragma: no cover - defensive logging
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
        
        import json
        
        try:
            parsed = json.loads(s)
            if isinstance(parsed, dict):
                return {str(k): float(vv) for k, vv in parsed.items()}
        except Exception as exc:  # pragma: no cover - defensive logging
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
            if not token or "=" not in token:
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

    @model_validator(mode="after")
    def _apply_env_profile(self) -> StrategySettings:
        """Backfill DSL defaults based on stage iff fields are empty.

        Order of precedence (highest to lowest):
        - Values provided explicitly in env/.env (already parsed above)
        - Stage profile defaults selected by APP__STAGE/Stage env
        - Fallbacks: derive from the other field or equal weights
        """
        if not self.dsl_files and not self.dsl_allocations:
            stage = (os.getenv("APP__STAGE") or os.getenv("STAGE") or "").lower()
            if stage == "prod":
                self.dsl_files = list(PROD_DSL_FILES)
                self.dsl_allocations = dict(PROD_DSL_ALLOCATIONS)
            else:
                self.dsl_files = list(DEV_DSL_FILES)
                self.dsl_allocations = dict(DEV_DSL_ALLOCATIONS)
        elif not self.dsl_files and self.dsl_allocations:
            # Use allocation keys order
            self.dsl_files = list(self.dsl_allocations.keys())
        elif self.dsl_files and not self.dsl_allocations:
            # Equal-weight files
            n = len(self.dsl_files) or 1
            w = 1.0 / n
            self.dsl_allocations = dict.fromkeys(self.dsl_files, w)
        return self


class EmailSettings(BaseModel):
    """SMTP configuration for notification delivery."""

    smtp_server: str = "smtp.mail.me.com"
    smtp_port: int = 587
    from_email: str | None = None
    to_email: str | None = None
    password: str | None = None
    neutral_mode: bool = True


class DataSettings(BaseModel):
    """Data provider tuning parameters."""

    cache_duration: int = 300
    default_symbol: str = "AAPL"


class TrackingSettings(BaseModel):
    """Locations and limits for strategy tracking artefacts."""

    s3_bucket: str = "the-alchemiser-s3"
    strategy_orders_path: str = "strategy_orders/"
    strategy_positions_path: str = "strategy_positions/"
    strategy_pnl_history_path: str = "strategy_pnl_history/"
    order_history_limit: int = 1000


class ExecutionSettings(BaseModel):
    """Trading execution parameters and safe defaults."""

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


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    logging: LoggingSettings = LoggingSettings()
    alpaca: AlpacaSettings = AlpacaSettings()
    aws: AwsSettings = AwsSettings()
    alerts: AlertsSettings = AlertsSettings()
    strategy: StrategySettings = StrategySettings()
    email: EmailSettings = EmailSettings()
    data: DataSettings = DataSettings()
    tracking: TrackingSettings = TrackingSettings()
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
