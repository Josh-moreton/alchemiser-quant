#!/usr/bin/env python3
"""Business Unit: shared; Status: current.

Configuration Service.

Handles loading and managing configuration for the trading system.
Provides a clean interface for accessing configuration settings.
"""

from __future__ import annotations

from the_alchemiser.shared.config.config import Settings, load_settings
from the_alchemiser.shared.errors.exceptions import ConfigurationError
from the_alchemiser.shared.logging import get_logger

# Default cache duration for market data (1 hour)
DEFAULT_CACHE_DURATION_SECONDS = 3600

logger = get_logger(__name__)


class ConfigService:
    """Service for loading and managing configuration.

    This service provides a clean facade over the Settings object, offering:
    - Lazy loading of configuration via load_settings()
    - Validated property access with clear error messages
    - Read-only access to prevent accidental mutations
    - Structured logging for configuration operations

    Public API:
        config: Settings - Get the underlying Settings object
        cache_duration: int - Get validated cache duration in seconds (>0)
        paper_endpoint: str - Get Alpaca paper trading endpoint URL
        live_endpoint: str - Get Alpaca live trading endpoint URL
        get_endpoint(paper_trading: bool) -> str - Get appropriate endpoint for trading mode

    Example:
        >>> service = ConfigService()
        >>> endpoint = service.get_endpoint(paper_trading=True)
        >>> cache_ttl = service.cache_duration  # Guaranteed positive

    Raises:
        ConfigurationError: If configuration is invalid or missing required keys

    """

    def __init__(self, config: Settings | None = None) -> None:
        """Initialize configuration service.

        Args:
            config: Optional configuration object. If None, loads from global config
                   via load_settings(). Accepts explicit config for testing or
                   dependency injection scenarios.

        Raises:
            ConfigurationError: If configuration fails to load

        Post-conditions:
            - self._config is guaranteed to be a valid Settings object
            - Configuration source is logged for audit trail

        """
        if config is None:
            logger.info("Loading configuration from environment")
            config = load_settings()
            if config is None:  # Should never happen but defensive check
                raise ConfigurationError("Failed to load configuration from environment")
            logger.info("Configuration loaded successfully from environment")
        else:
            logger.debug("Using explicitly provided configuration")

        self._config = config

    @property
    def config(self) -> Settings:
        """Get the configuration object.

        Returns:
            Settings: The underlying Pydantic Settings object containing all
                     configuration sections (alpaca, data, strategy, etc.)

        Post-conditions:
            - Returns the same Settings instance on every call (immutable)

        """
        return self._config

    @property
    def cache_duration(self) -> int:
        """Get cache duration in seconds.

        Returns:
            int: Cache duration in seconds, guaranteed to be positive.
                 Returns configured value or DEFAULT_CACHE_DURATION_SECONDS (3600)
                 if not configured or set to 0/None.

        Raises:
            ConfigurationError: If cache_duration is explicitly set to a negative value

        Post-conditions:
            - Return value is always > 0
            - Default of 3600 (1 hour) used for None/0 values

        """
        cache_duration = self._config.data.cache_duration or DEFAULT_CACHE_DURATION_SECONDS

        if cache_duration <= 0:
            logger.error(
                "Invalid cache_duration configuration",
                cache_duration=cache_duration,
                config_key="data.cache_duration",
            )
            raise ConfigurationError(
                "cache_duration must be positive",
                config_key="data.cache_duration",
                config_value=cache_duration,
            )

        return cache_duration

    @property
    def paper_endpoint(self) -> str:
        """Get Alpaca paper trading endpoint.

        Returns:
            str: Alpaca paper trading API endpoint URL (includes protocol and domain)

        Raises:
            ConfigurationError: If alpaca.paper_endpoint is missing or not a valid URL

        Post-conditions:
            - URL starts with 'http://' or 'https://'

        """
        try:
            endpoint = self._config.alpaca.paper_endpoint
        except AttributeError as e:
            logger.error("Missing Alpaca paper endpoint configuration", exc_info=True)
            raise ConfigurationError(
                "Missing Alpaca configuration: paper_endpoint",
                config_key="alpaca.paper_endpoint",
            ) from e

        if not endpoint or not endpoint.startswith("http"):
            logger.error(
                "Invalid paper endpoint URL",
                endpoint=endpoint,
                config_key="alpaca.paper_endpoint",
            )
            raise ConfigurationError(
                "Invalid paper endpoint URL: must start with http:// or https://",
                config_key="alpaca.paper_endpoint",
                config_value=endpoint,
            )

        return endpoint

    @property
    def live_endpoint(self) -> str:
        """Get Alpaca live trading endpoint.

        Returns:
            str: Alpaca live trading API endpoint URL (includes protocol and domain)

        Raises:
            ConfigurationError: If alpaca.endpoint is missing or not a valid URL

        Post-conditions:
            - URL starts with 'http://' or 'https://'

        """
        try:
            endpoint = self._config.alpaca.endpoint
        except AttributeError as e:
            logger.error("Missing Alpaca live endpoint configuration", exc_info=True)
            raise ConfigurationError(
                "Missing Alpaca configuration: endpoint",
                config_key="alpaca.endpoint",
            ) from e

        if not endpoint or not endpoint.startswith("http"):
            logger.error(
                "Invalid live endpoint URL",
                endpoint=endpoint,
                config_key="alpaca.endpoint",
            )
            raise ConfigurationError(
                "Invalid live endpoint URL: must start with http:// or https://",
                config_key="alpaca.endpoint",
                config_value=endpoint,
            )

        return endpoint

    def get_endpoint(self, *, paper_trading: bool) -> str:
        """Get the appropriate endpoint for the trading mode.

        Args:
            paper_trading: Whether using paper trading mode. Must be keyword-only
                          to prevent accidental boolean trap errors.

        Returns:
            str: Appropriate Alpaca API endpoint URL (paper or live)

        Raises:
            ConfigurationError: If the selected endpoint is missing or invalid

        Pre-conditions:
            - paper_trading must be explicitly provided as keyword argument

        Post-conditions:
            - Returns validated URL starting with 'http://' or 'https://'

        Example:
            >>> service = ConfigService()
            >>> paper_url = service.get_endpoint(paper_trading=True)
            >>> live_url = service.get_endpoint(paper_trading=False)

        """
        return self.paper_endpoint if paper_trading else self.live_endpoint
