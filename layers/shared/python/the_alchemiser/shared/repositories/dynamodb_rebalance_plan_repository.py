"""Business Unit: shared | Status: current.

DynamoDB repository for rebalance plan persistence.

Stores RebalancePlan documents with 90-day TTL for auditability,
enabling "why didn't we trade X?" queries beyond EventBridge's 24-hour retention.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from botocore.exceptions import BotoCoreError, ClientError

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlan

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)

__all__ = ["DynamoDBRebalancePlanRepository"]

# DynamoDB exception types for error handling
DynamoDBException = (ClientError, BotoCoreError)


class DynamoDBRebalancePlanRepository:
    """Repository for rebalance plans using DynamoDB.

    Table structure:
    - PK: PLAN#{plan_id}
    - SK: METADATA
    - GSI1: Query by correlation_id + created_at

    TTL is set for automatic 90-day cleanup.
    """

    def __init__(self, table_name: str, ttl_days: int = 90) -> None:
        """Initialize repository.

        Args:
            table_name: DynamoDB table name
            ttl_days: TTL in days for automatic cleanup (default 90)

        """
        import boto3

        self._dynamodb = boto3.resource("dynamodb")
        self._table = self._dynamodb.Table(table_name)
        self._ttl_days = ttl_days
        logger.debug(
            "Initialized DynamoDB rebalance plan repository",
            table=table_name,
            ttl_days=ttl_days,
        )

    def save_plan(self, plan: RebalancePlan) -> None:
        """Write a rebalance plan to DynamoDB.

        Args:
            plan: RebalancePlan to persist

        Raises:
            RuntimeError: If DynamoDB write fails

        """
        now = datetime.now(UTC)
        ttl_timestamp = int((now + timedelta(days=self._ttl_days)).timestamp())
        created_at = now.isoformat()

        # Serialize the full plan to JSON for storage
        plan_data = plan.to_dict()

        # Count items by action for quick summary queries
        action_counts = {"BUY": 0, "SELL": 0, "HOLD": 0}
        for plan_item in plan.items:
            action_counts[plan_item.action] = action_counts.get(plan_item.action, 0) + 1

        dynamo_item: dict[str, Any] = {
            "PK": f"PLAN#{plan.plan_id}",
            "SK": "METADATA",
            "EntityType": "REBALANCE_PLAN",
            # Core identifiers
            "plan_id": plan.plan_id,
            "correlation_id": plan.correlation_id,
            "causation_id": plan.causation_id,
            # Timestamps
            "plan_timestamp": plan.timestamp.isoformat(),
            "created_at": created_at,
            # Full plan data as JSON string
            "plan_data": json.dumps(plan_data),
            # Summary fields for quick queries without deserializing full plan
            "item_count": len(plan.items),
            "total_trade_value": str(plan.total_trade_value),
            "total_portfolio_value": str(plan.total_portfolio_value),
            "execution_urgency": plan.execution_urgency,
            "buy_count": action_counts["BUY"],
            "sell_count": action_counts["SELL"],
            "hold_count": action_counts["HOLD"],
            # GSI keys for access patterns
            "GSI1PK": f"CORR#{plan.correlation_id}",
            "GSI1SK": f"PLAN#{created_at}",
            # TTL for automatic cleanup
            "ttl": ttl_timestamp,
        }

        try:
            self._table.put_item(Item=dynamo_item)
            logger.info(
                "Persisted rebalance plan",
                plan_id=plan.plan_id,
                correlation_id=plan.correlation_id,
                item_count=len(plan.items),
                buy_count=action_counts["BUY"],
                sell_count=action_counts["SELL"],
                hold_count=action_counts["HOLD"],
            )
        except DynamoDBException as e:
            logger.error(
                "Failed to persist rebalance plan",
                plan_id=plan.plan_id,
                correlation_id=plan.correlation_id,
                error=str(e),
            )
            raise RuntimeError(f"Failed to persist rebalance plan: {e}") from e

    def get_plan_by_id(self, plan_id: str) -> RebalancePlan | None:
        """Retrieve a rebalance plan by its ID.

        Args:
            plan_id: Plan identifier

        Returns:
            RebalancePlan if found, None otherwise

        """
        try:
            response = self._table.get_item(
                Key={
                    "PK": f"PLAN#{plan_id}",
                    "SK": "METADATA",
                }
            )

            if "Item" not in response:
                return None

            plan_data_str = str(response["Item"]["plan_data"])
            plan_data = json.loads(plan_data_str)
            return RebalancePlan.from_dict(plan_data)

        except DynamoDBException as e:
            logger.error("Failed to retrieve rebalance plan", plan_id=plan_id, error=str(e))
            return None

    def get_plans_by_correlation_id(self, correlation_id: str) -> list[RebalancePlan]:
        """Retrieve all rebalance plans for a correlation ID.

        Args:
            correlation_id: Correlation identifier

        Returns:
            List of RebalancePlan instances

        """
        try:
            response = self._table.query(
                IndexName="GSI1-CorrelationIndex",
                KeyConditionExpression="GSI1PK = :pk",
                ExpressionAttributeValues={":pk": f"CORR#{correlation_id}"},
                ScanIndexForward=False,  # Most recent first
            )

            plans = []
            for dynamo_item in response.get("Items", []):
                plan_data_str = str(dynamo_item["plan_data"])
                plan_data = json.loads(plan_data_str)
                plans.append(RebalancePlan.from_dict(plan_data))

            return plans

        except DynamoDBException as e:
            logger.error(
                "Failed to query rebalance plans by correlation_id",
                correlation_id=correlation_id,
                error=str(e),
            )
            return []
