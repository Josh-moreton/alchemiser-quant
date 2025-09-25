#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Market data adapter for strategy execution.

Provides a thin wrapper around shared.brokers.AlpacaManager for strategy
consumption with batched data fetching and strategy-specific interface.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Protocol

from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.schemas.market_bar import MarketBarDTO
from the_alchemiser.shared.services.market_data_service import MarketDataService

logger = logging.getLogger(__name__)

# Component identifier for logging
_COMPONENT = "strategy_v2.adapters.market_data_adapter"


class MarketDataProvider(Protocol):
    """Protocol for market data providers."""

    def get_bars(
        self, symbols: list[str], timeframe: str, lookback_days: int
    ) -> dict[str, list[MarketBarDTO]]:
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
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        # Initialize MarketDataService for improved retry logic and consistent market data access
        self._market_data_service = MarketDataService(alpaca_manager)

    def get_bars(
        self,
        symbols: list[str],
        timeframe: str,
        lookback_days: int,
        end_date: datetime | None = None,
    ) -> dict[str, list[MarketBarDTO]]:
        """Get historical bars for multiple symbols.

        Args:
            symbols: List of symbols to fetch data for
            timeframe: Timeframe string (1D, 1H, 15Min, etc.)
            lookback_days: Number of days to look back
            end_date: Optional end date (defaults to current time)

        Returns:
            Dictionary mapping symbols to their bar data

        Note:
            Optimized for batched fetching to minimize API calls.
            Returns empty list for symbols with no data rather than failing.

        """
        if not symbols:
            return {}

        if end_date is None:
            end_date = datetime.now(UTC)

        start_date = end_date - timedelta(days=lookback_days)

        # Format dates for Alpaca API
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        result: dict[str, list[MarketBarDTO]] = {}

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

                # Convert legacy bar dictionaries to MarketBarDTO objects
                typed_bars = []
                for bar_dict in bars:
                    try:
                        bar_dto = MarketBarDTO.from_alpaca_bar(bar_dict, symbol, timeframe)
                        typed_bars.append(bar_dto)
                    except ValueError as e:
                        self._logger.warning(
                            f"Failed to convert bar data for {symbol}: {e}",
                            extra={"component": _COMPONENT},
                        )
                        continue

                result[symbol] = typed_bars
                self._logger.debug(
                    f"Fetched {len(typed_bars)} bars for {symbol} "
                    f"({timeframe}, {lookback_days}d lookback)"
                )
            except Exception as e:
                self._logger.warning(
                    f"Failed to fetch bars for {symbol}: {e}",
                    extra={"component": _COMPONENT},
                )
                result[symbol] = []

        return result

    def get_current_prices(self, symbols: list[str]) -> dict[str, float]:
        """Get current prices for multiple symbols.

        Args:
            symbols: List of symbols to get prices for

        Returns:
            Dictionary mapping symbols to their current prices

        Note:
            Uses quote data and falls back to 0.0 for symbols with no data.

        """
        if not symbols:
            return {}

        result: dict[str, float] = {}

        for symbol in symbols:
            try:
                quote = self._market_data_service.get_quote(symbol)
                if quote and "ask_price" in quote and "bid_price" in quote:
                    # Use mid price as current price
                    mid_price = (quote["ask_price"] + quote["bid_price"]) / 2.0
                    result[symbol] = mid_price
                    self._logger.debug(f"Current price for {symbol}: {mid_price}")
                else:
                    self._logger.warning(f"No quote data for {symbol}")
                    result[symbol] = 0.0
            except Exception as e:
                self._logger.warning(
                    f"Failed to get current price for {symbol}: {e}",
                    extra={"component": _COMPONENT},
                )
                result[symbol] = 0.0

        return result

    def validate_connection(self) -> bool:
        """Validate connection to market data provider.

        Returns:
            True if connection is working, False otherwise

        """
        try:
            return self._alpaca.validate_connection()
        except Exception as e:
            self._logger.error(
                f"Market data connection validation failed: {e}",
                extra={"component": _COMPONENT},
            )
            return False
