#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Portfolio adapter functions for converting between internal objects and DTOs.

Provides adapter functions for portfolio-related data transformations,
supporting communication between modules.
"""

from __future__ import annotations

from typing import Any

from the_alchemiser.shared.dto import PortfolioStateDTO, PositionDTO


def batch_positions_to_dtos(
    positions: list[dict[str, Any]],
) -> list[PositionDTO]:
    """Convert batch of position dictionaries to PositionDTO objects.
    
    Args:
        positions: List of position dictionaries
        
    Returns:
        List of PositionDTO objects
    """
    return [position_to_dto(position) for position in positions]


def dto_to_portfolio_context(
    portfolio_dto: PortfolioStateDTO,
) -> dict[str, Any]:
    """Convert PortfolioStateDTO to portfolio context dictionary.
    
    Args:
        portfolio_dto: PortfolioStateDTO object
        
    Returns:
        Portfolio context as dictionary
    """
    return {
        "total_portfolio_value": portfolio_dto.total_portfolio_value,
        "target_allocations": portfolio_dto.target_allocations,
        "current_allocations": portfolio_dto.current_allocations,
        "target_values": portfolio_dto.target_values,
        "current_values": portfolio_dto.current_values,
        "allocation_discrepancies": portfolio_dto.allocation_discrepancies,
        "largest_discrepancy": portfolio_dto.largest_discrepancy,
        "total_symbols": portfolio_dto.total_symbols,
        "correlation_id": portfolio_dto.correlation_id,
        "created_at": portfolio_dto.created_at,
        "positions": [
            {
                "symbol": pos.symbol,
                "quantity": pos.quantity,
                "market_value": pos.market_value,
                "cost_basis": pos.cost_basis,
                "unrealized_pnl": pos.unrealized_pnl,
            }
            for pos in portfolio_dto.positions
        ],
    }


def portfolio_state_to_dto(
    portfolio_state: dict[str, Any],
    correlation_id: str | None = None,
) -> PortfolioStateDTO:
    """Convert portfolio state dictionary to PortfolioStateDTO.
    
    Args:
        portfolio_state: Portfolio state as dictionary
        correlation_id: Optional correlation ID for tracking
        
    Returns:
        PortfolioStateDTO object
    """
    from decimal import Decimal
    from datetime import datetime, UTC
    
    # Helper function to convert to Decimal
    def to_decimal_dict(source: dict[str, Any]) -> dict[str, Decimal]:
        return {k: Decimal(str(v)) for k, v in source.items()}
    
    # Convert position dictionaries to PositionDTO objects
    positions = []
    if "positions" in portfolio_state:
        positions = [position_to_dto(pos) for pos in portfolio_state["positions"]]
    
    return PortfolioStateDTO(
        total_portfolio_value=Decimal(str(portfolio_state.get("total_portfolio_value", 0.0))),
        target_allocations=to_decimal_dict(portfolio_state.get("target_allocations", {})),
        current_allocations=to_decimal_dict(portfolio_state.get("current_allocations", {})),
        target_values=to_decimal_dict(portfolio_state.get("target_values", {})),
        current_values=to_decimal_dict(portfolio_state.get("current_values", {})),
        allocation_discrepancies=to_decimal_dict(portfolio_state.get("allocation_discrepancies", {})),
        largest_discrepancy=Decimal(str(portfolio_state["largest_discrepancy"])) if portfolio_state.get("largest_discrepancy") is not None else None,
        total_symbols=portfolio_state.get("total_symbols", 0),
        positions=positions,
        correlation_id=correlation_id or portfolio_state.get("correlation_id"),
        created_at=portfolio_state.get("created_at") or datetime.now(UTC),
    )


def position_to_dto(position: dict[str, Any]) -> PositionDTO:
    """Convert position dictionary to PositionDTO.
    
    Args:
        position: Position as dictionary
        
    Returns:
        PositionDTO object
    """
    from decimal import Decimal
    from datetime import datetime, UTC
    
    return PositionDTO(
        symbol=position.get("symbol", ""),
        quantity=Decimal(str(position.get("quantity", 0))),
        market_value=Decimal(str(position.get("market_value", 0))),
        cost_basis=Decimal(str(position.get("cost_basis", 0))),
        unrealized_pnl=Decimal(str(position.get("unrealized_pnl", 0))),
        correlation_id=position.get("correlation_id"),
        created_at=position.get("created_at") or datetime.now(UTC),
    )