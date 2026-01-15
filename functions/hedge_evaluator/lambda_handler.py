"""Business Unit: hedge_evaluator | Status: current.

Lambda handler for hedge evaluator microservice.

Triggered by EventBridge when RebalancePlanned is published by portfolio.
Runs hedge evaluation and publishes HedgeEvaluationCompleted to EventBridge.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from handlers.hedge_evaluation_handler import HedgeEvaluationHandler
from wiring import register_hedge_evaluator

from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.events import BaseEvent, WorkflowFailed
from the_alchemiser.shared.events.eventbridge_publisher import (
    publish_to_eventbridge,
    unwrap_eventbridge_event,
)
from the_alchemiser.shared.events.schemas import (
    HedgeEvaluationCompleted,
    RebalancePlanned,
)
from the_alchemiser.shared.logging import configure_application_logging, get_logger
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlan
from the_alchemiser.shared.utils.timezone_utils import ensure_timezone_aware

# Initialize logging on cold start (must be before get_logger)
configure_application_logging()

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle EventBridge event for hedge evaluation.

    This handler:
    1. Unwraps the EventBridge event to get RebalancePlanned data
    2. Runs the hedge evaluation handler
    3. Publishes HedgeEvaluationCompleted (or WorkflowFailed) to EventBridge

    Args:
        event: EventBridge event containing RebalancePlanned in 'detail'
        context: Lambda context (unused)

    Returns:
        Response indicating success/failure

    """
    # Extract correlation ID for logging
    detail = unwrap_eventbridge_event(event)
    correlation_id = detail.get("correlation_id", str(uuid.uuid4()))

    logger.info(
        "HedgeEvaluator Lambda invoked",
        extra={
            "correlation_id": correlation_id,
            "event_type": event.get("detail-type", "direct"),
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

        # Reconstruct RebalancePlan from detail
        rebalance_plan_data = detail.get("rebalance_plan", {})
        rebalance_plan = RebalancePlan.from_dict(rebalance_plan_data)

        # Reconstruct RebalancePlanned event
        rebalance_event = RebalancePlanned(
            correlation_id=detail.get("correlation_id", correlation_id),
            causation_id=detail.get("causation_id", correlation_id),
            event_id=detail.get("event_id", f"rebalance-planned-{uuid.uuid4()}"),
            timestamp=timestamp,
            source_module=detail.get("source_module", "portfolio_v2"),
            source_component=detail.get("source_component"),
            rebalance_plan=rebalance_plan,
            allocation_comparison=detail.get("allocation_comparison", {}),
            trades_required=detail.get("trades_required", False),
            metadata=detail.get("metadata", {}),
        )

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

        # Run hedge evaluation
        handler.handle_event(rebalance_event)

        # Publish result to EventBridge
        if evaluation_event is not None:
            publish_to_eventbridge(evaluation_event)
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
