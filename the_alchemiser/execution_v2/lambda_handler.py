"""Business Unit: execution_v2 | Status: current.

Lambda handler for execution microservice.

Supports two execution modes based on event source:
1. Legacy mode: Triggered by SQS (standard queue) with RebalancePlanned events
   - Processes full RebalancePlan in a single Lambda invocation
   - Uses TradingExecutionHandler

2. Per-trade mode: Triggered by SQS FIFO queue with TradeMessage events
   - Processes one trade per Lambda invocation
   - Uses SingleTradeHandler
   - DynamoDB tracks run state; Notifications aggregates results

The mode is detected by examining the event source ARN:
- FIFO queue: Contains ".fifo" in ARN
- Standard queue: No ".fifo" in ARN
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from the_alchemiser.execution_v2.handlers.single_trade_handler import (
    SingleTradeHandler,
)
from the_alchemiser.execution_v2.handlers.trading_execution_handler import (
    TradingExecutionHandler,
)
from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.events import (
    BaseEvent,
    RebalancePlanned,
    TradeExecuted,
    WorkflowCompleted,
    WorkflowFailed,
)
from the_alchemiser.shared.events.eventbridge_publisher import (
    publish_to_eventbridge,
    unwrap_sqs_event,
)
from the_alchemiser.shared.logging import configure_application_logging, get_logger
from the_alchemiser.shared.schemas.common import AllocationComparison
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlan, RebalancePlanItem
from the_alchemiser.shared.services.websocket_manager import WebSocketConnectionManager
from the_alchemiser.shared.utils.timezone_utils import ensure_timezone_aware

# Initialize logging on cold start (must be before get_logger)
configure_application_logging()

logger = get_logger(__name__)


def _convert_rebalance_plan(
    plan_data: dict[str, Any], correlation_id: str, causation_id: str
) -> RebalancePlan:
    """Convert a dict representation of RebalancePlan to the actual object.

    Args:
        plan_data: Dictionary with rebalance plan data
        correlation_id: Correlation ID for the plan
        causation_id: Causation ID for the plan

    Returns:
        RebalancePlan object

    """
    # Parse timestamp
    timestamp = plan_data.get("timestamp")
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    else:
        timestamp = datetime.now(UTC)
    result_timestamp = ensure_timezone_aware(timestamp)
    if result_timestamp is None:
        result_timestamp = datetime.now(UTC)

    # Convert items
    items = []
    for item_data in plan_data.get("items", []):
        items.append(
            RebalancePlanItem(
                symbol=item_data["symbol"],
                current_weight=Decimal(str(item_data.get("current_weight", 0))),
                target_weight=Decimal(str(item_data.get("target_weight", 0))),
                weight_diff=Decimal(str(item_data.get("weight_diff", 0))),
                target_value=Decimal(str(item_data.get("target_value", 0))),
                current_value=Decimal(str(item_data.get("current_value", 0))),
                trade_amount=Decimal(str(item_data.get("trade_amount", 0))),
                action=item_data.get("action", "HOLD"),
                priority=int(item_data.get("priority", 3)),
            )
        )

    return RebalancePlan(
        correlation_id=correlation_id,
        causation_id=causation_id,
        plan_id=plan_data.get("plan_id", str(uuid.uuid4())),
        timestamp=result_timestamp,
        total_portfolio_value=Decimal(str(plan_data.get("total_portfolio_value", 0))),
        total_trade_value=Decimal(str(plan_data.get("total_trade_value", 0))),
        max_drift_tolerance=Decimal(str(plan_data.get("max_drift_tolerance", "0.05"))),
        items=items,
        metadata=plan_data.get("metadata"),
    )


def _process_single_message(detail: dict[str, Any], correlation_id: str) -> tuple[bool, str | None]:
    """Process a single SQS message for trade execution.

    Args:
        detail: The unwrapped domain event data
        correlation_id: Correlation ID for tracing

    Returns:
        Tuple of (success, error_message). success=True if processed ok.

    """
    # Create application container
    container = ApplicationContainer.create_for_environment("production")

    # Parse timestamp
    timestamp = detail.get("timestamp")
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    else:
        timestamp = datetime.now(UTC)
    timestamp = ensure_timezone_aware(timestamp)

    # Convert rebalance plan
    plan_data = detail.get("rebalance_plan", {})
    rebalance_plan = _convert_rebalance_plan(
        plan_data,
        correlation_id=correlation_id,
        causation_id=detail.get("causation_id", correlation_id),
    )

    # Convert allocation comparison using from_json_dict to handle string Decimals
    alloc_data = detail.get("allocation_comparison", {})
    allocation_comparison = AllocationComparison.from_json_dict(alloc_data)

    # Reconstruct RebalancePlanned event
    rebalance_event = RebalancePlanned(
        correlation_id=detail.get("correlation_id", correlation_id),
        causation_id=detail.get("causation_id", correlation_id),
        event_id=detail.get("event_id", f"rebalance-planned-{uuid.uuid4()}"),
        timestamp=timestamp,
        source_module=detail.get("source_module", "portfolio_v2"),
        source_component=detail.get("source_component"),
        rebalance_plan=rebalance_plan,
        allocation_comparison=allocation_comparison,
        trades_required=detail.get("trades_required", False),
        metadata=detail.get("metadata", {}),
    )

    # Create handler and execute
    handler = TradingExecutionHandler(container)

    # Capture events using mutable container
    captured: dict[str, BaseEvent | None] = {
        "trade": None,
        "completed": None,
        "failed": None,
    }

    def capture_trade(evt: BaseEvent) -> None:
        if isinstance(evt, TradeExecuted):
            captured["trade"] = evt

    def capture_completed(evt: BaseEvent) -> None:
        if isinstance(evt, WorkflowCompleted):
            captured["completed"] = evt

    def capture_failure(evt: BaseEvent) -> None:
        if isinstance(evt, WorkflowFailed):
            captured["failed"] = evt

    handler.event_bus.subscribe("TradeExecuted", capture_trade)
    handler.event_bus.subscribe("WorkflowCompleted", capture_completed)
    handler.event_bus.subscribe("WorkflowFailed", capture_failure)

    # Run trade execution
    handler.handle_event(rebalance_event)

    # Publish results to EventBridge
    trade_event = captured["trade"]
    if trade_event is not None:
        publish_to_eventbridge(trade_event)
        logger.info(
            "Trade execution completed",
            extra={
                "correlation_id": correlation_id,
                "success": getattr(trade_event, "success", None),
                "orders_placed": getattr(trade_event, "orders_placed", None),
            },
        )

    completed_event = captured["completed"]
    failed_event = captured["failed"]

    if completed_event is not None:
        publish_to_eventbridge(completed_event)
        logger.info(
            "Workflow completed successfully",
            extra={"correlation_id": correlation_id},
        )
        return (True, None)

    if failed_event is not None:
        publish_to_eventbridge(failed_event)
        failure_reason = getattr(failed_event, "failure_reason", "Unknown")
        logger.error(
            "Trade execution failed",
            extra={
                "correlation_id": correlation_id,
                "failure_reason": failure_reason,
            },
        )
        # Still consider processed (don't retry failed trades)
        return (True, None)

    return (True, None)


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle SQS event for trade execution.

    This handler:
    1. Unwraps SQS messages to get RebalancePlanned data
    2. Runs the trading execution handler for each message
    3. Publishes TradeExecuted (or WorkflowFailed) to EventBridge

    Args:
        event: SQS event containing RebalancePlanned messages
        context: Lambda context (unused)

    Returns:
        Response indicating success/failure with batch item failures for SQS

    Note:
        SQS Lambda integration supports partial batch failures. We return
        batchItemFailures to indicate which messages failed so SQS can
        retry just those messages.

    """
    # Detect execution mode from event source
    records = event.get("Records", [])
    if not records:
        logger.warning("No records in SQS event")
        return {"batchItemFailures": []}

    # Check first record's eventSourceARN to detect FIFO queue
    first_record = records[0]
    event_source_arn = first_record.get("eventSourceARN", "")
    is_fifo_queue = ".fifo" in event_source_arn

    if is_fifo_queue:
        logger.info(
            "Per-trade execution mode: Processing TradeMessage from FIFO queue",
            extra={"event_source_arn": event_source_arn, "record_count": len(records)},
        )
        return _process_fifo_trades(event, records)
    logger.info(
        "Legacy execution mode: Processing RebalancePlanned from standard queue",
        extra={"event_source_arn": event_source_arn, "record_count": len(records)},
    )
    return _process_legacy_batch(event, records)


