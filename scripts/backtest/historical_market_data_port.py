"""Business Unit: scripts | Status: current.

Historical market data adapter for backtesting.

Provides MarketDataPort interface using stored historical data.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Add project root to path for imports
_project_root = Path(__file__).resolve().parents[2]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from scripts.backtest.storage.data_store import DataStore
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.types.market_data import BarModel, QuoteModel
from the_alchemiser.shared.value_objects.symbol import Symbol

# Constants
BID_ASK_SPREAD_PCT = Decimal("0.0001")  # 0.01% spread for simulated quotes
DEFAULT_PERIOD_DAYS = 252  # Default period for historical data (1 trading year)

logger = get_logger(__name__)


class HistoricalMarketDataPort:
    """Market data port that serves historical data for backtesting.

    Implements MarketDataPort interface using stored Parquet data.
    """

    def __init__(self, data_store: DataStore, current_date: datetime) -> None:
        """Initialize historical market data port.

        Args:
            data_store: DataStore instance with historical data
            current_date: Current date in backtest iteration (must be timezone-aware)

        Raises:
            ValueError: If current_date is not timezone-aware

        """
        if current_date.tzinfo is None:
            error_msg = "current_date must be timezone-aware"
            raise ValueError(error_msg)

        self.data_store = data_store
        self.current_date = current_date
        logger.debug(f"HistoricalMarketDataPort initialized for {current_date.date()}")

    def get_bars(self, symbol: Symbol, period: str, timeframe: str) -> list[BarModel]:
        """Get historical bars for a symbol.

        Args:
            symbol: Symbol to fetch
            period: Period string (e.g., "1Y", "6M")
            timeframe: Timeframe string (e.g., "1Day")

        Returns:
            List of BarModel objects

        """
        # Parse period to determine start date
        period_days = self._parse_period(period)
        start_date = self.current_date - timedelta(days=period_days)
        end_date = self.current_date

        # Load bars from data store
        try:
            daily_bars = self.data_store.load_bars(str(symbol), start_date, end_date)

            # Convert DailyBar to BarModel
            bar_models: list[BarModel] = []
            for bar in daily_bars:
                bar_model = BarModel(
                    symbol=str(symbol),
                    timestamp=bar.date,
                    open=float(bar.open),
                    high=float(bar.high),
                    low=float(bar.low),
                    close=float(bar.close),
                    volume=bar.volume,
                )
                bar_models.append(bar_model)

            logger.debug(
                f"Loaded {len(bar_models)} bars for {symbol}",
                symbol=str(symbol),
                bar_count=len(bar_models),
            )

            return bar_models

        except Exception as e:
            logger.warning(
                f"Failed to load bars for {symbol}: {e}",
                symbol=str(symbol),
                error=str(e),
            )
            return []

    def get_latest_quote(self, symbol: Symbol) -> QuoteModel | None:
        """Get latest quote (simulated from current day's bar).

        Args:
            symbol: Symbol to fetch

        Returns:
            Enhanced QuoteModel with bid/ask from Open price, or None

        """
        # Load current day's bar
        try:
            from datetime import UTC

            bars = self.data_store.load_bars(
                str(symbol),
                self.current_date,
                self.current_date,
            )

            if not bars:
                return None

            bar = bars[0]
            # Simulate bid/ask from open price with small spread
            mid_price = bar.open
            spread = mid_price * BID_ASK_SPREAD_PCT

            # Simulate bid_size and ask_size (typical market depth)
            bid_size = Decimal("100")
            ask_size = Decimal("100")

            return QuoteModel(
                symbol=str(symbol),
                bid_price=mid_price - spread,
                ask_price=mid_price + spread,
                bid_size=bid_size,
                ask_size=ask_size,
                timestamp=bar.date.replace(tzinfo=UTC) if bar.date.tzinfo is None else bar.date,
            )

        except Exception as e:
            logger.debug(
                f"Could not get quote for {symbol}: {e}",
                symbol=str(symbol),
                error=str(e),
            )
            return None

    def get_mid_price(self, symbol: Symbol) -> float | None:
        """Get mid price from current day's bar.

        Args:
            symbol: Symbol to fetch

        Returns:
            Mid price as float, or None

        """
        quote = self.get_latest_quote(symbol)
        if quote:
            return float(quote.mid)
        return None

    def _parse_period(self, period: str) -> int:
        """Parse period string to number of days.

        Args:
            period: Period string like "1Y", "6M", "1D"

        Returns:
            Number of days

        """
        period = period.upper().strip()

        # Extract number and unit
        if period[-1] == "Y":
            years = int(period[:-1])
            return years * 365
        if period[-1] == "M":
            months = int(period[:-1])
            return months * 30
        if period[-1] == "D":
            return int(period[:-1])

        # Default to 1 trading year
        return DEFAULT_PERIOD_DAYS
