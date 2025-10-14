"""Business Unit: scripts | Status: current.

Alpaca historical data provider for backtesting.

Downloads historical market data from Alpaca API.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

# Add project root to path for imports
_project_root = Path(__file__).resolve().parents[4]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from scripts.backtest.models.market_data import DailyBar
from the_alchemiser.shared.config.secrets_adapter import get_alpaca_keys
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


class AlpacaHistoricalProvider:
    """Alpaca historical data provider.

    Downloads daily OHLCV data from Alpaca API and converts to DailyBar DTOs.
    """

    def __init__(self) -> None:
        """Initialize Alpaca historical data provider."""
        api_key, secret_key, _ = get_alpaca_keys()
        if not api_key or not secret_key:
            error_msg = "Alpaca API credentials not available"
            raise ValueError(error_msg)

        self._client = StockHistoricalDataClient(api_key=api_key, secret_key=secret_key)
        logger.info("Alpaca historical provider initialized")

    def fetch_daily_bars(
        self, symbol: str, start_date: datetime, end_date: datetime
    ) -> list[DailyBar]:
        """Fetch daily bars for a symbol from Alpaca.

        Args:
            symbol: Stock symbol to fetch
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            List of DailyBar objects sorted by date

        Raises:
            Exception: If data fetch fails

        """
        logger.info(
            f"Fetching daily bars for {symbol}",
            symbol=symbol,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )

        try:
            # Ensure dates are timezone-aware (UTC)
            if start_date.tzinfo is None:
                start_date = start_date.replace(tzinfo=UTC)
            if end_date.tzinfo is None:
                end_date = end_date.replace(tzinfo=UTC)

            # Create request for daily bars
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Day,
                start=start_date,
                end=end_date + timedelta(days=1),  # Alpaca end is exclusive
                adjustment="all",  # Get adjusted prices for splits/dividends
            )

            # Fetch data from Alpaca
            bars_dict = self._client.get_stock_bars(request)

            # Access data from BarSet object (has .data attribute with dict)
            if not hasattr(bars_dict, "data") or symbol not in bars_dict.data:
                logger.warning(f"No data returned for {symbol}")
                return []

            bars = bars_dict.data[symbol]
            if not bars:
                logger.warning(f"Empty bar list returned for {symbol}")
                return []

            daily_bars: list[DailyBar] = []

            for bar in bars:
                # Ensure timestamp is timezone-aware
                timestamp = bar.timestamp
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=UTC)

                daily_bar = DailyBar(
                    date=timestamp,
                    open=Decimal(str(bar.open)),
                    high=Decimal(str(bar.high)),
                    low=Decimal(str(bar.low)),
                    close=Decimal(str(bar.close)),
                    volume=int(bar.volume),
                    adjusted_close=Decimal(str(bar.close)),  # Alpaca returns adjusted prices
                )
                daily_bars.append(daily_bar)

            logger.info(
                f"Fetched {len(daily_bars)} bars for {symbol}",
                symbol=symbol,
                bar_count=len(daily_bars),
            )

            return daily_bars

        except Exception as e:
            logger.error(
                f"Failed to fetch daily bars for {symbol}",
                symbol=symbol,
                error=str(e),
            )
            raise

    def fetch_multiple_symbols(
        self, symbols: list[str], start_date: datetime, end_date: datetime
    ) -> dict[str, list[DailyBar]]:
        """Fetch daily bars for multiple symbols.

        Args:
            symbols: List of stock symbols
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Dictionary mapping symbol to list of DailyBar objects

        """
        logger.info(
            f"Fetching daily bars for {len(symbols)} symbols",
            symbol_count=len(symbols),
            symbols=symbols,
        )

        results: dict[str, list[DailyBar]] = {}

        for symbol in symbols:
            try:
                bars = self.fetch_daily_bars(symbol, start_date, end_date)
                results[symbol] = bars
            except Exception as e:
                logger.error(
                    f"Failed to fetch data for {symbol}, skipping",
                    symbol=symbol,
                    error=str(e),
                )
                results[symbol] = []

        logger.info(
            f"Completed fetching data for {len(symbols)} symbols",
            symbol_count=len(symbols),
            successful=len([s for s, bars in results.items() if bars]),
        )

        return results
