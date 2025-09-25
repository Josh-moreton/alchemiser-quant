"""Business Unit: shared | Status: current.

Order tracking utility for WebSocket-based order monitoring.

Provides centralized order tracking functionality used by both AlpacaManager
and AlpacaTradingService to avoid code duplication.
"""

from __future__ import annotations

import threading
import time
from decimal import Decimal
from typing import Any


class OrderTracker:
    """Centralized order tracking for WebSocket-based order monitoring.

    Manages order events, status tracking, and completion waiting across
    multiple components that need to monitor order execution in real-time.
    """

    def __init__(self) -> None:
        """Initialize order tracking state."""
        self._order_events: dict[str, threading.Event] = {}
        self._order_status: dict[str, str] = {}
        self._order_avg_price: dict[str, Decimal | None] = {}
        self._lock = threading.Lock()

    def create_event(self, order_id: str) -> threading.Event:
        """Create or get an event for tracking order completion.

        Args:
            order_id: Order ID to track

        Returns:
            Threading event for the order

        """
        with self._lock:
            if order_id not in self._order_events:
                self._order_events[order_id] = threading.Event()
            return self._order_events[order_id]

    def update_order_status(
        self, order_id: str, status: str | None = None, avg_price: Decimal | None = None
    ) -> None:
        """Update order status and price information.

        Args:
            order_id: Order ID to update
            status: New order status
            avg_price: Average fill price if available

        """
        with self._lock:
            if status is not None:
                self._order_status[order_id] = status
            if avg_price is not None:
                self._order_avg_price[order_id] = avg_price

    def signal_completion(self, order_id: str) -> None:
        """Signal that an order has completed.

        Args:
            order_id: Order ID that completed

        """
        with self._lock:
            event = self._order_events.get(order_id)
            if event:
                event.set()

    def wait_for_completion(self, order_id: str, timeout: float = 30.0) -> bool:
        """Wait for a single order to complete.

        Args:
            order_id: Order ID to wait for
            timeout: Maximum time to wait in seconds

        Returns:
            True if order completed within timeout, False otherwise

        """
        event = self.create_event(order_id)
        return event.wait(timeout)

    def wait_for_multiple_orders(
        self, order_ids: list[str], timeout: float = 30.0
    ) -> list[str]:
        """Wait for multiple orders to complete within timeout.

        Args:
            order_ids: List of order IDs to wait for
            timeout: Maximum total time to wait

        Returns:
            List of order IDs that completed within timeout

        """
        completed = []
        start_time = time.time()

        for order_id in order_ids:
            remaining_time = timeout - (time.time() - start_time)
            if remaining_time <= 0:
                break

            if self.wait_for_completion(order_id, remaining_time):
                completed.append(order_id)

        return completed

    def get_status(self, order_id: str) -> str | None:
        """Get current status for an order.

        Args:
            order_id: Order ID to check

        Returns:
            Current status or None if not tracked

        """
        with self._lock:
            return self._order_status.get(order_id)

    def get_avg_price(self, order_id: str) -> Decimal | None:
        """Get average fill price for an order.

        Args:
            order_id: Order ID to check

        Returns:
            Average fill price or None if not available

        """
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

        """
        completed = []
        with self._lock:
            for order_id in order_ids:
                status = self._order_status.get(order_id, "")
                if self.is_terminal_status(status):
                    completed.append(order_id)
        return completed

    def cleanup_order(self, order_id: str) -> None:
        """Clean up tracking data for a completed order.

        Args:
            order_id: Order ID to clean up

        """
        with self._lock:
            self._order_events.pop(order_id, None)
            self._order_status.pop(order_id, None)
            self._order_avg_price.pop(order_id, None)

    def cleanup_all(self) -> None:
        """Clean up all tracking data."""
        with self._lock:
            self._order_events.clear()
            self._order_status.clear()
            self._order_avg_price.clear()

    def get_tracking_stats(self) -> dict[str, Any]:
        """Get statistics about tracked orders.

        Returns:
            Dictionary with tracking statistics

        """
        with self._lock:
            return {
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
