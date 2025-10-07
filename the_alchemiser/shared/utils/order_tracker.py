"""Business Unit: shared | Status: current.

Order tracking utility for WebSocket-based order monitoring.

Provides centralized order tracking functionality used by both AlpacaManager
and AlpacaTradingService to avoid code duplication.
"""

from __future__ import annotations

import threading
import time
from decimal import Decimal
from typing import TypedDict

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.types.exceptions import AlchemiserError

logger = get_logger(__name__)


class OrderTrackerError(AlchemiserError):
    """Error raised by OrderTracker operations."""


class TrackingStats(TypedDict):
    """Statistics about tracked orders."""

    total_orders: int
    orders_with_status: int
    orders_with_price: int
    completed_orders: int


class OrderTracker:
    """Centralized order tracking for WebSocket-based order monitoring.

    Manages order events, status tracking, and completion waiting across
    multiple components that need to monitor order execution in real-time.

    Thread-safe: All public methods use internal locking to ensure thread safety.

    Raises:
        OrderTrackerError: For invalid inputs or operational errors.

    """

    def __init__(self) -> None:
        """Initialize order tracking state.

        Creates empty tracking dictionaries and a lock for thread synchronization.
        """
        self._order_events: dict[str, threading.Event] = {}
        self._order_status: dict[str, str] = {}
        self._order_avg_price: dict[str, Decimal | None] = {}
        self._lock = threading.Lock()
        logger.debug("OrderTracker initialized")

    def create_event(self, order_id: str) -> threading.Event:
        """Create or get an event for tracking order completion.

        Args:
            order_id: Order ID to track. Must be non-empty string.

        Returns:
            Threading event for the order

        Raises:
            OrderTrackerError: If order_id is empty or invalid

        """
        if not order_id or not isinstance(order_id, str):
            msg = f"order_id must be non-empty string, got: {type(order_id).__name__}"
            logger.error(
                msg, order_id=order_id if isinstance(order_id, str) else "invalid"
            )
            raise OrderTrackerError(msg)

        with self._lock:
            if order_id not in self._order_events:
                self._order_events[order_id] = threading.Event()
                logger.debug("Created tracking event", order_id=order_id)
            return self._order_events[order_id]

    def update_order_status(
        self, order_id: str, status: str | None = None, avg_price: Decimal | None = None
    ) -> None:
        """Update order status and price information.

        Args:
            order_id: Order ID to update. Must be non-empty string.
            status: New order status (normalized to lowercase)
            avg_price: Average fill price if available

        Raises:
            OrderTrackerError: If order_id is empty or invalid

        """
        if not order_id or not isinstance(order_id, str):
            msg = f"order_id must be non-empty string, got: {type(order_id).__name__}"
            logger.error(
                msg, order_id=order_id if isinstance(order_id, str) else "invalid"
            )
            raise OrderTrackerError(msg)

        with self._lock:
            if status is not None:
                self._order_status[order_id] = str(status).lower()
                logger.debug(
                    "Updated order status",
                    order_id=order_id,
                    status=str(status).lower(),
                )
            if avg_price is not None:
                self._order_avg_price[order_id] = avg_price
                logger.debug(
                    "Updated order price", order_id=order_id, avg_price=str(avg_price)
                )

    def signal_completion(self, order_id: str) -> None:
        """Signal that an order has completed.

        Args:
            order_id: Order ID that completed. Must be non-empty string.

        Raises:
            OrderTrackerError: If order_id is empty or invalid

        """
        if not order_id or not isinstance(order_id, str):
            msg = f"order_id must be non-empty string, got: {type(order_id).__name__}"
            logger.error(
                msg, order_id=order_id if isinstance(order_id, str) else "invalid"
            )
            raise OrderTrackerError(msg)

        with self._lock:
            if order_id not in self._order_events:
                self._order_events[order_id] = threading.Event()
            event = self._order_events[order_id]
            event.set()
            logger.debug("Signaled order completion", order_id=order_id)

    def wait_for_completion(self, order_id: str, timeout: float = 30.0) -> bool:
        """Wait for a single order to complete.

        Args:
            order_id: Order ID to wait for. Must be non-empty string.
            timeout: Maximum time to wait in seconds. Must be positive.

        Returns:
            True if order completed within timeout, False otherwise

        Raises:
            OrderTrackerError: If order_id is invalid or timeout is non-positive

        """
        if not order_id or not isinstance(order_id, str):
            msg = f"order_id must be non-empty string, got: {type(order_id).__name__}"
            logger.error(
                msg, order_id=order_id if isinstance(order_id, str) else "invalid"
            )
            raise OrderTrackerError(msg)

        if timeout <= 0:
            msg = f"timeout must be positive, got: {timeout}"
            logger.error(msg, order_id=order_id, timeout=timeout)
            raise OrderTrackerError(msg)

        event = self.create_event(order_id)
        completed = event.wait(timeout)
        logger.debug(
            "Wait for completion finished",
            order_id=order_id,
            timeout=timeout,
            completed=completed,
        )
        return completed

    def wait_for_multiple_orders(
        self, order_ids: list[str], timeout: float = 30.0
    ) -> list[str]:
        """Wait for multiple orders to complete within timeout.

        Args:
            order_ids: List of order IDs to wait for. Must be non-empty.
            timeout: Maximum total time to wait. Must be positive.

        Returns:
            List of order IDs that completed within timeout

        Raises:
            OrderTrackerError: If order_ids is empty or timeout is non-positive

        """
        if not order_ids:
            msg = "order_ids must be non-empty list"
            logger.error(msg)
            raise OrderTrackerError(msg)

        if timeout <= 0:
            msg = f"timeout must be positive, got: {timeout}"
            logger.error(msg, timeout=timeout)
            raise OrderTrackerError(msg)

        completed: list[str] = []
        start_time = time.time()

        logger.debug(
            "Waiting for multiple orders", order_count=len(order_ids), timeout=timeout
        )

        for order_id in order_ids:
            remaining_time = timeout - (time.time() - start_time)
            if remaining_time <= 0:
                logger.debug(
                    "Timeout reached waiting for orders",
                    completed_count=len(completed),
                    total_count=len(order_ids),
                )
                break

            if self.wait_for_completion(order_id, remaining_time):
                completed.append(order_id)

        logger.debug(
            "Finished waiting for multiple orders",
            completed_count=len(completed),
            total_count=len(order_ids),
        )
        return completed

    def get_status(self, order_id: str) -> str | None:
        """Get current status for an order.

        Args:
            order_id: Order ID to check. Must be non-empty string.

        Returns:
            Current status (lowercase) or None if not tracked

        Raises:
            OrderTrackerError: If order_id is empty or invalid

        """
        if not order_id or not isinstance(order_id, str):
            msg = f"order_id must be non-empty string, got: {type(order_id).__name__}"
            logger.error(
                msg, order_id=order_id if isinstance(order_id, str) else "invalid"
            )
            raise OrderTrackerError(msg)

        with self._lock:
            return self._order_status.get(order_id)

    def get_avg_price(self, order_id: str) -> Decimal | None:
        """Get average fill price for an order.

        Args:
            order_id: Order ID to check. Must be non-empty string.

        Returns:
            Average fill price or None if not available

        Raises:
            OrderTrackerError: If order_id is empty or invalid

        """
        if not order_id or not isinstance(order_id, str):
            msg = f"order_id must be non-empty string, got: {type(order_id).__name__}"
            logger.error(
                msg, order_id=order_id if isinstance(order_id, str) else "invalid"
            )
            raise OrderTrackerError(msg)

        with self._lock:
            return self._order_avg_price.get(order_id)

    def is_terminal_status(self, status: str | None) -> bool:
        """Check if a status indicates terminal state.

        Args:
            status: Order status to check

        Returns:
            True if status is terminal (order won't change further)

        """
        if not status:
            return False
        return status.lower() in {
            "filled",
            "canceled",
            "cancelled",
            "rejected",
            "expired",
        }

    def get_completed_orders(self, order_ids: list[str]) -> list[str]:
        """Get list of orders that have completed from a list.

        Args:
            order_ids: Order IDs to check

        Returns:
            List of order IDs that are in terminal state

        Pre-conditions:
            - order_ids can be empty list (returns empty list)

        Post-conditions:
            - Returned list contains only IDs from input with terminal status

        """
        completed = []
        with self._lock:
            for order_id in order_ids:
                status = self._order_status.get(order_id, "")
                if self.is_terminal_status(status):
                    completed.append(order_id)
        logger.debug(
            "Retrieved completed orders",
            total_count=len(order_ids),
            completed_count=len(completed),
        )
        return completed

    def cleanup_order(self, order_id: str) -> None:
        """Clean up tracking data for a completed order.

        Args:
            order_id: Order ID to clean up. Must be non-empty string.

        Raises:
            OrderTrackerError: If order_id is empty or invalid

        Post-conditions:
            - All tracking data for order_id is removed

        """
        if not order_id or not isinstance(order_id, str):
            msg = f"order_id must be non-empty string, got: {type(order_id).__name__}"
            logger.error(
                msg, order_id=order_id if isinstance(order_id, str) else "invalid"
            )
            raise OrderTrackerError(msg)

        with self._lock:
            self._order_events.pop(order_id, None)
            self._order_status.pop(order_id, None)
            self._order_avg_price.pop(order_id, None)
            logger.debug("Cleaned up order tracking data", order_id=order_id)

    def cleanup_all(self) -> None:
        """Clean up all tracking data.

        Post-conditions:
            - All tracking dictionaries are cleared
            - All events are removed

        """
        with self._lock:
            total_orders = len(self._order_events)
            self._order_events.clear()
            self._order_status.clear()
            self._order_avg_price.clear()
            logger.info("Cleaned up all tracking data", orders_cleared=total_orders)

    def get_tracking_stats(self) -> TrackingStats:
        """Get statistics about tracked orders.

        Returns:
            Dictionary with tracking statistics:
            - total_orders: Total number of orders being tracked
            - orders_with_status: Orders with status information
            - orders_with_price: Orders with price information
            - completed_orders: Orders in terminal state

        Post-conditions:
            - Returned stats are consistent snapshot (taken under lock)

        """
        with self._lock:
            stats: TrackingStats = {
                "total_orders": len(self._order_events),
                "orders_with_status": len(self._order_status),
                "orders_with_price": len(
                    [p for p in self._order_avg_price.values() if p is not None]
                ),
                "completed_orders": len(
                    [
                        s
                        for s in self._order_status.values()
                        if self.is_terminal_status(s)
                    ]
                ),
            }
            logger.debug("Retrieved tracking stats", **stats)
            return stats
