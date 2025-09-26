#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Portfolio idempotency store for preventing duplicate rebalance plan processing.

Provides persistent storage for plan hashes and correlation IDs to enable
idempotent portfolio analysis and plan generation during event replay scenarios.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

from the_alchemiser.shared.logging.logging_utils import get_logger
from the_alchemiser.shared.persistence import get_default_persistence_handler
from the_alchemiser.shared.protocols.persistence import (
    PersistenceHandler as ProtocolPersistenceHandler,
)

logger = get_logger(__name__)


class PortfolioIdempotencyStore:
    """Store for portfolio plan idempotency keys and correlation tracking.

    Manages plan hashes and correlation IDs to prevent duplicate rebalance plan
    generation during event replay scenarios. Uses persistent storage with
    in-memory cache for performance.
    """

    def __init__(
        self,
        persistence_handler: ProtocolPersistenceHandler | None = None,
        max_cache_entries: int = 500,
    ) -> None:
        """Initialize the portfolio idempotency store.

        Args:
            persistence_handler: Optional persistence handler for durable storage
            max_cache_entries: Maximum number of entries to keep in memory cache

        """
        self._cache: dict[str, dict[str, Any]] = {}
        self._max_cache_entries = max_cache_entries
        self._persistence_handler = persistence_handler or get_default_persistence_handler()
        self._cache_file = "portfolio_idempotency_cache.json"

        # Load existing cache from persistence
        self._load_cache()

    def has_plan_hash(self, plan_hash: str, correlation_id: str) -> bool:
        """Check if plan hash has been processed for this correlation.

        Args:
            plan_hash: Deterministic plan hash to check
            correlation_id: Event correlation ID

        Returns:
            True if hash exists for correlation (plan already processed), False otherwise

        """
        try:
            cache_key = f"{correlation_id}:{plan_hash}"

            # Check in-memory cache first
            if cache_key in self._cache:
                entry = self._cache[cache_key]
                # Check if entry is not expired (6 hours default for plans)
                created_at = datetime.fromisoformat(entry.get("created_at", ""))
                if datetime.now(UTC) - created_at < timedelta(hours=6):
                    logger.debug(f"Plan hash {plan_hash} found in cache (not expired)")
                    return True
                # Remove expired entry
                del self._cache[cache_key]
                logger.debug(f"Removed expired plan hash {plan_hash} from cache")

            return False

        except Exception as e:
            logger.error(f"Error checking plan hash {plan_hash}: {e}")
            return False

    def store_plan_hash(
        self,
        plan_hash: str,
        correlation_id: str,
        causation_id: str | None = None,
        account_snapshot_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Store plan hash with correlation tracking.

        Args:
            plan_hash: Deterministic plan hash
            correlation_id: Event correlation ID
            causation_id: Optional causation ID for event chain tracking
            account_snapshot_id: Optional account snapshot identifier
            metadata: Optional additional metadata

        """
        try:
            cache_key = f"{correlation_id}:{plan_hash}"
            entry = {
                "plan_hash": plan_hash,
                "correlation_id": correlation_id,
                "causation_id": causation_id,
                "account_snapshot_id": account_snapshot_id,
                "created_at": datetime.now(UTC).isoformat(),
                "metadata": metadata or {},
            }

            # Store in memory cache
            self._cache[cache_key] = entry

            # Trim cache if it gets too large
            if len(self._cache) > self._max_cache_entries:
                self._trim_cache()

            # Persist to storage
            self._save_cache()

            logger.debug(f"Stored plan hash {plan_hash} with correlation {correlation_id}")

        except Exception as e:
            logger.error(f"Error storing plan hash {plan_hash}: {e}")

    def get_plan_metadata(self, plan_hash: str, correlation_id: str) -> dict[str, Any] | None:
        """Get metadata for a previously stored plan hash.

        Args:
            plan_hash: Plan hash to look up
            correlation_id: Event correlation ID

        Returns:
            Metadata dictionary if found, None otherwise

        """
        try:
            cache_key = f"{correlation_id}:{plan_hash}"
            entry = self._cache.get(cache_key)
            if entry:
                # Check if not expired
                created_at = datetime.fromisoformat(entry.get("created_at", ""))
                if datetime.now(UTC) - created_at < timedelta(hours=6):
                    return entry
                # Remove expired entry
                del self._cache[cache_key]

            return None

        except Exception as e:
            logger.error(f"Error getting plan metadata for {plan_hash}: {e}")
            return None

    def clear_expired_entries(self) -> int:
        """Clear expired entries from the cache.

        Returns:
            Number of entries removed

        """
        try:
            current_time = datetime.now(UTC)
            expired_keys = []

            for cache_key, entry in self._cache.items():
                try:
                    created_at = datetime.fromisoformat(entry.get("created_at", ""))
                    if current_time - created_at >= timedelta(hours=6):
                        expired_keys.append(cache_key)
                except (ValueError, TypeError):
                    # Invalid timestamp, consider it expired
                    expired_keys.append(cache_key)

            # Remove expired entries
            for key in expired_keys:
                del self._cache[key]

            if expired_keys:
                self._save_cache()
                logger.info(f"Cleared {len(expired_keys)} expired plan hash entries")

            return len(expired_keys)

        except Exception as e:
            logger.error(f"Error clearing expired entries: {e}")
            return 0

    def _load_cache(self) -> None:
        """Load cache from persistent storage."""
        try:
            if self._persistence_handler.file_exists(self._cache_file):
                content = self._persistence_handler.read_text(self._cache_file)
                if content:
                    self._cache = json.loads(content)
                logger.debug(f"Loaded {len(self._cache)} plan hash entries from cache")
            else:
                logger.debug("No existing portfolio idempotency cache found")

        except Exception as e:
            logger.warning(f"Failed to load portfolio idempotency cache: {e}")
            self._cache = {}

    def _save_cache(self) -> None:
        """Save cache to persistent storage."""
        try:
            content = json.dumps(self._cache, indent=2)
            self._persistence_handler.write_text(self._cache_file, content)
            logger.debug(f"Saved {len(self._cache)} plan hash entries to cache")

        except Exception as e:
            logger.error(f"Failed to save portfolio idempotency cache: {e}")

    def _trim_cache(self) -> None:
        """Trim cache to max entries by removing oldest entries."""
        try:
            if len(self._cache) <= self._max_cache_entries:
                return

            # Sort by creation time and keep only the most recent entries
            sorted_items = sorted(
                self._cache.items(),
                key=lambda x: x[1].get("created_at", ""),
                reverse=True,
            )

            # Keep only the most recent entries
            self._cache = dict(sorted_items[: self._max_cache_entries])

            logger.debug(f"Trimmed cache to {len(self._cache)} entries")

        except Exception as e:
            logger.error(f"Error trimming cache: {e}")


# Global instance for easy access
_portfolio_store: PortfolioIdempotencyStore | None = None


def get_portfolio_idempotency_store() -> PortfolioIdempotencyStore:
    """Get the global portfolio idempotency store instance.

    Returns:
        Singleton PortfolioIdempotencyStore instance

    """
    global _portfolio_store
    if _portfolio_store is None:
        _portfolio_store = PortfolioIdempotencyStore()
    return _portfolio_store
