"""Business Unit: strategy_v2 | Status: current.

Lambda handler for strategy microservice.

Triggered by EventBridge when WorkflowStarted is published by the orchestrator.
Runs signal generation and publishes SignalGenerated to EventBridge.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.events import (
    BaseEvent,
    SignalGenerated,
    WorkflowFailed,
    WorkflowStarted,
)
from the_alchemiser.shared.events.eventbridge_publisher import (
    publish_to_eventbridge,
    unwrap_eventbridge_event,
)
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.strategy_v2.handlers.signal_generation_handler import (
    SignalGenerationHandler,
)

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle EventBridge event for signal generation.

    This handler:
    1. Unwraps the EventBridge event to get WorkflowStarted data
    2. Runs the signal generation handler
    3. Publishes SignalGenerated (or WorkflowFailed) to EventBridge

    Args:
        event: EventBridge event containing WorkflowStarted in 'detail'
        context: Lambda context (unused)

    Returns:
        Response indicating success/failure

    """
    # Extract correlation ID for logging
    detail = unwrap_eventbridge_event(event)
    correlation_id = detail.get("correlation_id", str(uuid.uuid4()))

    logger.info(
        "Strategy Lambda invoked",
        extra={
            "correlation_id": correlation_id,
            "event_type": event.get("detail-type", "direct"),
            "source": event.get("source", "unknown"),
        },
    )

    try:
        # Create application container
        container = ApplicationContainer.create_for_environment("production")

        # Create the WorkflowStarted event from the detail payload
        workflow_event = WorkflowStarted(
            correlation_id=detail.get("correlation_id", correlation_id),
            causation_id=detail.get("causation_id", correlation_id),
            event_id=detail.get("event_id", f"workflow-started-{uuid.uuid4()}"),
            timestamp=datetime.now(UTC),
            source_module=detail.get("source_module", "orchestrator"),
            source_component=detail.get("source_component"),
            workflow_type=detail.get("workflow_type", "trading"),
            requested_by=detail.get("requested_by", "orchestrator"),
            configuration=detail.get("configuration", {}),
            metadata=detail.get("metadata", {}),
        )

        # Create handler - but we'll capture the generated event instead of using EventBus
        handler = SignalGenerationHandler(container)

        # Capture the SignalGenerated event
        generated_event: SignalGenerated | None = None
        failed_event: WorkflowFailed | None = None

        def capture_signal(evt: BaseEvent) -> None:
            nonlocal generated_event
            if isinstance(evt, SignalGenerated):
                generated_event = evt

        def capture_failure(evt: BaseEvent) -> None:
            nonlocal failed_event
            if isinstance(evt, WorkflowFailed):
                failed_event = evt

        # Subscribe to capture events
        handler.event_bus.subscribe("SignalGenerated", capture_signal)
        handler.event_bus.subscribe("WorkflowFailed", capture_failure)

        # Run signal generation
        handler.handle_event(workflow_event)

        # Publish result to EventBridge
        if generated_event is not None:
            publish_to_eventbridge(generated_event)
            logger.info(
                "Signal generation completed successfully",
                extra={
                    "correlation_id": correlation_id,
                    "signal_count": generated_event.signal_count,
                },
            )
            return {
                "statusCode": 200,
                "body": {
                    "status": "success",
                    "correlation_id": correlation_id,
                    "signal_count": generated_event.signal_count,
                },
            }

        if failed_event is not None:
            publish_to_eventbridge(failed_event)
            logger.error(
                "Signal generation failed",
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
            "Signal generation completed but no event was published",
            extra={"correlation_id": correlation_id},
        )
        return {
            "statusCode": 500,
            "body": {
                "status": "error",
                "correlation_id": correlation_id,
                "error": "No SignalGenerated or WorkflowFailed event was published",
            },
        }

    except Exception as e:
        logger.error(
            "Strategy Lambda failed with exception",
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
                source_module="strategy_v2",
                source_component="lambda_handler",
                workflow_type="signal_generation",
                failure_reason=str(e),
                failure_step="signal_generation",
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
