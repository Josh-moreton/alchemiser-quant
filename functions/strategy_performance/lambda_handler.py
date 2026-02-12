"""Business Unit: strategy_performance | Status: current.

Lambda handler for strategy performance metrics.

Consumes TradeExecuted events from EventBridge and writes per-strategy
performance metrics to DynamoDB for dashboard consumption.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from handlers.metrics_handler import MetricsHandler

from the_alchemiser.shared.events.eventbridge_publisher import unwrap_eventbridge_event
from the_alchemiser.shared.logging import configure_application_logging, get_logger

# Initialize logging on cold start
configure_application_logging()

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle TradeExecuted events and write performance metrics to DynamoDB.

    Args:
        event: EventBridge event containing TradeExecuted details
        context: Lambda context

    Returns:
        Response with status code and message

    """
    correlation_id = str(uuid4())

    try:
        detail_type = event.get("detail-type", "")
        detail = unwrap_eventbridge_event(event)
        correlation_id = detail.get("correlation_id", correlation_id)

        logger.info(
            "Strategy performance Lambda invoked",
            extra={
                "correlation_id": correlation_id,
                "detail_type": detail_type,
                "source": event.get("source", ""),
            },
        )

        if detail_type != "TradeExecuted":
            return {"statusCode": 200, "body": f"Ignored event type: {detail_type}"}

        handler = MetricsHandler()
        return handler.handle(detail, correlation_id)

    except Exception as e:
        logger.error(
            "Strategy performance Lambda failed",
            exc_info=True,
            extra={
                "correlation_id": correlation_id,
                "error_type": type(e).__name__,
                "error": str(e),
            },
        )
        return {"statusCode": 500, "body": f"Metrics writing failed: {e!s}"}
