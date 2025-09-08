"""Business Unit: execution | Status: current.

Consolidated broker integration mapping utilities.

This module consolidates Alpaca API integration mappings including:
- Alpaca DTO mapping utilities for infrastructure boundary
- Alpaca order to domain Order entity mapping
- Anti-corruption layer for clean broker integration

Consolidates alpaca_dto_mapping.py and order_mapping.py for better maintainability.
"""

from __future__ import annotations

import contextlib
import logging
from dataclasses import asdict
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Literal, TypedDict, cast

from the_alchemiser.execution.mappers.order_domain_mappers import normalize_order_status
from the_alchemiser.execution.orders.order import Order
from the_alchemiser.execution.orders.order_types import OrderId, OrderStatus, OrderType
from the_alchemiser.execution.orders.schemas import OrderExecutionResultDTO
from the_alchemiser.execution.schemas.alpaca import AlpacaErrorDTO, AlpacaOrderDTO
from the_alchemiser.shared.protocols.order_like import OrderLikeProtocol
from the_alchemiser.shared.types.money import Money
from the_alchemiser.shared.types.quantity import Quantity
from the_alchemiser.shared.types.time_in_force import TimeInForce
from the_alchemiser.shared.value_objects.symbol import Symbol

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# Alpaca DTO Mapping Section


def alpaca_order_to_dto(order: Any) -> AlpacaOrderDTO:
    """Convert raw Alpaca order object to AlpacaOrderDTO.

    Handles both attribute-based objects and dict responses from Alpaca API.

    Args:
        order: Raw Alpaca order object or dict

    Returns:
        AlpacaOrderDTO with validated and converted fields

    Raises:
        ValueError: If required fields are missing or invalid

    """

    # Extract helper function to handle both attribute access and dict access
    def get_attr(name: str, default: Any = None) -> Any:
        if isinstance(order, dict):
            return order.get(name, default)
        return getattr(order, name, default)

    # Extract required fields with validation
    order_id = get_attr("id")
    if not order_id:
        raise ValueError("Order ID is required")

    symbol = get_attr("symbol")
    if not symbol:
        raise ValueError("Symbol is required")

    # Convert and validate quantity
    raw_qty = get_attr("qty")
    try:
        qty = Decimal(str(raw_qty)) if raw_qty is not None else Decimal("0")
    except (ValueError, TypeError):
        raise ValueError(f"Invalid quantity: {raw_qty}")

    # Convert filled quantity
    raw_filled_qty = get_attr("filled_qty", "0")
    try:
        filled_qty = Decimal(str(raw_filled_qty))
    except (ValueError, TypeError):
        filled_qty = Decimal("0")

    # Handle status normalization
    raw_status = get_attr("status", "unknown")
    status = normalize_order_status(raw_status)

    # Convert timestamps
    created_at = get_attr("created_at")
    updated_at = get_attr("updated_at")
    submitted_at = get_attr("submitted_at")

    # Handle price fields
    limit_price = None
    avg_fill_price = None

    raw_limit = get_attr("limit_price")
    if raw_limit is not None:
        try:
            limit_price = Decimal(str(raw_limit))
        except (ValueError, TypeError):
            logger.warning(f"Invalid limit price: {raw_limit}")

    raw_avg_fill = get_attr("filled_avg_price") or get_attr("avg_fill_price")
    if raw_avg_fill is not None:
        try:
            avg_fill_price = Decimal(str(raw_avg_fill))
        except (ValueError, TypeError):
            logger.warning(f"Invalid average fill price: {raw_avg_fill}")

    return AlpacaOrderDTO(
        id=str(order_id),
        symbol=str(symbol),
        qty=qty,
        filled_qty=filled_qty,
        side=get_attr("side", "unknown"),
        order_type=get_attr("order_type") or get_attr("type", "unknown"),
        time_in_force=get_attr("time_in_force", "day"),
        status=status,
        limit_price=limit_price,
        avg_fill_price=avg_fill_price,
        created_at=created_at,
        updated_at=updated_at,
        submitted_at=submitted_at,
        client_order_id=get_attr("client_order_id"),
    )


