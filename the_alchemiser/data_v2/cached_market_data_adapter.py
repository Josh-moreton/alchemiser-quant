"""Business Unit: data | Status: current.

Cached market data adapter for S3-backed market data with Alpaca fallback.

This adapter implements the MarketDataPort interface using S3 Parquet storage
as the primary data source, with optional fallback to live Alpaca API for
quotes and missing historical data.

Architecture:
    S3 Cache (Parquet) -> IndicatorService
                      |
                      v
    Alpaca API (fallback for quotes/missing data)
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
    """Market data adapter that uses S3 cache with optional Alpaca fallback.

    This adapter first checks S3 for cached historical data. For quotes and
    potentially missing data, it can optionally fall back to a live market
    data provider.

    Attributes:
        market_data_store: S3-backed Parquet storage for historical data
        fallback_port: Optional MarketDataPort for live quotes and missing data

    """

    def __init__(
        self,
        market_data_store: MarketDataStore | None = None,
        fallback_port: MarketDataPort | None = None,
    ) -> None:
        """Initialize cached market data adapter.

        Args:
            market_data_store: S3 store for historical data. If None, creates default.
            fallback_port: Optional MarketDataPort for live quotes/missing data.
                If None, quotes will return None and missing data raises error.

        """
        self.market_data_store = market_data_store or MarketDataStore()
        self.fallback_port = fallback_port

        logger.info(
            "CachedMarketDataAdapter initialized",
            has_fallback=fallback_port is not None,
        )

    def get_bars(self, symbol: Symbol, period: str, timeframe: str) -> list[BarModel]:
        """Fetch historical bars from S3 cache.

        Args:
            symbol: Trading symbol
            period: Lookback period (e.g., "1Y", "6M", "90D")
            timeframe: Bar interval (must be "1Day" for cached data)

        Returns:
            List of BarModel objects, oldest first

        Raises:
            ValueError: If timeframe is not "1Day" or symbol not found

        """
        symbol_str = str(symbol)

        # Currently only support daily bars in cache
        if timeframe not in ("1Day", "1D"):
            if self.fallback_port:
                logger.debug(
                    "Timeframe not cached, using fallback",
                    symbol=symbol_str,
                    timeframe=timeframe,
                )
                return self.fallback_port.get_bars(symbol, period, timeframe)
            raise ValueError(f"Timeframe {timeframe} not supported without fallback")

        # Calculate lookback days from period
        lookback_days = _parse_period_to_days(period)

        # Read full symbol data and filter by date range
        df = self.market_data_store.read_symbol_data(symbol_str)

        if df is None or df.empty:
            logger.warning(
                "No cached data found",
                symbol=symbol_str,
            )

            if self.fallback_port:
                logger.debug(
                    "Using fallback for missing symbol",
                    symbol=symbol_str,
                )
                return self.fallback_port.get_bars(symbol, period, timeframe)
            return []

        # Ensure timestamp column and sort
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
            df = df.sort_values("timestamp")
        else:
            if self.fallback_port:
                return self.fallback_port.get_bars(symbol, period, timeframe)
            return []

        # Filter to lookback period
        cutoff_date = datetime.now(UTC) - timedelta(days=lookback_days)
        df = df[df["timestamp"] >= cutoff_date]

        if df.empty:
            if self.fallback_port:
                return self.fallback_port.get_bars(symbol, period, timeframe)
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
        """Get latest quote (requires fallback to live API).

        Args:
            symbol: Trading symbol

        Returns:
            QuoteModel from fallback, or None if no fallback configured

        """
        if not self.fallback_port:
            logger.debug(
                "No fallback configured for quotes",
                symbol=str(symbol),
            )
            return None

        return self.fallback_port.get_latest_quote(symbol)

    def get_mid_price(self, symbol: Symbol) -> float | None:
        """Get mid price (requires fallback to live API).

        Args:
            symbol: Trading symbol

        Returns:
            Mid price from fallback, or None if no fallback configured

        """
        if not self.fallback_port:
            logger.debug(
                "No fallback configured for mid price",
                symbol=str(symbol),
            )
            return None

        return self.fallback_port.get_mid_price(symbol)

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
