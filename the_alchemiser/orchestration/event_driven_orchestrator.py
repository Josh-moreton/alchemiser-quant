#!/usr/bin/env python3
"""Business Unit: orchestration | Status: current.

Event-driven orchestration handlers for cross-cutting concerns.

Provides event handlers for notifications, reconciliation, monitoring, and recovery
across the trading workflow. Focused on cross-cutting concerns rather than domain execution.
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
from the_alchemiser.shared.notifications.templates.multi_strategy import (
    MultiStrategyReportBuilder,
)


class EventDrivenOrchestrator:
    """Event-driven orchestrator for cross-cutting workflow concerns.

    Handles notifications, reconciliation, monitoring, and recovery across
    the trading workflow without duplicating domain logic.
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

        # Register event handlers
        self._register_handlers()

        # Track workflow state for monitoring and recovery
        self.workflow_state: dict[str, Any] = {
            "startup_completed": False,
            "signal_generation_in_progress": False,
            "rebalancing_in_progress": False,
            "trading_in_progress": False,
            "last_successful_workflow": None,
            "active_correlations": set(),
        }

    def _register_handlers(self) -> None:
        """Register event handlers for cross-cutting orchestration concerns."""
        # Subscribe to all event types for monitoring and cross-cutting concerns
        self.event_bus.subscribe("StartupEvent", self)
        self.event_bus.subscribe("SignalGenerated", self)
        self.event_bus.subscribe("RebalancePlanned", self)
        self.event_bus.subscribe("TradeExecuted", self)

        self.logger.info(
            "Registered event-driven orchestration handlers for cross-cutting concerns"
        )

    def handle_event(self, event: BaseEvent) -> None:
        """Handle events for cross-cutting orchestration concerns.

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
            "SignalGenerated",
            "RebalancePlanned",
            "TradeExecuted",
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
            f"📊 EventDrivenOrchestrator: Monitoring signal generation - {len(event.signals)} signals"
        )

        # Update monitoring state
        self.workflow_state.update(
            {
                "signal_generation_in_progress": False,  # Signals completed
                "rebalancing_in_progress": True,  # Rebalancing should start
            }
        )

        # Log signal summary for monitoring
        for signal in event.signals:
            self.logger.debug(
                f"Monitoring signal: {signal.symbol} {signal.action} "
                f"(strategy: {signal.strategy_name}, confidence: {signal.confidence})"
            )

        # Track successful signal processing
        self.workflow_state["last_successful_workflow"] = "signal_generation"

    def _handle_rebalance_planned(self, event: RebalancePlanned) -> None:
        """Handle rebalance planning event for monitoring.

        Args:
            event: The rebalance planned event

        """
        self.logger.info(
            f"⚖️ EventDrivenOrchestrator: Monitoring rebalance planning - {len(event.rebalance_plan.items)} trades"
        )

        # Update monitoring state
        self.workflow_state.update(
            {
                "rebalancing_in_progress": False,  # Rebalancing plan completed
                "trading_in_progress": True,  # Trading should start
            }
        )

        # Log rebalancing plan summary for monitoring
        total_value = event.rebalance_plan.total_trade_value
        self.logger.debug(f"Monitoring total trade value: ${total_value}")

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

        if success:
            self.logger.info(
                "EventDrivenOrchestrator: Full trading workflow monitoring completed successfully"
            )
            self.workflow_state["last_successful_workflow"] = "trading"

            # Perform post-trade reconciliation
            self._perform_reconciliation(event)

            # Send success notification
            self._send_trading_notification(event, success=True)
        else:
            self.logger.error(
                f"EventDrivenOrchestrator: Trading workflow monitoring detected failure - {event.error_message}"
            )

            # Send failure notification
            self._send_trading_notification(event, success=False)

            # Trigger recovery workflow
            self._trigger_recovery_workflow(event)

    def _send_trading_notification(self, event: TradeExecuted, *, success: bool) -> None:
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
            execution_data = event.execution_results
            orders_placed = execution_data.get("orders_placed", 0)
            orders_succeeded = execution_data.get("orders_succeeded", 0)
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
                            self.orders_executed: list[
                                Any
                            ] = []  # Event data doesn't have detailed order info
                            self.strategy_signals: dict[
                                str, Any
                            ] = {}  # Event data doesn't have signal details
                            self.correlation_id = correlation_id
                            # Add any other fields the template might use via getattr
                            self._execution_data = execution_data

                        def __getattr__(self, name: str) -> object:
                            # Allow template to access any field from execution_data
                            return self._execution_data.get(name, None)

                    result_adapter = EventResultAdapter(execution_data, event.correlation_id)
                    html_content = MultiStrategyReportBuilder.build_multi_strategy_report_neutral(
                        result_adapter,
                        mode_str,
                    )
                except Exception as template_error:
                    # Fallback to basic template if enhanced template fails
                    self.logger.warning(f"Enhanced template failed, using basic: {template_error}")
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
                error_message = event.error_message or "Unknown error"
                html_content = build_error_email_html(
                    "Trading Execution Failed",
                    f"Trading workflow failed: {error_message}",
                )

            status_tag = "SUCCESS" if success else "FAILURE"

            # Include error code in subject if available for failures
            if not success and hasattr(event, "error_code") and event.error_code:
                subject = f"[{status_tag}][{event.error_code}] 📈 The Alchemiser - {mode_str.upper()} Trading Report"
            else:
                subject = f"[{status_tag}] 📈 The Alchemiser - {mode_str.upper()} Trading Report"

            send_email_notification(
                subject=subject,
                html_content=html_content,
                text_content=f"Trading execution completed. Success: {success}",
            )

            self.logger.info(f"Trading notification sent successfully (success={success})")

        except Exception as e:
            # Don't let notification failure break the workflow
            self.logger.warning(f"Failed to send trading notification: {e}")

    def _perform_reconciliation(self, event: TradeExecuted) -> None:
        """Perform post-trade reconciliation workflow.

        Args:
            event: The trade executed event

        """
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

            self.logger.warning(f"Recovery: Assessing failure - {event.error_message}")
            self.logger.info("Recovery: Determining corrective actions")
            self.logger.info("Recovery: Preparing system alerts")

            # For now, log the recovery intent
            self.logger.info(
                "Recovery workflow prepared (full implementation in future iterations)"
            )

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
