"""Business Unit: execution_v2 | Status: current.

Lambda handler for execution microservice.

Triggered by SQS Standard queue (parallel execution) with TradeMessage events.
Multiple Lambda invocations process trades concurrently (up to 10 via
ReservedConcurrentExecutions). DynamoDB tracks run state and phase completion.

Two-phase ordering (sells before buys) is achieved via enqueue timing:
- Portfolio Lambda enqueues only SELL trades initially
- When all SELLs complete, the last Execution Lambda enqueues BUY trades
- BUYs then execute in parallel

Note: Despite env var name (EXECUTION_FIFO_QUEUE_URL), we use a Standard queue.
"""

from __future__ import annotations

from typing import Any

from handlers.single_trade_handler import SingleTradeHandler
from wiring import register_execution

from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.logging import configure_application_logging, get_logger
from the_alchemiser.shared.services.websocket_manager import WebSocketConnectionManager

# Initialize logging on cold start (must be before get_logger)
configure_application_logging()

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle SQS Standard queue event for per-trade parallel execution.

    Multiple Lambda invocations process trades concurrently (up to 10 via
    ReservedConcurrentExecutions). Two-phase ordering is achieved via enqueue
    timing, not FIFO guarantees.

    Args:
        event: SQS event containing TradeMessage records
        context: Lambda context (unused)

    Returns:
        Response with batch item failures for SQS

    Note:
        SQS Lambda integration supports partial batch failures. We return
        batchItemFailures to indicate which messages failed so SQS can
        retry just those messages.

    """
    records = event.get("Records", [])
    if not records:
        logger.warning("No records in SQS event")
        return {"batchItemFailures": []}

    event_source_arn = records[0].get("eventSourceARN", "")
    logger.info(
        "Execution Lambda processing trades",
        extra={"event_source_arn": event_source_arn, "record_count": len(records)},
    )

    batch_item_failures: list[dict[str, str]] = []

    # Create application container (minimal - no auto-wiring)
    container = ApplicationContainer()
    # Wire execution-specific dependencies
    register_execution(container)

    # Create single trade handler
    handler = SingleTradeHandler(container)

    for record in records:
        message_id = record.get("messageId", "unknown")

        try:
            # Process the trade message
            result = handler.handle_sqs_record(record)

            if not result.get("success", False) and not result.get("skipped", False):
                logger.error(
                    "Trade execution failed",
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
                    "Trade execution succeeded",
                    extra={
                        "message_id": message_id,
                        "trade_id": result.get("trade_id"),
                        "symbol": result.get("symbol"),
                        "skipped": result.get("skipped", False),
                    },
                )

        except Exception as e:
            logger.error(
                "Trade execution raised exception",
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
            # This is critical in Lambda as connections persist across warm invocations
            try:
                WebSocketConnectionManager.cleanup_all_instances()
            except Exception as cleanup_error:
                logger.warning(
                    "Failed to cleanup WebSocket connections",
                    extra={"error": str(cleanup_error)},
                )

    return {"batchItemFailures": batch_item_failures}
