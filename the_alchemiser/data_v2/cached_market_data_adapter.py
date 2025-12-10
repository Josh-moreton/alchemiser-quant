"""Business Unit: data | Status: current.

Cached market data adapter for S3-backed market data with live API fallback.

This adapter implements the MarketDataPort interface using S3 Parquet storage
as the primary data source. When cache misses occur, it falls back to the
live Alpaca API to fetch data on-demand.

Architecture:
    S3 Cache (Parquet) -> [cache miss?] -> Alpaca Live API
           ↓
    IndicatorService -> DSL Strategy Engine

    Data is populated nightly by DataRefresh Lambda (Alpaca -> S3).
    Strategy Lambda reads from S3 cache, with live API fallback.
"""

from __future__ import annotations

import os
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
    from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager

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
    """Market data adapter that uses S3 cache with live Alpaca API fallback.

    This adapter reads historical data from S3 Parquet files populated by the
    nightly DataRefresh Lambda. When cache is empty or stale, it falls back to
    the live Alpaca API to fetch data on-demand.

    This ensures strategies can always run, even before the first data refresh.

    Attributes:
        market_data_store: S3-backed Parquet storage for historical data
        _alpaca_manager: Lazy-loaded Alpaca client for fallback

    """

    def __init__(
        self,
        market_data_store: MarketDataStore | None = None,
        *,
        enable_live_fallback: bool = True,
    ) -> None:
        """Initialize cached market data adapter.

        Args:
            market_data_store: S3 store for historical data. If None, creates default.
            enable_live_fallback: Whether to fall back to live Alpaca API on cache miss.

        """
        self.market_data_store = market_data_store or MarketDataStore()
        self._alpaca_manager: AlpacaManager | None = None
        self._enable_live_fallback = enable_live_fallback

        logger.info(
            "CachedMarketDataAdapter initialized",
            live_fallback_enabled=enable_live_fallback,
        )

    def _get_alpaca_manager(self) -> AlpacaManager:
        """Lazy-load Alpaca manager for fallback queries."""
        if self._alpaca_manager is None:
            from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager

            self._alpaca_manager = AlpacaManager(
                api_key=os.environ.get("ALPACA__KEY", ""),
                secret_key=os.environ.get("ALPACA__SECRET", ""),
                paper=True,  # Data API works same for paper/live
            )
            logger.info("Alpaca manager initialized for live fallback")
        return self._alpaca_manager

    def _fetch_from_live_api(
        self,
        symbol_str: str,
        lookback_days: int,
    ) -> list[BarModel]:
        """Fetch bars from live Alpaca API.

        Args:
            symbol_str: Ticker symbol
            lookback_days: Number of days to look back

        Returns:
            List of BarModel objects from live API

        """
        from the_alchemiser.shared.services.market_data_service import MarketDataService

        logger.info(
            "Fetching from live Alpaca API (cache miss)",
            symbol=symbol_str,
            lookback_days=lookback_days,
        )

        try:
            alpaca = self._get_alpaca_manager()
            market_data_service = MarketDataService(alpaca)

            # Calculate date range
            end_date = datetime.now(UTC).date()
            start_date = end_date - timedelta(days=lookback_days)

            # Fetch bars from Alpaca (returns list of dicts)
            bars_data = market_data_service.get_historical_bars(
                symbol=symbol_str,
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                timeframe="1Day",
            )

            if not bars_data:
                logger.warning(
                    "Live API returned no bars",
                    symbol=symbol_str,
                )
                return []

            # Convert dict data to BarModel list
            bars: list[BarModel] = []
            for bar_dict in bars_data:
                # Parse timestamp
                ts = bar_dict.get("timestamp")
                if isinstance(ts, str):
                    if ts.endswith("Z"):
                        ts = ts[:-1] + "+00:00"
                    ts = datetime.fromisoformat(ts)
                elif ts is None:
                    continue

                bar = BarModel(
                    symbol=symbol_str,
                    timestamp=ts,
                    open=Decimal(str(bar_dict["open"])),
                    high=Decimal(str(bar_dict["high"])),
                    low=Decimal(str(bar_dict["low"])),
                    close=Decimal(str(bar_dict["close"])),
                    volume=int(bar_dict["volume"]),
                )
                bars.append(bar)

            logger.info(
                "Live API returned bars",
                symbol=symbol_str,
                bars_count=len(bars),
            )

            return bars

        except Exception as e:
            logger.error(
                "Live API fallback failed",
                symbol=symbol_str,
                error=str(e),
                error_type=type(e).__name__,
            )
            return []

    def get_bars(self, symbol: Symbol, period: str, timeframe: str) -> list[BarModel]:
        """Fetch historical bars from S3 cache, with live API fallback.

        Args:
            symbol: Trading symbol
            period: Lookback period (e.g., "1Y", "6M", "90D")
            timeframe: Bar interval (must be "1Day" for cached data)

        Returns:
            List of BarModel objects, oldest first

        Raises:
            ValueError: If timeframe is not "1Day"

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
                "No cached data found",
                symbol=symbol_str,
            )
            # Fall back to live API if enabled
            if self._enable_live_fallback:
                return self._fetch_from_live_api(symbol_str, lookback_days)
            return []

        # Ensure timestamp column and sort
        if "timestamp" not in df.columns:
            logger.error(
                "Cached data missing timestamp column",
                symbol=symbol_str,
            )
            # Fall back to live API if enabled
            if self._enable_live_fallback:
                return self._fetch_from_live_api(symbol_str, lookback_days)
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
            # Fall back to live API if enabled
            if self._enable_live_fallback:
                return self._fetch_from_live_api(symbol_str, lookback_days)
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
