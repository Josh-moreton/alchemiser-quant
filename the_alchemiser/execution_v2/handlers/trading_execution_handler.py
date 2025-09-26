#!/usr/bin/env python3
"""Business Unit: execution | Status: current.

Trading execution event handler for event-driven architecture.

Processes RebalancePlanned events to execute trades and emit TradeExecuted events.
This handler is stateless and focuses on trade execution logic without orchestration concerns.
Implements idempotent execution through persistent tracking and DTO adapters.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer

from the_alchemiser.execution_v2.adapters.alpaca_execution_adapter import (
    AlpacaExecutionAdapter,
)
from the_alchemiser.execution_v2.models.execution_result import (
    ExecutionResultDTO,
    ExecutionStatus,
)
from the_alchemiser.execution_v2.utils.execution_idempotency import (
    ExecutionIdempotencyStore,
    generate_execution_plan_hash,
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
from the_alchemiser.shared.logging.logging_utils import get_logger
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlanDTO


class TradingExecutionHandler:
    """Event handler for trading execution.

    Handles RebalancePlanned events by executing trades through DTO adapters
    and emitting enriched TradeExecuted events with idempotent behavior.
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

        # Initialize execution adapter with AlpacaManager
        self._execution_adapter = AlpacaExecutionAdapter(
            alpaca_manager=container.infrastructure.alpaca_manager()
        )

        # Initialize idempotency store
        self._idempotency_store = ExecutionIdempotencyStore(
            persistence_handler=container.services.persistence_handler()
        )

    def handle_event(self, event: BaseEvent) -> None:
        """Handle incoming events.

        Args:
            event: The event to handle

        """
        if isinstance(event, RebalancePlanned):
            self._handle_rebalance_planned(event)
        else:
            self.logger.warning(f"Unhandled event type: {type(event).__name__}")

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
        """Handle RebalancePlanned event by executing trades with idempotency.

        Args:
            event: The RebalancePlanned event

        """
        self.logger.info(
            "🔄 Starting trade execution from RebalancePlanned event",
            extra={
                "correlation_id": event.correlation_id,
                "causation_id": event.causation_id,
                "module": "execution_v2.handlers",
            },
        )

        try:
            # Reconstruct RebalancePlanDTO from event data
            rebalance_plan_data = event.rebalance_plan
            rebalance_plan = RebalancePlanDTO.model_validate(rebalance_plan_data)

            # Generate execution plan hash for idempotency
            execution_plan_hash = generate_execution_plan_hash(rebalance_plan, event.correlation_id)

            # Check if this execution has already been attempted
            if self._idempotency_store.has_been_executed(event.correlation_id, execution_plan_hash):
                self.logger.info(
                    "⏭️ Execution already attempted - skipping duplicate",
                    extra={
                        "correlation_id": event.correlation_id,
                        "execution_plan_hash": execution_plan_hash,
                        "module": "execution_v2.handlers",
                    },
                )
                return

            # Handle no-trade scenario
            if not event.trades_required or not rebalance_plan_data.items:
                self.logger.info(
                    "📊 No significant trades needed - portfolio already balanced",
                    extra={
                        "correlation_id": event.correlation_id,
                        "module": "execution_v2.handlers",
                    },
                )

                # Create empty execution result
                execution_result = ExecutionResultDTO(
                    success=True,
                    status=ExecutionStatus.SUCCESS,
                    plan_id=rebalance_plan_data.plan_id,
                    correlation_id=event.correlation_id,
                    orders=[],
                    orders_placed=0,
                    orders_succeeded=0,
                    total_trade_value=DECIMAL_ZERO,
                    execution_timestamp=datetime.now(UTC),
                    metadata={
                        "scenario": "no_trades_needed",
                        "execution_plan_hash": execution_plan_hash,
                    },
                )

                # Record the attempt
                self._idempotency_store.record_execution_attempt(
                    correlation_id=event.correlation_id,
                    execution_plan_hash=execution_plan_hash,
                    success=True,
                    metadata={"scenario": "no_trades_needed"},
                )

                # Emit successful trade executed event
                self._emit_trade_executed_event(execution_result, execution_plan_hash, success=True)

                # Emit workflow completed event
                self._emit_workflow_completed_event(event.correlation_id, execution_result)

                return

            # Execute the rebalance plan via adapter
            self.logger.info(
                f"🚀 Executing trades: {len(rebalance_plan.items)} items",
                extra={
                    "correlation_id": event.correlation_id,
                    "plan_id": rebalance_plan.plan_id,
                    "order_count": len(rebalance_plan.items),
                    "module": "execution_v2.handlers",
                },
            )

            # Execute through DTO adapter
            execution_result = self._execution_adapter.execute_orders(rebalance_plan)

            # Update correlation_id in result to match event
            execution_result = execution_result.model_copy(
                update={
                    "correlation_id": event.correlation_id,
                    "metadata": {
                        **(execution_result.metadata or {}),
                        "execution_plan_hash": execution_plan_hash,
                    },
                }
            )

            # Record the execution attempt
            self._idempotency_store.record_execution_attempt(
                correlation_id=event.correlation_id,
                execution_plan_hash=execution_plan_hash,
                success=execution_result.success,
                metadata={
                    "orders_placed": execution_result.orders_placed,
                    "orders_succeeded": execution_result.orders_succeeded,
                    "total_trade_value": str(execution_result.total_trade_value),
                },
            )

            # Log execution results
            self.logger.info(
                f"✅ Trade execution completed: {execution_result.orders_succeeded}/"
                f"{execution_result.orders_placed} orders succeeded (status: {execution_result.status.value})",
                extra={
                    "correlation_id": event.correlation_id,
                    "execution_plan_hash": execution_plan_hash,
                    "success": execution_result.success,
                    "module": "execution_v2.handlers",
                },
            )

            # Determine workflow success based on execution status
            # For now, treat partial success as workflow failure (can be configurable in future)
            treat_partial_as_failure = True  # TODO: Make this configurable

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

            # Emit TradeExecuted event with enriched metadata
            self._emit_trade_executed_event(
                execution_result, execution_plan_hash, success=execution_success
            )

            # Emit WorkflowCompleted event if successful
            if execution_success:
                self._emit_workflow_completed_event(event.correlation_id, execution_result)
            else:
                # Emit failure with detailed status information
                failure_reason = self._build_failure_reason(execution_result)
                self._emit_workflow_failure(event, failure_reason)

        except Exception as e:
            self.logger.error(
                f"Trade execution failed: {e}",
                extra={
                    "correlation_id": event.correlation_id,
                    "error": str(e),
                    "module": "execution_v2.handlers",
                },
            )
            self._emit_workflow_failure(event, str(e))

    def _emit_trade_executed_event(
        self,
        execution_result: ExecutionResultDTO,
        execution_plan_hash: str,
        *,
        success: bool,
    ) -> None:
        """Emit enriched TradeExecuted event with settlement metadata.

        Args:
            execution_result: Execution result data
            execution_plan_hash: Hash of the execution plan
            success: Whether the execution was successful

        """
        try:
            # Generate fill summaries from order results
            fill_summaries = {
                order.symbol: {
                    "filled_shares": str(order.shares),
                    "fill_price": str(order.price) if order.price else None,
                    "fill_value": str(order.trade_amount),
                    "success": order.success,
                }
                for order in execution_result.orders
            }

            # Create settlement details
            settlement_details = {
                "settlement_type": "immediate",  # Assuming immediate settlement
                "total_orders": execution_result.orders_placed,
                "successful_orders": execution_result.orders_succeeded,
                "failed_orders": execution_result.orders_placed - execution_result.orders_succeeded,
                "total_settled_value": str(execution_result.total_trade_value),
            }

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
                # Enhanced metadata fields
                schema_version="1.0",
                execution_plan_hash=execution_plan_hash,
                fill_summaries=fill_summaries,
                settlement_details=settlement_details,
                metadata={
                    "adapter_used": "AlpacaExecutionAdapter",
                    "idempotency_enabled": True,
                    **(execution_result.metadata or {}),
                },
            )

            self.event_bus.publish(event)

            self.logger.info(
                f"📤 TradeExecuted event emitted (alias: {event.settlement_event_type})",
                extra={
                    "correlation_id": execution_result.correlation_id,
                    "event_id": event.event_id,
                    "execution_plan_hash": execution_plan_hash,
                    "module": "execution_v2.handlers",
                },
            )

        except Exception as e:
            self.logger.error(
                f"Failed to emit TradeExecuted event: {e}",
                extra={
                    "correlation_id": execution_result.correlation_id,
                    "error": str(e),
                    "module": "execution_v2.handlers",
                },
            )

    def _emit_workflow_completed_event(
        self, correlation_id: str, execution_result: ExecutionResultDTO
    ) -> None:
        """Emit WorkflowCompleted event.

        Args:
            correlation_id: The correlation ID from the original event
            execution_result: Execution result data

        """
        try:
            # Calculate workflow duration using workflow start timestamp from execution_result if available
            if (
                hasattr(execution_result, "workflow_start_timestamp")
                and execution_result.workflow_start_timestamp  # type: ignore[attr-defined]
            ):
                workflow_start = execution_result.workflow_start_timestamp  # type: ignore[attr-defined]
            else:
                # Fallback: use execution_timestamp if workflow_start_timestamp is not available
                workflow_start = execution_result.execution_timestamp
            workflow_end = datetime.now(UTC)
            workflow_duration_ms = int((workflow_end - workflow_start).total_seconds() * 1000)
            event = WorkflowCompleted(
                correlation_id=correlation_id,
                causation_id=correlation_id,
                event_id=f"workflow-completed-{uuid.uuid4()}",
                timestamp=workflow_end,
                source_module=EXECUTION_HANDLERS_MODULE,
                source_component="TradingExecutionHandler",
                workflow_type="trade_execution",
                workflow_duration_ms=workflow_duration_ms,
                success=True,
                summary={
                    "orders_placed": execution_result.orders_placed,
                    "orders_succeeded": execution_result.orders_succeeded,
                    "total_trade_value": str(execution_result.total_trade_value),
                    "plan_id": execution_result.plan_id,
                },
            )

            self.event_bus.publish(event)

            self.logger.info(
                "📤 WorkflowCompleted event emitted",
                extra={
                    "correlation_id": correlation_id,
                    "event_id": event.event_id,
                    "module": "execution_v2.handlers",
                },
            )

        except Exception as e:
            self.logger.error(
                f"Failed to emit WorkflowCompleted event: {e}",
                extra={
                    "correlation_id": correlation_id,
                    "error": str(e),
                    "module": "execution_v2.handlers",
                },
            )

    def _emit_workflow_failure(self, original_event: BaseEvent, error_message: str) -> None:
        """Emit WorkflowFailed event when trade execution fails.

        Args:
            original_event: The original event that triggered the workflow
            error_message: Description of the failure

        """
        try:
            event = WorkflowFailed(
                correlation_id=original_event.correlation_id,
                causation_id=original_event.event_id,
                event_id=f"workflow-failed-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module=EXECUTION_HANDLERS_MODULE,
                source_component="TradingExecutionHandler",
                workflow_type="trade_execution",
                failure_reason=error_message,
                failure_step="trade_execution",
                error_details={
                    "original_event_type": original_event.event_type,
                    "plan_id": getattr(original_event.rebalance_plan, "plan_id", "unknown"),
                },
            )

            self.event_bus.publish(event)

            self.logger.error(
                "📤 WorkflowFailed event emitted",
                extra={
                    "correlation_id": original_event.correlation_id,
                    "event_id": event.event_id,
                    "error": error_message,
                    "module": "execution_v2.handlers",
                },
            )

        except Exception as e:
            self.logger.error(
                f"Failed to emit WorkflowFailed event: {e}",
                extra={
                    "correlation_id": original_event.correlation_id,
                    "error": str(e),
                    "module": "execution_v2.handlers",
                },
            )

    def _build_failure_reason(self, execution_result: ExecutionResultDTO) -> str:
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