def _process_fifo_trades(event: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    """Process TradeMessage records from SQS FIFO queue (per-trade mode).

    Each record contains a TradeMessage for a single trade.
    Uses SingleTradeHandler for execution.

    Args:
        event: Full SQS event
        records: List of SQS records

    Returns:
        Response with batch item failures for SQS

    """
    batch_item_failures: list[dict[str, str]] = []

    # Create application container
    container = ApplicationContainer.create_for_environment("production")

    # Create single trade handler
    handler = SingleTradeHandler(container)

    for record in records:
        message_id = record.get("messageId", "unknown")

        try:
            # Process the trade message
            result = handler.handle_sqs_record(record)

            if not result.get("success", False) and not result.get("skipped", False):
                logger.error(
                    "Per-trade execution failed",
                    extra={
                        "message_id": message_id,
                        "trade_id": result.get("trade_id"),
                        "error": result.get("error"),
                    },
                )
                # Mark as failed for SQS retry
                batch_item_failures.append({"itemIdentifier": message_id})
            else:
                logger.info(
                    "Per-trade execution succeeded",
                    extra={
                        "message_id": message_id,
                        "trade_id": result.get("trade_id"),
                        "symbol": result.get("symbol"),
                        "skipped": result.get("skipped", False),
                    },
                )

        except Exception as e:
            logger.error(
                "Per-trade execution raised exception",
                extra={
                    "message_id": message_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            batch_item_failures.append({"itemIdentifier": message_id})

        finally:
            # Clean up WebSocket connections after each trade
            try:
                WebSocketConnectionManager.cleanup_all_instances()
            except Exception as cleanup_error:
                logger.warning(
                    "Failed to cleanup WebSocket connections",
                    extra={"error": str(cleanup_error)},
                )

    return {"batchItemFailures": batch_item_failures}


def _process_legacy_batch(event: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    """Process RebalancePlanned records from standard SQS queue (legacy mode).

    Each record contains a RebalancePlanned event for full batch execution.
    Uses TradingExecutionHandler for execution.

    Args:
        event: Full SQS event
        records: List of SQS records

    Returns:
        Response with batch item failures for SQS

    """
    # Track failed messages for SQS batch failure reporting
    batch_item_failures: list[dict[str, str]] = []

    # Unwrap all SQS messages
    try:
        domain_events = unwrap_sqs_event(event)
    except Exception as e:
        logger.error(
            "Failed to unwrap SQS event",
            extra={"error": str(e)},
            exc_info=True,
        )
        # Return all messages as failed so they go to DLQ after retries
        return {
            "batchItemFailures": [
                {"itemIdentifier": record.get("messageId", "")} for record in records
            ]
        }

    # Process each message
    for i, detail in enumerate(domain_events):
        message_id = records[i].get("messageId", f"unknown-{i}") if i < len(records) else f"idx-{i}"
        correlation_id = detail.get("correlation_id", str(uuid.uuid4()))

        logger.info(
            "Execution Lambda processing message",
            extra={
                "correlation_id": correlation_id,
                "message_id": message_id,
            },
        )

        try:
            _process_single_message(detail, correlation_id)

        except Exception as e:
            logger.error(
                "Execution Lambda failed with exception",
                extra={
                    "correlation_id": correlation_id,
                    "message_id": message_id,
                    "error": str(e),
                },
                exc_info=True,
            )

            # Publish WorkflowFailed to EventBridge
            try:
                failure_event = WorkflowFailed(
                    correlation_id=correlation_id,
                    causation_id=detail.get("event_id", correlation_id),
                    event_id=f"workflow-failed-{uuid.uuid4()}",
                    timestamp=datetime.now(UTC),
                    source_module="execution_v2",
                    source_component="lambda_handler",
                    workflow_type="trade_execution",
                    failure_reason=str(e),
                    failure_step="trade_execution",
                    error_details={"exception_type": type(e).__name__},
                )
                publish_to_eventbridge(failure_event)
            except Exception as pub_error:
                logger.error(
                    "Failed to publish WorkflowFailed event",
                    extra={"error": str(pub_error)},
                )

            # Mark this message as failed for SQS retry
            batch_item_failures.append({"itemIdentifier": message_id})

        finally:
            # Clean up WebSocket connections to prevent connection limit exceeded errors
            # This is critical in Lambda as connections persist across warm invocations
            try:
                WebSocketConnectionManager.cleanup_all_instances(correlation_id=correlation_id)
                logger.debug(
                    "WebSocket connections cleaned up",
                    extra={"correlation_id": correlation_id},
                )
            except Exception as cleanup_error:
                logger.warning(
                    "Failed to cleanup WebSocket connections",
                    extra={"error": str(cleanup_error), "correlation_id": correlation_id},
                )

    # Return batch item failures for SQS partial batch handling
    return {"batchItemFailures": batch_item_failures}
