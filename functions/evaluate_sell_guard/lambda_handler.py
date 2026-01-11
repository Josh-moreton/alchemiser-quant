"""Business Unit: execution_v2 | Status: current.

Lambda function to evaluate SELL phase guard condition.

This function calculates the total dollar amount of failed SELL trades
and determines whether the BUY phase should proceed. If SELL failures
exceed a threshold (e.g., $500), BUY phase is blocked to avoid deploying
cash that wasn't freed by sells.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Evaluate SELL phase guard to determine if BUY phase should proceed.

    Args:
        event: Contains:
            - sellResults: List of SELL trade results from Map state
            - failureThresholdUsd: Threshold in dollars (default 500)
            - correlationId: Workflow correlation ID
            - runId: Execution run ID
        context: Lambda context (unused)

    Returns:
        Dict with:
            - buyPhaseAllowed: Boolean indicating if BUY phase can proceed
            - sellFailedAmount: Total dollar value of failed SELLs
            - sellSucceededAmount: Total dollar value of successful SELLs
            - sellFailedCount: Count of failed SELL trades

    """
    correlation_id = event.get("correlationId", "unknown")
    run_id = event.get("runId", "unknown")
    failure_threshold = Decimal(str(event.get("failureThresholdUsd", 500)))

    logger.info(
        "Evaluating SELL phase guard",
        extra={
            "correlation_id": correlation_id,
            "run_id": run_id,
            "failure_threshold_usd": str(failure_threshold),
        },
    )

    sell_results = event.get("sellResults", [])

    # Calculate SELL phase metrics
    failed_amount = Decimal("0")
    succeeded_amount = Decimal("0")
    failed_count = 0

    for result in sell_results:
        # Step Functions Map state wraps Lambda results in Payload
        payload = result.get("Payload", result)

        status = payload.get("status", "UNKNOWN")
        total_value = payload.get("totalValue")

        if total_value is not None:
            value_decimal = Decimal(str(total_value))
        else:
            value_decimal = Decimal("0")

        if status == "FAILED":
            failed_amount += abs(value_decimal)
            failed_count += 1
        elif status == "COMPLETED":
            succeeded_amount += abs(value_decimal)

    # Determine if BUY phase is allowed
    buy_phase_allowed = failed_amount < failure_threshold

    logger.info(
        "SELL phase guard evaluated",
        extra={
            "correlation_id": correlation_id,
            "run_id": run_id,
            "sell_failed_amount": str(failed_amount),
            "sell_succeeded_amount": str(succeeded_amount),
            "sell_failed_count": failed_count,
            "buy_phase_allowed": buy_phase_allowed,
            "failure_threshold": str(failure_threshold),
        },
    )

    return {
        "buyPhaseAllowed": buy_phase_allowed,
        "sellFailedAmount": str(failed_amount),
        "sellSucceededAmount": str(succeeded_amount),
        "sellFailedCount": failed_count,
    }
