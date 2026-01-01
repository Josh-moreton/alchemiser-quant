"""Business Unit: metrics | Status: current.

Lambda handler for metrics publishing microservice.

Consumes TradeExecuted events from EventBridge and publishes per-strategy
realized P&L metrics to CloudWatch for dashboard visualization.
"""

from __future__ import annotations

import os
from typing import Any
from uuid import uuid4

from the_alchemiser.shared.events.eventbridge_publisher import unwrap_eventbridge_event
from the_alchemiser.shared.logging import configure_application_logging, get_logger
from the_alchemiser.shared.metrics.cloudwatch_metrics_publisher import (
    CloudWatchMetricsPublisher,
)

# Initialize logging on cold start
configure_application_logging()

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle TradeExecuted events and publish metrics to CloudWatch.

    This Lambda is triggered by EventBridge when TradeExecuted events are published.
    It queries closed lots from DynamoDB, aggregates P&L by strategy, and publishes
    metrics to CloudWatch.

    Args:
        event: EventBridge event containing TradeExecuted details
        context: Lambda context

    Returns:
        Response with status code and message

    """
    correlation_id = str(uuid4())

    try:
        # Extract EventBridge envelope metadata
        detail_type = event.get("detail-type", "")
        source = event.get("source", "")

        # Unwrap EventBridge envelope to get the actual event payload
        detail = unwrap_eventbridge_event(event)

        # Extract correlation_id from event if available
        correlation_id = detail.get("correlation_id", correlation_id)

        logger.info(
            "Metrics Lambda invoked",
            extra={
                "correlation_id": correlation_id,
                "detail_type": detail_type,
                "source": source,
            },
        )

        # Only process TradeExecuted events
        if detail_type != "TradeExecuted":
            logger.debug(
                f"Ignoring unsupported event type: {detail_type}",
                extra={"correlation_id": correlation_id},
            )
            return {
                "statusCode": 200,
                "body": f"Ignored event type: {detail_type}",
            }

        # Get configuration from environment
        trade_ledger_table = os.environ.get("TRADE_LEDGER__TABLE_NAME")
        if not trade_ledger_table:
            logger.error(
                "TRADE_LEDGER__TABLE_NAME environment variable not set",
                extra={"correlation_id": correlation_id},
            )
            return {
                "statusCode": 500,
                "body": "Configuration error: missing TRADE_LEDGER__TABLE_NAME",
            }

        # Get deployment stage
        stage = os.environ.get("STAGE", "production")

        # Create metrics publisher and publish all metrics
        publisher = CloudWatchMetricsPublisher(
            trade_ledger_table_name=trade_ledger_table,
            stage=stage,
        )
        publisher.publish_strategy_pnl_metrics(correlation_id)
        publisher.publish_all_strategy_metrics(correlation_id)

        # Extract and publish capital deployed percentage from event metadata
        metadata = detail.get("metadata", {})
        if isinstance(metadata, dict):
            capital_deployed_pct_str = metadata.get("capital_deployed_pct")
            if capital_deployed_pct_str is not None:
                try:
                    from decimal import Decimal

                    capital_deployed_pct = Decimal(str(capital_deployed_pct_str))
                    publisher.publish_capital_deployed_metric(capital_deployed_pct, correlation_id)
                except (TypeError, ValueError) as e:
                    logger.warning(
                        f"Failed to parse capital_deployed_pct: {e}",
                        extra={"correlation_id": correlation_id},
                    )

        logger.info(
            "Metrics published successfully",
            extra={"correlation_id": correlation_id},
        )

        return {
            "statusCode": 200,
            "body": f"Metrics published for correlation_id: {correlation_id}",
        }

    except Exception as e:
        logger.error(
            f"Metrics Lambda failed: {e}",
            exc_info=True,
            extra={
                "correlation_id": correlation_id,
                "error_type": type(e).__name__,
            },
        )
        # Don't raise - metrics publishing shouldn't fail the workflow
        return {
            "statusCode": 500,
            "body": f"Metrics publishing failed: {e!s}",
        }
