"""Business Unit: strategy_v2 | Status: current.

Lambda handler for strategy microservice.

This is the entry point for the trading workflow. It can be triggered by:
1. EventBridge Schedule (daily at market open)
2. Manual invocation for testing

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
)
from the_alchemiser.shared.logging import configure_application_logging, get_logger
from the_alchemiser.strategy_v2.handlers.signal_generation_handler import (
    SignalGenerationHandler,
)

configure_application_logging()
logger = get_logger(__name__)


def _check_market_status(container: ApplicationContainer, correlation_id: str) -> tuple[bool, str]:
    """Check if market is currently open.

    Args:
        container: Application container with Alpaca client
        correlation_id: Correlation ID for logging

    Returns:
        Tuple of (is_open, status_string)

    """
    try:
        trading_client = container.infrastructure.alpaca_manager().trading_client
        clock = trading_client.get_clock()
        is_open = clock.is_open
        status = "open" if is_open else "closed"

        if not is_open:
            logger.warning(
                "Market is closed - signal generation will proceed but orders skipped",
                extra={"correlation_id": correlation_id, "market_status": status},
            )
        else:
            logger.info(
                "Market is open - full trading workflow will execute",
                extra={"correlation_id": correlation_id, "market_status": status},
            )
        return is_open, status
    except Exception as e:
        logger.warning(
            "Market status check failed, proceeding anyway",
            extra={"correlation_id": correlation_id, "error": str(e)},
        )
        return False, "unknown"


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle scheduled or manual invocation for signal generation.

    This handler:
    1. Checks market status via Alpaca clock
    2. Runs the signal generation handler
    3. Publishes SignalGenerated (or WorkflowFailed) to EventBridge

    Args:
        event: Lambda event (from schedule or manual invocation)
        context: Lambda context

    Returns:
        Response indicating success/failure

    """
    # Generate correlation ID for this workflow
    correlation_id = event.get("correlation_id") or f"workflow-{uuid.uuid4()}"

    logger.info(
        "Strategy Lambda invoked - workflow entry point",
        extra={
            "correlation_id": correlation_id,
            "event_source": event.get("source", "schedule"),
        },
    )

    try:
        # Create application container
        container = ApplicationContainer.create_for_environment("production")

        # Check market status
        market_is_open, market_status = _check_market_status(container, correlation_id)

        # Create the WorkflowStarted event (used internally by handler)
        workflow_event = WorkflowStarted(
            correlation_id=correlation_id,
            causation_id=f"schedule-{datetime.now(UTC).isoformat()}",
            event_id=f"workflow-started-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="strategy_v2.lambda_handler",
            source_component="StrategyLambda",
            workflow_type="trading",
            requested_by="EventBridgeSchedule",
            configuration={
                "live_trading": not container.config.paper_trading(),
                "market_is_open": market_is_open,
                "market_status": market_status,
            },
        )

        # Create handler
        handler = SignalGenerationHandler(container)

        # Capture the generated event
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
                    "market_status": market_status,
                },
            )
            return {
                "statusCode": 200,
                "body": {
                    "status": "success",
                    "correlation_id": correlation_id,
                    "signal_count": generated_event.signal_count,
                    "market_status": market_status,
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
                causation_id=correlation_id,
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
