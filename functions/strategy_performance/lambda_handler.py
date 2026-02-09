"""Business Unit: strategy_performance | Status: current.

Lambda handler for strategy performance metrics.

Consumes TradeExecuted events from EventBridge and writes per-strategy
performance metrics to DynamoDB for dashboard consumption.
"""

from __future__ import annotations

import os
from decimal import Decimal
from typing import Any
from uuid import uuid4

from the_alchemiser.shared.events.eventbridge_publisher import unwrap_eventbridge_event
from the_alchemiser.shared.logging import configure_application_logging, get_logger
from the_alchemiser.shared.metrics.dynamodb_metrics_publisher import (
    DynamoDBMetricsPublisher,
)

# Initialize logging on cold start
configure_application_logging()

logger = get_logger(__name__)


def _validate_config(correlation_id: str) -> tuple[str, str] | None:
    """Validate required environment variables.

    Returns:
        Tuple of (trade_ledger_table, strategy_performance_table) or None on failure.

    """
    trade_ledger_table = os.environ.get("TRADE_LEDGER__TABLE_NAME")
    strategy_performance_table = os.environ.get("STRATEGY_PERFORMANCE_TABLE")

    if not trade_ledger_table:
        logger.error(
            "TRADE_LEDGER__TABLE_NAME environment variable not set",
            extra={"correlation_id": correlation_id},
        )
        return None

    if not strategy_performance_table:
        logger.error(
            "STRATEGY_PERFORMANCE_TABLE environment variable not set",
            extra={"correlation_id": correlation_id},
        )
        return None

    return trade_ledger_table, strategy_performance_table


def _process_capital_deployed(
    publisher: DynamoDBMetricsPublisher,
    detail: dict[str, Any],
    correlation_id: str,
) -> None:
    """Extract and write capital_deployed_pct from event metadata."""
    metadata = detail.get("metadata", {})
    if not isinstance(metadata, dict):
        return

    capital_deployed_pct_str = metadata.get("capital_deployed_pct")
    if capital_deployed_pct_str is None:
        return

    try:
        capital_deployed_pct = Decimal(str(capital_deployed_pct_str))
        publisher.write_capital_deployed_metric(capital_deployed_pct, correlation_id)
    except (TypeError, ValueError):
        logger.warning(
            "Failed to parse capital_deployed_pct",
            extra={
                "correlation_id": correlation_id,
                "raw_value": str(capital_deployed_pct_str),
            },
        )


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

        config = _validate_config(correlation_id)
        if config is None:
            return {"statusCode": 500, "body": "Configuration error: missing env vars"}

        publisher = DynamoDBMetricsPublisher(
            trade_ledger_table_name=config[0],
            strategy_performance_table_name=config[1],
        )
        publisher.write_strategy_metrics(correlation_id)
        _process_capital_deployed(publisher, detail, correlation_id)

        logger.info(
            "Strategy performance metrics written successfully",
            extra={"correlation_id": correlation_id},
        )
        return {"statusCode": 200, "body": "Metrics written successfully"}

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
