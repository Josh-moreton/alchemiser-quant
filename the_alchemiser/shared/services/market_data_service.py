"""Business Unit: shared | Status: current

Market data service providing unified interface for strategy engines.

This service provides a clean interface for accessing market data from various sources,
primarily through AlpacaManager, while maintaining compatibility with strategy engines
that expect a MarketDataPort interface.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from the_alchemiser.shared.types.quote import QuoteModel
from the_alchemiser.shared.value_objects.symbol import Symbol

if TYPE_CHECKING:
    from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
    from the_alchemiser.strategy.types.bar import BarModel

logger = logging.getLogger(__name__)


class MarketDataService:
    """Market data service providing unified interface for strategy engines.

    This service wraps AlpacaManager to provide a clean, strategy-friendly interface
    for accessing market data. It implements the MarketDataPort protocol to ensure
    compatibility with strategy engines.
    """

    def __init__(self, market_data_repo: AlpacaManager) -> None:
        """Initialize market data service.

        Args:
            market_data_repo: AlpacaManager instance for data access

        """
        self._alpaca = market_data_repo
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def get_bars(self, symbol: Symbol, period: str, timeframe: str) -> list[BarModel]:
        """Get historical bars for a symbol.

        Args:
            symbol: Symbol to get bars for
            period: Period string (e.g., "30d", "1y")
            timeframe: Timeframe string (e.g., "1Day", "1Hour")

        Returns:
            List of BarModel instances

        """
        try:
            # Convert period to start/end dates
            end_date = datetime.now()

            # Parse period string
            if period.endswith("d"):
                days = int(period[:-1])
                start_date = end_date - timedelta(days=days)
            elif period.endswith("y"):
                years = int(period[:-1])
                start_date = end_date - timedelta(days=years * 365)
            else:
                # Default to 30 days
                start_date = end_date - timedelta(days=30)

            # Format for AlpacaManager
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")

            # Normalize timeframe
            timeframe_normalized = timeframe
            if timeframe.lower() == "1day":
                timeframe_normalized = "1Day"
            elif timeframe.lower() == "1hour":
                timeframe_normalized = "1Hour"

            # Get bars from AlpacaManager
            bars_data = self._alpaca.get_historical_bars(
                symbol=symbol.value,
                start_date=start_str,
                end_date=end_str,
                timeframe=timeframe_normalized,
            )

            # Convert to BarModel instances (simplified for now)
            # TODO: Import and use actual BarModel when strategy module is available
            bars = []
            for bar_data in bars_data:
                # For now, create a simple dict-based bar
                # This will be replaced with proper BarModel when available
                bars.append(bar_data)  # type: ignore[misc]

            self._logger.debug(f"Retrieved {len(bars)} bars for {symbol.value}")
            return bars

        except Exception as e:
            self._logger.warning(f"Failed to get bars for {symbol.value}: {e}")
            return []

    def get_latest_quote(self, symbol: Symbol) -> QuoteModel | None:
        """Get latest quote for a symbol.

        Args:
            symbol: Symbol to get quote for

        Returns:
            QuoteModel instance or None if not available

        """
        try:
            quote_data = self._alpaca.get_latest_quote(symbol.value)

            if quote_data is None:
                return None

            # quote_data is tuple[float, float] (bid, ask)
            bid, ask = quote_data

            return QuoteModel(
                symbol=symbol.value,
                bid=bid,
                ask=ask,
                bid_size=100.0,  # Default size
                ask_size=100.0,  # Default size
            )

        except Exception as e:
            self._logger.warning(f"Failed to get quote for {symbol.value}: {e}")
            return None

    def get_mid_price(self, symbol: Symbol) -> float | None:
        """Get mid price for a symbol.

        Args:
            symbol: Symbol to get mid price for

        Returns:
            Mid price as float or None if not available

        """
        try:
            quote = self.get_latest_quote(symbol)
            if quote is None:
                return None

            return (quote.bid + quote.ask) / 2.0

        except Exception as e:
            self._logger.warning(f"Failed to get mid price for {symbol.value}: {e}")
            return None
