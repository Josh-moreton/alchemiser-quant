"""Business Unit: data | Status: current.

Cached market data adapter for S3-backed market data.

This adapter implements the MarketDataPort interface using S3 Parquet storage
as the primary data source. When cache misses occur, it can optionally delegate
to a configurable fallback adapter (e.g., direct Alpaca API calls).

Architecture:
    S3 Cache (Parquet) -> CachedMarketDataAdapter
           |
    IndicatorService <- DSL Strategy Engine <- Strategy Lambda

    Data is populated by DataRefresh Lambda (Alpaca -> S3):
    - Morning refresh (9:30 AM UTC): fetches previous day's completed bars
    - Post-close refresh (4:05 PM ET): fetches today's completed daily bar

    Strategy Lambda runs after market close using completed daily bars.
"""

from __future__ import annotations

import json
import os
import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING

import boto3
import pandas as pd
from botocore.config import Config

from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.types.market_data import BarModel, QuoteModel
from the_alchemiser.shared.types.market_data_port import MarketDataPort
from the_alchemiser.shared.value_objects.symbol import Symbol

if TYPE_CHECKING:
    from mypy_boto3_lambda import LambdaClient

    from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager

logger = get_logger(__name__)

# Sync refresh configuration
SYNC_REFRESH_MAX_RETRIES = 2
SYNC_REFRESH_WAIT_SECONDS = 5.0
# Default timeout for sync refresh Lambda invocation (5 minutes)
# Can be overridden via SYNC_REFRESH_TIMEOUT_SECONDS env var
DEFAULT_SYNC_REFRESH_TIMEOUT_SECONDS = 300


def _get_sync_refresh_timeout() -> int:
    """Get sync refresh timeout from environment variable.

    Returns:
        Timeout in seconds for Data Lambda invocation

    """
    try:
        return int(
            os.environ.get("SYNC_REFRESH_TIMEOUT_SECONDS", DEFAULT_SYNC_REFRESH_TIMEOUT_SECONDS)
        )
    except (ValueError, TypeError):
        return DEFAULT_SYNC_REFRESH_TIMEOUT_SECONDS


def _parse_period_to_days(period: str) -> int:
    """Convert period string (e.g., '1Y', '6M', '90D', 'MAX') to number of days.

    Args:
        period: Period string in format <number><unit> where unit is Y/M/D,
            or the special value 'MAX' to request all available data.

    Returns:
        Number of calendar days. Returns -1 for 'MAX' (all available).

    Raises:
        ValueError: If period format is invalid

    """
    period = period.strip().upper()

    # Special sentinel: return all available data without date filtering
    if period == "MAX":
        return -1

    if period.endswith("Y"):
        years = int(period[:-1])
        return years * 365
    if period.endswith("M"):
        months = int(period[:-1])
        return months * 30
    if period.endswith("D"):
        return int(period[:-1])
    raise ValueError(
        f"Invalid period format: {period}. Expected format like '1Y', '6M', '90D', 'MAX'"
    )


