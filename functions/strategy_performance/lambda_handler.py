"""Business Unit: strategy_performance | Status: current.

Lambda handler for strategy performance metrics.

Consumes TradeExecuted events from EventBridge and writes per-strategy
performance metrics to DynamoDB for dashboard consumption.
"""

from __future__ import annotations

import os
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
        source = event.get("source", "")
        detail = unwrap_eventbridge_event(event)
        correlation_id = detail.get("correlation_id", correlation_id)

        logger.info(
            "Strategy performance Lambda invoked",
            extra={
                "correlation_id": correlation_id,
                "detail_type": detail_type,
                "source": source,
            },
        )

        if detail_type != "TradeExecuted":
            logger.debug(
                f"Ignoring unsupported event type: {detail_type}",
                extra={"correlation_id": correlation_id},
            )
            return {
                "statusCode": 200,
                "body": f"Ignored event type: {detail_type}",
            }

        trade_ledger_table = os.environ.get("TRADE_LEDGER__TABLE_NAME")
        strategy_performance_table = os.environ.get("STRATEGY_PERFORMANCE_TABLE")

        if not trade_ledger_table:
            logger.error(
                "TRADE_LEDGER__TABLE_NAME environment variable not set",
                extra={"correlation_id": correlation_id},
            )
            return {
                "statusCode": 500,
                "body": "Configuration error: missing TRADE_LEDGER__TABLE_NAME",
            }

        if not strategy_performance_table:
            logger.error(
                "STRATEGY_PERFORMANCE_TABLE environment variable not set",
                extra={"correlation_id": correlation_id},
            )
            return {
                "statusCode": 500,
                "body": "Configuration error: missing STRATEGY_PERFORMANCE_TABLE",
            }

        publisher = DynamoDBMetricsPublisher(
            trade_ledger_table_name=trade_ledger_table,
            strategy_performance_table_name=strategy_performance_table,
        )
        publisher.write_strategy_metrics(correlation_id)

        metadata = detail.get("metadata", {})
        if isinstance(metadata, dict):
            capital_deployed_pct_str = metadata.get("capital_deployed_pct")
            if capital_deployed_pct_str is not None:
                try:
                    from decimal import Decimal

                    capital_deployed_pct = Decimal(str(capital_deployed_pct_str))
                    publisher.write_capital_deployed_metric(capital_deployed_pct, correlation_id)
                except (TypeError, ValueError) as e:
                    logger.warning(
                        f"Failed to parse capital_deployed_pct: {e}",
                        extra={"correlation_id": correlation_id},
                    )

        logger.info(
            "Strategy performance metrics written successfully",
            extra={"correlation_id": correlation_id},
        )

        return {
            "statusCode": 200,
            "body": f"Metrics written for correlation_id: {correlation_id}",
        }

    except Exception as e:
        logger.error(
            f"Strategy performance Lambda failed: {e}",
            exc_info=True,
            extra={
                "correlation_id": correlation_id,
                "error_type": type(e).__name__,
            },
        )
        return {
            "statusCode": 500,
            "body": f"Metrics writing failed: {e!s}",
        }
