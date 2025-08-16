"""Mapping utilities between Alpaca order objects and domain Order entity.

This module is part of the anti-corruption layer. It converts external Alpaca
order representations into pure domain models so the rest of the application
can operate with strong types.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, TypedDict

from the_alchemiser.domain.shared_kernel.value_objects.money import Money
from the_alchemiser.domain.trading.entities.order import Order
from the_alchemiser.domain.trading.value_objects.order_id import OrderId
from the_alchemiser.domain.trading.value_objects.order_status import OrderStatus
from the_alchemiser.domain.trading.value_objects.quantity import Quantity
from the_alchemiser.domain.trading.value_objects.symbol import Symbol


class OrderSummary(TypedDict, total=False):
    """Lightweight order summary for UI/reporting when needed."""

    id: str
    symbol: str
    qty: float
    status: str
    type: str
    limit_price: float | None
    created_at: str | None


def _coerce_decimal(value: Any) -> Decimal | None:
    try:
        if value is None:
            return None
        return Decimal(str(value))
    except Exception:
        return None


def _map_status(raw_status: Any) -> OrderStatus:
    """Map Alpaca status strings/enums to domain OrderStatus."""
    if raw_status is None:
        return OrderStatus.NEW
    s = str(raw_status).lower().replace("orderstatus.", "")
    if s in {"new", "accepted", "pending_new", "submitted"}:
        return OrderStatus.NEW
    if s in {"partially_filled", "partial", "pending_fill"}:
        return OrderStatus.PARTIALLY_FILLED
    if s in {"filled", "done_for_day"}:
        return OrderStatus.FILLED
    if s in {"cancelled", "canceled"}:
        return OrderStatus.CANCELLED
    if s in {"rejected", "expired", "stopped"}:
        return OrderStatus.REJECTED
    # Default conservatively to NEW
    return OrderStatus.NEW


def alpaca_order_to_domain(order: Any) -> Order:
    """Convert an Alpaca order object/dict to a domain Order entity.

    Supports both attribute-based objects and dicts.
    """

    # Extract helpers handling attr/dict
    def get_attr(name: str, default: Any = None) -> Any:
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
    if order.limit_price is None:
        limit_val = None
    else:
        limit_val = float(order.limit_price.amount)

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
