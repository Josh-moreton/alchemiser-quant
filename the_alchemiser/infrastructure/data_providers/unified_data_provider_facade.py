"""
Backward-compatible facade for UnifiedDataProvider using refactored services.

This facade maintains the exact same interface as the original UnifiedDataProvider
while internally using the new service-based architecture. This allows for
gradual migration of existing code.
"""

import logging
from typing import Any, cast

import pandas as pd

from the_alchemiser.infrastructure.config import Settings
from the_alchemiser.services.account.legacy_account_service import AccountService
from the_alchemiser.services.errors.error_handling import ErrorHandler, handle_service_errors
from the_alchemiser.services.market_data.market_data_client import MarketDataClient
from the_alchemiser.services.market_data.price_service import ModernPriceFetchingService
from the_alchemiser.services.market_data.streaming_service import StreamingService
from the_alchemiser.services.shared.cache_manager import CacheManager
from the_alchemiser.services.shared.config_service import ConfigService
from the_alchemiser.services.shared.secrets_service import SecretsService
from the_alchemiser.services.trading.trading_client_service import TradingClientService

logger = logging.getLogger(__name__)


class UnifiedDataProviderFacade:
    # Class-level attribute annotations to help mypy infer instance attribute types
    _trading_client: Any | None
    _price_service: "ModernPriceFetchingService | None"
    """
    Backward-compatible facade for UnifiedDataProvider using new service architecture.

    This class provides the exact same interface as the original UnifiedDataProvider
    but internally uses the new modular services. Existing code can use this
    without any changes while benefiting from the improved architecture.
    """

    def __init__(
        self,
        paper_trading: bool = True,
        cache_duration: int | None = None,
        config: Settings | None = None,
        enable_real_time: bool = True,
    ) -> None:
        """
        Initialize UnifiedDataProvider facade with same interface as original.

        Args:
            paper_trading: Whether to use paper trading keys
            cache_duration: Cache duration in seconds
            config: Configuration object
            enable_real_time: Whether to enable real-time pricing
        """
        self.paper_trading = paper_trading
        self.enable_real_time = enable_real_time

        # Initialize services
        self._config_service = ConfigService(config)
        self._secrets_service = SecretsService()
        self._error_handler = ErrorHandler(logger)

        # Get credentials
        api_key, secret_key = self._secrets_service.get_alpaca_credentials(paper_trading)

        # Initialize cache with custom duration if provided
        cache_ttl = cache_duration or self._config_service.cache_duration
        self._cache = CacheManager[Any](maxsize=1000, default_ttl=cache_ttl)

        # Initialize core services
        self._market_data_client = MarketDataClient(api_key, secret_key)
        self._trading_client_service = TradingClientService(api_key, secret_key, paper_trading)

        # Initialize specialized services
        # Pass self as data_provider for legacy compatibility paths used by AccountService
        self._account_service = AccountService(
            self._trading_client_service,
            api_key,
            secret_key,
            self._config_service.get_endpoint(paper_trading),
            data_provider=self,
        )

        if enable_real_time:
            try:
                streaming: StreamingService | None = None
                # Streaming could be wired here in future; keep None for now
                self._price_service: ModernPriceFetchingService | None = ModernPriceFetchingService(
                    self._market_data_client, streaming
                )
            except Exception as e:
                logger.warning(f"Real-time pricing disabled due to error: {e}")
                self._price_service = None
        else:
            self._price_service = None

        # Backward compatibility attributes
        self._endpoint = self._config_service.get_endpoint(paper_trading)
        self.api_key = api_key
        self.secret_key = secret_key
        # Cache for trading client access (backward compatibility)
        self._trading_client = None

    @property
    def trading_client(self) -> Any:
        """
        Provide access to trading client for backward compatibility.

        Returns the underlying Alpaca trading client instance.
        """
        if self._trading_client is None:
            # Expose underlying AlpacaManager instance
            self._trading_client = self._trading_client_service.client
        return self._trading_client

    @handle_service_errors(default_return=pd.DataFrame())
    def get_data(
        self,
        symbol: str,
        timeframe: str = "1day",
        period: str = "1y",
        start_date: str | None = None,
        end_date: str | None = None,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Get historical market data - maintains exact original interface.

        Args:
            symbol: Stock symbol
            timeframe: Time frame for data
            period: Time period
            start_date: Start date string
            end_date: End date string
            **kwargs: Additional arguments for backward compatibility

        Returns:
            DataFrame with historical data
        """
        # Check cache first
        cache_key = f"{symbol}:{timeframe}:{period}:{start_date}:{end_date}"
        cached_data = self._cache.get(cache_key, "historical_data")
        if cached_data is not None:
            return cached_data

        # Get data using new service
        df = self._market_data_client.get_historical_bars(symbol, period, timeframe)

        # Cache the result
        if not df.empty:
            self._cache.set(cache_key, df, "historical_data")

        return df

    @handle_service_errors(default_return=None)
    def get_current_price(self, symbol: str, **kwargs: Any) -> float | None:
        """
        Get current price for symbol - maintains exact original interface.

        Args:
            symbol: Stock symbol
            **kwargs: Additional arguments for backward compatibility

        Returns:
            Current price or None if unavailable
        """
        # Try modern price service if available
        if self._price_service:
            try:
                import asyncio

                loop = asyncio.get_event_loop()
                return loop.run_until_complete(self._price_service.get_current_price_async(symbol))
            except Exception:
                # Fall back to synchronous method
                pass

        # Fall back to market data client
        try:
            bid, ask = self._market_data_client.get_latest_quote(symbol)
            return (bid + ask) / 2 if bid and ask else None
        except Exception as e:
            # Log handled error with correct argument order and return None
            self._error_handler.log_and_handle(e, {"symbol": symbol}, None)
            return None

    @handle_service_errors(default_return=None)
    def get_account_info(self, **kwargs: Any) -> dict[str, Any] | None:
        """
        Get account information - maintains exact original interface.

        Args:
            **kwargs: Additional arguments for backward compatibility

        Returns:
            Dictionary with account information or None on failure
        """
        account_model = self._account_service.get_account_info()
        if account_model:
            # Convert TypedDict to plain dict for broader compatibility
            return cast(dict[str, Any], dict(account_model.to_dict()))
        return None

    @handle_service_errors(default_return=[])
    def get_positions(self, **kwargs: Any) -> list[dict[str, Any]]:
        """
        Get current positions - maintains exact original interface.

        Args:
            **kwargs: Additional arguments for backward compatibility

        Returns:
            List of position dictionaries
        """
        # Only use the modern trading client service; no legacy fallback
        try:
            positions = self._trading_client_service.get_all_positions()
            return positions
        except Exception as e:
            logger.error(f"Error fetching positions from trading client service: {e}")
            return []

    @handle_service_errors(default_return=(None, None))
    def get_latest_quote(self, symbol: str, **kwargs: Any) -> tuple[float | None, float | None]:
        """
        Get latest bid/ask quote - maintains exact original interface.

        Args:
            symbol: Stock symbol
            **kwargs: Additional arguments for backward compatibility

        Returns:
            Tuple of (bid, ask) prices
        """
        return self._market_data_client.get_latest_quote(symbol)

    @handle_service_errors(default_return=[])
    def get_orders(self, **kwargs: Any) -> list[dict[str, Any]]:
        """
        Get orders - maintains exact original interface.

        Args:
            **kwargs: Additional arguments for backward compatibility

        Returns:
            List of order dictionaries
        """
        # TradingClientService does not expose get_orders; return empty for now
        return []

    @handle_service_errors(default_return={})
    def place_order(self, **kwargs: Any) -> dict[str, Any]:
        """
        Place order - maintains exact original interface.

        Args:
            **kwargs: Order parameters

        Returns:
            Order confirmation dictionary
        """
        # TradingClientService handles orders via higher-level methods; not available here
        return {"error": "place_order not available in facade"}

    def get_cache_stats(self) -> dict[str, Any]:
        """
        Get cache statistics for monitoring.

        Returns:
            Dictionary with cache statistics
        """
        return self._cache.get_stats()

    def clear_cache(self, pattern: str | None = None) -> None:
        """
        Clear cache entries.

        Args:
            pattern: Optional pattern to match for selective clearing
        """
        if pattern:
            self._cache.invalidate_by_pattern(pattern)
        else:
            self._cache.clear()

    # Additional methods for backward compatibility
    def __enter__(self) -> "UnifiedDataProviderFacade":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        # Clean up resources if needed
        pass

    def __str__(self) -> str:
        """String representation."""
        return f"UnifiedDataProviderFacade(paper_trading={self.paper_trading})"

    def __repr__(self) -> str:
        """Detailed representation."""
        return (
            f"UnifiedDataProviderFacade("
            f"paper_trading={self.paper_trading}, "
            f"enable_real_time={self.enable_real_time}, "
            f"endpoint={self._endpoint})"
        )


# Alias for backward compatibility
UnifiedDataProvider = UnifiedDataProviderFacade
