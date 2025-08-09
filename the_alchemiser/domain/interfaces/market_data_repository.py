"""
Market Data Repository Interface

This interface defines the contract for all market data operations including
current prices, quotes, historical data, and streaming data.

This interface is designed to match our current AlpacaManager and data provider
usage patterns while providing the abstraction needed for the eventual architecture.
"""

from typing import Any, Protocol


class MarketDataRepository(Protocol):
    """
    Protocol defining market data operations interface.

    This interface abstracts all market data operations, allowing us to
    swap implementations (Alpaca, other data providers, mocks for testing)
    without changing dependent code.

    Designed to be compatible with current usage patterns while providing
    the foundation for our eventual infrastructure layer.
    """

    def get_current_price(self, symbol: str) -> float | None:
        """
        Get current price for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Current price, or None if not available.
        """
        ...

    def get_latest_quote(self, symbol: str) -> tuple[float, float] | None:
        """
        Get latest bid/ask quote for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Tuple of (bid, ask) prices, or None if not available.
        """
        ...

    def get_historical_bars(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        timeframe: str = "1Day",
    ) -> list[dict[str, Any]]:
        """
        Get historical price bars.

        Args:
            symbol: Stock symbol
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            timeframe: Bar timeframe (e.g., "1Day", "1Hour")

        Returns:
            List of price bar dictionaries.
        """
        ...

    def get_asset_info(self, symbol: str) -> dict[str, Any] | None:
        """
        Get asset information.

        Args:
            symbol: Stock symbol

        Returns:
            Asset information dictionary, or None if not found.
        """
        ...

    def is_market_open(self) -> bool:
        """
        Check if the market is currently open.

        Returns:
            True if market is open, False otherwise.
        """
        ...

    def get_market_calendar(self, start_date: str, end_date: str) -> list[dict[str, Any]]:
        """
        Get market calendar information.

        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)

        Returns:
            List of market calendar entries.
        """
        ...

    def validate_connection(self) -> bool:
        """
        Validate connection to market data service.

        Returns:
            True if connection is valid, False otherwise.
        """
        ...

    @property
    def data_client(self) -> Any:
        """
        Access to underlying data client for backward compatibility.

        Note: This property is for backward compatibility during migration.
        Eventually, this should be removed as dependent code migrates to
        use the interface methods directly.

        Returns:
            Underlying data client instance.
        """
        ...
