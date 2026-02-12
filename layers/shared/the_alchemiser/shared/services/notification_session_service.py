"""Business Unit: shared | Status: current.

Service for managing notification aggregation sessions in DynamoDB.

When the Coordinator dispatches N strategies, it creates a notification session
that tracks completion of each strategy. When all strategies have reported
(TRADED, ALL_HOLD, or FAILED), the last reporter publishes AllStrategiesCompleted
so the Notifications Lambda can send a single consolidated email.

DynamoDB Schema (reuses ExecutionRunsTable):
    PK: NOTIFY#{correlation_id}
    SK: METADATA | STRATEGY#{strategy_id}
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any
from uuid import uuid4

import boto3

from the_alchemiser.shared.config import DYNAMODB_RETRY_CONFIG
from the_alchemiser.shared.logging import get_logger

if TYPE_CHECKING:
    from mypy_boto3_dynamodb import DynamoDBClient

logger = get_logger(__name__)

SESSION_TTL_HOURS = 24


class NotificationSessionService:
    """Manages notification aggregation sessions in DynamoDB.

    Tracks how many strategies have completed in a daily run and stores
    per-strategy results for the consolidated email. Uses the same atomic
    counter pattern as TradeAggregatorService.

    DynamoDB Schema (reuses execution-runs table):
        PK: NOTIFY#{correlation_id}
        SK: METADATA | STRATEGY#{strategy_id}

    Session metadata fields:
        - total_strategies: Target count for completion check
        - completed_strategies: Atomic counter
        - status: PENDING | AGGREGATING | SENT
        - strategy_files: JSON list of DSL file names
        - created_at, TTL

    Per-strategy result fields:
        - strategy_id, dsl_file, outcome (TRADED/ALL_HOLD/FAILED)
        - run_id (for TRADED), trade_count
        - execution_detail (JSON, for TRADED)
        - failure_detail (JSON, for FAILED)
        - completed_at
    """

    def __init__(
        self,
        table_name: str,
        region: str | None = None,
    ) -> None:
        """Initialize the notification session service.

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

    def create_session(
        self,
        correlation_id: str,
        total_strategies: int,
        strategy_files: list[str],
    ) -> None:
        """Create a notification session for a daily run.

        Called by the Coordinator after dispatching all strategies.
        Uses conditional put (attribute_not_exists) for idempotency.

        Args:
            correlation_id: Shared workflow correlation ID.
            total_strategies: Number of strategies dispatched.
            strategy_files: List of DSL file names for display.

        """
        now = datetime.now(UTC)
        ttl = int((now + timedelta(hours=SESSION_TTL_HOURS)).timestamp())

        try:
            self._client.put_item(
                TableName=self._table_name,
                Item={
                    "PK": {"S": f"NOTIFY#{correlation_id}"},
                    "SK": {"S": "METADATA"},
                    "correlation_id": {"S": correlation_id},
                    "total_strategies": {"N": str(total_strategies)},
                    "completed_strategies": {"N": "0"},
                    "status": {"S": "PENDING"},
                    "strategy_files": {"S": json.dumps(strategy_files)},
                    "created_at": {"S": now.isoformat()},
                    "TTL": {"N": str(ttl)},
                },
                ConditionExpression="attribute_not_exists(PK)",
            )

            logger.info(
                "Notification session created",
                extra={
                    "correlation_id": correlation_id,
                    "total_strategies": total_strategies,
                    "strategy_files": strategy_files,
                },
            )

        except self._client.exceptions.ConditionalCheckFailedException:
            logger.info(
                "Notification session already exists (idempotent)",
                extra={"correlation_id": correlation_id},
            )

    def record_strategy_completion(
        self,
        correlation_id: str,
        strategy_id: str,
        dsl_file: str,
        outcome: str,
        detail: dict[str, Any],
    ) -> tuple[int, int]:
        """Record a strategy as complete and atomically increment the counter.

        Writes a per-strategy result item and increments completed_strategies.
        Uses two operations: a conditional put for the strategy result (idempotent)
        and an atomic increment on the metadata counter.

        Args:
            correlation_id: Shared workflow correlation ID.
            strategy_id: Strategy identifier (e.g., '1-KMLM').
            dsl_file: DSL file name.
            outcome: One of 'TRADED', 'ALL_HOLD', 'FAILED'.
            detail: Outcome-specific detail (execution_detail or failure_detail).

        Returns:
            Tuple of (completed_strategies, total_strategies) after increment.

        """
        now = datetime.now(UTC)
        ttl_val = int((now + timedelta(hours=SESSION_TTL_HOURS)).timestamp())

        strategy_item = self._build_strategy_item(
            correlation_id,
            strategy_id,
            dsl_file,
            outcome,
            detail,
            now,
            ttl_val,
        )

        try:
            self._client.put_item(
                TableName=self._table_name,
                Item=strategy_item,
                ConditionExpression="attribute_not_exists(PK)",
            )
        except self._client.exceptions.ConditionalCheckFailedException:
            logger.info(
                "Strategy already recorded (idempotent)",
                extra={
                    "correlation_id": correlation_id,
                    "strategy_id": strategy_id,
                },
            )
            return self._get_counts(correlation_id)

        # Step 2: Atomically increment completed_strategies counter
        response = self._client.update_item(
            TableName=self._table_name,
            Key={
                "PK": {"S": f"NOTIFY#{correlation_id}"},
                "SK": {"S": "METADATA"},
            },
            UpdateExpression="SET completed_strategies = completed_strategies + :one",
            ExpressionAttributeValues={":one": {"N": "1"}},
            ReturnValues="ALL_NEW",
        )

        attrs = response.get("Attributes", {})
        completed = int(attrs.get("completed_strategies", {}).get("N", "0"))
        total = int(attrs.get("total_strategies", {}).get("N", "0"))

        logger.info(
            "Recorded strategy completion",
            extra={
                "correlation_id": correlation_id,
                "strategy_id": strategy_id,
                "outcome": outcome,
                "completed_strategies": completed,
                "total_strategies": total,
            },
        )

        return (completed, total)

    @staticmethod
    def _build_strategy_item(
        correlation_id: str,
        strategy_id: str,
        dsl_file: str,
        outcome: str,
        detail: dict[str, Any],
        now: datetime,
        ttl_val: int,
    ) -> dict[str, dict[str, str]]:
        """Build the DynamoDB item for a per-strategy result.

        Args:
            correlation_id: Shared workflow correlation ID.
            strategy_id: Strategy identifier.
            dsl_file: DSL file name.
            outcome: One of 'TRADED', 'ALL_HOLD', 'FAILED'.
            detail: Outcome-specific detail dict.
            now: Current UTC timestamp.
            ttl_val: TTL epoch seconds.

        Returns:
            DynamoDB item dict ready for PutItem.

        """
        item: dict[str, dict[str, str]] = {
            "PK": {"S": f"NOTIFY#{correlation_id}"},
            "SK": {"S": f"STRATEGY#{strategy_id}"},
            "strategy_id": {"S": strategy_id},
            "dsl_file": {"S": dsl_file},
            "outcome": {"S": outcome},
            "completed_at": {"S": now.isoformat()},
            "TTL": {"N": str(ttl_val)},
        }

        if outcome == "TRADED":
            item["run_id"] = {"S": detail.get("run_id", "")}
            item["trade_count"] = {"N": str(detail.get("total_trades", 0))}
            item["execution_detail"] = {"S": json.dumps(detail, default=str)}
        elif outcome == "ALL_HOLD":
            item["trade_count"] = {"N": "0"}
        elif outcome == "FAILED":
            item["trade_count"] = {"N": "0"}
            item["failure_detail"] = {"S": json.dumps(detail, default=str)}

        return item

    def try_claim_notification(self, correlation_id: str) -> bool:
        """Atomically claim the right to send the consolidated notification.

        Transitions status from PENDING to AGGREGATING. Only one invocation
        can succeed, preventing duplicate emails.

        Args:
            correlation_id: Shared workflow correlation ID.

        Returns:
            True if this invocation claimed notification rights.

        """
        now = datetime.now(UTC)

        try:
            self._client.update_item(
                TableName=self._table_name,
                Key={
                    "PK": {"S": f"NOTIFY#{correlation_id}"},
                    "SK": {"S": "METADATA"},
                },
                UpdateExpression="SET #status = :aggregating, notification_claimed_at = :now",
                ConditionExpression="#status = :pending",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":aggregating": {"S": "AGGREGATING"},
                    ":pending": {"S": "PENDING"},
                    ":now": {"S": now.isoformat()},
                },
            )

            logger.info(
                "Claimed notification lock",
                extra={"correlation_id": correlation_id},
            )
            return True

        except self._client.exceptions.ConditionalCheckFailedException:
            logger.debug(
                "Notification already claimed",
                extra={"correlation_id": correlation_id},
            )
            return False

    def get_session(self, correlation_id: str) -> dict[str, Any] | None:
        """Get notification session metadata.

        Args:
            correlation_id: Shared workflow correlation ID.

        Returns:
            Session metadata dict, or None if no session exists.

        """
        response = self._client.get_item(
            TableName=self._table_name,
            Key={
                "PK": {"S": f"NOTIFY#{correlation_id}"},
                "SK": {"S": "METADATA"},
            },
        )

        item = response.get("Item")
        if not item:
            return None

        strategy_files_raw = item.get("strategy_files", {}).get("S", "[]")
        try:
            strategy_files = json.loads(strategy_files_raw)
        except json.JSONDecodeError:
            strategy_files = []

        return {
            "correlation_id": item.get("correlation_id", {}).get("S", ""),
            "total_strategies": int(item.get("total_strategies", {}).get("N", "0")),
            "completed_strategies": int(item.get("completed_strategies", {}).get("N", "0")),
            "status": item.get("status", {}).get("S", "UNKNOWN"),
            "strategy_files": strategy_files,
            "created_at": item.get("created_at", {}).get("S", ""),
        }

    def get_all_strategy_results(self, correlation_id: str) -> list[dict[str, Any]]:
        """Get all per-strategy result items for a notification session.

        Args:
            correlation_id: Shared workflow correlation ID.

        Returns:
            List of per-strategy result dicts.

        """
        items: list[dict[str, Any]] = []
        query_kwargs: dict[str, Any] = {
            "TableName": self._table_name,
            "KeyConditionExpression": "PK = :pk AND begins_with(SK, :sk_prefix)",
            "ExpressionAttributeValues": {
                ":pk": {"S": f"NOTIFY#{correlation_id}"},
                ":sk_prefix": {"S": "STRATEGY#"},
            },
        }

        while True:
            response = self._client.query(**query_kwargs)
            items.extend(response.get("Items", []))

            last_key = response.get("LastEvaluatedKey")
            if not last_key:
                break
            query_kwargs["ExclusiveStartKey"] = last_key

        results = [self._parse_strategy_result_item(item) for item in items]

        logger.debug(
            "Retrieved strategy results",
            extra={
                "correlation_id": correlation_id,
                "result_count": len(results),
            },
        )

        return results

    @staticmethod
    def _parse_strategy_result_item(item: dict[str, Any]) -> dict[str, Any]:
        """Parse a DynamoDB strategy result item into a plain dict.

        Args:
            item: Raw DynamoDB item from query response.

        Returns:
            Parsed strategy result dict.

        """
        result: dict[str, Any] = {
            "strategy_id": item.get("strategy_id", {}).get("S", ""),
            "dsl_file": item.get("dsl_file", {}).get("S", ""),
            "outcome": item.get("outcome", {}).get("S", ""),
            "trade_count": int(item.get("trade_count", {}).get("N", "0")),
            "completed_at": item.get("completed_at", {}).get("S", ""),
        }

        if result["outcome"] == "TRADED":
            result["run_id"] = item.get("run_id", {}).get("S", "")
            exec_detail_raw = item.get("execution_detail", {}).get("S")
            if exec_detail_raw:
                try:
                    result["execution_detail"] = json.loads(exec_detail_raw)
                except json.JSONDecodeError:
                    result["execution_detail"] = {}

        if result["outcome"] == "FAILED":
            fail_detail_raw = item.get("failure_detail", {}).get("S")
            if fail_detail_raw:
                try:
                    result["failure_detail"] = json.loads(fail_detail_raw)
                except json.JSONDecodeError:
                    result["failure_detail"] = {}

        return result

    def mark_session_sent(self, correlation_id: str) -> None:
        """Mark the notification session as sent after email dispatched.

        Args:
            correlation_id: Shared workflow correlation ID.

        """
        now = datetime.now(UTC)

        self._client.update_item(
            TableName=self._table_name,
            Key={
                "PK": {"S": f"NOTIFY#{correlation_id}"},
                "SK": {"S": "METADATA"},
            },
            UpdateExpression="SET #status = :sent, sent_at = :now",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":sent": {"S": "SENT"},
                ":now": {"S": now.isoformat()},
            },
        )

        logger.info(
            "Marked notification session as sent",
            extra={"correlation_id": correlation_id},
        )

    def _get_counts(self, correlation_id: str) -> tuple[int, int]:
        """Read current completion counts from session metadata.

        Args:
            correlation_id: Shared workflow correlation ID.

        Returns:
            Tuple of (completed_strategies, total_strategies).

        """
        response = self._client.get_item(
            TableName=self._table_name,
            Key={
                "PK": {"S": f"NOTIFY#{correlation_id}"},
                "SK": {"S": "METADATA"},
            },
        )

        item = response.get("Item")
        if not item:
            return (0, 0)

        completed = int(item.get("completed_strategies", {}).get("N", "0"))
        total = int(item.get("total_strategies", {}).get("N", "0"))
        return (completed, total)


