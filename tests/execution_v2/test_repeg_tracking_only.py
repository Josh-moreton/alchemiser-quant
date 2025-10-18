"""Business Unit: execution | Status: current

Simple test for the order tracker quantity fix without full imports.
"""

from datetime import UTC, datetime
from decimal import Decimal


# Simple mock instead of importing full models
class MockSmartOrderRequest:
    def __init__(self, symbol: str, side: str, quantity: Decimal, is_complete_exit: bool = False):
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.is_complete_exit = is_complete_exit


def test_order_tracker_filled_quantity_tracking():
    """Test that order tracker correctly tracks filled quantities."""
    # Import directly to avoid circular imports
    import os
    import sys

    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

    from the_alchemiser.execution_v2.core.smart_execution_strategy.tracking import OrderTracker

    order_tracker = OrderTracker()
    order_id = "test-order-123"
    original_qty = Decimal("100")

    request = MockSmartOrderRequest(
        symbol="TECL",
        side="SELL",
        quantity=original_qty,
        is_complete_exit=False,
    )

    # Add order to tracker
    order_tracker.add_order(
        order_id=order_id,
        request=request,
        placement_time=datetime.now(UTC),
        anchor_price=Decimal("100.00"),
    )

    # Initially no fills
    assert order_tracker.get_filled_quantity(order_id) == Decimal("0")
    assert order_tracker.get_remaining_quantity(order_id) == original_qty

    # Update with partial fill
    filled_qty = Decimal("30")
    order_tracker.update_filled_quantity(order_id, filled_qty)

    assert order_tracker.get_filled_quantity(order_id) == filled_qty
    expected_remaining = original_qty - filled_qty
    assert order_tracker.get_remaining_quantity(order_id) == expected_remaining

    # Update with larger fill
    filled_qty = Decimal("80")
    order_tracker.update_filled_quantity(order_id, filled_qty)

    assert order_tracker.get_filled_quantity(order_id) == filled_qty
    expected_remaining = original_qty - filled_qty
    assert order_tracker.get_remaining_quantity(order_id) == expected_remaining

    # Test over-fill protection (should return 0, not negative)
    filled_qty = Decimal("120")  # More than original
    order_tracker.update_filled_quantity(order_id, filled_qty)

    assert order_tracker.get_filled_quantity(order_id) == filled_qty
    assert order_tracker.get_remaining_quantity(order_id) == Decimal("0")


def test_order_tracker_preserves_filled_qty_across_repegs():
    """Test that filled quantities are preserved across repeg operations."""
    import os
    import sys

    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

    from the_alchemiser.execution_v2.core.smart_execution_strategy.tracking import OrderTracker

    order_tracker = OrderTracker()
    old_order_id = "old-order-123"
    new_order_id = "new-order-456"
    original_qty = Decimal("100")
    filled_qty = Decimal("40")

    request = MockSmartOrderRequest(
        symbol="TECL",
        side="SELL",
        quantity=original_qty,
        is_complete_exit=False,
    )

    # Add initial order
    order_tracker.add_order(
        order_id=old_order_id,
        request=request,
        placement_time=datetime.now(UTC),
        anchor_price=Decimal("100.00"),
    )

    # Update with partial fill
    order_tracker.update_filled_quantity(old_order_id, filled_qty)

    # Simulate repeg (update order)
    order_tracker.update_order(
        old_order_id=old_order_id,
        new_order_id=new_order_id,
        new_anchor_price=Decimal("100.25"),
        placement_time=datetime.now(UTC),
    )

    # Verify filled quantity was preserved
    assert order_tracker.get_filled_quantity(new_order_id) == filled_qty
    expected_remaining = original_qty - filled_qty
    assert order_tracker.get_remaining_quantity(new_order_id) == expected_remaining

    # Verify old order was removed
    assert order_tracker.get_filled_quantity(old_order_id) == Decimal("0")
    assert order_tracker.get_remaining_quantity(old_order_id) == Decimal("0")


if __name__ == "__main__":
    test_order_tracker_filled_quantity_tracking()
    test_order_tracker_preserves_filled_qty_across_repegs()
    print("All tests passed!")
