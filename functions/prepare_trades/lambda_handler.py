"""Business Unit: execution_v2 | Status: current.

Lambda function to prepare trades for Step Functions execution.

This function splits a rebalance plan into SELL and BUY trade arrays for
two-phase execution. SELLs must complete before BUYs to ensure cash is
available for purchases.
"""

from __future__ import annotations

from typing import Any

from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Prepare trades for Step Functions execution.

    This Lambda is the first step in the execution workflow. It receives
    a rebalance plan and splits it into SELL and BUY arrays for two-phase
    execution.

    Args:
        event: Step Functions input containing:
            - rebalancePlan: RebalancePlan object
            - correlationId: Workflow correlation ID
            - runId: Execution run ID
            - planId: Rebalance plan ID
        context: Lambda context (unused)

    Returns:
        Dict with:
            - sellTrades: List of SELL trade messages
            - buyTrades: List of BUY trade messages
            - runId: Execution run ID
            - planId: Rebalance plan ID
            - correlationId: Correlation ID

    """
    correlation_id = event.get("correlationId", "unknown")
    run_id = event.get("runId", "unknown")
    plan_id = event.get("planId", "unknown")

    logger.info(
        "Preparing trades for execution",
        extra={
            "correlation_id": correlation_id,
            "run_id": run_id,
            "plan_id": plan_id,
        },
    )

    # Extract rebalance plan from event
    rebalance_plan = event.get("rebalancePlan", {})
    trade_messages = rebalance_plan.get("tradeMessages", [])

    if not trade_messages:
        logger.warning(
            "No trade messages in rebalance plan",
            extra={"correlation_id": correlation_id},
        )
        return {
            "sellTrades": [],
            "buyTrades": [],
            "runId": run_id,
            "planId": plan_id,
            "correlationId": correlation_id,
        }

    # Split trades into SELL and BUY arrays
    sell_trades: list[dict[str, Any]] = []
    buy_trades: list[dict[str, Any]] = []

    for trade_msg in trade_messages:
        action = trade_msg.get("action", "").upper()

        if action == "SELL":
            sell_trades.append(trade_msg)
        elif action == "BUY":
            buy_trades.append(trade_msg)
        else:
            logger.warning(
                "Unknown trade action, skipping",
                extra={
                    "action": action,
                    "symbol": trade_msg.get("symbol"),
                    "correlation_id": correlation_id,
                },
            )

    logger.info(
        "Trades prepared for execution",
        extra={
            "correlation_id": correlation_id,
            "sell_count": len(sell_trades),
            "buy_count": len(buy_trades),
            "total_trades": len(trade_messages),
        },
    )

    return {
        "sellTrades": sell_trades,
        "buyTrades": buy_trades,
        "runId": run_id,
        "planId": plan_id,
        "correlationId": correlation_id,
    }
