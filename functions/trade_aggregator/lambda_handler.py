"""Business Unit: trade_aggregator | Status: current.

Lambda handler for Trade Aggregator microservice.

The TradeAggregator collects TradeExecuted events from parallel execution
invocations and emits a single AllTradesCompleted event when all trades
in a run finish. This eliminates race conditions in notifications.

Trigger: EventBridge rule matching TradeExecuted events.
"""

from __future__ import annotations

from typing import Any

from handlers import AggregationHandler

from the_alchemiser.shared.events.eventbridge_publisher import unwrap_eventbridge_event
from the_alchemiser.shared.logging import configure_application_logging, get_logger

configure_application_logging()

logger = get_logger(__name__)

_handler = AggregationHandler()


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Route TradeExecuted events to the aggregation handler.

    Args:
        event: EventBridge event containing TradeExecuted.
        context: Lambda context.

    Returns:
        Response indicating aggregation status.

    """
    detail = unwrap_eventbridge_event(event)

    metadata = detail.get("metadata", {})
    run_id = metadata.get("run_id", "")
    trade_id = metadata.get("trade_id", "")
    correlation_id = detail.get("correlation_id", "")

    if not run_id:
        logger.debug(
            "TradeExecuted event without run_id - skipping aggregation",
            extra={"correlation_id": correlation_id, "trade_id": trade_id},
        )
        return {
            "statusCode": 200,
            "body": {"status": "skipped", "reason": "no_run_id"},
        }

    logger.info(
        "Trade Aggregator received TradeExecuted event",
        extra={
            "run_id": run_id,
            "trade_id": trade_id,
            "correlation_id": correlation_id,
        },
    )

    return _handler.handle(detail, run_id, trade_id, correlation_id)
