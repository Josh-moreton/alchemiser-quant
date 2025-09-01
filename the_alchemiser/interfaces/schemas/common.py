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

from pydantic import BaseModel, ConfigDict


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

    # Strategy data (using Any to avoid circular imports)
    strategy_signals: dict[Any, Any]
    consolidated_portfolio: dict[str, float]

    # Order execution results
    orders_executed: list[dict[str, Any]]

    # Account state tracking
    account_info_before: dict[str, Any]
    account_info_after: dict[str, Any]

    # Structured execution summary and portfolio state (Any to avoid imports)
    execution_summary: dict[str, Any]
    final_portfolio_state: dict[str, Any] | None = None


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
    """DTO for consolidated multi-strategy summary with allocation comparison.
    
    Provides a single unified DTO containing execution results, allocation 
    comparison, enriched account info, and closed P&L subset to eliminate
    duplicate calculations and ensure consistent Decimal precision across
    the CLI rendering pipeline.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Core execution results (Any to avoid circular imports)
    execution_result: Any
    
    # Allocation comparison with Decimal precision
    allocation_comparison: AllocationComparisonDTO
    
    # Enriched account information
    enriched_account: dict[str, Any]
    
    # Closed P&L subset (summary metrics only to avoid duplication)
    closed_pnl_summary: dict[str, Decimal] | None = None
