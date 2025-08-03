from __future__ import annotations

"""Typed configuration loader for The Alchemiser."""

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LoggingSettings(BaseModel):
    level: str = "INFO"


class AlpacaSettings(BaseModel):
    endpoint: str = "https://api.alpaca.markets/v2"
    paper_endpoint: str = "https://paper-api.alpaca.markets/v2"
    cash_reserve_pct: float = 0.05
    slippage_bps: int = 5
    enable_websocket_orders: bool = True


class AwsSettings(BaseModel):
    region: str = "eu-west-2"
    account_id: str = ""
    repo_name: str = ""
    lambda_arn: str = ""
    image_tag: str = "latest"


class AlertsSettings(BaseModel):
    alert_config_s3: str = ""
    cooldown_minutes: int = 30


class SecretsManagerSettings(BaseModel):
    region_name: str = "eu-west-2"
    secret_name: str = "nuclear-secrets"


class StrategySettings(BaseModel):
    default_strategy_allocations: dict[str, float] = Field(
        default_factory=lambda: {"nuclear": 0.3, "tecl": 0.5, "klm": 0.2}
    )
    poll_timeout: int = 30
    poll_interval: float = 2.0


class EmailSettings(BaseModel):
    smtp_server: str = "smtp.mail.me.com"
    smtp_port: int = 587
    from_email: str | None = None
    to_email: str | None = None
    neutral_mode: bool = True


class DataSettings(BaseModel):
    cache_duration: int = 300
    default_symbol: str = "AAPL"


class TrackingSettings(BaseModel):
    s3_bucket: str = "the-alchemiser-s3"
    strategy_orders_path: str = "strategy_orders/"
    strategy_positions_path: str = "strategy_positions/"
    strategy_pnl_history_path: str = "strategy_pnl_history/"
    order_history_limit: int = 1000


class ExecutionSettings(BaseModel):
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


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

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


def load_settings() -> Settings:
    """Load settings from environment variables and .env file.
    
    Pydantic BaseSettings automatically handles environment variables with precedence.
    .env values serve as defaults, environment variables override them.
    """
    return Settings()
