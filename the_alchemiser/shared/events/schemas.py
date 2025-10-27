#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Event schemas for event-driven architecture.

Provides specific event classes for the system workflow:
- StartupEvent: System initialization event
- SignalGenerated: Strategy signal generation event
- RebalancePlanned: Portfolio rebalancing plan event
- TradeExecuted: Trade execution completion event
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import Field, field_validator

from ..constants import (
    EVENT_SCHEMA_VERSION_DESCRIPTION,
    EVENT_TYPE_DESCRIPTION,
    RECIPIENT_OVERRIDE_DESCRIPTION,
)
from ..errors import TypeConversionError
from ..schemas.common import AllocationComparison
from ..schemas.portfolio_state import PortfolioState
from ..schemas.rebalance_plan import RebalancePlan
from .base import BaseEvent


class StartupEvent(BaseEvent):
    """Event emitted when the system starts up.

    Triggers the beginning of workflow processes.
    """

    # Override event_type with default
    event_type: str = Field(default="StartupEvent", description=EVENT_TYPE_DESCRIPTION)
    schema_version: str = Field(default="1.0", description=EVENT_SCHEMA_VERSION_DESCRIPTION)

    # Startup-specific fields
    startup_mode: str = Field(..., description="Startup mode (signal, trade, etc.)")
    configuration: dict[str, Any] | None = Field(
        default=None, description="Startup configuration parameters"
    )


class SignalGenerated(BaseEvent):
    """Event emitted when strategy signals are generated.

    Contains the strategy signal data for portfolio consumption.
    """

    # Override event_type with default
    event_type: str = Field(default="SignalGenerated", description=EVENT_TYPE_DESCRIPTION)
    schema_version: str = Field(default="1.0", description=EVENT_SCHEMA_VERSION_DESCRIPTION)

    # Signal-specific fields
    signals_data: dict[str, Any] = Field(..., description="Strategy signals data")
    consolidated_portfolio: dict[str, Any] = Field(
        ..., description="Consolidated portfolio allocation"
    )
    signal_count: int = Field(..., description="Number of signals generated")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional signal metadata")


class RebalancePlanned(BaseEvent):
    """Event emitted when portfolio rebalancing plan is created.

    Contains the rebalancing plan for execution consumption.
    """

    # Override event_type with default
    event_type: str = Field(default="RebalancePlanned", description=EVENT_TYPE_DESCRIPTION)
    schema_version: str = Field(default="1.0", description=EVENT_SCHEMA_VERSION_DESCRIPTION)

    # Rebalance-specific fields
    rebalance_plan: RebalancePlan = Field(..., description="Portfolio rebalancing plan")
    allocation_comparison: AllocationComparison = Field(
        ..., description="Allocation comparison data"
    )
    trades_required: bool = Field(..., description="Whether trades are required")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional rebalance metadata"
    )


class TradeExecuted(BaseEvent):
    """Event emitted when trades are executed.

    Contains the execution results and updated portfolio state.
    """

    # Override event_type with default
    event_type: str = Field(default="TradeExecuted", description=EVENT_TYPE_DESCRIPTION)
    schema_version: str = Field(default="1.0", description=EVENT_SCHEMA_VERSION_DESCRIPTION)

    # Trade execution fields
    execution_data: dict[str, Any] = Field(..., description="Trade execution data")
    success: bool = Field(..., description="Whether execution was successful")
    orders_placed: int = Field(..., description="Number of orders placed")
    orders_succeeded: int = Field(..., description="Number of orders that succeeded")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional execution metadata"
    )
    # Failure details (populated when success=False)
    failure_reason: str | None = Field(
        default=None, description="Detailed failure reason when execution fails"
    )
    failed_symbols: list[str] = Field(
        default_factory=list, description="List of symbols that failed execution"
    )


