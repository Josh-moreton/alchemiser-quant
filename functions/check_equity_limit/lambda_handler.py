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

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
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

    # In a real implementation, this would:
    # 1. Query current account equity from Alpaca
    # 2. Query cumulative BUY value so far from DynamoDB
    # 3. Calculate if adding this trade would exceed limit
    #
    # For Phase 1, we'll use a simplified version that always allows trades
    # The full circuit breaker logic will be ported from execution_run_service.py

    # TODO: Implement full circuit breaker logic in Phase 2
    # For now, always allow (existing execution path has this logic)

    return {
        "allowed": True,
        "cumulative": "0",
        "limit": str(equity_deployment_pct),
    }
