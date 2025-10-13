"""Business Unit: execution | Status: current.

Order tracking and state management for smart execution strategy.

This module manages the state of active orders including tracking for re-pegging,
placement times, anchor prices, and repeg counts.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from the_alchemiser.shared.errors.exceptions import AlchemiserError
from the_alchemiser.shared.logging import get_logger

from .models import SmartOrderRequest

logger = get_logger(__name__)


class OrderTrackerError(AlchemiserError):
    """Error raised by OrderTracker operations for invalid inputs or states."""


class OrderTracker:
    """Manages tracking state for active orders during smart execution.

    Provides in-memory tracking of orders being managed by the smart execution
    strategy, including re-pegging history, partial fills, and timing information.

    Thread-safety: This class is NOT thread-safe. If concurrent access is required,
    external synchronization must be used.

    Raises:
        OrderTrackerError: For invalid inputs or operational errors.

    """

    def __init__(self) -> None:
        """Initialize order tracker with empty state.

        Post-conditions:
            - All tracking dictionaries are empty
            - Instance is ready to track orders
        """
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

        logger.debug("OrderTracker initialized")

    def add_order(
        self,
        order_id: str,
        request: SmartOrderRequest,
        placement_time: datetime,
        anchor_price: Decimal,
    ) -> None:
        """Add a new order to tracking.

        Args:
            order_id: Order ID to track. Must be non-empty string.
            request: Original order request containing symbol, side, quantity, correlation_id.
            placement_time: When the order was placed. Must be timezone-aware (UTC).
            anchor_price: Price at which order was anchored. Must be positive.

        Raises:
            OrderTrackerError: If order_id is empty, anchor_price is invalid,
                             or placement_time is not timezone-aware.

        Post-conditions:
            - Order is tracked in all internal dictionaries
            - Repeg count initialized to 0
            - Price history initialized with anchor_price
            - Filled quantity initialized to 0

        """
        # Input validation
        if not order_id or not isinstance(order_id, str):
            msg = f"order_id must be non-empty string, got: {type(order_id).__name__}"
            logger.error(msg, order_id=order_id if isinstance(order_id, str) else "invalid")
            raise OrderTrackerError(msg)

        if anchor_price <= Decimal("0"):
            msg = f"anchor_price must be positive, got: {anchor_price}"
            logger.error(
                msg,
                order_id=order_id,
                anchor_price=str(anchor_price),
                correlation_id=getattr(request, "correlation_id", None),
            )
            raise OrderTrackerError(msg)

        if placement_time.tzinfo is None:
            msg = "placement_time must be timezone-aware (UTC)"
            logger.error(
                msg,
                order_id=order_id,
                correlation_id=getattr(request, "correlation_id", None),
            )
            raise OrderTrackerError(msg)

        self._active_orders[order_id] = request
        self._repeg_counts[order_id] = 0
        self._order_placement_times[order_id] = placement_time
        self._order_anchor_prices[order_id] = anchor_price
        # Initialize price history with the initial anchor price
        self._price_history[order_id] = [anchor_price]
        # Initialize filled quantity tracking
        self._filled_quantities[order_id] = Decimal("0")

        logger.debug(
            "Added order to tracking",
            order_id=order_id,
            symbol=request.symbol,
            side=request.side,
            quantity=str(request.quantity),
            anchor_price=str(anchor_price),
            correlation_id=getattr(request, "correlation_id", None),
        )

    def update_order(
        self,
        old_order_id: str,
        new_order_id: str,
        new_anchor_price: Decimal,
        placement_time: datetime,
    ) -> None:
        """Update order tracking when re-pegging creates a new order.

        Args:
            old_order_id: Previous order ID to remove. Must exist in tracking.
            new_order_id: New order ID to track. Must be non-empty string.
            new_anchor_price: New anchor price. Must be positive.
            placement_time: When the new order was placed. Must be timezone-aware (UTC).

        Raises:
            OrderTrackerError: If old_order_id doesn't exist, new_order_id is invalid,
                             new_anchor_price is invalid, or placement_time is not timezone-aware.

        Post-conditions:
            - Old order removed from all tracking
            - New order added with incremented repeg count
            - Price history extended with new anchor price
            - Filled quantity preserved from old order

        """
        # Input validation
        if not new_order_id or not isinstance(new_order_id, str):
            msg = f"new_order_id must be non-empty string, got: {type(new_order_id).__name__}"
            logger.error(
                msg, new_order_id=new_order_id if isinstance(new_order_id, str) else "invalid"
            )
            raise OrderTrackerError(msg)

        if new_anchor_price <= Decimal("0"):
            msg = f"new_anchor_price must be positive, got: {new_anchor_price}"
            logger.error(
                msg,
                old_order_id=old_order_id,
                new_order_id=new_order_id,
                new_anchor_price=str(new_anchor_price),
            )
            raise OrderTrackerError(msg)

        if placement_time.tzinfo is None:
            msg = "placement_time must be timezone-aware (UTC)"
            logger.error(msg, old_order_id=old_order_id, new_order_id=new_order_id)
            raise OrderTrackerError(msg)

        # Preserve the request and increment repeg count
        request = self._active_orders.get(old_order_id)
        if not request:
            msg = f"Cannot update order: old_order_id '{old_order_id}' not found in tracking"
            logger.error(
                msg,
                old_order_id=old_order_id,
                new_order_id=new_order_id,
            )
            raise OrderTrackerError(msg)

        old_repeg_count = self._repeg_counts.get(old_order_id, 0)
        # Preserve price history to prevent re-pegging at same prices
        price_history = self._price_history.get(old_order_id, [])
        # Preserve filled quantity for cumulative tracking across repegs
        filled_quantity = self._filled_quantities.get(old_order_id, Decimal("0"))

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
            "Updated order tracking after repeg",
            old_order_id=old_order_id,
            new_order_id=new_order_id,
            repeg_count=old_repeg_count + 1,
            new_anchor_price=str(new_anchor_price),
            cumulative_filled=str(filled_quantity),
            symbol=request.symbol,
            correlation_id=getattr(request, "correlation_id", None),
        )

    def remove_order(self, order_id: str) -> None:
        """Remove order from tracking.

        Args:
            order_id: Order ID to remove. Must be non-empty string.

        Raises:
            OrderTrackerError: If order_id is empty or invalid.

        Note:
            This method is idempotent - removing a non-existent order_id succeeds
            silently without error. This allows safe cleanup even if order was
            already removed.

        """
        # Input validation
        if not order_id or not isinstance(order_id, str):
            msg = f"order_id must be non-empty string, got: {type(order_id).__name__}"
            logger.error(msg, order_id=order_id if isinstance(order_id, str) else "invalid")
            raise OrderTrackerError(msg)

        # Check if order exists before removal for logging purposes
        request = self._active_orders.get(order_id)

        self._active_orders.pop(order_id, None)
        self._repeg_counts.pop(order_id, None)
        self._order_placement_times.pop(order_id, None)
        self._order_anchor_prices.pop(order_id, None)
        self._price_history.pop(order_id, None)
        self._filled_quantities.pop(order_id, None)

        logger.debug(
            "Removed order from tracking",
            order_id=order_id,
            existed=request is not None,
            correlation_id=getattr(request, "correlation_id", None) if request else None,
        )

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
            order_id: Order ID to update. Must be non-empty string.
            filled_quantity: New filled quantity. Must be non-negative.

        Raises:
            OrderTrackerError: If order_id is invalid, filled_quantity is negative,
                             or order_id doesn't exist in tracking.

        Note:
            This method should be called when partial fills are detected to maintain
            accurate remaining quantity calculations across re-pegs.

        """
        # Input validation
        if not order_id or not isinstance(order_id, str):
            msg = f"order_id must be non-empty string, got: {type(order_id).__name__}"
            logger.error(msg, order_id=order_id if isinstance(order_id, str) else "invalid")
            raise OrderTrackerError(msg)

        if filled_quantity < Decimal("0"):
            msg = f"filled_quantity must be non-negative, got: {filled_quantity}"
            logger.error(msg, order_id=order_id, filled_quantity=str(filled_quantity))
            raise OrderTrackerError(msg)

        if order_id not in self._active_orders:
            msg = f"Cannot update filled quantity: order_id '{order_id}' not found in tracking"
            logger.error(msg, order_id=order_id, filled_quantity=str(filled_quantity))
            raise OrderTrackerError(msg)

        request = self._active_orders[order_id]
        old_filled = self._filled_quantities.get(order_id, Decimal("0"))
        self._filled_quantities[order_id] = filled_quantity

        logger.info(
            "Updated filled quantity for order",
            order_id=order_id,
            old_filled=str(old_filled),
            new_filled=str(filled_quantity),
            symbol=request.symbol,
            total_quantity=str(request.quantity),
            remaining=str(request.quantity - filled_quantity),
            correlation_id=getattr(request, "correlation_id", None),
        )

    def get_remaining_quantity(self, order_id: str) -> Decimal:
        """Get the remaining quantity for an order (original - filled).

        Args:
            order_id: Order ID to check

        Returns:
            Remaining quantity to be filled (Decimal("0") if order not found)

        Note:
            Return value is always non-negative, even if filled > original
            (which could happen due to broker reporting issues).

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
        """Clear tracking for all orders.

        Post-conditions:
            - All internal tracking dictionaries are empty
            - Instance is ready to track new orders

        Note:
            This is typically called at the end of an execution cycle to prepare
            for the next batch of orders.

        """
        self._active_orders.clear()
        self._repeg_counts.clear()
        self._order_placement_times.clear()
        self._order_anchor_prices.clear()
        self._price_history.clear()
        self._filled_quantities.clear()
        self._operation_keys.clear()

        logger.info("📊 Cleared all order tracking data")

    def generate_idempotency_key(self, order_id: str, operation: str, timestamp: datetime) -> str:
        """Generate an idempotency key for an order operation.

        Args:
            order_id: Order ID
            operation: Operation type (e.g., 'repeg', 'escalate')
            timestamp: Timestamp of the operation (ISO format)

        Returns:
            Idempotency key string (SHA-256 hash, truncated to 16 chars)

        Example:
            >>> from datetime import datetime, UTC
            >>> tracker = OrderTracker()
            >>> timestamp = datetime.now(UTC)
            >>> key = tracker.generate_idempotency_key("order-123", "repeg", timestamp)
            >>> print(len(key))  # 16 characters
            16

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

        This method provides idempotency protection by tracking which operations
        have been attempted. If an operation has already been recorded, it returns
        False to indicate a duplicate.

        Args:
            order_id: Order ID
            operation: Operation type (e.g., 'repeg', 'escalate')
            timestamp: Timestamp of the operation

        Returns:
            True if operation is new (not duplicate), False if duplicate

        Example:
            >>> from datetime import datetime, UTC
            >>> tracker = OrderTracker()
            >>> timestamp = datetime.now(UTC)
            >>> # First attempt - should succeed
            >>> result1 = tracker.check_and_record_operation("order-123", "repeg", timestamp)
            >>> print(result1)
            True
            >>> # Second attempt with same parameters - should be blocked
            >>> result2 = tracker.check_and_record_operation("order-123", "repeg", timestamp)
            >>> print(result2)
            False

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
