"""Business Unit: hedge_reports | Status: current.

Lambda handler for hedge reports generation.

Generates daily and weekly hedge reports, publishes summaries to SNS,
and stores full reports in S3 for reference.
"""

from __future__ import annotations

import json
import os
from typing import Any
from uuid import uuid4

from the_alchemiser.shared.logging import configure_application_logging, get_logger

# Initialize logging on cold start
configure_application_logging()

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle scheduled report generation trigger.

    This Lambda is triggered by EventBridge Schedule rules:
    - Daily: 4:30 PM ET (after hedge activity)
    - Weekly: Friday 5:00 PM ET

    Args:
        event: EventBridge scheduled event or test event
        context: Lambda context

    Returns:
        Response with status code and report summary

    """
    correlation_id = str(uuid4())

    try:
        # Determine report type from event
        report_type = event.get("report_type", "daily")
        detail = event.get("detail", {})

        # Get report type from scheduled event if present
        if "resources" in event and "rule" in str(event.get("resources", [])):
            # Parse rule name to determine report type
            resources = event.get("resources", [])
            if any("weekly" in r.lower() for r in resources):
                report_type = "weekly"

        logger.info(
            "Hedge Reports Lambda invoked",
            correlation_id=correlation_id,
            report_type=report_type,
        )

        # Import handler here to avoid cold start overhead if not needed
        from handlers.report_generation_handler import ReportGenerationHandler

        # Get account ID from environment or event
        account_id = os.environ.get("ALPACA_ACCOUNT_ID", detail.get("account_id", "default"))

        handler = ReportGenerationHandler(
            account_id=account_id,
            correlation_id=correlation_id,
        )

        if report_type == "weekly":
            result = handler.generate_weekly_report()
        else:
            result = handler.generate_daily_report()

        logger.info(
            "Hedge report generated successfully",
            correlation_id=correlation_id,
            report_type=report_type,
            active_positions=result.get("active_positions_count", 0),
        )

        return {
            "statusCode": 200,
            "body": json.dumps(result, default=str),
        }

    except Exception as e:
        logger.error(
            "Hedge Reports Lambda failed",
            error=str(e),
            exc_info=True,
            correlation_id=correlation_id,
        )
        # Don't raise - report generation failures shouldn't alarm
        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "error": str(e),
                    "correlation_id": correlation_id,
                }
            ),
        }
