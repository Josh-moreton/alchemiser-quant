"""Business Unit: portfolio_v2 | Status: current.

Lambda handler for portfolio microservice.

Triggered by EventBridge when SignalGenerated is published by strategy.
Runs portfolio analysis and publishes RebalancePlanned to EventBridge.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from handlers.portfolio_analysis_handler import PortfolioAnalysisHandler
from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.events import (
    BaseEvent,
    RebalancePlanned,
    SignalGenerated,
    WorkflowFailed,
)
from the_alchemiser.shared.events.eventbridge_publisher import (
    publish_to_eventbridge,
    unwrap_eventbridge_event,
)
from the_alchemiser.shared.logging import configure_application_logging, get_logger
from the_alchemiser.shared.utils.timezone_utils import ensure_timezone_aware

# Initialize logging on cold start (must be before get_logger)
configure_application_logging()

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle EventBridge event for portfolio analysis.

    This handler:
    1. Unwraps the EventBridge event to get SignalGenerated data
    2. Runs the portfolio analysis handler
    3. Publishes RebalancePlanned (or WorkflowFailed) to EventBridge

    Args:
        event: EventBridge event containing SignalGenerated in 'detail'
        context: Lambda context (unused)

    Returns:
        Response indicating success/failure

    """
    # Extract correlation ID for logging
    detail = unwrap_eventbridge_event(event)
    correlation_id = detail.get("correlation_id", str(uuid.uuid4()))

    logger.info(
        "Portfolio Lambda invoked",
        extra={
            "correlation_id": correlation_id,
            "event_type": event.get("detail-type", "direct"),
            "source": event.get("source", "unknown"),
        },
    )

    try:
        # Create application container
        container = ApplicationContainer.create_for_environment("production")

        # Parse timestamp if string
        timestamp = detail.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        else:
            timestamp = datetime.now(UTC)
        timestamp = ensure_timezone_aware(timestamp)

        # Reconstruct SignalGenerated event from the detail payload
        signal_event = SignalGenerated(
            correlation_id=detail.get("correlation_id", correlation_id),
            causation_id=detail.get("causation_id", correlation_id),
            event_id=detail.get("event_id", f"signal-generated-{uuid.uuid4()}"),
            timestamp=timestamp,
            source_module=detail.get("source_module", "strategy_v2"),
            source_component=detail.get("source_component"),
            signals_data=detail.get("signals_data", {}),
            consolidated_portfolio=detail.get("consolidated_portfolio", {}),
            signal_count=detail.get("signal_count", 0),
            metadata=detail.get("metadata", {}),
        )

        # Create handler - but we'll capture the generated event instead of using EventBus
        handler = PortfolioAnalysisHandler(container)

        # Capture the RebalancePlanned event
        generated_event: RebalancePlanned | None = None
        failed_event: WorkflowFailed | None = None

        def capture_rebalance(evt: BaseEvent) -> None:
            nonlocal generated_event
            if isinstance(evt, RebalancePlanned):
                generated_event = evt

        def capture_failure(evt: BaseEvent) -> None:
            nonlocal failed_event
            if isinstance(evt, WorkflowFailed):
                failed_event = evt

        # Subscribe to capture events
        handler.event_bus.subscribe("RebalancePlanned", capture_rebalance)
        handler.event_bus.subscribe("WorkflowFailed", capture_failure)

        # Run portfolio analysis
        handler.handle_event(signal_event)

        # Publish result to EventBridge
        if generated_event is not None:
            publish_to_eventbridge(generated_event)
            logger.info(
                "Portfolio analysis completed successfully",
                extra={
                    "correlation_id": correlation_id,
                    "trades_required": generated_event.trades_required,
                },
            )
            return {
                "statusCode": 200,
                "body": {
                    "status": "success",
                    "correlation_id": correlation_id,
                    "trades_required": generated_event.trades_required,
                },
            }

        if failed_event is not None:
            publish_to_eventbridge(failed_event)
            logger.error(
                "Portfolio analysis failed",
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
            "Portfolio analysis completed but no event was published",
            extra={"correlation_id": correlation_id},
        )
        return {
            "statusCode": 500,
            "body": {
                "status": "error",
                "correlation_id": correlation_id,
                "error": "No RebalancePlanned or WorkflowFailed event was published",
            },
        }

    except Exception as e:
        logger.error(
            "Portfolio Lambda failed with exception",
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
                source_module="portfolio_v2",
                source_component="lambda_handler",
                workflow_type="portfolio_analysis",
                failure_reason=str(e),
                failure_step="portfolio_analysis",
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
