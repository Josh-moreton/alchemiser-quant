"""Business Unit: execution_v2 | Status: current.

Lambda function to execute a single trade for Step Functions workflow.

This is a simplified version of the execution Lambda designed for use
with Step Functions. It executes a single trade and returns the result
without complex state machine coordination logic.
"""

from __future__ import annotations

from typing import Any

from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Execute a single trade.

    This is a placeholder implementation for Phase 1. In Phase 2, we'll
    extract the core trade execution logic from the existing execution
    Lambda and remove the SQS/DynamoDB coordination code.

    Args:
        event: Contains:
            - tradeId: Unique trade ID
            - symbol: Asset symbol
            - action: "BUY" or "SELL"
            - quantity: Number of shares
            - targetValue: Target dollar value
            - correlationId: Workflow correlation ID
            - runId: Execution run ID
        context: Lambda context (unused)

    Returns:
        Dict with:
            - tradeId: Trade ID
            - symbol: Asset symbol
            - action: Trade action
            - status: "COMPLETED" | "FAILED"
            - quantity: Actual quantity filled
            - averagePrice: Average execution price
            - totalValue: Total dollar value
            - orderId: Broker order ID
            - errorMessage: Error message if failed

    """
    trade_id = event.get("tradeId", "unknown")
    symbol = event.get("symbol", "UNKNOWN")
    action = event.get("action", "UNKNOWN")
    correlation_id = event.get("correlationId", "unknown")
    run_id = event.get("runId", "unknown")

    logger.info(
        "Executing trade (Step Functions mode)",
        extra={
            "trade_id": trade_id,
            "symbol": symbol,
            "action": action,
            "correlation_id": correlation_id,
            "run_id": run_id,
        },
    )

    # TODO: Phase 2 - Extract core execution logic from existing Lambda
    # For now, this is a placeholder that always succeeds
    # Real implementation will:
    # 1. Validate trade parameters
    # 2. Place order via Alpaca API
    # 3. Monitor order status
    # 4. Return execution result

    logger.warning(
        "Using placeholder trade execution (Phase 1)",
        extra={
            "trade_id": trade_id,
            "symbol": symbol,
            "action": action,
        },
    )

    return {
        "tradeId": trade_id,
        "symbol": symbol,
        "action": action,
        "status": "COMPLETED",
        "quantity": event.get("quantity", 0),
        "averagePrice": "100.00",
        "totalValue": event.get("targetValue", "0"),
        "orderId": f"mock-order-{trade_id}",
        "errorMessage": None,
    }
