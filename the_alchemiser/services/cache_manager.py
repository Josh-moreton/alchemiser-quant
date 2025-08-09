"""
Cache management service with TTL support.

Provides configurable caching with time-to-live per data type.
"""

import logging
import time
from typing import Any, Generic, TypeVar

from cachetools import TTLCache

from the_alchemiser.services.config_service import ConfigService

T = TypeVar("T")


class CacheManager(Generic[T]):
    """Generic cache manager with TTL support."""

    def __init__(
        self,
        maxsize: int = 1000,
        default_ttl: int = 3600,
        config_service: ConfigService | None = None,
    ) -> None:
        """
        Initialize cache manager.

        Args:
            maxsize: Maximum number of items in cache
            default_ttl: Default time-to-live in seconds
            config_service: Configuration service for TTL overrides
        """
        self._cache: TTLCache[str, tuple[float, T]] = TTLCache(maxsize=maxsize, ttl=default_ttl)
        self._default_ttl = default_ttl
        self._config_service = config_service

        # Data type specific TTL overrides
        self._ttl_overrides: dict[str, int] = {
            "historical_data": self._get_ttl_from_config("historical_data", 3600),
            "current_price": self._get_ttl_from_config("current_price", 30),
            "account_info": self._get_ttl_from_config("account_info", 60),
            "positions": self._get_ttl_from_config("positions", 60),
            "quotes": self._get_ttl_from_config("quotes", 10),
        }

        logging.debug(
            f"Initialized CacheManager with {maxsize} max items, {default_ttl}s default TTL"
        )

    def _get_ttl_from_config(self, data_type: str, default: int) -> int:
        """Get TTL from config or use default."""
        if self._config_service:
            # Could extend ConfigService to support cache-specific settings
            return getattr(self._config_service.config.data, f"{data_type}_cache_ttl", default)
        return default

    def get(self, key: str, data_type: str = "default") -> T | None:
        """
        Get item from cache if not expired.

        Args:
            key: Cache key
            data_type: Type of data for TTL selection

        Returns:
            Cached item or None if not found/expired
        """
        cache_key = f"{data_type}:{key}"
        try:
            cached_time, data = self._cache[cache_key]
            ttl = self._ttl_overrides.get(data_type, self._default_ttl)

            if time.time() - cached_time < ttl:
                logging.debug(f"Cache hit for {cache_key}")
                return data  # type: ignore[no-any-return]
            else:
                # Item expired, remove it
                del self._cache[cache_key]
                logging.debug(f"Cache expired for {cache_key}")
                return None
        except KeyError:
            logging.debug(f"Cache miss for {cache_key}")
            return None

    def set(self, key: str, value: T, data_type: str = "default") -> None:
        """
        Set item in cache with timestamp.

        Args:
            key: Cache key
            value: Value to cache
            data_type: Type of data for TTL selection
        """
        cache_key = f"{data_type}:{key}"
        self._cache[cache_key] = (time.time(), value)
        logging.debug(f"Cache set for {cache_key}")

    def invalidate(self, key: str, data_type: str = "default") -> bool:
        """
        Invalidate specific cache entry.

        Args:
            key: Cache key
            data_type: Type of data

        Returns:
            True if item was found and removed
        """
        cache_key = f"{data_type}:{key}"
        try:
            del self._cache[cache_key]
            logging.debug(f"Cache invalidated for {cache_key}")
            return True
        except KeyError:
            return False

    def invalidate_by_pattern(self, pattern: str) -> int:
        """
        Invalidate cache entries matching pattern.

        Args:
            pattern: Pattern to match (simple string contains)

        Returns:
            Number of items invalidated
        """
        keys_to_remove = [key for key in self._cache.keys() if pattern in key]
        count = 0
        for key in keys_to_remove:
            try:
                del self._cache[key]
                count += 1
            except KeyError:
                pass  # Already removed

        if count > 0:
            logging.debug(f"Cache invalidated {count} items matching pattern '{pattern}'")
        return count

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        logging.debug("Cache cleared")

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        stats = {
            "cache_size": len(self._cache),
            "max_size": self._cache.maxsize,
            "default_ttl": self._default_ttl,
            "ttl_overrides": self._ttl_overrides.copy(),
        }

        # Group by data type
        type_counts: dict[str, int] = {}
        for key in self._cache.keys():
            data_type = key.split(":", 1)[0] if ":" in key else "default"
            type_counts[data_type] = type_counts.get(data_type, 0) + 1

        stats["type_breakdown"] = type_counts
        return stats

    def set_ttl_override(self, data_type: str, ttl_seconds: int) -> None:
        """
        Set TTL override for a specific data type.

        Args:
            data_type: Type of data
            ttl_seconds: TTL in seconds
        """
        self._ttl_overrides[data_type] = ttl_seconds
        logging.debug(f"Set TTL override for {data_type}: {ttl_seconds}s")

    def get_effective_ttl(self, data_type: str) -> int:
        """
        Get effective TTL for a data type.

        Args:
            data_type: Type of data

        Returns:
            TTL in seconds
        """
        return self._ttl_overrides.get(data_type, self._default_ttl)

    @property
    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)

    @property
    def maxsize(self) -> int:
        """Get maximum cache size."""
        return int(self._cache.maxsize)

    def __len__(self) -> int:
        """Get current cache size."""
        return len(self._cache)

    def __contains__(self, key: str) -> bool:
        """Check if key exists in cache (regardless of expiry)."""
        return any(key in cache_key for cache_key in self._cache.keys())
