#!/usr/bin/env python3
"""Business Unit: utilities; Status: current.

Mapping utilities between tracking DTOs and internal dataclasses.

This module provides anti-corruption layer mappings for the strategy_order_tracker
refactor, converting between StrategyOrderEventDTO/StrategyExecutionSummaryDTO
and internal dataclasses. Updated to support new Pydantic DTOs for strategy tracking.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, cast

# Import DTOs and new strategy DTOs
from the_alchemiser.shared_kernel.interfaces.tracking import (
    ExecutionStatus,
    OrderEventStatus,
    StrategyExecutionSummaryDTO,
    StrategyLiteral,
    StrategyOrderDTO,
    StrategyOrderEventDTO,
    StrategyPnLDTO,
    StrategyPositionDTO,
)

# Constants to avoid duplication
UTC_OFFSET_STRING = "+00:00"
DECIMAL_QUANTIZE_PRECISION = "0.000001"


def strategy_order_to_event_dto(
    order: Any,  # StrategyOrder - avoid import to prevent circular dependency
    event_id: str | None = None,
    status: OrderEventStatus = OrderEventStatus.FILLED,
    error: str | None = None,
) -> StrategyOrderEventDTO:
    """Convert StrategyOrder to StrategyOrderEventDTO."""
    return StrategyOrderEventDTO(
        event_id=event_id or f"evt_{order.order_id}",
        strategy=cast(StrategyLiteral, order.strategy),
        symbol=order.symbol,
        side=order.side.lower(),  # DTO expects lowercase
        quantity=Decimal(str(order.quantity)),
        status=status,
        price=Decimal(str(order.price)) if order.price > 0 else None,
        ts=(
            datetime.fromisoformat(order.timestamp.replace("Z", UTC_OFFSET_STRING))
            if isinstance(order.timestamp, str)
            else order.timestamp
        ),
        error=error,
    )


def event_dto_to_strategy_order_dict(event: StrategyOrderEventDTO, order_id: str) -> dict[str, Any]:
    """Convert StrategyOrderEventDTO to StrategyOrder data dict."""
    return {
        "order_id": order_id,
        "strategy": event.strategy,
        "symbol": event.symbol,
        "side": event.side.upper(),  # Internal uses uppercase
        "quantity": float(event.quantity),
        "price": float(event.price) if event.price else 0.0,
        "timestamp": (event.ts.isoformat() if isinstance(event.ts, datetime) else event.ts),
    }


def orders_to_execution_summary_dto(
    orders: list[Any],  # list[StrategyOrder] - avoid import
    strategy: str,
    symbol: str,
    status: ExecutionStatus = ExecutionStatus.OK,
    pnl: Decimal | None = None,
    error: str | None = None,
) -> StrategyExecutionSummaryDTO:
    """Convert list of StrategyOrders to StrategyExecutionSummaryDTO."""
    if not orders:
        return StrategyExecutionSummaryDTO(
            strategy=cast(StrategyLiteral, strategy),
            symbol=symbol,
            total_qty=Decimal("0"),
            avg_price=None,
            pnl=pnl,
            status=status,
            details=[],
        )

    # Sort orders by timestamp to ensure chronological order
    sorted_orders = sorted(orders, key=lambda o: o.timestamp)

    # Convert orders to events
    events = [
        strategy_order_to_event_dto(
            order,
            status=OrderEventStatus.ERROR if error else OrderEventStatus.FILLED,
            error=error if error else None,
        )
        for order in sorted_orders
    ]

    # Calculate totals
    quantities = [Decimal(str(order.quantity)) for order in sorted_orders]
    total_qty: Decimal = sum(quantities, Decimal(0))

    # Calculate weighted average price
    if total_qty > 0:
        total_value = sum(
            Decimal(str(order.quantity)) * Decimal(str(order.price))
            for order in sorted_orders
            if order.price > 0
        )
        avg_price: Decimal | None = total_value / total_qty if total_value > 0 else None
    else:
        avg_price = None

    return StrategyExecutionSummaryDTO(
        strategy=cast(StrategyLiteral, strategy),
        symbol=symbol,
        total_qty=total_qty,
        avg_price=avg_price,
        pnl=pnl,
        status=status,
        details=events,
    )


def strategy_pnl_to_dict(pnl: Any) -> dict[str, Any]:  # StrategyPnL - avoid import
    """Convert StrategyPnL to dict with Decimal precision."""
    return {
        "strategy": pnl.strategy,
        "realized_pnl": Decimal(str(pnl.realized_pnl)),
        "unrealized_pnl": Decimal(str(pnl.unrealized_pnl)),
        "total_pnl": Decimal(str(pnl.total_pnl)),
        "positions": {symbol: Decimal(str(quantity)) for symbol, quantity in pnl.positions.items()},
        "allocation_value": Decimal(str(pnl.allocation_value)),
        "total_return_pct": Decimal(str(pnl.total_return_pct)),
    }


def dict_to_strategy_pnl_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Convert dict to StrategyPnL data dict (for loading from storage)."""
    return {
        "strategy": data["strategy"],
        "realized_pnl": float(data.get("realized_pnl", 0)),
        "unrealized_pnl": float(data.get("unrealized_pnl", 0)),
        "total_pnl": float(data.get("total_pnl", 0)),
        "positions": {
            symbol: float(quantity) for symbol, quantity in data.get("positions", {}).items()
        },
        "allocation_value": float(data.get("allocation_value", 0)),
    }


