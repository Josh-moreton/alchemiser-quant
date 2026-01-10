"""Business Unit: shared | Status: current.

DynamoDB repository for dynamic strategy weights.

Stores dynamically adjusted strategy allocations based on Sharpe ratio analysis.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from botocore.exceptions import BotoCoreError, ClientError

from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)

__all__ = ["DynamoDBStrategyWeightsRepository"]

# DynamoDB exception types for error handling
DynamoDBException = (ClientError, BotoCoreError)

# TTL for weight records (7 days - weights are refreshed weekly)
WEIGHTS_TTL_DAYS = 7


class DynamoDBStrategyWeightsRepository:
    """Repository for dynamic strategy weights using DynamoDB.

    Table structure:
    - PK: "WEIGHTS#CURRENT" (single active record)
    - SK: timestamp ISO string
    - TTL: Auto-expire old records after 7 days
    """

    def __init__(self, table_name: str) -> None:
        """Initialize repository.

        Args:
            table_name: DynamoDB table name

        """
        import boto3

        self._dynamodb = boto3.resource("dynamodb")
        self._table = self._dynamodb.Table(table_name)
        logger.debug("Initialized DynamoDB strategy weights repository", table=table_name)

    def put_dynamic_weights(
        self,
        weights: dict[str, Decimal],
        sharpe_ratios: dict[str, Decimal],
        baseline_allocations: dict[str, Decimal],
        correlation_id: str,
    ) -> None:
        """Store dynamic strategy weights in DynamoDB.

        Args:
            weights: Dict mapping strategy name to adjusted allocation (0-1)
            sharpe_ratios: Dict mapping strategy name to Sharpe ratio
            baseline_allocations: Dict mapping strategy name to baseline allocation
            correlation_id: Correlation ID for tracing

        """
        timestamp = datetime.now(UTC)
        ttl = int((timestamp + timedelta(days=WEIGHTS_TTL_DAYS)).timestamp())

        # Create item with all metadata
        item: dict[str, Any] = {
            "PK": "WEIGHTS#CURRENT",
            "SK": timestamp.isoformat(),
            "EntityType": "DYNAMIC_WEIGHTS",
            "updated_at": timestamp.isoformat(),
            "correlation_id": correlation_id,
            "ttl": ttl,
            # Store weights as dict[str, str] for DynamoDB
            "weights": {k: str(v) for k, v in weights.items()},
            "sharpe_ratios": {k: str(v) for k, v in sharpe_ratios.items()},
            "baseline_allocations": {k: str(v) for k, v in baseline_allocations.items()},
        }

        try:
            self._table.put_item(Item=item)
            logger.info(
                "Dynamic weights written to DynamoDB",
                extra={
                    "correlation_id": correlation_id,
                    "strategy_count": len(weights),
                    "timestamp": timestamp.isoformat(),
                },
            )
        except DynamoDBException as e:
            logger.error(
                f"Failed to write dynamic weights: {e}",
                extra={"correlation_id": correlation_id, "error_type": type(e).__name__},
            )
            raise

    def get_current_weights(self) -> dict[str, Decimal] | None:
        """Get the most recent dynamic weights from DynamoDB.

        Returns:
            Dict mapping strategy name to adjusted allocation, or None if not found

        """
        try:
            # Query for most recent weights (descending sort on SK)
            response = self._table.query(
                KeyConditionExpression="PK = :pk",
                ExpressionAttributeValues={":pk": "WEIGHTS#CURRENT"},
                ScanIndexForward=False,  # Descending order (newest first)
                Limit=1,
            )

            items = response.get("Items", [])
            if not items:
                logger.info("No dynamic weights found in DynamoDB")
                return None

            item = items[0]

            # Parse weights from string to Decimal
            weights_str = item.get("weights", {})
            weights = {k: Decimal(v) for k, v in weights_str.items()}

            logger.info(
                "Loaded dynamic weights from DynamoDB",
                extra={
                    "strategy_count": len(weights),
                    "updated_at": item.get("updated_at"),
                },
            )

            return weights

        except DynamoDBException as e:
            logger.error(
                f"Failed to get dynamic weights: {e}",
                extra={"error_type": type(e).__name__},
            )
            return None

    def get_weights_history(self, days: int = 30) -> list[dict[str, Any]]:
        """Get historical dynamic weights records.

        Args:
            days: Number of days of history to retrieve

        Returns:
            List of weight records (most recent first)

        """
        cutoff = datetime.now(UTC) - timedelta(days=days)
        cutoff_iso = cutoff.isoformat()

        try:
            response = self._table.query(
                KeyConditionExpression="PK = :pk AND SK >= :cutoff",
                ExpressionAttributeValues={":pk": "WEIGHTS#CURRENT", ":cutoff": cutoff_iso},
                ScanIndexForward=False,  # Descending order (newest first)
            )

            items = response.get("Items", [])

            # Handle pagination
            while "LastEvaluatedKey" in response:
                response = self._table.query(
                    KeyConditionExpression="PK = :pk AND SK >= :cutoff",
                    ExpressionAttributeValues={":pk": "WEIGHTS#CURRENT", ":cutoff": cutoff_iso},
                    ScanIndexForward=False,
                    ExclusiveStartKey=response["LastEvaluatedKey"],
                )
                items.extend(response.get("Items", []))

            logger.info(f"Retrieved {len(items)} weight history records")

            return [dict(item) for item in items]

        except DynamoDBException as e:
            logger.error(
                f"Failed to get weights history: {e}",
                extra={"error_type": type(e).__name__},
            )
            return []
