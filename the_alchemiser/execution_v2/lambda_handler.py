"""Business Unit: execution_v2 | Status: current.

Lambda handler for execution microservice.

Supports two invocation modes:

1. **SQS Trigger (TradeMessage)**: Initiates time-aware execution for new trades.
   The trade is registered as a PendingExecution and processing begins based
   on current market phase.

2. **EventBridge Scheduler Tick**: Processes all pending executions.
   Runs every 10 minutes during market hours to:
   - Detect current execution phase
   - Compute urgency scores
   - Manage child orders (cancel stale, submit new)
   - Handle closing auction (CLS) order submission

The time-aware execution framework replaces the urgency-biased walk-the-book
approach with institutional-style, time-phased execution that:
- Avoids aggressive trading during market open
- Uses passive pegs during midday
- Increases urgency only as deadline approaches
- Supports MOC/LOC via Alpaca's CLS time-in-force
"""

from __future__ import annotations

import asyncio
from typing import Any

from the_alchemiser.execution_v2.time_aware.execution_service import (
    TimeAwareExecutionService,
)
from the_alchemiser.execution_v2.time_aware.pending_execution_repository import (
    PendingExecutionRepository,
)
from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.logging import configure_application_logging, get_logger
from the_alchemiser.shared.schemas.trade_message import TradeMessage
from the_alchemiser.shared.services.websocket_manager import WebSocketConnectionManager

# Initialize logging on cold start (must be before get_logger)
configure_application_logging()

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle execution Lambda invocations.

    Supports two invocation patterns:

    1. SQS Event (Records present): Process new TradeMessage, initiate execution
    2. Scheduler Tick (tick_type present): Process all pending executions

    Args:
        event: SQS event or EventBridge Scheduler event
        context: Lambda context (unused)

    Returns:
        Response with batch item failures (SQS) or tick results (Scheduler)

    """
    # Detect invocation type
    if "Records" in event:
        return _handle_sqs_event(event)
    if event.get("tick_type") == "time_aware_execution":
        return _handle_execution_tick(event)
    logger.warning(
        "Unknown event type",
        extra={"event_keys": list(event.keys())},
    )
    return {"statusCode": 400, "body": "Unknown event type"}


def _handle_sqs_event(event: dict[str, Any]) -> dict[str, Any]:
    """Handle SQS event containing TradeMessage records.

    Each TradeMessage initiates a new time-aware execution.
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

    # Create application container
    container = ApplicationContainer.create_for_environment("production")

    # Create time-aware execution service using container's AlpacaManager
    alpaca_manager = container.alpaca_manager()
    repository = PendingExecutionRepository()
    time_aware_service = TimeAwareExecutionService(
        alpaca_manager=alpaca_manager,
        repository=repository,
    )

    for record in records:
        message_id = record.get("messageId", "unknown")

        try:
            # Parse TradeMessage from SQS body
            import json

            body = json.loads(record.get("body", "{}"))
            trade_message = TradeMessage.model_validate(body)

            logger.info(
                "Initiating time-aware execution",
                extra={
                    "message_id": message_id,
                    "trade_id": trade_message.trade_id,
                    "symbol": trade_message.symbol,
                    "side": trade_message.side,
                    "quantity": str(trade_message.quantity),
                },
            )

            # Initiate time-aware execution
            execution = asyncio.get_event_loop().run_until_complete(
                time_aware_service.initiate_execution(trade_message)
            )

            logger.info(
                "Time-aware execution initiated",
                extra={
                    "message_id": message_id,
                    "execution_id": execution.execution_id,
                    "state": execution.state.value,
                    "current_phase": execution.current_phase.value,
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
            try:
                WebSocketConnectionManager.cleanup_all_instances()
            except Exception as cleanup_error:
                logger.warning(
                    "Failed to cleanup WebSocket connections",
                    extra={"error": str(cleanup_error)},
                )

    return {"batchItemFailures": batch_item_failures}


def _handle_execution_tick(event: dict[str, Any]) -> dict[str, Any]:
    """Handle scheduled execution tick.

    Processes all pending executions based on current market phase and urgency.
    """
    logger.info(
        "Processing execution tick",
        extra={"tick_type": event.get("tick_type")},
    )

    try:
        # Create application container
        container = ApplicationContainer.create_for_environment("production")

        # Create time-aware execution service using container's AlpacaManager
        alpaca_manager = container.alpaca_manager()
        repository = PendingExecutionRepository()
        time_aware_service = TimeAwareExecutionService(
            alpaca_manager=alpaca_manager,
            repository=repository,
        )

        # Process all pending executions
        results = asyncio.get_event_loop().run_until_complete(time_aware_service.process_tick())

        logger.info(
            "Execution tick complete",
            extra={
                "executions_processed": len(results),
                "results": results,
            },
        )

        return {
            "statusCode": 200,
            "body": {
                "tick_type": "time_aware_execution",
                "executions_processed": len(results),
                "results": results,
            },
        }

    except Exception as e:
        logger.error(
            "Execution tick failed",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        return {
            "statusCode": 500,
            "body": {"error": str(e)},
        }

    finally:
        # Clean up WebSocket connections
        try:
            WebSocketConnectionManager.cleanup_all_instances()
        except Exception as cleanup_error:
            logger.warning(
                "Failed to cleanup WebSocket connections",
                extra={"error": str(cleanup_error)},
            )
