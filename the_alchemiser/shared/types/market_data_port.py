"""Business Unit: shared | Status: current.

Domain port for market data access.

This port defines the minimal contract strategies need for accessing market data
from various providers (live trading, backtesting, etc.). It follows the hexagonal
architecture pattern, allowing different adapters to implement the same interface.

Example Usage:
    >>> from the_alchemiser.shared.value_objects.symbol import Symbol
    >>> # Implementation provided by dependency injection
    >>> port: MarketDataPort = get_market_data_port()
    >>>
    >>> # Fetch historical bars
    >>> symbol = Symbol("AAPL")
    >>> bars = port.get_bars(symbol, period="1Y", timeframe="1Day")
    >>>
    >>> # Get latest quote
    >>> quote = port.get_latest_quote(symbol)
    >>> if quote:
    >>>     print(f"Bid: {quote.bid}, Ask: {quote.ask}")
    >>>
    >>> # Get current mid price
    >>> mid = port.get_mid_price(symbol)
    >>> if mid:
    >>>     print(f"Mid price: {mid}")

Known Implementations:
    - MarketDataService: Production implementation using Alpaca API
    - HistoricalMarketDataPort: Backtesting implementation using stored data

Note:
    This port currently uses the "legacy" QuoteModel from shared.types.quote.
    Migration to the enhanced QuoteModel in shared.types.market_data is planned
    to support bid_size/ask_size for improved spread calculations.

"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from the_alchemiser.shared.types.market_data import BarModel
from the_alchemiser.shared.types.quote import QuoteModel
from the_alchemiser.shared.value_objects.symbol import Symbol


@runtime_checkable
class MarketDataPort(Protocol):
    """Domain port for accessing market data providers.

    Provides a minimal interface used by strategy engines to fetch
    historical bars and current quotes via a shared abstraction.

    This is a Protocol (structural subtyping) allowing any class that
    implements these methods to be used as a MarketDataPort without
    explicit inheritance.

    Error Handling Contract:
        - Methods return None when data is unavailable (e.g., market closed, no quote)
        - Methods may raise exceptions for:
            * Invalid input (ValueError)
            * Network/API errors (transient failures should be retried by implementation)
            * Configuration errors (misconfigured credentials, etc.)
        - Implementations should log errors with appropriate context

    Idempotency:
        - All methods are idempotent - repeated calls with same parameters
          should return equivalent data (subject to market data updates)
        - No side effects beyond caching (implementations may cache responses)

    Performance:
        - Implementations should handle rate limiting
        - Batch operations preferred when fetching multiple symbols
        - Network timeouts should be bounded (implementation-specific)
    """

    def get_bars(self, symbol: Symbol, period: str, timeframe: str) -> list[BarModel]:
        """Fetch historical bars for a symbol.

        Args:
            symbol: Trading symbol (e.g., Symbol("AAPL"))
            period: Lookback period as string (e.g., "1Y" = 1 year, "6M" = 6 months,
                   "90D" = 90 days). Format: <number><unit> where unit is Y/M/D.
            timeframe: Bar interval as string (e.g., "1Day", "1Hour", "15Min").
                      Common values: "1Day", "1Hour", "15Min", "5Min", "1Min"

        Returns:
            List of BarModel objects, ordered chronologically (oldest first).
            Returns empty list if no data available for the period.

        Raises:
            ValueError: If symbol, period, or timeframe format is invalid
            DataProviderError: If market data provider fails after retries
            ConfigurationError: If provider is not configured correctly

        Example:
            >>> symbol = Symbol("AAPL")
            >>> bars = port.get_bars(symbol, period="1Y", timeframe="1Day")
            >>> if bars:
            >>>     print(f"Got {len(bars)} daily bars for {symbol}")
            >>>     latest = bars[-1]
            >>>     print(f"Latest close: {latest.close}")

        Note:
            period/timeframe are kept as strings to avoid broad refactors.
            Future enhancement: use typed Period and Timeframe enums.

        """
        ...

    def get_latest_quote(self, symbol: Symbol) -> QuoteModel | None:
        """Get the latest bid/ask quote for a symbol.

        Fetches the most recent bid and ask prices available from the market
        data provider. Returns None if no quote is available (e.g., market
        closed, symbol not found, or pre-market/after-hours with no quotes).

        Args:
            symbol: Trading symbol to get quote for

        Returns:
            QuoteModel with bid/ask prices, or None if unavailable.
            QuoteModel has fields: ts (timestamp), bid (Decimal), ask (Decimal)

        Raises:
            ValueError: If symbol is invalid
            DataProviderError: If provider fails after retries

        Example:
            >>> symbol = Symbol("AAPL")
            >>> quote = port.get_latest_quote(symbol)
            >>> if quote:
            >>>     spread = quote.ask - quote.bid
            >>>     mid = quote.mid  # Uses @property
            >>>     print(f"Bid: {quote.bid}, Ask: {quote.ask}, Mid: {mid}")
            >>> else:
            >>>     print("No quote available")

        Note:
            Currently uses legacy QuoteModel from shared.types.quote.
            Migration to enhanced QuoteModel (with bid_size/ask_size) planned.

        """
        ...

    def get_mid_price(self, symbol: Symbol) -> float | None:
        """Get current mid price derived from the latest quote.

        Calculates the mid-point price between bid and ask from the most
        recent quote. Returns None if no quote is available.

        This is a convenience method equivalent to:
            quote = get_latest_quote(symbol)
            mid = quote.mid if quote else None

        Args:
            symbol: Trading symbol to get mid price for

        Returns:
            Mid price as float, or None if no quote available

        Raises:
            ValueError: If symbol is invalid
            DataProviderError: If provider fails after retries

        Example:
            >>> symbol = Symbol("AAPL")
            >>> mid_price = port.get_mid_price(symbol)
            >>> if mid_price:
            >>>     print(f"Current mid price: ${mid_price:.2f}")

        Note:
            Returns float (not Decimal) for backward compatibility.
            Precision suitable for trading decisions but not financial accounting.

        """
        ...
