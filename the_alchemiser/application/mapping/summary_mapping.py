"""Business Unit: portfolio | Status: current.

Summary mapping utilities for multi-strategy execution results.

Provides mapping functions to assemble unified summary DTOs without
interface layer imports, maintaining proper layering separation.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any

from the_alchemiser.application.trading.portfolio_calculations import (
    AllocationComparison,
    build_allocation_comparison,
)
from the_alchemiser.domain.types import AccountInfo, PositionsDict

if TYPE_CHECKING:
    from the_alchemiser.interfaces.schemas.common import (
        AllocationComparisonDTO,
        MultiStrategySummaryDTO,
    )


def _allocation_comparison_to_dto(comparison: AllocationComparison) -> AllocationComparisonDTO:
    """Convert AllocationComparison TypedDict to DTO.
    
    Args:
        comparison: AllocationComparison TypedDict from application layer
        
    Returns:
        AllocationComparisonDTO for interface layer usage

    """
    from the_alchemiser.interfaces.schemas.common import AllocationComparisonDTO
    
    return AllocationComparisonDTO(
        target_values=comparison["target_values"],
        current_values=comparison["current_values"],
        deltas=comparison["deltas"]
    )


def build_multi_strategy_summary(
    execution_result: Any,  # MultiStrategyExecutionResultDTO
    target_portfolio: dict[str, float],
    account_info: AccountInfo | dict[str, Any],
    current_positions: PositionsDict | dict[str, Any],
    enriched_account: dict[str, Any] | None = None,
    closed_pnl_summary: dict[str, Decimal] | None = None,
) -> MultiStrategySummaryDTO:
    """Build unified multi-strategy summary DTO with allocation comparison.
    
    Assembles all execution data, allocation comparison, and enriched account
    information into a single DTO to eliminate duplicate calculations in
    the CLI renderer and ensure consistent Decimal precision.
    
    Args:
        execution_result: Core execution result DTO
        target_portfolio: Target allocation weights by symbol
        account_info: Account information for allocation calculations
        current_positions: Current position data
        enriched_account: Optional enriched account data for display
        closed_pnl_summary: Optional closed P&L summary metrics
        
    Returns:
        MultiStrategySummaryDTO containing all rendering data

    """
    from the_alchemiser.interfaces.schemas.common import MultiStrategySummaryDTO
    
    # Build allocation comparison using application layer function
    allocation_comparison = build_allocation_comparison(
        target_portfolio=target_portfolio,
        account_info=account_info,
        current_positions=current_positions
    )
    
    # Convert to DTO for interface layer
    allocation_dto = _allocation_comparison_to_dto(allocation_comparison)
    
    # Use enriched account or fallback to execution result account info
    final_enriched_account = enriched_account or dict(execution_result.account_info_after)
    
    return MultiStrategySummaryDTO(
        execution_result=execution_result,
        allocation_comparison=allocation_dto,
        enriched_account=final_enriched_account,
        closed_pnl_summary=closed_pnl_summary
    )


__all__ = [
    "build_multi_strategy_summary",
]