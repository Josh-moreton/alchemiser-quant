"""Business Unit: order execution/placement | Status: current

In-memory order router adapter for smoke validation.

TODO: Replace with production broker adapter (e.g., Alpaca, Interactive Brokers)
FIXME: This simplified adapter only simulates order execution
"""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from the_alchemiser.execution.application.ports import (
    CancelAckVO,
    OrderAckVO,
    OrderRouterPort,
    OrderStatusVO,
)
from the_alchemiser.portfolio.application.contracts.rebalance_plan_contract_v1 import PlannedOrderV1
from the_alchemiser.shared_kernel.providers.uuid_provider import UUIDProviderPort


class InMemoryOrderRouterAdapter(OrderRouterPort):
    """Simple in-memory order router for smoke validation.

    Simulates immediate order execution with deterministic fills.

    TODO: Replace with production broker implementation
    FIXME: No real order management or partial fills in current implementation
    """

    def __init__(
        self, uuid_provider: UUIDProviderPort, fill_price: Decimal = Decimal("100.0")
    ) -> None:
        """Initialize with UUID provider and default fill price.

        Args:
            uuid_provider: Provider for deterministic UUIDs
            fill_price: Fixed price for all simulated fills

        """
        self._uuid_provider = uuid_provider
        self._fill_price = fill_price
        self._submitted_orders: dict[UUID, PlannedOrderV1] = {}
        self._order_statuses: dict[UUID, str] = {}

    def submit_order(self, order: PlannedOrderV1) -> OrderAckVO:
        """Submit order to simulated broker for execution.

        Args:
            order: Validated planned order ready for submission

        Returns:
            OrderAckVO with broker response and tracking info

        """
        # Store the order
        self._submitted_orders[order.order_id] = order
        self._order_statuses[order.order_id] = "filled"  # Simulate immediate fill

        # Generate broker order ID
        broker_order_id = f"BROKER-{order.order_id}"

        return OrderAckVO(
            order_id=order.order_id,
            accepted=True,
            broker_order_id=broker_order_id,
            message=f"Order accepted and filled: {order.side} {order.quantity} {order.symbol}",
            timestamp=datetime.now(UTC),
        )

    def cancel_order(self, order_id: UUID) -> CancelAckVO:
        """Cancel existing order by ID.

        Args:
            order_id: Order identifier to cancel

        Returns:
            CancelAckVO with cancellation status

        """
        if order_id not in self._submitted_orders:
            return CancelAckVO(
                order_id=order_id,
                cancelled=False,
                message="Order not found",
                timestamp=datetime.now(UTC),
            )

        # Simulate cancellation (though orders are immediately filled in this adapter)
        status = self._order_statuses.get(order_id, "unknown")
        if status == "filled":
            return CancelAckVO(
                order_id=order_id,
                cancelled=False,
                message="Cannot cancel - order already filled",
                timestamp=datetime.now(UTC),
            )

        self._order_statuses[order_id] = "cancelled"
        return CancelAckVO(
            order_id=order_id,
            cancelled=True,
            message="Order cancelled successfully",
            timestamp=datetime.now(UTC),
        )

    def get_order_status(self, order_id: UUID) -> OrderStatusVO:
        """Get current status of submitted order.

        Args:
            order_id: Order identifier to check

        Returns:
            OrderStatusVO with current state and fills

        """
        order = self._submitted_orders.get(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")

        status = self._order_statuses.get(order_id, "unknown")

        if status == "filled":
            return OrderStatusVO(
                order_id=order_id,
                status="filled",
                filled_quantity=order.quantity,
                remaining_quantity=Decimal("0"),
                average_fill_price=self._fill_price,
                last_update=datetime.now(UTC),
            )

        return OrderStatusVO(
            order_id=order_id,
            status=status,
            filled_quantity=Decimal("0"),
            remaining_quantity=order.quantity,
            average_fill_price=None,
            last_update=datetime.now(UTC),
        )

    def get_submitted_orders(self) -> list[PlannedOrderV1]:
        """Get all submitted orders (for smoke validation purposes).

        TODO: Remove this method in production - only needed for smoke validation
        """
        return list(self._submitted_orders.values())

    def clear_orders(self) -> None:
        """Clear all orders (for smoke validation purposes).

        TODO: Remove this method in production - only needed for smoke validation
        """
        self._submitted_orders.clear()
        self._order_statuses.clear()
