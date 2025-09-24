"""Business Unit: shared | Status: current.

Alpaca asset metadata cache with TTL support.

This module provides a broker-scoped asset metadata cache that stores
asset information with time-to-live expiration. It's specifically designed
for Alpaca asset metadata caching needs.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

from alpaca.trading.client import TradingClient

from the_alchemiser.shared.dto.asset_info_dto import AssetInfoDTO

logger = logging.getLogger(__name__)


class AlpacaAssetCache:
    """Alpaca-specific asset metadata cache with TTL support.
    
    Provides thread-safe caching of asset information with automatic
    expiration based on configurable time-to-live values.
    """

    def __init__(
        self,
        trading_client: TradingClient,
        ttl_seconds: float = 300.0,  # 5 minutes default TTL
    ) -> None:
        """Initialize the asset cache.
        
        Args:
            trading_client: Alpaca TradingClient for asset queries
            ttl_seconds: Time-to-live in seconds for cached entries
        """
        self._trading_client = trading_client
        self._ttl_seconds = ttl_seconds
        
        # Thread-safe cache storage
        self._asset_cache: dict[str, AssetInfoDTO] = {}
        self._asset_cache_timestamps: dict[str, float] = {}
        self._cache_lock = threading.Lock()
        
        logger.info(f"AlpacaAssetCache initialized with TTL={ttl_seconds}s")

    def get_asset_info(self, symbol: str) -> AssetInfoDTO | None:
        """Get asset information with caching.
        
        Args:
            symbol: Stock symbol to get asset info for
            
        Returns:
            AssetInfoDTO if found, None if not available
        """
        # Check cache first
        cached_asset = self._get_cached_asset(symbol)
        if cached_asset is not None:
            return cached_asset
            
        # Cache miss - fetch from API
        return self._fetch_and_cache_asset(symbol)

    def _get_cached_asset(self, symbol: str) -> AssetInfoDTO | None:
        """Get asset from cache if not expired."""
        with self._cache_lock:
            if symbol not in self._asset_cache:
                return None
                
            # Check if cache entry is still valid
            timestamp = self._asset_cache_timestamps.get(symbol, 0.0)
            if time.time() - timestamp > self._ttl_seconds:
                # Cache expired, remove entry
                self._asset_cache.pop(symbol, None)
                self._asset_cache_timestamps.pop(symbol, None)
                logger.debug(f"Cache expired for asset {symbol}")
                return None
                
            logger.debug(f"Cache hit for asset {symbol}")
            return self._asset_cache[symbol]

    def _fetch_and_cache_asset(self, symbol: str) -> AssetInfoDTO | None:
        """Fetch asset from API and cache the result."""
        try:
            # Fetch from Alpaca API
            asset = self._trading_client.get_asset(symbol)
            if not asset:
                logger.warning(f"No asset information found for {symbol}")
                return None
                
            # Convert to DTO
            asset_dto = self._convert_asset_to_dto(asset, symbol)
            
            # Cache the result
            with self._cache_lock:
                self._asset_cache[symbol] = asset_dto
                self._asset_cache_timestamps[symbol] = time.time()
                
            logger.debug(f"Cached asset info for {symbol}")
            return asset_dto
            
        except Exception as e:
            logger.error(f"Failed to fetch asset info for {symbol}: {e}")
            return None

    def _convert_asset_to_dto(self, asset: Any, symbol: str) -> AssetInfoDTO:
        """Convert Alpaca asset object to AssetInfoDTO.
        
        Args:
            asset: Alpaca asset object
            symbol: Stock symbol
            
        Returns:
            AssetInfoDTO with extracted information
        """
        try:
            return AssetInfoDTO(
                symbol=symbol,
                name=getattr(asset, "name", None),
                asset_class=getattr(asset, "class", None),
                exchange=getattr(asset, "exchange", None),
                status=getattr(asset, "status", None),
                tradable=getattr(asset, "tradable", False),
                marginable=getattr(asset, "marginable", False),
                shortable=getattr(asset, "shortable", False),
                easy_to_borrow=getattr(asset, "easy_to_borrow", False),
                fractionable=getattr(asset, "fractionable", False),
            )
        except Exception as e:
            logger.warning(f"Failed to convert asset to DTO for {symbol}: {e}")
            # Return minimal DTO with known symbol
            return AssetInfoDTO(
                symbol=symbol,
                name=None,
                asset_class=None,
                exchange=None,
                status=None,
                tradable=False,
                marginable=False,
                shortable=False,
                easy_to_borrow=False,
                fractionable=False,
            )

    def is_fractionable(self, symbol: str) -> bool:
        """Check if asset is fractionable.
        
        Args:
            symbol: Stock symbol to check
            
        Returns:
            True if asset is fractionable, False otherwise
        """
        asset_info = self.get_asset_info(symbol)
        return asset_info.fractionable if asset_info else False

    def clear_cache(self) -> None:
        """Clear all cached asset information."""
        with self._cache_lock:
            count = len(self._asset_cache)
            self._asset_cache.clear()
            self._asset_cache_timestamps.clear()
            logger.info(f"Cleared {count} cached asset entries")

    def cache_stats(self) -> dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        with self._cache_lock:
            current_time = time.time()
            expired_count = sum(
                1 for timestamp in self._asset_cache_timestamps.values()
                if current_time - timestamp > self._ttl_seconds
            )
            
            return {
                "total_entries": len(self._asset_cache),
                "expired_entries": expired_count,
                "valid_entries": len(self._asset_cache) - expired_count,
                "ttl_seconds": self._ttl_seconds,
            }

    def cleanup_expired(self) -> int:
        """Remove expired entries from cache.
        
        Returns:
            Number of expired entries removed
        """
        with self._cache_lock:
            current_time = time.time()
            expired_symbols = [
                symbol for symbol, timestamp in self._asset_cache_timestamps.items()
                if current_time - timestamp > self._ttl_seconds
            ]
            
            for symbol in expired_symbols:
                self._asset_cache.pop(symbol, None)
                self._asset_cache_timestamps.pop(symbol, None)
                
            if expired_symbols:
                logger.debug(f"Cleaned up {len(expired_symbols)} expired cache entries")
                
            return len(expired_symbols)