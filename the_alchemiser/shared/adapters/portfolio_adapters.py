#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Portfolio adapters for converting between portfolio domain objects and DTOs.

Provides conversion functions between internal portfolio objects and
PortfolioStateDTO/PositionDTO for inter-module communication.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from the_alchemiser.shared.dto.portfolio_state_dto import (
    PortfolioMetricsDTO,
    PortfolioStateDTO,
    PositionDTO,
)


def position_to_dto(
    position: Any,  # Position object - avoid import to prevent circular dependency
    correlation_context: dict[str, Any] | None = None,
) -> PositionDTO:
    """Convert internal Position object to PositionDTO.

    Args:
        position: Internal position object (could be from various sources)
        correlation_context: Optional context for correlation tracking

    Returns:
        PositionDTO instance

    Raises:
        ValueError: If position data is invalid

    """
    # Handle different position object types and attribute names
    # This handles both dataclass-style and dict-style position objects

    def get_attr_value(obj: Any, attr_name: str, default: Any = None) -> Any:
        """Get attribute value from object, handling both attr access and dict access."""
        if hasattr(obj, attr_name):
            return getattr(obj, attr_name)
        if isinstance(obj, dict) and attr_name in obj:
            return obj[attr_name]
        return default

    # Extract position data with fallbacks for different naming conventions
    symbol = get_attr_value(position, "symbol") or get_attr_value(position, "Symbol")
    quantity = (
        get_attr_value(position, "quantity")
        or get_attr_value(position, "qty")
        or get_attr_value(position, "Quantity")
    )

    # Average cost / entry price
    average_cost = (
        get_attr_value(position, "average_cost")
        or get_attr_value(position, "avg_cost")
        or get_attr_value(position, "average_entry_price")
        or get_attr_value(position, "avg_entry_price")
        or get_attr_value(position, "entry_price")
        or Decimal("0")
    )

    # Current price
    current_price = (
        get_attr_value(position, "current_price")
        or get_attr_value(position, "price")
        or get_attr_value(position, "market_price")
        or average_cost  # Fallback to average cost if no current price
    )

    # Market value
    market_value = get_attr_value(position, "market_value")
    if market_value is None:
        # Calculate market value if not provided
        market_value = Decimal(str(quantity)) * Decimal(str(current_price))

    # Unrealized P&L
    unrealized_pnl = get_attr_value(position, "unrealized_pnl") or get_attr_value(
        position, "unrealized_pl"
    )
    if unrealized_pnl is None:
        # Calculate unrealized P&L if not provided
        cost_basis = Decimal(str(quantity)) * Decimal(str(average_cost))
        unrealized_pnl = Decimal(str(market_value)) - cost_basis

    # Unrealized P&L percentage
    unrealized_pnl_percent = get_attr_value(position, "unrealized_pnl_percent") or get_attr_value(
        position, "unrealized_plpc"
    )
    if unrealized_pnl_percent is None and average_cost and float(average_cost) != 0:
        # Calculate unrealized P&L percentage if not provided
        unrealized_pnl_percent = (
            Decimal(str(current_price)) - Decimal(str(average_cost))
        ) / Decimal(str(average_cost))

    # Optional fields
    last_updated = get_attr_value(position, "last_updated")
    if last_updated and isinstance(last_updated, str):
        try:
            last_updated = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
        except ValueError:
            last_updated = None

    side = get_attr_value(position, "side")
    cost_basis = get_attr_value(position, "cost_basis") or get_attr_value(position, "total_cost")

    return PositionDTO(
        symbol=str(symbol).upper() if symbol else "UNKNOWN",
        quantity=Decimal(str(quantity)) if quantity is not None else Decimal("0"),
        average_cost=Decimal(str(average_cost)) if average_cost is not None else Decimal("0"),
        current_price=Decimal(str(current_price)) if current_price is not None else Decimal("0"),
        market_value=Decimal(str(market_value)) if market_value is not None else Decimal("0"),
        unrealized_pnl=Decimal(str(unrealized_pnl)) if unrealized_pnl is not None else Decimal("0"),
        unrealized_pnl_percent=Decimal(str(unrealized_pnl_percent))
        if unrealized_pnl_percent is not None
        else Decimal("0"),
        last_updated=last_updated,
        side=str(side) if side else None,
        cost_basis=Decimal(str(cost_basis)) if cost_basis is not None else None,
    )


