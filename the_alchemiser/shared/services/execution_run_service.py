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
from typing import TYPE_CHECKING, Any, cast

import boto3

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
        - status: PENDING | RUNNING | COMPLETED | FAILED
        - created_at, TTL

    Trade result items (one per trade):
        - trade_id, symbol, action, phase
        - status: PENDING | RUNNING | COMPLETED | FAILED
        - order_id, error_message
        - started_at, completed_at
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
        self._client: DynamoDBClient = boto3.client("dynamodb", region_name=self._region)
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
    ) -> dict[str, Any]:
        """Create a new execution run.

        Called by Portfolio Lambda when decomposing a RebalancePlan into
        individual TradeMessages.

        Args:
            run_id: Unique run identifier (UUID).
            plan_id: Source RebalancePlan identifier.
            correlation_id: Workflow correlation ID for tracing.
            trade_messages: List of TradeMessage objects for this run.
            run_timestamp: When the run started.

        Returns:
            Run metadata dict.

        """
        now = datetime.now(UTC)
        ttl = int((now + timedelta(hours=24)).timestamp())

        # Create run metadata item
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
                "status": {"S": "PENDING"},
                "run_timestamp": {"S": run_timestamp.isoformat()},
                "created_at": {"S": now.isoformat()},
                "TTL": {"N": str(ttl)},
                # Store trade IDs for reference
                "trade_ids": {"L": [{"S": msg.trade_id} for msg in trade_messages]},
            },
        )

        self._client.put_item(TableName=self._table_name, Item=item)

        # Create pending trade items for each trade
        for msg in trade_messages:
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
                    "status": {"S": "PENDING"},
                    "TTL": {"N": str(ttl)},
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
            },
        )

        return {
            "run_id": run_id,
            "plan_id": plan_id,
            "correlation_id": correlation_id,
            "total_trades": len(trade_messages),
            "completed_trades": 0,
            "status": "PENDING",
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
        order_id: str | None = None,
        error_message: str | None = None,
        execution_data: dict[str, Any] | None = None,
    ) -> int:
        """Mark a trade as completed and increment completion counter.

        Called by Execution Lambda after trade execution completes.
        Uses conditional put to ensure idempotency.

        Args:
            run_id: Run identifier.
            trade_id: Trade identifier.
            success: Whether the trade succeeded.
            order_id: Broker order ID if available.
            error_message: Error message if failed.
            execution_data: Additional execution data.

        Returns:
            Updated completed_trades count.

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

            # Increment counters atomically
            counter_field = "succeeded_trades" if success else "failed_trades"
            response = self._client.update_item(
                TableName=self._table_name,
                Key={
                    "PK": {"S": f"RUN#{run_id}"},
                    "SK": {"S": "METADATA"},
                },
                UpdateExpression=f"ADD completed_trades :one, {counter_field} :one",
                ExpressionAttributeValues={":one": {"N": "1"}},
                ReturnValues="UPDATED_NEW",
            )

            completed = int(response["Attributes"]["completed_trades"]["N"])

            logger.info(
                "Marked trade as completed",
                extra={
                    "run_id": run_id,
                    "trade_id": trade_id,
                    "success": success,
                    "completed_trades": completed,
                },
            )

            return completed

        except self._client.exceptions.ConditionalCheckFailedException:
            # Trade already marked as completed - get current count
            logger.warning(
                "Trade already completed (duplicate)",
                extra={"run_id": run_id, "trade_id": trade_id},
            )
            run = self.get_run(run_id)
            return run.get("completed_trades", 0) if run else 0

    def get_run(self, run_id: str) -> dict[str, Any] | None:
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
            "plan_id": item["plan_id"]["S"],
            "correlation_id": item["correlation_id"]["S"],
            "total_trades": int(item["total_trades"]["N"]),
            "completed_trades": int(item["completed_trades"]["N"]),
            "succeeded_trades": int(item.get("succeeded_trades", {"N": "0"})["N"]),
            "failed_trades": int(item.get("failed_trades", {"N": "0"})["N"]),
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

    def mark_run_completed(self, run_id: str) -> bool:
        """Mark a run as completed (idempotent).

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
            status: New status (PENDING, RUNNING, COMPLETED, FAILED).

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
