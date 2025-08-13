"""Configuration providers for dependency injection."""

from dependency_injector import containers, providers

from the_alchemiser.infrastructure.config import load_settings
from the_alchemiser.infrastructure.secrets.secrets_manager import SecretsManager


def get_alpaca_api_key() -> str:
    """Get Alpaca API key from Secrets Manager."""
    secrets_manager = SecretsManager()
    # Default to paper trading for DI mode for safety
    api_key, _ = secrets_manager.get_alpaca_keys(paper_trading=True)
    if not api_key:
        raise ValueError("Failed to retrieve Alpaca API key from Secrets Manager")
    return api_key


def get_alpaca_secret_key() -> str:
    """Get Alpaca secret key from Secrets Manager."""
    secrets_manager = SecretsManager()
    # Default to paper trading for DI mode for safety
    _, secret_key = secrets_manager.get_alpaca_keys(paper_trading=True)
    if not secret_key:
        raise ValueError("Failed to retrieve Alpaca secret key from Secrets Manager")
    return secret_key


class ConfigProviders(containers.DeclarativeContainer):
    """Providers for configuration management."""

    # Settings configuration
    settings = providers.Singleton(load_settings)

    # Alpaca configuration - use factory providers that call SecretsManager
    alpaca_api_key = providers.Factory(get_alpaca_api_key)
    alpaca_secret_key = providers.Factory(get_alpaca_secret_key)

    paper_trading = providers.Factory(
        lambda settings: True, settings=settings  # Always use paper trading for DI mode for now
    )

    # Email configuration
    email_recipient = providers.Factory(lambda settings: settings.email.to_email, settings=settings)
