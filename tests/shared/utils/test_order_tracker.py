"""Business Unit: shared | Status: current.

Comprehensive tests for OrderTracker utility.

Tests cover:
- Thread-safety of order tracking operations
- Input validation and error handling
- Event creation and signaling
- Status tracking and retrieval
- Timeout handling in wait operations
- Cleanup operations
- Statistics tracking
"""

from __future__ import annotations

import threading
import time
from decimal import Decimal

import pytest

from the_alchemiser.shared.utils.order_tracker import OrderTracker, OrderTrackerError


class TestOrderTrackerInitialization:
    """Test OrderTracker initialization."""

    def test_init_creates_empty_tracker(self):
        """Test that initialization creates empty tracking structures."""
        tracker = OrderTracker()

        stats = tracker.get_tracking_stats()
        assert stats["total_orders"] == 0
        assert stats["orders_with_status"] == 0
        assert stats["orders_with_price"] == 0
        assert stats["completed_orders"] == 0


class TestOrderTrackerEventCreation:
    """Test event creation and retrieval."""

    def test_create_event_returns_new_event(self):
        """Test creating a new event for an order."""
        tracker = OrderTracker()
        order_id = "test-order-123"

        event = tracker.create_event(order_id)

        assert isinstance(event, threading.Event)
        assert not event.is_set()

    def test_create_event_returns_existing_event(self):
        """Test that creating the same event twice returns the same instance."""
        tracker = OrderTracker()
        order_id = "test-order-123"

        event1 = tracker.create_event(order_id)
        event2 = tracker.create_event(order_id)

        assert event1 is event2

    def test_create_event_with_empty_order_id_raises_error(self):
        """Test that empty order_id raises OrderTrackerError."""
        tracker = OrderTracker()

        with pytest.raises(OrderTrackerError, match="order_id must be non-empty string"):
            tracker.create_event("")

    def test_create_event_with_none_order_id_raises_error(self):
        """Test that None order_id raises OrderTrackerError."""
        tracker = OrderTracker()

        with pytest.raises(OrderTrackerError, match="order_id must be non-empty string"):
            tracker.create_event(None)  # type: ignore[arg-type]

    def test_create_event_with_non_string_order_id_raises_error(self):
        """Test that non-string order_id raises OrderTrackerError."""
        tracker = OrderTracker()

        with pytest.raises(OrderTrackerError, match="order_id must be non-empty string"):
            tracker.create_event(123)  # type: ignore[arg-type]


class TestOrderTrackerStatusUpdates:
    """Test status update operations."""

    def test_update_order_status_sets_status(self):
        """Test that update_order_status correctly sets status."""
        tracker = OrderTracker()
        order_id = "test-order-123"

        tracker.update_order_status(order_id, status="FILLED")

        assert tracker.get_status(order_id) == "filled"  # Normalized to lowercase

    def test_update_order_status_sets_avg_price(self):
        """Test that update_order_status correctly sets average price."""
        tracker = OrderTracker()
        order_id = "test-order-123"
        price = Decimal("150.25")

        tracker.update_order_status(order_id, avg_price=price)

        assert tracker.get_avg_price(order_id) == price

    def test_update_order_status_sets_both(self):
        """Test that update_order_status can set both status and price."""
        tracker = OrderTracker()
        order_id = "test-order-123"
        price = Decimal("150.25")

        tracker.update_order_status(order_id, status="FILLED", avg_price=price)

        assert tracker.get_status(order_id) == "filled"
        assert tracker.get_avg_price(order_id) == price

    def test_update_order_status_with_none_values_does_nothing(self):
        """Test that update_order_status with None values doesn't change state."""
        tracker = OrderTracker()
        order_id = "test-order-123"

        tracker.update_order_status(order_id, status=None, avg_price=None)

        assert tracker.get_status(order_id) is None
        assert tracker.get_avg_price(order_id) is None

    def test_update_order_status_with_empty_order_id_raises_error(self):
        """Test that empty order_id raises OrderTrackerError."""
        tracker = OrderTracker()

        with pytest.raises(OrderTrackerError, match="order_id must be non-empty string"):
            tracker.update_order_status("", status="FILLED")


