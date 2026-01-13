"""Business Unit: shared/config; Status: current.

Configuration providers for dependency injection.
"""

from __future__ import annotations

from dependency_injector import containers, providers

from the_alchemiser.shared.config.config import load_settings
from the_alchemiser.shared.config.secrets_adapter import get_alpaca_keys
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


def _safe_get_credential(
    creds: tuple[str, str, str] | tuple[None, None, None], index: int
) -> str | None:
    """Safely extract a credential from the credentials tuple.

    Handles the case where get_alpaca_keys() returns (None, None, None)
    when credentials are not found in the environment.

    Args:
        creds: Tuple of (api_key, secret_key, endpoint) or (None, None, None)
        index: Index of the credential to extract (0=api_key, 1=secret_key, 2=endpoint)

    Returns:
        The credential value or None if not found or empty

    """
    if creds == (None, None, None):
        return None
    return creds[index] or None


def _is_paper_trading(endpoint: str | None) -> bool:
    """Determine if endpoint is for paper trading.

    Args:
        endpoint: Alpaca API endpoint URL

    Returns:
        True if paper trading, False if live trading.
        Defaults to True if endpoint is None.

    """
    if not endpoint:
        return True
    return "paper" in endpoint.lower()


class ConfigProviders(containers.DeclarativeContainer):
    """Providers for configuration management.

    This container provides dependency injection configuration for application settings
    and credentials. All providers are lazy-evaluated and thread-safe.

    Providers:
        settings: Application configuration singleton (Settings)
            - Loaded once from environment variables and .env file
            - Returns: Settings instance with all configuration sections

        paper_trading: Trading mode flag (bool)
            - True for paper trading, False for live trading
            - Determined by checking if endpoint URL contains "paper"
            - Defaults to True if no endpoint is configured

        alpaca_api_key: Alpaca API key (str | None)
            - Returns None if credentials not found in environment
            - Environment variables: ALPACA_KEY or ALPACA__KEY

        alpaca_secret_key: Alpaca secret key (str | None)
            - Returns None if credentials not found in environment
            - Environment variables: ALPACA_SECRET or ALPACA__SECRET

        alpaca_endpoint: Alpaca API endpoint URL (str | None)
            - Returns None if not configured (defaults to paper trading)
            - Environment variables: ALPACA_ENDPOINT or ALPACA__ENDPOINT

        execution: Execution configuration settings (ExecutionSettings)
            - Extracted from settings.execution

    Note:
        Alpaca credentials are loaded from environment variables via get_alpaca_keys().
        If credentials are not found, providers return None and a warning is logged
        by the secrets adapter.

    Example:
        >>> container = ConfigProviders()
        >>> settings = container.settings()
        >>> api_key = container.alpaca_api_key()
        >>> is_paper = container.paper_trading()

    """

    # Settings configuration
    settings = providers.Singleton(load_settings)

    # Alpaca credentials (private - use individual providers below)
    _alpaca_credentials = providers.Factory(get_alpaca_keys)

    # Trading mode: determined by endpoint URL
    paper_trading = providers.Factory(
        lambda creds: _is_paper_trading(_safe_get_credential(creds, 2)),
        creds=_alpaca_credentials,
    )

    # Individual credential providers with safe extraction
    alpaca_api_key = providers.Factory(
        lambda creds: _safe_get_credential(creds, 0), creds=_alpaca_credentials
    )
    alpaca_secret_key = providers.Factory(
        lambda creds: _safe_get_credential(creds, 1), creds=_alpaca_credentials
    )
    alpaca_endpoint = providers.Factory(
        lambda creds: _safe_get_credential(creds, 2), creds=_alpaca_credentials
    )

    # Execution configuration
    execution = providers.Factory(lambda settings: settings.execution, settings=settings)
