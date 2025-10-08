#!/usr/bin/env python3
"""Business Unit: execution | Status: current.

Trading execution event handler for event-driven architecture.

Processes RebalancePlanned events to execute trades and emit TradeExecuted events.
This handler is stateless and focuses on trade execution logic without orchestration concerns.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer

from the_alchemiser.execution_v2.models.execution_result import (
    ExecutionResult,
    ExecutionStatus,
)
from the_alchemiser.shared.constants import DECIMAL_ZERO, EXECUTION_HANDLERS_MODULE
from the_alchemiser.shared.events import (
    BaseEvent,
    EventBus,
    RebalancePlanned,
    TradeExecuted,
    WorkflowCompleted,
    WorkflowFailed,
)
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlan


class TradingExecutionHandler:
    """Event handler for trade execution.

    Listens for RebalancePlanned events and executes trades,
    emitting TradeExecuted events and WorkflowCompleted events.
    """

    def __init__(self, container: ApplicationContainer) -> None:
        """Initialize the trading execution handler.

        Args:
            container: Application container for dependency injection

        """
        self.container = container
        self.logger = get_logger(__name__)

        # Get event bus from container
        self.event_bus: EventBus = container.services.event_bus()

    def handle_event(self, event: BaseEvent) -> None:
        """Handle events for trade execution.

        Args:
            event: The event to handle

        """
        try:
            if isinstance(event, RebalancePlanned):
                self._handle_rebalance_planned(event)
            else:
                self.logger.debug(
                    f"TradingExecutionHandler ignoring event type: {event.event_type}"
                )

        except Exception as e:
            self.logger.error(
                f"TradingExecutionHandler event handling failed for {event.event_type}: {e}",
                extra={
                    "event_id": event.event_id,
                    "correlation_id": event.correlation_id,
                },
            )

            # Emit workflow failure event
            self._emit_workflow_failure(event, str(e))

    def can_handle(self, event_type: str) -> bool:
        """Check if handler can handle a specific event type.

        Args:
            event_type: The type of event to check

        Returns:
            True if this handler can handle the event type

        """
        return event_type in [
            "RebalancePlanned",
        ]

    def _handle_rebalance_planned(self, event: RebalancePlanned) -> None:
        """Handle RebalancePlanned event by executing trades.

        Args:
            event: The RebalancePlanned event

        """
        self.logger.info("🔄 Starting trade execution from RebalancePlanned event")

        try:
            # Reconstruct RebalancePlan from event data
            rebalance_plan_data = event.rebalance_plan

            # Handle no-trade scenario
            if not event.trades_required or not rebalance_plan_data.items:
                self.logger.info("📊 No significant trades needed - portfolio already balanced")

                # Create empty execution result
                execution_result = ExecutionResult(
                    success=True,
                    status=ExecutionStatus.SUCCESS,
                    plan_id=rebalance_plan_data.plan_id,
                    correlation_id=event.correlation_id,
                    orders=[],
                    orders_placed=0,
                    orders_succeeded=0,
                    total_trade_value=DECIMAL_ZERO,
                    execution_timestamp=datetime.now(UTC),
                    metadata={"scenario": "no_trades_needed"},
                )

                # Emit successful trade executed event
                self._emit_trade_executed_event(execution_result, success=True)

                # Emit workflow completed event
                self._emit_workflow_completed_event(event.correlation_id, execution_result)

                return

            # Reconstruct the rebalance plan for execution
            rebalance_plan = RebalancePlan.model_validate(rebalance_plan_data)

            # Execute the rebalance plan
            self.logger.info(f"🚀 Executing trades: {len(rebalance_plan.items)} items")

            execution_settings = self.container.config.execution()

            # Create execution manager directly from infrastructure (like other handlers)
            from the_alchemiser.execution_v2.core.execution_manager import (
                ExecutionManager,
            )
            from the_alchemiser.execution_v2.core.smart_execution_strategy import (
                ExecutionConfig,
            )

            execution_manager = ExecutionManager(
                alpaca_manager=self.container.infrastructure.alpaca_manager(),
                execution_config=ExecutionConfig(),
            )

            try:
                execution_result = execution_manager.execute_rebalance_plan(rebalance_plan)
            finally:
                # Always cleanup execution resources, including WebSocket connections
                execution_manager.shutdown()

            # Note: ExecutionResult.metadata is read-only (frozen), so strategy attribution
            # needs to be handled in the ExecutionManager itself via rebalance plan metadata

            # Log execution results
            self.logger.info(
                f"✅ Trade execution completed: {execution_result.orders_succeeded}/"
                f"{execution_result.orders_placed} orders succeeded (status: {execution_result.status.value})"
            )

            # Determine workflow success based on execution status
            treat_partial_as_failure = execution_settings.treat_partial_execution_as_failure

            if execution_result.status == ExecutionStatus.SUCCESS:
                execution_success = True
            elif execution_result.status == ExecutionStatus.PARTIAL_SUCCESS:
                execution_success = not treat_partial_as_failure
                if treat_partial_as_failure:
                    self.logger.warning(
                        f"⚠️ Partial execution treated as workflow failure: "
                        f"{execution_result.orders_succeeded}/{execution_result.orders_placed} orders succeeded"
                    )
            else:  # ExecutionStatus.FAILURE
                execution_success = False

            # Emit TradeExecuted event with execution status information
            self._emit_trade_executed_event(execution_result, success=execution_success)

            # Emit WorkflowCompleted event if successful
            if execution_success:
                self._emit_workflow_completed_event(event.correlation_id, execution_result)
            else:
                # Emit failure with detailed status information
                failure_reason = self._build_failure_reason(execution_result)
                self._emit_workflow_failure(event, failure_reason)

        except Exception as e:
            self.logger.error(f"Trade execution failed: {e}")
            self._emit_workflow_failure(event, str(e))

    def _emit_trade_executed_event(
        self, execution_result: ExecutionResult, *, success: bool
    ) -> None:
        """Emit TradeExecuted event.

        Args:
            execution_result: Execution result data
            success: Whether the execution was successful

        """
        try:
            # Build failure details if execution was not successful
            failure_reason = None
            failed_symbols: list[str] = []
            if not success:
                failure_reason = self._build_failure_reason(execution_result)
                failed_orders = [order for order in execution_result.orders if not order.success]
                failed_symbols = [order.symbol for order in failed_orders]

            event = TradeExecuted(
                correlation_id=execution_result.correlation_id,
                causation_id=execution_result.correlation_id,  # This is the continuation of the workflow
                event_id=f"trade-executed-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module=EXECUTION_HANDLERS_MODULE,
                source_component="TradingExecutionHandler",
                execution_data={
                    "plan_id": execution_result.plan_id,
                    "orders_placed": execution_result.orders_placed,
                    "orders_succeeded": execution_result.orders_succeeded,
                    "total_trade_value": str(execution_result.total_trade_value),
                    "execution_timestamp": execution_result.execution_timestamp.isoformat(),
                    "success": execution_result.success,
                    "orders": [order.model_dump() for order in execution_result.orders],
                },
                success=success,
                orders_placed=execution_result.orders_placed,
                orders_succeeded=execution_result.orders_succeeded,
                metadata={
                    "execution_timestamp": datetime.now(UTC).isoformat(),
                    "source": "event_driven_handler",
                },
                failure_reason=failure_reason,
                failed_symbols=failed_symbols,
            )

            self.event_bus.publish(event)
            self.logger.info(
                f"📡 Emitted TradeExecuted event - "
                f"{execution_result.orders_succeeded}/{execution_result.orders_placed} orders"
            )

        except Exception as e:
            self.logger.error(f"Failed to emit TradeExecuted event: {e}")
            raise

    def _emit_workflow_completed_event(
        self, correlation_id: str, execution_result: ExecutionResult
    ) -> None:
        """Emit WorkflowCompleted event when trading workflow finishes successfully.

        Args:
            correlation_id: Correlation ID from the workflow
            execution_result: Execution result data

        """
        try:
            # Calculate workflow duration using workflow start timestamp from execution_result
            if (
                hasattr(execution_result, "workflow_start_timestamp")
                and execution_result.workflow_start_timestamp
            ):
                workflow_start = execution_result.workflow_start_timestamp
            else:
                # Fallback: use execution_timestamp if workflow_start_timestamp is not available
                workflow_start = execution_result.execution_timestamp
            workflow_end = datetime.now(UTC)
            workflow_duration_ms = int((workflow_end - workflow_start).total_seconds() * 1000)

            event = WorkflowCompleted(
                correlation_id=correlation_id,
                causation_id=execution_result.plan_id,
                event_id=f"workflow-completed-{uuid.uuid4()}",
                timestamp=workflow_end,
                source_module=EXECUTION_HANDLERS_MODULE,
                source_component="TradingExecutionHandler",
                workflow_type="trading",
                workflow_duration_ms=workflow_duration_ms,
                success=True,
                summary={
                    "orders_placed": execution_result.orders_placed,
                    "orders_succeeded": execution_result.orders_succeeded,
                    "total_trade_value": str(execution_result.total_trade_value),
                    "execution_plan_id": execution_result.plan_id,
                },
            )

            self.event_bus.publish(event)
            self.logger.info(
                "📡 Emitted WorkflowCompleted event - trading workflow finished successfully"
            )

        except Exception as e:
            self.logger.error(f"Failed to emit WorkflowCompleted event: {e}")
            raise

    def _emit_workflow_failure(self, original_event: BaseEvent, error_message: str) -> None:
        """Emit WorkflowFailed event when trade execution fails.

        Args:
            original_event: The event that triggered the failed operation
            error_message: Error message describing the failure

        """
        try:
            failure_event = WorkflowFailed(
                correlation_id=original_event.correlation_id,
                causation_id=original_event.event_id,
                event_id=f"workflow-failed-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module=EXECUTION_HANDLERS_MODULE,
                source_component="TradingExecutionHandler",
                workflow_type="trading_execution",
                failure_reason=error_message,
                failure_step="trade_execution",
                error_details={
                    "original_event_type": original_event.event_type,
                    "original_event_id": original_event.event_id,
                },
            )

            self.event_bus.publish(failure_event)
            self.logger.error(f"📡 Emitted WorkflowFailed event: {error_message}")

        except Exception as e:
            self.logger.error(f"Failed to emit WorkflowFailed event: {e}")

    def _build_failure_reason(self, execution_result: ExecutionResult) -> str:
        """Build detailed failure reason based on execution status.

        Args:
            execution_result: The execution result

        Returns:
            Detailed failure reason string

        """
        if execution_result.status == ExecutionStatus.PARTIAL_SUCCESS:
            failed_orders = [order for order in execution_result.orders if not order.success]
            failed_symbols = [order.symbol for order in failed_orders]
            return (
                f"Trade execution partially failed: {execution_result.orders_succeeded}/"
                f"{execution_result.orders_placed} orders succeeded. "
                f"Failed symbols: {', '.join(failed_symbols)}"
            )
        if execution_result.status == ExecutionStatus.FAILURE:
            if execution_result.orders_placed == 0:
                return "Trade execution failed: No orders were placed"
            return f"Trade execution failed: 0/{execution_result.orders_placed} orders succeeded"
        return f"Trade execution failed with status: {execution_result.status.value}"