class TestOrderTrackerSignalCompletion:
    """Test signal completion operations."""

    def test_signal_completion_sets_event(self):
        """Test that signal_completion sets the event."""
        tracker = OrderTracker()
        order_id = "test-order-123"

        event = tracker.create_event(order_id)
        assert not event.is_set()

        tracker.signal_completion(order_id)
        assert event.is_set()

    def test_signal_completion_creates_event_if_missing(self):
        """Test that signal_completion creates event if it doesn't exist."""
        tracker = OrderTracker()
        order_id = "test-order-123"

        # Signal without creating event first
        tracker.signal_completion(order_id)

        # Event should be created and set
        event = tracker.create_event(order_id)
        assert event.is_set()

    def test_signal_completion_with_empty_order_id_raises_error(self):
        """Test that empty order_id raises OrderTrackerError."""
        tracker = OrderTracker()

        with pytest.raises(OrderTrackerError, match="order_id must be non-empty string"):
            tracker.signal_completion("")


class TestOrderTrackerWaitForCompletion:
    """Test wait for completion operations."""

    def test_wait_for_completion_returns_true_when_signaled(self):
        """Test that wait_for_completion returns True when order is signaled."""
        tracker = OrderTracker()
        order_id = "test-order-123"

        # Signal in a separate thread after a short delay
        def signal_after_delay():
            time.sleep(0.1)
            tracker.signal_completion(order_id)

        thread = threading.Thread(target=signal_after_delay)
        thread.start()

        result = tracker.wait_for_completion(order_id, timeout=1.0)
        thread.join()

        assert result is True

    def test_wait_for_completion_returns_false_on_timeout(self):
        """Test that wait_for_completion returns False on timeout."""
        tracker = OrderTracker()
        order_id = "test-order-123"

        result = tracker.wait_for_completion(order_id, timeout=0.1)

        assert result is False

    def test_wait_for_completion_with_empty_order_id_raises_error(self):
        """Test that empty order_id raises OrderTrackerError."""
        tracker = OrderTracker()

        with pytest.raises(OrderTrackerError, match="order_id must be non-empty string"):
            tracker.wait_for_completion("")

    def test_wait_for_completion_with_zero_timeout_raises_error(self):
        """Test that zero timeout raises OrderTrackerError."""
        tracker = OrderTracker()

        with pytest.raises(OrderTrackerError, match="timeout must be positive"):
            tracker.wait_for_completion("test-order", timeout=0.0)

    def test_wait_for_completion_with_negative_timeout_raises_error(self):
        """Test that negative timeout raises OrderTrackerError."""
        tracker = OrderTracker()

        with pytest.raises(OrderTrackerError, match="timeout must be positive"):
            tracker.wait_for_completion("test-order", timeout=-1.0)


class TestOrderTrackerWaitForMultipleOrders:
    """Test wait for multiple orders operations."""

    def test_wait_for_multiple_orders_returns_all_when_signaled(self):
        """Test waiting for multiple orders that all complete."""
        tracker = OrderTracker()
        order_ids = ["order-1", "order-2", "order-3"]

        # Signal all orders in a separate thread
        def signal_all():
            time.sleep(0.1)
            for order_id in order_ids:
                tracker.signal_completion(order_id)

        thread = threading.Thread(target=signal_all)
        thread.start()

        completed = tracker.wait_for_multiple_orders(order_ids, timeout=1.0)
        thread.join()

        assert len(completed) == 3
        assert set(completed) == set(order_ids)

    def test_wait_for_multiple_orders_returns_partial_on_timeout(self):
        """Test waiting for multiple orders with partial completion."""
        tracker = OrderTracker()
        order_ids = ["order-1", "order-2", "order-3"]

        # Signal only first order
        def signal_one():
            time.sleep(0.05)
            tracker.signal_completion("order-1")

        thread = threading.Thread(target=signal_one)
        thread.start()

        completed = tracker.wait_for_multiple_orders(order_ids, timeout=0.2)
        thread.join()

        assert len(completed) == 1
        assert "order-1" in completed

    def test_wait_for_multiple_orders_with_empty_list_raises_error(self):
        """Test that empty order_ids list raises OrderTrackerError."""
        tracker = OrderTracker()

        with pytest.raises(OrderTrackerError, match="order_ids must be non-empty list"):
            tracker.wait_for_multiple_orders([])

    def test_wait_for_multiple_orders_with_zero_timeout_raises_error(self):
        """Test that zero timeout raises OrderTrackerError."""
        tracker = OrderTracker()

        with pytest.raises(OrderTrackerError, match="timeout must be positive"):
            tracker.wait_for_multiple_orders(["order-1"], timeout=0.0)


