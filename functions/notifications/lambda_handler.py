"""Business Unit: notifications | Status: current.

Lambda handler for event-driven notifications microservice.

Thin routing layer that delegates to handler classes in handlers/ package.
Consumes AllTradesCompleted, WorkflowFailed, HedgeEvaluationCompleted,
DataLakeUpdateCompleted, ScheduleCreated, Lambda async failures, and
CloudWatch alarm events from EventBridge.
"""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from consolidated_handler import handle_all_strategies_completed
from handlers import ErrorHandler, HedgeHandler, OperationalHandler, TradingHandler

from the_alchemiser.shared.events.eventbridge_publisher import unwrap_eventbridge_event
from the_alchemiser.shared.logging import configure_application_logging, get_logger

configure_application_logging()

logger = get_logger(__name__)

_trading = TradingHandler()
_error = ErrorHandler()
_hedge = HedgeHandler()
_operational = OperationalHandler()


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Route EventBridge events to the appropriate notification handler.

    Args:
        event: EventBridge event envelope.
        context: Lambda context.

    Returns:
        Response with status code and message.

    """
    correlation_id = str(uuid4())

    try:
        detail_type = event.get("detail-type", "")
        source = event.get("source", "")
        detail = unwrap_eventbridge_event(event)
        correlation_id = detail.get("correlation_id", correlation_id)

        logger.info(
            "Notifications Lambda invoked",
            extra={
                "correlation_id": correlation_id,
                "detail_type": detail_type,
                "source": source,
            },
        )

        if detail_type == "AllStrategiesCompleted":
            return handle_all_strategies_completed(detail, correlation_id)
        if detail_type == "AllTradesCompleted":
            return _trading.handle(detail, correlation_id)
        if detail_type == "WorkflowFailed":
            return _error.handle_workflow_failed(detail, correlation_id, source)
        if detail_type == "HedgeEvaluationCompleted":
            return _hedge.handle(detail, correlation_id)
        if detail_type == "DataLakeUpdateCompleted":
            return _operational.handle_data_lake_update(detail, correlation_id)
        if detail_type == "ScheduleCreated":
            return _operational.handle_schedule_created(detail, correlation_id)
        if detail_type == "Lambda Function Invocation Result - Failure":
            return _error.handle_lambda_async_failure(detail, correlation_id, source)
        if detail_type == "CloudWatch Alarm State Change":
            return _error.handle_cloudwatch_alarm(event, correlation_id)

        logger.debug(
            "Ignoring unsupported event type",
            extra={"correlation_id": correlation_id, "detail_type": detail_type},
        )
        return {"statusCode": 200, "body": f"Ignored event type: {detail_type}"}

    except Exception as e:
        logger.error(
            "Notifications Lambda failed",
            exc_info=True,
            extra={
                "correlation_id": correlation_id,
                "error": str(e),
                "error_type": type(e).__name__,
            },
        )
        return {"statusCode": 500, "body": f"Notification failed: {e!s}"}
