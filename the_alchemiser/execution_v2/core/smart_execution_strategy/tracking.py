"""Business Unit: execution | Status: current.

Order tracking and state management for smart execution strategy.

This module manages the state of active orders including tracking for re-pegging,
placement times, anchor prices, and repeg counts.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from the_alchemiser.shared.logging import get_logger

from .models import SmartOrderRequest

logger = get_logger(__name__)


class OrderTracker:
    """Manages tracking state for active orders during smart execution."""

    def __init__(self) -> None:
        """Initialize order tracker with empty state."""
        # Track active orders for re-pegging
        self._active_orders: dict[str, SmartOrderRequest] = {}
        self._repeg_counts: dict[str, int] = {}
        self._order_placement_times: dict[str, datetime] = {}
        self._order_anchor_prices: dict[str, Decimal] = {}
        # Track price history to prevent re-pegging at same prices
        self._price_history: dict[str, list[Decimal]] = {}
        # Track filled quantities for partial fill handling
        self._filled_quantities: dict[str, Decimal] = {}
        # Track idempotency keys for order operations to prevent duplicates
        self._operation_keys: set[str] = set()

    def add_order(
        self,
        order_id: str,
        request: SmartOrderRequest,
        placement_time: datetime,
        anchor_price: Decimal,
    ) -> None:
        """Add a new order to tracking.

        Args:
            order_id: Order ID to track
            request: Original order request
            placement_time: When the order was placed
            anchor_price: Price at which order was anchored

        """
        self._active_orders[order_id] = request
        self._repeg_counts[order_id] = 0
        self._order_placement_times[order_id] = placement_time
        self._order_anchor_prices[order_id] = anchor_price
        # Initialize price history with the initial anchor price
        self._price_history[order_id] = [anchor_price]
        # Initialize filled quantity tracking
        self._filled_quantities[order_id] = Decimal("0")

        logger.debug(f"📊 Added order {order_id} to tracking (anchor: ${anchor_price})")

    def update_order(
        self,
        old_order_id: str,
        new_order_id: str,
        new_anchor_price: Decimal,
        placement_time: datetime,
    ) -> None:
        """Update order tracking when re-pegging creates a new order.

        Args:
            old_order_id: Previous order ID to remove
            new_order_id: New order ID to track
            new_anchor_price: New anchor price
            placement_time: When the new order was placed

        """
        # Preserve the request and increment repeg count
        request = self._active_orders.get(old_order_id)
        old_repeg_count = self._repeg_counts.get(old_order_id, 0)
        # Preserve price history to prevent re-pegging at same prices
        price_history = self._price_history.get(old_order_id, [])
        # Preserve filled quantity for cumulative tracking across repegs
        filled_quantity = self._filled_quantities.get(old_order_id, Decimal("0"))

        if request:
            # Remove old tracking
            self.remove_order(old_order_id)

            # Add new tracking with incremented count and extended price history
            self._active_orders[new_order_id] = request
            self._repeg_counts[new_order_id] = old_repeg_count + 1
            self._order_placement_times[new_order_id] = placement_time
            self._order_anchor_prices[new_order_id] = new_anchor_price
            # Transfer and extend price history
            self._price_history[new_order_id] = [*price_history, new_anchor_price]
            # Transfer filled quantity tracking
            self._filled_quantities[new_order_id] = filled_quantity

            logger.debug(
                f"📊 Updated order tracking: {old_order_id} -> {new_order_id} "
                f"(repeg count: {old_repeg_count + 1}, new anchor: ${new_anchor_price}, "
                f"cumulative filled: {filled_quantity})"
            )

    def remove_order(self, order_id: str) -> None:
        """Remove order from tracking.

        Args:
            order_id: Order ID to remove

        """
        self._active_orders.pop(order_id, None)
        self._repeg_counts.pop(order_id, None)
        self._order_placement_times.pop(order_id, None)
        self._order_anchor_prices.pop(order_id, None)
        self._price_history.pop(order_id, None)
        self._filled_quantities.pop(order_id, None)

        logger.debug(f"📊 Removed order {order_id} from tracking")

    def get_order_request(self, order_id: str) -> SmartOrderRequest | None:
        """Get the original order request for an order ID.

        Args:
            order_id: Order ID to look up

        Returns:
            Original order request or None if not found

        """
        return self._active_orders.get(order_id)

    def get_repeg_count(self, order_id: str) -> int:
        """Get the current repeg count for an order.

        Args:
            order_id: Order ID to check

        Returns:
            Current repeg count (0 if not found)

        """
        return self._repeg_counts.get(order_id, 0)

    def get_placement_time(self, order_id: str) -> datetime | None:
        """Get the placement time for an order.

        Args:
            order_id: Order ID to check

        Returns:
            Placement time or None if not found

        """
        return self._order_placement_times.get(order_id)

    def get_anchor_price(self, order_id: str) -> Decimal | None:
        """Get the anchor price for an order.

        Args:
            order_id: Order ID to check

        Returns:
            Anchor price or None if not found

        """
        return self._order_anchor_prices.get(order_id)

    def get_price_history(self, order_id: str) -> list[Decimal]:
        """Get the price history for an order.

        Args:
            order_id: Order ID to check

        Returns:
            List of prices used for this order chain (empty if not found)

        """
        return self._price_history.get(order_id, [])

    def get_filled_quantity(self, order_id: str) -> Decimal:
        """Get the filled quantity for an order.

        Args:
            order_id: Order ID to check

        Returns:
            Filled quantity (Decimal("0") if not found)

        """
        return self._filled_quantities.get(order_id, Decimal("0"))

    def update_filled_quantity(self, order_id: str, filled_quantity: Decimal) -> None:
        """Update the filled quantity for an order.

        Args:
            order_id: Order ID to update
            filled_quantity: New filled quantity

        """
        if order_id in self._active_orders:
            old_filled = self._filled_quantities.get(order_id, Decimal("0"))
            self._filled_quantities[order_id] = filled_quantity

            if filled_quantity != old_filled:
                logger.info(
                    f"📊 Updated filled quantity for {order_id}: {old_filled} -> {filled_quantity}"
                )

    def get_remaining_quantity(self, order_id: str) -> Decimal:
        """Get the remaining quantity for an order (original - filled).

        Args:
            order_id: Order ID to check

        Returns:
            Remaining quantity to be filled (Decimal("0") if order not found)

        """
        request = self._active_orders.get(order_id)
        if not request:
            return Decimal("0")

        filled = self._filled_quantities.get(order_id, Decimal("0"))
        remaining = request.quantity - filled

        # Ensure remaining is non-negative
        return max(remaining, Decimal("0"))

    def get_active_orders(self) -> dict[str, SmartOrderRequest]:
        """Get all active orders being tracked.

        Returns:
            Dictionary of order_id -> SmartOrderRequest

        """
        return self._active_orders.copy()

    def get_active_order_count(self) -> int:
        """Get count of active orders being monitored.

        Returns:
            Number of active orders

        """
        return len(self._active_orders)

    def clear_completed_orders(self) -> None:
        """Clear tracking for all orders."""
        self._active_orders.clear()
        self._repeg_counts.clear()
        self._order_placement_times.clear()
        self._order_anchor_prices.clear()
        self._price_history.clear()
        self._filled_quantities.clear()
        self._operation_keys.clear()

        logger.info("📊 Cleared all order tracking data")

    def generate_idempotency_key(
        self, order_id: str, operation: str, timestamp: datetime
    ) -> str:
        """Generate an idempotency key for an order operation.

        Args:
            order_id: Order ID
            operation: Operation type (e.g., 'repeg', 'escalate')
            timestamp: Timestamp of the operation (ISO format)

        Returns:
            Idempotency key string

        """
        import hashlib

        repeg_count = self.get_repeg_count(order_id)
        # Create a deterministic key from order_id, operation, repeg_count, and timestamp
        key_parts = f"{order_id}:{operation}:{repeg_count}:{timestamp.isoformat()}"
        return hashlib.sha256(key_parts.encode()).hexdigest()[:16]

    def check_and_record_operation(
        self, order_id: str, operation: str, timestamp: datetime
    ) -> bool:
        """Check if operation has been performed and record it if not.

        Args:
            order_id: Order ID
            operation: Operation type (e.g., 'repeg', 'escalate')
            timestamp: Timestamp of the operation

        Returns:
            True if operation is new (not duplicate), False if duplicate

        """
        idempotency_key = self.generate_idempotency_key(order_id, operation, timestamp)

        if idempotency_key in self._operation_keys:
            logger.warning(
                "Duplicate operation detected, skipping",
                order_id=order_id,
                operation=operation,
                idempotency_key=idempotency_key,
            )
            return False

        self._operation_keys.add(idempotency_key)
        logger.debug(
            "Recorded new operation",
            order_id=order_id,
            operation=operation,
            idempotency_key=idempotency_key,
        )
        return True
