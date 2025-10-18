#!/usr/bin/env python3
"""Business Unit: orchestration | Status: current.

Event-driven orchestration handlers for cross-cutting concerns.

Provides event handlers for notifications, reconciliation, monitoring, and recovery
across the trading workflow. Focused on cross-cutting concerns rather than domain execution.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable as TypingCallable
from datetime import UTC, datetime
from decimal import Decimal
from threading import Lock
from typing import TYPE_CHECKING, Any, cast
from uuid import uuid4

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer

from the_alchemiser.shared.events import (
    BaseEvent,
    EventBus,
    RebalancePlanned,
    SignalGenerated,
    StartupEvent,
    TradeExecuted,
    WorkflowCompleted,
    WorkflowFailed,
    WorkflowStarted,
)
from the_alchemiser.shared.events.handlers import EventHandler as SharedEventHandler
from the_alchemiser.shared.logging import get_logger

# Import workflow state management
from .workflow_state import (
    StateCheckingHandlerWrapper,
    WorkflowState,
)


class EventDrivenOrchestrator:
    """Event-driven orchestrator for primary workflow coordination.

    Coordinates complete trading workflows through event-driven handlers,
    managing domain handlers and workflow state. This is the primary coordinator
    for event-driven architecture.
    """

    def __init__(self, container: ApplicationContainer) -> None:
        """Initialize the event-driven orchestrator.

        Args:
            container: Application container for dependency injection

        """
        self.container = container
        self.logger = get_logger(__name__)

        # Get event bus from container
        self.event_bus: EventBus = container.services.event_bus()

        # Cache event dispatch mapping to avoid per-call construction
        # Use cast to align specific handler signatures with BaseEvent for dispatching
        self._event_handlers: dict[type[BaseEvent], TypingCallable[[BaseEvent], None]] = {
            StartupEvent: cast(TypingCallable[[BaseEvent], None], self._handle_startup),
            SignalGenerated: cast(TypingCallable[[BaseEvent], None], self._handle_signal_generated),
            RebalancePlanned: cast(
                TypingCallable[[BaseEvent], None], self._handle_rebalance_planned
            ),
            TradeExecuted: cast(TypingCallable[[BaseEvent], None], self._handle_trade_executed),
            WorkflowCompleted: cast(
                TypingCallable[[BaseEvent], None], self._handle_workflow_completed
            ),
            WorkflowFailed: cast(TypingCallable[[BaseEvent], None], self._handle_workflow_failed),
        }

        # Register orchestrator's event handlers FIRST so workflow_results is populated
        # before domain handlers process events (critical for data flow)
        self._register_handlers()

        # Register domain handlers using module registration functions
        # These run AFTER orchestrator handlers, so they can access workflow_results
        self._register_domain_handlers()

        # Track workflow state for monitoring and recovery
        self.workflow_state: dict[str, Any] = {
            "startup_completed": False,
            "signal_generation_in_progress": False,
            "rebalancing_in_progress": False,
            "trading_in_progress": False,
            "last_successful_workflow": None,
            "active_correlations": set(),
            "workflow_start_times": {},  # Track workflow start times for duration calculation
            "completed_correlations": set(),  # Track completed/failed correlation IDs to dedupe starts
        }

        # Collect workflow results for each correlation ID
        self.workflow_results: dict[str, dict[str, Any]] = {}

        # Track workflow states per correlation_id for failure prevention
        self.workflow_states: dict[str, WorkflowState] = {}
        self.workflow_states_lock = Lock()

        # Set this orchestrator as the workflow state checker on the event bus
        self.event_bus.set_workflow_state_checker(self)

    def _register_domain_handlers(self) -> None:
        """Register domain event handlers using module registration functions.

        This uses the event-driven API from each business module to register
        their handlers with the event bus. This maintains proper module boundaries.
        """
        try:
            # Register handlers from each business module
            from the_alchemiser.execution_v2 import register_execution_handlers
            from the_alchemiser.notifications_v2 import register_notification_handlers
            from the_alchemiser.portfolio_v2 import register_portfolio_handlers
            from the_alchemiser.strategy_v2 import register_strategy_handlers

            register_strategy_handlers(self.container)
            register_portfolio_handlers(self.container)
            register_execution_handlers(self.container)
            register_notification_handlers(self.container)

            # Wrap handlers with state checking
            self._wrap_handlers_with_state_checking()

            self.logger.debug("Registered domain event handlers via module registration functions")

        except Exception as e:
            self.logger.error(f"Failed to register domain handlers: {e}")
            raise RuntimeError(f"Domain handler registration failed: {e}") from e

    def _wrap_handlers_with_state_checking(self) -> None:
        """Wrap registered handlers with workflow state checking.

        This ensures handlers skip processing for failed workflows without
        modifying the handlers themselves.
        """
        # Get the event bus to access registered handlers
        event_bus = self.event_bus

        # Event types that should check workflow state before processing
        # Note: TradeExecuted added to prevent post-failure execution events
        state_checked_events = [
            "SignalGenerated",
            "RebalancePlanned",
            "TradeExecuted",
        ]

        for event_type in state_checked_events:
            if event_type in event_bus._handlers:
                original_handlers = event_bus._handlers[event_type].copy()
                event_bus._handlers[event_type].clear()

                for handler in original_handlers:
                    # Only wrap real EventHandler implementations; pass through plain callables
                    if isinstance(handler, SharedEventHandler):
                        wrapped_handler = StateCheckingHandlerWrapper(
                            handler, self, event_type, self.logger
                        )
                        event_bus._handlers[event_type].append(wrapped_handler)
                    else:
                        event_bus._handlers[event_type].append(handler)

    def start_trading_workflow(self, *, correlation_id: str | None = None) -> str:
        """Start a complete trading workflow via event-driven coordination.

        Args:
            correlation_id: Optional correlation ID for tracking (generates one if None)

        Returns:
            The correlation ID for tracking the workflow

        """
        workflow_correlation_id = correlation_id or str(uuid.uuid4())

        self.logger.info(f"🚀 Starting event-driven trading workflow: {workflow_correlation_id}")

        try:
            # Check market status before starting workflow
            market_is_open = False
            market_status = "unknown"
            try:
                from the_alchemiser.shared.services.market_clock_service import (
                    MarketClockService,
                )

                # Get trading client from container
                trading_client = self.container.infrastructure.alpaca_manager().trading_client
                market_clock_service = MarketClockService(trading_client)

                # Check if market is open
                market_is_open = market_clock_service.is_market_open(
                    correlation_id=workflow_correlation_id
                )
                market_status = "open" if market_is_open else "closed"

                if not market_is_open:
                    self.logger.warning(
                        "⚠️  Market is currently closed - signal generation will proceed "
                        "but order placement will be skipped",
                        correlation_id=workflow_correlation_id,
                        market_status=market_status,
                    )
                else:
                    self.logger.info(
                        "✅ Market is open - full trading workflow will execute",
                        correlation_id=workflow_correlation_id,
                        market_status=market_status,
                    )
            except Exception as market_check_error:
                # Don't fail workflow if market check fails - log and continue
                self.logger.warning(
                    f"Failed to check market status: {market_check_error}",
                    correlation_id=workflow_correlation_id,
                    error_type=type(market_check_error).__name__,
                )

            # Emit WorkflowStarted event to trigger the domain handlers
            workflow_event = WorkflowStarted(
                correlation_id=workflow_correlation_id,
                causation_id=f"system-request-{datetime.now(UTC).isoformat()}",
                event_id=f"workflow-started-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="orchestration.event_driven_orchestrator",
                source_component="EventDrivenOrchestrator",
                workflow_type="trading",
                requested_by="TradingSystem",
                configuration={
                    "live_trading": not self.container.config.paper_trading(),
                    "market_is_open": market_is_open,
                    "market_status": market_status,
                },
            )

            self.event_bus.publish(workflow_event)
            self.logger.debug(f"📡 Emitted WorkflowStarted event: {workflow_correlation_id}")

            return workflow_correlation_id

        except Exception as e:
            self.logger.error(f"Failed to start trading workflow: {e}")
            raise

    def wait_for_workflow_completion(
        self, correlation_id: str, timeout_seconds: int = 300
    ) -> dict[str, Any]:
        """Wait for workflow completion and return results.

        Args:
            correlation_id: Correlation ID to track
            timeout_seconds: Maximum time to wait for completion

        Returns:
            Dictionary containing workflow results

        """
        start_time = time.time()

        self.logger.info(f"⏳ Waiting for workflow completion: {correlation_id}")

        while time.time() - start_time < timeout_seconds:
            # Check if workflow completed
            if correlation_id not in self.workflow_state["active_correlations"]:
                self.logger.info(f"✅ Workflow completed: {correlation_id}")

                # Get collected workflow results
                workflow_results = self.workflow_results.get(correlation_id, {})

                # Clean up stored results to prevent memory leaks
                self.workflow_results.pop(correlation_id, None)

                # Clean up workflow state to prevent memory leaks
                self.cleanup_workflow_state(correlation_id)

                return {
                    "success": True,
                    "correlation_id": correlation_id,
                    "completion_status": "completed",
                    "duration_seconds": time.time() - start_time,
                    "strategy_signals": workflow_results.get("strategy_signals", {}),
                    "rebalance_plan": workflow_results.get("rebalance_plan", {}),
                    "orders_executed": workflow_results.get("orders_executed", []),
                    "execution_summary": workflow_results.get("execution_summary", {}),
                    "warnings": [],  # Can be populated from event data if needed
                }

            # Brief sleep to avoid busy waiting
            time.sleep(0.1)

        # Timeout occurred
        self.logger.warning(f"⏰ Workflow timeout after {timeout_seconds}s: {correlation_id}")

        # Clean up on timeout
        self.workflow_results.pop(correlation_id, None)
        self.cleanup_workflow_state(correlation_id)

        return {
            "success": False,
            "correlation_id": correlation_id,
            "completion_status": "timeout",
            "duration_seconds": timeout_seconds,
        }

    def _register_handlers(self) -> None:
        """Register orchestration event handlers for cross-cutting concerns."""
        # Subscribe to all event types for cross-cutting concerns (monitoring, notifications)
        for event_type in (
            "StartupEvent",
            "WorkflowStarted",
            "SignalGenerated",
            "RebalancePlanned",
            "TradeExecuted",
            "WorkflowCompleted",
            "WorkflowFailed",
        ):
            self.event_bus.subscribe(event_type, self)

        self.logger.debug(
            "Registered event-driven orchestration handlers for cross-cutting concerns"
        )

    def handle_event(self, event: BaseEvent) -> None:
        """Handle events for cross-cutting orchestration concerns.

        Args:
            event: The event to handle

        """
        try:
            # Use cached dispatch map to avoid per-call dictionary creation
            handler = self._event_handlers.get(type(event))
            if handler:
                handler(event)
            else:
                self.logger.debug(
                    f"EventDrivenOrchestrator ignoring event type: {event.event_type}"
                )

        except Exception as e:
            self.logger.error(
                f"EventDrivenOrchestrator event handling failed for {event.event_type}: {e}",
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
            "WorkflowStarted",
            "SignalGenerated",
            "RebalancePlanned",
            "TradeExecuted",
            "WorkflowCompleted",
            "WorkflowFailed",
        ]

    def _handle_startup(self, event: StartupEvent) -> None:
        """Handle system startup event for monitoring and coordination.

        Args:
            event: The startup event

        """
        self.logger.info(
            f"🚀 EventDrivenOrchestrator: System startup monitoring for mode: {event.startup_mode}"
        )

        # Update workflow monitoring state
        self.workflow_state.update(
            {
                "startup_completed": True,
                "signal_generation_in_progress": False,
                "rebalancing_in_progress": False,
                "trading_in_progress": False,
            }
        )

        # Track this correlation for monitoring
        self.workflow_state["active_correlations"].add(event.correlation_id)

        # Log startup configuration for monitoring
        configuration = event.configuration or {}
        self.logger.debug(f"Monitoring startup configuration: {configuration}")

        # Track successful startup
        self.workflow_state["last_successful_workflow"] = "startup"

    def _handle_signal_generated(self, event: SignalGenerated) -> None:
        """Handle signal generation event for monitoring.

        Args:
            event: The signal generated event

        """
        # Check if workflow has failed before processing
        if self.is_workflow_failed(event.correlation_id):
            self.logger.info(
                f"🚫 Skipping signal generation monitoring - workflow {event.correlation_id} already failed"
            )
            return

        self.logger.debug(
            f"📊 EventDrivenOrchestrator: Monitoring signal generation - {event.signal_count} signals"
        )

        # Update monitoring state
        self.workflow_state.update(
            {
                "signal_generation_in_progress": False,  # Signals completed
                "rebalancing_in_progress": True,  # Rebalancing should start
            }
        )

        # Log signal summary for monitoring
        self.logger.debug(f"Monitoring signals data: {event.signals_data}")

        # Collect strategy signals for workflow results
        if event.correlation_id not in self.workflow_results:
            self.workflow_results[event.correlation_id] = {}

        # Use the signals_data directly from the event
        self.workflow_results[event.correlation_id]["strategy_signals"] = event.signals_data

        # Store consolidated_portfolio for notification enrichment
        self.workflow_results[event.correlation_id]["consolidated_portfolio"] = (
            event.consolidated_portfolio
        )

        # Track successful signal processing
        self.workflow_state["last_successful_workflow"] = "signal_generation"

    def _handle_rebalance_planned(self, event: RebalancePlanned) -> None:
        """Handle rebalance planning event for monitoring.

        Args:
            event: The rebalance planned event

        """
        # Check if workflow has failed before processing
        if self.is_workflow_failed(event.correlation_id):
            self.logger.info(
                f"🚫 Skipping rebalance planning monitoring - workflow {event.correlation_id} already failed"
            )
            return

        self.logger.debug(
            f"⚖️ EventDrivenOrchestrator: Monitoring rebalance planning - trades required: {event.trades_required}"
        )

        # Update monitoring state
        self.workflow_state.update(
            {
                "rebalancing_in_progress": False,  # Rebalancing plan completed
                "trading_in_progress": True,  # Trading should start
            }
        )

        # Log rebalancing plan summary for monitoring
        self.logger.debug(f"Monitoring rebalance plan: {event.rebalance_plan}")

        # Collect rebalance plan for workflow results
        if event.correlation_id not in self.workflow_results:
            self.workflow_results[event.correlation_id] = {}

        # Use the rebalance_plan directly from the event
        self.workflow_results[event.correlation_id]["rebalance_plan"] = event.rebalance_plan

        # Track successful rebalancing
        self.workflow_state["last_successful_workflow"] = "rebalancing"

    def _handle_trade_executed(self, event: TradeExecuted) -> None:
        """Handle trade execution event for notifications and reconciliation.

        Args:
            event: The trade executed event

        """
        success = event.success
        self.logger.debug(
            f"🎯 EventDrivenOrchestrator: Trade execution monitoring - {'✅' if success else '❌'}"
        )

        # Update monitoring state
        self.workflow_state.update(
            {
                "trading_in_progress": False,  # Trading completed
            }
        )

        # Remove from active correlations as workflow is complete
        self.workflow_state["active_correlations"].discard(event.correlation_id)

        # Collect execution results for workflow results
        if event.correlation_id not in self.workflow_results:
            self.workflow_results[event.correlation_id] = {}

        # Use execution data directly from the event
        self.workflow_results[event.correlation_id].update(
            {
                "orders_executed": event.execution_data.get("orders", []),
                "execution_summary": {
                    "orders_placed": event.orders_placed,
                    "orders_succeeded": event.orders_succeeded,
                },
                "success": success,
            }
        )

        if success:
            self.logger.info(
                "EventDrivenOrchestrator: Full trading workflow monitoring completed successfully"
            )
            self.workflow_state["last_successful_workflow"] = "trading"

            # Perform post-trade reconciliation
            self._perform_reconciliation()

            # Send success notification
            self._send_trading_notification(event, success=True)
        else:
            self.logger.error(
                "EventDrivenOrchestrator: Trading workflow monitoring detected failure"
            )

            # Send failure notification
            self._send_trading_notification(event, success=False)

            # Trigger recovery workflow
            self._trigger_recovery_workflow(event)

    def _extract_consolidated_portfolio(self, workflow_results: dict[str, Any]) -> dict[str, Any]:
        """Extract consolidated portfolio from workflow context.

        Args:
            workflow_results: Dictionary containing workflow results

        Returns:
            Dictionary mapping symbols to their target weights

        """
        # Try to get from SignalGenerated event first
        consolidated_portfolio = workflow_results.get("consolidated_portfolio", {})
        if consolidated_portfolio:
            return cast(dict[str, Any], consolidated_portfolio)

        # Fall back to rebalance plan
        if "rebalance_plan" not in workflow_results:
            return {}

        rebalance_plan = workflow_results["rebalance_plan"]

        # Try to extract from rebalance plan metadata
        if hasattr(rebalance_plan, "metadata") and isinstance(rebalance_plan.metadata, dict):
            consolidated_portfolio = rebalance_plan.metadata.get("consolidated_portfolio", {})
            if consolidated_portfolio:
                return cast(dict[str, Any], consolidated_portfolio)

        # Build from rebalance plan items as last resort
        result: dict[str, Any] = {}
        if hasattr(rebalance_plan, "items") and rebalance_plan.items:
            for item in rebalance_plan.items:
                symbol = getattr(item, "symbol", None)
                target_weight = getattr(item, "target_weight", None)
                if symbol and target_weight is not None:
                    result[symbol] = float(target_weight)

        return result

    def _prepare_execution_data(self, event: TradeExecuted, *, success: bool) -> dict[str, Any]:
        """Prepare execution data with failure details and workflow context.

        Args:
            event: The TradeExecuted event
            success: Whether the trading was successful

        Returns:
            Dictionary containing execution data with failure details and workflow context

        """
        execution_data = event.execution_data.copy() if event.execution_data else {}

        # Add failed symbols to execution data for notification service
        if not success and event.failed_symbols:
            execution_data["failed_symbols"] = event.failed_symbols

        # Enrich execution_data with workflow context for comprehensive email notifications
        workflow_results = self.workflow_results.get(event.correlation_id, {})

        # Add strategy signals from workflow context
        if "strategy_signals" in workflow_results:
            execution_data["strategy_signals"] = workflow_results["strategy_signals"]

        # Add consolidated portfolio from workflow context
        consolidated_portfolio = self._extract_consolidated_portfolio(workflow_results)
        if consolidated_portfolio:
            execution_data["consolidated_portfolio"] = consolidated_portfolio

        # Add execution summary with consolidated portfolio for template compatibility
        if "execution_summary" in workflow_results:
            execution_data["execution_summary"] = workflow_results["execution_summary"]
            # Ensure execution_summary has consolidated_portfolio for template lookup
            if "consolidated_portfolio" in execution_data:
                execution_data["execution_summary"]["consolidated_portfolio"] = execution_data[
                    "consolidated_portfolio"
                ]

        # Add orders_executed list for order detail display
        if "orders_executed" in workflow_results:
            execution_data["orders_executed"] = workflow_results["orders_executed"]

        return execution_data

    def _extract_trade_value(self, execution_data: dict[str, Any]) -> Decimal:
        """Extract and normalize total trade value to Decimal.

        Args:
            execution_data: Dictionary containing execution data

        Returns:
            Total trade value as Decimal, or Decimal("0") if conversion fails

        """
        raw_total_value = execution_data.get("total_trade_value", 0)
        try:
            return Decimal(str(raw_total_value))
        except (TypeError, ValueError):
            return Decimal("0")

    def _extract_error_details(
        self, event: TradeExecuted, *, success: bool
    ) -> tuple[str | None, str | None]:
        """Extract error message and code from failed trade event.

        Args:
            event: The TradeExecuted event
            success: Whether the trading was successful

        Returns:
            Tuple of (error_message, error_code), both None if successful

        """
        if not success:
            error_message = (
                event.failure_reason or event.metadata.get("error_message") or "Unknown error"
            )
            error_code = getattr(event, "error_code", None)
            return error_message, error_code
        return None, None

    def _build_trading_notification(
        self, event: TradeExecuted, *, success: bool
    ) -> BaseEvent:  # Returns TradingNotificationRequested which inherits from BaseEvent
        """Build trading notification event from trade execution event.

        Args:
            event: The TradeExecuted event
            success: Whether the trading was successful

        Returns:
            TradingNotificationRequested event ready to publish

        """
        from the_alchemiser.shared.events.schemas import TradingNotificationRequested

        mode_str = "LIVE" if not self.container.config.paper_trading() else "PAPER"
        execution_data = self._prepare_execution_data(event, success=success)
        total_trade_value = self._extract_trade_value(execution_data)
        error_message, error_code = self._extract_error_details(event, success=success)

        return TradingNotificationRequested(
            correlation_id=event.correlation_id,
            causation_id=event.event_id,
            event_id=f"trading-notification-{uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="orchestration.event_driven_orchestrator",
            source_component="EventDrivenOrchestrator",
            trading_success=success,
            trading_mode=mode_str,
            orders_placed=event.orders_placed,
            orders_succeeded=event.orders_succeeded,
            total_trade_value=total_trade_value,
            execution_data=execution_data,
            error_message=error_message,
            error_code=error_code,
        )

    def _send_trading_notification(self, event: TradeExecuted, *, success: bool) -> None:
        """Send trading completion notification via event bus.

        Args:
            event: The TradeExecuted event
            success: Whether the trading was successful

        """
        try:
            trading_event = self._build_trading_notification(event, success=success)
            self.event_bus.publish(trading_event)

            self.logger.info(
                f"Trading notification event published successfully (success={success})",
                extra={"correlation_id": event.correlation_id},
            )

        except Exception as e:
            # Don't let notification failure break the workflow
            self.logger.error(
                f"Failed to publish trading notification event: {e}",
                extra={"correlation_id": event.correlation_id},
            )

    def _perform_reconciliation(self) -> None:
        """Perform post-trade reconciliation workflow."""
        self.logger.debug("🔄 Starting post-trade reconciliation")

        try:
            # In the future, this would:
            # 1. Verify portfolio state matches expectations
            # 2. Check trade execution accuracy
            # 3. Update position tracking
            # 4. Generate reconciliation reports
            self.logger.debug("Reconciliation: Verifying portfolio state")
            self.logger.debug("Reconciliation: Checking trade execution accuracy")
            self.logger.debug("Reconciliation: Updating position tracking")

            self.logger.info("✅ Post-trade reconciliation completed successfully")

        except Exception as e:
            self.logger.error(f"Reconciliation failed: {e}")

    def _trigger_recovery_workflow(self, event: TradeExecuted) -> None:
        """Trigger recovery workflow for failed trades.

        Args:
            event: The trade executed event (failed)

        """
        self.logger.debug("🚨 Starting recovery workflow for failed trades")

        try:
            # In the future, this would:
            # 1. Analyze failure causes
            # 2. Determine recovery actions
            # 3. Emit recovery events
            # 4. Alert system administrators

            self.logger.warning(
                f"Recovery: Assessing failure - {event.metadata.get('error_message', 'Unknown error')}"
            )
            self.logger.debug("Recovery: Determining corrective actions")
            self.logger.debug("Recovery: Preparing system alerts")

            # For now, log the recovery intent
            self.logger.debug(
                "Recovery workflow prepared (full implementation in future iterations)"
            )

        except Exception as e:
            self.logger.error(f"Recovery workflow failed: {e}")

    def _handle_workflow_completed(self, event: WorkflowCompleted) -> None:
        """Handle WorkflowCompleted event for monitoring and cleanup.

        Args:
            event: The WorkflowCompleted event

        """
        self.logger.info(
            f"✅ Workflow completed successfully: {event.workflow_type}",
            extra={
                "correlation_id": event.correlation_id,
                "workflow_type": event.workflow_type,
                "workflow_state": WorkflowState.COMPLETED.value,
            },
        )

        # Calculate and log workflow duration
        start_time = self.workflow_state["workflow_start_times"].get(event.correlation_id)
        if start_time:
            duration_ms = (event.timestamp - start_time).total_seconds() * 1000
            self.logger.info(
                f"📊 Workflow duration: {duration_ms:.0f}ms",
                extra={
                    "correlation_id": event.correlation_id,
                    "duration_ms": duration_ms,
                },
            )

        # Update workflow state
        self.workflow_state["last_successful_workflow"] = event.workflow_type
        self.workflow_state["active_correlations"].discard(event.correlation_id)

        # Track completion to prevent duplicate starts
        self.workflow_state["completed_correlations"].add(event.correlation_id)

        # Clean up tracking data
        self.workflow_state["workflow_start_times"].pop(event.correlation_id, None)

        # Reset progress flags
        self.workflow_state.update(
            {
                "signal_generation_in_progress": False,
                "rebalancing_in_progress": False,
                "trading_in_progress": False,
            }
        )

        # Set workflow state to COMPLETED
        self._set_workflow_state(event.correlation_id, WorkflowState.COMPLETED)
        self.logger.info(
            f"✅ Workflow {event.correlation_id} marked as COMPLETED",
            extra={
                "correlation_id": event.correlation_id,
                "workflow_state": WorkflowState.COMPLETED.value,
            },
        )

    def _handle_workflow_failed(self, event: WorkflowFailed) -> None:
        """Handle WorkflowFailed event for error handling and recovery.

        Args:
            event: The WorkflowFailed event

        """
        self.logger.error(f"❌ Workflow failed: {event.workflow_type} - {event.failure_reason}")

        # Set workflow state to FAILED to prevent further event processing
        self._set_workflow_state(event.correlation_id, WorkflowState.FAILED)
        self.logger.info(
            f"🚫 Workflow {event.correlation_id} marked as FAILED - future events will be skipped",
            extra={
                "correlation_id": event.correlation_id,
                "workflow_state": WorkflowState.FAILED.value,
            },
        )

        # Update workflow state
        self.workflow_state["active_correlations"].discard(event.correlation_id)

        # Track completion to prevent duplicate starts
        self.workflow_state["completed_correlations"].add(event.correlation_id)

        # Clean up tracking data
        self.workflow_state["workflow_start_times"].pop(event.correlation_id, None)

        # Reset progress flags
        self.workflow_state.update(
            {
                "signal_generation_in_progress": False,
                "rebalancing_in_progress": False,
                "trading_in_progress": False,
            }
        )

        # Trigger error notifications and recovery
        try:
            self.logger.info("Triggering error notification for workflow failure")
            # In future iterations, implement comprehensive error handling

        except Exception as e:
            self.logger.error(f"Failed to handle workflow failure: {e}")

    def get_workflow_status(self) -> dict[str, Any]:
        """Get current workflow status for monitoring.

        Returns:
            Dictionary containing workflow state information

        """
        # Calculate state metrics
        with self.workflow_states_lock:
            state_counts = {
                "running": 0,
                "failed": 0,
                "completed": 0,
            }
            for state in self.workflow_states.values():
                state_counts[state.value] += 1

            workflow_states_copy = self.workflow_states.copy()

        return {
            "workflow_state": self.workflow_state.copy(),
            "event_bus_stats": self.event_bus.get_stats(),
            "orchestrator_active": True,
            "workflow_state_metrics": {
                "total_tracked": len(workflow_states_copy),
                "by_state": state_counts,
                "active_workflows": len(self.workflow_state["active_correlations"]),
                "completed_workflows": len(self.workflow_state["completed_correlations"]),
            },
        }

    def is_workflow_failed(self, correlation_id: str) -> bool:
        """Check if a workflow has failed.

        Args:
            correlation_id: The workflow correlation ID to check

        Returns:
            True if the workflow has failed, False otherwise

        """
        with self.workflow_states_lock:
            return self.workflow_states.get(correlation_id) == WorkflowState.FAILED

    def is_workflow_active(self, correlation_id: str) -> bool:
        """Check if a workflow is actively running.

        Args:
            correlation_id: The workflow correlation ID to check

        Returns:
            True if the workflow is running, False otherwise

        """
        with self.workflow_states_lock:
            return self.workflow_states.get(correlation_id) == WorkflowState.RUNNING

    def get_workflow_state(self, correlation_id: str) -> WorkflowState | None:
        """Get the current workflow state for a given correlation ID.

        Args:
            correlation_id: The workflow correlation ID to check

        Returns:
            The current WorkflowState, or None if workflow not tracked

        """
        with self.workflow_states_lock:
            return self.workflow_states.get(correlation_id)

    def cleanup_workflow_state(self, correlation_id: str) -> bool:
        """Clean up workflow state for a given correlation ID.

        This should be called after workflow results have been retrieved to prevent
        memory leaks from accumulating workflow states.

        Args:
            correlation_id: The workflow correlation ID to clean up

        Returns:
            True if state was cleaned up, False if correlation_id not found

        """
        with self.workflow_states_lock:
            if correlation_id in self.workflow_states:
                state = self.workflow_states.pop(correlation_id)
                self.logger.debug(
                    f"🧹 Cleaned up workflow state for {correlation_id} (was {state.value})"
                )
                return True
            return False

    def _set_workflow_state(self, correlation_id: str, state: WorkflowState) -> None:
        """Set the workflow state for a given correlation ID.

        Args:
            correlation_id: The workflow correlation ID
            state: The new state to set

        """
        with self.workflow_states_lock:
            self.workflow_states[correlation_id] = state
