"""Business Unit: data | Status: current.

Cached market data adapter for S3-backed market data.

This adapter implements the MarketDataPort interface using S3 Parquet storage
as the primary data source. For Strategy Lambda, this is the ONLY data source -
no live Alpaca API calls are made.

Architecture:
    S3 Cache (Parquet) -> IndicatorService -> DSL Strategy Engine

    Data is populated nightly by DataRefresh Lambda (Alpaca -> S3).
    Strategy Lambda reads only from S3 cache.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

import pandas as pd

from the_alchemiser.data_v2.market_data_store import MarketDataStore
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.types.market_data import BarModel, QuoteModel
from the_alchemiser.shared.types.market_data_port import MarketDataPort
from the_alchemiser.shared.value_objects.symbol import Symbol

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)


def _parse_period_to_days(period: str) -> int:
    """Convert period string (e.g., '1Y', '6M', '90D') to number of days.

    Args:
        period: Period string in format <number><unit> where unit is Y/M/D

    Returns:
        Number of calendar days

    Raises:
        ValueError: If period format is invalid

    """
    period = period.strip().upper()

    if period.endswith("Y"):
        years = int(period[:-1])
        return years * 365
    if period.endswith("M"):
        months = int(period[:-1])
        return months * 30
    if period.endswith("D"):
        return int(period[:-1])
    raise ValueError(f"Invalid period format: {period}. Expected format like '1Y', '6M', '90D'")


class CachedMarketDataAdapter(MarketDataPort):
    """Market data adapter that uses S3 cache as the sole data source.

    This adapter reads historical data from S3 Parquet files populated by the
    nightly DataRefresh Lambda. It does NOT require alpaca-py or live API access.

    For Strategy Lambda, this removes the Alpaca SDK dependency entirely.

    Attributes:
        market_data_store: S3-backed Parquet storage for historical data

    """

    def __init__(
        self,
        market_data_store: MarketDataStore | None = None,
    ) -> None:
        """Initialize cached market data adapter.

        Args:
            market_data_store: S3 store for historical data. If None, creates default.

        """
        self.market_data_store = market_data_store or MarketDataStore()

        logger.info("CachedMarketDataAdapter initialized (S3-only, no fallback)")

    def get_bars(self, symbol: Symbol, period: str, timeframe: str) -> list[BarModel]:
        """Fetch historical bars from S3 cache.

        Args:
            symbol: Trading symbol
            period: Lookback period (e.g., "1Y", "6M", "90D")
            timeframe: Bar interval (must be "1Day" for cached data)

        Returns:
            List of BarModel objects, oldest first

        Raises:
            ValueError: If timeframe is not "1Day" or symbol data not found

        """
        symbol_str = str(symbol)

        # Currently only support daily bars in cache
        if timeframe not in ("1Day", "1D"):
            raise ValueError(
                f"Timeframe {timeframe} not supported in S3 cache. "
                f"Only daily bars (1Day/1D) are cached. Symbol: {symbol_str}"
            )

        # Calculate lookback days from period
        lookback_days = _parse_period_to_days(period)

        # Read full symbol data and filter by date range
        df = self.market_data_store.read_symbol_data(symbol_str)

        if df is None or df.empty:
            logger.warning(
                "No cached data found - ensure DataRefresh has run",
                symbol=symbol_str,
            )
            # Return empty list - let caller handle missing data gracefully
            return []

        # Ensure timestamp column and sort
        if "timestamp" not in df.columns:
            logger.error(
                "Cached data missing timestamp column",
                symbol=symbol_str,
            )
            return []

        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df = df.sort_values("timestamp")

        # Filter to lookback period
        cutoff_date = datetime.now(UTC) - timedelta(days=lookback_days)
        df = df[df["timestamp"] >= cutoff_date]

        if df.empty:
            logger.warning(
                "No data in lookback period",
                symbol=symbol_str,
                lookback_days=lookback_days,
            )
            return []

        # Convert DataFrame to BarModel list
        bars: list[BarModel] = []
        for _, row in df.iterrows():
            # Parse timestamp
            ts = row["timestamp"]
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            elif isinstance(ts, pd.Timestamp):
                ts = ts.to_pydatetime()
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=UTC)

            bar = BarModel(
                symbol=symbol_str,
                timestamp=ts,
                open=Decimal(str(row["open"])),
                high=Decimal(str(row["high"])),
                low=Decimal(str(row["low"])),
                close=Decimal(str(row["close"])),
                volume=int(row["volume"]),
            )
            bars.append(bar)

        logger.debug(
            "Retrieved bars from cache",
            symbol=symbol_str,
            bars_count=len(bars),
        )

        return bars

    def get_latest_quote(self, symbol: Symbol) -> QuoteModel | None:
        """Get latest quote from cached data.

        For Strategy Lambda, we don't need live quotes - the strategy uses
        historical close prices for signal generation. Returns a synthetic
        quote based on the most recent cached bar.

        Args:
            symbol: Trading symbol

        Returns:
            QuoteModel with bid/ask set to last close, or None if no data

        """
        symbol_str = str(symbol)
        df = self.market_data_store.read_symbol_data(symbol_str)

        if df is None or df.empty:
            logger.debug(
                "No cached data for quote",
                symbol=symbol_str,
            )
            return None

        # Get the most recent bar's close price
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
            df = df.sort_values("timestamp")

        last_row = df.iloc[-1]
        close_price = Decimal(str(last_row["close"]))

        # Return synthetic quote with bid=ask=close (no spread)
        return QuoteModel(
            symbol=symbol_str,
            bid_price=close_price,
            ask_price=close_price,
            bid_size=Decimal("0"),
            ask_size=Decimal("0"),
            timestamp=datetime.now(UTC),
        )

    def get_mid_price(self, symbol: Symbol) -> float | None:
        """Get mid price from cached data.

        Returns the most recent close price from the cache.

        Args:
            symbol: Trading symbol

        Returns:
            Latest close price as float, or None if no data

        """
        symbol_str = str(symbol)
        df = self.market_data_store.read_symbol_data(symbol_str)

        if df is None or df.empty:
            logger.debug(
                "No cached data for mid price",
                symbol=symbol_str,
            )
            return None

        # Get the most recent bar's close price
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
            df = df.sort_values("timestamp")

        return float(df.iloc[-1]["close"])

    def warm_cache(self, symbols: list[str]) -> None:
        """Pre-load symbol data into local Lambda /tmp cache.

        Call during cold start to minimize S3 calls during indicator computation.

        Args:
            symbols: List of symbol strings to pre-cache

        """
        logger.info(
            "Warming cache",
            symbol_count=len(symbols),
        )

        try:
            results = self.market_data_store.download_to_cache(symbols)
            failed = [s for s, ok in results.items() if not ok]
            if failed:
                logger.warning(
                    "Some symbols failed to cache",
                    failed_symbols=failed,
                )
        except Exception as e:
            logger.warning(
                "Failed to warm cache",
                error=str(e),
            )