class CachedMarketDataAdapter(MarketDataPort):
    """Market data adapter that uses S3 cache with optional fallback.

    This adapter reads daily bars from S3 Parquet files populated by the
    DataRefresh Lambda (morning + post-close schedules). When cache is empty
    or stale, it can optionally delegate to a configurable fallback adapter
    to fetch data on-demand.

    Fallback options:
    1. Direct Alpaca API: Falls back to live Alpaca API (requires alpaca-py)
    2. None (default): Returns empty data on cache miss

    In production, data should always be pre-populated by the scheduled refresh.

    Attributes:
        market_data_store: S3-backed Parquet storage for historical data
        fallback_adapter: Optional MarketDataPort for cache miss handling
        _alpaca_manager: Lazy-loaded Alpaca client for direct API fallback

    """

    def __init__(
        self,
        market_data_store: MarketDataStore | None = None,
        *,
        fallback_adapter: MarketDataPort | None = None,
        enable_live_fallback: bool = False,
        enable_sync_refresh: bool = False,
    ) -> None:
        """Initialize cached market data adapter.

        Args:
            market_data_store: S3 store for historical data. If None, creates default.
            fallback_adapter: Optional adapter to use on cache miss.
                             Takes precedence over enable_live_fallback.
            enable_live_fallback: Whether to fall back to direct Alpaca API on cache miss.
                                 Only used if fallback_adapter is None.
            enable_sync_refresh: Whether to synchronously invoke the Data Lambda to
                                refresh stale/missing data. Only for live trading runs.
                                Defaults to False to avoid blocking in backtests.

        """
        self.market_data_store = market_data_store or MarketDataStore()
        self._fallback_adapter = fallback_adapter
        self._alpaca_manager: AlpacaManager | None = None
        self._enable_live_fallback = enable_live_fallback
        self._enable_sync_refresh = enable_sync_refresh
        self._lambda_client: LambdaClient | None = None  # Lazy-init for sync refresh

        logger.info(
            "CachedMarketDataAdapter initialized",
            has_fallback_adapter=fallback_adapter is not None,
            live_fallback_enabled=enable_live_fallback,
            sync_refresh_enabled=enable_sync_refresh,
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

    def _get_lambda_client(self) -> LambdaClient:
        """Lazy-load Lambda client for sync refresh with 5-minute timeout.

        The timeout is configurable via SYNC_REFRESH_TIMEOUT_SECONDS env var.
        Default is 300 seconds (5 minutes) to allow Data Lambda time to fetch
        and store historical data for new symbols.

        Returns:
            boto3 Lambda client configured with read timeout for Data Lambda invocation.

        """
        if self._lambda_client is None:
            timeout_seconds = _get_sync_refresh_timeout()
            # Configure boto3 with extended read timeout for sync refresh
            # read_timeout must account for Data Lambda execution time
            config = Config(
                read_timeout=timeout_seconds + 30,  # Extra buffer for network latency
                connect_timeout=10,
                retries={"max_attempts": 0},  # No retries - we handle at higher level
            )
            self._lambda_client = boto3.client("lambda", config=config)
            logger.info(
                "Lambda client initialized for sync refresh",
                read_timeout_seconds=timeout_seconds + 30,
            )
        return self._lambda_client

    def _sync_refresh_symbol(self, symbol_str: str) -> bool:
        """Invoke Data Lambda synchronously to refresh a single symbol.

        This method invokes the Data Lambda directly (RequestResponse mode) to
        fetch and store data for a missing/stale symbol. Used only during live
        trading runs to ensure strategies have complete data.

        Timeout is controlled by SYNC_REFRESH_TIMEOUT_SECONDS env var (default 300s).

        Args:
            symbol_str: Symbol to refresh

        Returns:
            True if refresh succeeded and S3 now has fresh data, False otherwise

        """
        data_function_name = os.environ.get("DATA_FUNCTION_NAME", "")
        if not data_function_name:
            # Try constructing from stage
            stage = os.environ.get("STAGE", "dev")
            data_function_name = f"alchemiser-{stage}-data"

        timeout_seconds = _get_sync_refresh_timeout()
        logger.info(
            "Invoking Data Lambda synchronously for symbol refresh",
            symbol=symbol_str,
            function_name=data_function_name,
            timeout_seconds=timeout_seconds,
        )

        try:
            lambda_client = self._get_lambda_client()

            # Build event payload matching MarketDataFetchRequested format
            event_payload = {
                "detail-type": "MarketDataFetchRequested",
                "source": "alchemiser.strategy",
                "detail": {
                    "symbol": symbol_str,
                    "requested_by": "sync_refresh",
                    "correlation_id": f"sync-refresh-{symbol_str}",
                },
            }

            response = lambda_client.invoke(
                FunctionName=data_function_name,
                InvocationType="RequestResponse",  # Synchronous
                Payload=json.dumps(event_payload),
            )

            # Check response
            status_code = response.get("StatusCode", 0)
            if status_code != 200:
                logger.error(
                    "Data Lambda returned non-200 status",
                    symbol=symbol_str,
                    status_code=status_code,
                )
                return False

            # Parse response payload
            payload = response.get("Payload")
            if payload:
                result = json.loads(payload.read())
                body = result.get("body", {})
                if isinstance(body, str):
                    body = json.loads(body)

                # Match Data Lambda response statuses:
                # - "success": fetch completed with new bars
                # - "deduplicated": another request handled it recently
                status = body.get("status", "")
                if status in ("success", "deduplicated"):
                    logger.info(
                        "Sync refresh completed successfully",
                        symbol=symbol_str,
                        status=status,
                        bars_fetched=body.get("bars_fetched", 0),
                    )
                    return True

            logger.warning(
                "Sync refresh returned unexpected response",
                symbol=symbol_str,
            )
            return False

        except Exception as e:
            logger.error(
                "Sync refresh failed",
                symbol=symbol_str,
                error=str(e),
                error_type=type(e).__name__,
            )
            return False

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

    def _handle_cache_miss(
        self,
        symbol: Symbol,
        symbol_str: str,
        period: str,
        timeframe: str,
        lookback_days: int,
    ) -> list[BarModel]:
        """Handle cache miss by delegating to fallback.

        Args:
            symbol: Trading symbol object
            symbol_str: Symbol as string
            period: Lookback period string
            timeframe: Bar interval string
            lookback_days: Number of days to look back

        Returns:
            List of bars from fallback, or empty list

        """
        # Priority 1: Use pluggable fallback adapter (if configured)
        if self._fallback_adapter is not None:
            logger.info(
                "Cache miss - delegating to fallback adapter",
                symbol=symbol_str,
            )
            return self._fallback_adapter.get_bars(symbol, period, timeframe)

        # Priority 2: Sync refresh via Data Lambda (for live trading runs)
        if self._enable_sync_refresh:
            logger.info(
                "Cache miss - attempting sync refresh via Data Lambda",
                symbol=symbol_str,
            )
            for attempt in range(SYNC_REFRESH_MAX_RETRIES):
                if self._sync_refresh_symbol(symbol_str):
                    # Wait for S3 to be consistent, then retry read
                    time.sleep(SYNC_REFRESH_WAIT_SECONDS)

                    # Re-read from S3 cache (bypass local cache)
                    df = self.market_data_store.read_symbol_data(symbol_str, use_cache=False)
                    if df is not None and not df.empty:
                        # Convert and return the refreshed data
                        return self._dataframe_to_bars(df, symbol_str, lookback_days)

                if attempt < SYNC_REFRESH_MAX_RETRIES - 1:
                    logger.warning(
                        "Sync refresh attempt failed, retrying",
                        symbol=symbol_str,
                        attempt=attempt + 1,
                        max_retries=SYNC_REFRESH_MAX_RETRIES,
                    )
                    time.sleep(1.0)  # Brief pause before retry

            logger.error(
                "Sync refresh failed after all retries",
                symbol=symbol_str,
                attempts=SYNC_REFRESH_MAX_RETRIES,
            )
            # Fall through to other fallbacks

        # Priority 3: Direct Alpaca API fallback
        if self._enable_live_fallback:
            logger.info(
                "Cache miss - falling back to live Alpaca API",
                symbol=symbol_str,
            )
            return self._fetch_from_live_api(symbol_str, lookback_days)

        # No fallback available
        logger.warning(
            "Cache miss and no fallback configured",
            symbol=symbol_str,
        )
        return []

    def _dataframe_to_bars(
        self, df: pd.DataFrame, symbol_str: str, lookback_days: int
    ) -> list[BarModel]:
        """Convert DataFrame to BarModel list, filtering by lookback period.

        Creates a copy of the input DataFrame to avoid mutating caller's data.
        Uses itertuples for efficient row iteration per coding guidelines.
        Validates that no partial bars for today are included.

        Args:
            df: DataFrame with OHLCV data
            symbol_str: Symbol string for bar construction
            lookback_days: Number of days to include

        Returns:
            List of BarModel objects filtered to lookback period

        """
        if "timestamp" not in df.columns:
            return []

        # Create copy to avoid mutating caller's DataFrame
        df = df.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df = df.sort_values("timestamp")

        # Filter to lookback period
        cutoff_date = datetime.now(UTC) - timedelta(days=lookback_days)
        df = df[df["timestamp"] >= cutoff_date]

        if df.empty:
            return []

        # Use itertuples for efficient iteration (faster than iterrows)
        bars: list[BarModel] = []
        for row in df.itertuples(index=False):
            ts = row.timestamp
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            elif isinstance(ts, pd.Timestamp):
                ts = ts.to_pydatetime()
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=UTC)

            bar = BarModel(
                symbol=symbol_str,
                timestamp=ts,
                open=Decimal(str(row.open)),
                high=Decimal(str(row.high)),
                low=Decimal(str(row.low)),
                close=Decimal(str(row.close)),
                volume=int(row.volume),
            )
            bars.append(bar)

        return bars

    def get_bars(self, symbol: Symbol, period: str, timeframe: str) -> list[BarModel]:
        """Fetch historical bars from S3 cache, with fallback on miss.

        Args:
            symbol: Trading symbol
            period: Lookback period (e.g., "1Y", "6M", "90D")
            timeframe: Bar interval (must be "1Day" for cached data)

        Returns:
            List of BarModel objects, oldest first.

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
            return self._handle_cache_miss(symbol, symbol_str, period, timeframe, lookback_days)

        # Ensure timestamp column and sort
        if "timestamp" not in df.columns:
            logger.error(
                "Cached data missing timestamp column",
                symbol=symbol_str,
            )
            return self._handle_cache_miss(symbol, symbol_str, period, timeframe, lookback_days)

        df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        df = df.sort_values("timestamp")

        # Filter to lookback period (skip for MAX = all available data)
        if lookback_days > 0:
            cutoff_date = datetime.now(UTC) - timedelta(days=lookback_days)
            df = df[df["timestamp"] >= cutoff_date]

        if df.empty:
            logger.warning(
                "No data in lookback period",
                symbol=symbol_str,
                lookback_days=lookback_days,
            )
            return self._handle_cache_miss(symbol, symbol_str, period, timeframe, lookback_days)

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
