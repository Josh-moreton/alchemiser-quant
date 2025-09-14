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

from ..dto.portfolio_state_dto import PortfolioStateDTO
from ..dto.rebalance_plan_dto import RebalancePlanDTO
from ..dto.signal_dto import StrategySignalDTO
from .base import BaseEvent


class StartupEvent(BaseEvent):
    """Event emitted when the system starts up.

    Triggers the beginning of workflow processes.
    """

    # Override event_type with default
    event_type: str = Field(default="StartupEvent", description="Type of event")

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
    event_type: str = Field(default="SignalGenerated", description="Type of event")

    # Signal-specific fields
    signals: list[StrategySignalDTO] = Field(..., description="List of generated strategy signals")
    strategy_allocations: dict[str, Decimal] = Field(
        default_factory=dict, description="Strategy allocation weights"
    )
    consolidated_portfolio: dict[str, Decimal] = Field(
        default_factory=dict, description="Consolidated portfolio allocation"
    )


class RebalancePlanned(BaseEvent):
    """Event emitted when portfolio rebalancing plan is created.

    Contains the rebalancing plan for execution consumption.
    """

    # Override event_type with default
    event_type: str = Field(default="RebalancePlanned", description="Type of event")

    # Rebalance-specific fields
    rebalance_plan: RebalancePlanDTO = Field(..., description="Portfolio rebalancing plan")
    portfolio_state: PortfolioStateDTO = Field(..., description="Current portfolio state")


class TradeExecuted(BaseEvent):
    """Event emitted when trades are executed.

    Contains the execution results and updated portfolio state.
    """

    # Override event_type with default
    event_type: str = Field(default="TradeExecuted", description="Type of event")

    # Trade execution fields
    execution_results: dict[str, Any] = Field(..., description="Trade execution results")
    portfolio_state_after: PortfolioStateDTO | None = Field(
        default=None, description="Portfolio state after execution"
    )
    success: bool = Field(..., description="Whether execution was successful")
    error_message: str | None = Field(default=None, description="Error message if execution failed")


class TradingWorkflowRequested(BaseEvent):
    """Event emitted to request a complete trading workflow execution.

    This replaces direct orchestrator instantiation and method calls.
    """

    # Override event_type with default
    event_type: str = Field(default="TradingWorkflowRequested", description="Type of event")

    # Trading workflow specific fields
    workflow_mode: str = Field(..., description="Workflow mode: 'signal_only' or 'full_trading'")
    ignore_market_hours: bool = Field(default=False, description="Whether to ignore market hours")
    execution_parameters: dict[str, Any] | None = Field(
        default=None, description="Additional execution parameters"
    )


class PortfolioAnalysisRequested(BaseEvent):
    """Event emitted to request portfolio analysis.

    Replaces direct PortfolioOrchestrator method calls.
    """

    # Override event_type with default
    event_type: str = Field(default="PortfolioAnalysisRequested", description="Type of event")

    # Portfolio analysis specific fields
    trigger_event_id: str = Field(..., description="ID of event that triggered this analysis")
    target_allocations: dict[str, Decimal] | None = Field(
        default=None, description="Target allocation percentages"
    )
    analysis_type: str = Field(
        default="comprehensive", description="Type of analysis: 'state', 'comparison', 'comprehensive'"
    )


class PortfolioAnalysisCompleted(BaseEvent):
    """Event emitted when portfolio analysis is completed.

    Contains portfolio analysis results for consumption by other handlers.
    """

    # Override event_type with default
    event_type: str = Field(default="PortfolioAnalysisCompleted", description="Type of event")

    # Portfolio analysis results
    portfolio_state: dict[str, Any] = Field(..., description="Current portfolio state")
    account_data: dict[str, Any] = Field(..., description="Comprehensive account data")
    allocation_comparison: dict[str, Any] | None = Field(
        default=None, description="Target vs current allocation comparison"
    )
    analysis_timestamp: str = Field(..., description="ISO timestamp of analysis completion")