def publish_all_strategies_completed(
    correlation_id: str,
    completed: int,
    total: int,
    source_component: str,
) -> None:
    """Publish AllStrategiesCompleted event to trigger consolidated email.

    Args:
        correlation_id: Shared workflow correlation ID.
        completed: Number of strategies that completed.
        total: Total strategies in the run.
        source_component: Name of the calling component (e.g. 'StrategyWorker').

    """
    try:
        from the_alchemiser.shared.events import AllStrategiesCompleted
        from the_alchemiser.shared.events.eventbridge_publisher import (
            publish_to_eventbridge,
        )

        event = AllStrategiesCompleted(
            event_id=f"all-strategies-completed-{uuid4()}",
            correlation_id=correlation_id,
            causation_id=correlation_id,
            timestamp=datetime.now(UTC),
            source_module="coordinator",
            source_component=source_component,
            total_strategies=total,
            completed_strategies=completed,
        )
        publish_to_eventbridge(event)

        logger.info(
            "Published AllStrategiesCompleted event",
            extra={
                "correlation_id": correlation_id,
                "total_strategies": total,
                "completed_strategies": completed,
            },
        )
    except Exception as e:
        logger.error(
            "Failed to publish AllStrategiesCompleted",
            extra={"correlation_id": correlation_id, "error": str(e)},
        )