def normalize_timestamp(ts: str | datetime) -> datetime:
    """Normalize timestamp to timezone-aware datetime."""
    if isinstance(ts, str):
        # Handle ISO format strings
        try:
            dt = datetime.fromisoformat(ts.replace("Z", UTC_OFFSET_STRING))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=UTC)
            return dt
        except ValueError:
            # Fallback to current time if parsing fails
            return datetime.now(UTC)
    else:  # isinstance(ts, datetime)
        if ts.tzinfo is None:
            return ts.replace(tzinfo=UTC)
        return ts


def ensure_decimal_precision(value: float | str | Decimal) -> Decimal:
    """Ensure value is converted to Decimal with appropriate precision."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


# New DTO mapping functions


def strategy_order_dataclass_to_dto(order: Any) -> StrategyOrderDTO:
    """Convert StrategyOrder dataclass to StrategyOrderDTO."""
    # Convert to Decimal and quantize to 6 decimal places to avoid precision errors
    from decimal import ROUND_HALF_UP

    quantized_quantity = Decimal(str(order.quantity)).quantize(
        Decimal(DECIMAL_QUANTIZE_PRECISION), rounding=ROUND_HALF_UP
    )
    quantized_price = Decimal(str(order.price)).quantize(
        Decimal(DECIMAL_QUANTIZE_PRECISION), rounding=ROUND_HALF_UP
    )

    return StrategyOrderDTO(
        order_id=order.order_id,
        strategy=cast(StrategyLiteral, order.strategy),
        symbol=order.symbol,
        side=order.side.lower(),  # DTO expects lowercase
        quantity=quantized_quantity,
        price=quantized_price,
        timestamp=(
            datetime.fromisoformat(order.timestamp.replace("Z", UTC_OFFSET_STRING))
            if isinstance(order.timestamp, str)
            else order.timestamp
        ),
    )


def strategy_order_dto_to_dataclass_dict(dto: StrategyOrderDTO) -> dict[str, Any]:
    """Convert StrategyOrderDTO to dataclass creation dict."""
    return {
        "order_id": dto.order_id,
        "strategy": dto.strategy,
        "symbol": dto.symbol,
        "side": dto.side.upper(),  # Dataclass uses uppercase
        "quantity": float(dto.quantity),
        "price": float(dto.price),
        "timestamp": dto.timestamp.isoformat(),
    }


def strategy_position_dataclass_to_dto(position: Any) -> StrategyPositionDTO:
    """Convert StrategyPosition dataclass to StrategyPositionDTO."""
    return StrategyPositionDTO(
        strategy=cast(StrategyLiteral, position.strategy),
        symbol=position.symbol,
        quantity=Decimal(str(position.quantity)),
        average_cost=Decimal(str(position.average_cost)),
        total_cost=Decimal(str(position.total_cost)),
        last_updated=(
            datetime.fromisoformat(position.last_updated.replace("Z", UTC_OFFSET_STRING))
            if isinstance(position.last_updated, str)
            else position.last_updated
        ),
    )


def strategy_position_dto_to_dataclass_dict(dto: StrategyPositionDTO) -> dict[str, Any]:
    """Convert StrategyPositionDTO to dataclass creation dict."""
    return {
        "strategy": dto.strategy,
        "symbol": dto.symbol,
        "quantity": float(dto.quantity),
        "average_cost": float(dto.average_cost),
        "total_cost": float(dto.total_cost),
        "last_updated": dto.last_updated.isoformat(),
    }


def strategy_pnl_dataclass_to_dto(pnl: Any) -> StrategyPnLDTO:
    """Convert StrategyPnL dataclass to StrategyPnLDTO."""
    return StrategyPnLDTO(
        strategy=cast(StrategyLiteral, pnl.strategy),
        realized_pnl=Decimal(str(pnl.realized_pnl)),
        unrealized_pnl=Decimal(str(pnl.unrealized_pnl)),
        total_pnl=Decimal(str(pnl.total_pnl)),
        positions={symbol: Decimal(str(qty)) for symbol, qty in pnl.positions.items()},
        allocation_value=Decimal(str(pnl.allocation_value)),
    )


def strategy_pnl_dto_to_dataclass_dict(dto: StrategyPnLDTO) -> dict[str, Any]:
    """Convert StrategyPnLDTO to dataclass creation dict."""
    return {
        "strategy": dto.strategy,
        "realized_pnl": float(dto.realized_pnl),
        "unrealized_pnl": float(dto.unrealized_pnl),
        "total_pnl": float(dto.total_pnl),
        "positions": {symbol: float(qty) for symbol, qty in dto.positions.items()},
        "allocation_value": float(dto.allocation_value),
    }


def strategy_pnl_dto_to_dict(dto: StrategyPnLDTO) -> dict[str, Any]:
    """Convert StrategyPnLDTO to dict with Decimal precision for serialization."""
    return {
        "strategy": dto.strategy,
        "realized_pnl": dto.realized_pnl,
        "unrealized_pnl": dto.unrealized_pnl,
        "total_pnl": dto.total_pnl,
        "positions": dict(dto.positions),  # Keep as Decimal
        "allocation_value": dto.allocation_value,
        "total_return_pct": dto.total_return_pct,
        "position_count": dto.position_count,
    }
