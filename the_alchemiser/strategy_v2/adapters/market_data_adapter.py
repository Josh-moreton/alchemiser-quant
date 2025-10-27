#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Market data adapter for strategy execution.

Provides a thin wrapper around shared.brokers.AlpacaManager for strategy
consumption with batched data fetching and strategy-specific interface.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Protocol

from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.errors import (
    DataProviderError,
    MarketDataError,
    SymbolValidationError,
    TimeframeValidationError,
    ValidationError,
)
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.market_bar import MarketBar
from the_alchemiser.shared.services.market_data_service import MarketDataService

logger = get_logger(__name__)

# Component identifier for logging
_COMPONENT = "strategy_v2.adapters.market_data_adapter"


class MarketDataProvider(Protocol):
    """Protocol for market data providers.

    Defines the interface that market data adapters must implement for
    strategy consumption. Ensures type safety and testability through
    dependency inversion.
    """

    def get_bars(
        self,
        symbols: list[str],
        timeframe: str,
        lookback_days: int,
        end_date: datetime | None = None,
    ) -> dict[str, list[MarketBar]]:
        """Get historical bars for multiple symbols.

        Args:
            symbols: List of trading symbols
            timeframe: Bar timeframe (1D, 1H, etc.)
            lookback_days: Days of historical data
            end_date: Optional end date (defaults to now)

        Returns:
            Dictionary mapping symbols to their bar data

        """
        ...

    def get_current_prices(self, symbols: list[str]) -> dict[str, Decimal | None]:
        """Get current prices for multiple symbols.

        Args:
            symbols: List of trading symbols

        Returns:
            Dictionary mapping symbols to their current prices.
            None value indicates price unavailable for that symbol.

        """
        ...


