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
from typing import Any, Literal

from pydantic import Field, field_validator

from ..constants import (
    CONTRACT_VERSION,
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
    __event_version__: str = CONTRACT_VERSION

    schema_version: str = Field(
        default=CONTRACT_VERSION, description=EVENT_SCHEMA_VERSION_DESCRIPTION
    )

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
    __event_version__: str = CONTRACT_VERSION

    schema_version: str = Field(
        default=CONTRACT_VERSION, description=EVENT_SCHEMA_VERSION_DESCRIPTION
    )

    # Signal-specific fields
    signals_data: dict[str, Any] = Field(..., description="Strategy signals data")
    consolidated_portfolio: dict[str, Any] = Field(
        ..., description="Consolidated portfolio allocation"
    )
    signal_count: int = Field(..., description="Number of signals generated")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional signal metadata")

    # Data freshness info aggregated from all strategy workers
    data_freshness: dict[str, Any] = Field(
        default_factory=dict,
        description="Data freshness info: latest_timestamp, age_days, gate_status",
    )


class PartialSignalGenerated(BaseEvent):
    """Event emitted when a single strategy file generates signals.

    Used in multi-node scaling mode where each DSL strategy file runs
    in its own Lambda invocation. The Aggregator Lambda collects all
    PartialSignalGenerated events and merges them into a single
    SignalGenerated event for Portfolio Lambda.

    Supports both success and failure cases:
    - success=True: Contains valid signals_data and consolidated_portfolio
    - success=False: Empty portfolio/signals, error_message populated

    This allows the aggregator to proceed with partial results when some
    strategies fail, rather than blocking the entire workflow.
    """

    # Override event_type with default
    event_type: str = Field(default="PartialSignalGenerated", description=EVENT_TYPE_DESCRIPTION)
    __event_version__: str = CONTRACT_VERSION

    schema_version: str = Field(
        default=CONTRACT_VERSION, description=EVENT_SCHEMA_VERSION_DESCRIPTION
    )

    # Session tracking fields (links partial signals for aggregation)
    session_id: str = Field(..., description="Aggregation session ID linking all partial signals")
    dsl_file: str = Field(..., description="DSL strategy file name (e.g., '1-KMLM.clj')")
    allocation: Decimal = Field(..., description="Weight allocation for this strategy file (0-1)")
    strategy_number: int = Field(..., description="Order index of this strategy (1-based)")
    total_strategies: int = Field(..., description="Total number of strategies in this session")

    # Success/failure tracking for partial failure resilience
    success: bool = Field(
        default=True,
        description="Whether this strategy evaluated successfully. False indicates failure.",
    )
    error_message: str | None = Field(
        default=None,
        description="Error message when success=False. None when successful.",
    )

    # Signal data (same structure as SignalGenerated but for single file)
    # Empty when success=False
    signals_data: dict[str, Any] = Field(
        default_factory=dict,
        description="Strategy signals from this single file (empty on failure)",
    )
    consolidated_portfolio: dict[str, Any] = Field(
        default_factory=dict,
        description="Partial portfolio allocation (scaled by file weight, empty on failure)",
    )
    signal_count: int = Field(
        default=0, description="Number of signals generated by this file (0 on failure)"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional signal metadata")

    # Data freshness info from market data validation
    data_freshness: dict[str, Any] = Field(
        default_factory=dict,
        description="Data freshness info: latest_timestamp, age_days, gate_status",
    )


class RebalancePlanned(BaseEvent):
    """Event emitted when portfolio rebalancing plan is created.

    Contains the rebalancing plan for execution consumption.
    """

    # Override event_type with default
    event_type: str = Field(default="RebalancePlanned", description=EVENT_TYPE_DESCRIPTION)
    __event_version__: str = CONTRACT_VERSION

    schema_version: str = Field(
        default=CONTRACT_VERSION, description=EVENT_SCHEMA_VERSION_DESCRIPTION
    )

    # Rebalance-specific fields
    rebalance_plan: RebalancePlan = Field(..., description="Portfolio rebalancing plan")
    allocation_comparison: AllocationComparison = Field(
        ..., description="Allocation comparison data"
    )
    trades_required: bool = Field(..., description="Whether trades are required")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional rebalance metadata"
    )

    # Data freshness info propagated from strategy phase
    data_freshness: dict[str, Any] = Field(
        default_factory=dict,
        description="Data freshness info: latest_timestamp, age_days, gate_status",
    )


class TradeExecuted(BaseEvent):
    """Event emitted when trades are executed.

    Contains the execution results and updated portfolio state.
    """

    # Override event_type with default
    event_type: str = Field(default="TradeExecuted", description=EVENT_TYPE_DESCRIPTION)
    __event_version__: str = CONTRACT_VERSION

    schema_version: str = Field(
        default=CONTRACT_VERSION, description=EVENT_SCHEMA_VERSION_DESCRIPTION
    )

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
    __event_version__: str = CONTRACT_VERSION

    schema_version: str = Field(
        default=CONTRACT_VERSION, description=EVENT_SCHEMA_VERSION_DESCRIPTION
    )

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
    __event_version__: str = CONTRACT_VERSION

    schema_version: str = Field(
        default=CONTRACT_VERSION, description=EVENT_SCHEMA_VERSION_DESCRIPTION
    )

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
    __event_version__: str = CONTRACT_VERSION

    schema_version: str = Field(
        default=CONTRACT_VERSION, description=EVENT_SCHEMA_VERSION_DESCRIPTION
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
    __event_version__: str = CONTRACT_VERSION

    schema_version: str = Field(
        default=CONTRACT_VERSION, description=EVENT_SCHEMA_VERSION_DESCRIPTION
    )

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
    __event_version__: str = CONTRACT_VERSION

    schema_version: str = Field(
        default=CONTRACT_VERSION, description=EVENT_SCHEMA_VERSION_DESCRIPTION
    )

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
    __event_version__: str = CONTRACT_VERSION

    schema_version: str = Field(
        default=CONTRACT_VERSION, description=EVENT_SCHEMA_VERSION_DESCRIPTION
    )

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
    __event_version__: str = CONTRACT_VERSION

    schema_version: str = Field(
        default=CONTRACT_VERSION, description=EVENT_SCHEMA_VERSION_DESCRIPTION
    )

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
    __event_version__: str = CONTRACT_VERSION

    schema_version: str = Field(
        default=CONTRACT_VERSION, description=EVENT_SCHEMA_VERSION_DESCRIPTION
    )

    # Workflow completion fields
    workflow_type: str = Field(..., description="Type of workflow completed")
    workflow_duration_ms: int = Field(..., description="Total workflow duration in milliseconds")
    success: bool = Field(..., description="Whether the workflow completed successfully")
    summary: dict[str, Any] = Field(default_factory=dict, description="Workflow execution summary")


class AllTradesCompleted(BaseEvent):
    """Event emitted when all trades in an execution run have completed.

    This event is emitted by TradeAggregator Lambda after receiving TradeExecuted
    events and detecting that all trades in a run have finished (success or failure).
    This eliminates the race condition in notifications by ensuring only one
    notification is triggered per run.

    The event contains pre-aggregated execution data so notifications don't need
    to query DynamoDB.
    """

    # Override event_type with default
    event_type: str = Field(default="AllTradesCompleted", description=EVENT_TYPE_DESCRIPTION)
    __event_version__: str = CONTRACT_VERSION

    schema_version: str = Field(
        default=CONTRACT_VERSION, description=EVENT_SCHEMA_VERSION_DESCRIPTION
    )

    # Run identification
    run_id: str = Field(..., description="Unique execution run identifier")
    plan_id: str = Field(..., description="Source RebalancePlan identifier")

    # Aggregated trade statistics
    total_trades: int = Field(..., description="Total number of trades in the run")
    succeeded_trades: int = Field(..., description="Number of trades that succeeded")
    failed_trades: int = Field(..., description="Number of trades that failed")
    skipped_trades: int = Field(..., description="Number of trades that were skipped")

    # Pre-aggregated execution data for notifications
    aggregated_execution_data: dict[str, Any] = Field(
        ..., description="Pre-aggregated trade results for notifications"
    )

    # Capital metrics (captured after all trades complete)
    capital_deployed_pct: Decimal | None = Field(
        default=None,
        description="Percentage of account equity deployed in positions (0-100)",
    )

    # Failed symbols for error reporting
    failed_symbols: list[str] = Field(
        default_factory=list, description="List of symbols that failed execution"
    )

    # Non-fractionable skips (expected, not failures)
    non_fractionable_skipped_symbols: list[str] = Field(
        default_factory=list,
        description="Symbols skipped because non-fractionable quantity rounded to zero",
    )

    # Timing fields for notifications
    started_at: str | None = Field(default=None, description="Run start time in ISO format (UTC)")
    completed_at: str | None = Field(
        default=None, description="Run completion time in ISO format (UTC)"
    )

    # Portfolio snapshot (always fetched from Alpaca after trades complete)
    portfolio_snapshot: dict[str, Any] = Field(
        default_factory=dict,
        description="Current portfolio state: equity, cash, positions, exposures",
    )

    # Data freshness info (propagated from strategy workers)
    data_freshness: dict[str, Any] = Field(
        default_factory=dict,
        description="Data freshness info: latest_timestamp, age_days, gate_status",
    )

    # P&L metrics (fetched from Alpaca after trades complete)
    pnl_metrics: dict[str, Any] = Field(
        default_factory=dict,
        description="P&L metrics: monthly_pnl and yearly_pnl with total_pnl, total_pnl_pct",
    )

    # Strategy evaluation metadata (for email notifications)
    strategies_evaluated: int = Field(
        default=0,
        description="Number of DSL strategy files evaluated in this run",
    )

    # Rebalance plan summary (for email notifications)
    rebalance_plan_summary: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Summary of rebalance plan items: symbol, action, weights, trade_amount",
    )

    @field_validator("capital_deployed_pct", mode="before")
    @classmethod
    def convert_capital_deployed_pct_to_decimal(cls, v: object) -> Decimal | None:
        """Convert capital_deployed_pct to Decimal if it's a float or int."""
        if v is None:
            return None
        if isinstance(v, Decimal):
            return v
        if isinstance(v, int | float):
            return Decimal(str(v))
        if isinstance(v, str):
            return Decimal(v)
        type_name = type(v).__name__
        raise TypeConversionError(
            f"Cannot convert {type_name} to Decimal",
            source_type=type_name,
            target_type="Decimal",
            value=str(v),
        )


class WorkflowFailed(BaseEvent):
    """Event emitted when a trading workflow fails.

    Used to signal workflow failure and trigger recovery processes.
    """

    # Override event_type with default
    event_type: str = Field(default="WorkflowFailed", description=EVENT_TYPE_DESCRIPTION)
    __event_version__: str = CONTRACT_VERSION

    schema_version: str = Field(
        default=CONTRACT_VERSION, description=EVENT_SCHEMA_VERSION_DESCRIPTION
    )

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
    __event_version__: str = CONTRACT_VERSION

    schema_version: str = Field(
        default=CONTRACT_VERSION, description=EVENT_SCHEMA_VERSION_DESCRIPTION
    )

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
    __event_version__: str = CONTRACT_VERSION

    schema_version: str = Field(
        default=CONTRACT_VERSION, description=EVENT_SCHEMA_VERSION_DESCRIPTION
    )

    # Trading notification fields
    trading_success: bool = Field(..., description="Whether trading was successful")
    trading_mode: str = Field(..., description="Trading mode (LIVE, PAPER)")
    orders_placed: int = Field(..., description="Number of orders placed")
    orders_succeeded: int = Field(..., description="Number of orders that succeeded")
    orders_skipped: int = Field(default=0, description="Number of orders skipped")
    capital_deployed_pct: Decimal | None = Field(
        default=None,
        description="Percentage of account equity deployed in positions (0-100)",
    )
    execution_data: dict[str, Any] = Field(..., description="Detailed execution data")
    error_message: str | None = Field(default=None, description="Error message if trading failed")
    error_code: str | None = Field(default=None, description="Optional error code")
    recipient_override: str | None = Field(default=None, description=RECIPIENT_OVERRIDE_DESCRIPTION)

    @field_validator("capital_deployed_pct", mode="before")
    @classmethod
    def convert_capital_deployed_pct_to_decimal(cls, v: object) -> Decimal | None:
        """Convert capital_deployed_pct to Decimal if it's a float or int."""
        if v is None:
            return None
        if isinstance(v, Decimal):
            return v
        if isinstance(v, int | float):
            return Decimal(str(v))
        if isinstance(v, str):
            return Decimal(v)
        type_name = type(v).__name__
        raise TypeConversionError(
            f"Cannot convert {type_name} to Decimal",
            source_type=type_name,
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
    __event_version__: str = CONTRACT_VERSION

    schema_version: str = Field(
        default=CONTRACT_VERSION, description=EVENT_SCHEMA_VERSION_DESCRIPTION
    )

    # System notification fields
    notification_type: str = Field(..., description="Type of notification (INFO, WARNING, ALERT)")
    subject: str = Field(..., description="Email subject line")
    html_content: str = Field(..., description="HTML email content")
    text_content: str | None = Field(default=None, description="Optional plain text content")
    recipient_override: str | None = Field(default=None, description=RECIPIENT_OVERRIDE_DESCRIPTION)


class DataLakeNotificationRequested(BaseEvent):
    """Event emitted when a data lake update notification should be sent.

    Contains data lake refresh results and metrics for email notifications.
    Supports SUCCESS, SUCCESS_WITH_WARNINGS, and FAILURE statuses.
    """

    event_type: str = Field(
        default="DataLakeNotificationRequested", description=EVENT_TYPE_DESCRIPTION
    )
    __event_version__: str = CONTRACT_VERSION

    schema_version: str = Field(
        default=CONTRACT_VERSION, description=EVENT_SCHEMA_VERSION_DESCRIPTION
    )

    # Data lake notification fields
    status: str = Field(..., description="Update status (SUCCESS, SUCCESS_WITH_WARNINGS, FAILURE)")
    data_lake_context: dict[str, Any] = Field(
        ..., description="Data lake update context for templates"
    )
    recipient_override: str | None = Field(default=None, description=RECIPIENT_OVERRIDE_DESCRIPTION)


class ScheduleNotificationRequested(BaseEvent):
    """Event emitted when a schedule notification should be sent.

    Contains schedule creation details for email notifications.
    Supports 'scheduled', 'early_close', and 'skipped_holiday' statuses.
    """

    event_type: str = Field(
        default="ScheduleNotificationRequested", description=EVENT_TYPE_DESCRIPTION
    )
    __event_version__: str = CONTRACT_VERSION

    schema_version: str = Field(
        default=CONTRACT_VERSION, description=EVENT_SCHEMA_VERSION_DESCRIPTION
    )

    # Schedule notification fields
    schedule_context: dict[str, Any] = Field(
        ..., description="Schedule context for templates (status, date, times, etc.)"
    )
    recipient_override: str | None = Field(default=None, description=RECIPIENT_OVERRIDE_DESCRIPTION)


# Schedule Events (for schedule creation notifications)


class ScheduleCreated(BaseEvent):
    """Event emitted when the Schedule Manager creates a trading schedule.

    Sent on successful schedule creation, early close days, or when
    market is closed (holidays only, not weekends).
    """

    # Override event_type with default
    event_type: str = Field(default="ScheduleCreated", description=EVENT_TYPE_DESCRIPTION)
    __event_version__: str = CONTRACT_VERSION

    schema_version: str = Field(
        default=CONTRACT_VERSION, description=EVENT_SCHEMA_VERSION_DESCRIPTION
    )

    # Schedule outcome
    status: str = Field(
        ...,
        description="Schedule status: 'scheduled', 'skipped_holiday', 'early_close'",
    )
    date: str = Field(..., description="Trading date (ISO format YYYY-MM-DD)")

    # Schedule details (populated when status='scheduled' or 'early_close')
    execution_time: str | None = Field(
        default=None, description="Scheduled execution time (ISO format)"
    )
    market_close_time: str | None = Field(
        default=None, description="Market close time for the day (ISO format)"
    )
    is_early_close: bool = Field(default=False, description="Whether this is an early close day")
    schedule_name: str | None = Field(
        default=None, description="Name of the created EventBridge schedule"
    )

    # Skip reason (populated when status='skipped_holiday')
    skip_reason: str | None = Field(
        default=None, description="Reason for skipping (holiday name, etc.)"
    )


# Market Data Events (for shared data infrastructure)


class MarketDataFetchRequested(BaseEvent):
    """Event emitted when a strategy lambda detects missing market data.

    Published to the shared data event bus to request the Data Lambda to fetch
    the missing data. Multiple stages may publish this event simultaneously for
    the same symbol; the Data Lambda deduplicates using DynamoDB conditional writes.

    The requesting stage does NOT wait for the fetch to complete - it should
    handle the missing data gracefully (e.g., skip the symbol or use fallback).
    """

    # Override event_type with default
    event_type: str = Field(default="MarketDataFetchRequested", description=EVENT_TYPE_DESCRIPTION)
    __event_version__: str = CONTRACT_VERSION

    schema_version: str = Field(
        default=CONTRACT_VERSION, description=EVENT_SCHEMA_VERSION_DESCRIPTION
    )

    # Request fields
    symbol: str = Field(..., description="Ticker symbol that needs data")
    requesting_stage: str = Field(
        ..., description="Stage that detected missing data (dev/staging/prod)"
    )
    requesting_component: str = Field(..., description="Component that detected missing data")
    lookback_days: int = Field(
        default=400, description="Days of historical data to fetch if seeding"
    )
    reason: str = Field(
        default="missing_data",
        description="Reason for fetch request (missing_data, stale_data, etc.)",
    )


class MarketDataFetchCompleted(BaseEvent):
    """Event emitted when the Data Lambda completes a fetch request.

    Published after successfully fetching and storing market data.
    Consuming stages can subscribe to this for cache invalidation or retries.
    """

    # Override event_type with default
    event_type: str = Field(default="MarketDataFetchCompleted", description=EVENT_TYPE_DESCRIPTION)
    __event_version__: str = CONTRACT_VERSION

    schema_version: str = Field(
        default=CONTRACT_VERSION, description=EVENT_SCHEMA_VERSION_DESCRIPTION
    )

    # Completion fields
    symbol: str = Field(..., description="Ticker symbol that was fetched")
    success: bool = Field(..., description="Whether the fetch was successful")
    bars_fetched: int = Field(default=0, description="Number of bars fetched and stored")
    error_message: str | None = Field(default=None, description="Error message if fetch failed")
    was_deduplicated: bool = Field(
        default=False, description="True if request was skipped due to recent fetch"
    )


class DataLakeUpdateCompleted(BaseEvent):
    """Event emitted when scheduled data lake refresh completes.

    Published by DataFunction after processing all configured symbols in the daily
    refresh job. Contains detailed metrics for notification emails.

    This is distinct from MarketDataFetchCompleted which tracks individual
    on-demand symbol fetches.
    """

    event_type: str = Field(default="DataLakeUpdateCompleted", description=EVENT_TYPE_DESCRIPTION)
    __event_version__: str = CONTRACT_VERSION

    schema_version: str = Field(
        default=CONTRACT_VERSION, description=EVENT_SCHEMA_VERSION_DESCRIPTION
    )

    # Outcome fields
    success: bool = Field(..., description="Overall success (true if all symbols succeeded)")
    status_code: int = Field(..., description="Lambda status code (200/206/500)")

    # Symbol metrics
    total_symbols: int = Field(..., description="Total symbols processed")
    symbols_updated: list[str] = Field(
        default_factory=list, description="Successfully updated symbols"
    )
    failed_symbols: list[str] = Field(
        default_factory=list, description="Symbols that failed to update"
    )
    symbols_updated_count: int = Field(..., description="Count of successful updates")
    symbols_failed_count: int = Field(..., description="Count of failed updates")

    # Data metrics
    total_bars_fetched: int = Field(default=0, description="Total bars fetched across all symbols")
    bar_dates: list[str] = Field(
        default_factory=list,
        description="List of unique dates (YYYY-MM-DD) for which bars were fetched"
    )
    data_source: str = Field(default="alpaca_api", description="Data source (alpaca_api, etc)")

    # Adjustment tracking (NEW)
    symbols_adjusted: list[str] = Field(
        default_factory=list,
        description="Symbols with retroactive price adjustments detected (splits, dividends)",
    )
    adjustment_count: int = Field(
        default=0, description="Total number of bars adjusted across all symbols"
    )
    adjusted_dates_by_symbol: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Map of symbol to list of dates (YYYY-MM-DD) where adjustments were detected",
    )

    # Timing metrics
    start_time_utc: str = Field(..., description="Refresh start time (ISO format)")
    end_time_utc: str = Field(..., description="Refresh end time (ISO format)")
    duration_seconds: float = Field(..., description="Total duration in seconds")

    # Error details (populated on partial/full failure)
    error_message: str | None = Field(default=None, description="Error message if failed")
    error_details: dict[str, Any] = Field(
        default_factory=dict, description="Detailed error information per symbol"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Options Hedging Events
# ═══════════════════════════════════════════════════════════════════════════════


class HedgeEvaluationRequested(BaseEvent):
    """Event emitted when hedge evaluation is needed after rebalance.

    Triggered by RebalancePlanned event to evaluate current portfolio exposure
    and determine appropriate hedge sizing.
    """

    event_type: str = Field(default="HedgeEvaluationRequested", description=EVENT_TYPE_DESCRIPTION)
    __event_version__: str = CONTRACT_VERSION

    schema_version: str = Field(
        default=CONTRACT_VERSION, description=EVENT_SCHEMA_VERSION_DESCRIPTION
    )

    # Source rebalance plan context
    plan_id: str = Field(..., description="Source RebalancePlan ID")
    portfolio_nav: Decimal = Field(..., description="Total portfolio NAV (net asset value)")

    # Exposure by sector ETF (calculated from positions)
    sector_exposures: dict[str, str] = Field(
        ...,
        description="Beta-dollar exposure per sector ETF (symbol -> exposure as string)",
    )
    net_exposure_ratio: Decimal = Field(
        ...,
        description="Net portfolio exposure ratio (e.g., 2.0 = 2.0x leverage)",
    )

    # Current VIX for adaptive budgeting
    current_vix: Decimal | None = Field(
        default=None, description="Current VIX index value for budget calculation"
    )

    # Existing hedge positions (for roll evaluation)
    existing_hedge_count: int = Field(default=0, description="Number of existing hedge positions")


class HedgeEvaluationCompleted(BaseEvent):
    """Event emitted when hedge evaluation completes with recommendations.

    Contains the hedge sizing recommendations for execution.
    """

    event_type: str = Field(default="HedgeEvaluationCompleted", description=EVENT_TYPE_DESCRIPTION)
    __event_version__: str = CONTRACT_VERSION

    schema_version: str = Field(
        default=CONTRACT_VERSION, description=EVENT_SCHEMA_VERSION_DESCRIPTION
    )

    # Source context
    plan_id: str = Field(..., description="Source RebalancePlan ID")
    portfolio_nav: Decimal = Field(..., description="Portfolio NAV at evaluation")

    # Hedge recommendations
    recommendations: list[dict[str, Any]] = Field(
        ...,
        description="List of hedge recommendations (underlying, delta, contracts, etc.)",
    )
    total_premium_budget: Decimal = Field(
        ..., description="Total premium budget for this hedging cycle"
    )
    budget_nav_pct: Decimal = Field(
        ..., description="Budget as percentage of NAV (e.g., 0.008 = 0.8%)"
    )

    # Evaluation metadata
    vix_tier: str = Field(default="mid", description="VIX tier used for budget (low/mid/high)")
    current_vix: Decimal | None = Field(
        default=None, description="Current VIX level for dynamic selection"
    )
    exposure_multiplier: Decimal = Field(
        default=Decimal("1.0"), description="Exposure-based budget multiplier"
    )

    # Template selection metadata (new)
    template_selected: Literal["tail_first", "smoothing"] | None = Field(
        default=None, description="Template selected (tail_first, smoothing)"
    )
    template_regime: (
        Literal["low_iv_normal_skew", "mid_iv_moderate_skew", "high_iv_rich_skew"] | None
    ) = Field(default=None, description="Regime classification for template selection")
    template_selection_reason: str | None = Field(
        default=None, description="Human-readable reason for template selection"
    )

    # Skip reason (if no hedges needed)
    skip_reason: str | None = Field(
        default=None,
        description="Reason if hedging was skipped (e.g., existing hedges sufficient)",
    )


class HedgeOrderRequested(BaseEvent):
    """Event emitted for individual hedge option order.

    Represents a single hedge order to be executed.
    """

    event_type: str = Field(default="HedgeOrderRequested", description=EVENT_TYPE_DESCRIPTION)
    __event_version__: str = CONTRACT_VERSION

    schema_version: str = Field(
        default=CONTRACT_VERSION, description=EVENT_SCHEMA_VERSION_DESCRIPTION
    )

    # Hedge identification
    hedge_id: str = Field(..., description="Unique hedge identifier")
    plan_id: str = Field(..., description="Source RebalancePlan ID")

    # Option contract details
    underlying_symbol: str = Field(..., description="Underlying ETF (SPY, QQQ, etc.)")
    option_symbol: str = Field(..., description="OCC option symbol")
    option_type: str = Field(..., description="PUT or CALL")
    strike_price: Decimal = Field(..., description="Strike price")
    expiration_date: str = Field(..., description="Expiration date (YYYY-MM-DD)")

    # Order details
    quantity: int = Field(..., description="Number of contracts")
    action: str = Field(..., description="BUY or SELL")
    order_type: str = Field(default="LIMIT", description="MARKET or LIMIT")
    limit_price: Decimal | None = Field(default=None, description="Limit price if applicable")

    # Hedge metadata
    target_delta: Decimal | None = Field(default=None, description="Target delta for this hedge")
    hedge_template: str = Field(default="tail_first", description="Hedge template used")


class HedgeExecuted(BaseEvent):
    """Event emitted when hedge option order is executed.

    Contains the execution result for a single hedge order.
    """

    event_type: str = Field(default="HedgeExecuted", description=EVENT_TYPE_DESCRIPTION)
    __event_version__: str = CONTRACT_VERSION

    schema_version: str = Field(
        default=CONTRACT_VERSION, description=EVENT_SCHEMA_VERSION_DESCRIPTION
    )

    # Hedge identification
    hedge_id: str = Field(..., description="Unique hedge identifier")
    plan_id: str = Field(..., description="Source RebalancePlan ID")
    order_id: str = Field(..., description="Alpaca order ID")

    # Contract details
    option_symbol: str = Field(..., description="OCC option symbol")
    underlying_symbol: str = Field(..., description="Underlying ETF")

    # Execution results
    quantity: int = Field(..., description="Contracts executed")
    filled_price: Decimal = Field(..., description="Average fill price per contract")
    total_premium: Decimal = Field(..., description="Total premium paid/received")
    nav_percentage: Decimal = Field(..., description="Premium as percentage of portfolio NAV")

    # Status
    success: bool = Field(..., description="Whether execution succeeded")
    error_message: str | None = Field(default=None, description="Error message if failed")


class AllHedgesCompleted(BaseEvent):
    """Event emitted when all hedge orders in a cycle have completed.

    Aggregates results from multiple HedgeExecuted events for notifications.
    """

    event_type: str = Field(default="AllHedgesCompleted", description=EVENT_TYPE_DESCRIPTION)
    __event_version__: str = CONTRACT_VERSION

    schema_version: str = Field(
        default=CONTRACT_VERSION, description=EVENT_SCHEMA_VERSION_DESCRIPTION
    )

    # Identification
    plan_id: str = Field(..., description="Source RebalancePlan ID")

    # Aggregated results
    total_hedges: int = Field(..., description="Total number of hedge orders")
    succeeded_hedges: int = Field(..., description="Number that succeeded")
    failed_hedges: int = Field(..., description="Number that failed")

    # Cost summary
    total_premium_spent: Decimal = Field(..., description="Total premium spent")
    total_nav_pct: Decimal = Field(..., description="Total premium as percentage of NAV")

    # Position summary
    hedge_positions: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Summary of new hedge positions created",
    )

    # Failed symbols for error reporting
    failed_symbols: list[str] = Field(
        default_factory=list, description="Underlying symbols that failed"
    )

    # Skip indicator
    was_skipped: bool = Field(
        default=False,
        description="True if hedge evaluation was skipped (no recommendations)",
    )


class HedgeRollTriggered(BaseEvent):
    """Event emitted when a hedge position needs to be rolled.

    Triggered by the roll manager when DTE falls below threshold.
    """

    event_type: str = Field(default="HedgeRollTriggered", description=EVENT_TYPE_DESCRIPTION)
    __event_version__: str = CONTRACT_VERSION

    schema_version: str = Field(
        default=CONTRACT_VERSION, description=EVENT_SCHEMA_VERSION_DESCRIPTION
    )

    # Existing position to roll
    hedge_id: str = Field(..., description="Hedge position ID to roll")
    option_symbol: str = Field(..., description="Current option symbol")
    underlying_symbol: str = Field(..., description="Underlying ETF")
    current_dte: int = Field(..., description="Current days to expiry")
    current_contracts: int = Field(..., description="Number of contracts to roll")

    # Roll reason
    roll_reason: str = Field(
        ..., description="Reason for roll (dte_threshold, profit_taking, etc.)"
    )
