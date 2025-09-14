#!/usr/bin/env python3
"""Business Unit: orchestration | Status: current.

Event-driven trading workflow handler.

This demonstrates the migration from direct orchestrator coupling to
event-driven coordination for complete trading workflows.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer

from the_alchemiser.shared.events import (
    BaseEvent,
    EventBus,
    PortfolioAnalysisCompleted,
    PortfolioAnalysisRequested,
    SignalGenerated,
    TradingWorkflowRequested,
)
from the_alchemiser.shared.logging.logging_utils import get_logger


class TradingWorkflowHandler:
    """Event-driven handler for complete trading workflows.

    This handler demonstrates the migration from TradingOrchestrator's direct
    orchestrator instantiation and method calls to event-driven coordination.

    Instead of:
        self.signal_orchestrator = SignalOrchestrator(...)
        self.portfolio_orchestrator = PortfolioOrchestrator(...)
        signals = self.signal_orchestrator.generate_signals()
        account_data = self.portfolio_orchestrator.get_comprehensive_account_data()

    We now use:
        emit TradingWorkflowRequested -> handle SignalGenerated -> emit PortfolioAnalysisRequested
    """

    def __init__(self, container: ApplicationContainer) -> None:
        """Initialize trading workflow handler.

        Args:
            container: Application container for dependency injection

        """
        self.container = container
        self.logger = get_logger(__name__)
        self.event_bus: EventBus = container.services.event_bus()

        # Track workflow state for coordination
        self.workflow_state: dict[str, dict[str, Any]] = {}

        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register event handlers for trading workflows."""
        self.event_bus.subscribe("TradingWorkflowRequested", self)
        self.event_bus.subscribe("SignalGenerated", self)
        self.event_bus.subscribe("PortfolioAnalysisCompleted", self)
        self.logger.info("Registered trading workflow event handlers")

    def handle_event(self, event: BaseEvent) -> None:
        """Handle trading workflow events.

        Args:
            event: The event to handle

        """
        try:
            if isinstance(event, TradingWorkflowRequested):
                self._handle_trading_workflow_requested(event)
            elif isinstance(event, SignalGenerated):
                self._handle_signal_generated_for_workflow(event)
            elif isinstance(event, PortfolioAnalysisCompleted):
                self._handle_portfolio_analysis_completed(event)
            else:
                self.logger.debug(f"Trading workflow handler ignoring event type: {event.event_type}")

        except Exception as e:
            self.logger.error(
                f"Trading workflow event handling failed for {event.event_type}: {e}",
                extra={
                    "event_id": event.event_id,
                    "correlation_id": event.correlation_id,
                },
            )

    def can_handle(self, event_type: str) -> bool:
        """Check if this handler can process the given event type.

        Args:
            event_type: The type of event

        Returns:
            True if this handler can process the event type

        """
        return event_type in [
            "TradingWorkflowRequested",
            "SignalGenerated",
            "PortfolioAnalysisCompleted",
        ]

    def _handle_trading_workflow_requested(self, event: TradingWorkflowRequested) -> None:
        """Handle request to start a complete trading workflow.

        This replaces the TradingOrchestrator's execute_trading_workflow method
        with event-driven coordination.

        Args:
            event: The trading workflow request event

        """
        workflow_id = str(uuid.uuid4())
        self.logger.info(
            f"🚀 Trading workflow requested: {event.workflow_mode}",
            extra={
                "correlation_id": event.correlation_id,
                "workflow_id": workflow_id,
                "workflow_mode": event.workflow_mode,
            },
        )

        # Initialize workflow state tracking
        self.workflow_state[workflow_id] = {
            "workflow_id": workflow_id,
            "correlation_id": event.correlation_id,
            "workflow_mode": event.workflow_mode,
            "ignore_market_hours": event.ignore_market_hours,
            "execution_parameters": event.execution_parameters or {},
            "start_time": datetime.now(UTC),
            "status": "started",
            "signals_received": False,
            "portfolio_analysis_completed": False,
            "execution_completed": False,
        }

        # In a traditional orchestrator, we would call:
        #   self.signal_orchestrator.generate_signals()
        # Instead, we rely on the SignalOrchestrator's existing dual-path emission
        # and wait for SignalGenerated events to continue the workflow

        self.logger.info(
            f"Trading workflow {workflow_id} initialized, waiting for signals",
            extra={"correlation_id": event.correlation_id, "workflow_id": workflow_id},
        )

    def _handle_signal_generated_for_workflow(self, event: SignalGenerated) -> None:
        """Handle signal generation in the context of a trading workflow.

        This replaces the direct signal processing in TradingOrchestrator.

        Args:
            event: The signal generated event

        """
        # Find any active workflows that should process this signal
        active_workflows = [
            wf for wf in self.workflow_state.values() if wf["status"] in ["started", "processing"]
        ]

        if not active_workflows:
            # No active trading workflows, this is probably from signal-only mode
            return

        for workflow in active_workflows:
            workflow_id = workflow["workflow_id"]
            self.logger.info(
                f"📊 Processing signals for trading workflow {workflow_id}",
                extra={
                    "correlation_id": event.correlation_id,
                    "workflow_id": workflow_id,
                    "signal_count": len(event.signals),
                },
            )

            # Update workflow state
            workflow["status"] = "processing"
            workflow["signals_received"] = True
            workflow["signal_event_id"] = event.event_id

            # Request portfolio analysis (replaces direct PortfolioOrchestrator calls)
            analysis_event = PortfolioAnalysisRequested(
                correlation_id=event.correlation_id,
                causation_id=event.event_id,
                event_id=f"portfolio-analysis-{workflow_id}",
                timestamp=datetime.now(UTC),
                source_module="orchestration",
                source_component="TradingWorkflowHandler",
                trigger_event_id=event.event_id,
                target_allocations=event.consolidated_portfolio,
                analysis_type="comprehensive",
            )

            self.event_bus.publish(analysis_event)

            self.logger.info(
                f"Requested portfolio analysis for workflow {workflow_id}",
                extra={
                    "correlation_id": event.correlation_id,
                    "workflow_id": workflow_id,
                    "analysis_event_id": analysis_event.event_id,
                },
            )

    def _handle_portfolio_analysis_completed(self, event: PortfolioAnalysisCompleted) -> None:
        """Handle completion of portfolio analysis in trading workflow.

        This replaces the direct portfolio analysis processing in TradingOrchestrator.

        Args:
            event: The portfolio analysis completed event

        """
        # Find the workflow this analysis belongs to
        target_workflow = None
        for workflow in self.workflow_state.values():
            if workflow["correlation_id"] == event.correlation_id:
                target_workflow = workflow
                break

        if not target_workflow:
            # This analysis is not part of an active trading workflow
            return

        workflow_id = target_workflow["workflow_id"]
        self.logger.info(
            f"🏦 Portfolio analysis completed for workflow {workflow_id}",
            extra={
                "correlation_id": event.correlation_id,
                "workflow_id": workflow_id,
                "analysis_timestamp": event.analysis_timestamp,
            },
        )

        # Update workflow state
        target_workflow["portfolio_analysis_completed"] = True
        target_workflow["portfolio_state"] = event.portfolio_state
        target_workflow["account_data"] = event.account_data
        target_workflow["allocation_comparison"] = event.allocation_comparison

        # Check if we're ready for execution (in full trading mode)
        if target_workflow["workflow_mode"] == "full_trading":
            self._initiate_trade_execution(target_workflow, event)
        else:
            # Signal-only mode - mark workflow complete
            self._complete_workflow(target_workflow, {"mode": "signal_only"})

    def _initiate_trade_execution(self, workflow: dict[str, Any], analysis_event: PortfolioAnalysisCompleted) -> None:
        """Initiate trade execution for a trading workflow.

        This would replace the trade execution logic in TradingOrchestrator.

        Args:
            workflow: The workflow state
            analysis_event: The portfolio analysis event that triggered execution

        """
        workflow_id = workflow["workflow_id"]
        self.logger.info(
            f"🔄 Initiating trade execution for workflow {workflow_id}",
            extra={
                "correlation_id": workflow["correlation_id"],
                "workflow_id": workflow_id,
            },
        )

        # In a full implementation, this would:
        # 1. Check market hours (if not ignored)
        # 2. Generate rebalancing plan
        # 3. Emit trade execution events
        # 4. Wait for TradeExecuted events
        # 5. Complete the workflow

        # For demonstration, mark as completed
        self._complete_workflow(workflow, {
            "mode": "full_trading",
            "message": "Trade execution would be initiated here"
        })

    def _complete_workflow(self, workflow: dict[str, Any], results: dict[str, Any]) -> None:
        """Complete a trading workflow.

        Args:
            workflow: The workflow state
            results: The workflow results

        """
        workflow_id = workflow["workflow_id"]
        workflow["status"] = "completed"
        workflow["end_time"] = datetime.now(UTC)
        workflow["results"] = results

        self.logger.info(
            f"✅ Trading workflow {workflow_id} completed",
            extra={
                "correlation_id": workflow["correlation_id"],
                "workflow_id": workflow_id,
                "duration": (workflow["end_time"] - workflow["start_time"]).total_seconds(),
            },
        )

        # In a full implementation, emit TradingWorkflowCompleted event here

    def get_workflow_status(self) -> dict[str, Any]:
        """Get current trading workflow status for monitoring.

        Returns:
            Dictionary containing workflow status information

        """
        active_workflows = [
            wf for wf in self.workflow_state.values() if wf["status"] in ["started", "processing"]
        ]

        completed_workflows = [
            wf for wf in self.workflow_state.values() if wf["status"] == "completed"
        ]

        return {
            "handler_active": True,
            "registered_events": [
                "TradingWorkflowRequested",
                "SignalGenerated",
                "PortfolioAnalysisCompleted",
            ],
            "active_workflows": len(active_workflows),
            "completed_workflows": len(completed_workflows),
            "total_workflows": len(self.workflow_state),
            "workflow_details": list(self.workflow_state.values()),
        }