def alpaca_order_to_execution_result(order: Any) -> OrderExecutionResultDTO:  # noqa: ANN401  # Alpaca SDK order object with dynamic structure
    """Convert Alpaca order object to OrderExecutionResultDTO.

    Args:
        order: Raw Alpaca order object from SDK

    Returns:
        OrderExecutionResultDTO with proper success flag and error handling

    """
    try:
        alpaca_dto = alpaca_order_to_dto(order)

        # Determine success based on status
        success = alpaca_dto.status not in ["rejected", "canceled", "expired"]

        # Convert timestamps
        submitted_at = datetime.now(UTC)
        completed_at = None

        if alpaca_dto.submitted_at:
            with contextlib.suppress(Exception):
                if isinstance(alpaca_dto.submitted_at, str):
                    submitted_at = datetime.fromisoformat(
                        alpaca_dto.submitted_at.replace("Z", "+00:00")
                    )
                elif hasattr(alpaca_dto.submitted_at, "isoformat"):
                    submitted_at = alpaca_dto.submitted_at

        if alpaca_dto.updated_at and alpaca_dto.status in ["filled", "canceled", "rejected"]:
            with contextlib.suppress(Exception):
                if isinstance(alpaca_dto.updated_at, str):
                    completed_at = datetime.fromisoformat(
                        alpaca_dto.updated_at.replace("Z", "+00:00")
                    )
                elif hasattr(alpaca_dto.updated_at, "isoformat"):
                    completed_at = alpaca_dto.updated_at

        return OrderExecutionResultDTO(
            success=success,
            order_id=alpaca_dto.id,
            status=cast(
                Literal["accepted", "filled", "partially_filled", "rejected", "canceled"],
                alpaca_dto.status,
            ),
            filled_qty=alpaca_dto.filled_qty,
            avg_fill_price=alpaca_dto.avg_fill_price,
            submitted_at=submitted_at,
            completed_at=completed_at,
            error=None if success else f"Order {alpaca_dto.status}",
        )

    except Exception as e:
        logger.error(f"Failed to convert Alpaca order to execution result: {e}")
        return OrderExecutionResultDTO(
            success=False,
            order_id="unknown",
            status="rejected",
            filled_qty=Decimal("0"),
            avg_fill_price=None,
            submitted_at=datetime.now(UTC),
            completed_at=None,
            error=str(e),
        )


def alpaca_error_to_dto(error: Any) -> AlpacaErrorDTO:
    """Convert Alpaca error response to AlpacaErrorDTO.

    Args:
        error: Raw Alpaca error object or dict

    Returns:
        AlpacaErrorDTO with normalized error information

    """

    def get_attr(name: str, default: Any = None) -> Any:
        if isinstance(error, dict):
            return error.get(name, default)
        return getattr(error, name, default)

    return AlpacaErrorDTO(
        code=get_attr("code", "unknown"),
        message=get_attr("message", "Unknown error"),
        details=get_attr("details"),
    )


# Order Domain Mapping Section


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
    """Safely coerce value to Decimal."""
    try:
        if value is None:
            return None
        return Decimal(str(value))
    except (ValueError, TypeError):
        return None


def _coerce_datetime(value: Any) -> datetime | None:
    """Safely coerce value to datetime."""
    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    if isinstance(value, str):
        try:
            # Handle various ISO format variations
            if value.endswith("Z"):
                value = value[:-1] + "+00:00"
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    return None


