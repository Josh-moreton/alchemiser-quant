"""Business Unit: order execution/placement; Status: current.

Order domain models.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from the_alchemiser.execution.orders.order_status import OrderStatus
from the_alchemiser.execution.orders.order_status_literal import (
    OrderStatusLiteral,
)
from the_alchemiser.shared.value_objects.core_types import OrderDetails
from the_alchemiser.shared.math.num import floats_equal


@dataclass(frozen=True)
class OrderModel:
    """Immutable order model."""

    id: str
    symbol: str
    qty: float
    side: Literal["buy", "sell"]
    order_type: Literal["market", "limit", "stop", "stop_limit"]
    time_in_force: Literal["day", "gtc", "ioc", "fok"]
    status: OrderStatus  # Domain uses enum, boundary uses lowercase literal
    filled_qty: float
    filled_avg_price: float | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_dict(cls, data: OrderDetails) -> OrderModel:
        """Create from OrderDetails TypedDict."""
        created_at_raw = data["created_at"]
        created_at_parsed = datetime.fromisoformat(created_at_raw.replace("Z", "+00:00"))

        updated_at_raw = data["updated_at"]
        updated_at_parsed = datetime.fromisoformat(updated_at_raw.replace("Z", "+00:00"))

        filled_avg_price = data["filled_avg_price"]
        if filled_avg_price is not None:
            filled_avg_price = float(filled_avg_price)

        # Map lowercase literal status to domain enum (uppercase member names)
        status_literal = data["status"]
        literal_to_enum = {
            "new": OrderStatus.NEW,
            "partially_filled": OrderStatus.PARTIALLY_FILLED,
            "filled": OrderStatus.FILLED,
            "canceled": OrderStatus.CANCELLED,
            "expired": OrderStatus.REJECTED,  # Collapsed in domain layer
            "rejected": OrderStatus.REJECTED,
        }

        return cls(
            id=data["id"],
            symbol=data["symbol"],
            qty=float(data["qty"]),
            side=data["side"],
            order_type=data["order_type"],
            time_in_force=data["time_in_force"],
            status=literal_to_enum.get(status_literal, OrderStatus.NEW),
            filled_qty=float(data["filled_qty"]),
            filled_avg_price=filled_avg_price,
            created_at=created_at_parsed,
            updated_at=updated_at_parsed,
        )

    def to_dict(self) -> OrderDetails:
        """Convert to OrderDetails TypedDict."""
        # Convert enum back to lowercase literal for boundary representation
        enum_to_literal: dict[OrderStatus, OrderStatusLiteral] = {
            OrderStatus.NEW: "new",
            OrderStatus.PARTIALLY_FILLED: "partially_filled",
            OrderStatus.FILLED: "filled",
            OrderStatus.CANCELLED: "canceled",
            OrderStatus.REJECTED: "rejected",
        }

        return {
            "id": self.id,
            "symbol": self.symbol,
            "qty": self.qty,
            "side": self.side,
            "order_type": self.order_type,
            "time_in_force": self.time_in_force,
            "status": enum_to_literal.get(self.status, "new"),
            "filled_qty": self.filled_qty,
            "filled_avg_price": self.filled_avg_price,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @property
    def is_buy_order(self) -> bool:
        """Check if this is a buy order."""
        return self.side == "buy"

    @property
    def is_sell_order(self) -> bool:
        """Check if this is a sell order."""
        return self.side == "sell"

    @property
    def is_filled(self) -> bool:
        """Check if order is completely filled."""
        return self.status == OrderStatus.FILLED

    @property
    def is_partially_filled(self) -> bool:
        """Check if order is partially filled."""
        return self.status == OrderStatus.PARTIALLY_FILLED

    @property
    def is_complete(self) -> bool:
        """Check if order is complete (filled or canceled/rejected)."""
        return self.status in [
            OrderStatus.FILLED,
            OrderStatus.CANCELLED,
            OrderStatus.REJECTED,
        ]

    @property
    def remaining_qty(self) -> float:
        """Calculate remaining quantity to be filled."""
        return max(0, self.qty - self.filled_qty)

    @property
    def fill_percentage(self) -> float:
        """Calculate percentage of order that has been filled."""
        if floats_equal(self.qty, 0.0):
            return 0.0
        return (self.filled_qty / self.qty) * 100

    @property
    def total_value(self) -> float | None:
        """Calculate total value of filled portion."""
        if self.filled_avg_price is None or floats_equal(self.filled_qty, 0.0):
            return None
        return self.filled_qty * self.filled_avg_price
