"""Business Unit: utilities; Status: current.

Configuration providers for dependency injection.
"""

from __future__ import annotations

from dependency_injector import containers, providers

from the_alchemiser.infrastructure.config import load_settings
from the_alchemiser.infrastructure.secrets.secrets_manager import SecretsManager


class ConfigProviders(containers.DeclarativeContainer):
    """Providers for configuration management."""

    # Settings configuration
    settings = providers.Singleton(load_settings)

    # Trading mode: derive from Settings by default, but allow runtime overrides
    paper_trading = providers.Factory(
        lambda settings: settings.alpaca.paper_trading, settings=settings
    )

    # Secrets manager
    _secrets_manager = providers.Factory(SecretsManager)

    # Credentials based on current trading mode
    _alpaca_credentials = providers.Factory(
        lambda secrets_manager, paper: secrets_manager.get_alpaca_keys(paper_trading=paper),
        secrets_manager=_secrets_manager,
        paper=paper_trading,
    )

    alpaca_api_key = providers.Factory(lambda creds: creds[0], creds=_alpaca_credentials)
    alpaca_secret_key = providers.Factory(lambda creds: creds[1], creds=_alpaca_credentials)

    # Email configuration
    email_recipient = providers.Factory(lambda settings: settings.email.to_email, settings=settings)
