#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Signal idempotency store for preventing duplicate signal processing.

Provides in-memory and persistent storage for signal hashes and correlation IDs
to enable idempotent signal generation and replay detection.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from the_alchemiser.shared.logging.logging_utils import get_logger
from the_alchemiser.shared.persistence import get_default_persistence_handler


class PersistenceHandler(Protocol):
    """Protocol for persistence handlers."""
    
    def exists(self, path: str) -> bool:
        """Check if file exists."""
        ...
        
    def read(self, path: str) -> str:
        """Read file content."""
        ...
        
    def write(self, path: str, content: str) -> None:
        """Write file content."""
        ...

logger = get_logger(__name__)


class SignalIdempotencyStore:
    """Store for signal idempotency keys and correlation tracking.
    
    Manages signal hashes and correlation IDs to prevent duplicate signal
    processing during event replay scenarios. Uses in-memory cache with
    optional persistent storage.
    """
    
    def __init__(self, persistence_handler: PersistenceHandler | None = None, max_cache_entries: int = 1000) -> None:
        """Initialize the idempotency store.
        
        Args:
            persistence_handler: Optional persistence handler for durable storage
            max_cache_entries: Maximum number of entries to keep in memory cache
            
        """
        self._cache: dict[str, dict[str, Any]] = {}
        self._max_cache_entries = max_cache_entries
        self._persistence_handler = persistence_handler or get_default_persistence_handler()
        self._cache_file = "signal_idempotency_cache.json"
        
        # Load existing cache from persistence
        self._load_cache()
    
    def has_signal_hash(self, signal_hash: str) -> bool:
        """Check if signal hash has been processed before.
        
        Args:
            signal_hash: Deterministic signal hash to check
            
        Returns:
            True if hash exists (signal already processed), False otherwise
            
        """
        try:
            # Check in-memory cache first
            if signal_hash in self._cache:
                entry = self._cache[signal_hash]
                # Check if entry is not expired (24 hours default)
                created_at = datetime.fromisoformat(entry.get("created_at", ""))
                if datetime.now(UTC) - created_at < timedelta(hours=24):
                    logger.debug(f"Signal hash {signal_hash} found in cache (not expired)")
                    return True
                # Remove expired entry
                del self._cache[signal_hash]
                logger.debug(f"Removed expired signal hash {signal_hash} from cache")
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking signal hash {signal_hash}: {e}")
            return False
    
    def store_signal_hash(
        self,
        signal_hash: str,
        correlation_id: str,
        causation_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Store signal hash with correlation tracking.
        
        Args:
            signal_hash: Deterministic signal hash
            correlation_id: Event correlation ID
            causation_id: Optional causation ID for event chain tracking
            metadata: Optional additional metadata
            
        """
        try:
            entry = {
                "correlation_id": correlation_id,
                "causation_id": causation_id,
                "created_at": datetime.now(UTC).isoformat(),
                "metadata": metadata or {},
            }
            
            # Store in memory cache
            self._cache[signal_hash] = entry
            
            # Trim cache if it gets too large
            if len(self._cache) > self._max_cache_entries:
                self._trim_cache()
            
            # Persist to storage
            self._save_cache()
            
            logger.debug(
                f"Stored signal hash {signal_hash} with correlation {correlation_id}"
            )
            
        except Exception as e:
            logger.error(f"Error storing signal hash {signal_hash}: {e}")
    
    def get_signal_metadata(self, signal_hash: str) -> dict[str, Any] | None:
        """Get metadata for a previously stored signal hash.
        
        Args:
            signal_hash: Signal hash to look up
            
        Returns:
            Metadata dictionary if found, None otherwise
            
        """
        try:
            entry = self._cache.get(signal_hash)
            if entry:
                # Check if not expired
                created_at = datetime.fromisoformat(entry.get("created_at", ""))
                if datetime.now(UTC) - created_at < timedelta(hours=24):
                    return entry
                # Remove expired entry
                del self._cache[signal_hash]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting signal metadata for {signal_hash}: {e}")
            return None
    
    def clear_expired_entries(self) -> int:
        """Clear expired entries from the cache.
        
        Returns:
            Number of entries removed
            
        """
        try:
            current_time = datetime.now(UTC)
            expired_keys = []
            
            for signal_hash, entry in self._cache.items():
                try:
                    created_at = datetime.fromisoformat(entry.get("created_at", ""))
                    if current_time - created_at >= timedelta(hours=24):
                        expired_keys.append(signal_hash)
                except (ValueError, TypeError):
                    # Invalid timestamp, consider it expired
                    expired_keys.append(signal_hash)
            
            # Remove expired entries
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                self._save_cache()
                logger.info(f"Cleared {len(expired_keys)} expired signal hash entries")
            
            return len(expired_keys)
            
        except Exception as e:
            logger.error(f"Error clearing expired entries: {e}")
            return 0
    
    def _load_cache(self) -> None:
        """Load cache from persistent storage."""
        try:
            if self._persistence_handler.exists(self._cache_file):
                content = self._persistence_handler.read(self._cache_file)
                self._cache = json.loads(content)
                logger.debug(f"Loaded {len(self._cache)} signal hash entries from cache")
            else:
                logger.debug("No existing signal idempotency cache found")
                
        except Exception as e:
            logger.warning(f"Failed to load signal idempotency cache: {e}")
            self._cache = {}
    
    def _save_cache(self) -> None:
        """Save cache to persistent storage."""
        try:
            content = json.dumps(self._cache, indent=2)
            self._persistence_handler.write(self._cache_file, content)
            logger.debug(f"Saved {len(self._cache)} signal hash entries to cache")
            
        except Exception as e:
            logger.error(f"Failed to save signal idempotency cache: {e}")
    
    def _trim_cache(self) -> None:
        """Trim cache to max entries by removing oldest entries."""
        try:
            if len(self._cache) <= self._max_cache_entries:
                return
            
            # Sort by creation time and keep only the most recent entries
            sorted_items = sorted(
                self._cache.items(),
                key=lambda x: x[1].get("created_at", ""),
                reverse=True
            )
            
            # Keep only the most recent entries
            self._cache = dict(sorted_items[:self._max_cache_entries])
            
            logger.debug(f"Trimmed cache to {len(self._cache)} entries")
            
        except Exception as e:
            logger.error(f"Error trimming cache: {e}")


# Global instance for easy access
_signal_store: SignalIdempotencyStore | None = None


def get_signal_idempotency_store() -> SignalIdempotencyStore:
    """Get the global signal idempotency store instance.
    
    Returns:
        Singleton SignalIdempotencyStore instance
        
    """
    global _signal_store
    if _signal_store is None:
        _signal_store = SignalIdempotencyStore()
    return _signal_store