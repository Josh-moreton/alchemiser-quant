#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Portfolio adapter functions for converting between internal objects and DTOs.

Provides adapter functions for portfolio-related data transformations,
supporting communication between modules.
"""

from __future__ import annotations

from typing import Any

from the_alchemiser.shared.dto.portfolio_state_dto import PortfolioStateDTO, PositionDTO


def portfolio_state_to_dto(
    portfolio_data: dict[str, Any],
    positions: list[dict[str, Any]],
    correlation_id: str | None = None,
    portfolio_id: str = "main_portfolio",
) -> PortfolioStateDTO:
    """Convert portfolio data and positions to PortfolioStateDTO.
    
    Args:
        portfolio_data: Portfolio data as dictionary
        positions: List of position dictionaries
        correlation_id: Optional correlation ID for tracking
        portfolio_id: Portfolio identifier
        
    Returns:
        PortfolioStateDTO object

    """
    import uuid
    from datetime import UTC, datetime
    from decimal import Decimal
    
    # Convert position dictionaries to PositionDTO objects
    position_dtos = [position_to_dto(pos) for pos in positions]
    
    # Create portfolio metrics from the portfolio data
    from the_alchemiser.shared.dto import PortfolioMetricsDTO
    
    metrics = PortfolioMetricsDTO(
        total_value=Decimal(str(portfolio_data.get("total_value", portfolio_data.get("portfolio_value", 0)))),
        cash_value=Decimal(str(portfolio_data.get("cash_value", 0))),
        equity_value=Decimal(str(portfolio_data.get("equity_value", 0))),
        buying_power=Decimal(str(portfolio_data.get("buying_power", 0))),
        day_pnl=Decimal(str(portfolio_data.get("day_pnl", 0))),
        day_pnl_percent=Decimal(str(portfolio_data.get("day_pnl_percent", 0))),
        total_pnl=Decimal(str(portfolio_data.get("total_pnl", 0))),
        total_pnl_percent=Decimal(str(portfolio_data.get("total_pnl_percent", 0))),
    )
    
    correlation_id = correlation_id or f"portfolio_{uuid.uuid4().hex[:12]}"
    
    return PortfolioStateDTO(
        correlation_id=correlation_id,
        causation_id=correlation_id,
        timestamp=datetime.now(UTC),
        portfolio_id=portfolio_id,
        positions=position_dtos,
        metrics=metrics,
        metadata=portfolio_data.get("metadata", {}),
    )


def position_to_dto(position: dict[str, Any]) -> PositionDTO:
    """Convert position dictionary to PositionDTO.
    
    Args:
        position: Position as dictionary
        
    Returns:
        PositionDTO object

    """
    from decimal import Decimal

    # Import the PositionDTO from the correct location
    from the_alchemiser.shared.dto.portfolio_state_dto import PositionDTO
    
    return PositionDTO(
        symbol=position.get("symbol", ""),
        quantity=Decimal(str(position.get("qty", position.get("quantity", 0)))),
        average_cost=Decimal(str(position.get("avg_entry_price", position.get("average_cost", 0)))),
        current_price=Decimal(str(position.get("current_price", 0))),
        market_value=Decimal(str(position.get("market_value", 0))),
        unrealized_pnl=Decimal(str(position.get("unrealized_pl", position.get("unrealized_pnl", 0)))),
        unrealized_pnl_percent=Decimal(str(position.get("unrealized_plpc", position.get("unrealized_pnl_percent", 0)))),
        last_updated=position.get("last_updated"),
        side=position.get("side"),
        cost_basis=Decimal(str(position.get("cost_basis", 0))) if position.get("cost_basis") is not None else None,
    )