"""Business Unit: shared | Status: current.."""

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
        settings_cls: Any,
        init_settings: Any,
        env_settings: Any,
        dotenv_settings: Any,
        file_secret_settings: Any,
    ) -> tuple[Any, ...]:
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
