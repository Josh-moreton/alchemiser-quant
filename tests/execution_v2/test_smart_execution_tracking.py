"""Business Unit: execution | Status: current.

Comprehensive tests for smart execution strategy order tracking module.

Tests cover:
- Input validation and error handling
- Order lifecycle (add, update, remove)
- Filled quantity tracking across repegs
- Correlation ID propagation
- Edge cases and error conditions
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from the_alchemiser.execution_v2.core.smart_execution_strategy.tracking import (
    OrderTracker,
    OrderTrackerError,
)


# Mock SmartOrderRequest for testing
class MockSmartOrderRequest:
    """Mock for SmartOrderRequest to avoid full imports."""

    def __init__(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        correlation_id: str,
        is_complete_exit: bool = False,
    ):
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.correlation_id = correlation_id
        self.is_complete_exit = is_complete_exit


class TestOrderTrackerInitialization:
    """Test OrderTracker initialization."""

    def test_init_creates_empty_tracker(self):
        """Test that initialization creates empty tracking state."""
        tracker = OrderTracker()

        assert tracker.get_active_order_count() == 0
        assert tracker.get_active_orders() == {}


class TestOrderTrackerAddOrder:
    """Test add_order method."""

    def test_add_order_success(self):
        """Test successfully adding an order to tracking."""
        tracker = OrderTracker()
        order_id = "order-123"
        request = MockSmartOrderRequest(
            symbol="SPY",
            side="BUY",
            quantity=Decimal("100"),
            correlation_id="corr-456",
        )
        placement_time = datetime.now(UTC)
        anchor_price = Decimal("450.50")

        tracker.add_order(order_id, request, placement_time, anchor_price)

        assert tracker.get_order_request(order_id) == request
        assert tracker.get_repeg_count(order_id) == 0
        assert tracker.get_placement_time(order_id) == placement_time
        assert tracker.get_anchor_price(order_id) == anchor_price
        assert tracker.get_price_history(order_id) == [anchor_price]
        assert tracker.get_filled_quantity(order_id) == Decimal("0")
        assert tracker.get_active_order_count() == 1

    def test_add_order_with_empty_order_id_raises_error(self):
        """Test that empty order_id raises OrderTrackerError."""
        tracker = OrderTracker()
        request = MockSmartOrderRequest(
            symbol="SPY", side="BUY", quantity=Decimal("100"), correlation_id="corr-1"
        )

        with pytest.raises(OrderTrackerError, match="must be non-empty string"):
            tracker.add_order("", request, datetime.now(UTC), Decimal("100"))

    def test_add_order_with_none_order_id_raises_error(self):
        """Test that None order_id raises OrderTrackerError."""
        tracker = OrderTracker()
        request = MockSmartOrderRequest(
            symbol="SPY", side="BUY", quantity=Decimal("100"), correlation_id="corr-1"
        )

        with pytest.raises(OrderTrackerError, match="must be non-empty string"):
            tracker.add_order(None, request, datetime.now(UTC), Decimal("100"))  # type: ignore

    def test_add_order_with_negative_anchor_price_raises_error(self):
        """Test that negative anchor_price raises OrderTrackerError."""
        tracker = OrderTracker()
        request = MockSmartOrderRequest(
            symbol="SPY", side="BUY", quantity=Decimal("100"), correlation_id="corr-1"
        )

        with pytest.raises(OrderTrackerError, match="must be positive"):
            tracker.add_order("order-1", request, datetime.now(UTC), Decimal("-10"))

    def test_add_order_with_zero_anchor_price_raises_error(self):
        """Test that zero anchor_price raises OrderTrackerError."""
        tracker = OrderTracker()
        request = MockSmartOrderRequest(
            symbol="SPY", side="BUY", quantity=Decimal("100"), correlation_id="corr-1"
        )

        with pytest.raises(OrderTrackerError, match="must be positive"):
            tracker.add_order("order-1", request, datetime.now(UTC), Decimal("0"))

    def test_add_order_with_naive_datetime_raises_error(self):
        """Test that timezone-naive datetime raises OrderTrackerError."""
        tracker = OrderTracker()
        request = MockSmartOrderRequest(
            symbol="SPY", side="BUY", quantity=Decimal("100"), correlation_id="corr-1"
        )
        naive_time = datetime.now()  # No timezone

        with pytest.raises(OrderTrackerError, match="must be timezone-aware"):
            tracker.add_order("order-1", request, naive_time, Decimal("100"))


class TestOrderTrackerUpdateOrder:
    """Test update_order method for repeg operations."""

    def test_update_order_success(self):
        """Test successfully updating an order during repeg."""
        tracker = OrderTracker()
        old_order_id = "old-order-123"
        new_order_id = "new-order-456"
        request = MockSmartOrderRequest(
            symbol="TECL", side="SELL", quantity=Decimal("50"), correlation_id="corr-789"
        )

        # Add initial order
        tracker.add_order(old_order_id, request, datetime.now(UTC), Decimal("100.00"))

        # Update with partial fill
        tracker.update_filled_quantity(old_order_id, Decimal("20"))

        # Repeg to new order
        new_anchor = Decimal("100.25")
        new_placement_time = datetime.now(UTC) + timedelta(seconds=10)
        tracker.update_order(old_order_id, new_order_id, new_anchor, new_placement_time)

        # Verify new order exists with incremented repeg count
        assert tracker.get_order_request(new_order_id) == request
        assert tracker.get_repeg_count(new_order_id) == 1
        assert tracker.get_anchor_price(new_order_id) == new_anchor
        assert tracker.get_placement_time(new_order_id) == new_placement_time

        # Verify filled quantity was preserved
        assert tracker.get_filled_quantity(new_order_id) == Decimal("20")

        # Verify price history was extended
        assert tracker.get_price_history(new_order_id) == [Decimal("100.00"), new_anchor]

        # Verify old order was removed
        assert tracker.get_order_request(old_order_id) is None
        assert tracker.get_active_order_count() == 1

    def test_update_order_increments_repeg_count(self):
        """Test that multiple repegs correctly increment count."""
        tracker = OrderTracker()
        request = MockSmartOrderRequest(
            symbol="SPY", side="BUY", quantity=Decimal("100"), correlation_id="corr-1"
        )

        # Add initial order
        tracker.add_order("order-1", request, datetime.now(UTC), Decimal("450.00"))
        assert tracker.get_repeg_count("order-1") == 0

        # First repeg
        tracker.update_order("order-1", "order-2", Decimal("450.10"), datetime.now(UTC))
        assert tracker.get_repeg_count("order-2") == 1

        # Second repeg
        tracker.update_order("order-2", "order-3", Decimal("450.20"), datetime.now(UTC))
        assert tracker.get_repeg_count("order-3") == 2

    def test_update_order_with_missing_old_order_raises_error(self):
        """Test that updating non-existent order raises OrderTrackerError."""
        tracker = OrderTracker()

        with pytest.raises(OrderTrackerError, match="not found in tracking"):
            tracker.update_order(
                "nonexistent-order", "new-order", Decimal("100"), datetime.now(UTC)
            )

    def test_update_order_with_empty_new_order_id_raises_error(self):
        """Test that empty new_order_id raises OrderTrackerError."""
        tracker = OrderTracker()
        request = MockSmartOrderRequest(
            symbol="SPY", side="BUY", quantity=Decimal("100"), correlation_id="corr-1"
        )
        tracker.add_order("order-1", request, datetime.now(UTC), Decimal("100"))

        with pytest.raises(OrderTrackerError, match="must be non-empty string"):
            tracker.update_order("order-1", "", Decimal("100"), datetime.now(UTC))

    def test_update_order_with_negative_price_raises_error(self):
        """Test that negative new_anchor_price raises OrderTrackerError."""
        tracker = OrderTracker()
        request = MockSmartOrderRequest(
            symbol="SPY", side="BUY", quantity=Decimal("100"), correlation_id="corr-1"
        )
        tracker.add_order("order-1", request, datetime.now(UTC), Decimal("100"))

        with pytest.raises(OrderTrackerError, match="must be positive"):
            tracker.update_order("order-1", "order-2", Decimal("-10"), datetime.now(UTC))

    def test_update_order_with_naive_datetime_raises_error(self):
        """Test that timezone-naive datetime raises OrderTrackerError."""
        tracker = OrderTracker()
        request = MockSmartOrderRequest(
            symbol="SPY", side="BUY", quantity=Decimal("100"), correlation_id="corr-1"
        )
        tracker.add_order("order-1", request, datetime.now(UTC), Decimal("100"))

        with pytest.raises(OrderTrackerError, match="must be timezone-aware"):
            tracker.update_order("order-1", "order-2", Decimal("100"), datetime.now())


class TestOrderTrackerRemoveOrder:
    """Test remove_order method."""

    def test_remove_order_success(self):
        """Test successfully removing an order."""
        tracker = OrderTracker()
        request = MockSmartOrderRequest(
            symbol="SPY", side="BUY", quantity=Decimal("100"), correlation_id="corr-1"
        )
        tracker.add_order("order-1", request, datetime.now(UTC), Decimal("100"))

        tracker.remove_order("order-1")

        assert tracker.get_order_request("order-1") is None
        assert tracker.get_active_order_count() == 0

    def test_remove_order_is_idempotent(self):
        """Test that removing non-existent order succeeds silently."""
        tracker = OrderTracker()

        # Should not raise error
        tracker.remove_order("nonexistent-order")

        assert tracker.get_active_order_count() == 0

    def test_remove_order_with_empty_order_id_raises_error(self):
        """Test that empty order_id raises OrderTrackerError."""
        tracker = OrderTracker()

        with pytest.raises(OrderTrackerError, match="must be non-empty string"):
            tracker.remove_order("")

    def test_remove_order_with_none_order_id_raises_error(self):
        """Test that None order_id raises OrderTrackerError."""
        tracker = OrderTracker()

        with pytest.raises(OrderTrackerError, match="must be non-empty string"):
            tracker.remove_order(None)  # type: ignore


class TestOrderTrackerFilledQuantity:
    """Test filled quantity tracking methods."""

    def test_update_filled_quantity_success(self):
        """Test successfully updating filled quantity."""
        tracker = OrderTracker()
        request = MockSmartOrderRequest(
            symbol="SPY", side="BUY", quantity=Decimal("100"), correlation_id="corr-1"
        )
        tracker.add_order("order-1", request, datetime.now(UTC), Decimal("450"))

        tracker.update_filled_quantity("order-1", Decimal("30"))

        assert tracker.get_filled_quantity("order-1") == Decimal("30")
        assert tracker.get_remaining_quantity("order-1") == Decimal("70")

    def test_update_filled_quantity_with_missing_order_raises_error(self):
        """Test that updating filled quantity for non-existent order raises error."""
        tracker = OrderTracker()

        with pytest.raises(OrderTrackerError, match="not found in tracking"):
            tracker.update_filled_quantity("nonexistent-order", Decimal("10"))

    def test_update_filled_quantity_with_negative_value_raises_error(self):
        """Test that negative filled_quantity raises OrderTrackerError."""
        tracker = OrderTracker()
        request = MockSmartOrderRequest(
            symbol="SPY", side="BUY", quantity=Decimal("100"), correlation_id="corr-1"
        )
        tracker.add_order("order-1", request, datetime.now(UTC), Decimal("100"))

        with pytest.raises(OrderTrackerError, match="must be non-negative"):
            tracker.update_filled_quantity("order-1", Decimal("-10"))

    def test_get_filled_quantity_for_missing_order_returns_zero(self):
        """Test that getting filled quantity for missing order returns 0."""
        tracker = OrderTracker()

        assert tracker.get_filled_quantity("nonexistent-order") == Decimal("0")

    def test_get_remaining_quantity_handles_overfill(self):
        """Test that remaining quantity is never negative (overfill protection)."""
        tracker = OrderTracker()
        request = MockSmartOrderRequest(
            symbol="SPY", side="BUY", quantity=Decimal("100"), correlation_id="corr-1"
        )
        tracker.add_order("order-1", request, datetime.now(UTC), Decimal("450"))

        # Simulate overfill (more filled than original - can happen with broker quirks)
        tracker.update_filled_quantity("order-1", Decimal("120"))

        assert tracker.get_remaining_quantity("order-1") == Decimal("0")

    def test_filled_quantity_preserved_across_repegs(self):
        """Test that filled quantity is preserved when order is re-pegged."""
        tracker = OrderTracker()
        request = MockSmartOrderRequest(
            symbol="TECL", side="SELL", quantity=Decimal("100"), correlation_id="corr-1"
        )
        tracker.add_order("order-1", request, datetime.now(UTC), Decimal("50.00"))

        # Partial fill
        tracker.update_filled_quantity("order-1", Decimal("40"))

        # Repeg
        tracker.update_order("order-1", "order-2", Decimal("50.10"), datetime.now(UTC))

        # Verify filled quantity was preserved
        assert tracker.get_filled_quantity("order-2") == Decimal("40")
        assert tracker.get_remaining_quantity("order-2") == Decimal("60")


class TestOrderTrackerGetters:
    """Test various getter methods."""

    def test_get_order_request_returns_none_for_missing_order(self):
        """Test that get_order_request returns None for missing order."""
        tracker = OrderTracker()

        assert tracker.get_order_request("nonexistent-order") is None

    def test_get_repeg_count_returns_zero_for_missing_order(self):
        """Test that get_repeg_count returns 0 for missing order."""
        tracker = OrderTracker()

        assert tracker.get_repeg_count("nonexistent-order") == 0

    def test_get_placement_time_returns_none_for_missing_order(self):
        """Test that get_placement_time returns None for missing order."""
        tracker = OrderTracker()

        assert tracker.get_placement_time("nonexistent-order") is None

    def test_get_anchor_price_returns_none_for_missing_order(self):
        """Test that get_anchor_price returns None for missing order."""
        tracker = OrderTracker()

        assert tracker.get_anchor_price("nonexistent-order") is None

    def test_get_price_history_returns_empty_list_for_missing_order(self):
        """Test that get_price_history returns [] for missing order."""
        tracker = OrderTracker()

        assert tracker.get_price_history("nonexistent-order") == []

    def test_get_remaining_quantity_returns_zero_for_missing_order(self):
        """Test that get_remaining_quantity returns 0 for missing order."""
        tracker = OrderTracker()

        assert tracker.get_remaining_quantity("nonexistent-order") == Decimal("0")

    def test_get_active_orders_returns_copy(self):
        """Test that get_active_orders returns a copy (not internal dict)."""
        tracker = OrderTracker()
        request = MockSmartOrderRequest(
            symbol="SPY", side="BUY", quantity=Decimal("100"), correlation_id="corr-1"
        )
        tracker.add_order("order-1", request, datetime.now(UTC), Decimal("450"))

        orders = tracker.get_active_orders()
        orders["order-2"] = request  # Modify copy

        # Original should be unchanged
        assert tracker.get_active_order_count() == 1
        assert "order-2" not in tracker.get_active_orders()


class TestOrderTrackerClearOrders:
    """Test clear_completed_orders method."""

    def test_clear_completed_orders_empties_all_tracking(self):
        """Test that clear removes all tracked orders."""
        tracker = OrderTracker()
        request1 = MockSmartOrderRequest(
            symbol="SPY", side="BUY", quantity=Decimal("100"), correlation_id="corr-1"
        )
        request2 = MockSmartOrderRequest(
            symbol="QQQ", side="SELL", quantity=Decimal("50"), correlation_id="corr-2"
        )

        tracker.add_order("order-1", request1, datetime.now(UTC), Decimal("450"))
        tracker.add_order("order-2", request2, datetime.now(UTC), Decimal("380"))

        assert tracker.get_active_order_count() == 2

        tracker.clear_completed_orders()

        assert tracker.get_active_order_count() == 0
        assert tracker.get_active_orders() == {}

    def test_clear_completed_orders_on_empty_tracker(self):
        """Test that clearing an empty tracker succeeds without error."""
        tracker = OrderTracker()

        # Should not raise error
        tracker.clear_completed_orders()

        assert tracker.get_active_order_count() == 0


class TestOrderTrackerPriceHistory:
    """Test price history tracking across repegs."""

    def test_price_history_extends_on_repeg(self):
        """Test that price history accumulates across repegs."""
        tracker = OrderTracker()
        request = MockSmartOrderRequest(
            symbol="SPY", side="BUY", quantity=Decimal("100"), correlation_id="corr-1"
        )

        # Initial order
        tracker.add_order("order-1", request, datetime.now(UTC), Decimal("450.00"))
        assert tracker.get_price_history("order-1") == [Decimal("450.00")]

        # First repeg
        tracker.update_order("order-1", "order-2", Decimal("450.10"), datetime.now(UTC))
        assert tracker.get_price_history("order-2") == [
            Decimal("450.00"),
            Decimal("450.10"),
        ]

        # Second repeg
        tracker.update_order("order-2", "order-3", Decimal("450.20"), datetime.now(UTC))
        assert tracker.get_price_history("order-3") == [
            Decimal("450.00"),
            Decimal("450.10"),
            Decimal("450.20"),
        ]


class TestOrderTrackerEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_multiple_orders_tracked_independently(self):
        """Test that multiple orders are tracked independently."""
        tracker = OrderTracker()
        request1 = MockSmartOrderRequest(
            symbol="SPY", side="BUY", quantity=Decimal("100"), correlation_id="corr-1"
        )
        request2 = MockSmartOrderRequest(
            symbol="QQQ", side="SELL", quantity=Decimal("50"), correlation_id="corr-2"
        )

        tracker.add_order("order-1", request1, datetime.now(UTC), Decimal("450"))
        tracker.add_order("order-2", request2, datetime.now(UTC), Decimal("380"))

        # Update one order
        tracker.update_filled_quantity("order-1", Decimal("30"))

        # Verify independence
        assert tracker.get_filled_quantity("order-1") == Decimal("30")
        assert tracker.get_filled_quantity("order-2") == Decimal("0")
        assert tracker.get_active_order_count() == 2

    def test_decimal_precision_maintained(self):
        """Test that Decimal precision is maintained throughout operations."""
        tracker = OrderTracker()
        request = MockSmartOrderRequest(
            symbol="SPY", side="BUY", quantity=Decimal("100.5"), correlation_id="corr-1"
        )

        anchor = Decimal("450.123456")
        tracker.add_order("order-1", request, datetime.now(UTC), anchor)

        assert tracker.get_anchor_price("order-1") == Decimal("450.123456")

        tracker.update_filled_quantity("order-1", Decimal("30.25"))
        assert tracker.get_filled_quantity("order-1") == Decimal("30.25")
        assert tracker.get_remaining_quantity("order-1") == Decimal("70.25")
