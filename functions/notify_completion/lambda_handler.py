"""Business Unit: notifications_v2 | Status: current.

Lambda function to send completion notifications.

This function sends an email notification via SNS when trade execution
completes successfully. It formats the aggregated results into a
human-readable message.
"""

from __future__ import annotations

import os
from typing import Any

import boto3

from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Send completion notification via SNS.

    Args:
        event: Contains:
            - aggregation: Aggregated trade results
            - correlationId: Workflow correlation ID
            - runId: Execution run ID
        context: Lambda context (unused)

    Returns:
        Dict with:
            - status: "SUCCESS"
            - messageId: SNS message ID

    """
    correlation_id = event.get("correlationId", "unknown")
    run_id = event.get("runId", "unknown")
    aggregation = event.get("aggregation", {})

    logger.info(
        "Sending completion notification",
        extra={
            "correlation_id": correlation_id,
            "run_id": run_id,
        },
    )

    # Extract aggregation data
    total_trades = aggregation.get("totalTrades", 0)
    succeeded = aggregation.get("succeededTrades", 0)
    failed = aggregation.get("failedTrades", 0)
    skipped = aggregation.get("skippedTrades", 0)
    total_value = aggregation.get("totalValue", "0")
    summary = aggregation.get("summary", "No summary available")

    # Format notification message
    subject = f"✅ Trade Execution Completed - {succeeded}/{total_trades} succeeded"
    message = f"""
Trade Execution Workflow Completed

Run ID: {run_id}
Correlation ID: {correlation_id}

Results:
- Total Trades: {total_trades}
- Succeeded: {succeeded}
- Failed: {failed}
- Skipped: {skipped}
- Total Value: ${total_value}

Summary:
{summary}

This notification was sent from the Step Functions execution workflow.
    """.strip()

    # Publish to SNS
    sns_topic_arn = os.environ.get("SNS_NOTIFICATION_TOPIC_ARN")
    if not sns_topic_arn:
        logger.error(
            "SNS_NOTIFICATION_TOPIC_ARN not configured",
            extra={"correlation_id": correlation_id},
        )
        return {
            "status": "ERROR",
            "message": "SNS topic ARN not configured",
        }

    sns = boto3.client("sns")
    response = sns.publish(
        TopicArn=sns_topic_arn,
        Subject=subject,
        Message=message,
    )

    logger.info(
        "Completion notification sent",
        extra={
            "correlation_id": correlation_id,
            "run_id": run_id,
            "message_id": response.get("MessageId"),
        },
    )

    return {
        "status": "SUCCESS",
        "messageId": response.get("MessageId"),
    }
