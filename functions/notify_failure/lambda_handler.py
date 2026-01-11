"""Business Unit: notifications_v2 | Status: current.

Lambda function to send failure notifications.

This function sends an email notification via SNS when trade execution
fails or the BUY phase is blocked due to SELL failures exceeding threshold.
"""

from __future__ import annotations

import os
from typing import Any

import boto3

from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Send failure notification via SNS.

    Args:
        event: Contains:
            - reason: Failure reason (e.g., "BUY_PHASE_BLOCKED")
            - sellResults: SELL trade results (optional)
            - guardResult: Guard evaluation result (optional)
            - error: Error details (optional)
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
    reason = event.get("reason", "UNKNOWN_FAILURE")

    logger.warning(
        "Sending failure notification",
        extra={
            "correlation_id": correlation_id,
            "run_id": run_id,
            "reason": reason,
        },
    )

    # Format notification based on failure reason
    if reason == "BUY_PHASE_BLOCKED":
        guard_result = event.get("guardResult", {})
        payload = guard_result.get("Payload", guard_result)
        failed_amount = payload.get("sellFailedAmount", "0")
        failed_count = payload.get("sellFailedCount", 0)

        subject = "⚠️ Trade Execution Failed - BUY Phase Blocked"
        message = f"""
Trade Execution Workflow Failed: BUY Phase Blocked

Run ID: {run_id}
Correlation ID: {correlation_id}

Reason: SELL failures exceeded threshold

SELL Phase Results:
- Failed Amount: ${failed_amount}
- Failed Count: {failed_count}
- Threshold: $500

BUY phase was blocked to prevent deploying cash that wasn't freed by sells.

This notification was sent from the Step Functions execution workflow.
        """.strip()
    else:
        error = event.get("error", {})
        subject = f"❌ Trade Execution Failed - {reason}"
        message = f"""
Trade Execution Workflow Failed

Run ID: {run_id}
Correlation ID: {correlation_id}

Reason: {reason}

Error Details:
{error}

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
        "Failure notification sent",
        extra={
            "correlation_id": correlation_id,
            "run_id": run_id,
            "reason": reason,
            "message_id": response.get("MessageId"),
        },
    )

    return {
        "status": "SUCCESS",
        "messageId": response.get("MessageId"),
    }
