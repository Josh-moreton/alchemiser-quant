from __future__ import annotations

"""Typed configuration loader for The Alchemiser."""

from pathlib import Path
import os
import yaml
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
        default_factory=lambda: {"nuclear": 0.4, "tecl": 0.6}
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


class Settings(BaseSettings):
    """Application settings loaded from YAML and environment."""

    logging: LoggingSettings = LoggingSettings()
    alpaca: AlpacaSettings = AlpacaSettings()
    aws: AwsSettings = AwsSettings()
    alerts: AlertsSettings = AlertsSettings()
    secrets_manager: SecretsManagerSettings = SecretsManagerSettings()
    strategy: StrategySettings = StrategySettings()
    email: EmailSettings = EmailSettings()
    data: DataSettings = DataSettings()
    tracking: TrackingSettings = TrackingSettings()

    model_config = SettingsConfigDict(env_nested_delimiter="__", env_prefix="")

    def __getitem__(self, key: str):
        value = getattr(self, key)
        if isinstance(value, BaseModel):
            return value.model_dump()
        return value

    def get(self, key: str, default=None):
        return self[key] if hasattr(self, key) else default

    def __contains__(self, key: str) -> bool:
        return hasattr(self, key)


class Config(Settings):
    """Backward compatible alias for Settings."""
    pass


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[1] / "config.yaml"


def load_settings(config_path: str | os.PathLike | None = None) -> Settings:
    """Load settings from YAML and environment variables."""
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    yaml_data = {}
    if path.exists():
        with path.open("r") as f:
            parsed = yaml.safe_load(f) or {}
            if isinstance(parsed, dict):
                yaml_data = parsed

    # Environment variables have precedence
    yaml_settings = Settings.model_validate(yaml_data)
    env_settings = Settings()
    merged = yaml_settings.model_dump()
    merged.update(env_settings.model_dump(exclude_unset=True))
    return Settings.model_validate(merged)


# Backwards compatible helper
get_config = load_settings
