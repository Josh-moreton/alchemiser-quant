"""Business Unit: shared | Status: current.

Service for managing execution run state in DynamoDB.

Execution runs track the state of per-trade execution, including which trades
have completed and their results. This follows the same pattern as the
AggregationSessionService used for Strategy multi-node scaling.

Design Principle: Execution Lambda writes trade results here. Notifications Lambda
reads and interprets the run state to detect completion and aggregate results.
This separation keeps write contention low and maintains clean separation of concerns.

Note: This service is in shared/ because it's used by multiple business modules:
- portfolio_v2: Creates runs when decomposing RebalancePlans
- execution_v2: Marks trades as started/completed
- notifications_v2: Checks completion and aggregates results
"""

from __future__ import annotations

import contextlib
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Any, TypedDict, cast

import boto3

from the_alchemiser.shared.config import DYNAMODB_RETRY_CONFIG
from the_alchemiser.shared.logging import get_logger

if TYPE_CHECKING:
    from mypy_boto3_dynamodb import DynamoDBClient

    from the_alchemiser.shared.schemas.trade_message import TradeMessage

logger = get_logger(__name__)


class ExecutionRunService:
    """Manages execution run state in DynamoDB.

    DynamoDB Schema:
        PK: RUN#{run_id}
        SK: METADATA | TRADE#{trade_id}

    Run metadata item:
        - run_id, plan_id, correlation_id
        - total_trades, completed_trades (atomic counter)
        - succeeded_trades, failed_trades
        - sell_total, sell_completed, buy_total, buy_completed (phase tracking)
        - sell_failed_amount, sell_succeeded_amount (dollar tracking for BUY phase guard)
        - current_phase: SELL | BUY | COMPLETED (two-phase execution)
        - status: PENDING | RUNNING | SELL_PHASE | BUY_PHASE | NOTIFYING | COMPLETED | FAILED
        - notification_lock_at, notification_lock_expires (two-phase notification locking)
        - created_at, TTL

    Trade result items (one per trade):
        - trade_id, symbol, action, phase
        - status: PENDING | RUNNING | COMPLETED | FAILED
        - order_id, error_message
        - started_at, completed_at

    Phase Execution Flow:
        1. Portfolio Lambda enqueues only SELL trades, sets current_phase=SELL
        2. When all SELLs complete, BUY phase guard checks sell_failed_amount
        3. If sell_failed_amount > threshold, BUY phase is BLOCKED (run marked FAILED)
        4. If within threshold, BUY trades are enqueued and current_phase=BUY
        5. When all BUYs complete, run is marked COMPLETED
    """

    def __init__(
        self,
        table_name: str,
        region: str | None = None,
    ) -> None:
        """Initialize the execution run service.

        Args:
            table_name: DynamoDB table name for run state.
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
            "ExecutionRunService initialized",
            extra={"table_name": table_name},
        )

    def create_run(
        self,
        run_id: str,
        plan_id: str,
        correlation_id: str,
        trade_messages: list[TradeMessage],
        run_timestamp: datetime,
        *,
        enqueue_sells_only: bool = False,
        max_equity_limit_usd: Decimal | None = None,
        data_freshness: dict[str, Any] | None = None,
        strategies_evaluated: int | None = None,
        rebalance_plan_summary: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Create a new execution run with optional two-phase execution.

        Called by Portfolio Lambda when decomposing a RebalancePlan into
        individual TradeMessages.

        For two-phase execution (enqueue_sells_only=True):
        - Only SELL trades are enqueued immediately
        - BUY trades are stored in DynamoDB for later enqueue
        - current_phase is set to "SELL"
        - When SELLs complete, trigger_buy_phase() enqueues the BUYs

        Args:
            run_id: Unique run identifier (UUID).
            plan_id: Source RebalancePlan identifier.
            correlation_id: Workflow correlation ID for tracing.
            trade_messages: List of TradeMessage objects for this run.
            run_timestamp: When the run started.
            enqueue_sells_only: If True, only SELL trades are enqueued now.
            max_equity_limit_usd: Maximum allowed equity deployment (circuit breaker limit).
                Calculated as portfolio_equity * EQUITY_DEPLOYMENT_PCT.
            data_freshness: Data freshness info from strategy phase.
            strategies_evaluated: Number of DSL strategy files evaluated.
            rebalance_plan_summary: Serialized rebalance plan items for email display.

        Returns:
            Run metadata dict.

        """
        now = datetime.now(UTC)
        ttl = int((now + timedelta(hours=24)).timestamp())

        # Separate trades by phase for tracking
        sell_trades = [m for m in trade_messages if m.phase == "SELL"]
        buy_trades = [m for m in trade_messages if m.phase == "BUY"]

        # For two-phase execution, only track sells as "active" initially
        if enqueue_sells_only:
            current_phase = "SELL"
            status = "SELL_PHASE"
        else:
            current_phase = "ALL"  # Legacy single-phase mode
            status = "PENDING"

        # Create run metadata item with phase tracking
        item = cast(
            "dict[str, dict[str, Any]]",
            {
                "PK": {"S": f"RUN#{run_id}"},
                "SK": {"S": "METADATA"},
                "run_id": {"S": run_id},
                "plan_id": {"S": plan_id},
                "correlation_id": {"S": correlation_id},
                "total_trades": {"N": str(len(trade_messages))},
                "completed_trades": {"N": "0"},
                "succeeded_trades": {"N": "0"},
                "failed_trades": {"N": "0"},
                "skipped_trades": {"N": "0"},
                # Phase tracking for two-phase execution
                "sell_total": {"N": str(len(sell_trades))},
                "sell_completed": {"N": "0"},
                "buy_total": {"N": str(len(buy_trades))},
                "buy_completed": {"N": "0"},
                # Dollar amount tracking for BUY phase guard
                "sell_failed_amount": {"N": "0"},
                "sell_succeeded_amount": {"N": "0"},
                # Equity deployment circuit breaker (BUY phase limit)
                "cumulative_buy_succeeded_value": {"N": "0"},
                "max_equity_limit_usd": {
                    "N": str(max_equity_limit_usd) if max_equity_limit_usd else "0"
                },
                "current_phase": {"S": current_phase},
                "status": {"S": status},
                "run_timestamp": {"S": run_timestamp.isoformat()},
                "created_at": {"S": now.isoformat()},
                "TTL": {"N": str(ttl)},
                # Store trade IDs for reference
                "trade_ids": {"L": [{"S": msg.trade_id} for msg in trade_messages]},
            },
        )

        # Store data freshness as JSON if provided
        if data_freshness:
            import json

            item["data_freshness"] = {"S": json.dumps(data_freshness)}

        # Store strategies_evaluated count
        if strategies_evaluated is not None:
            item["strategies_evaluated"] = {"N": str(strategies_evaluated)}

        # Store rebalance_plan_summary as JSON for email display
        if rebalance_plan_summary:
            import json

            item["rebalance_plan_summary"] = {"S": json.dumps(rebalance_plan_summary)}

        self._client.put_item(TableName=self._table_name, Item=item)

        # Create pending trade items for each trade
        for msg in trade_messages:
            # For two-phase execution, mark BUY trades as WAITING (not yet enqueued)
            initial_status = "PENDING"
            if enqueue_sells_only and msg.phase == "BUY":
                initial_status = "WAITING"  # Will be enqueued when SELLs complete

            trade_item = cast(
                "dict[str, dict[str, Any]]",
                {
                    "PK": {"S": f"RUN#{run_id}"},
                    "SK": {"S": f"TRADE#{msg.trade_id}"},
                    "trade_id": {"S": msg.trade_id},
                    "symbol": {"S": msg.symbol},
                    "action": {"S": msg.action},
                    "phase": {"S": msg.phase},
                    "sequence_number": {"N": str(msg.sequence_number)},
                    "trade_amount": {"N": str(msg.trade_amount)},
                    "status": {"S": initial_status},
                    "TTL": {"N": str(ttl)},
                    # Store full message body for deferred BUY enqueue
                    "message_body": {"S": msg.to_sqs_message_body()},
                },
            )
            self._client.put_item(TableName=self._table_name, Item=trade_item)

        logger.info(
            "Created execution run",
            extra={
                "run_id": run_id,
                "plan_id": plan_id,
                "correlation_id": correlation_id,
                "total_trades": len(trade_messages),
                "sell_count": len(sell_trades),
                "buy_count": len(buy_trades),
                "current_phase": current_phase,
                "enqueue_sells_only": enqueue_sells_only,
            },
        )

        return {
            "run_id": run_id,
            "plan_id": plan_id,
            "correlation_id": correlation_id,
            "total_trades": len(trade_messages),
            "completed_trades": 0,
            "sell_total": len(sell_trades),
            "sell_completed": 0,
            "sell_failed_amount": Decimal("0"),
            "sell_succeeded_amount": Decimal("0"),
            "cumulative_buy_succeeded_value": Decimal("0"),
            "max_equity_limit_usd": max_equity_limit_usd or Decimal("0"),
            "buy_total": len(buy_trades),
            "buy_completed": 0,
            "current_phase": current_phase,
            "status": status,
            "created_at": now.isoformat(),
        }

    def mark_trade_started(
        self,
        run_id: str,
        trade_id: str,
    ) -> None:
        """Mark a trade as started (RUNNING).

        Called by Execution Lambda when beginning trade execution.

        Args:
            run_id: Run identifier.
            trade_id: Trade identifier.

        """
        now = datetime.now(UTC)

        # Update trade status
        self._client.update_item(
            TableName=self._table_name,
            Key={
                "PK": {"S": f"RUN#{run_id}"},
                "SK": {"S": f"TRADE#{trade_id}"},
            },
            UpdateExpression="SET #status = :status, started_at = :started_at",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":status": {"S": "RUNNING"},
                ":started_at": {"S": now.isoformat()},
            },
        )

        # Update run status to RUNNING if still PENDING
        with contextlib.suppress(self._client.exceptions.ConditionalCheckFailedException):
            self._client.update_item(
                TableName=self._table_name,
                Key={
                    "PK": {"S": f"RUN#{run_id}"},
                    "SK": {"S": "METADATA"},
                },
                UpdateExpression="SET #status = :running",
                ConditionExpression="#status = :pending",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":running": {"S": "RUNNING"},
                    ":pending": {"S": "PENDING"},
                },
            )

        logger.debug(
            "Marked trade as started",
            extra={"run_id": run_id, "trade_id": trade_id},
        )

    def mark_trade_completed(
        self,
        run_id: str,
        trade_id: str,
        *,
        success: bool,
        skipped: bool = False,
        order_id: str | None = None,
        error_message: str | None = None,
        execution_data: dict[str, Any] | None = None,
        phase: str | None = None,
        trade_amount: Decimal | None = None,
    ) -> dict[str, Any]:
        """Mark a trade as completed and increment completion counters.

        Called by Execution Lambda after trade execution completes.
        Uses conditional put to ensure idempotency.
        Updates both overall and phase-specific counters for two-phase execution.

        For SELL phase trades, also tracks dollar amounts (sell_failed_amount,
        sell_succeeded_amount) for the BUY phase guard that prevents over-deployment.

        Args:
            run_id: Run identifier.
            trade_id: Trade identifier.
            success: Whether the trade succeeded.
            skipped: Whether the trade was skipped (e.g., market closed).
            order_id: Broker order ID if available.
            error_message: Error message if failed.
            execution_data: Additional execution data.
            phase: Trade phase (SELL or BUY) for phase-specific counter updates.
            trade_amount: Dollar amount of the trade (for SELL phase guard tracking).

        Returns:
            Dict with completion info including phase_complete flag and
            sell_failed_amount for BUY phase guard evaluation.

        """
        import json

        now = datetime.now(UTC)
        status = "COMPLETED" if success else "FAILED"

        # Build update expression for trade item
        update_expr = "SET #status = :status, completed_at = :completed_at"
        expr_names: dict[str, str] = {"#status": "status"}
        expr_values: dict[str, dict[str, str]] = {
            ":status": {"S": status},
            ":completed_at": {"S": now.isoformat()},
        }

        if order_id:
            update_expr += ", order_id = :order_id"
            expr_values[":order_id"] = {"S": order_id}

        if error_message:
            update_expr += ", error_message = :error_message"
            expr_values[":error_message"] = {"S": error_message}

        if execution_data:
            update_expr += ", execution_data = :execution_data"
            expr_values[":execution_data"] = {"S": json.dumps(execution_data, default=str)}

        # Update trade item (idempotent - only if not already completed)
        try:
            self._client.update_item(
                TableName=self._table_name,
                Key={
                    "PK": {"S": f"RUN#{run_id}"},
                    "SK": {"S": f"TRADE#{trade_id}"},
                },
                UpdateExpression=update_expr,
                ConditionExpression="#status <> :completed AND #status <> :failed",
                ExpressionAttributeNames=expr_names,
                ExpressionAttributeValues={
                    **expr_values,
                    ":completed": {"S": "COMPLETED"},
                    ":failed": {"S": "FAILED"},
                },
            )

            # Increment counters atomically - both overall and phase-specific
            # Determine which counter to increment based on outcome
            if skipped:
                counter_field = "skipped_trades"
            elif success:
                counter_field = "succeeded_trades"
            else:
                counter_field = "failed_trades"

            # Build update expression for phase-specific counters
            if phase == "SELL":
                phase_counter = "sell_completed"
            elif phase == "BUY":
                phase_counter = "buy_completed"
            else:
                phase_counter = None

            if phase_counter:
                update_expression = (
                    f"ADD completed_trades :one, {counter_field} :one, {phase_counter} :one"
                )
            else:
                update_expression = f"ADD completed_trades :one, {counter_field} :one"

            # Track dollar amounts for phase guards
            # CRITICAL: Skip amount tracking for skipped trades to avoid corrupting risk calculations
            expr_attr_values: dict[str, dict[str, str]] = {":one": {"N": "1"}}
            if trade_amount is not None and not skipped:
                amount_str = str(abs(trade_amount))
                # For SELL phase, track sell_failed_amount and sell_succeeded_amount
                if phase == "SELL":
                    if success:
                        update_expression += ", sell_succeeded_amount :amount"
                    else:
                        update_expression += ", sell_failed_amount :amount"
                    expr_attr_values[":amount"] = {"N": amount_str}
                # For BUY phase, track cumulative_buy_succeeded_value for equity circuit breaker
                elif phase == "BUY" and success:
                    update_expression += ", cumulative_buy_succeeded_value :amount"
                    expr_attr_values[":amount"] = {"N": amount_str}

            response = self._client.update_item(
                TableName=self._table_name,
                Key={
                    "PK": {"S": f"RUN#{run_id}"},
                    "SK": {"S": "METADATA"},
                },
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expr_attr_values,
                ReturnValues="ALL_NEW",
            )

            attrs = response.get("Attributes", {})
            completed = int(attrs.get("completed_trades", {"N": "0"})["N"])
            total = int(attrs.get("total_trades", {"N": "0"})["N"])
            succeeded_trades = int(attrs.get("succeeded_trades", {"N": "0"})["N"])
            failed_trades = int(attrs.get("failed_trades", {"N": "0"})["N"])
            skipped_trades = int(attrs.get("skipped_trades", {"N": "0"})["N"])
            sell_completed = int(attrs.get("sell_completed", {"N": "0"})["N"])
            sell_total = int(attrs.get("sell_total", {"N": "0"})["N"])
            buy_completed = int(attrs.get("buy_completed", {"N": "0"})["N"])
            buy_total = int(attrs.get("buy_total", {"N": "0"})["N"])
            current_phase = attrs.get("current_phase", {"S": "ALL"})["S"]
            # Dollar amounts for BUY phase guard
            sell_failed_amount = Decimal(attrs.get("sell_failed_amount", {"N": "0"})["N"])
            sell_succeeded_amount = Decimal(attrs.get("sell_succeeded_amount", {"N": "0"})["N"])
            # Equity deployment circuit breaker fields
            cumulative_buy_succeeded_value = Decimal(
                attrs.get("cumulative_buy_succeeded_value", {"N": "0"})["N"]
            )
            max_equity_limit_usd = Decimal(attrs.get("max_equity_limit_usd", {"N": "0"})["N"])

            # Determine if phase is complete
            # Note: When sell_total == 0, the SELL phase is immediately complete
            # (there's nothing to sell), so we should proceed to BUY phase
            sell_phase_complete = sell_total == 0 or sell_completed >= sell_total
            buy_phase_complete = buy_completed >= buy_total
            run_complete = completed >= total

            logger.info(
                "Marked trade as completed",
                extra={
                    "run_id": run_id,
                    "trade_id": trade_id,
                    "success": success,
                    "phase": phase,
                    "completed_trades": completed,
                    "sell_completed": sell_completed,
                    "sell_total": sell_total,
                    "buy_completed": buy_completed,
                    "buy_total": buy_total,
                    "sell_phase_complete": sell_phase_complete,
                    "current_phase": current_phase,
                    "sell_failed_amount": str(sell_failed_amount),
                    "sell_succeeded_amount": str(sell_succeeded_amount),
                },
            )

            return {
                "completed_trades": completed,
                "total_trades": total,
                "succeeded_trades": succeeded_trades,
                "failed_trades": failed_trades,
                "skipped_trades": skipped_trades,
                "sell_completed": sell_completed,
                "sell_total": sell_total,
                "buy_completed": buy_completed,
                "buy_total": buy_total,
                "current_phase": current_phase,
                "sell_phase_complete": sell_phase_complete,
                "buy_phase_complete": buy_phase_complete,
                "run_complete": run_complete,
                "sell_failed_amount": sell_failed_amount,
                "sell_succeeded_amount": sell_succeeded_amount,
                "cumulative_buy_succeeded_value": cumulative_buy_succeeded_value,
                "max_equity_limit_usd": max_equity_limit_usd,
            }

        except self._client.exceptions.ConditionalCheckFailedException:
            # Trade already marked as completed - get current state
            logger.warning(
                "Trade already completed (duplicate)",
                extra={"run_id": run_id, "trade_id": trade_id},
            )
            run = self.get_run(run_id)
            if run:
                return {
                    "completed_trades": run.get("completed_trades", 0),
                    "total_trades": run.get("total_trades", 0),
                    "succeeded_trades": run.get("succeeded_trades", 0),
                    "failed_trades": run.get("failed_trades", 0),
                    "skipped_trades": run.get("skipped_trades", 0),
                    "sell_completed": run.get("sell_completed", 0),
                    "sell_total": run.get("sell_total", 0),
                    "buy_completed": run.get("buy_completed", 0),
                    "buy_total": run.get("buy_total", 0),
                    "current_phase": run.get("current_phase", "ALL"),
                    "sell_phase_complete": run.get("sell_completed", 0) >= run.get("sell_total", 0),
                    "buy_phase_complete": run.get("buy_completed", 0) >= run.get("buy_total", 0),
                    "run_complete": run.get("completed_trades", 0) >= run.get("total_trades", 0),
                    "sell_failed_amount": run.get("sell_failed_amount", Decimal("0")),
                    "sell_succeeded_amount": run.get("sell_succeeded_amount", Decimal("0")),
                    "cumulative_buy_succeeded_value": run.get(
                        "cumulative_buy_succeeded_value", Decimal("0")
                    ),
                    "max_equity_limit_usd": run.get("max_equity_limit_usd", Decimal("0")),
                }
            return {
                "completed_trades": 0,
                "total_trades": 0,
                "succeeded_trades": 0,
                "failed_trades": 0,
                "skipped_trades": 0,
                "run_complete": False,
                "sell_failed_amount": Decimal("0"),
                "sell_succeeded_amount": Decimal("0"),
            }

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        """Get run metadata including phase tracking.

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
            "plan_id": item["plan_id"]["S"],
            "correlation_id": item["correlation_id"]["S"],
            "total_trades": int(item["total_trades"]["N"]),
            "completed_trades": int(item["completed_trades"]["N"]),
            "succeeded_trades": int(item.get("succeeded_trades", {"N": "0"})["N"]),
            "failed_trades": int(item.get("failed_trades", {"N": "0"})["N"]),
            "skipped_trades": int(item.get("skipped_trades", {"N": "0"})["N"]),
            # Phase tracking fields
            "sell_total": int(item.get("sell_total", {"N": "0"})["N"]),
            "sell_completed": int(item.get("sell_completed", {"N": "0"})["N"]),
            "buy_total": int(item.get("buy_total", {"N": "0"})["N"]),
            "buy_completed": int(item.get("buy_completed", {"N": "0"})["N"]),
            # Dollar amount tracking for BUY phase guard
            "sell_failed_amount": Decimal(item.get("sell_failed_amount", {"N": "0"})["N"]),
            "sell_succeeded_amount": Decimal(item.get("sell_succeeded_amount", {"N": "0"})["N"]),
            # Equity deployment circuit breaker fields
            "cumulative_buy_succeeded_value": Decimal(
                item.get("cumulative_buy_succeeded_value", {"N": "0"})["N"]
            ),
            "max_equity_limit_usd": Decimal(item.get("max_equity_limit_usd", {"N": "0"})["N"]),
            "current_phase": item.get("current_phase", {"S": "ALL"})["S"],
            "status": item["status"]["S"],
            "run_timestamp": item.get("run_timestamp", {}).get("S"),
            "created_at": item["created_at"]["S"],
        }

    def get_trade_result(self, run_id: str, trade_id: str) -> dict[str, Any] | None:
        """Get a single trade result by ID.

        Efficient O(1) lookup for checking if a trade exists/completed.
        Prefer this over get_all_trade_results() for duplicate detection.

        Args:
            run_id: Run identifier.
            trade_id: Trade identifier.

        Returns:
            Trade result dict or None if not found.

        """
        import json

        response = self._client.get_item(
            TableName=self._table_name,
            Key={
                "PK": {"S": f"RUN#{run_id}"},
                "SK": {"S": f"TRADE#{trade_id}"},
            },
        )

        item = response.get("Item")
        if not item:
            return None

        trade: dict[str, Any] = {
            "trade_id": item["trade_id"]["S"],
            "symbol": item["symbol"]["S"],
            "action": item["action"]["S"],
            "phase": item["phase"]["S"],
            "sequence_number": int(item["sequence_number"]["N"]),
            "trade_amount": Decimal(item["trade_amount"]["N"]),
            "status": item["status"]["S"],
        }

        # Optional fields
        if "order_id" in item:
            trade["order_id"] = item["order_id"]["S"]
        if "error_message" in item:
            trade["error_message"] = item["error_message"]["S"]
        if "started_at" in item:
            trade["started_at"] = item["started_at"]["S"]
        if "completed_at" in item:
            trade["completed_at"] = item["completed_at"]["S"]
        if "execution_data" in item:
            trade["execution_data"] = json.loads(item["execution_data"]["S"])

        return trade

    def get_all_trade_results(self, run_id: str) -> list[dict[str, Any]]:
        """Get all trade results for a run.

        Args:
            run_id: Run identifier.

        Returns:
            List of trade result dicts.

        """
        import json

        response = self._client.query(
            TableName=self._table_name,
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
            ExpressionAttributeValues={
                ":pk": {"S": f"RUN#{run_id}"},
                ":sk_prefix": {"S": "TRADE#"},
            },
        )

        trades = []
        for item in response.get("Items", []):
            trade = {
                "trade_id": item["trade_id"]["S"],
                "symbol": item["symbol"]["S"],
                "action": item["action"]["S"],
                "phase": item["phase"]["S"],
                "sequence_number": int(item["sequence_number"]["N"]),
                "trade_amount": Decimal(item["trade_amount"]["N"]),
                "status": item["status"]["S"],
            }

            # Optional fields
            if "order_id" in item:
                trade["order_id"] = item["order_id"]["S"]
            if "error_message" in item:
                trade["error_message"] = item["error_message"]["S"]
            if "started_at" in item:
                trade["started_at"] = item["started_at"]["S"]
            if "completed_at" in item:
                trade["completed_at"] = item["completed_at"]["S"]
            if "execution_data" in item:
                trade["execution_data"] = json.loads(item["execution_data"]["S"])

            trades.append(trade)

        # Sort by sequence_number (sells before buys)
        def get_sequence_number(t: dict[str, Any]) -> int:
            return int(t.get("sequence_number", 0))

        trades.sort(key=get_sequence_number)

        logger.debug(
            "Retrieved trade results",
            extra={"run_id": run_id, "trade_count": len(trades)},
        )

        return trades

    def is_run_complete(self, run_id: str) -> bool:
        """Check if a run is complete (all trades finished).

        This is called by Notifications Lambda to detect completion.
        Execution Lambda should NOT call this - it just writes facts.

        Args:
            run_id: Run identifier.

        Returns:
            True if all trades have completed (success or failure).

        """
        run = self.get_run(run_id)
        if not run:
            return False

        completed: int = run["completed_trades"]
        total: int = run["total_trades"]
        return completed >= total

    def claim_notification_lock(self, run_id: str, timeout_seconds: int = 60) -> bool:
        """Claim exclusive right to send notification for this run.

        Uses two-phase locking: (active status) -> NOTIFYING -> COMPLETED.
        This ensures that if notification sending fails, another invocation
        can retry after the lock expires.

        Active statuses that can transition to NOTIFYING:
        - RUNNING: Standard single-phase execution
        - SELL_PHASE: Two-phase execution, still in sells
        - BUY_PHASE: Two-phase execution, all sells done

        Args:
            run_id: Run identifier.
            timeout_seconds: How long the lock is valid (default 60s).

        Returns:
            True if this call acquired the lock, False if already locked/completed.

        """
        now = datetime.now(UTC)
        lock_expires_at = now + timedelta(seconds=timeout_seconds)

        try:
            # Allow any active status to transition to NOTIFYING
            # RUNNING = single-phase, SELL_PHASE/BUY_PHASE = two-phase execution
            # Also allow retaking an expired NOTIFYING lock
            self._client.update_item(
                TableName=self._table_name,
                Key={
                    "PK": {"S": f"RUN#{run_id}"},
                    "SK": {"S": "METADATA"},
                },
                UpdateExpression=(
                    "SET #status = :notifying, "
                    "notification_lock_at = :lock_at, "
                    "notification_lock_expires = :lock_expires"
                ),
                ConditionExpression=(
                    "#status IN (:running, :sell_phase, :buy_phase) "
                    "OR (#status = :notifying AND notification_lock_expires < :now)"
                ),
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":notifying": {"S": "NOTIFYING"},
                    ":running": {"S": "RUNNING"},
                    ":sell_phase": {"S": "SELL_PHASE"},
                    ":buy_phase": {"S": "BUY_PHASE"},
                    ":lock_at": {"S": now.isoformat()},
                    ":lock_expires": {"S": lock_expires_at.isoformat()},
                    ":now": {"S": now.isoformat()},
                },
            )
            logger.info(
                "Acquired notification lock",
                extra={"run_id": run_id, "lock_expires": lock_expires_at.isoformat()},
            )
            return True

        except self._client.exceptions.ConditionalCheckFailedException:
            # Already locked by another invocation or completed
            logger.debug(
                "Failed to acquire notification lock (already locked or completed)",
                extra={"run_id": run_id},
            )
            return False

    def mark_notification_sent(self, run_id: str) -> None:
        """Mark notification as successfully sent, completing the run.

        Called after notification is confirmed sent. Transitions NOTIFYING -> COMPLETED.

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
            UpdateExpression="SET #status = :completed, completed_at = :completed_at, notification_sent_at = :sent_at",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":completed": {"S": "COMPLETED"},
                ":completed_at": {"S": now.isoformat()},
                ":sent_at": {"S": now.isoformat()},
            },
        )
        logger.info("Marked run as completed with notification sent", extra={"run_id": run_id})

    def mark_run_completed(self, run_id: str) -> bool:
        """Mark a run as completed (idempotent).

        DEPRECATED: Use claim_notification_lock() + mark_notification_sent() instead.

        Called by Notifications Lambda after detecting all trades are done.
        Uses conditional update to ensure only one caller finalizes the run.

        Args:
            run_id: Run identifier.

        Returns:
            True if this call finalized the run, False if already finalized.

        """
        now = datetime.now(UTC)

        try:
            self._client.update_item(
                TableName=self._table_name,
                Key={
                    "PK": {"S": f"RUN#{run_id}"},
                    "SK": {"S": "METADATA"},
                },
                UpdateExpression="SET #status = :completed, completed_at = :completed_at",
                ConditionExpression="#status = :running",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":completed": {"S": "COMPLETED"},
                    ":running": {"S": "RUNNING"},
                    ":completed_at": {"S": now.isoformat()},
                },
            )
            logger.info("Marked run as completed", extra={"run_id": run_id})
            return True

        except self._client.exceptions.ConditionalCheckFailedException:
            # Already completed by another invocation
            logger.debug(
                "Run already completed (by another invocation)",
                extra={"run_id": run_id},
            )
            return False

    def update_run_status(self, run_id: str, status: str) -> None:
        """Update run status.

        Args:
            run_id: Run identifier.
            status: New status (PENDING, RUNNING, SELL_PHASE, BUY_PHASE, COMPLETED, FAILED).

        """
        self._client.update_item(
            TableName=self._table_name,
            Key={
                "PK": {"S": f"RUN#{run_id}"},
                "SK": {"S": "METADATA"},
            },
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": {"S": status}},
        )

        logger.info(
            "Updated run status",
            extra={"run_id": run_id, "status": status},
        )

    def is_sell_phase_complete(self, run_id: str) -> bool:
        """Check if SELL phase is complete for two-phase execution.

        Args:
            run_id: Run identifier.

        Returns:
            True if all SELL trades have completed.

        """
        run = self.get_run(run_id)
        if not run:
            return False

        sell_completed: int = run.get("sell_completed", 0)
        sell_total: int = run.get("sell_total", 0)
        current_phase: str = run.get("current_phase", "ALL")

        # Only relevant for two-phase execution (SELL phase)
        if current_phase != "SELL":
            return False

        # When sell_total == 0, the SELL phase is immediately complete
        # (there's nothing to sell), so BUY trades should proceed
        return sell_total == 0 or sell_completed >= sell_total

    def check_equity_circuit_breaker(
        self, run_id: str, proposed_buy_value: Decimal
    ) -> tuple[bool, dict[str, Any]]:
        """Check if a proposed BUY trade would exceed the equity deployment limit.

        This is the equity deployment circuit breaker - it prevents over-deployment
        by blocking BUY trades when cumulative executed buys would exceed the
        configured maximum (portfolio_equity * EQUITY_DEPLOYMENT_PCT).

        Args:
            run_id: Run identifier.
            proposed_buy_value: Dollar value of the proposed BUY trade.

        Returns:
            Tuple of (allowed, details):
            - allowed: True if trade is within limit, False if it would exceed
            - details: Dict with circuit breaker state for logging/diagnostics

        """
        run = self.get_run(run_id)
        if not run:
            # Run not found - fail safe (block the trade)
            logger.warning(
                "Equity circuit breaker: run not found - blocking trade",
                extra={"run_id": run_id},
            )
            return False, {"error": "run_not_found", "run_id": run_id}

        max_equity_limit = run.get("max_equity_limit_usd", Decimal("0"))
        cumulative_buy = run.get("cumulative_buy_succeeded_value", Decimal("0"))

        # If max_equity_limit is 0 or not set, circuit breaker is disabled
        if max_equity_limit <= Decimal("0"):
            return True, {
                "circuit_breaker_enabled": False,
                "reason": "max_equity_limit_usd not configured",
            }

        # Calculate what the new cumulative would be
        new_cumulative = cumulative_buy + abs(proposed_buy_value)
        headroom = max_equity_limit - cumulative_buy

        details = {
            "circuit_breaker_enabled": True,
            "max_equity_limit_usd": max_equity_limit,
            "cumulative_buy_succeeded_value": cumulative_buy,
            "proposed_buy_value": proposed_buy_value,
            "new_cumulative_if_executed": new_cumulative,
            "headroom_remaining": headroom,
            "would_exceed_limit": new_cumulative > max_equity_limit,
        }

        if new_cumulative > max_equity_limit:
            logger.warning(
                "🚫 Equity circuit breaker TRIGGERED - BUY would exceed limit",
                extra={
                    "run_id": run_id,
                    "max_equity_limit_usd": str(max_equity_limit),
                    "cumulative_buy_succeeded_value": str(cumulative_buy),
                    "proposed_buy_value": str(proposed_buy_value),
                    "new_cumulative_if_executed": str(new_cumulative),
                    "overage": str(new_cumulative - max_equity_limit),
                },
            )
            return False, details

        logger.debug(
            "Equity circuit breaker check passed",
            extra={
                "run_id": run_id,
                "cumulative_buy": str(cumulative_buy),
                "proposed_buy": str(proposed_buy_value),
                "headroom": str(headroom),
            },
        )
        return True, details

    def get_pending_buy_trades(self, run_id: str) -> list[dict[str, Any]]:
        """Get BUY trades that are waiting to be enqueued.

        For two-phase execution, BUY trades are stored with status=WAITING
        until the SELL phase completes.

        Args:
            run_id: Run identifier.

        Returns:
            List of trade dicts with message_body for SQS enqueue.

        """
        response = self._client.query(
            TableName=self._table_name,
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
            FilterExpression="phase = :buy AND #status = :waiting",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":pk": {"S": f"RUN#{run_id}"},
                ":sk_prefix": {"S": "TRADE#"},
                ":buy": {"S": "BUY"},
                ":waiting": {"S": "WAITING"},
            },
        )

        class _PendingBuyTrade(TypedDict):
            trade_id: str
            symbol: str
            action: str
            phase: str
            sequence_number: int
            message_body: str

        trades: list[_PendingBuyTrade] = []
        for item in response.get("Items", []):
            trade: _PendingBuyTrade = {
                "trade_id": item["trade_id"]["S"],
                "symbol": item["symbol"]["S"],
                "action": item["action"]["S"],
                "phase": item["phase"]["S"],
                "sequence_number": int(item["sequence_number"]["N"]),
                "message_body": item.get("message_body", {"S": ""})["S"],
            }
            trades.append(trade)

        # Sort by sequence number
        trades.sort(key=lambda t: t["sequence_number"])

        logger.debug(
            "Retrieved pending BUY trades",
            extra={"run_id": run_id, "count": len(trades)},
        )

        return cast("list[dict[str, Any]]", trades)

    def transition_to_buy_phase(self, run_id: str) -> bool:
        """Transition run from SELL phase to BUY phase (idempotent).

        Called when SELL phase completes to start BUY phase.
        Uses conditional update to ensure only one caller triggers the transition.

        Args:
            run_id: Run identifier.

        Returns:
            True if this call triggered the transition, False if already transitioned.

        """
        now = datetime.now(UTC)

        try:
            self._client.update_item(
                TableName=self._table_name,
                Key={
                    "PK": {"S": f"RUN#{run_id}"},
                    "SK": {"S": "METADATA"},
                },
                UpdateExpression="SET #status = :buy_phase, current_phase = :buy, buy_phase_started_at = :now",
                ConditionExpression="current_phase = :sell AND #status = :sell_phase",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":buy_phase": {"S": "BUY_PHASE"},
                    ":buy": {"S": "BUY"},
                    ":sell": {"S": "SELL"},
                    ":sell_phase": {"S": "SELL_PHASE"},
                    ":now": {"S": now.isoformat()},
                },
            )
            logger.info(
                "Transitioned run to BUY phase",
                extra={"run_id": run_id},
            )
            return True

        except self._client.exceptions.ConditionalCheckFailedException:
            # Already transitioned by another invocation
            logger.debug(
                "Run already transitioned to BUY phase",
                extra={"run_id": run_id},
            )
            return False

    def mark_buy_trades_pending(self, run_id: str, trade_ids: list[str]) -> int:
        """Mark BUY trades as PENDING after enqueue.

        Updates trade status from WAITING to PENDING after SQS enqueue.

        Args:
            run_id: Run identifier.
            trade_ids: List of trade IDs that were enqueued.

        Returns:
            Number of trades updated.

        """
        updated = 0
        for trade_id in trade_ids:
            try:
                self._client.update_item(
                    TableName=self._table_name,
                    Key={
                        "PK": {"S": f"RUN#{run_id}"},
                        "SK": {"S": f"TRADE#{trade_id}"},
                    },
                    UpdateExpression="SET #status = :pending",
                    ConditionExpression="#status = :waiting",
                    ExpressionAttributeNames={"#status": "status"},
                    ExpressionAttributeValues={
                        ":pending": {"S": "PENDING"},
                        ":waiting": {"S": "WAITING"},
                    },
                )
                updated += 1
            except self._client.exceptions.ConditionalCheckFailedException:
                # Already updated, skip
                pass

        logger.info(
            "Marked BUY trades as PENDING",
            extra={"run_id": run_id, "updated": updated, "total": len(trade_ids)},
        )
        return updated

    def find_stuck_runs(self, max_age_minutes: int = 30) -> list[dict[str, Any]]:
        """Find runs that have been in RUNNING status for too long.

        Used for monitoring and alerting on potential orphaned runs.
        A run is considered "stuck" if it's been RUNNING for longer than
        max_age_minutes without completing.

        Note: This uses a Scan operation which is expensive. Should only be
        called periodically (e.g., every 5-10 minutes) for monitoring.

        Args:
            max_age_minutes: Maximum age in minutes before a run is considered stuck.

        Returns:
            List of stuck run metadata dicts.

        """
        from datetime import timedelta

        cutoff_time = datetime.now(UTC) - timedelta(minutes=max_age_minutes)
        cutoff_iso = cutoff_time.isoformat()

        # Scan for RUNNING runs (this is expensive but acceptable for monitoring)
        # In production, consider using a GSI on status + created_at
        response = self._client.scan(
            TableName=self._table_name,
            FilterExpression="#status = :running AND SK = :metadata AND created_at < :cutoff",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":running": {"S": "RUNNING"},
                ":metadata": {"S": "METADATA"},
                ":cutoff": {"S": cutoff_iso},
            },
        )

        stuck_runs = []
        for item in response.get("Items", []):
            stuck_runs.append(
                {
                    "run_id": item["run_id"]["S"],
                    "plan_id": item["plan_id"]["S"],
                    "correlation_id": item["correlation_id"]["S"],
                    "total_trades": int(item["total_trades"]["N"]),
                    "completed_trades": int(item["completed_trades"]["N"]),
                    "created_at": item["created_at"]["S"],
                    "status": item["status"]["S"],
                }
            )

        if stuck_runs:
            logger.warning(
                f"Found {len(stuck_runs)} stuck runs (RUNNING > {max_age_minutes} mins)",
                extra={"stuck_run_count": len(stuck_runs)},
            )

        return stuck_runs

    def emit_stuck_runs_metric(self, max_age_minutes: int = 30) -> int:
        """Find stuck runs and emit CloudWatch metric.

        This can be called by a scheduled Lambda or monitoring script
        to track stuck runs over time.

        Args:
            max_age_minutes: Maximum age in minutes before a run is considered stuck.

        Returns:
            Count of stuck runs found.

        """
        import boto3

        stuck_runs = self.find_stuck_runs(max_age_minutes)
        count = len(stuck_runs)

        # Emit CloudWatch metric
        try:
            cloudwatch = boto3.client("cloudwatch")
            cloudwatch.put_metric_data(
                Namespace="Alchemiser/Execution",
                MetricData=[
                    {
                        "MetricName": "StuckRuns",
                        "Value": count,
                        "Unit": "Count",
                        "Dimensions": [
                            {"Name": "TableName", "Value": self._table_name},
                        ],
                    }
                ],
            )
            logger.debug(
                f"Emitted StuckRuns metric: {count}",
                extra={"stuck_run_count": count},
            )
        except Exception as e:
            logger.warning(f"Failed to emit StuckRuns metric: {e}")

        return count
