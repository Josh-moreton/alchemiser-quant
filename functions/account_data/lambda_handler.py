"""Business Unit: account_data | Status: current.

Lambda handler for the Account Data service.

Runs on a 6-hourly EventBridge schedule (4 AM, 10 AM, 4 PM, 10 PM ET) to
fetch account information, positions, and deposit-adjusted PnL history from
Alpaca, then persist everything to a single-table DynamoDB design.

The Streamlit dashboard reads from this table instead of calling Alpaca directly,
eliminating all broker API calls from the frontend.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

from handlers.account_collection_handler import AccountCollectionHandler

from the_alchemiser.shared.logging import configure_application_logging, get_logger

# Initialise logging on cold start (must be before get_logger)
configure_application_logging()

logger = get_logger(__name__)

# Environment variables
ACCOUNT_DATA_TABLE = os.environ.get("ACCOUNT_DATA_TABLE", "")


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Lambda entry point for the account data collection service.

    Args:
        event: Lambda event (from EventBridge Scheduler or manual invocation).
        context: Lambda context object.

    Returns:
        Response dict with status, phases completed, and any errors.

    """
    correlation_id = event.get(
        "correlation_id",
        f"account-data-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}",
    )

    logger.info(
        "Account data Lambda invoked",
        extra={
            "correlation_id": correlation_id,
            "source": event.get("source", "manual"),
        },
    )

    if not ACCOUNT_DATA_TABLE:
        error_msg = "ACCOUNT_DATA_TABLE environment variable not set"
        logger.error(error_msg)
        return {"statusCode": 500, "body": {"status": "error", "error": error_msg}}

    handler = AccountCollectionHandler()
    return handler.handle(table_name=ACCOUNT_DATA_TABLE, correlation_id=correlation_id)


# Backward-compatible alias for existing template.yaml Handler reference
handler = lambda_handler
