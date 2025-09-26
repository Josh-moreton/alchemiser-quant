"""Business Unit: shared | Status: current.

Metrics and state accumulation for pricing service.
"""

from __future__ import annotations

import threading
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .data_store import PricingDataStore

class PricingStats:
    """Thread-safe statistics collection for pricing service."""

    def __init__(self, data_store: PricingDataStore) -> None:
        """Initialize statistics collector.
        
        Args:
            data_store: Data store to get storage statistics from

        """
        self._data_store = data_store
        self._stats: dict[str, int] = {
            "quotes_received": 0,
            "total_subscriptions": 0,
            "trades_received": 0,
            "subscription_limit_hits": 0,
        }
        self._datetime_stats: dict[str, datetime] = {}
        self._connected = False
        self._lock = threading.Lock()

    def increment_quotes_received(self) -> None:
        """Increment quotes received counter."""
        with self._lock:
            self._stats["quotes_received"] += 1

    def increment_trades_received(self) -> None:
        """Increment trades received counter."""
        with self._lock:
            self._stats["trades_received"] += 1

    def increment_total_subscriptions(self) -> None:
        """Increment total subscriptions counter."""
        with self._lock:
            self._stats["total_subscriptions"] += 1

    def increment_subscription_limit_hits(self) -> None:
        """Increment subscription limit hits counter."""
        with self._lock:
            self._stats["subscription_limit_hits"] += 1

    def update_last_heartbeat(self) -> None:
        """Update last heartbeat timestamp."""
        with self._lock:
            self._datetime_stats["last_heartbeat"] = datetime.now(UTC)

    def set_connected(self, *, connected: bool) -> None:
        """Set connection status.
        
        Args:
            connected: Whether the service is connected

        """
        with self._lock:
            self._connected = connected

    def is_connected(self) -> bool:
        """Check if the service is connected.
        
        Returns:
            Connection status

        """
        with self._lock:
            return self._connected

    def get_stats(self) -> dict[str, str | int | float | datetime | bool]:
        """Get comprehensive service statistics.
        
        Returns:
            Dictionary with all statistics including storage metrics

        """
        with self._lock:
            # Calculate uptime
            last_hb = self._datetime_stats.get("last_heartbeat")
            uptime = (
                (datetime.now(UTC) - last_hb).total_seconds() 
                if isinstance(last_hb, datetime) 
                else 0
            )

            # Get storage statistics
            storage_stats = self._data_store.get_stats()

            return {
                **self._stats,
                **self._datetime_stats,
                **storage_stats,
                "connected": self._connected,
                "uptime_seconds": uptime,
            }

    def reset_stats(self) -> None:
        """Reset all statistics counters."""
        with self._lock:
            self._stats = {
                "quotes_received": 0,
                "total_subscriptions": 0,
                "trades_received": 0,
                "subscription_limit_hits": 0,
            }
            self._datetime_stats.clear()

    def get_raw_stats(self) -> dict[str, int]:
        """Get raw statistics dictionary for internal use.
        
        Returns:
            Reference to internal stats dictionary

        """
        return self._stats

    def get_raw_datetime_stats(self) -> dict[str, datetime]:
        """Get raw datetime statistics dictionary for internal use.
        
        Returns:
            Reference to internal datetime stats dictionary

        """
        return self._datetime_stats