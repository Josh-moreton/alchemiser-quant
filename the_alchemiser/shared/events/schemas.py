#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Event schema DTOs for event-driven architecture.

Provides specific event classes for the system workflow:
- StartupEvent: System initialization event
- SignalGenerated: Strategy signal generation event
- RebalancePlanned: Portfolio rebalancing plan event
- TradeExecuted: Trade execution completion event
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import Field

from ..constants import EVENT_TYPE_DESCRIPTION
from ..schemas.common import AllocationComparisonDTO
from ..schemas.portfolio_state import PortfolioStateDTO
from ..schemas.rebalance_plan import RebalancePlanDTO
from .base import BaseEvent

# Constants


class StartupEvent(BaseEvent):
    """Event emitted when the system starts up.

    Triggers the beginning of workflow processes.
    """

    # Override event_type with default
    event_type: str = Field(default="StartupEvent", description=EVENT_TYPE_DESCRIPTION)

    # Startup-specific fields
    startup_mode: str = Field(..., description="Startup mode (signal, trade, etc.)")
    configuration: dict[str, Any] | None = Field(
        default=None, description="Startup configuration parameters"
    )


class SignalGenerated(BaseEvent):
    """Event emitted when strategy signals are generated.

    Contains the strategy signal data for portfolio consumption with
    idempotency support and enhanced metadata for event-driven workflows.
    """

    # Override event_type with default
    event_type: str = Field(default="SignalGenerated", description=EVENT_TYPE_DESCRIPTION)

    # Signal-specific fields
    signals_data: dict[str, Any] = Field(..., description="Strategy signals data")
    consolidated_portfolio: dict[str, Any] = Field(
        ..., description="Consolidated portfolio allocation"
    )
    signal_count: int = Field(..., description="Number of signals generated")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional signal metadata")

    # Event-driven enhancement fields for idempotency and traceability
    schema_version: str = Field(default="1.0", description="Event schema version for compatibility")
    signal_hash: str = Field(..., description="Deterministic hash of signal data for idempotency")
    market_snapshot_id: str = Field(
        ..., description="Market data snapshot identifier for correlation"
    )


class RebalancePlanned(BaseEvent):
    """Event emitted when portfolio rebalancing plan is created.

    Contains the rebalancing plan for execution consumption with enhanced
    metadata for idempotency and deterministic replay support.
    """

    # Override event_type with default
    event_type: str = Field(default="RebalancePlanned", description=EVENT_TYPE_DESCRIPTION)

    # Rebalance-specific fields
    rebalance_plan: RebalancePlanDTO = Field(..., description="Portfolio rebalancing plan")
    allocation_comparison: AllocationComparisonDTO = Field(
        ..., description="Allocation comparison data"
    )
    trades_required: bool = Field(..., description="Whether trades are required")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional rebalance metadata"
    )

    # Event-driven enhancement fields for idempotency and traceability
    schema_version: str = Field(default="1.0", description="Event schema version for compatibility")
    plan_hash: str = Field(..., description="Deterministic hash of rebalance plan for idempotency")
    account_snapshot_id: str = Field(
        ..., description="Account state snapshot identifier for correlation"
    )


class TradeExecuted(BaseEvent):
    """Event emitted when trades are executed.

    Contains the execution results and updated portfolio state.
    Also serves as settlement event with alias 'execution.order.settled.v1'.
    """

    # Override event_type with default, supporting alias for settlement
    event_type: str = Field(default="TradeExecuted", description=EVENT_TYPE_DESCRIPTION)

    # Enhanced execution fields with metadata
    execution_data: dict[str, Any] = Field(..., description="Trade execution data")
    success: bool = Field(..., description="Whether execution was successful")
    orders_placed: int = Field(..., description="Number of orders placed")
    orders_succeeded: int = Field(..., description="Number of orders that succeeded")

    # New idempotency and schema fields
    schema_version: str = Field(default="1.0", description="Event schema version")
    execution_plan_hash: str = Field(
        ..., description="Hash of execution plan for idempotency"
    )

    # Enhanced metadata with fill summaries
    fill_summaries: dict[str, Any] = Field(
        default_factory=dict, description="Order fill summary data"
    )
    settlement_details: dict[str, Any] = Field(
        default_factory=dict, description="Settlement-specific details"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional execution metadata"
    )

    @property
    def settlement_event_type(self) -> str:
        """Return the settlement event type alias."""
        return "execution.order.settled.v1"


class TradeExecutionStarted(BaseEvent):
    """Event emitted when trade execution begins.

    Contains the trading plan and execution parameters.
    """

    # Override event_type with default
    event_type: str = Field(default="TradeExecutionStarted", description=EVENT_TYPE_DESCRIPTION)

    # Execution startup fields
    execution_plan: dict[str, Any] = Field(..., description="Trading execution plan")
    portfolio_state_before: PortfolioStateDTO | None = Field(
        default=None, description="Portfolio state before execution"
    )
    trade_mode: str = Field(..., description="Trading mode (live/paper)")
    market_conditions: dict[str, Any] | None = Field(
        default=None, description="Market conditions at execution start"
    )


class PortfolioStateChanged(BaseEvent):
    """Event emitted when portfolio state changes significantly.

    Contains before and after portfolio states for comparison.
    """

    # Override event_type with default
    event_type: str = Field(default="PortfolioStateChanged", description=EVENT_TYPE_DESCRIPTION)

    # Portfolio state change fields
    portfolio_state_before: PortfolioStateDTO = Field(
        ..., description="Portfolio state before change"
    )
    portfolio_state_after: PortfolioStateDTO = Field(
        ..., description="Portfolio state after change"
    )
    change_type: str = Field(..., description="Type of change (rebalance, trade, etc.)")
    change_summary: dict[str, Any] = Field(
        default_factory=dict, description="Summary of changes made"
    )