def alpaca_order_to_domain(alpaca_order: Any) -> Order:
    """Convert Alpaca order object to domain Order entity.

    This function is part of the anti-corruption layer, converting external
    Alpaca order representations into pure domain models.

    Args:
        alpaca_order: Raw Alpaca order object (from alpaca-py)

    Returns:
        Domain Order entity with strongly typed fields

    Raises:
        ValueError: If required fields are missing or invalid

    """

    # Handle both dict and object access patterns
    def get_attr(name: str, default: Any = None) -> Any:
        if isinstance(alpaca_order, dict):
            return alpaca_order.get(name, default)
        return getattr(alpaca_order, name, default)

    # Extract and validate required fields
    order_id_str = get_attr("id")
    if not order_id_str:
        raise ValueError("Order ID is required")

    symbol_str = get_attr("symbol")
    if not symbol_str:
        raise ValueError("Symbol is required")

    # Convert to domain value objects
    try:
        order_id = OrderId.from_string(str(order_id_str))
        symbol = Symbol(str(symbol_str))

        # Quantity handling
        qty_value = get_attr("qty")
        quantity = Quantity(_coerce_decimal(qty_value) or Decimal("0"))

        # Order type
        order_type_str = get_attr("order_type") or get_attr("type", "market")
        order_type = OrderType(
            value=order_type_str if order_type_str in ["market", "limit"] else "market"
        )

        # Time in force
        tif_str = get_attr("time_in_force", "day")
        time_in_force = TimeInForce(
            value=tif_str if tif_str in ["day", "gtc", "ioc", "fok"] else "day"
        )

        # Status
        status_str = normalize_order_status(get_attr("status", "NEW"))
        status = OrderStatus(status_str)

        # Optional fields
        limit_price = None
        limit_price_value = get_attr("limit_price")
        if limit_price_value is not None:
            limit_price_decimal = _coerce_decimal(limit_price_value)
            if limit_price_decimal:
                limit_price = Money(amount=limit_price_decimal, currency="USD")

        # Timestamps
        created_at = _coerce_datetime(get_attr("created_at")) or datetime.now(UTC)
        updated_at = _coerce_datetime(get_attr("updated_at"))

        # Execution details
        filled_qty = _coerce_decimal(get_attr("filled_qty")) or Decimal("0")
        avg_fill_price = _coerce_decimal(get_attr("filled_avg_price") or get_attr("avg_fill_price"))

        return Order(
            id=order_id,
            symbol=symbol,
            quantity=quantity,
            order_type=order_type,
            time_in_force=time_in_force,
            status=status,
            limit_price=limit_price,
            created_at=created_at,
            updated_at=updated_at,
            filled_qty=filled_qty,
            avg_fill_price=avg_fill_price,
            client_order_id=get_attr("client_order_id"),
        )

    except Exception as e:
        logger.error(f"Failed to convert Alpaca order to domain: {e}")
        raise ValueError(f"Invalid order data: {e}") from e


def summarize_order(order: Order) -> OrderSummary:
    """Create a lightweight summary of an order for UI/reporting.

    Args:
        order: Domain Order entity

    Returns:
        OrderSummary dict with key fields

    """
    return OrderSummary(
        id=str(order.id),
        symbol=str(order.symbol),
        qty=float(order.quantity.value),
        status=order.status.value,
        type=order.order_type.value,
        limit_price=float(order.limit_price.amount) if order.limit_price else None,
        created_at=order.created_at.isoformat() if order.created_at else None,
    )


def order_to_dict(order: Order) -> dict[str, Any]:
    """Convert domain Order to dict representation.

    Args:
        order: Domain Order entity

    Returns:
        Dictionary representation suitable for serialization

    """
    order_dict = asdict(order)

    # Convert complex types to serializable formats
    order_dict["id"] = str(order.id)
    order_dict["symbol"] = str(order.symbol)
    order_dict["quantity"] = float(order.quantity.value)
    order_dict["order_type"] = order.order_type.value
    order_dict["time_in_force"] = order.time_in_force.value
    order_dict["status"] = order.status.value

    if order.limit_price:
        order_dict["limit_price"] = float(order.limit_price.amount)
        order_dict["currency"] = order.limit_price.currency
    else:
        order_dict["limit_price"] = None
        order_dict["currency"] = None

    if order.created_at:
        order_dict["created_at"] = order.created_at.isoformat()

    if order.updated_at:
        order_dict["updated_at"] = order.updated_at.isoformat()

    if order.filled_qty:
        order_dict["filled_qty"] = float(order.filled_qty)

    if order.avg_fill_price:
        order_dict["avg_fill_price"] = float(order.avg_fill_price)

    return order_dict


__all__ = [
    # Alpaca DTO mapping
    "alpaca_order_to_dto",
    "alpaca_order_to_execution_result",
    "alpaca_error_to_dto",
    # Order domain mapping
    "alpaca_order_to_domain",
    "summarize_order",
    "order_to_dict",
    # Types
    "OrderSummary",
]
