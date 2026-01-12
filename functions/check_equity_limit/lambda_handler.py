"""Business Unit: execution_v2 | Status: current.

Lambda function to check equity circuit breaker for BUY trades.

This function implements the equity deployment limit circuit breaker.
It checks if the cumulative value of BUY trades would exceed the
configured equity deployment percentage (e.g., 100% or 110% with margin).
"""

from __future__ import annotations

import os
from decimal import Decimal
from typing import Any

import boto3

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.services.execution_run_service import ExecutionRunService

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Check if BUY trade is allowed based on equity circuit breaker.

    This checks the cumulative value of BUY trades against the equity
    deployment limit. If the limit is exceeded, the trade is skipped.

    Args:
        event: Contains:
            - totalValue: Dollar value of this BUY trade
            - runId: Execution run ID
            - correlationId: Correlation ID
        context: Lambda context (unused)

    Returns:
        Dict with:
            - allowed: Boolean indicating if trade should proceed
            - cumulative: Cumulative BUY value so far
            - limit: Equity deployment limit

    """
    correlation_id = event.get("correlationId", "unknown")
    run_id = event.get("runId", "unknown")
    trade_value = Decimal(str(event.get("totalValue", 0)))

    # Get equity deployment percentage from environment (default 1.0 = 100%)
    equity_deployment_pct = Decimal(os.environ.get("EQUITY_DEPLOYMENT_PCT", "1.0"))

    logger.info(
        "Checking equity circuit breaker",
        extra={
            "correlation_id": correlation_id,
            "run_id": run_id,
            "trade_value": str(trade_value),
            "equity_deployment_pct": str(equity_deployment_pct),
        },
    )

    try:
        # Initialize ExecutionRunService to access run state
        dynamodb = boto3.resource("dynamodb")
        table_name = os.environ.get("EXECUTION_RUNS_TABLE_NAME")

        if not table_name:
            logger.warning("EXECUTION_RUNS_TABLE_NAME not configured, allowing trade")
            return {
                "allowed": True,
                "cumulative": "0",
                "limit": str(equity_deployment_pct),
                "reason": "table_not_configured",
            }

        table = dynamodb.Table(table_name)
        run_service = ExecutionRunService(table=table)

        # Get current run state
        run = run_service.get_run(run_id)
        if not run:
            logger.warning(
                "Run not found - blocking trade (fail-safe)",
                extra={"run_id": run_id},
            )
            return {
                "allowed": False,
                "cumulative": "0",
                "limit": str(equity_deployment_pct),
                "reason": "run_not_found",
            }

        # Get max equity limit and cumulative BUY value
        max_equity_limit = run.get("max_equity_limit_usd", Decimal("0"))
        cumulative_buy = run.get("cumulative_buy_succeeded_value", Decimal("0"))

        # If max_equity_limit is 0 or not set, circuit breaker is disabled
        if max_equity_limit <= Decimal("0"):
            logger.debug(
                "Circuit breaker disabled (max_equity_limit not set)",
                extra={"run_id": run_id},
            )
            return {
                "allowed": True,
                "cumulative": str(cumulative_buy),
                "limit": "0",
                "reason": "circuit_breaker_disabled",
            }

        # Calculate what the new cumulative would be
        new_cumulative = cumulative_buy + abs(trade_value)
        headroom = max_equity_limit - cumulative_buy

        # Check if adding this trade would exceed the limit
        if new_cumulative > max_equity_limit:
            logger.warning(
                "🚫 Equity circuit breaker TRIGGERED - BUY would exceed limit",
                extra={
                    "run_id": run_id,
                    "max_equity_limit_usd": str(max_equity_limit),
                    "cumulative_buy_succeeded_value": str(cumulative_buy),
                    "proposed_buy_value": str(trade_value),
                    "new_cumulative_if_executed": str(new_cumulative),
                    "overage": str(new_cumulative - max_equity_limit),
                },
            )
            return {
                "allowed": False,
                "cumulative": str(cumulative_buy),
                "limit": str(max_equity_limit),
                "reason": "would_exceed_limit",
                "headroom": str(headroom),
            }

        logger.debug(
            "Equity circuit breaker check passed",
            extra={
                "run_id": run_id,
                "cumulative_buy": str(cumulative_buy),
                "proposed_buy": str(trade_value),
                "headroom": str(headroom),
            },
        )

        return {
            "allowed": True,
            "cumulative": str(cumulative_buy),
            "limit": str(max_equity_limit),
            "reason": "within_limit",
            "headroom": str(headroom),
        }

    except Exception as e:
        logger.error(
            f"Error checking equity circuit breaker: {e}",
            exc_info=True,
            extra={
                "run_id": run_id,
                "error_type": type(e).__name__,
            },
        )
        # On error, fail-safe: block the trade
        return {
            "allowed": False,
            "cumulative": "0",
            "limit": str(equity_deployment_pct),
            "reason": f"error_{type(e).__name__}",
        }
