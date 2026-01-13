"""Business Unit: shared | Status: current.

Service for managing aggregation sessions in DynamoDB.

Aggregation sessions track the state of multi-node strategy execution,
including which strategies have completed and their partial signals.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Any, cast

import boto3

from the_alchemiser.shared.config import DYNAMODB_RETRY_CONFIG
from the_alchemiser.shared.logging import get_logger

if TYPE_CHECKING:
    from mypy_boto3_dynamodb import DynamoDBClient

logger = get_logger(__name__)


class AggregationSessionService:
    """Manages aggregation session state in DynamoDB.

    DynamoDB Schema:
        PK: SESSION#<session_id>
        SK: METADATA | STRATEGY#<dsl_file>

    Session metadata item:
        - session_id, correlation_id
        - total_strategies, completed_strategies (atomic counter)
        - status: PENDING | AGGREGATING | COMPLETED | FAILED | TIMEOUT
        - created_at, timeout_at, TTL

    Strategy completion items (one per file):
        - dsl_file, allocation
        - consolidated_portfolio, signals_data
        - completed_at
    """

    def __init__(
        self,
        table_name: str,
        region: str | None = None,
    ) -> None:
        """Initialize the aggregation session service.

        Args:
            table_name: DynamoDB table name for session state.
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
            "AggregationSessionService initialized",
            extra={"table_name": table_name},
        )

    def create_session(
        self,
        session_id: str,
        correlation_id: str,
        strategy_configs: list[tuple[str, Decimal]],
        timeout_seconds: int = 600,
    ) -> dict[str, Any]:
        """Create a new aggregation session.

        Args:
            session_id: Unique session identifier (usually correlation_id).
            correlation_id: Workflow correlation ID for tracing.
            strategy_configs: List of (dsl_file, allocation) tuples with Decimal allocations.
            timeout_seconds: Session timeout in seconds.

        Returns:
            Session metadata dict.

        """
        now = datetime.now(UTC)
        timeout_at = now + timedelta(seconds=timeout_seconds)
        ttl = int((now + timedelta(hours=24)).timestamp())

        item = cast(
            "dict[str, dict[str, Any]]",
            {
                "PK": {"S": f"SESSION#{session_id}"},
                "SK": {"S": "METADATA"},
                "session_id": {"S": session_id},
                "correlation_id": {"S": correlation_id},
                "total_strategies": {"N": str(len(strategy_configs))},
                "completed_strategies": {"N": "0"},
                "status": {"S": "PENDING"},
                "created_at": {"S": now.isoformat()},
                "timeout_at": {"S": timeout_at.isoformat()},
                "TTL": {"N": str(ttl)},
                "strategy_configs": {
                    "L": [
                        {
                            "M": {
                                "dsl_file": {"S": dsl_file},
                                "allocation": {"N": str(allocation)},
                            }
                        }
                        for dsl_file, allocation in strategy_configs
                    ]
                },
            },
        )

        self._client.put_item(TableName=self._table_name, Item=item)

        logger.info(
            "Created aggregation session",
            extra={
                "session_id": session_id,
                "correlation_id": correlation_id,
                "total_strategies": len(strategy_configs),
                "timeout_at": timeout_at.isoformat(),
            },
        )

        return {
            "session_id": session_id,
            "correlation_id": correlation_id,
            "total_strategies": len(strategy_configs),
            "completed_strategies": 0,
            "status": "PENDING",
            "created_at": now.isoformat(),
            "timeout_at": timeout_at.isoformat(),
        }

    def store_partial_signal(
        self,
        session_id: str,
        dsl_file: str,
        allocation: Decimal,
        consolidated_portfolio: dict[str, Any],
        signals_data: dict[str, Any],
        signal_count: int,
        data_freshness: dict[str, Any] | None = None,
    ) -> int:
        """Store a partial signal and increment completion counter.

        Uses conditional put to ensure idempotency - duplicate deliveries
        are ignored. Returns the new completed count.

        Args:
            session_id: Session ID this signal belongs to.
            dsl_file: Strategy file that generated this signal.
            allocation: Weight allocation for this file.
            consolidated_portfolio: Partial portfolio data.
            signals_data: Signal data from this file.
            signal_count: Number of signals generated.
            data_freshness: Data freshness info (latest_timestamp, age_days, gate_status).

        Returns:
            Updated completed_strategies count.

        """
        import json

        now = datetime.now(UTC)

        # Store partial signal (idempotent - fails silently if exists)
        partial_item = cast(
            "dict[str, dict[str, Any]]",
            {
                "PK": {"S": f"SESSION#{session_id}"},
                "SK": {"S": f"STRATEGY#{dsl_file}"},
                "dsl_file": {"S": dsl_file},
                "allocation": {"N": str(allocation)},
                "completed_at": {"S": now.isoformat()},
                "signal_count": {"N": str(signal_count)},
                "consolidated_portfolio": {"S": json.dumps(consolidated_portfolio, default=str)},
                "signals_data": {"S": json.dumps(signals_data, default=str)},
                "data_freshness": {"S": json.dumps(data_freshness or {}, default=str)},
            },
        )
        try:
            self._client.put_item(
                TableName=self._table_name,
                Item=partial_item,
                ConditionExpression="attribute_not_exists(SK)",
            )

            # Increment counter atomically
            response = self._client.update_item(
                TableName=self._table_name,
                Key={
                    "PK": {"S": f"SESSION#{session_id}"},
                    "SK": {"S": "METADATA"},
                },
                UpdateExpression="ADD completed_strategies :one",
                ExpressionAttributeValues={":one": {"N": "1"}},
                ReturnValues="UPDATED_NEW",
            )

            completed = int(response["Attributes"]["completed_strategies"]["N"])

            logger.info(
                "Stored partial signal",
                extra={
                    "session_id": session_id,
                    "dsl_file": dsl_file,
                    "completed_strategies": completed,
                    "signal_count": signal_count,
                },
            )

            return completed

        except self._client.exceptions.ConditionalCheckFailedException:
            # Duplicate delivery - get current count without incrementing
            logger.warning(
                "Duplicate partial signal ignored",
                extra={"session_id": session_id, "dsl_file": dsl_file},
            )
            session = self.get_session(session_id)
            return session.get("completed_strategies", 0) if session else 0

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        """Get session metadata.

        Args:
            session_id: Session ID to retrieve.

        Returns:
            Session metadata dict or None if not found.

        """
        response = self._client.get_item(
            TableName=self._table_name,
            Key={
                "PK": {"S": f"SESSION#{session_id}"},
                "SK": {"S": "METADATA"},
            },
        )

        item = response.get("Item")
        if not item:
            return None

        return {
            "session_id": item["session_id"]["S"],
            "correlation_id": item["correlation_id"]["S"],
            "total_strategies": int(item["total_strategies"]["N"]),
            "completed_strategies": int(item["completed_strategies"]["N"]),
            "status": item["status"]["S"],
            "created_at": item["created_at"]["S"],
            "timeout_at": item["timeout_at"]["S"],
        }

    def get_all_partial_signals(self, session_id: str) -> list[dict[str, Any]]:
        """Get all partial signals for a session.

        Args:
            session_id: Session ID to retrieve signals for.

        Returns:
            List of partial signal dicts.

        """
        import json

        response = self._client.query(
            TableName=self._table_name,
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
            ExpressionAttributeValues={
                ":pk": {"S": f"SESSION#{session_id}"},
                ":sk_prefix": {"S": "STRATEGY#"},
            },
        )

        signals = []
        for item in response.get("Items", []):
            signals.append(
                {
                    "dsl_file": item["dsl_file"]["S"],
                    "allocation": Decimal(item["allocation"]["N"]),
                    "completed_at": item["completed_at"]["S"],
                    "signal_count": int(item["signal_count"]["N"]),
                    "consolidated_portfolio": json.loads(item["consolidated_portfolio"]["S"]),
                    "signals_data": json.loads(item["signals_data"]["S"]),
                    "data_freshness": json.loads(item.get("data_freshness", {}).get("S", "{}")),
                }
            )

        logger.debug(
            "Retrieved partial signals",
            extra={
                "session_id": session_id,
                "signal_count": len(signals),
            },
        )

        return signals

    def update_session_status(self, session_id: str, status: str) -> None:
        """Update session status.

        Args:
            session_id: Session ID to update.
            status: New status (PENDING, AGGREGATING, COMPLETED, FAILED, TIMEOUT).

        """
        self._client.update_item(
            TableName=self._table_name,
            Key={
                "PK": {"S": f"SESSION#{session_id}"},
                "SK": {"S": "METADATA"},
            },
            UpdateExpression="SET #status = :status",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={":status": {"S": status}},
        )

        logger.info(
            "Updated session status",
            extra={"session_id": session_id, "status": status},
        )

    def find_stuck_sessions(self, max_age_minutes: int = 30) -> list[dict[str, Any]]:
        """Find sessions stuck in PENDING state for too long.

        Scans for sessions that are still PENDING and were created
        more than max_age_minutes ago. These indicate silent worker failures
        (e.g., async invocation dropped, throttled, or crashed without publishing).

        Args:
            max_age_minutes: Maximum age in minutes before a session is considered stuck.

        Returns:
            List of stuck session metadata dicts.

        """
        cutoff_time = datetime.now(UTC) - timedelta(minutes=max_age_minutes)

        # Scan for PENDING sessions (table is small, typically < 100 items)
        # Note: Could optimize with GSI on status if table grows significantly
        response = self._client.scan(
            TableName=self._table_name,
            FilterExpression="#status = :pending AND SK = :metadata",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":pending": {"S": "PENDING"},
                ":metadata": {"S": "METADATA"},
            },
        )

        stuck_sessions = []
        for item in response.get("Items", []):
            created_at_str = item.get("created_at", {}).get("S", "")
            if not created_at_str:
                continue

            try:
                created_at = datetime.fromisoformat(created_at_str)
                if created_at < cutoff_time:
                    stuck_sessions.append(
                        {
                            "session_id": item["session_id"]["S"],
                            "correlation_id": item["correlation_id"]["S"],
                            "total_strategies": int(item["total_strategies"]["N"]),
                            "completed_strategies": int(item["completed_strategies"]["N"]),
                            "status": item["status"]["S"],
                            "created_at": created_at_str,
                            "age_minutes": int(
                                (datetime.now(UTC) - created_at).total_seconds() / 60
                            ),
                        }
                    )
            except (ValueError, KeyError) as e:
                logger.warning(
                    f"Failed to parse session created_at: {e}",
                    extra={"session_id": item.get("session_id", {}).get("S", "unknown")},
                )

        if stuck_sessions:
            logger.warning(
                f"Found {len(stuck_sessions)} stuck aggregation sessions (PENDING > {max_age_minutes} mins)",
                extra={"stuck_session_count": len(stuck_sessions)},
            )

        return stuck_sessions

    def emit_stuck_sessions_metric(self, max_age_minutes: int = 30) -> int:
        """Find stuck sessions and emit CloudWatch metric.

        This is called by the Strategy Aggregator Lambda on each invocation
        to track stuck sessions over time. The StuckAggregationSessionsAlarm
        monitors this metric.

        Args:
            max_age_minutes: Maximum age in minutes before a session is considered stuck.

        Returns:
            Count of stuck sessions found.

        """
        stuck_sessions = self.find_stuck_sessions(max_age_minutes)
        count = len(stuck_sessions)

        # Emit CloudWatch metric
        try:
            cloudwatch = boto3.client("cloudwatch")
            cloudwatch.put_metric_data(
                Namespace="Alchemiser/Aggregation",
                MetricData=[
                    {
                        "MetricName": "StuckAggregationSessions",
                        "Value": count,
                        "Unit": "Count",
                        "Dimensions": [
                            {"Name": "TableName", "Value": self._table_name},
                        ],
                    }
                ],
            )
            logger.debug(
                f"Emitted StuckAggregationSessions metric: {count}",
                extra={"stuck_session_count": count},
            )
        except Exception as e:
            logger.warning(f"Failed to emit StuckAggregationSessions metric: {e}")

        return count