class TestOrderTrackerStatusRetrieval:
    """Test status retrieval operations."""

    def test_get_status_returns_none_for_untracked_order(self):
        """Test that get_status returns None for untracked order."""
        tracker = OrderTracker()

        status = tracker.get_status("unknown-order")

        assert status is None

    def test_get_status_returns_tracked_status(self):
        """Test that get_status returns the tracked status."""
        tracker = OrderTracker()
        order_id = "test-order-123"

        tracker.update_order_status(order_id, status="FILLED")
        status = tracker.get_status(order_id)

        assert status == "filled"

    def test_get_status_with_empty_order_id_raises_error(self):
        """Test that empty order_id raises OrderTrackerError."""
        tracker = OrderTracker()

        with pytest.raises(OrderTrackerError, match="order_id must be non-empty string"):
            tracker.get_status("")


class TestOrderTrackerAvgPriceRetrieval:
    """Test average price retrieval operations."""

    def test_get_avg_price_returns_none_for_untracked_order(self):
        """Test that get_avg_price returns None for untracked order."""
        tracker = OrderTracker()

        price = tracker.get_avg_price("unknown-order")

        assert price is None

    def test_get_avg_price_returns_tracked_price(self):
        """Test that get_avg_price returns the tracked price."""
        tracker = OrderTracker()
        order_id = "test-order-123"
        price = Decimal("150.25")

        tracker.update_order_status(order_id, avg_price=price)
        retrieved_price = tracker.get_avg_price(order_id)

        assert retrieved_price == price

    def test_get_avg_price_with_empty_order_id_raises_error(self):
        """Test that empty order_id raises OrderTrackerError."""
        tracker = OrderTracker()

        with pytest.raises(OrderTrackerError, match="order_id must be non-empty string"):
            tracker.get_avg_price("")


class TestOrderTrackerTerminalStatus:
    """Test terminal status checking."""

    def test_is_terminal_status_with_filled(self):
        """Test that 'filled' is recognized as terminal."""
        tracker = OrderTracker()

        assert tracker.is_terminal_status("filled") is True
        assert tracker.is_terminal_status("FILLED") is True

    def test_is_terminal_status_with_canceled(self):
        """Test that 'canceled' is recognized as terminal."""
        tracker = OrderTracker()

        assert tracker.is_terminal_status("canceled") is True
        assert tracker.is_terminal_status("cancelled") is True
        assert tracker.is_terminal_status("CANCELED") is True

    def test_is_terminal_status_with_rejected(self):
        """Test that 'rejected' is recognized as terminal."""
        tracker = OrderTracker()

        assert tracker.is_terminal_status("rejected") is True
        assert tracker.is_terminal_status("REJECTED") is True

    def test_is_terminal_status_with_expired(self):
        """Test that 'expired' is recognized as terminal."""
        tracker = OrderTracker()

        assert tracker.is_terminal_status("expired") is True
        assert tracker.is_terminal_status("EXPIRED") is True

    def test_is_terminal_status_with_non_terminal(self):
        """Test that non-terminal statuses return False."""
        tracker = OrderTracker()

        assert tracker.is_terminal_status("pending") is False
        assert tracker.is_terminal_status("new") is False
        assert tracker.is_terminal_status("partially_filled") is False

    def test_is_terminal_status_with_none(self):
        """Test that None returns False."""
        tracker = OrderTracker()

        assert tracker.is_terminal_status(None) is False

    def test_is_terminal_status_with_empty_string(self):
        """Test that empty string returns False."""
        tracker = OrderTracker()

        assert tracker.is_terminal_status("") is False


class TestOrderTrackerCompletedOrders:
    """Test completed orders retrieval."""

    def test_get_completed_orders_returns_empty_for_empty_input(self):
        """Test that get_completed_orders returns empty list for empty input."""
        tracker = OrderTracker()

        completed = tracker.get_completed_orders([])

        assert completed == []

    def test_get_completed_orders_returns_only_completed(self):
        """Test that get_completed_orders returns only terminal orders."""
        tracker = OrderTracker()

        tracker.update_order_status("order-1", status="filled")
        tracker.update_order_status("order-2", status="pending")
        tracker.update_order_status("order-3", status="canceled")

        completed = tracker.get_completed_orders(["order-1", "order-2", "order-3"])

        assert len(completed) == 2
        assert "order-1" in completed
        assert "order-3" in completed
        assert "order-2" not in completed

    def test_get_completed_orders_handles_unknown_orders(self):
        """Test that get_completed_orders handles unknown orders gracefully."""
        tracker = OrderTracker()

        tracker.update_order_status("order-1", status="filled")

        completed = tracker.get_completed_orders(["order-1", "unknown-order"])

        assert len(completed) == 1
        assert "order-1" in completed


