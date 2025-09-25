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

import threading
import time
from typing import TYPE_CHECKING, Any

from the_alchemiser.shared.dto.asset_info_dto import AssetInfoDTO
from the_alchemiser.shared.logging.logging_utils import get_logger

if TYPE_CHECKING:
    from alpaca.trading.client import TradingClient

logger = get_logger(__name__)


class AssetMetadataService:
    """Service for asset metadata management with caching.

    This service handles asset metadata operations with thread-safe caching,
    providing a centralized interface for asset information retrieval.
    """

    def __init__(self, trading_client: TradingClient, *, asset_cache_ttl: float = 300.0) -> None:
        """Initialize the asset metadata service.

        Args:
            trading_client: Alpaca TradingClient instance for API access
            asset_cache_ttl: Cache TTL in seconds (default: 5 minutes)

        """
        self._trading_client = trading_client
        self._asset_cache: dict[str, AssetInfoDTO] = {}
        self._asset_cache_timestamps: dict[str, float] = {}
        self._asset_cache_ttl = asset_cache_ttl
        self._asset_cache_lock = threading.Lock()

    def get_asset_info(self, symbol: str) -> AssetInfoDTO | None:
        """Get asset information with caching.

        Args:
            symbol: Stock symbol

        Returns:
            AssetInfoDTO with asset metadata, or None if not found.

        """
        symbol_upper = symbol.upper()
        current_time = time.time()

        # Check cache first
        with self._asset_cache_lock:
            if symbol_upper in self._asset_cache:
                cache_time = self._asset_cache_timestamps.get(symbol_upper, 0)
                if current_time - cache_time < self._asset_cache_ttl:
                    logger.debug(f"📋 Asset cache hit for {symbol_upper}")
                    return self._asset_cache[symbol_upper]
                # Cache expired, remove
                self._asset_cache.pop(symbol_upper, None)
                self._asset_cache_timestamps.pop(symbol_upper, None)
                logger.debug(f"🗑️ Asset cache expired for {symbol_upper}")

        try:
            asset = self._trading_client.get_asset(symbol_upper)

            # Convert SDK object to DTO at adapter boundary
            asset_dto = AssetInfoDTO(
                symbol=getattr(asset, "symbol", symbol_upper),
                name=getattr(asset, "name", None),
                exchange=getattr(asset, "exchange", None),
                asset_class=getattr(asset, "asset_class", None),
                tradable=getattr(asset, "tradable", True),
                fractionable=getattr(asset, "fractionable", True),
                marginable=getattr(asset, "marginable", None),
                shortable=getattr(asset, "shortable", None),
            )

            # Cache the result
            with self._asset_cache_lock:
                self._asset_cache[symbol_upper] = asset_dto
                self._asset_cache_timestamps[symbol_upper] = current_time

            logger.debug(
                f"🏷️ Asset info retrieved for {symbol_upper}: "
                f"fractionable={asset_dto.fractionable}, "
                f"tradable={asset_dto.tradable}"
            )
            return asset_dto

        except Exception as e:
            logger.error(f"Failed to get asset info for {symbol_upper}: {e}")
            return None

    def is_fractionable(self, symbol: str) -> bool:
        """Check if an asset supports fractional shares.

        Args:
            symbol: Stock symbol to check

        Returns:
            True if asset supports fractional shares, False otherwise.
            Defaults to True if asset info cannot be retrieved.

        """
        asset_info = self.get_asset_info(symbol)
        if asset_info is None:
            logger.warning(f"Could not determine fractionability for {symbol}, defaulting to True")
            return True
        return asset_info.fractionable

    def is_market_open(self) -> bool:
        """Check if the market is currently open.

        Returns:
            True if market is open, False otherwise.

        """
        try:
            clock = self._trading_client.get_clock()
            return getattr(clock, "is_open", False)
        except Exception as e:
            logger.error(f"Failed to get market status: {e}")
            return False

    def get_market_calendar(self, _start_date: str, _end_date: str) -> list[dict[str, Any]]:
        """Get market calendar information.

        Args:
            _start_date: Start date (ISO format) - currently unused
            _end_date: End date (ISO format) - currently unused

        Returns:
            List of market calendar entries.

        """
        try:
            # Some stubs may not accept start/end; fetch without filters
            calendar = self._trading_client.get_calendar()
            # Convert to list of dictionaries
            return [
                {
                    "date": str(getattr(day, "date", "")),
                    "open": str(getattr(day, "open", "")),
                    "close": str(getattr(day, "close", "")),
                }
                for day in calendar
            ]
        except Exception as e:
            logger.error(f"Failed to get market calendar: {e}")
            return []

    def clear_cache(self) -> None:
        """Clear asset metadata cache."""
        with self._asset_cache_lock:
            self._asset_cache.clear()
            self._asset_cache_timestamps.clear()
            logger.info("🧹 Asset metadata cache cleared")

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics for monitoring.

        Returns:
            Dictionary with cache statistics.

        """
        with self._asset_cache_lock:
            current_time = time.time()
            expired_count = sum(
                1
                for symbol, cache_time in self._asset_cache_timestamps.items()
                if current_time - cache_time >= self._asset_cache_ttl
            )

            return {
                "total_cached": len(self._asset_cache),
                "expired_entries": expired_count,
                "cache_ttl": self._asset_cache_ttl,
                "cache_hit_ratio": "N/A",  # Would need hit/miss counters for full stats
            }
