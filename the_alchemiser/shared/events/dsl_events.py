#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

DSL engine event schemas for event-driven architecture.

Provides specific event classes for DSL strategy evaluation workflow:
- StrategyEvaluationRequested: Trigger for DSL evaluation
- StrategyEvaluated: DSL evaluation completion with trace
- IndicatorComputed: Individual indicator calculation completion
- PortfolioAllocationProduced: Final allocation result
- FilterEvaluated: Filter decision completion
- TopNSelected: Top-N selection completion
"""

from __future__ import annotations

from typing import Any

from pydantic import Field

from ..constants import EVENT_SCHEMA_VERSION_DESCRIPTION, EVENT_TYPE_DESCRIPTION
from ..dto.ast_node_dto import ASTNodeDTO
from ..dto.indicator_request_dto import PortfolioFragmentDTO
from ..dto.strategy_allocation_dto import StrategyAllocation
from ..dto.technical_indicators_dto import TechnicalIndicatorDTO
from ..dto.trace_dto import TraceDTO
from .base import BaseEvent

# Constants


class StrategyEvaluationRequested(BaseEvent):
    """Event requesting DSL strategy evaluation.

    Triggers the DSL engine to evaluate a specific strategy configuration.
    """

    # Override event_type with default
    event_type: str = Field(
        default="StrategyEvaluationRequested", description=EVENT_TYPE_DESCRIPTION
    )

    # Schema version for backward compatibility
    schema_version: int = Field(default=1, ge=1, description=EVENT_SCHEMA_VERSION_DESCRIPTION)

    # Request fields
    strategy_id: str = Field(..., min_length=1, description="Strategy identifier to evaluate")
    strategy_config_path: str = Field(..., min_length=1, description="Path to .clj strategy file")
    universe: list[str] = Field(default_factory=list, description="Trading universe symbols")
    as_of_date: str | None = Field(
        default=None, description="Optional evaluation date (ISO format)"
    )

    # Optional parameters
    parameters: dict[str, Any] = Field(default_factory=dict, description="Evaluation parameters")


class StrategyEvaluated(BaseEvent):
    """Event emitted when DSL strategy evaluation completes.

    Contains the complete evaluation result with trace and allocation.
    """

    # Override event_type with default
    event_type: str = Field(default="StrategyEvaluated", description=EVENT_TYPE_DESCRIPTION)

    # Schema version for backward compatibility
    schema_version: int = Field(default=1, ge=1, description=EVENT_SCHEMA_VERSION_DESCRIPTION)

    # Result fields
    strategy_id: str = Field(..., min_length=1, description="Strategy that was evaluated")
    allocation: StrategyAllocation = Field(..., description="Final portfolio allocation")
    trace: TraceDTO = Field(..., description="Complete evaluation trace")
    success: bool = Field(..., description="Whether evaluation succeeded")

    # Optional error information
    error_message: str | None = Field(
        default=None, description="Error message if evaluation failed"
    )
    error_code: str | None = Field(default=None, description="Structured error code if failed")

    # Metadata
    evaluation_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional evaluation metadata"
    )


class IndicatorComputed(BaseEvent):
    """Event emitted when an indicator is computed.

    Published during DSL evaluation for each indicator calculation.
    """

    # Override event_type with default
    event_type: str = Field(default="IndicatorComputed", description=EVENT_TYPE_DESCRIPTION)

    # Schema version for backward compatibility
    schema_version: int = Field(default=1, ge=1, description=EVENT_SCHEMA_VERSION_DESCRIPTION)

    # Indicator fields
    request_id: str = Field(..., min_length=1, description="Original request identifier")
    indicator: TechnicalIndicatorDTO = Field(..., description="Computed indicator data")
    computation_time_ms: float = Field(ge=0, description="Computation time in milliseconds")

    # Optional metadata
    computation_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional computation metadata"
    )


class PortfolioAllocationProduced(BaseEvent):
    """Event emitted when final portfolio allocation is produced.

    Contains the allocation result from DSL strategy evaluation.
    """

    # Override event_type with default
    event_type: str = Field(
        default="PortfolioAllocationProduced", description=EVENT_TYPE_DESCRIPTION
    )

    # Schema version for backward compatibility
    schema_version: int = Field(default=1, ge=1, description=EVENT_SCHEMA_VERSION_DESCRIPTION)

    # Allocation fields
    strategy_id: str = Field(..., min_length=1, description="Strategy that produced allocation")
    allocation: StrategyAllocation = Field(..., description="Portfolio allocation result")
    allocation_type: str = Field(
        ..., min_length=1, description="Type of allocation (final, intermediate)"
    )

    # Metadata
    allocation_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional allocation metadata"
    )


class FilterEvaluated(BaseEvent):
    """Event emitted when a filter decision is evaluated.

    Published during DSL evaluation for filter operations.
    """

    # Override event_type with default
    event_type: str = Field(default="FilterEvaluated", description=EVENT_TYPE_DESCRIPTION)

    # Schema version for backward compatibility
    schema_version: int = Field(default=1, ge=1, description=EVENT_SCHEMA_VERSION_DESCRIPTION)

    # Filter fields
    filter_expression: ASTNodeDTO = Field(..., description="Filter expression that was evaluated")
    input_symbols: list[str] = Field(default_factory=list, description="Input symbols to filter")
    filtered_symbols: list[str] = Field(
        default_factory=list, description="Symbols that passed filter"
    )
    filter_criteria: dict[str, Any] = Field(
        default_factory=dict, description="Filter criteria used"
    )

    # Metadata
    filter_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional filter metadata"
    )


class TopNSelected(BaseEvent):
    """Event emitted when top-N selection is completed.

    Published during DSL evaluation for selection operations.
    """

    # Override event_type with default
    event_type: str = Field(default="TopNSelected", description=EVENT_TYPE_DESCRIPTION)

    # Schema version for backward compatibility
    schema_version: int = Field(default=1, ge=1, description=EVENT_SCHEMA_VERSION_DESCRIPTION)

    # Selection fields
    selection_expression: ASTNodeDTO = Field(
        ..., description="Selection expression that was evaluated"
    )
    input_symbols: list[str] = Field(
        default_factory=list, description="Input symbols for selection"
    )
    selected_symbols: list[str] = Field(default_factory=list, description="Selected symbols")
    selection_criteria: dict[str, Any] = Field(
        default_factory=dict, description="Selection criteria used"
    )
    n_selected: int = Field(ge=0, description="Number of symbols selected")

    # Metadata
    selection_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional selection metadata"
    )


class DecisionEvaluated(BaseEvent):
    """Event emitted when a decision branch is evaluated.

    Published during DSL evaluation for conditional expressions.
    """

    # Override event_type with default
    event_type: str = Field(default="DecisionEvaluated", description=EVENT_TYPE_DESCRIPTION)

    # Schema version for backward compatibility
    schema_version: int = Field(default=1, ge=1, description=EVENT_SCHEMA_VERSION_DESCRIPTION)

    # Decision fields
    decision_expression: ASTNodeDTO = Field(
        ..., description="Decision expression that was evaluated"
    )
    condition_result: bool = Field(..., description="Result of condition evaluation")
    branch_taken: str = Field(..., min_length=1, description="Branch taken (then/else)")
    branch_result: PortfolioFragmentDTO | None = Field(
        default=None, description="Result of branch evaluation"
    )

    # Metadata
    decision_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional decision metadata"
    )
