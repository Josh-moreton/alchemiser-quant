"""Business Unit: hedge_evaluator | Status: current.

Lambda handler for hedge evaluator microservice.

Triggered by EventBridge when AllTradesCompleted is published by TradeAggregator.
Evaluates actual portfolio positions and publishes HedgeEvaluationCompleted to EventBridge.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import boto3
from handlers.hedge_evaluation_handler import HedgeEvaluationHandler
from wiring import register_hedge_evaluator

from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.events import BaseEvent, WorkflowFailed
from the_alchemiser.shared.events.eventbridge_publisher import (
    DecimalEncoder,
    publish_to_eventbridge,
    unwrap_eventbridge_event,
)
from the_alchemiser.shared.events.schemas import (
    HedgeEvaluationCompleted,
)
from the_alchemiser.shared.logging import configure_application_logging, get_logger
from the_alchemiser.shared.utils.timezone_utils import ensure_timezone_aware

# Initialize logging on cold start (must be before get_logger)
configure_application_logging()

logger = get_logger(__name__)


def _is_hedging_enabled() -> bool:
    """Check if options hedging is enabled via environment variable.

    Returns:
        True if OPTIONS_HEDGING_ENABLED is set to 'true' (case-insensitive),
        False otherwise. Defaults to False for safety.

    """
    return os.environ.get("OPTIONS_HEDGING_ENABLED", "false").lower() == "true"


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle EventBridge event for hedge evaluation.

    This handler:
    1. Unwraps the EventBridge event to get AllTradesCompleted data
    2. Extracts portfolio positions from portfolio_snapshot
    3. Runs the hedge evaluation handler
    4. Publishes HedgeEvaluationCompleted (or WorkflowFailed) to EventBridge

    Args:
        event: EventBridge event containing AllTradesCompleted in 'detail'
        context: Lambda context (unused)

    Returns:
        Response indicating success/failure

    """
    # Extract correlation ID for logging
    detail = unwrap_eventbridge_event(event)
    correlation_id = detail.get("correlation_id", str(uuid.uuid4()))

    # Feature flag check - skip hedging if disabled
    if not _is_hedging_enabled():
        logger.info(
            "Options hedging DISABLED via feature flag - skipping evaluation",
            extra={
                "correlation_id": correlation_id,
                "feature_flag": "OPTIONS_HEDGING_ENABLED",
                "status": "skipped",
            },
        )
        return {
            "statusCode": 200,
            "body": {
                "status": "skipped",
                "correlation_id": correlation_id,
                "reason": "Options hedging disabled via OPTIONS_HEDGING_ENABLED feature flag",
            },
        }

    # Get event type from EventBridge envelope
    event_type = event.get("detail-type", "unknown")

    logger.info(
        "HedgeEvaluator Lambda invoked",
        extra={
            "correlation_id": correlation_id,
            "event_type": event_type,
            "source": event.get("source", "unknown"),
        },
    )

    try:
        # Create application container
        container = ApplicationContainer()
        # Wire hedge evaluator dependencies
        register_hedge_evaluator(container)

        # Parse timestamp
        timestamp = detail.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        else:
            timestamp = datetime.now(UTC)
        timestamp = ensure_timezone_aware(timestamp)

        # Create handler
        handler = HedgeEvaluationHandler(container)

        # Capture events
        evaluation_event: HedgeEvaluationCompleted | None = None
        failed_event: WorkflowFailed | None = None

        def capture_evaluation(evt: BaseEvent) -> None:
            nonlocal evaluation_event
            if isinstance(evt, HedgeEvaluationCompleted):
                evaluation_event = evt

        def capture_failure(evt: BaseEvent) -> None:
            nonlocal failed_event
            if isinstance(evt, WorkflowFailed):
                failed_event = evt

        # Subscribe to capture events
        handler.event_bus.subscribe("HedgeEvaluationCompleted", capture_evaluation)
        handler.event_bus.subscribe("WorkflowFailed", capture_failure)

        # Route based on event type
        if event_type == "AllTradesCompleted":
            # New flow: Triggered after all trades complete
            # Extract portfolio data from AllTradesCompleted event
            portfolio_snapshot = detail.get("portfolio_snapshot", {})

            if not portfolio_snapshot or "equity" not in portfolio_snapshot:
                logger.warning(
                    "No portfolio_snapshot in AllTradesCompleted - skipping hedge evaluation",
                    extra={"correlation_id": correlation_id},
                )
                return {
                    "statusCode": 200,
                    "body": {
                        "status": "skipped",
                        "correlation_id": correlation_id,
                        "reason": "No portfolio_snapshot available",
                    },
                }

            # Extract identifiers
            plan_id = detail.get("plan_id", str(uuid.uuid4()))
            run_id = detail.get("run_id", "")

            # Get equity (NAV) from portfolio snapshot
            portfolio_nav = Decimal(str(portfolio_snapshot.get("equity", 0)))

            if portfolio_nav <= 0:
                logger.warning(
                    "Zero or negative portfolio NAV - skipping hedge evaluation",
                    extra={"correlation_id": correlation_id, "nav": str(portfolio_nav)},
                )
                return {
                    "statusCode": 200,
                    "body": {
                        "status": "skipped",
                        "correlation_id": correlation_id,
                        "reason": "Invalid portfolio NAV",
                    },
                }

            # Call handler with AllTradesCompleted data
            handler.handle_all_trades_completed(
                correlation_id=correlation_id,
                causation_id=detail.get("event_id", correlation_id),
                plan_id=plan_id,
                run_id=run_id,
                portfolio_nav=portfolio_nav,
                portfolio_snapshot=portfolio_snapshot,
                timestamp=timestamp,
            )
        else:
            # Unknown event type
            logger.error(
                "Unsupported event type for hedge evaluation",
                extra={
                    "correlation_id": correlation_id,
                    "event_type": event_type,
                    "expected": "AllTradesCompleted",
                },
            )
            return {
                "statusCode": 400,
                "body": {
                    "status": "error",
                    "correlation_id": correlation_id,
                    "error": f"Unsupported event type: {event_type}. Expected AllTradesCompleted.",
                },
            }

        # Publish result to EventBridge and SQS
        if evaluation_event is not None:
            publish_to_eventbridge(evaluation_event)

            # Send to HedgeExecutionQueue to trigger hedge executor
            queue_url = os.environ.get("HEDGE_EXECUTION_QUEUE_URL")
            if queue_url:
                sqs_client = boto3.client("sqs")
                sqs_client.send_message(
                    QueueUrl=queue_url,
                    MessageBody=json.dumps(
                        evaluation_event.model_dump(mode="json"),
                        cls=DecimalEncoder,
                    ),
                )
                logger.info(
                    "Sent HedgeEvaluationCompleted to execution queue",
                    extra={
                        "correlation_id": correlation_id,
                        "queue_url": queue_url,
                    },
                )
            else:
                logger.warning(
                    "HEDGE_EXECUTION_QUEUE_URL not set, skipping SQS send",
                    extra={"correlation_id": correlation_id},
                )

            logger.info(
                "Hedge evaluation completed successfully",
                extra={
                    "correlation_id": correlation_id,
                    "recommendations_count": len(evaluation_event.recommendations),
                    "premium_budget": str(evaluation_event.total_premium_budget),
                },
            )
            return {
                "statusCode": 200,
                "body": {
                    "status": "success",
                    "correlation_id": correlation_id,
                    "recommendations_count": len(evaluation_event.recommendations),
                    "premium_budget": str(evaluation_event.total_premium_budget),
                },
            }

        if failed_event is not None:
            publish_to_eventbridge(failed_event)
            logger.error(
                "Hedge evaluation failed",
                extra={
                    "correlation_id": correlation_id,
                    "failure_reason": failed_event.failure_reason,
                },
            )
            return {
                "statusCode": 500,
                "body": {
                    "status": "failed",
                    "correlation_id": correlation_id,
                    "error": failed_event.failure_reason,
                },
            }

        # No event captured - unexpected state
        logger.error(
            "Hedge evaluation completed but no event was published",
            extra={"correlation_id": correlation_id},
        )
        return {
            "statusCode": 500,
            "body": {
                "status": "error",
                "correlation_id": correlation_id,
                "error": "No HedgeEvaluationCompleted or WorkflowFailed event was published",
            },
        }

    except Exception as e:
        logger.error(
            "HedgeEvaluator Lambda failed with exception",
            extra={"correlation_id": correlation_id, "error": str(e)},
            exc_info=True,
        )

        # Publish WorkflowFailed to EventBridge
        try:
            failure_event = WorkflowFailed(
                correlation_id=correlation_id,
                causation_id=detail.get("event_id", correlation_id),
                event_id=f"workflow-failed-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="hedge_evaluator",
                source_component="lambda_handler",
                workflow_type="hedge_evaluation",
                failure_reason=str(e),
                failure_step="hedge_evaluation",
                error_details={"exception_type": type(e).__name__},
            )
            publish_to_eventbridge(failure_event)
        except Exception as pub_error:
            logger.error(
                "Failed to publish WorkflowFailed event",
                extra={"error": str(pub_error)},
            )

        return {
            "statusCode": 500,
            "body": {
                "status": "error",
                "correlation_id": correlation_id,
                "error": str(e),
            },
        }
