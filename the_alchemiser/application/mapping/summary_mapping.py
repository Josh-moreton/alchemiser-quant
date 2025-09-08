"""Business Unit: shared | Status: current.

Summary mapping functions for assembling multi-strategy DTOs.

This module provides mapping utilities to create MultiStrategySummaryDTO
from execution results, allocation comparisons, and account information.
"""

from __future__ import annotations

from typing import Any

from the_alchemiser.portfolio.calculations.portfolio_calculations import AllocationComparison
from the_alchemiser.shared.schemas.common import (
    AllocationComparisonDTO,
    MultiStrategyExecutionResultDTO,
    MultiStrategySummaryDTO,
)


def create_multi_strategy_summary(
    execution_result: MultiStrategyExecutionResultDTO,
    allocation_comparison: AllocationComparison | None = None,
    enriched_account: dict[str, Any] | None = None,
    closed_pnl_subset: dict[str, Any] | None = None,
) -> MultiStrategySummaryDTO:
    """Assemble a MultiStrategySummaryDTO from execution results and optional components.

    Args:
        execution_result: The core execution result
        allocation_comparison: Optional allocation comparison with Decimal precision
        enriched_account: Optional enriched account information
        closed_pnl_subset: Optional closed P&L subset for performance display

    Returns:
        MultiStrategySummaryDTO with all components assembled

    """
    allocation_comparison_dto = None
    if allocation_comparison:
        allocation_comparison_dto = AllocationComparisonDTO(
            target_values=allocation_comparison["target_values"],
            current_values=allocation_comparison["current_values"],
            deltas=allocation_comparison["deltas"],
        )

    return MultiStrategySummaryDTO(
        execution_result=execution_result,
        allocation_comparison=allocation_comparison_dto,
        enriched_account=enriched_account,
        closed_pnl_subset=closed_pnl_subset,
    )


def allocation_comparison_to_dict(allocation_comparison: AllocationComparisonDTO) -> dict[str, Any]:
    """Convert AllocationComparisonDTO to dict format for renderer compatibility.

    Args:
        allocation_comparison: The allocation comparison DTO

    Returns:
        Dict with target_values, current_values, and deltas

    """
    return {
        "target_values": allocation_comparison.target_values,
        "current_values": allocation_comparison.current_values,
        "deltas": allocation_comparison.deltas,
    }