class AllocationComparisonCompleted(BaseEvent):
    """Event emitted when allocation comparison analysis is completed.

    Contains target vs current allocation analysis results.
    """

    # Override event_type with default
    event_type: str = Field(
        default="AllocationComparisonCompleted", description=EVENT_TYPE_DESCRIPTION
    )

    # Allocation comparison fields
    target_allocations: dict[str, Decimal] = Field(..., description="Target allocation percentages")
    current_allocations: dict[str, Decimal] = Field(
        ..., description="Current allocation percentages"
    )
    allocation_differences: dict[str, Decimal] = Field(
        ..., description="Differences requiring rebalancing"
    )
    rebalancing_required: bool = Field(..., description="Whether rebalancing is needed")
    comparison_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional comparison analysis data"
    )


class OrderSettlementCompleted(BaseEvent):
    """Event emitted when an order settlement is completed.

    Signals that an order has been filled and settled, which may release buying power.
    """

    # Override event_type with default
    event_type: str = Field(default="OrderSettlementCompleted", description=EVENT_TYPE_DESCRIPTION)

    # Settlement fields
    order_id: str = Field(..., description="Order ID that completed settlement")
    symbol: str = Field(..., description="Symbol of the settled order")
    side: str = Field(..., description="Order side (BUY/SELL)")
    settled_quantity: Decimal = Field(..., description="Quantity that settled")
    settlement_price: Decimal = Field(..., description="Price at which settlement occurred")
    settled_value: Decimal = Field(..., description="Total value settled")
    buying_power_released: Decimal = Field(
        default=Decimal("0"), description="Buying power released from settlement"
    )
    original_correlation_id: str | None = Field(
        default=None, description="Original correlation ID for order tracking"
    )


class BulkSettlementCompleted(BaseEvent):
    """Event emitted when multiple sell orders have completed settlement.

    Signals that buying power has been released and buy orders can proceed.
    """

    # Override event_type with default
    event_type: str = Field(default="BulkSettlementCompleted", description=EVENT_TYPE_DESCRIPTION)

    # Bulk settlement fields
    settled_order_ids: list[str] = Field(
        ..., description="List of order IDs that completed settlement"
    )
    total_buying_power_released: Decimal = Field(..., description="Total buying power released")
    settlement_details: dict[str, Any] = Field(
        default_factory=dict, description="Detailed settlement information"
    )
    execution_plan_id: str | None = Field(default=None, description="Associated execution plan ID")


class ExecutionPhaseCompleted(BaseEvent):
    """Event emitted when an execution phase (sell or buy) is completed.

    Used to coordinate multi-phase execution workflows.
    """

    # Override event_type with default
    event_type: str = Field(default="ExecutionPhaseCompleted", description=EVENT_TYPE_DESCRIPTION)

    # Execution phase fields
    phase_type: str = Field(..., description="Phase type (SELL_PHASE/BUY_PHASE)")
    plan_id: str = Field(..., description="Execution plan ID")
    completed_orders: list[str] = Field(..., description="Order IDs completed in this phase")
    successful_orders: list[str] = Field(..., description="Successfully completed order IDs")
    failed_orders: list[str] = Field(default_factory=list, description="Failed order IDs")
    phase_metadata: dict[str, Any] = Field(
        default_factory=dict, description="Phase execution metadata"
    )


class WorkflowStarted(BaseEvent):
    """Event emitted when a complete trading workflow starts.

    Used to initiate the event-driven workflow coordination.
    """

    # Override event_type with default
    event_type: str = Field(default="WorkflowStarted", description=EVENT_TYPE_DESCRIPTION)

    # Workflow fields
    workflow_type: str = Field(..., description="Type of workflow (trading, signal_analysis, etc.)")
    requested_by: str = Field(..., description="Component that requested the workflow")
    configuration: dict[str, Any] = Field(
        default_factory=dict, description="Workflow configuration parameters"
    )


class WorkflowCompleted(BaseEvent):
    """Event emitted when a complete trading workflow finishes successfully.

    Used to signal successful completion of event-driven workflow.
    """

    # Override event_type with default
    event_type: str = Field(default="WorkflowCompleted", description=EVENT_TYPE_DESCRIPTION)

    # Workflow completion fields
    workflow_type: str = Field(..., description="Type of workflow completed")
    workflow_duration_ms: int = Field(..., description="Total workflow duration in milliseconds")
    success: bool = Field(..., description="Whether the workflow completed successfully")
    summary: dict[str, Any] = Field(default_factory=dict, description="Workflow execution summary")


class WorkflowFailed(BaseEvent):
    """Event emitted when a trading workflow fails.

    Used to signal workflow failure and trigger recovery processes.
    """

    # Override event_type with default
    event_type: str = Field(default="WorkflowFailed", description=EVENT_TYPE_DESCRIPTION)

    # Workflow failure fields
    workflow_type: str = Field(..., description="Type of workflow that failed")
    failure_reason: str = Field(..., description="Reason for workflow failure")
    failure_step: str = Field(..., description="Step where the workflow failed")
    error_details: dict[str, Any] = Field(
        default_factory=dict, description="Detailed error information"
    )
