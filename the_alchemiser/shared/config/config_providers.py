"""Business Unit: utilities; Status: current.

Configuration providers for dependency injection.
"""

from __future__ import annotations

import os

from dependency_injector import containers, providers

from the_alchemiser.shared.config.config import load_settings
from the_alchemiser.shared.config.secrets_adapter import get_alpaca_keys


class ConfigProviders(containers.DeclarativeContainer):
    """Providers for configuration management."""

    # Settings configuration
    settings = providers.Singleton(load_settings)

    # Trading mode: determined by which credentials are provided
    # Paper trading URLs typically contain "paper" in the endpoint
    _alpaca_credentials = providers.Factory(get_alpaca_keys)
    paper_trading = providers.Factory(
        lambda creds: "paper" in (creds[2] or "").lower() if creds[2] else True,
        creds=_alpaca_credentials
    )

    # Credentials from simple secrets helper
    alpaca_api_key = providers.Factory(lambda creds: creds[0] if creds[0] else None, creds=_alpaca_credentials)
    alpaca_secret_key = providers.Factory(lambda creds: creds[1] if creds[1] else None, creds=_alpaca_credentials)
    alpaca_endpoint = providers.Factory(lambda creds: creds[2] if creds[2] else None, creds=_alpaca_credentials)

    # Email configuration
    email_recipient = providers.Factory(lambda settings: settings.email.to_email, settings=settings)
