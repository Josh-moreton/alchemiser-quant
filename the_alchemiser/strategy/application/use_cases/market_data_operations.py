"""Business Unit: strategy & signal generation | Status: current.

Market data operations use case for strategy context.

Provides intelligent market data operations with caching, validation, and batch
processing capabilities to support strategy signal generation.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pandas as pd

from the_alchemiser.anti_corruption.market_data.domain_mappers import bars_to_domain
from the_alchemiser.domain.interfaces import MarketDataRepository
from the_alchemiser.domain.market_data.models.bar import BarModel
from the_alchemiser.domain.market_data.models.quote import QuoteModel
from the_alchemiser.infrastructure.error_handling.decorators import translate_market_data_errors
from the_alchemiser.shared_kernel.value_objects.symbol import Symbol

logger = logging.getLogger(__name__)


class MarketDataOperations:
    """Market data operations use case for strategy context.

    This service provides high-level market data operations built on top of
    the MarketDataRepository interface, adding intelligent caching, validation,
    and batch processing capabilities for strategy needs.
    """

    def __init__(
        self,
        market_data_repo: MarketDataRepository,
        cache_ttl_seconds: int = 5,
        enable_validation: bool = True,
    ) -> None:
        """Initialize the market data operations.

        Args:
            market_data_repo: Repository for market data operations
            cache_ttl_seconds: Cache time-to-live in seconds
            enable_validation: Whether to enable data validation

        """
        self.market_data_repo = market_data_repo
        self.cache_ttl_seconds = cache_ttl_seconds
        self.enable_validation = enable_validation
        self.logger = logging.getLogger(__name__)

        # Simple in-memory cache
        self._cache: dict[str, tuple[datetime, Any]] = {}

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid."""
        if cache_key not in self._cache:
            return False
        cached_time, _ = self._cache[cache_key]
        return (datetime.now(UTC) - cached_time).total_seconds() < self.cache_ttl_seconds

    def _get_from_cache(self, cache_key: str) -> Any:
        """Get data from cache if valid."""
        if self._is_cache_valid(cache_key):
            _, data = self._cache[cache_key]
            return data
        return None

    def _cache_data(self, cache_key: str, data: Any) -> None:
        """Cache data with timestamp."""
        self._cache[cache_key] = (datetime.now(UTC), data)

    @translate_market_data_errors
    def get_bars(
        self,
        symbol: Symbol,
        start: datetime,
        end: datetime,
        timeframe: str = "1Day",
    ) -> list[BarModel]:
        """Get market bars for a symbol within a date range.

        Args:
            symbol: Symbol to fetch bars for
            start: Start datetime
            end: End datetime
            timeframe: Timeframe for bars

        Returns:
            List of BarModel objects

        """
        cache_key = f"bars_{symbol.value}_{start.isoformat()}_{end.isoformat()}_{timeframe}"

        # Check cache first
        cached_data = self._get_from_cache(cache_key)
        if cached_data is not None:
            return cached_data

        # Fetch from repository
        raw_bars = self.market_data_repo.get_historical_bars(symbol.value, start, end, timeframe)

        # Convert to domain models
        bars = bars_to_domain(raw_bars)

        # Validate if enabled
        if self.enable_validation:
            bars = self._validate_bars(bars)

        # Cache the result
        self._cache_data(cache_key, bars)

        return bars

    @translate_market_data_errors
    def get_latest_quote(self, symbol: Symbol) -> QuoteModel:
        """Get latest quote for a symbol.

        Args:
            symbol: Symbol to fetch quote for

        Returns:
            QuoteModel with latest quote data

        """
        cache_key = f"quote_{symbol.value}"

        # For quotes, use shorter cache TTL
        cached_data = self._get_from_cache(cache_key) if self.cache_ttl_seconds > 1 else None
        if cached_data is not None:
            return cached_data

        # Fetch from repository
        raw_quote = self.market_data_repo.get_latest_quote(symbol.value)

        # Convert to domain model
        quote = QuoteModel(
            symbol=symbol,
            bid_price=Decimal(str(raw_quote.get("bid_price", 0))),
            ask_price=Decimal(str(raw_quote.get("ask_price", 0))),
            bid_size=int(raw_quote.get("bid_size", 0)),
            ask_size=int(raw_quote.get("ask_size", 0)),
            timestamp=raw_quote.get("timestamp", datetime.now(UTC)),
        )

        # Cache the result
        self._cache_data(cache_key, quote)

        return quote

    @translate_market_data_errors
    def get_mid_price(self, symbol: Symbol) -> Decimal:
        """Get mid price for a symbol.

        Args:
            symbol: Symbol to get mid price for

        Returns:
            Mid price as Decimal

        """
        quote = self.get_latest_quote(symbol)
        return (quote.bid_price + quote.ask_price) / Decimal("2")

    def get_current_prices(self, symbols: list[str]) -> dict[str, float]:
        """Get current prices for multiple symbols.

        Args:
            symbols: List of symbol strings

        Returns:
            Dictionary mapping symbols to current prices

        """
        prices = {}
        for symbol_str in symbols:
            try:
                symbol = Symbol(symbol_str)
                quote = self.get_latest_quote(symbol)
                mid_price = (quote.bid_price + quote.ask_price) / Decimal("2")
                prices[symbol_str] = float(mid_price)
            except Exception as e:
                self.logger.warning(f"Failed to get price for {symbol_str}: {e}")
                prices[symbol_str] = 0.0

        return prices

    def get_historical_data_dataframe(
        self,
        symbol: str,
        period: str = "1y",
        interval: str = "1d",
    ) -> pd.DataFrame:
        """Get historical data as DataFrame for backward compatibility.

        Args:
            symbol: Symbol string
            period: Time period
            interval: Data interval

        Returns:
            DataFrame with historical data

        """
        # Convert period to datetime range
        end_time = datetime.now(UTC)
        if period == "1y":
            start_time = end_time - timedelta(days=365)
        elif period == "6mo":
            start_time = end_time - timedelta(days=180)
        elif period == "3mo":
            start_time = end_time - timedelta(days=90)
        elif period == "1mo":
            start_time = end_time - timedelta(days=30)
        else:
            start_time = end_time - timedelta(days=365)  # default to 1 year

        symbol_obj = Symbol(symbol)
        bars = self.get_bars(symbol_obj, start_time, end_time, interval)

        # Convert to DataFrame
        data = []
        for bar in bars:
            data.append(
                {
                    "timestamp": bar.timestamp,
                    "open": float(bar.open_price),
                    "high": float(bar.high_price),
                    "low": float(bar.low_price),
                    "close": float(bar.close_price),
                    "volume": bar.volume,
                }
            )

        df = pd.DataFrame(data)
        if not df.empty:
            df.set_index("timestamp", inplace=True)

        return df

    def _validate_bars(self, bars: list[BarModel]) -> list[BarModel]:
        """Validate and filter bar data."""
        if not self.enable_validation:
            return bars

        valid_bars = []
        for bar in bars:
            # Basic validation checks
            if (
                bar.open_price > 0
                and bar.high_price > 0
                and bar.low_price > 0
                and bar.close_price > 0
                and bar.volume >= 0
                and bar.high_price >= bar.low_price
                and bar.high_price >= bar.open_price
                and bar.high_price >= bar.close_price
                and bar.low_price <= bar.open_price
                and bar.low_price <= bar.close_price
            ):
                valid_bars.append(bar)
            else:
                self.logger.warning(
                    f"Invalid bar data for {bar.symbol}: "
                    f"O={bar.open_price} H={bar.high_price} L={bar.low_price} C={bar.close_price} V={bar.volume}"
                )

        return valid_bars

    def clear_cache(self) -> None:
        """Clear the market data cache."""
        self._cache.clear()
        self.logger.info("Market data cache cleared")

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        now = datetime.now(UTC)
        valid_entries = 0
        expired_entries = 0

        for cache_key, (cached_time, _) in self._cache.items():
            if (now - cached_time).total_seconds() < self.cache_ttl_seconds:
                valid_entries += 1
            else:
                expired_entries += 1

        return {
            "total_entries": len(self._cache),
            "valid_entries": valid_entries,
            "expired_entries": expired_entries,
            "cache_ttl_seconds": self.cache_ttl_seconds,
        }
