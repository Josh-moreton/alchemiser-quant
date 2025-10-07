"""Business Unit: shared; Status: current.

Asset Metadata Service.

This service manages asset metadata caching and retrieval operations,
extracting asset-related responsibilities from AlpacaManager to provide
a dedicated service for asset information management.

Key Features:
- Asset metadata caching with configurable TTL
- Thread-safe cache operations
- Fractionability checks
- Market status and calendar information
- Cache statistics and monitoring
"""

from __future__ import annotations

import re
import threading
import time
from typing import TYPE_CHECKING, Any, TypedDict

from the_alchemiser.shared.errors.exceptions import (
    DataProviderError,
    TradingClientError,
    ValidationError,
)
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.asset_info import AssetInfo

if TYPE_CHECKING:
    from alpaca.trading.client import TradingClient

logger = get_logger(__name__)


class CacheStats(TypedDict):
    """Type definition for cache statistics."""

    total_cached: int
    expired_entries: int
    cache_ttl: float
    cache_hits: int
    cache_misses: int
    cache_hit_ratio: float


class AssetMetadataService:
    """Service for asset metadata management with caching.

    This service handles asset metadata operations with thread-safe caching,
    providing a centralized interface for asset information retrieval.
    """

    # Valid symbol pattern: alphanumeric, dots, hyphens
    SYMBOL_PATTERN = re.compile(r"^[A-Z0-9.\-]+$")
    API_TIMEOUT = 10.0  # Timeout for API calls in seconds

    def __init__(
        self,
        trading_client: TradingClient,
        *,
        asset_cache_ttl: float = 300.0,
        max_cache_size: int = 1000,
    ) -> None:
        """Initialize the asset metadata service.

        Args:
            trading_client: Alpaca TradingClient instance for API access
            asset_cache_ttl: Cache TTL in seconds (default: 5 minutes)
            max_cache_size: Maximum number of cached entries (default: 1000)

        Raises:
            ValidationError: If parameters are invalid

        """
        if not trading_client:
            raise ValidationError("trading_client cannot be None", field_name="trading_client")
        if asset_cache_ttl <= 0:
            raise ValidationError(
                "asset_cache_ttl must be positive",
                field_name="asset_cache_ttl",
                value=asset_cache_ttl,
            )
        if max_cache_size <= 0:
            raise ValidationError(
                "max_cache_size must be positive",
                field_name="max_cache_size",
                value=max_cache_size,
            )

        self._trading_client = trading_client
        self._asset_cache: dict[str, AssetInfo] = {}
        self._asset_cache_timestamps: dict[str, float] = {}
        self._asset_cache_ttl = asset_cache_ttl
        self._max_cache_size = max_cache_size
        self._asset_cache_lock = threading.Lock()
        
        # Metrics
        self._cache_hits = 0
        self._cache_misses = 0

    def _validate_symbol(self, symbol: str) -> str:
        """Validate and normalize symbol.

        Args:
            symbol: Stock symbol to validate

        Returns:
            Normalized symbol (uppercase, stripped)

        Raises:
            ValidationError: If symbol is invalid

        """
        if not symbol or not symbol.strip():
            raise ValidationError("Symbol cannot be empty", field_name="symbol", value=symbol)

        symbol_upper = symbol.strip().upper()

        if not self.SYMBOL_PATTERN.match(symbol_upper):
            raise ValidationError(
                f"Invalid symbol format: {symbol}",
                field_name="symbol",
                value=symbol,
            )

        return symbol_upper

    def _evict_lru_if_needed(self) -> None:
        """Evict least recently used cache entry if cache is full.
        
        Must be called within cache lock.
        """
        if len(self._asset_cache) >= self._max_cache_size:
            # Find oldest entry
            oldest_symbol = min(
                self._asset_cache_timestamps,
                key=self._asset_cache_timestamps.get,  # type: ignore
            )
            self._asset_cache.pop(oldest_symbol, None)
            self._asset_cache_timestamps.pop(oldest_symbol, None)
            logger.debug(
                "Cache LRU eviction",
                evicted_symbol=oldest_symbol,
                cache_size=len(self._asset_cache),
            )

    def get_asset_info(
        self, symbol: str, *, correlation_id: str | None = None
    ) -> AssetInfo | None:
        """Get asset information with caching.

        Args:
            symbol: Stock symbol
            correlation_id: Optional correlation ID for tracing

        Returns:
            AssetInfo with asset metadata, or None if not found.

        Raises:
            ValidationError: If symbol is invalid
            DataProviderError: If asset data is incomplete or API fails
            TradingClientError: If API call fails

        """
        symbol_upper = self._validate_symbol(symbol)
        
        log_context = {"symbol": symbol_upper}
        if correlation_id:
            log_context["correlation_id"] = correlation_id

        # Check cache first (outside lock for read)
        with self._asset_cache_lock:
            if symbol_upper in self._asset_cache:
                cache_time = self._asset_cache_timestamps.get(symbol_upper, 0)
                current_time = time.time()
                if current_time - cache_time < self._asset_cache_ttl:
                    self._cache_hits += 1
                    logger.debug("Asset cache hit", **log_context)
                    return self._asset_cache[symbol_upper]
                # Cache expired, remove
                self._asset_cache.pop(symbol_upper, None)
                self._asset_cache_timestamps.pop(symbol_upper, None)
                logger.debug("Asset cache expired", **log_context)

        # Cache miss - fetch from API
        self._cache_misses += 1
        logger.debug("Asset cache miss, fetching from API", **log_context)

        try:
            # TODO: Add timeout wrapper when available
            asset = self._trading_client.get_asset(symbol_upper)

            # Validate required fields exist
            if not hasattr(asset, "fractionable"):
                raise DataProviderError(
                    f"Asset data missing required field: fractionable for {symbol_upper}",
                    context={"symbol": symbol_upper, "available_fields": dir(asset)},
                )
            if not hasattr(asset, "tradable"):
                raise DataProviderError(
                    f"Asset data missing required field: tradable for {symbol_upper}",
                    context={"symbol": symbol_upper, "available_fields": dir(asset)},
                )

            # Convert SDK object to DTO at adapter boundary
            asset_info = AssetInfo(
                symbol=getattr(asset, "symbol", symbol_upper),
                name=getattr(asset, "name", None),
                exchange=getattr(asset, "exchange", None),
                asset_class=getattr(asset, "asset_class", None),
                tradable=asset.tradable,  # Required field, no default
                fractionable=asset.fractionable,  # Required field, no default
                marginable=getattr(asset, "marginable", None),
                shortable=getattr(asset, "shortable", None),
            )

            # Cache the result with fresh timestamp
            with self._asset_cache_lock:
                # Double-check: another thread might have updated cache
                if symbol_upper not in self._asset_cache:
                    self._evict_lru_if_needed()
                    self._asset_cache[symbol_upper] = asset_info
                    self._asset_cache_timestamps[symbol_upper] = time.time()

            logger.debug(
                "Asset info retrieved",
                symbol=symbol_upper,
                fractionable=asset_info.fractionable,
                tradable=asset_info.tradable,
                exchange=asset_info.exchange,
                **({} if not correlation_id else {"correlation_id": correlation_id}),
            )
            return asset_info

        except AttributeError as e:
            # Likely missing required field
            error_msg = f"Asset data structure invalid for {symbol_upper}: {e}"
            logger.error(
                "Asset data validation failed",
                symbol=symbol_upper,
                error=str(e),
                error_type="AttributeError",
                **log_context,
            )
            raise DataProviderError(error_msg, context={"symbol": symbol_upper}) from e

        except Exception as e:
            # Catch API errors and re-raise as appropriate typed exception
            error_msg = f"Failed to retrieve asset info for {symbol_upper}"
            logger.error(
                "Asset metadata retrieval failed",
                symbol=symbol_upper,
                error=str(e),
                error_type=type(e).__name__,
                **log_context,
            )
            
            # Check if it's a not found case
            if "not found" in str(e).lower() or "404" in str(e):
                # Asset doesn't exist - return None
                logger.info("Asset not found", symbol=symbol_upper, **log_context)
                return None
            
            # Re-raise as TradingClientError with context
            raise TradingClientError(error_msg) from e

    def is_fractionable(self, symbol: str, *, correlation_id: str | None = None) -> bool:
        """Check if an asset supports fractional shares.

        Args:
            symbol: Stock symbol to check
            correlation_id: Optional correlation ID for tracing

        Returns:
            True if asset supports fractional shares, False otherwise.

        Raises:
            ValidationError: If symbol is invalid
            DataProviderError: If asset info cannot be retrieved
            TradingClientError: If API call fails

        """
        log_context = {"symbol": symbol}
        if correlation_id:
            log_context["correlation_id"] = correlation_id

        asset_info = self.get_asset_info(symbol, correlation_id=correlation_id)
        
        if asset_info is None:
            # Asset not found - this is a critical path, don't default to True
            error_msg = f"Cannot determine fractionability for {symbol}: asset not found"
            logger.error("Asset not found for fractionability check", **log_context)
            raise DataProviderError(
                error_msg,
                context={"symbol": symbol, "operation": "fractionability_check"},
            )
        
        return asset_info.fractionable

    def is_market_open(self, *, correlation_id: str | None = None) -> bool:
        """Check if the market is currently open.

        Args:
            correlation_id: Optional correlation ID for tracing

        Returns:
            True if market is open, False otherwise.

        Raises:
            TradingClientError: If API call fails

        """
        log_context = {}
        if correlation_id:
            log_context["correlation_id"] = correlation_id

        try:
            # TODO: Add timeout wrapper when available
            clock = self._trading_client.get_clock()
            is_open = getattr(clock, "is_open", False)
            
            logger.debug(
                "Market status checked",
                is_open=is_open,
                **log_context,
            )
            return is_open

        except Exception as e:
            error_msg = "Failed to get market status"
            logger.error(
                "Market status check failed",
                error=str(e),
                error_type=type(e).__name__,
                **log_context,
            )
            raise TradingClientError(error_msg) from e

    def get_market_calendar(self, *, correlation_id: str | None = None) -> list[dict[str, Any]]:
        """Get market calendar information.

        Args:
            correlation_id: Optional correlation ID for tracing

        Returns:
            List of market calendar entries.

        Raises:
            TradingClientError: If API call fails

        Note:
            Alpaca API returns all calendar data without date filtering support.

        """
        log_context = {}
        if correlation_id:
            log_context["correlation_id"] = correlation_id

        try:
            # TODO: Add timeout wrapper when available
            # Note: Alpaca API may not support date filtering
            calendar = self._trading_client.get_calendar()
            
            # Convert to list of dictionaries
            result = [
                {
                    "date": str(getattr(day, "date", "")),
                    "open": str(getattr(day, "open", "")),
                    "close": str(getattr(day, "close", "")),
                }
                for day in calendar
            ]
            
            logger.debug(
                "Market calendar retrieved",
                entries_count=len(result),
                **log_context,
            )
            return result

        except Exception as e:
            error_msg = "Failed to get market calendar"
            logger.error(
                "Market calendar retrieval failed",
                error=str(e),
                error_type=type(e).__name__,
                **log_context,
            )
            raise TradingClientError(error_msg) from e

    def clear_cache(self) -> None:
        """Clear asset metadata cache."""
        with self._asset_cache_lock:
            cache_size_before = len(self._asset_cache)
            self._asset_cache.clear()
            self._asset_cache_timestamps.clear()
            logger.info(
                "Asset metadata cache cleared",
                entries_cleared=cache_size_before,
            )

    def get_cache_stats(self) -> CacheStats:
        """Get cache statistics for monitoring.

        Returns:
            Dictionary with cache statistics including hit ratio.

        """
        with self._asset_cache_lock:
            current_time = time.time()
            expired_count = sum(
                1
                for symbol, cache_time in self._asset_cache_timestamps.items()
                if current_time - cache_time >= self._asset_cache_ttl
            )

            total_requests = self._cache_hits + self._cache_misses
            hit_ratio = (
                self._cache_hits / total_requests if total_requests > 0 else 0.0
            )

            return CacheStats(
                total_cached=len(self._asset_cache),
                expired_entries=expired_count,
                cache_ttl=self._asset_cache_ttl,
                cache_hits=self._cache_hits,
                cache_misses=self._cache_misses,
                cache_hit_ratio=hit_ratio,
            )