class TradeExecutionStarted(BaseEvent):
    """Event emitted when trade execution begins.

    Contains the trading plan and execution parameters.
    """

    # Override event_type with default
    event_type: str = Field(default="TradeExecutionStarted", description=EVENT_TYPE_DESCRIPTION)
    schema_version: str = Field(default="1.0", description=EVENT_SCHEMA_VERSION_DESCRIPTION)

    # Execution startup fields
    execution_plan: dict[str, Any] = Field(..., description="Trading execution plan")
    portfolio_state_before: PortfolioState | None = Field(
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
    schema_version: str = Field(default="1.0", description=EVENT_SCHEMA_VERSION_DESCRIPTION)

    # Portfolio state change fields
    portfolio_state_before: PortfolioState = Field(..., description="Portfolio state before change")
    portfolio_state_after: PortfolioState = Field(..., description="Portfolio state after change")
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
    schema_version: str = Field(default="1.0", description=EVENT_SCHEMA_VERSION_DESCRIPTION)

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
    schema_version: str = Field(default="1.0", description=EVENT_SCHEMA_VERSION_DESCRIPTION)

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
    schema_version: str = Field(default="1.0", description=EVENT_SCHEMA_VERSION_DESCRIPTION)

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
    schema_version: str = Field(default="1.0", description=EVENT_SCHEMA_VERSION_DESCRIPTION)

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
    schema_version: str = Field(default="1.0", description=EVENT_SCHEMA_VERSION_DESCRIPTION)

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
    schema_version: str = Field(default="1.0", description=EVENT_SCHEMA_VERSION_DESCRIPTION)

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
    schema_version: str = Field(default="1.0", description=EVENT_SCHEMA_VERSION_DESCRIPTION)

    # Workflow failure fields
    workflow_type: str = Field(..., description="Type of workflow that failed")
    failure_reason: str = Field(..., description="Reason for workflow failure")
    failure_step: str = Field(..., description="Step where the workflow failed")
    error_details: dict[str, Any] = Field(
        default_factory=dict, description="Detailed error information"
    )


# Notification Events (for event-driven email notifications)


class ErrorNotificationRequested(BaseEvent):
    """Event emitted when an error notification email should be sent.

    Contains error details and notification preferences.
    """

    # Override event_type with default
    event_type: str = Field(
        default="ErrorNotificationRequested", description=EVENT_TYPE_DESCRIPTION
    )
    schema_version: str = Field(default="1.0", description=EVENT_SCHEMA_VERSION_DESCRIPTION)

    # Error notification fields
    error_severity: str = Field(..., description="Error severity level (CRITICAL, HIGH, MEDIUM)")
    error_priority: str = Field(..., description="Error priority (URGENT, HIGH, MEDIUM)")
    error_title: str = Field(..., description="Error title for subject line")
    error_report: str = Field(..., description="Detailed error report content")
    error_code: str | None = Field(
        default=None, description="Optional error code for categorization"
    )
    recipient_override: str | None = Field(default=None, description=RECIPIENT_OVERRIDE_DESCRIPTION)


class TradingNotificationRequested(BaseEvent):
    """Event emitted when a trading completion notification should be sent.

    Contains trading execution results and notification details.
    """

    # Override event_type with default
    event_type: str = Field(
        default="TradingNotificationRequested", description=EVENT_TYPE_DESCRIPTION
    )
    schema_version: str = Field(default="1.0", description=EVENT_SCHEMA_VERSION_DESCRIPTION)

    # Trading notification fields
    trading_success: bool = Field(..., description="Whether trading was successful")
    trading_mode: str = Field(..., description="Trading mode (LIVE, PAPER)")
    orders_placed: int = Field(..., description="Number of orders placed")
    orders_succeeded: int = Field(..., description="Number of orders that succeeded")
    total_trade_value: Decimal = Field(..., description="Total value of trades executed")
    execution_data: dict[str, Any] = Field(..., description="Detailed execution data")
    error_message: str | None = Field(default=None, description="Error message if trading failed")
    error_code: str | None = Field(default=None, description="Optional error code")
    recipient_override: str | None = Field(default=None, description=RECIPIENT_OVERRIDE_DESCRIPTION)

    @field_validator("total_trade_value", mode="before")
    @classmethod
    def convert_total_trade_value_to_decimal(cls, v: object) -> Decimal:
        """Convert total_trade_value to Decimal if it's a float or int."""
        if isinstance(v, Decimal):
            return v
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        if isinstance(v, str):
            return Decimal(v)
        raise TypeConversionError(
            f"Cannot convert {type(v).__name__} to Decimal",
            source_type=type(v).__name__,
            target_type="Decimal",
            value=str(v),
        )


class SystemNotificationRequested(BaseEvent):
    """Event emitted when a general system notification should be sent.

    Contains system status or general notification details.
    """

    # Override event_type with default
    event_type: str = Field(
        default="SystemNotificationRequested", description=EVENT_TYPE_DESCRIPTION
    )
    schema_version: str = Field(default="1.0", description=EVENT_SCHEMA_VERSION_DESCRIPTION)

    # System notification fields
    notification_type: str = Field(..., description="Type of notification (INFO, WARNING, ALERT)")
    subject: str = Field(..., description="Email subject line")
    html_content: str = Field(..., description="HTML email content")
    text_content: str | None = Field(default=None, description="Optional plain text content")
    recipient_override: str | None = Field(default=None, description=RECIPIENT_OVERRIDE_DESCRIPTION)
