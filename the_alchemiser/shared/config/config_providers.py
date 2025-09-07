"""Business Unit: utilities; Status: current.

Configuration providers for dependency injection.
"""

from __future__ import annotations

from dependency_injector import containers, providers

from the_alchemiser.shared.config.config import load_settings
from the_alchemiser.shared.config.secrets_adapter import secrets_adapter


class ConfigProviders(containers.DeclarativeContainer):
    """Providers for configuration management."""

    # Settings configuration
    settings = providers.Singleton(load_settings)

    # Trading mode: now derived from secrets adapter stage detection
    paper_trading = providers.Factory(lambda: secrets_adapter.is_paper_trading)

    # Credentials from stage-aware secrets adapter
    _alpaca_credentials = providers.Factory(lambda: secrets_adapter.get_alpaca_keys())

    alpaca_api_key = providers.Factory(lambda creds: creds[0], creds=_alpaca_credentials)
    alpaca_secret_key = providers.Factory(lambda creds: creds[1], creds=_alpaca_credentials)

    # Email configuration
    email_recipient = providers.Factory(lambda settings: settings.email.to_email, settings=settings)