class TestOrderTrackerCleanup:
    """Test cleanup operations."""

    def test_cleanup_order_removes_all_data(self):
        """Test that cleanup_order removes all tracking data for an order."""
        tracker = OrderTracker()
        order_id = "test-order-123"
        price = Decimal("150.25")

        tracker.create_event(order_id)
        tracker.update_order_status(order_id, status="filled", avg_price=price)

        tracker.cleanup_order(order_id)

        assert tracker.get_status(order_id) is None
        assert tracker.get_avg_price(order_id) is None
        stats = tracker.get_tracking_stats()
        assert stats["total_orders"] == 0

    def test_cleanup_order_with_empty_order_id_raises_error(self):
        """Test that empty order_id raises OrderTrackerError."""
        tracker = OrderTracker()

        with pytest.raises(OrderTrackerError, match="order_id must be non-empty string"):
            tracker.cleanup_order("")

    def test_cleanup_order_handles_unknown_order(self):
        """Test that cleanup_order handles unknown order gracefully."""
        tracker = OrderTracker()

        # Should not raise error
        tracker.cleanup_order("unknown-order")

    def test_cleanup_all_removes_all_data(self):
        """Test that cleanup_all removes all tracking data."""
        tracker = OrderTracker()

        # Add multiple orders
        for i in range(3):
            order_id = f"order-{i}"
            tracker.create_event(order_id)
            tracker.update_order_status(order_id, status="filled")

        stats_before = tracker.get_tracking_stats()
        assert stats_before["total_orders"] == 3

        tracker.cleanup_all()

        stats_after = tracker.get_tracking_stats()
        assert stats_after["total_orders"] == 0
        assert stats_after["orders_with_status"] == 0


class TestOrderTrackerStatistics:
    """Test statistics tracking."""

    def test_get_tracking_stats_returns_correct_counts(self):
        """Test that get_tracking_stats returns correct counts."""
        tracker = OrderTracker()
        price = Decimal("150.25")

        tracker.create_event("order-1")
        tracker.update_order_status("order-2", status="filled", avg_price=price)
        tracker.update_order_status("order-3", status="pending")

        stats = tracker.get_tracking_stats()

        assert stats["total_orders"] == 1  # Only order-1 has explicit event
        assert stats["orders_with_status"] == 2  # order-2 and order-3
        assert stats["orders_with_price"] == 1  # Only order-2
        assert stats["completed_orders"] == 1  # Only order-2 (filled)

    def test_get_tracking_stats_handles_none_prices(self):
        """Test that get_tracking_stats correctly counts only non-None prices."""
        tracker = OrderTracker()

        tracker.update_order_status("order-1", avg_price=Decimal("100.00"))
        tracker.update_order_status("order-2", avg_price=None)

        stats = tracker.get_tracking_stats()

        assert stats["orders_with_price"] == 1


class TestOrderTrackerThreadSafety:
    """Test thread safety of OrderTracker operations."""

    def test_concurrent_event_creation(self):
        """Test that concurrent event creation is thread-safe."""
        tracker = OrderTracker()
        order_id = "test-order"
        events = []

        def create_event():
            event = tracker.create_event(order_id)
            events.append(event)

        threads = [threading.Thread(target=create_event) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # All threads should get the same event instance
        assert len(set(id(e) for e in events)) == 1

    def test_concurrent_status_updates(self):
        """Test that concurrent status updates are thread-safe."""
        tracker = OrderTracker()
        order_id = "test-order"

        def update_status(status):
            tracker.update_order_status(order_id, status=status)

        threads = [threading.Thread(target=update_status, args=(f"status-{i}",)) for i in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Should have one of the statuses (no crashes/exceptions)
        final_status = tracker.get_status(order_id)
        assert final_status is not None
        assert final_status.startswith("status-")
