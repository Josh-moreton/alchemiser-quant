#!/usr/bin/env python3
"""
Mapping utilities between tracking DTOs and internal dataclasses.

This module provides anti-corruption layer mappings for the strategy_order_tracker
refactor, converting between StrategyOrderEventDTO/StrategyExecutionSummaryDTO 
and internal dataclasses.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, cast

# Import only DTOs to avoid circular imports
from the_alchemiser.interfaces.schemas.tracking import (
    StrategyOrderEventDTO,
    StrategyExecutionSummaryDTO,
    OrderEventStatus,
    ExecutionStatus,
    StrategyLiteral,
)


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
        ts=datetime.fromisoformat(order.timestamp.replace("Z", "+00:00"))
        if isinstance(order.timestamp, str)
        else order.timestamp,
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
        "timestamp": event.ts.isoformat() if isinstance(event.ts, datetime) else event.ts,
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
        "positions": {
            symbol: Decimal(str(quantity)) for symbol, quantity in pnl.positions.items()
        },
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
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            # Fallback to current time if parsing fails
            return datetime.now(timezone.utc)
    elif isinstance(ts, datetime):
        if ts.tzinfo is None:
            return ts.replace(tzinfo=timezone.utc)
        return ts
    
    # For any other type, return current time
    return datetime.now(timezone.utc)


def ensure_decimal_precision(value: float | str | Decimal) -> Decimal:
    """Ensure value is converted to Decimal with appropriate precision."""
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))