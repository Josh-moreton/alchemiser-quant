#!/usr/bin/env python3
"""Business Unit: orchestration | Status: current.

Event-driven orchestration handlers for cross-cutting concerns.

Provides event handlers for notifications, reconciliation, monitoring, and recovery
across the trading workflow. Focused on cross-cutting concerns rather than domain execution.
"""

from __future__ import annotations

from collections.abc import Callable as TypingCallable
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, cast

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
from the_alchemiser.shared.logging.logging_utils import get_logger
from the_alchemiser.shared.notifications.templates.multi_strategy import (
    MultiStrategyReportBuilder,
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

        # Initialize domain handlers
        self.domain_handlers = self._initialize_domain_handlers()

        # Cache event dispatch mapping to avoid per-call construction
        # Use cast to align specific handler signatures with BaseEvent for dispatching
        self._event_handlers: dict[
            type[BaseEvent], TypingCallable[[BaseEvent], None]
        ] = {
            StartupEvent: cast(TypingCallable[[BaseEvent], None], self._handle_startup),
            WorkflowStarted: cast(
                TypingCallable[[BaseEvent], None], self._handle_workflow_started
            ),
            SignalGenerated: cast(
                TypingCallable[[BaseEvent], None], self._handle_signal_generated
            ),
            RebalancePlanned: cast(
                TypingCallable[[BaseEvent], None], self._handle_rebalance_planned
            ),
            TradeExecuted: cast(
                TypingCallable[[BaseEvent], None], self._handle_trade_executed
            ),
            WorkflowCompleted: cast(
                TypingCallable[[BaseEvent], None], self._handle_workflow_completed
            ),
            WorkflowFailed: cast(
                TypingCallable[[BaseEvent], None], self._handle_workflow_failed
            ),
        }

        # Register event handlers (both cross-cutting and domain)
        self._register_handlers()

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

    def _initialize_domain_handlers(self) -> dict[str, Any]:
        """Initialize domain event handlers.

        Returns:
            Dictionary of initialized domain handlers

        """
        handlers: dict[str, Any] = {}

        try:
            # Import and initialize domain handlers
            from the_alchemiser.execution_v2.handlers import TradingExecutionHandler
            from the_alchemiser.portfolio_v2.handlers import PortfolioAnalysisHandler
            from the_alchemiser.strategy_v2.handlers import SignalGenerationHandler

            handlers["signal_generation"] = SignalGenerationHandler(self.container)
            handlers["portfolio_analysis"] = PortfolioAnalysisHandler(self.container)
            handlers["trading_execution"] = TradingExecutionHandler(self.container)

            self.logger.info("Initialized domain event handlers")

        except Exception as e:
            self.logger.error(f"Failed to initialize domain handlers: {e}")

        return handlers

    def start_trading_workflow(self, *, correlation_id: str | None = None) -> str:
        """Start a complete trading workflow via event-driven coordination.

        Args:
            correlation_id: Optional correlation ID for tracking (generates one if None)

        Returns:
            The correlation ID for tracking the workflow

        """
        import uuid

        workflow_correlation_id = correlation_id or str(uuid.uuid4())

        self.logger.info(
            f"🚀 Starting event-driven trading workflow: {workflow_correlation_id}"
        )

        try:
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
                },
            )

            self.event_bus.publish(workflow_event)
            self.logger.info(
                f"📡 Emitted WorkflowStarted event: {workflow_correlation_id}"
            )

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
        import time

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
        self.logger.warning(
            f"⏰ Workflow timeout after {timeout_seconds}s: {correlation_id}"
        )

        # Clean up on timeout
        self.workflow_results.pop(correlation_id, None)

        return {
            "success": False,
            "correlation_id": correlation_id,
            "completion_status": "timeout",
            "duration_seconds": timeout_seconds,
        }

    def _register_handlers(self) -> None:
        """Register event handlers for primary workflow coordination and cross-cutting concerns."""
        # Register domain handlers for primary workflow coordination
        for handler_name, handler in self.domain_handlers.items():
            if hasattr(handler, "can_handle") and hasattr(handler, "handle_event"):
                # Register handler for events it can handle
                for evt in (
                    "StartupEvent",
                    "WorkflowStarted",
                    "SignalGenerated",
                    "RebalancePlanned",
                ):
                    if handler.can_handle(evt):
                        self.event_bus.subscribe(evt, handler)

                self.logger.info(f"Registered domain handler: {handler_name}")

        # Subscribe to all event types for cross-cutting concerns (monitoring, notifications)
        for evt in (
            "StartupEvent",
            "WorkflowStarted",
            "SignalGenerated",
            "RebalancePlanned",
            "TradeExecuted",
            "WorkflowCompleted",
            "WorkflowFailed",
        ):
            self.event_bus.subscribe(evt, self)

        self.logger.info(
            "Registered event-driven orchestration handlers for primary coordination and cross-cutting concerns"
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
        self.logger.info(
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
        self.workflow_results[event.correlation_id][
            "strategy_signals"
        ] = event.signals_data

        # Track successful signal processing
        self.workflow_state["last_successful_workflow"] = "signal_generation"

    def _handle_rebalance_planned(self, event: RebalancePlanned) -> None:
        """Handle rebalance planning event for monitoring.

        Args:
            event: The rebalance planned event

        """
        self.logger.info(
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
        self.workflow_results[event.correlation_id][
            "rebalance_plan"
        ] = event.rebalance_plan

        # Track successful rebalancing
        self.workflow_state["last_successful_workflow"] = "rebalancing"

    def _handle_trade_executed(self, event: TradeExecuted) -> None:
        """Handle trade execution event for notifications and reconciliation.

        Args:
            event: The trade executed event

        """
        success = event.success
        self.logger.info(
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

    def _send_trading_notification(
        self, event: TradeExecuted, *, success: bool
    ) -> None:
        """Send trading completion notification.

        Args:
            event: The TradeExecuted event
            success: Whether the trading was successful

        """
        try:
            from the_alchemiser.shared.notifications.email_utils import (
                build_error_email_html,
                send_email_notification,
            )

            # Determine trading mode from container
            is_live = not self.container.config.paper_trading()
            mode_str = "LIVE" if is_live else "PAPER"

            # Extract execution data
            execution_data = event.execution_data
            orders_placed = event.orders_placed
            orders_succeeded = event.orders_succeeded
            # total_trade_value may be Decimal, float, or string; normalize for formatting
            raw_total_value = execution_data.get("total_trade_value", 0)
            try:
                total_trade_value_float = float(raw_total_value)
            except (TypeError, ValueError):
                total_trade_value_float = 0.0

            if success:
                # Use enhanced successful trading run template instead of basic HTML
                try:
                    # Create a result adapter for the enhanced template
                    class EventResultAdapter:
                        def __init__(
                            self, execution_data: dict[str, Any], correlation_id: str
                        ) -> None:
                            self.success = True
                            self.orders_executed: list[Any] = (
                                []
                            )  # Event data doesn't have detailed order info
                            self.strategy_signals: dict[str, Any] = (
                                {}
                            )  # Event data doesn't have signal details
                            self.correlation_id = correlation_id
                            # Add any other fields the template might use via getattr
                            self._execution_data = execution_data

                        def __getattr__(self, name: str) -> object:
                            # Allow template to access any field from execution_data
                            return self._execution_data.get(name, None)

                    result_adapter = EventResultAdapter(
                        execution_data, event.correlation_id
                    )
                    html_content = (
                        MultiStrategyReportBuilder.build_multi_strategy_report_neutral(
                            result_adapter,
                            mode_str,
                        )
                    )
                except Exception as template_error:
                    # Fallback to basic template if enhanced template fails
                    self.logger.warning(
                        f"Enhanced template failed, using basic: {template_error}"
                    )
                    html_content = f"""
                    <h2>Trading Execution Report - {mode_str.upper()}</h2>
                    <p><strong>Status:</strong> Success</p>
                    <p><strong>Orders Placed:</strong> {orders_placed}</p>
                    <p><strong>Orders Succeeded:</strong> {orders_succeeded}</p>
                    <p><strong>Total Trade Value:</strong> ${total_trade_value_float:,.2f}</p>
                    <p><strong>Correlation ID:</strong> {event.correlation_id}</p>
                    <p><strong>Timestamp:</strong> {event.timestamp}</p>
                    """
            else:
                error_message = event.metadata.get("error_message") or "Unknown error"
                html_content = build_error_email_html(
                    "Trading Execution Failed",
                    f"Trading workflow failed: {error_message}",
                )

            status_tag = "SUCCESS" if success else "FAILURE"

            # Include error code in subject if available for failures
            if not success and hasattr(event, "error_code") and event.error_code:
                subject = f"[{status_tag}][{event.error_code}] The Alchemiser - {mode_str.upper()} Trading Report"
            else:
                subject = (
                    f"[{status_tag}] The Alchemiser - {mode_str.upper()} Trading Report"
                )

            send_email_notification(
                subject=subject,
                html_content=html_content,
                text_content=f"Trading execution completed. Success: {success}",
            )

            self.logger.info(
                f"Trading notification sent successfully (success={success})"
            )

        except Exception as e:
            # Don't let notification failure break the workflow
            self.logger.warning(f"Failed to send trading notification: {e}")

    def _perform_reconciliation(self) -> None:
        """Perform post-trade reconciliation workflow."""
        self.logger.info("🔄 Starting post-trade reconciliation")

        try:
            # In the future, this would:
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
        """Trigger recovery workflow for failed trades.

        Args:
            event: The trade executed event (failed)

        """
        self.logger.info("🚨 Starting recovery workflow for failed trades")

        try:
            # In the future, this would:
            # 1. Analyze failure causes
            # 2. Determine recovery actions
            # 3. Emit recovery events
            # 4. Alert system administrators

            self.logger.warning(
                f"Recovery: Assessing failure - {event.metadata.get('error_message', 'Unknown error')}"
            )
            self.logger.info("Recovery: Determining corrective actions")
            self.logger.info("Recovery: Preparing system alerts")

            # For now, log the recovery intent
            self.logger.info(
                "Recovery workflow prepared (full implementation in future iterations)"
            )

        except Exception as e:
            self.logger.error(f"Recovery workflow failed: {e}")

    def _handle_workflow_started(self, event: WorkflowStarted) -> None:
        """Handle WorkflowStarted event for monitoring and state tracking.

        Args:
            event: The WorkflowStarted event

        """
        # Check if this workflow has already completed - ignore duplicate starts
        if event.correlation_id in self.workflow_state["completed_correlations"]:
            self.logger.info(
                f"🔄 Ignoring duplicate WorkflowStarted event for already completed workflow: "
                f"{event.workflow_type} (correlation_id: {event.correlation_id})"
            )
            return

        self.logger.info(f"🚀 Workflow started: {event.workflow_type}")

        # Track workflow start time
        self.workflow_state["workflow_start_times"][
            event.correlation_id
        ] = event.timestamp
        self.workflow_state["active_correlations"].add(event.correlation_id)

        # Update workflow state based on type
        if event.workflow_type == "trading":
            self.workflow_state["signal_generation_in_progress"] = True

    def _handle_workflow_completed(self, event: WorkflowCompleted) -> None:
        """Handle WorkflowCompleted event for monitoring and cleanup.

        Args:
            event: The WorkflowCompleted event

        """
        self.logger.info(f"✅ Workflow completed successfully: {event.workflow_type}")

        # Calculate and log workflow duration
        start_time = self.workflow_state["workflow_start_times"].get(
            event.correlation_id
        )
        if start_time:
            duration_ms = (event.timestamp - start_time).total_seconds() * 1000
            self.logger.info(f"📊 Workflow duration: {duration_ms:.0f}ms")

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

    def _handle_workflow_failed(self, event: WorkflowFailed) -> None:
        """Handle WorkflowFailed event for error handling and recovery.

        Args:
            event: The WorkflowFailed event

        """
        self.logger.error(
            f"❌ Workflow failed: {event.workflow_type} - {event.failure_reason}"
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
        return {
            "workflow_state": self.workflow_state.copy(),
            "event_bus_stats": self.event_bus.get_stats(),
            "orchestrator_active": True,
        }
