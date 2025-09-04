"""Business Unit: execution | Status: current

Consolidated order domain mapping utilities.

This module consolidates order domain functionality including:
- Order domain models and immutable representations
- Order mapping utilities and status normalization
- DTO conversion and validation mappings

Consolidates order.py and orders.py for better maintainability.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Literal, cast

from the_alchemiser.execution.entities.order import Order
from the_alchemiser.execution.orders.order_types import OrderId, OrderStatus
from the_alchemiser.execution.orders.schemas import (
    OrderExecutionResultDTO,
    OrderRequestDTO,
    ValidatedOrderDTO,
)
from the_alchemiser.shared.math.num import floats_equal
from the_alchemiser.shared.types.money import Money
from the_alchemiser.shared.types.order_status import OrderStatusLiteral
from the_alchemiser.shared.types.quantity import Quantity
from the_alchemiser.shared.value_objects.core_types import OrderDetails
from the_alchemiser.shared.value_objects.symbol import Symbol

logger = logging.getLogger(__name__)


# Order Status Normalization

_STATUS_SYNONYMS: dict[str, OrderStatusLiteral] = {
    "placed": "new",
    "submitted": "new",
    "simulated": "new",
    "new": "new",
    "accepted": "new",
    "pending_new": "new",
    "partially_filled": "partially_filled",
    "partial": "partially_filled",
    "pending_fill": "partially_filled",
    "filled": "filled",
    "done_for_day": "filled",
    "canceled": "canceled",
    "cancelled": "canceled",
    "pending_cancel": "canceled",
    "expired": "expired",
    "rejected": "rejected",
    "failed": "rejected",
    "stopped": "rejected",
}


def normalize_order_status(status: Any) -> OrderStatusLiteral:
    """Normalize order status to canonical lowercase literal.

    Args:
        status: Raw status from any source (Alpaca, internal, etc.)

    Returns:
        Normalized OrderStatusLiteral

    Examples:
        >>> normalize_order_status("FILLED")
        "filled"
        >>> normalize_order_status("partial")
        "partially_filled"
        >>> normalize_order_status("cancelled")
        "canceled"

    """
    if status is None:
        return "new"

    # Convert to lowercase string
    status_str = str(status).lower().strip()

    # Look up in synonyms mapping
    normalized = _STATUS_SYNONYMS.get(status_str)
    if normalized:
        return normalized

    # Fallback for unknown statuses
    logger.warning(f"Unknown order status: {status}, defaulting to 'new'")
    return "new"


# Order Domain Models


@dataclass(frozen=True)
class OrderModel:
    """Immutable order model for internal use."""

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
        normalized_status = normalize_order_status(status_literal)

        # Convert to OrderStatus enum
        status_enum_mapping = {
            "new": OrderStatus.NEW,
            "partially_filled": OrderStatus.PARTIALLY_FILLED,
            "filled": OrderStatus.FILLED,
            "canceled": OrderStatus.CANCELLED,
            "rejected": OrderStatus.REJECTED,
        }
        status_enum = status_enum_mapping.get(normalized_status, OrderStatus.NEW)

        return cls(
            id=data["id"],
            symbol=data["symbol"],
            qty=float(data["qty"]),
            side=cast(Literal["buy", "sell"], data["side"]),
            order_type=cast(Literal["market", "limit", "stop", "stop_limit"], data["order_type"]),
            time_in_force=cast(Literal["day", "gtc", "ioc", "fok"], data["time_in_force"]),
            status=status_enum,
            filled_qty=float(data["filled_qty"]),
            filled_avg_price=filled_avg_price,
            created_at=created_at_parsed,
            updated_at=updated_at_parsed,
        )

    def is_filled(self) -> bool:
        """Check if order is completely filled."""
        return floats_equal(self.qty, self.filled_qty)

    def is_partial(self) -> bool:
        """Check if order is partially filled."""
        return self.filled_qty > 0 and not self.is_filled()

    def is_terminal(self) -> bool:
        """Check if order is in terminal state."""
        return self.status in {OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED}


# DTO Mapping Utilities


def dict_to_order_request_dto(order_dict: dict[str, Any]) -> OrderRequestDTO:
    """Convert dictionary to OrderRequestDTO.

    Args:
        order_dict: Dictionary containing order parameters

    Returns:
        Validated OrderRequestDTO

    Raises:
        ValueError: If required fields are missing or invalid

    """
    try:
        return OrderRequestDTO(
            symbol=str(order_dict["symbol"]).upper().strip(),
            side=order_dict["side"],
            quantity=Decimal(str(order_dict["quantity"])),
            order_type=order_dict["order_type"],
            time_in_force=order_dict.get("time_in_force", "day"),
            limit_price=Decimal(str(order_dict["limit_price"]))
            if order_dict.get("limit_price")
            else None,
            client_order_id=order_dict.get("client_order_id"),
        )
    except Exception as e:
        logger.error(f"Failed to convert dict to OrderRequestDTO: {e}")
        raise ValueError(f"Invalid order dictionary: {e}") from e


def order_request_to_validated_dto(order_request: OrderRequestDTO) -> ValidatedOrderDTO:
    """Convert OrderRequestDTO to ValidatedOrderDTO with additional metadata.

    Args:
        order_request: Validated order request

    Returns:
        ValidatedOrderDTO with derived fields

    """
    # Calculate estimated value if limit price is available
    estimated_value = None
    if order_request.limit_price:
        estimated_value = order_request.quantity * order_request.limit_price

    # Determine if fractional
    is_fractional = order_request.quantity % 1 != 0

    return ValidatedOrderDTO(
        symbol=order_request.symbol,
        side=order_request.side,
        quantity=order_request.quantity,
        order_type=order_request.order_type,
        time_in_force=order_request.time_in_force,
        limit_price=order_request.limit_price,
        client_order_id=order_request.client_order_id,
        estimated_value=estimated_value,
        is_fractional=is_fractional,
        normalized_quantity=order_request.quantity,  # Same for now
        risk_score=None,  # Would be calculated by risk engine
        validation_timestamp=datetime.now(UTC),
    )


def domain_order_to_execution_result(order: Order, success: bool = True) -> OrderExecutionResultDTO:
    """Convert domain Order to OrderExecutionResultDTO.

    Args:
        order: Domain order entity
        success: Whether the operation was successful

    Returns:
        OrderExecutionResultDTO with proper status mapping

    """
    # Map domain status to DTO status
    status_mapping = {
        OrderStatus.NEW: "accepted",
        OrderStatus.PARTIALLY_FILLED: "partially_filled",
        OrderStatus.FILLED: "filled",
        OrderStatus.CANCELLED: "canceled",
        OrderStatus.REJECTED: "rejected",
    }

    dto_status = status_mapping.get(order.status, "accepted")

    return OrderExecutionResultDTO(
        success=success,
        order_id=str(order.id),
        status=cast(
            Literal["accepted", "filled", "partially_filled", "rejected", "canceled"], dto_status
        ),
        filled_qty=order.filled_qty or Decimal("0"),
        avg_fill_price=order.avg_fill_price,
        submitted_at=order.created_at or datetime.now(UTC),
        completed_at=order.updated_at
        if order.status in {OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED}
        else None,
        error=None if success else f"Order {dto_status}",
    )


def create_order_from_request(order_request: OrderRequestDTO, order_id: str | None = None) -> Order:
    """Create domain Order entity from OrderRequestDTO.

    Args:
        order_request: Validated order request
        order_id: Optional order ID, generates new one if not provided

    Returns:
        Domain Order entity

    """
    from the_alchemiser.execution.orders.order_types import OrderType, Side
    from the_alchemiser.shared.types.time_in_force import TimeInForce

    # Create domain value objects
    order_id_obj = OrderId.from_string(order_id) if order_id else OrderId.generate()
    symbol = Symbol(order_request.symbol)
    quantity = Quantity(order_request.quantity)
    order_type = OrderType(value=order_request.order_type)
    side = Side(value=order_request.side)
    time_in_force = TimeInForce(value=order_request.time_in_force)

    # Handle limit price
    limit_price = None
    if order_request.limit_price:
        limit_price = Money(amount=order_request.limit_price, currency="USD")

    return Order(
        id=order_id_obj,
        symbol=symbol,
        quantity=quantity,
        order_type=order_type,
        side=side,
        time_in_force=time_in_force,
        status=OrderStatus.NEW,
        limit_price=limit_price,
        created_at=datetime.now(UTC),
        updated_at=None,
        filled_qty=Decimal("0"),
        avg_fill_price=None,
        client_order_id=order_request.client_order_id,
    )


__all__ = [
    # Status normalization
    "normalize_order_status",
    "OrderStatusLiteral",
    # Domain models
    "OrderModel",
    # DTO mapping
    "dict_to_order_request_dto",
    "order_request_to_validated_dto",
    "domain_order_to_execution_result",
    "create_order_from_request",
]
