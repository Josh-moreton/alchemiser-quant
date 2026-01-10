"""Business Unit: data | Status: current.

Live bar provider for fetching today's OHLCV data from Alpaca Snapshot API.

This module provides real-time daily bar data for the current trading day,
enabling strategies to compute indicators using the most recent price action.
It uses Alpaca's Snapshot API which returns today's partial daily bar with
cumulative volume, open, high, low, and current close.

Architecture:
    Strategy Lambda -> CachedMarketDataAdapter -> LiveBarProvider
                                                      |
                                                      v
                                              Alpaca Snapshot API

The provider caches fetched bars for the duration of a strategy run to
minimize API calls when multiple indicators request the same symbol.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from the_alchemiser.shared.brokers.alpaca_utils import normalize_symbol_for_alpaca
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.types.market_data import BarModel

if TYPE_CHECKING:
    from alpaca.data.historical import StockHistoricalDataClient

logger = get_logger(__name__)


class LiveBarProvider:
    """Provider for fetching today's live bar from Alpaca Snapshot API.

    Uses Alpaca's Snapshot endpoint which provides:
    - latest_quote: Current bid/ask
    - latest_trade: Most recent trade price
    - daily_bar: Today's OHLCV (partial, updates throughout the day)

    Bars are cached for the duration of the strategy run to avoid redundant
    API calls when multiple indicators request the same symbol.

    Attributes:
        _client: Alpaca data client for API calls
        _cache: In-memory cache of fetched bars {symbol: BarModel}

    """

    def __init__(
        self,
        api_key: str | None = None,
        secret_key: str | None = None,
    ) -> None:
        """Initialize live bar provider.

        Args:
            api_key: Alpaca API key. Reads from ALPACA_KEY or ALPACA__KEY env var if not provided.
            secret_key: Alpaca secret key. Reads from ALPACA_SECRET or ALPACA__SECRET env var if not provided.

        """
        self._api_key = (
            api_key or os.environ.get("ALPACA_KEY") or os.environ.get("ALPACA__KEY") or ""
        )
        self._secret_key = (
            secret_key or os.environ.get("ALPACA_SECRET") or os.environ.get("ALPACA__SECRET") or ""
        )
        self._client: StockHistoricalDataClient | None = None
        self._cache: dict[str, BarModel] = {}

        logger.info("LiveBarProvider initialized")

    def _get_client(self) -> StockHistoricalDataClient:
        """Lazy-load Alpaca data client."""
        if self._client is None:
            from alpaca.data.historical import StockHistoricalDataClient

            self._client = StockHistoricalDataClient(self._api_key, self._secret_key)
            logger.debug("Alpaca data client initialized for live bars")
        return self._client

    def get_todays_bar(self, symbol: str) -> BarModel | None:
        """Fetch today's bar for a symbol using Alpaca Snapshot API.

        Returns the current day's OHLCV bar with:
        - open: Today's opening price
        - high: Today's high (so far)
        - low: Today's low (so far)
        - close: Current/latest price
        - volume: Today's cumulative volume

        Args:
            symbol: Stock ticker symbol (e.g., "SPY", "AAPL")

        Returns:
            BarModel with today's data, or None if unavailable

        """
        # Check cache first
        if symbol in self._cache:
            logger.debug(
                "Returning cached live bar",
                symbol=symbol,
            )
            return self._cache[symbol]

        try:
            from alpaca.data.requests import StockSnapshotRequest

            client = self._get_client()
            # Normalize symbol for Alpaca API (e.g., BRK/B -> BRK.B)
            api_symbol = normalize_symbol_for_alpaca(symbol)
            request = StockSnapshotRequest(symbol_or_symbols=[api_symbol])
            snapshots = client.get_stock_snapshot(request)

            snapshot = snapshots.get(api_symbol)
            if not snapshot:
                logger.warning(
                    "No snapshot data for symbol",
                    symbol=symbol,
                    api_symbol=api_symbol,
                )
                return None

            # Get today's daily bar from snapshot
            daily_bar = snapshot.daily_bar
            if not daily_bar:
                logger.warning(
                    "No daily bar in snapshot",
                    symbol=symbol,
                )
                return None

            # Construct BarModel from snapshot daily_bar
            # Mark as incomplete since this is today's partial bar (close-so-far)
            bar = BarModel(
                symbol=symbol,
                timestamp=datetime.now(UTC),  # Mark as current time
                open=Decimal(str(daily_bar.open)),
                high=Decimal(str(daily_bar.high)),
                low=Decimal(str(daily_bar.low)),
                close=Decimal(str(daily_bar.close)),
                volume=int(daily_bar.volume),
                is_incomplete=True,  # Partial bar: today's data is not yet complete
            )

            # Cache for subsequent calls
            self._cache[symbol] = bar

            logger.info(
                "Fetched live bar from Alpaca snapshot",
                symbol=symbol,
                close=float(bar.close),
                volume=bar.volume,
            )

            return bar

        except Exception as e:
            logger.error(
                "Failed to fetch live bar",
                symbol=symbol,
                error=str(e),
                error_type=type(e).__name__,
            )
            return None

    def get_todays_bars_bulk(self, symbols: list[str]) -> dict[str, BarModel]:
        """Fetch today's bars for multiple symbols in a single API call.

        More efficient than calling get_todays_bar() for each symbol when
        fetching data for multiple symbols.

        Args:
            symbols: List of stock ticker symbols

        Returns:
            Dictionary mapping symbol to BarModel (missing symbols excluded)

        """
        # Separate cached and uncached symbols
        results: dict[str, BarModel] = {}
        uncached_symbols: list[str] = []

        for symbol in symbols:
            if symbol in self._cache:
                results[symbol] = self._cache[symbol]
            else:
                uncached_symbols.append(symbol)

        if not uncached_symbols:
            logger.debug(
                "All symbols found in cache",
                symbol_count=len(symbols),
            )
            return results

        try:
            from alpaca.data.requests import StockSnapshotRequest

            client = self._get_client()
            # Normalize symbols for Alpaca API (e.g., BRK/B -> BRK.B)
            # Create mapping from API symbol back to original symbol
            api_to_original: dict[str, str] = {
                normalize_symbol_for_alpaca(s): s for s in uncached_symbols
            }
            api_symbols = list(api_to_original.keys())

            request = StockSnapshotRequest(symbol_or_symbols=api_symbols)
            snapshots = client.get_stock_snapshot(request)

            now = datetime.now(UTC)

            for api_symbol, original_symbol in api_to_original.items():
                snapshot = snapshots.get(api_symbol)
                if not snapshot or not snapshot.daily_bar:
                    logger.warning(
                        "No daily bar in snapshot for symbol",
                        symbol=original_symbol,
                        api_symbol=api_symbol,
                    )
                    continue

                daily_bar = snapshot.daily_bar
                bar = BarModel(
                    symbol=original_symbol,  # Use original symbol in BarModel
                    timestamp=now,
                    open=Decimal(str(daily_bar.open)),
                    high=Decimal(str(daily_bar.high)),
                    low=Decimal(str(daily_bar.low)),
                    close=Decimal(str(daily_bar.close)),
                    volume=int(daily_bar.volume),
                    is_incomplete=True,  # Partial bar: today's data is not yet complete
                )

                self._cache[original_symbol] = bar
                results[original_symbol] = bar

            logger.info(
                "Bulk fetched live bars from Alpaca",
                requested=len(uncached_symbols),
                fetched=len(results) - (len(symbols) - len(uncached_symbols)),
            )

            return results

        except Exception as e:
            logger.error(
                "Failed to bulk fetch live bars",
                symbols=uncached_symbols,
                error=str(e),
                error_type=type(e).__name__,
            )
            return results

    def clear_cache(self) -> None:
        """Clear the in-memory bar cache.

        Call this at the start of a new strategy run to ensure fresh data.

        """
        self._cache.clear()
        logger.debug("Live bar cache cleared")

    def get_cache_stats(self) -> dict[str, int]:
        """Get cache statistics.

        Returns:
            Dictionary with cache_size count

        """
        return {"cache_size": len(self._cache)}