def portfolio_state_to_dto(
    portfolio_data: Any,  # Portfolio state object or dict
    positions: list[Any] | None = None,  # List of position objects
    correlation_id: str | None = None,
    causation_id: str | None = None,
    portfolio_id: str | None = None,
) -> PortfolioStateDTO:
    """Convert internal portfolio state to PortfolioStateDTO.

    Args:
        portfolio_data: Internal portfolio state object or metrics dict
        positions: Optional list of position objects
        correlation_id: Optional correlation ID, generated if not provided
        causation_id: Optional causation ID, uses correlation_id if not provided
        portfolio_id: Optional portfolio ID override

    Returns:
        PortfolioStateDTO instance

    """
    # Generate IDs if not provided
    if correlation_id is None:
        correlation_id = f"portfolio_{uuid.uuid4().hex[:12]}"
    if causation_id is None:
        causation_id = correlation_id
    if portfolio_id is None:
        portfolio_id = f"default_portfolio_{datetime.now(UTC).strftime('%Y%m%d')}"

    def get_value(obj: Any, key: str, default: Any = Decimal("0")) -> Any:
        """Get value from object or dict."""
        if hasattr(obj, key):
            return getattr(obj, key)
        if isinstance(obj, dict) and key in obj:
            return obj[key]
        return default

    # Extract portfolio metrics
    total_value = get_value(portfolio_data, "total_value") or get_value(
        portfolio_data, "portfolio_value"
    )
    cash_value = get_value(portfolio_data, "cash_value") or get_value(portfolio_data, "cash")
    equity_value = get_value(portfolio_data, "equity_value") or get_value(portfolio_data, "equity")
    buying_power = get_value(portfolio_data, "buying_power") or get_value(
        portfolio_data, "daytrading_buying_power"
    )

    # P&L metrics
    day_pnl = get_value(portfolio_data, "day_pnl") or get_value(portfolio_data, "unrealized_pl")
    day_pnl_percent = get_value(portfolio_data, "day_pnl_percent") or get_value(
        portfolio_data, "unrealized_plpc"
    )
    total_pnl = get_value(portfolio_data, "total_pnl") or day_pnl
    total_pnl_percent = get_value(portfolio_data, "total_pnl_percent") or day_pnl_percent

    # Risk metrics (optional)
    portfolio_margin = get_value(portfolio_data, "portfolio_margin", None)
    maintenance_margin = get_value(portfolio_data, "maintenance_margin", None)

    # Create metrics DTO
    metrics = PortfolioMetricsDTO(
        total_value=Decimal(str(total_value)) if total_value is not None else Decimal("0"),
        cash_value=Decimal(str(cash_value)) if cash_value is not None else Decimal("0"),
        equity_value=Decimal(str(equity_value)) if equity_value is not None else Decimal("0"),
        buying_power=Decimal(str(buying_power)) if buying_power is not None else Decimal("0"),
        day_pnl=Decimal(str(day_pnl)) if day_pnl is not None else Decimal("0"),
        day_pnl_percent=Decimal(str(day_pnl_percent))
        if day_pnl_percent is not None
        else Decimal("0"),
        total_pnl=Decimal(str(total_pnl)) if total_pnl is not None else Decimal("0"),
        total_pnl_percent=Decimal(str(total_pnl_percent))
        if total_pnl_percent is not None
        else Decimal("0"),
        portfolio_margin=Decimal(str(portfolio_margin)) if portfolio_margin is not None else None,
        maintenance_margin=Decimal(str(maintenance_margin))
        if maintenance_margin is not None
        else None,
    )

    # Convert positions if provided
    position_dtos = []
    if positions:
        for position in positions:
            try:
                position_dto = position_to_dto(position)
                position_dtos.append(position_dto)
            except Exception as e:
                # Log warning but continue with other positions
                # In a real implementation, you'd use proper logging
                print(f"Warning: Failed to convert position {position}: {e}")

    # Extract strategy allocations if available
    strategy_allocations = get_value(portfolio_data, "strategy_allocations", {})
    if isinstance(strategy_allocations, dict):
        # Convert values to Decimal
        strategy_allocations = {k: Decimal(str(v)) for k, v in strategy_allocations.items()}
    else:
        strategy_allocations = {}

    # Extract constraints and settings
    cash_target = get_value(portfolio_data, "cash_target", None)
    max_position_size = get_value(portfolio_data, "max_position_size", None)
    rebalance_threshold = get_value(portfolio_data, "rebalance_threshold", None)
    last_rebalance_time = get_value(portfolio_data, "last_rebalance_time", None)

    # Handle timestamp conversion
    if last_rebalance_time and isinstance(last_rebalance_time, str):
        try:
            last_rebalance_time = datetime.fromisoformat(last_rebalance_time.replace("Z", "+00:00"))
        except ValueError:
            last_rebalance_time = None

    # Extract account ID
    account_id = get_value(portfolio_data, "account_id", None)

    return PortfolioStateDTO(
        correlation_id=correlation_id,
        causation_id=causation_id,
        timestamp=datetime.now(UTC),
        portfolio_id=portfolio_id,
        account_id=str(account_id) if account_id else None,
        positions=position_dtos,
        metrics=metrics,
        strategy_allocations=strategy_allocations,
        cash_target=Decimal(str(cash_target)) if cash_target is not None else None,
        max_position_size=Decimal(str(max_position_size))
        if max_position_size is not None
        else None,
        rebalance_threshold=Decimal(str(rebalance_threshold))
        if rebalance_threshold is not None
        else None,
        last_rebalance_time=last_rebalance_time,
    )


