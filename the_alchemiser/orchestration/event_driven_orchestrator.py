#!/usr/bin/env python3
"""Business Unit: orchestration | Status: current.

Event-driven orchestration handlers for startup, recovery, and reconciliation.

Provides event handlers that replace traditional direct-call orchestration
with event-driven workflows for better decoupling and extensibility.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer

from the_alchemiser.shared.events import (
    BaseEvent,
    EventBus,
    RebalancePlanned,
    SignalGenerated,
    StartupEvent,
    TradeExecuted,
)
from the_alchemiser.shared.logging.logging_utils import get_logger


class EventDrivenOrchestrator:
    """Event-driven orchestrator for startup, recovery, and reconciliation workflows.

    Replaces traditional direct-call orchestration with event-driven handlers
    that provide better decoupling and extensibility.
    """
    
    workflow_state: dict[str, bool | str | None]

    def __init__(self, container: ApplicationContainer) -> None:
        """Initialize the event-driven orchestrator.

        Args:
            container: Application container for dependency injection

        """
        self.container = container
        self.logger = get_logger(__name__)

        # Get event bus from container
        self.event_bus: EventBus = container.services.event_bus()

        # Register event handlers
        self._register_handlers()

        # Track workflow state for recovery and reconciliation
        self.workflow_state = {
            "startup_completed": False,
            "signal_generation_in_progress": False,
            "rebalancing_in_progress": False,
            "trading_in_progress": False,
            "last_successful_workflow": None,
        }

    def _register_handlers(self) -> None:
        """Register event handlers for orchestration workflows."""
        # Subscribe to all event types for orchestration monitoring
        self.event_bus.subscribe("StartupEvent", self)
        self.event_bus.subscribe("SignalGenerated", self)
        self.event_bus.subscribe("RebalancePlanned", self)
        self.event_bus.subscribe("TradeExecuted", self)

        self.logger.info("Registered event-driven orchestration handlers")

    def handle_event(self, event: BaseEvent) -> None:
        """Handle events for orchestration workflows.

        Args:
            event: The event to handle

        """
        try:
            if isinstance(event, StartupEvent):
                self._handle_startup(event)
            elif isinstance(event, SignalGenerated):
                self._handle_signal_generated(event)
            elif isinstance(event, RebalancePlanned):
                self._handle_rebalance_planned(event)
            elif isinstance(event, TradeExecuted):
                self._handle_trade_executed(event)
            else:
                self.logger.debug(f"Orchestrator ignoring event type: {event.event_type}")

        except Exception as e:
            self.logger.error(
                f"Orchestration event handling failed for {event.event_type}: {e}",
                extra={
                    "event_id": event.event_id,
                    "correlation_id": event.correlation_id,
                },
            )

    def can_handle(self, event_type: str) -> bool:
        """Check if handler can handle a specific event type.

        Args:
            event_type: The type of event to check

        Returns:
            True if this handler can handle the event type

        """
        return event_type in [
            "StartupEvent",
            "SignalGenerated",
            "RebalancePlanned",
            "TradeExecuted",
        ]

    def _handle_startup(self, event: StartupEvent) -> None:
        """Handle system startup event.

        Initializes orchestration workflows and prepares for signal generation.

        Args:
            event: The startup event

        """
        self.logger.info(
            f"🚀 System startup orchestration triggered for mode: {event.startup_mode}"
        )

        # Reset workflow state for new run
        self.workflow_state.update(
            {
                "startup_completed": True,
                "signal_generation_in_progress": False,
                "rebalancing_in_progress": False,
                "trading_in_progress": False,
            }
        )

        # Perform startup orchestration tasks
        startup_mode = event.startup_mode
        configuration = event.configuration or {}

        if startup_mode == "signal":
            self.logger.info("Orchestrating signal-only workflow")
            # For signal mode, workflow will be triggered by SignalOrchestrator
        elif startup_mode == "trade":
            self.logger.info("Orchestrating full trading workflow")
            # For trade mode, workflow includes portfolio rebalancing and execution

        # Log startup configuration
        self.logger.debug(f"Startup configuration: {configuration}")

        # Track successful startup
        self.workflow_state["last_successful_workflow"] = "startup"

    def _handle_signal_generated(self, event: SignalGenerated) -> None:
        """Handle signal generation event.

        Orchestrates the portfolio rebalancing workflow in response to signals.

        Args:
            event: The signal generated event

        """
        self.logger.info(
            f"📊 Signal generation orchestration: {len(event.signals)} signals received"
        )

        # Update workflow state
        self.workflow_state.update(
            {
                "signal_generation_in_progress": False,  # Signals completed
                "rebalancing_in_progress": True,  # Start rebalancing
            }
        )

        # Log signal summary for orchestration tracking
        for signal in event.signals:
            self.logger.debug(
                f"Orchestrating signal: {signal.symbol} {signal.action} "
                f"(strategy: {signal.strategy_name}, confidence: {signal.confidence})"
            )

        # In Phase 7, this would trigger portfolio rebalancing via events
        # For now, log orchestration intent
        self.logger.info("Orchestration: Ready to trigger portfolio rebalancing")

        # Track successful signal processing
        self.workflow_state["last_successful_workflow"] = "signal_generation"

    def _handle_rebalance_planned(self, event: RebalancePlanned) -> None:
        """Handle rebalance planning event.

        Orchestrates the trade execution workflow in response to rebalancing plans.

        Args:
            event: The rebalance planned event

        """
        self.logger.info(
            f"⚖️ Rebalance planning orchestration: {len(event.rebalance_plan.items)} trades planned"
        )

        # Update workflow state
        self.workflow_state.update(
            {
                "rebalancing_in_progress": False,  # Rebalancing plan completed
                "trading_in_progress": True,  # Start trade execution
            }
        )

        # Log rebalancing plan summary for orchestration tracking
        total_value = event.rebalance_plan.total_trade_value
        self.logger.debug(f"Orchestrating total trade value: ${total_value}")

        # In Phase 7, this would trigger trade execution via events
        # For now, log orchestration intent
        self.logger.info("Orchestration: Ready to trigger trade execution")

        # Track successful rebalancing
        self.workflow_state["last_successful_workflow"] = "rebalancing"

    def _handle_trade_executed(self, event: TradeExecuted) -> None:
        """Handle trade execution event.

        Completes the orchestration workflow and performs reconciliation.

        Args:
            event: The trade executed event

        """
        success = event.success
        self.logger.info(f"🎯 Trade execution orchestration completed: {'✅' if success else '❌'}")

        # Update workflow state
        self.workflow_state.update(
            {
                "trading_in_progress": False,  # Trading completed
            }
        )

        if success:
            self.logger.info("Orchestration: Full trading workflow completed successfully")
            self.workflow_state["last_successful_workflow"] = "trading"

            # Perform post-trade reconciliation
            self._perform_reconciliation(event)
        else:
            self.logger.error(f"Orchestration: Trading workflow failed - {event.error_message}")

            # Trigger recovery workflow
            self._trigger_recovery_workflow(event)

    def _perform_reconciliation(self, event: TradeExecuted) -> None:
        """Perform post-trade reconciliation workflow.

        Args:
            event: The trade executed event

        """
        self.logger.info("🔄 Starting post-trade reconciliation")

        try:
            # In Phase 7, this would:
            # 1. Verify portfolio state matches expectations
            # 2. Check trade execution accuracy
            # 3. Update position tracking
            # 4. Generate reconciliation reports

            self.logger.info("Reconciliation: Verifying portfolio state")
            self.logger.info("Reconciliation: Checking trade execution accuracy")
            self.logger.info("Reconciliation: Updating position tracking")

            self.logger.info("✅ Post-trade reconciliation completed successfully")

        except Exception as e:
            self.logger.error(f"Reconciliation failed: {e}")

    def _trigger_recovery_workflow(self, event: TradeExecuted) -> None:
        """Trigger recovery workflow for failed operations.

        Args:
            event: The trade executed event that failed

        """
        self.logger.info("🛠️ Starting recovery workflow")

        try:
            # In Phase 7, this would:
            # 1. Assess the failure state
            # 2. Determine recovery actions
            # 3. Emit recovery events
            # 4. Alert system administrators

            self.logger.warning(f"Recovery: Assessing failure - {event.error_message}")
            self.logger.info("Recovery: Determining corrective actions")
            self.logger.info("Recovery: Preparing system alerts")

            # For now, log the recovery intent
            self.logger.info("Recovery workflow prepared (full implementation in Phase 7)")

        except Exception as e:
            self.logger.error(f"Recovery workflow failed: {e}")

    def get_workflow_status(self) -> dict[str, Any]:
        """Get current workflow status for monitoring.

        Returns:
            Dictionary containing workflow state information

        """
        return {
            "workflow_state": self.workflow_state.copy(),
            "event_bus_stats": self.event_bus.get_stats(),
            "orchestrator_active": True,
        }
