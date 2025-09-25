"""Business Unit: utilities; Status: current."""

from __future__ import annotations

from pydantic import BaseModel, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

from ..constants import DEFAULT_AWS_REGION

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


class SecretsManagerSettings(BaseModel):
    """Configuration for AWS Secrets Manager access."""

    enabled: bool = True
    region_name: str = DEFAULT_AWS_REGION
    secret_name: str = "the-alchemiser-secrets"  # noqa: S105


class StrategySettings(BaseModel):
    """High level configuration for strategy orchestration."""

    default_strategy_allocations: dict[str, float] = Field(
        default_factory=lambda: {"nuclear": 0.3, "tecl": 0.5, "klm": 0.2}
    )
    # DSL multi-file support
    dsl_files: list[str] = Field(
        default_factory=lambda: ["KLM.clj"],
        description="List of DSL .clj strategy files",
    )
    dsl_allocations: dict[str, float] = Field(
        default_factory=lambda: {"KLM.clj": 1.0},
        description="Per-DSL-file allocation weights that should sum to ~1.0",
    )
    poll_timeout: int = 30
    poll_interval: float = 2.0


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
    # Phase 1: Canonical order executor feature flag (enabled by default for consolidation)
    use_canonical_executor: bool = True
    # Smart execution with liquidity-aware volume analysis (enabled by default)
    enable_smart_execution: bool = True
    # Trade ledger recording for execution tracking and performance attribution
    enable_trade_ledger: bool = False


class Settings(BaseSettings):
    """Application settings loaded from environment variables, .env file, and AWS Secrets Manager."""

    logging: LoggingSettings = LoggingSettings()
    alpaca: AlpacaSettings = AlpacaSettings()
    aws: AwsSettings = AwsSettings()
    alerts: AlertsSettings = AlertsSettings()
    secrets_manager: SecretsManagerSettings = SecretsManagerSettings()
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
