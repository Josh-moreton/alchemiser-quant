"""
Typed Data Provider Adapter

This adapter provides backward-compatible access to market data using the typed
MarketDataService while maintaining the same interface as UnifiedDataProvider.

This allows strategies to use the typed market data port without requiring
changes to their implementation.
"""

import logging
from typing import Any

import pandas as pd

from the_alchemiser.infrastructure.config import Settings
from the_alchemiser.services.errors.error_handling import handle_service_errors
from the_alchemiser.services.market_data.market_data_service import MarketDataService
from the_alchemiser.services.repository.alpaca_manager import AlpacaManager

logger = logging.getLogger(__name__)


class TypedDataProviderAdapter:
    """
    Adapter that provides UnifiedDataProvider interface using typed MarketDataService.

    This adapter bridges the gap between legacy strategy engines expecting a simple
    get_data() interface and the new typed market data services.
    """

    def __init__(self, paper_trading: bool = True, config: Settings | None = None):
        """
        Initialize the typed data provider adapter.

        Args:
            paper_trading: Whether to use paper trading environment
            config: Optional configuration settings
        """
        self.logger = logging.getLogger(__name__)
        self._paper_trading = paper_trading

        if config is None:
            from the_alchemiser.infrastructure.config import load_settings

            config = load_settings()

        # Initialize the core repository implementation
        self._alpaca_manager = AlpacaManager(
            config.alpaca.api_key,
            config.alpaca.secret_key,
            paper_trading,
        )

        # Initialize typed market data service
        self._market_data_service = MarketDataService(
            self._alpaca_manager,
            cache_ttl_seconds=5,
            enable_validation=True,
        )

        self.logger.info(f"TypedDataProviderAdapter initialized with paper={paper_trading}")

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
        Get historical market data using typed services.

        Args:
            symbol: Stock symbol
            timeframe: Time frame for data (default: "1day")
            period: Time period (default: "1y")
            start_date: Start date string (optional)
            end_date: End date string (optional)
            **kwargs: Additional arguments for backward compatibility

        Returns:
            DataFrame with historical data matching UnifiedDataProvider format
        """
        try:
            # Use the underlying market data client through the repository
            # This maintains the pandas DataFrame format expected by strategies
            df = self._alpaca_manager.get_historical_bars(symbol, period, timeframe)

            if not df.empty:
                self.logger.debug(
                    f"TypedDataProviderAdapter: fetched {len(df)} bars for {symbol} "
                    f"(period={period}, timeframe={timeframe})"
                )
            else:
                self.logger.warning(f"TypedDataProviderAdapter: no data returned for {symbol}")

            return df

        except Exception as e:
            self.logger.error(
                f"TypedDataProviderAdapter: failed to fetch data for {symbol}: "
                f"{type(e).__name__}: {e}"
            )
            # Return empty DataFrame to maintain compatibility
            return pd.DataFrame()

    @handle_service_errors(default_return=None)
    def get_current_price(self, symbol: str, **kwargs: Any) -> float | None:
        """
        Get current price using typed service.

        Args:
            symbol: Stock symbol
            **kwargs: Additional arguments for backward compatibility

        Returns:
            Current price, or None if not available
        """
        return self._market_data_service.get_validated_price(symbol)

    @handle_service_errors(default_return=(None, None))
    def get_latest_quote(self, symbol: str, **kwargs: Any) -> tuple[float | None, float | None]:
        """
        Get latest bid/ask quote using typed service.

        Args:
            symbol: Stock symbol
            **kwargs: Additional arguments for backward compatibility

        Returns:
            Tuple of (bid, ask) prices, or (None, None) if not available
        """
        try:
            quote = self._alpaca_manager.get_latest_quote(symbol)
            return quote if quote else (None, None)
        except Exception as e:
            self.logger.error(f"Failed to get quote for {symbol}: {e}")
            return (None, None)

    @handle_service_errors(default_return=None)
    def get_account_info(self, **kwargs: Any) -> dict[str, Any] | None:
        """
        Get account information using typed service.

        Args:
            **kwargs: Additional arguments for backward compatibility

        Returns:
            Account information dictionary, or None if not available
        """
        try:
            return self._alpaca_manager.get_account_info()
        except Exception as e:
            self.logger.error(f"Failed to get account info: {e}")
            return None

    @handle_service_errors(default_return=[])
    def get_positions(self, **kwargs: Any) -> list[dict[str, Any]]:
        """
        Get current positions using typed service.

        Args:
            **kwargs: Additional arguments for backward compatibility

        Returns:
            List of position dictionaries
        """
        try:
            return self._alpaca_manager.get_all_positions()
        except Exception as e:
            self.logger.error(f"Failed to get positions: {e}")
            return []

    @handle_service_errors(default_return=[])
    def get_orders(self, **kwargs: Any) -> list[dict[str, Any]]:
        """
        Get orders using typed service.

        Args:
            **kwargs: Additional arguments for backward compatibility

        Returns:
            List of order dictionaries
        """
        try:
            return self._alpaca_manager.get_all_orders()
        except Exception as e:
            self.logger.error(f"Failed to get orders: {e}")
            return []

    # Properties for backward compatibility
    @property
    def data_client(self) -> Any:
        """Access to underlying data client for backward compatibility."""
        return self._alpaca_manager.data_client

    @property
    def api_key(self) -> str:
        """API key for backward compatibility."""
        return self._alpaca_manager.api_key

    @property
    def secret_key(self) -> str:
        """Secret key for backward compatibility."""
        return self._alpaca_manager.secret_key