"""Business Unit: order execution/placement; Status: current."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal

from the_alchemiser.shared_kernel.value_objects.money import Money
from the_alchemiser.execution.domain.value_objects.order_id import OrderId
from the_alchemiser.execution.domain.value_objects.order_status import OrderStatus
from the_alchemiser.execution.domain.value_objects.order_type import OrderType
from the_alchemiser.execution.domain.value_objects.quantity import Quantity
from the_alchemiser.execution.domain.value_objects.symbol import Symbol
from the_alchemiser.execution.domain.value_objects.time_in_force import TimeInForce


@dataclass
class Order:
    """Order entity with business behavior."""

    id: OrderId
    symbol: Symbol
    quantity: Quantity
    status: OrderStatus
    order_type: OrderType
    time_in_force: TimeInForce
    limit_price: Money | None = None
    filled_quantity: Quantity = field(default_factory=lambda: Quantity(Decimal("0")))
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def cancel(self) -> None:
        """Cancel the order if possible."""
        if self.status in (OrderStatus.FILLED, OrderStatus.CANCELLED):
            raise ValueError(f"Cannot cancel order in {self.status} status")
        self.status = OrderStatus.CANCELLED

    def fill(self, quantity: Quantity) -> None:
        """Fill the order partially or completely."""
        if self.status not in (OrderStatus.NEW, OrderStatus.PARTIALLY_FILLED):
            raise ValueError(f"Cannot fill order in {self.status} status")

        new_filled_value = self.filled_quantity.value + quantity.value
        if new_filled_value > self.quantity.value:
            raise ValueError("Fill quantity exceeds order quantity")

        self.filled_quantity = Quantity(new_filled_value)
        if new_filled_value == self.quantity.value:
            self.status = OrderStatus.FILLED
        else:
            self.status = OrderStatus.PARTIALLY_FILLED