class StrategyMarketDataAdapter:
    """Market data adapter for strategy execution.

    Wraps shared.brokers.AlpacaManager with strategy-specific interface
    optimized for batched data fetching and strategy consumption patterns.
    """

    def __init__(
        self,
        alpaca_manager: AlpacaManager,
        correlation_id: str | None = None,
    ) -> None:
        """Initialize adapter with AlpacaManager instance.

        Args:
            alpaca_manager: Configured AlpacaManager instance
            correlation_id: Optional correlation ID for tracing operations across boundaries

        """
        self._alpaca = alpaca_manager
        self._correlation_id = correlation_id

        # Initialize MarketDataService for improved retry logic and consistent market data access
        self._market_data_service = MarketDataService(alpaca_manager)

    def get_bars(
        self,
        symbols: list[str],
        timeframe: str,
        lookback_days: int,
        end_date: datetime | None = None,
    ) -> dict[str, list[MarketBar]]:
        """Get historical bars for multiple symbols.

        Args:
            symbols: List of symbols to fetch data for (max 100 recommended)
            timeframe: Timeframe string (1D, 1H, 15Min, etc.)
            lookback_days: Number of days to look back (must be > 0)
            end_date: Optional end date (defaults to current UTC time)

        Returns:
            Dictionary mapping symbols to their bar data. Empty list for symbols
            with no data available.

        Raises:
            ValueError: If symbols is empty, timeframe is invalid, or lookback_days <= 0
            MarketDataError: If critical data fetch failure occurs

        Note:
            - Optimized for batched fetching to minimize API calls
            - Returns empty list for symbols with no data rather than failing
            - Idempotent: repeated calls with same parameters return same data
            - Tolerates individual symbol failures to maximize data availability

        """
        # Input validation
        if not symbols:
            raise SymbolValidationError("symbols list cannot be empty", reason="Empty symbols list")
        if lookback_days <= 0:
            raise ValidationError(
                f"lookback_days must be > 0, got {lookback_days}",
                field_name="lookback_days",
                value=lookback_days,
            )
        if not timeframe or not timeframe.strip():
            raise TimeframeValidationError("timeframe cannot be empty", timeframe=timeframe)

        if end_date is None:
            end_date = datetime.now(UTC)

        start_date = end_date - timedelta(days=lookback_days)

        # Format dates for Alpaca API
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        result: dict[str, list[MarketBar]] = {}

        # Fetch data for each symbol
        # Note: Could be optimized for batch requests if Alpaca SDK supports it
        for symbol in symbols:
            try:
                bars = self._market_data_service.get_historical_bars(
                    symbol=symbol,
                    start_date=start_str,
                    end_date=end_str,
                    timeframe=timeframe,
                )

                # Convert legacy bar dictionaries to MarketBar objects
                typed_bars = []
                for bar_dict in bars:
                    try:
                        market_bar = MarketBar.from_alpaca_bar(bar_dict, symbol, timeframe)
                        typed_bars.append(market_bar)
                    except ValueError as e:
                        logger.warning(
                            "Failed to convert bar data",
                            extra={
                                "component": _COMPONENT,
                                "symbol": symbol,
                                "error": str(e),
                                "correlation_id": self._correlation_id,
                            },
                        )
                        continue

                result[symbol] = typed_bars
                logger.debug(
                    f"Fetched {len(typed_bars)} bars for {symbol}",
                    extra={
                        "component": _COMPONENT,
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "lookback_days": lookback_days,
                        "bar_count": len(typed_bars),
                        "correlation_id": self._correlation_id,
                    },
                )
            except (RuntimeError, ValueError) as e:
                # Narrow exception handling - specific errors from market data service
                logger.warning(
                    "Failed to fetch bars",
                    extra={
                        "component": _COMPONENT,
                        "symbol": symbol,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "correlation_id": self._correlation_id,
                    },
                )
                result[symbol] = []
            except Exception as e:
                # Unexpected errors - log and re-raise as domain error
                logger.error(
                    "Unexpected error fetching bars",
                    extra={
                        "component": _COMPONENT,
                        "symbol": symbol,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "correlation_id": self._correlation_id,
                    },
                )
                raise MarketDataError(
                    f"Unexpected error fetching bars for {symbol}: {e}",
                    symbol=symbol,
                    data_type="bars",
                ) from e

        return result

    def get_current_prices(self, symbols: list[str]) -> dict[str, Decimal | None]:
        """Get current prices for multiple symbols.

        Args:
            symbols: List of symbols to get prices for (max 100 recommended)

        Returns:
            Dictionary mapping symbols to their current prices (mid-price between bid/ask).
            None value indicates price is unavailable for that symbol.

        Raises:
            SymbolValidationError: If symbols list is empty
            DataProviderError: If critical API failure occurs affecting all symbols

        Note:
            - Uses quote data mid-price (bid + ask) / 2
            - Returns None for individual symbol failures to maximize availability
            - All prices use Decimal for financial correctness
            - Idempotent: repeated calls return same prices for same market state

        """
        # Input validation
        if not symbols:
            raise SymbolValidationError("symbols list cannot be empty", reason="Empty symbols list")

        result: dict[str, Decimal | None] = {}

        for symbol in symbols:
            try:
                quote = self._market_data_service.get_quote(symbol)
                if quote and "ask_price" in quote and "bid_price" in quote:
                    # Use mid price as current price - CRITICAL: Use Decimal for financial correctness
                    ask_price = Decimal(str(quote["ask_price"]))
                    bid_price = Decimal(str(quote["bid_price"]))

                    # Calculate mid-price using Decimal arithmetic
                    mid_price = (ask_price + bid_price) / Decimal("2")

                    result[symbol] = mid_price
                    logger.debug(
                        "Retrieved current price",
                        extra={
                            "component": _COMPONENT,
                            "symbol": symbol,
                            "mid_price": str(mid_price),
                            "bid": str(bid_price),
                            "ask": str(ask_price),
                            "correlation_id": self._correlation_id,
                        },
                    )
                else:
                    logger.warning(
                        "No quote data available",
                        extra={
                            "component": _COMPONENT,
                            "symbol": symbol,
                            "correlation_id": self._correlation_id,
                        },
                    )
                    result[symbol] = None
            except (RuntimeError, ValueError, KeyError) as e:
                # Narrow exception handling - specific errors from quote fetch
                logger.warning(
                    "Failed to get current price",
                    extra={
                        "component": _COMPONENT,
                        "symbol": symbol,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "correlation_id": self._correlation_id,
                    },
                )
                result[symbol] = None
            except Exception as e:
                # Unexpected errors - log and re-raise as domain error
                logger.error(
                    "Unexpected error fetching price",
                    extra={
                        "component": _COMPONENT,
                        "symbol": symbol,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "correlation_id": self._correlation_id,
                    },
                )
                raise DataProviderError(f"Unexpected error fetching price for {symbol}: {e}") from e

        return result

    def validate_connection(self) -> bool:
        """Validate connection to market data provider.

        Returns:
            True if connection is working, False otherwise

        Raises:
            DataProviderError: If validation encounters critical system error

        Note:
            This is a lightweight health check that should complete quickly.
            Does not guarantee data availability for specific symbols.

        """
        try:
            return self._alpaca.validate_connection()
        except (RuntimeError, ValueError, ConnectionError) as e:
            # Expected connection errors - log and return False
            logger.error(
                "Market data connection validation failed",
                extra={
                    "component": _COMPONENT,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "correlation_id": self._correlation_id,
                },
            )
            return False
        except Exception as e:
            # Unexpected system errors - log and re-raise
            logger.error(
                "Unexpected error during connection validation",
                extra={
                    "component": _COMPONENT,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "correlation_id": self._correlation_id,
                },
            )
            raise DataProviderError(
                f"Unexpected error validating market data connection: {e}"
            ) from e
