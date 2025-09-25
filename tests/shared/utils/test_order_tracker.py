"""Business Unit: shared | Status: current"""

from the_alchemiser.shared.utils.order_tracker import OrderTracker


def test_signal_completion_without_prior_event() -> None:
    tracker = OrderTracker()
    order_id = "test-order-123"

    tracker.update_order_status(order_id, "FILLED")
    tracker.signal_completion(order_id)

    assert tracker.wait_for_completion(order_id, timeout=0.01)
    assert tracker.get_status(order_id) == "filled"


def test_update_order_status_normalizes_case() -> None:
    tracker = OrderTracker()
    order_id = "test-order-456"

    tracker.update_order_status(order_id, "CANCELED")

    assert tracker.get_status(order_id) == "canceled"
