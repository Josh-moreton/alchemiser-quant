#!/usr/bin/env python3
"""Business Unit: pnl_capture | Status: current.

Lambda handler for daily P&L capture.

This Lambda runs on a daily schedule to capture the previous day's P&L data
from Alpaca and store it in DynamoDB, providing a canonical source of truth
for historical portfolio performance.

Trigger: EventBridge schedule (daily, after market close).
"""

from __future__ import annotations

import os
from datetime import UTC, date, datetime, timedelta
from typing import Any

from the_alchemiser.shared.brokers.alpaca_manager import create_alpaca_manager
from the_alchemiser.shared.config.secrets_adapter import get_alpaca_keys
from the_alchemiser.shared.logging import configure_application_logging, get_logger
from the_alchemiser.shared.services.daily_pnl_service import DailyPnLService

# Initialize logging on cold start
configure_application_logging()

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Capture daily P&L and store in DynamoDB.

    This handler:
    1. Determines target date (yesterday by default, or from event)
    2. Fetches equity and P&L data from Alpaca
    3. Adjusts P&L for deposits/withdrawals
    4. Stores record in DynamoDB

    Args:
        event: Lambda event (may contain 'target_date' for backfilling)
        context: Lambda context

    Returns:
        Response with capture status and metrics.

    """
    # Get configuration from environment
    table_name = os.environ.get("DAILY_PNL_TABLE_NAME", "")
    environment = os.environ.get("ENVIRONMENT", "dev")

    if not table_name:
        logger.error("DAILY_PNL_TABLE_NAME not configured")
        return {
            "statusCode": 500,
            "body": {"status": "error", "message": "Table name not configured"},
        }

    # Determine target date (yesterday by default, or from event for backfill)
    target_date_str = event.get("target_date")
    if target_date_str:
        try:
            target_date = date.fromisoformat(target_date_str)
            logger.info(f"Backfilling PnL for {target_date_str}")
        except ValueError:
            logger.error(f"Invalid target_date format: {target_date_str}")
            return {
                "statusCode": 400,
                "body": {"status": "error", "message": "Invalid target_date format"},
            }
    else:
        # Default: yesterday
        target_date = (datetime.now(UTC) - timedelta(days=1)).date()
        logger.info(f"Capturing PnL for yesterday: {target_date}")

    try:
        # Initialize Alpaca manager
        api_key, secret_key, endpoint = get_alpaca_keys()
        paper = "paper" in endpoint.lower() if endpoint else True
        alpaca_manager = create_alpaca_manager(
            api_key=api_key, secret_key=secret_key, paper=paper
        )

        # Initialize PnL service
        pnl_service = DailyPnLService(
            table_name=table_name,
            environment=environment,
            alpaca_manager=alpaca_manager,
        )

        # Capture daily PnL
        record = pnl_service.capture_daily_pnl(target_date)

        logger.info(
            f"Successfully captured PnL for {target_date}",
            extra={
                "date": record.date,
                "equity": float(record.equity),
                "pnl_amount": float(record.pnl_amount),
                "pnl_percent": float(record.pnl_percent),
                "raw_pnl": float(record.raw_pnl),
                "deposits_settled": float(record.deposits_settled),
            },
        )

        return {
            "statusCode": 200,
            "body": {
                "status": "success",
                "date": record.date,
                "equity": float(record.equity),
                "pnl_amount": float(record.pnl_amount),
                "pnl_percent": float(record.pnl_percent),
                "raw_pnl": float(record.raw_pnl),
                "deposits_settled": float(record.deposits_settled),
                "deposits": float(record.deposits),
                "withdrawals": float(record.withdrawals),
            },
        }

    except Exception as e:
        logger.error(
            f"Failed to capture daily PnL: {e}",
            extra={"date": target_date.isoformat(), "error_type": type(e).__name__},
        )
        return {
            "statusCode": 500,
            "body": {
                "status": "error",
                "message": str(e),
                "date": target_date.isoformat(),
            },
        }
