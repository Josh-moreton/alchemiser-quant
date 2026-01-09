"""Business Unit: trade_aggregator | Status: current.

Service for aggregating trade execution results.

Reuses the existing execution-runs DynamoDB table to track trade completion
and aggregate results when all trades finish. Uses atomic counter pattern
(like AggregationSessionService) to ensure exactly-once aggregation.
"""

from __future__ import annotations

import contextlib
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

import boto3

from the_alchemiser.shared.config import DYNAMODB_RETRY_CONFIG
from the_alchemiser.shared.logging import get_logger

if TYPE_CHECKING:
    from mypy_boto3_dynamodb import DynamoDBClient

logger = get_logger(__name__)


class TradeAggregatorService:
    """Aggregates trade execution results using the execution-runs table.

    This service is used by the TradeAggregator Lambda to:
    1. Record that a trade event was received (idempotent via conditional put)
    2. Check if all trades in a run have completed
    3. Claim aggregation lock to ensure only one invocation aggregates
    4. Aggregate trade results for the AllTradesCompleted event

    Unlike the notifications model, this service uses the atomic counter pattern
    from AggregationSessionService, which eliminates racing by making the
    completion check and status transition atomic.

    DynamoDB Schema (reuses execution-runs table):
        PK: RUN#{run_id}
        SK: METADATA | TRADE#{trade_id}

    Key fields used:
        - completed_trades: Atomic counter incremented per trade
        - total_trades: Target count for completion check
        - status: RUNNING | AGGREGATING | COMPLETED | FAILED
    """

    def __init__(
        self,
        table_name: str,
        region: str | None = None,
    ) -> None:
        """Initialize the trade aggregator service.

        Args:
            table_name: DynamoDB table name (execution-runs table).
            region: AWS region (defaults to AWS_REGION env var).

        """
        self._table_name = table_name
        self._region = region
        self._client: DynamoDBClient = boto3.client(
            "dynamodb",
            region_name=self._region,
            config=DYNAMODB_RETRY_CONFIG,
        )
        logger.debug(
            "TradeAggregatorService initialized",
            extra={"table_name": table_name},
        )

    def record_trade_completed(
        self,
        run_id: str,
        trade_id: str,
    ) -> tuple[int, int]:
        """Record that a trade completed and return completion counts.

        This is idempotent - if the trade was already recorded by execution lambda,
        we just read the current count without incrementing again.

        The key insight: Execution Lambda already calls mark_trade_completed()
        which increments completed_trades. We just need to read the current
        state and check for completion.

        Args:
            run_id: Execution run identifier.
            trade_id: Trade identifier that completed.

        Returns:
            Tuple of (completed_trades, total_trades).

        """
        # Get current run state
        response = self._client.get_item(
            TableName=self._table_name,
            Key={
                "PK": {"S": f"RUN#{run_id}"},
                "SK": {"S": "METADATA"},
            },
        )

        item = response.get("Item")
        if not item:
            logger.warning(
                "Run not found for trade completion",
                extra={"run_id": run_id, "trade_id": trade_id},
            )
            return (0, 0)

        completed = int(item.get("completed_trades", {}).get("N", "0"))
        total = int(item.get("total_trades", {}).get("N", "0"))

        logger.debug(
            "Checked run completion state",
            extra={
                "run_id": run_id,
                "trade_id": trade_id,
                "completed_trades": completed,
                "total_trades": total,
            },
        )

        return (completed, total)

    def try_claim_aggregation(self, run_id: str) -> bool:
        """Atomically claim the right to aggregate this run.

        Uses conditional update to transition from an active status to AGGREGATING.
        Only one invocation can succeed - all others will get
        ConditionalCheckFailedException.

        This is the key to eliminating races: the aggregation claim is atomic
        with the status check.

        Args:
            run_id: Execution run identifier.

        Returns:
            True if this invocation claimed aggregation rights, False otherwise.

        """
        now = datetime.now(UTC)

        try:
            # Atomically transition from active status to AGGREGATING
            # Accept RUNNING, SELL_PHASE, or BUY_PHASE as valid starting states
            self._client.update_item(
                TableName=self._table_name,
                Key={
                    "PK": {"S": f"RUN#{run_id}"},
                    "SK": {"S": "METADATA"},
                },
                UpdateExpression="SET #status = :aggregating, aggregation_started_at = :now",
                ConditionExpression="#status IN (:running, :sell_phase, :buy_phase)",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":aggregating": {"S": "AGGREGATING"},
                    ":running": {"S": "RUNNING"},
                    ":sell_phase": {"S": "SELL_PHASE"},
                    ":buy_phase": {"S": "BUY_PHASE"},
                    ":now": {"S": now.isoformat()},
                },
            )

            logger.info(
                "Claimed aggregation lock",
                extra={"run_id": run_id, "claimed_at": now.isoformat()},
            )
            return True

        except self._client.exceptions.ConditionalCheckFailedException:
            # Another invocation already claimed it or status is COMPLETED/FAILED
            logger.debug(
                "Aggregation already claimed by another invocation",
                extra={"run_id": run_id},
            )
            return False

    def get_run_metadata(self, run_id: str) -> dict[str, Any] | None:
        """Get run metadata.

        Args:
            run_id: Run identifier.

        Returns:
            Run metadata dict or None if not found.

        """
        response = self._client.get_item(
            TableName=self._table_name,
            Key={
                "PK": {"S": f"RUN#{run_id}"},
                "SK": {"S": "METADATA"},
            },
        )

        item = response.get("Item")
        if not item:
            return None

        return {
            "run_id": item["run_id"]["S"],
            "plan_id": item.get("plan_id", {}).get("S", ""),
            "correlation_id": item.get("correlation_id", {}).get("S", ""),
            "total_trades": int(item.get("total_trades", {}).get("N", "0")),
            "completed_trades": int(item.get("completed_trades", {}).get("N", "0")),
            "succeeded_trades": int(item.get("succeeded_trades", {}).get("N", "0")),
            "failed_trades": int(item.get("failed_trades", {}).get("N", "0")),
            "skipped_trades": int(item.get("skipped_trades", {}).get("N", "0")),
            "status": item.get("status", {}).get("S", "UNKNOWN"),
            "created_at": item.get("created_at", {}).get("S", ""),
            # Data freshness stored as JSON string in DynamoDB
            "data_freshness": item.get("data_freshness", {}).get("S", ""),
        }

    def get_all_trade_results(self, run_id: str) -> list[dict[str, Any]]:
        """Get all trade results for a run.

        Args:
            run_id: Run identifier.

        Returns:
            List of trade result dicts.

        """
        response = self._client.query(
            TableName=self._table_name,
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
            ExpressionAttributeValues={
                ":pk": {"S": f"RUN#{run_id}"},
                ":sk_prefix": {"S": "TRADE#"},
            },
        )

        trades: list[dict[str, Any]] = []
        for item in response.get("Items", []):
            trade: dict[str, Any] = {
                "trade_id": item["trade_id"]["S"],
                "symbol": item.get("symbol", {}).get("S", ""),
                "action": item.get("action", {}).get("S", ""),
                "phase": item.get("phase", {}).get("S", ""),
                "status": item.get("status", {}).get("S", "UNKNOWN"),
                "order_id": item.get("order_id", {}).get("S"),
                "error_message": item.get("error_message", {}).get("S"),
            }

            # Parse trade amount
            trade_amount_raw = item.get("trade_amount", {}).get("N")
            if trade_amount_raw:
                trade["trade_amount"] = Decimal(trade_amount_raw)

            # Parse execution data if present
            execution_data_raw = item.get("execution_data", {}).get("S")
            if execution_data_raw:
                import json

                with contextlib.suppress(json.JSONDecodeError):
                    trade["execution_data"] = json.loads(execution_data_raw)

            trades.append(trade)

        logger.debug(
            "Retrieved trade results",
            extra={"run_id": run_id, "trade_count": len(trades)},
        )

        return trades

    def mark_run_completed(self, run_id: str) -> None:
        """Mark run as completed after successful aggregation.

        Args:
            run_id: Run identifier.

        """
        now = datetime.now(UTC)

        self._client.update_item(
            TableName=self._table_name,
            Key={
                "PK": {"S": f"RUN#{run_id}"},
                "SK": {"S": "METADATA"},
            },
            UpdateExpression="SET #status = :completed, completed_at = :now",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":completed": {"S": "COMPLETED"},
                ":now": {"S": now.isoformat()},
            },
        )

        logger.info(
            "Marked run as completed",
            extra={"run_id": run_id, "completed_at": now.isoformat()},
        )

    def mark_run_failed(self, run_id: str, error_message: str) -> None:
        """Mark run as failed.

        Args:
            run_id: Run identifier.
            error_message: Error description.

        """
        now = datetime.now(UTC)

        self._client.update_item(
            TableName=self._table_name,
            Key={
                "PK": {"S": f"RUN#{run_id}"},
                "SK": {"S": "METADATA"},
            },
            UpdateExpression="SET #status = :failed, failed_at = :now, failure_reason = :error",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":failed": {"S": "FAILED"},
                ":now": {"S": now.isoformat()},
                ":error": {"S": error_message},
            },
        )

        logger.info(
            "Marked run as failed",
            extra={"run_id": run_id, "error_message": error_message},
        )

    def aggregate_trade_results(
        self,
        run_metadata: dict[str, Any],
        trade_results: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Aggregate trade results into summary for AllTradesCompleted event.

        Separates actual failures from expected skips (non-fractionable assets
        where quantity rounds to zero). This enables partial success emails
        when only non-fractionable skips occurred.

        Args:
            run_metadata: Run metadata from DynamoDB.
            trade_results: List of individual trade results.

        Returns:
            Aggregated execution data dict with failed_symbols and
            non_fractionable_skipped_symbols separated.

        """
        total_trades = run_metadata.get("total_trades", len(trade_results))
        succeeded = run_metadata.get("succeeded_trades", 0)
        failed = run_metadata.get("failed_trades", 0)

        # Calculate total trade value
        total_value = Decimal("0")
        orders_executed: list[dict[str, Any]] = []
        failed_symbols: list[str] = []
        non_fractionable_skipped_symbols: list[str] = []

        # Pattern to identify non-fractionable skips in error messages
        non_fractionable_pattern = "rounds to zero"

        for trade in trade_results:
            trade_amount = trade.get("trade_amount", Decimal("0"))
            if isinstance(trade_amount, str):
                trade_amount = Decimal(trade_amount)
            total_value += abs(trade_amount)

            order_summary = {
                "symbol": trade.get("symbol"),
                "action": trade.get("action"),
                "status": trade.get("status"),
                "order_id": trade.get("order_id"),
                "trade_amount": str(trade_amount),
            }
            orders_executed.append(order_summary)

            if trade.get("status") == "FAILED":
                symbol = trade.get("symbol", "unknown")
                error_message = trade.get("error_message", "") or ""

                # Categorize: non-fractionable skip vs actual failure
                if non_fractionable_pattern in error_message.lower():
                    if symbol not in non_fractionable_skipped_symbols:
                        non_fractionable_skipped_symbols.append(symbol)
                        logger.debug(
                            f"Categorized {symbol} as non-fractionable skip",
                            extra={"error_message": error_message},
                        )
                else:
                    if symbol not in failed_symbols:
                        failed_symbols.append(symbol)

        return {
            "orders_executed": orders_executed,
            "execution_summary": {
                "total_trades": total_trades,
                "succeeded": succeeded,
                "failed": failed,
                "total_value": str(total_value),
                "symbols_evaluated": total_trades,  # Approximation: total planned trades
                "eligible_signals": total_trades,  # Approximation: all planned trades are eligible signals
                "blocked_by_risk": failed,  # Approximation: failed trades = blocked by risk (conservative estimate)
            },
            "failed_symbols": failed_symbols,
            "non_fractionable_skipped_symbols": non_fractionable_skipped_symbols,
        }