def dto_to_portfolio_context(dto: PortfolioStateDTO) -> dict[str, Any]:
    """Convert PortfolioStateDTO to context dict for other modules.

    Args:
        dto: PortfolioStateDTO instance

    Returns:
        Dictionary with portfolio context data

    """
    return {
        "portfolio_id": dto.portfolio_id,
        "account_id": dto.account_id,
        "total_value": float(dto.metrics.total_value),
        "cash_value": float(dto.metrics.cash_value),
        "equity_value": float(dto.metrics.equity_value),
        "buying_power": float(dto.metrics.buying_power),
        "day_pnl": float(dto.metrics.day_pnl),
        "total_pnl": float(dto.metrics.total_pnl),
        "positions": [
            {
                "symbol": pos.symbol,
                "quantity": float(pos.quantity),
                "market_value": float(pos.market_value),
                "unrealized_pnl": float(pos.unrealized_pnl),
            }
            for pos in dto.positions
        ],
        "strategy_allocations": {k: float(v) for k, v in dto.strategy_allocations.items()},
        "timestamp": dto.timestamp,
        "correlation_id": dto.correlation_id,
        "causation_id": dto.causation_id,
    }


def batch_positions_to_dtos(
    positions: list[Any],  # list[Position]
    correlation_context: dict[str, Any] | None = None,
) -> list[PositionDTO]:
    """Convert a batch of positions to DTOs.

    Args:
        positions: List of internal position objects
        correlation_context: Optional correlation context

    Returns:
        List of PositionDTO instances

    """
    dtos = []
    for position in positions:
        try:
            dto = position_to_dto(position, correlation_context)
            dtos.append(dto)
        except Exception as e:
            # Log warning but continue with other positions
            print(f"Warning: Failed to convert position {position}: {e}")

    return dtos
