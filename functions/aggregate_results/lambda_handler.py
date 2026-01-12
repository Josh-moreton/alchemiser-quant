"""Business Unit: execution_v2 | Status: current.

Lambda function to aggregate trade execution results.

This function collects results from both SELL and BUY phases and
creates a summary for notifications. It calculates totals, counts
successes/failures, and prepares a structured summary.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Aggregate trade execution results from SELL and BUY phases.

    Args:
        event: Contains:
            - sellResults: List of SELL trade results
            - buyResults: List of BUY trade results
            - correlationId: Workflow correlation ID
            - runId: Execution run ID
            - planId: Rebalance plan ID
        context: Lambda context (unused)

    Returns:
        Dict with:
            - totalTrades: Total number of trades
            - succeededTrades: Number of successful trades
            - failedTrades: Number of failed trades
            - skippedTrades: Number of skipped trades
            - sellCount: SELL trade count
            - buyCount: BUY trade count
            - totalValue: Total dollar value traded
            - summary: Human-readable summary
            - correlationId: Correlation ID
            - runId: Run ID

    """
    correlation_id = event.get("correlationId", "unknown")
    run_id = event.get("runId", "unknown")
    plan_id = event.get("planId", "unknown")

    logger.info(
        "Aggregating trade results",
        extra={
            "correlation_id": correlation_id,
            "run_id": run_id,
            "plan_id": plan_id,
        },
    )

    sell_results = event.get("sellResults", [])
    buy_results = event.get("buyResults", [])

    # Initialize counters
    total_trades = 0
    succeeded_trades = 0
    failed_trades = 0
    skipped_trades = 0
    unknown_trades = 0
    total_value = Decimal("0")

    # Process SELL results
    sell_count = 0
    for result in sell_results:
        payload = result.get("Payload", result)
        status = payload.get("status", "UNKNOWN")
        value = payload.get("totalValue")

        if value is not None:
            total_value += abs(Decimal(str(value)))

        total_trades += 1
        sell_count += 1

        if status == "COMPLETED":
            succeeded_trades += 1
        elif status == "FAILED":
            failed_trades += 1
        elif status == "SKIPPED":
            skipped_trades += 1
        else:
            unknown_trades += 1
            logger.warning(
                "Unknown trade status encountered",
                extra={
                    "status": status,
                    "trade_id": payload.get("tradeId"),
                    "symbol": payload.get("symbol"),
                },
            )

    # Process BUY results
    buy_count = 0
    for result in buy_results:
        payload = result.get("Payload", result)
        status = payload.get("status", "UNKNOWN")
        value = payload.get("totalValue")

        if value is not None:
            total_value += abs(Decimal(str(value)))

        total_trades += 1
        buy_count += 1

        if status == "COMPLETED":
            succeeded_trades += 1
        elif status == "FAILED":
            failed_trades += 1
        elif status == "SKIPPED":
            skipped_trades += 1
        else:
            unknown_trades += 1
            logger.warning(
                "Unknown trade status encountered",
                extra={
                    "status": status,
                    "trade_id": payload.get("tradeId"),
                    "symbol": payload.get("symbol"),
                },
            )

    # Create summary
    summary = (
        f"Execution completed: {succeeded_trades}/{total_trades} trades succeeded. "
        f"SELLs: {sell_count}, BUYs: {buy_count}. "
        f"Total value: ${total_value:.2f}"
    )
    if unknown_trades > 0:
        summary += f" ({unknown_trades} with unknown status)"

    logger.info(
        "Trade results aggregated",
        extra={
            "correlation_id": correlation_id,
            "run_id": run_id,
            "total_trades": total_trades,
            "succeeded_trades": succeeded_trades,
            "failed_trades": failed_trades,
            "skipped_trades": skipped_trades,
            "unknown_trades": unknown_trades,
            "total_value": str(total_value),
        },
    )

    return {
        "totalTrades": total_trades,
        "succeededTrades": succeeded_trades,
        "failedTrades": failed_trades,
        "skippedTrades": skipped_trades,
        "unknownTrades": unknown_trades,
        "sellCount": sell_count,
        "buyCount": buy_count,
        "totalValue": str(total_value),
        "summary": summary,
        "correlationId": correlation_id,
        "runId": run_id,
        "planId": plan_id,
    }
