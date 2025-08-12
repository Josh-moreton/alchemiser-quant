"""Configuration providers for dependency injection."""

from dependency_injector import containers, providers

from the_alchemiser.infrastructure.config import load_settings


class ConfigProviders(containers.DeclarativeContainer):
    """Providers for configuration management."""

    # Settings configuration
    settings = providers.Singleton(load_settings)

    # Alpaca configuration - use factory providers that call settings
    alpaca_api_key = providers.Factory(lambda settings: settings.alpaca.api_key, settings=settings)

    alpaca_secret_key = providers.Factory(
        lambda settings: settings.alpaca.secret_key, settings=settings
    )

    paper_trading = providers.Factory(
        lambda settings: settings.alpaca.paper_trading, settings=settings
    )

    # Email configuration
    email_recipient = providers.Factory(
        lambda settings: settings.email.recipient, settings=settings
    )
