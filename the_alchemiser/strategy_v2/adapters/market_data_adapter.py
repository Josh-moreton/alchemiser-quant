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
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.market_bar import MarketBar
from the_alchemiser.shared.services.market_data_service import MarketDataService

from ..errors import MarketDataError

logger = get_logger(__name__)

# Component identifier for logging
_COMPONENT = "strategy_v2.adapters.market_data_adapter"


class MarketDataProvider(Protocol):
    """Protocol for market data providers."""

    def get_bars(
        self,
        symbols: list[str],
        timeframe: str,
        lookback_days: int,
        end_date: datetime | None = None,
    ) -> dict[str, list[MarketBar]]:
        """Get historical bars for multiple symbols."""
        ...

    def get_current_prices(self, symbols: list[str]) -> dict[str, float]:
        """Get current prices for multiple symbols."""
        ...


class StrategyMarketDataAdapter:
    """Market data adapter for strategy execution.

    Wraps shared.brokers.AlpacaManager with strategy-specific interface
    optimized for batched data fetching and strategy consumption patterns.
    """

    def __init__(self, alpaca_manager: AlpacaManager) -> None:
        """Initialize adapter with AlpacaManager instance.

        Args:
            alpaca_manager: Configured AlpacaManager instance

        """
        self._alpaca = alpaca_manager

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
            symbols: List of symbols to fetch data for
            timeframe: Timeframe string (1D, 1H, 15Min, etc.)
            lookback_days: Number of days to look back (must be > 0)
            end_date: Optional end date (defaults to current UTC time)

        Returns:
            Dictionary mapping symbols to their bar data.
            Returns empty list for symbols with no data.

        Raises:
            MarketDataError: If input validation fails or API call fails critically

        Note:
            Optimized for batched fetching to minimize API calls.
            Returns empty list for symbols with no data rather than failing.
            All timestamps are UTC timezone-aware.

        """
        if not symbols:
            return {}

        # Validate input parameters
        if lookback_days <= 0:
            raise MarketDataError(
                f"Invalid lookback_days: {lookback_days}, must be positive"
            )

        if not timeframe or not timeframe.strip():
            raise MarketDataError("Timeframe cannot be empty")

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
                    except (ValueError, KeyError, TypeError) as e:
                        logger.warning(
                            "Failed to convert bar data for symbol",
                            extra={
                                "component": _COMPONENT,
                                "symbol": symbol,
                                "error": str(e),
                            },
                        )
                        continue

                result[symbol] = typed_bars
                logger.debug(
                    f"Fetched {len(typed_bars)} bars for {symbol} "
                    f"({timeframe}, {lookback_days}d lookback)",
                    extra={
                        "component": _COMPONENT,
                        "symbol": symbol,
                        "bar_count": len(typed_bars),
                        "timeframe": timeframe,
                        "lookback_days": lookback_days,
                    },
                )
            except MarketDataError:
                # Re-raise typed errors without wrapping
                raise
            except Exception as e:
                logger.warning(
                    "Failed to fetch bars for symbol",
                    extra={
                        "component": _COMPONENT,
                        "symbol": symbol,
                        "error": str(e),
                    },
                )
                result[symbol] = []

        return result

    def get_current_prices(self, symbols: list[str]) -> dict[str, float]:
        """Get current prices for multiple symbols.

        Args:
            symbols: List of symbols to get prices for

        Returns:
            Dictionary mapping symbols to their current prices

        Raises:
            MarketDataError: If quote data is unavailable or API call fails

        Note:
            Uses quote data and calculates mid-price using Decimal arithmetic
            for financial precision. Converts to float for return compatibility.

        """
        if not symbols:
            return {}

        result: dict[str, float] = {}

        for symbol in symbols:
            try:
                quote = self._market_data_service.get_quote(symbol)
                if quote and "ask_price" in quote and "bid_price" in quote:
                    # Use Decimal for precise financial arithmetic
                    bid = Decimal(str(quote["bid_price"]))
                    ask = Decimal(str(quote["ask_price"]))

                    if bid <= 0 or ask <= 0:
                        raise MarketDataError(
                            f"Invalid quote prices for {symbol}: bid={bid}, ask={ask}",
                            symbol=symbol,
                        )

                    # Calculate mid price with Decimal precision
                    mid_price_decimal = (bid + ask) / Decimal("2")
                    # Convert to float for return type compatibility
                    mid_price = float(mid_price_decimal)

                    result[symbol] = mid_price
                    logger.debug(
                        "Current price fetched for symbol",
                        extra={
                            "component": _COMPONENT,
                            "symbol": symbol,
                            "mid_price": mid_price,
                            "bid": float(bid),
                            "ask": float(ask),
                        },
                    )
                else:
                    logger.warning(
                        "Quote data missing required fields for symbol",
                        extra={
                            "component": _COMPONENT,
                            "symbol": symbol,
                            "quote_keys": list(quote.keys()) if quote else None,
                        },
                    )
                    raise MarketDataError(
                        f"Incomplete quote data for {symbol}: missing bid or ask price",
                        symbol=symbol,
                    )
            except MarketDataError:
                # Re-raise typed errors
                raise
            except Exception as e:
                logger.error(
                    "Failed to get current price for symbol",
                    extra={
                        "component": _COMPONENT,
                        "symbol": symbol,
                        "error": str(e),
                    },
                )
                raise MarketDataError(
                    f"Failed to get current price for {symbol}: {e}",
                    symbol=symbol,
                ) from e

        return result

    def validate_connection(self) -> bool:
        """Validate connection to market data provider.

        Returns:
            True if connection is working, False otherwise

        Note:
            Swallows exceptions and returns False on failure for compatibility.
            Logs errors with structured logging for observability.

        """
        try:
            return self._alpaca.validate_connection()
        except Exception as e:
            logger.error(
                "Market data connection validation failed",
                extra={
                    "component": _COMPONENT,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            return False
