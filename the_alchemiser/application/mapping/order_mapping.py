"""Mapping utilities between Alpaca order objects and domain Order entity.

This module is part of the anti-corruption layer. It converts external Alpaca
order representations into pure domain models so the rest of the application
can operate with strong types.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, TypedDict

from the_alchemiser.application.mapping.orders import normalize_order_status
from the_alchemiser.domain.shared_kernel.value_objects.money import Money
from the_alchemiser.domain.trading.entities.order import Order
from the_alchemiser.domain.trading.value_objects.order_id import OrderId
from the_alchemiser.domain.trading.value_objects.order_status import OrderStatus
from the_alchemiser.domain.trading.value_objects.quantity import Quantity
from the_alchemiser.domain.trading.value_objects.symbol import Symbol

if TYPE_CHECKING:
    from the_alchemiser.interfaces.schemas.orders import OrderExecutionResultDTO, RawOrderEnvelope


class OrderSummary(TypedDict, total=False):
    """Lightweight order summary for UI/reporting when needed."""

    id: str
    symbol: str
    qty: float
    status: str
    type: str
    limit_price: float | None
    created_at: str | None


def _coerce_decimal(value: object) -> Decimal | None:
    try:
        if value is None:
            return None
        return Decimal(str(value))
    except Exception:
        return None


def _map_status(raw_status: object) -> OrderStatus:
    """Map Alpaca status strings/enums to domain OrderStatus.

    Uses the centralized order status normalizer and then converts to domain enum.
    """
    if raw_status is None:
        return OrderStatus.NEW

    # Use the centralized normalizer to get consistent mapping
    raw_str = str(raw_status).lower().replace("orderstatus.", "")
    normalized = normalize_order_status(raw_str)

    # Convert from literal to domain enum
    literal_to_domain = {
        "new": OrderStatus.NEW,
        "partially_filled": OrderStatus.PARTIALLY_FILLED,
        "filled": OrderStatus.FILLED,
        "canceled": OrderStatus.CANCELLED,
        "expired": OrderStatus.REJECTED,  # Map expired to REJECTED as domain only has these statuses
        "rejected": OrderStatus.REJECTED,
    }

    return literal_to_domain.get(normalized, OrderStatus.NEW)


def alpaca_order_to_domain(order: object) -> Order:
    """Convert an Alpaca order object/dict to a domain Order entity.

    Supports both attribute-based objects and dicts.
    """

    # Extract helpers handling attr/dict
    def get_attr(name: str, default: object = None) -> object:
        if isinstance(order, dict):
            return order.get(name, default)
        return getattr(order, name, default)

    raw_id = get_attr("id") or get_attr("order_id")
    if not raw_id:
        # Generate a synthetic ID to avoid crashing, but prefer explicit mapping
        raw_id = "00000000-0000-0000-0000-000000000000"

    symbol_raw = get_attr("symbol") or "UNKNOWN"
    qty_raw = get_attr("qty") or get_attr("quantity") or 0
    status_raw = get_attr("status")
    order_type_raw = get_attr("order_type") or get_attr("type") or "market"
    limit_price_raw = get_attr("limit_price")
    created_at_raw = get_attr("created_at")

    # Map primitives to domain value objects
    order_id = OrderId.from_string(str(raw_id))
    symbol = Symbol(str(symbol_raw))
    quantity_dec = _coerce_decimal(qty_raw) or Decimal("0")
    quantity = Quantity(quantity_dec)
    status = _map_status(status_raw)
    order_type = str(order_type_raw)

    limit_price_dec = _coerce_decimal(limit_price_raw)
    limit_price = Money(limit_price_dec, "USD") if limit_price_dec is not None else None

    # created_at handling
    created_at: datetime
    try:
        if isinstance(created_at_raw, datetime):
            created_at = (
                created_at_raw if created_at_raw.tzinfo else created_at_raw.replace(tzinfo=UTC)
            )
        elif created_at_raw:
            created_at = datetime.fromisoformat(str(created_at_raw))
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=UTC)
        else:
            created_at = datetime.now(UTC)
    except Exception:
        created_at = datetime.now(UTC)

    return Order(
        id=order_id,
        symbol=symbol,
        quantity=quantity,
        status=status,
        order_type=order_type,
        limit_price=limit_price,
        created_at=created_at,
    )


def summarize_order(order: Order) -> OrderSummary:
    """Create a lightweight summary dictionary from a domain Order."""
    limit_val: float | None
    limit_val = None if order.limit_price is None else float(order.limit_price.amount)

    return {
        "id": str(order.id.value),
        "symbol": order.symbol.value,
        "qty": float(order.quantity.value),
        "status": order.status.value,
        "type": order.order_type,
        "limit_price": limit_val,
        "created_at": order.created_at.isoformat(),
    }


def order_to_dict(order: Order) -> dict[str, Any]:
    """Serialize Order to a plain dict (best-effort).

    Note: This is intended for diagnostics or JSON-like logging, not persistence.
    """
    d = asdict(order)
    # Convert complex types
    d["id"] = str(order.id.value)
    d["symbol"] = order.symbol.value
    d["quantity"] = float(order.quantity.value)
    d["status"] = order.status.value
    d["limit_price"] = None if order.limit_price is None else float(order.limit_price.amount)
    d["created_at"] = order.created_at.isoformat()
    return d


def raw_order_envelope_to_domain_order(envelope: RawOrderEnvelope) -> Order:
    """Convert RawOrderEnvelope to domain Order entity.

    Args:
        envelope: RawOrderEnvelope containing raw Alpaca order and metadata

    Returns:
        Domain Order entity

    Raises:
        ValueError: If envelope data cannot be converted to domain Order
    """
    if not envelope.success or envelope.raw_order is None:
        raise ValueError("Cannot convert failed order envelope to domain order")

    # Delegate to existing alpaca_order_to_domain function
    return alpaca_order_to_domain(envelope.raw_order)


def raw_order_envelope_to_execution_result_dto(
    envelope: RawOrderEnvelope,
) -> OrderExecutionResultDTO:
    """Convert RawOrderEnvelope to OrderExecutionResultDTO.

    Args:
        envelope: RawOrderEnvelope containing raw Alpaca order and metadata

    Returns:
        OrderExecutionResultDTO with execution details
    """
    from the_alchemiser.application.mapping.alpaca_dto_mapping import (
        alpaca_order_to_execution_result,
        create_error_execution_result,
    )

    if not envelope.success:
        # Create error result from envelope metadata
        error_msg = envelope.error_message or "Order execution failed"
        return create_error_execution_result(
            Exception(error_msg),
            context="Order execution",
        )

    # For successful orders, delegate to existing function
    return alpaca_order_to_execution_result(envelope.raw_order)
