#!/usr/bin/env python3
"""
Monthly Summary Lambda Handler

This module provides the AWS Lambda handler for generating and sending
monthly trading summary emails.
"""

import json
import logging
from datetime import datetime
from typing import Any

from the_alchemiser.application.reporting.monthly_summary_service import MonthlySummaryService
from the_alchemiser.infrastructure.config import load_settings
from the_alchemiser.interface.email.client import send_email_notification
from the_alchemiser.interface.email.templates.monthly_summary import MonthlySummaryBuilder
from the_alchemiser.services.errors.exceptions import (
    DataProviderError,
    TradingClientError,
)

# Set up logging
logger = logging.getLogger(__name__)


def monthly_summary_lambda_handler(
    event: dict[str, Any] | None = None, context: Any = None
) -> dict[str, Any]:
    """
    AWS Lambda handler for monthly summary reports.

    Args:
        event: AWS Lambda event data containing optional month configuration
        context: AWS Lambda runtime context object

    Returns:
        dict: Execution status and summary information

    Event Structure:
        {
            "month": "2024-01",           # Optional: specific month (YYYY-MM format)
            "trading_mode": "paper" | "live"  # Optional: trading mode (default: live)
        }
    """
    # Extract request ID for tracking
    request_id = getattr(context, "aws_request_id", "unknown") if context else "local"

    try:
        # Log the incoming event
        logger.info(
            f"Monthly summary Lambda invoked with event: {json.dumps(event) if event else 'None'}"
        )

        # Load settings
        settings = load_settings()

        # Determine trading mode
        trading_mode = event.get("trading_mode", "live") if event else "live"
        paper_trading = trading_mode.lower() == "paper"

        # Parse target month if provided
        target_month = None
        if event and event.get("month"):
            try:
                target_month = datetime.strptime(event["month"], "%Y-%m")
            except ValueError:
                logger.warning(f"Invalid month format: {event['month']}, using default")

        logger.info(f"Generating monthly summary - Paper trading: {paper_trading}")

        # Get API credentials
        from the_alchemiser.services.shared.secrets_service import SecretsService

        secrets_service = SecretsService()
        alpaca_api_key, alpaca_secret_key = secrets_service.get_alpaca_credentials(paper_trading)

        # Generate monthly summary
        summary_service = MonthlySummaryService(
            api_key=alpaca_api_key, secret_key=alpaca_secret_key, paper=paper_trading
        )

        summary_data = summary_service.generate_monthly_summary(target_month)

        # Build email content
        email_html = MonthlySummaryBuilder.build_monthly_summary_email(summary_data)

        # Send email notification
        month_name = summary_data.get("month", "Unknown")
        subject = f"The Alchemiser - Monthly Summary ({month_name})"

        # Add trading mode to subject if paper trading
        if paper_trading:
            subject += " [PAPER]"

        send_email_notification(
            subject=subject,
            html_content=email_html,
            text_content=f"Monthly trading summary for {month_name}. Please view HTML version for full details.",
        )

        # Build response
        response = {
            "status": "success",
            "message": f"Monthly summary for {month_name} generated and sent successfully",
            "month": month_name,
            "trading_mode": trading_mode,
            "request_id": request_id,
            "summary": {
                "portfolio_value": summary_data.get("account_summary", {}).get(
                    "portfolio_value", 0
                ),
                "monthly_return": summary_data.get("portfolio_performance", {}).get(
                    "total_return", 0
                ),
                "monthly_return_pct": summary_data.get("portfolio_performance", {}).get(
                    "total_return_pct", 0
                ),
                "total_trades": summary_data.get("trading_activity", {}).get("total_trades", 0),
                "strategy_pnl": summary_data.get("strategy_performance", {}).get(
                    "total_strategy_pnl", 0
                ),
            },
        }

        logger.info(f"Monthly summary completed successfully: {response}")
        return response

    except (DataProviderError, TradingClientError) as e:
        from the_alchemiser.infrastructure.logging.logging_utils import log_error_with_context

        error_message = f"Monthly summary error ({type(e).__name__}): {str(e)}"
        log_error_with_context(
            logger,
            e,
            "monthly_summary_execution",
            function="monthly_summary_lambda_handler",
            error_type=type(e).__name__,
            trading_mode=locals().get("trading_mode", "unknown"),
            request_id=request_id,
        )
        logger.error(error_message, exc_info=True)

        return {
            "status": "failed",
            "message": error_message,
            "error_type": type(e).__name__,
            "request_id": request_id,
        }

    except Exception as e:
        from the_alchemiser.infrastructure.logging.logging_utils import log_error_with_context

        error_message = f"Monthly summary unexpected error: {str(e)}"
        log_error_with_context(
            logger,
            e,
            "monthly_summary_execution",
            function="monthly_summary_lambda_handler",
            error_type="unexpected_error",
            original_error=type(e).__name__,
            request_id=request_id,
        )
        logger.error(error_message, exc_info=True)

        return {
            "status": "failed",
            "message": error_message,
            "error_type": "unexpected_error",
            "request_id": request_id,
        }
