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

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from the_alchemiser.shared.schemas.execution_summary import ExecutionSummary
from the_alchemiser.shared.schemas.portfolio_state import PortfolioState
from the_alchemiser.shared.value_objects.core_types import (
    AccountInfo,
    OrderDetails,
    StrategySignal,
)


class MultiStrategyExecutionResult(BaseModel):
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
    success: bool = Field(..., description="Whether the execution was successful")

    # Strategy data
    strategy_signals: dict[str, StrategySignal] = Field(
        ..., description="Strategy signals by strategy name"
    )
    consolidated_portfolio: dict[str, Decimal] = Field(
        ..., description="Consolidated portfolio allocations by symbol (Decimal precision)"
    )

    # Order execution results
    orders_executed: list[OrderDetails] = Field(..., description="List of executed order details")

    # Account state tracking
    account_info_before: AccountInfo = Field(..., description="Account state before execution")
    account_info_after: AccountInfo = Field(..., description="Account state after execution")

    # Structured execution summary and portfolio state
    execution_summary: ExecutionSummary = Field(
        ..., description="Structured execution summary with metrics"
    )
    final_portfolio_state: PortfolioState | None = Field(
        None, description="Final portfolio state after execution (optional)"
    )


class AllocationComparison(BaseModel):
    """DTO for allocation comparison with Decimal precision.

    Provides precise comparison of target vs current allocations with calculated deltas.
    All values use Decimal to maintain financial precision per Alchemiser guardrails.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    target_values: dict[str, Decimal] = Field(..., description="Target allocation values by symbol")
    current_values: dict[str, Decimal] = Field(
        ..., description="Current allocation values by symbol"
    )
    deltas: dict[str, Decimal] = Field(
        ..., description="Allocation deltas by symbol (current - target)"
    )


class MultiStrategySummary(BaseModel):
    """DTO for multi-strategy summary including allocation comparison & account info.

    Provides a unified summary structure that includes execution results,
    allocation comparison, and enriched account information for CLI rendering.

    Note: enriched_account and closed_pnl_subset use dict[str, Any] to support
    flexible display/rendering requirements. This is intentional for UI/CLI boundaries.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    # Core execution result
    execution_result: MultiStrategyExecutionResult = Field(
        ..., description="Multi-strategy execution result with metrics"
    )

    # Allocation comparison with Decimal precision
    allocation_comparison: AllocationComparison | None = Field(
        None, description="Optional allocation comparison with target vs current"
    )

    # Enriched account information (flexible for CLI/display)
    enriched_account: dict[str, Any] | None = Field(
        None,
        description="Enriched account data for display (flexible schema for UI rendering)",
    )

    # Closed P&L subset for performance display (flexible for CLI/display)
    closed_pnl_subset: dict[str, Any] | None = Field(
        None, description="Closed P&L data subset for display (flexible schema for UI rendering)"
    )


class Configuration(BaseModel):
    """Placeholder for configuration data transfer.

    Proper Pydantic v2 DTO to replace placeholder class.
    Will be enhanced with specific config fields in Phase 2.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    config_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Configuration data (flexible for Phase 1 scaffolding)",
    )


class Error(BaseModel):
    """Placeholder for error data transfer.

    Proper Pydantic v2 DTO to replace placeholder class.
    Will be enhanced with specific error fields in Phase 2.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    error_type: str = Field(description="Type of error")
    message: str = Field(description="Error message")
    context: dict[str, Any] = Field(default_factory=dict, description="Error context data")
