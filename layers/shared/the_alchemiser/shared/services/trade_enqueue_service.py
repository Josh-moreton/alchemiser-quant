"""Business Unit: shared | Status: current.

Trade enqueue service for decomposing rebalance plans into trade messages
and enqueueing them to SQS for parallel per-trade execution.

Extracted from portfolio_v2 handlers to enable reuse by strategy workers
in the per-strategy books architecture.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import boto3

from the_alchemiser.shared.config.config import load_settings
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlan
from the_alchemiser.shared.schemas.trade_message import TradeMessage
from the_alchemiser.shared.services.execution_run_service import ExecutionRunService

logger = get_logger(__name__)

MODULE_NAME = "shared.services.trade_enqueue_service"


def enqueue_rebalance_trades(
    rebalance_plan: RebalancePlan,
    correlation_id: str,
    causation_id: str,
    queue_url: str,
    runs_table_name: str,
    *,
    alpaca_equity: Decimal | None = None,
    data_freshness: dict[str, Any] | None = None,
    strategies_evaluated: int = 0,
) -> int:
    """Decompose rebalance plan and enqueue to SQS FIFO queue for parallel execution.

    Two-Phase Parallel Execution Architecture:
    1. Creates TradeMessage for each BUY/SELL item (skips HOLD)
    2. Creates run state entry in DynamoDB (BUY trades stored with status=WAITING)
    3. Enqueues only SELL trades to SQS FIFO queue (MessageGroupId + MessageDeduplicationId)
    4. When last SELL completes, Execution Lambda enqueues BUY trades
    5. Multiple Lambda invocations process BUYs in parallel

    Args:
        rebalance_plan: The rebalance plan to decompose.
        correlation_id: Workflow correlation ID.
        causation_id: Event that caused this operation.
        queue_url: SQS queue URL for trade execution.
        runs_table_name: DynamoDB table name for execution run tracking.
        alpaca_equity: Alpaca account equity for circuit breaker calculation.
        data_freshness: Data freshness info from strategy phase.
        strategies_evaluated: Number of DSL strategy files evaluated.

    Returns:
        Number of trades enqueued.

    """
    run_id = str(uuid.uuid4())
    run_timestamp = datetime.now(UTC)

    # Pre-compute total non-HOLD trades once (avoid re-counting per item)
    total_run_trades = sum(1 for i in rebalance_plan.items if i.action in ["BUY", "SELL"])

    trade_messages: list[TradeMessage] = []
    for item in rebalance_plan.items:
        if item.action == "HOLD":
            continue

        sequence_number = TradeMessage.compute_sequence_number(item.action, item.priority)

        is_complete_exit = (
            item.action == "SELL"
            and item.target_weight == Decimal("0")
            and item.current_weight > Decimal("0")
        )
        is_full_liquidation = item.target_weight == Decimal("0")

        trade_message = TradeMessage(
            run_id=run_id,
            trade_id=str(uuid.uuid4()),
            plan_id=rebalance_plan.plan_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
            strategy_id=rebalance_plan.strategy_id,
            symbol=item.symbol,
            action=item.action,
            trade_amount=item.trade_amount,
            current_weight=item.current_weight,
            target_weight=item.target_weight,
            target_value=item.target_value,
            current_value=item.current_value,
            priority=item.priority,
            phase=item.action,
            sequence_number=sequence_number,
            is_complete_exit=is_complete_exit,
            is_full_liquidation=is_full_liquidation,
            total_portfolio_value=rebalance_plan.total_portfolio_value,
            total_run_trades=total_run_trades,
            run_timestamp=run_timestamp,
            metadata=rebalance_plan.metadata,
        )
        trade_messages.append(trade_message)

    if not trade_messages:
        logger.info(
            "No trades to enqueue (all HOLD)",
            extra={"correlation_id": correlation_id},
        )
        return 0

    trade_messages.sort(key=lambda m: m.sequence_number)

    sell_trades = [m for m in trade_messages if m.phase == "SELL"]
    buy_trades = [m for m in trade_messages if m.phase == "BUY"]

    # Calculate max equity deployment limit for circuit breaker
    settings = load_settings()
    equity_deployment_pct = Decimal(str(settings.alpaca.effective_deployment_pct))
    circuit_breaker_equity = (
        alpaca_equity if alpaca_equity else rebalance_plan.total_portfolio_value
    )
    max_equity_limit_usd = circuit_breaker_equity * equity_deployment_pct

    logger.info(
        "Calculated equity deployment limit for circuit breaker",
        extra={
            "run_id": run_id,
            "correlation_id": correlation_id,
            "alpaca_equity": str(alpaca_equity) if alpaca_equity else "N/A",
            "circuit_breaker_equity": str(circuit_breaker_equity),
            "equity_deployment_pct": str(equity_deployment_pct),
            "max_equity_limit_usd": str(max_equity_limit_usd),
        },
    )

    run_service = ExecutionRunService(table_name=runs_table_name)

    rebalance_plan_summary = [
        {
            "symbol": item.symbol,
            "action": item.action,
            "current_weight_pct": float(item.current_weight * 100),
            "target_weight_pct": float(item.target_weight * 100),
            "trade_amount": float(item.trade_amount),
        }
        for item in rebalance_plan.items
        if item.action in ["BUY", "SELL"]
    ]

    run_service.create_run(
        run_id=run_id,
        plan_id=rebalance_plan.plan_id,
        correlation_id=correlation_id,
        trade_messages=trade_messages,
        run_timestamp=run_timestamp,
        enqueue_sells_only=True,
        max_equity_limit_usd=max_equity_limit_usd,
        data_freshness=data_freshness,
        strategies_evaluated=strategies_evaluated,
        rebalance_plan_summary=rebalance_plan_summary,
        strategy_id=rebalance_plan.strategy_id,
    )

    sqs_client = boto3.client("sqs")
    enqueued_count = 0

    # Handle edge case: 0 SELLs means go directly to BUY phase
    if len(sell_trades) == 0 and len(buy_trades) > 0:
        logger.info(
            "No SELL trades - transitioning directly to BUY phase",
            extra={
                "run_id": run_id,
                "correlation_id": correlation_id,
                "buy_count": len(buy_trades),
            },
        )
        run_service.transition_to_buy_phase(run_id)

        try:
            for msg in buy_trades:
                sqs_client.send_message(
                    QueueUrl=queue_url,
                    MessageBody=msg.to_sqs_message_body(),
                    MessageDeduplicationId=msg.trade_id,
                    MessageGroupId=msg.symbol,
                    MessageAttributes={
                        "RunId": {"DataType": "String", "StringValue": run_id},
                        "TradeId": {"DataType": "String", "StringValue": msg.trade_id},
                        "Phase": {"DataType": "String", "StringValue": msg.phase},
                    },
                )
                enqueued_count += 1

            run_service.mark_buy_trades_pending(run_id, [t.trade_id for t in buy_trades])

            logger.info(
                "Enqueued BUY trades directly (0 SELLs scenario)",
                extra={
                    "run_id": run_id,
                    "correlation_id": correlation_id,
                    "buy_enqueued": len(buy_trades),
                },
            )
            return enqueued_count

        except Exception as enqueue_error:
            logger.error(
                f"SQS enqueue failed for BUY trades: {enqueue_error}",
                extra={
                    "run_id": run_id,
                    "correlation_id": correlation_id,
                    "enqueued_count": enqueued_count,
                    "total_buys": len(buy_trades),
                },
            )
            run_service.update_run_status(run_id, "FAILED")
            raise

    # Normal two-phase: enqueue SELL trades first
    try:
        for msg in sell_trades:
            sqs_client.send_message(
                QueueUrl=queue_url,
                MessageBody=msg.to_sqs_message_body(),
                MessageDeduplicationId=msg.trade_id,
                MessageGroupId=msg.symbol,
                MessageAttributes={
                    "RunId": {"DataType": "String", "StringValue": run_id},
                    "TradeId": {"DataType": "String", "StringValue": msg.trade_id},
                    "Phase": {"DataType": "String", "StringValue": msg.phase},
                },
            )
            enqueued_count += 1

    except Exception as enqueue_error:
        logger.error(
            f"SQS enqueue failed after {enqueued_count}/{len(sell_trades)} SELL messages: {enqueue_error}",
            extra={
                "run_id": run_id,
                "correlation_id": correlation_id,
                "enqueued_count": enqueued_count,
                "total_sells": len(sell_trades),
                "total_buys": len(buy_trades),
                "error_type": type(enqueue_error).__name__,
                "error_details": str(enqueue_error),
            },
        )
        try:
            run_service.update_run_status(run_id, "FAILED")
            logger.info(
                f"Marked run {run_id} as FAILED due to SQS enqueue error",
                extra={"run_id": run_id, "correlation_id": correlation_id},
            )
        except Exception as status_error:
            logger.error(
                f"Failed to mark run as FAILED: {status_error}",
                extra={"run_id": run_id, "correlation_id": correlation_id},
            )
        raise

    logger.info(
        "Enqueued SELL trades for parallel execution (BUYs waiting for SELL completion)",
        extra={
            "run_id": run_id,
            "correlation_id": correlation_id,
            "total_trades": len(trade_messages),
            "sell_enqueued": len(sell_trades),
            "buy_waiting": len(buy_trades),
            "execution_mode": "two_phase_parallel",
        },
    )

    return enqueued_count
