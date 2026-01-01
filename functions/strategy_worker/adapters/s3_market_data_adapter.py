"""Business Unit: strategy | Status: current.

S3 Market Data Adapter for strategy execution.

Provides read-only access to market data stored in S3 by the shared Data Lambda.
On missing data detection, publishes MarketDataFetchRequested events to EventBridge
instead of writing to S3 directly.

This adapter is read-only - all writes are performed by the shared Data Lambda.
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

import pandas as pd

from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore
from the_alchemiser.shared.events import MarketDataFetchRequested
from the_alchemiser.shared.events.eventbridge_publisher import EventBridgePublisher
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.market_bar import MarketBar

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)

# Component identifier for logging
_COMPONENT = "strategy_v2.adapters.s3_market_data_adapter"

# Environment variable for shared data event bus
SHARED_DATA_EVENT_BUS_ENV = "SHARED_DATA_EVENT_BUS"


class S3MarketDataAdapter:
    """Read-only market data adapter backed by S3 Parquet files.

    Provides market data access for strategy execution by reading from the
    shared S3 bucket. Does not write to S3 - on missing data, publishes
    MarketDataFetchRequested events for the Data Lambda to handle.

    Attributes:
        market_data_store: S3 store for reading data
        correlation_id: Correlation ID for tracing
        stage: Current stage (dev/staging/prod) for event attribution

    """

    def __init__(
        self,
        market_data_store: MarketDataStore | None = None,
        correlation_id: str | None = None,
        stage: str | None = None,
    ) -> None:
        """Initialize S3 market data adapter.

        Args:
            market_data_store: S3 store instance. If None, creates from env vars.
            correlation_id: Optional correlation ID for tracing.
            stage: Current stage. If None, reads from APP__STAGE env var.

        """
        self.market_data_store = market_data_store or MarketDataStore()
        self.correlation_id = correlation_id
        self.stage = stage or os.environ.get("APP__STAGE", "dev")

        logger.debug(
            "S3MarketDataAdapter initialized",
            extra={
                "component": _COMPONENT,
                "bucket": self.market_data_store.bucket_name,
                "stage": self.stage,
                "correlation_id": self.correlation_id,
            },
        )

    def get_bars(
        self,
        symbols: list[str],
        lookback_days: int = 365,
    ) -> dict[str, list[MarketBar]]:
        """Get historical bars for multiple symbols from S3.

        Reads Parquet files from S3 and converts to MarketBar objects.
        On missing data, publishes MarketDataFetchRequested event and returns
        empty list for that symbol (does not block waiting for fetch).

        Args:
            symbols: List of symbols to fetch data for
            lookback_days: Number of days of data to return

        Returns:
            Dictionary mapping symbols to their bar data. Empty list for symbols
            with missing data (fetch request published asynchronously).

        """
        result: dict[str, list[MarketBar]] = {}
        missing_symbols: list[str] = []

        for symbol in symbols:
            try:
                df = self.market_data_store.read_symbol_data(symbol, use_cache=True)

                if df is None or df.empty:
                    # Data missing - track for fetch request
                    logger.warning(
                        "Missing market data",
                        extra={
                            "component": _COMPONENT,
                            "symbol": symbol,
                            "correlation_id": self.correlation_id,
                        },
                    )
                    missing_symbols.append(symbol)
                    result[symbol] = []
                    continue

                # Convert DataFrame to MarketBar objects
                bars = self._convert_df_to_bars(df, symbol, lookback_days)
                result[symbol] = bars

                logger.debug(
                    "Read bars from S3",
                    extra={
                        "component": _COMPONENT,
                        "symbol": symbol,
                        "bar_count": len(bars),
                        "correlation_id": self.correlation_id,
                    },
                )

            except Exception as e:
                logger.error(
                    "Failed to read market data",
                    extra={
                        "component": _COMPONENT,
                        "symbol": symbol,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "correlation_id": self.correlation_id,
                    },
                )
                result[symbol] = []

        # Publish fetch requests for missing symbols
        if missing_symbols:
            self._publish_fetch_requests(missing_symbols, lookback_days)

        return result

    def _convert_df_to_bars(
        self,
        df: pd.DataFrame,
        symbol: str,
        lookback_days: int,
    ) -> list[MarketBar]:
        """Convert DataFrame to list of MarketBar objects.

        Args:
            df: DataFrame with OHLCV data
            symbol: Ticker symbol
            lookback_days: Days of data to return

        Returns:
            List of MarketBar objects

        """
        # Ensure timestamp column and sort
        if "timestamp" not in df.columns:
            logger.warning(
                "DataFrame missing timestamp column",
                extra={"component": _COMPONENT, "symbol": symbol},
            )
            return []

        df = df.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values("timestamp")

        # Filter to lookback period
        cutoff = datetime.now(UTC) - pd.Timedelta(days=lookback_days)
        df = df[df["timestamp"] >= cutoff]

        # Convert to MarketBar objects
        bars: list[MarketBar] = []
        for _, row in df.iterrows():
            try:
                bar = MarketBar(
                    symbol=symbol,
                    timestamp=row["timestamp"].to_pydatetime().replace(tzinfo=UTC),
                    timeframe="1D",
                    open_price=Decimal(str(row["open"])),
                    high_price=Decimal(str(row["high"])),
                    low_price=Decimal(str(row["low"])),
                    close_price=Decimal(str(row["close"])),
                    volume=int(row.get("volume", 0)),
                )
                bars.append(bar)
            except Exception as e:
                logger.warning(
                    "Failed to convert bar",
                    extra={
                        "component": _COMPONENT,
                        "symbol": symbol,
                        "error": str(e),
                    },
                )
                continue

        return bars

    def _publish_fetch_requests(
        self,
        symbols: list[str],
        lookback_days: int,
    ) -> None:
        """Publish MarketDataFetchRequested events for missing symbols.

        Args:
            symbols: List of symbols with missing data
            lookback_days: Days of data to request

        """
        # Get shared data event bus name (if configured)
        event_bus = os.environ.get(SHARED_DATA_EVENT_BUS_ENV)

        # Create publisher with appropriate event bus
        publisher = EventBridgePublisher(event_bus_name=event_bus)

        for symbol in symbols:
            try:
                event = MarketDataFetchRequested(
                    correlation_id=self.correlation_id or f"fetch-request-{uuid.uuid4()}",
                    causation_id=self.correlation_id or f"fetch-request-{uuid.uuid4()}",
                    event_id=f"fetch-request-{symbol}-{uuid.uuid4()}",
                    timestamp=datetime.now(UTC),
                    source_module="strategy_v2",
                    source_component="s3_market_data_adapter",
                    symbol=symbol,
                    requesting_stage=self.stage,
                    requesting_component="s3_market_data_adapter",
                    lookback_days=lookback_days,
                    reason="missing_data",
                )

                # Publish using our configured publisher
                publisher.publish(event)

                logger.info(
                    "Published MarketDataFetchRequested",
                    extra={
                        "component": _COMPONENT,
                        "symbol": symbol,
                        "stage": self.stage,
                        "event_bus": event_bus or "default",
                        "correlation_id": self.correlation_id,
                    },
                )

            except Exception as e:
                logger.error(
                    "Failed to publish MarketDataFetchRequested",
                    extra={
                        "component": _COMPONENT,
                        "symbol": symbol,
                        "error": str(e),
                        "correlation_id": self.correlation_id,
                    },
                )

    def get_close_prices(
        self,
        symbol: str,
        lookback_days: int = 365,
    ) -> pd.Series | None:
        """Get closing prices for a symbol as a pandas Series.

        Convenience method for indicator computation.

        Args:
            symbol: Ticker symbol
            lookback_days: Number of days of data

        Returns:
            Series of closing prices indexed by date, or None if not found

        """
        bars = self.get_bars([symbol], lookback_days).get(symbol, [])

        if not bars:
            return None

        return pd.Series(
            [float(bar.close_price) for bar in bars],
            index=[bar.timestamp for bar in bars],
        )

    def validate_data_freshness(
        self,
        symbol: str,
        max_stale_days: int = 3,
    ) -> bool:
        """Check if data for a symbol is fresh enough.

        Args:
            symbol: Ticker symbol
            max_stale_days: Maximum days since last bar before considered stale

        Returns:
            True if data is fresh, False if stale or missing

        """
        metadata = self.market_data_store.get_metadata(symbol)

        if metadata is None:
            logger.warning(
                "No metadata for symbol",
                extra={"component": _COMPONENT, "symbol": symbol},
            )
            return False

        try:
            last_bar_date = datetime.strptime(metadata.last_bar_date, "%Y-%m-%d").replace(
                tzinfo=UTC
            )
            days_since = (datetime.now(UTC) - last_bar_date).days

            is_fresh = days_since <= max_stale_days

            if not is_fresh:
                logger.warning(
                    "Stale market data",
                    extra={
                        "component": _COMPONENT,
                        "symbol": symbol,
                        "last_bar_date": metadata.last_bar_date,
                        "days_since": days_since,
                        "max_stale_days": max_stale_days,
                    },
                )
                # Publish fetch request for stale data
                self._publish_fetch_requests([symbol], lookback_days=30)

            return is_fresh

        except Exception as e:
            logger.error(
                "Failed to check data freshness",
                extra={
                    "component": _COMPONENT,
                    "symbol": symbol,
                    "error": str(e),
                },
            )
            return False
