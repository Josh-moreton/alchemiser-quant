"""Business Unit: utilities; Status: current.

Common DTOs for application layer and interface boundaries.

This module provides Pydantic v2 DTOs for common data structures used across
the application layer, replacing loose dataclasses and dict usage with
strongly typed, validated structures.

Key Features:
- Pydantic v2 BaseModel with strict validation
- Type safety for execution results and summaries
- Comprehensive field validation and normalization
- Immutable DTOs for consistent data flow
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, ConfigDict

from the_alchemiser.shared.dto.execution_report_dto import ExecutionReportDTO
from the_alchemiser.shared.dto.portfolio_state_dto import PortfolioStateDTO
from the_alchemiser.shared.value_objects.core_types import AccountInfo, OrderDetails, StrategySignal

if TYPE_CHECKING:
    from decimal import Decimal

    from the_alchemiser.strategy.types.strategy_type import StrategyType


class MultiStrategyExecutionResultDTO(BaseModel):
    """DTO for multi-strategy execution results.

    Provides an immutable, validated container for multi-strategy execution
    outcomes, replacing the dataclass version with enhanced type safety
    and validation capabilities.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Core execution status
    success: bool

    # Strategy data
    strategy_signals: dict[StrategyType, StrategySignal]
    consolidated_portfolio: dict[str, float]

    # Order execution results
    orders_executed: list[OrderDetails]

    # Account state tracking
    account_info_before: AccountInfo
    account_info_after: AccountInfo

    # Structured execution summary and portfolio state
    execution_summary: ExecutionReportDTO
    final_portfolio_state: PortfolioStateDTO | None = None


class AllocationComparisonDTO(BaseModel):
    """DTO for allocation comparison with Decimal precision."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    target_values: dict[str, Decimal]
    current_values: dict[str, Decimal]
    deltas: dict[str, Decimal]


class MultiStrategySummaryDTO(BaseModel):
    """DTO for multi-strategy summary including allocation comparison & account info.

    Provides a unified summary structure that includes execution results,
    allocation comparison, and enriched account information for CLI rendering.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    # Core execution result
    execution_result: MultiStrategyExecutionResultDTO

    # Allocation comparison with Decimal precision
    allocation_comparison: AllocationComparisonDTO | None = None

    # Enriched account information
    enriched_account: dict[str, Any] | None = None

    # Closed P&L subset for performance display
    closed_pnl_subset: dict[str, Any] | None = None
