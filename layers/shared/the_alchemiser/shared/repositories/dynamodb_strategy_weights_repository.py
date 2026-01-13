"""Business Unit: shared | Status: current.

DynamoDB repository for strategy weights with Calmar-tilted adjustments.

Implements single-table design with versioning for historical tracking
of weight adjustments over time.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from botocore.exceptions import BotoCoreError, ClientError

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.strategy_weights import (
    CalmarMetrics,
    StrategyWeights,
    StrategyWeightsHistory,
)

logger = get_logger(__name__)

__all__ = ["DynamoDBStrategyWeightsRepository"]

# DynamoDB exception types for error handling
DynamoDBException = (ClientError, BotoCoreError)

# Entity type constants
CURRENT_WEIGHTS_PK = "WEIGHTS#CURRENT"
CURRENT_WEIGHTS_SK = "METADATA"
VERSION_PREFIX = "VERSION#"


class DynamoDBStrategyWeightsRepository:
    """Repository for strategy weights using DynamoDB single-table design.

    Table structure:
    - Main table: PK (partition key), SK (sort key)
    - GSI1: Query by version for historical tracking

    Entity types:
    - CURRENT: Current active weights (PK=WEIGHTS#CURRENT, SK=METADATA)
    - VERSION: Historical weight snapshots (PK=WEIGHTS#CURRENT, SK=VERSION#{timestamp})
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

    def get_current_weights(self) -> StrategyWeights | None:
        """Get current active strategy weights.

        Returns:
            Current StrategyWeights or None if not found

        """
        try:
            response = self._table.get_item(Key={"PK": CURRENT_WEIGHTS_PK, "SK": CURRENT_WEIGHTS_SK})

            item = response.get("Item")
            if not item:
                logger.info("No current strategy weights found in DynamoDB")
                return None

            # Convert DynamoDB item to DTO
            weights = self._item_to_weights_dto(item)
            logger.info(
                "Loaded current strategy weights",
                version=weights.version,
                strategy_count=len(weights.realized_weights),
            )
            return weights

        except DynamoDBException as e:
            logger.error("Failed to get current strategy weights", error=str(e), exc_info=True)
            raise

    def put_current_weights(
        self, weights: StrategyWeights, correlation_id: str, reason: str = "update"
    ) -> None:
        """Save current strategy weights and create historical snapshot.

        Args:
            weights: Strategy weights to save
            correlation_id: Correlation ID for traceability
            reason: Reason for weight update

        """
        now = datetime.now(UTC)
        version_timestamp = now.isoformat()

        try:
            # Prepare current weights item
            current_item = self._weights_dto_to_item(weights)
            current_item.update(
                {
                    "PK": CURRENT_WEIGHTS_PK,
                    "SK": CURRENT_WEIGHTS_SK,
                    "EntityType": "CURRENT_WEIGHTS",
                    "updated_at": now.isoformat(),
                }
            )

            # Prepare version history item
            history = StrategyWeightsHistory(
                version=weights.version,
                weights=weights,
                reason=reason,
                correlation_id=correlation_id,
                created_at=now,
            )
            version_item = self._history_dto_to_item(history)
            version_item.update(
                {
                    "PK": CURRENT_WEIGHTS_PK,
                    "SK": f"{VERSION_PREFIX}{version_timestamp}",
                    "EntityType": "VERSION_HISTORY",
                    # GSI keys for version queries
                    "GSI1PK": "HISTORY#ALL",
                    "GSI1SK": f"VERSION#{version_timestamp}",
                }
            )

            # Write both items (current + history)
            self._table.put_item(Item=current_item)
            self._table.put_item(Item=version_item)

            logger.info(
                "Strategy weights saved to DynamoDB",
                version=weights.version,
                reason=reason,
                correlation_id=correlation_id,
            )

        except DynamoDBException as e:
            logger.error(
                "Failed to save strategy weights",
                version=weights.version,
                error=str(e),
                exc_info=True,
            )
            raise

    def get_version_history(self, limit: int = 10) -> list[StrategyWeightsHistory]:
        """Get version history of strategy weights.

        Args:
            limit: Maximum number of versions to return (default: 10)

        Returns:
            List of historical weight snapshots, newest first

        """
        try:
            response = self._table.query(
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
                ExpressionAttributeValues={":pk": CURRENT_WEIGHTS_PK, ":sk_prefix": VERSION_PREFIX},
                ScanIndexForward=False,  # Newest first
                Limit=limit,
            )

            items = response.get("Items", [])
            history = [self._item_to_history_dto(item) for item in items]

            logger.info("Loaded strategy weights history", count=len(history), limit=limit)
            return history

        except DynamoDBException as e:
            logger.error("Failed to get version history", error=str(e), exc_info=True)
            raise

    def initialize_weights_from_base(
        self,
        base_weights: dict[str, float],
        initial_calmar_metrics: dict[str, dict[str, float]],
        correlation_id: str,
    ) -> StrategyWeights:
        """Initialize strategy weights from base configuration.

        This is used for first-time setup or reset of strategy weights.

        Args:
            base_weights: Base weights from strategy.prod.json
            initial_calmar_metrics: Initial Calmar metrics by strategy name
            correlation_id: Correlation ID for traceability

        Returns:
            Initialized StrategyWeights

        """
        now = datetime.now(UTC)

        # Convert base weights to Decimal
        base_weights_decimal = {k: Decimal(str(v)) for k, v in base_weights.items()}

        # Convert initial Calmar metrics to CalmarMetrics DTOs
        calmar_dtos: dict[str, CalmarMetrics] = {}
        for strategy_name, metrics in initial_calmar_metrics.items():
            calmar_dtos[strategy_name] = CalmarMetrics(
                strategy_name=strategy_name,
                twelve_month_return=Decimal(str(metrics.get("twelve_month_return", 0))),
                twelve_month_max_drawdown=Decimal(str(metrics.get("twelve_month_max_drawdown", 1))),
                calmar_ratio=Decimal(str(metrics.get("calmar_ratio", 0))),
                months_of_data=int(metrics.get("months_of_data", 12)),
                as_of=now,
            )

        # Initialize with base weights = target = realized (no tilt yet)
        weights = StrategyWeights(
            version="v1",
            base_weights=base_weights_decimal,
            target_weights=base_weights_decimal.copy(),
            realized_weights=base_weights_decimal.copy(),
            calmar_metrics=calmar_dtos,
            adjustment_lambda=Decimal("0.1"),
            rebalance_frequency_days=30,
            last_rebalance=now,
            next_rebalance=None,  # Will be set by weight management service
            created_at=now,
            updated_at=now,
        )

        # Save to DynamoDB
        self.put_current_weights(weights, correlation_id, reason="initialization")

        logger.info(
            "Initialized strategy weights from base configuration",
            strategy_count=len(base_weights),
            correlation_id=correlation_id,
        )

        return weights

    def _item_to_weights_dto(self, item: dict[str, Any]) -> StrategyWeights:
        """Convert DynamoDB item to StrategyWeights DTO.

        Args:
            item: DynamoDB item

        Returns:
            StrategyWeights instance

        """
        # Convert weight dictionaries from DynamoDB format
        base_weights = {k: Decimal(v) for k, v in item.get("base_weights", {}).items()}
        target_weights = {k: Decimal(v) for k, v in item.get("target_weights", {}).items()}
        realized_weights = {k: Decimal(v) for k, v in item.get("realized_weights", {}).items()}

        # Convert Calmar metrics
        calmar_metrics: dict[str, CalmarMetrics] = {}
        for strategy_name, metrics_dict in item.get("calmar_metrics", {}).items():
            calmar_metrics[strategy_name] = CalmarMetrics(
                strategy_name=strategy_name,
                twelve_month_return=Decimal(metrics_dict["twelve_month_return"]),
                twelve_month_max_drawdown=Decimal(metrics_dict["twelve_month_max_drawdown"]),
                calmar_ratio=Decimal(metrics_dict["calmar_ratio"]),
                months_of_data=int(metrics_dict.get("months_of_data", 12)),
                as_of=datetime.fromisoformat(metrics_dict["as_of"]),
            )

        # Parse timestamps
        last_rebalance = (
            datetime.fromisoformat(item["last_rebalance"]) if item.get("last_rebalance") else None
        )
        next_rebalance = (
            datetime.fromisoformat(item["next_rebalance"]) if item.get("next_rebalance") else None
        )

        return StrategyWeights(
            version=item["version"],
            base_weights=base_weights,
            target_weights=target_weights,
            realized_weights=realized_weights,
            calmar_metrics=calmar_metrics,
            adjustment_lambda=Decimal(item.get("adjustment_lambda", "0.1")),
            rebalance_frequency_days=int(item.get("rebalance_frequency_days", 30)),
            last_rebalance=last_rebalance,
            next_rebalance=next_rebalance,
            created_at=datetime.fromisoformat(item["created_at"]),
            updated_at=datetime.fromisoformat(item["updated_at"]),
        )

    def _weights_dto_to_item(self, weights: StrategyWeights) -> dict[str, Any]:
        """Convert StrategyWeights DTO to DynamoDB item.

        Args:
            weights: StrategyWeights instance

        Returns:
            DynamoDB item dictionary

        """
        # Convert Calmar metrics to DynamoDB format
        calmar_metrics_dict: dict[str, Any] = {}
        for strategy_name, metrics in weights.calmar_metrics.items():
            calmar_metrics_dict[strategy_name] = {
                "twelve_month_return": str(metrics.twelve_month_return),
                "twelve_month_max_drawdown": str(metrics.twelve_month_max_drawdown),
                "calmar_ratio": str(metrics.calmar_ratio),
                "months_of_data": metrics.months_of_data,
                "as_of": metrics.as_of.isoformat(),
            }

        item: dict[str, Any] = {
            "version": weights.version,
            "base_weights": {k: str(v) for k, v in weights.base_weights.items()},
            "target_weights": {k: str(v) for k, v in weights.target_weights.items()},
            "realized_weights": {k: str(v) for k, v in weights.realized_weights.items()},
            "calmar_metrics": calmar_metrics_dict,
            "adjustment_lambda": str(weights.adjustment_lambda),
            "rebalance_frequency_days": weights.rebalance_frequency_days,
            "created_at": weights.created_at.isoformat(),
            "updated_at": weights.updated_at.isoformat(),
        }

        if weights.last_rebalance:
            item["last_rebalance"] = weights.last_rebalance.isoformat()
        if weights.next_rebalance:
            item["next_rebalance"] = weights.next_rebalance.isoformat()

        return item

    def _item_to_history_dto(self, item: dict[str, Any]) -> StrategyWeightsHistory:
        """Convert DynamoDB item to StrategyWeightsHistory DTO.

        Args:
            item: DynamoDB item

        Returns:
            StrategyWeightsHistory instance

        """
        # Extract nested weights
        weights_data = {
            "version": item["version"],
            "base_weights": item["base_weights"],
            "target_weights": item["target_weights"],
            "realized_weights": item["realized_weights"],
            "calmar_metrics": item.get("calmar_metrics", {}),
            "adjustment_lambda": item.get("adjustment_lambda", "0.1"),
            "rebalance_frequency_days": item.get("rebalance_frequency_days", 30),
            "last_rebalance": item.get("last_rebalance"),
            "next_rebalance": item.get("next_rebalance"),
            "created_at": item["weights_created_at"],
            "updated_at": item["weights_updated_at"],
        }
        weights = self._item_to_weights_dto(weights_data)

        return StrategyWeightsHistory(
            version=item["version"],
            weights=weights,
            reason=item["reason"],
            correlation_id=item["correlation_id"],
            created_at=datetime.fromisoformat(item["created_at"]),
        )

    def _history_dto_to_item(self, history: StrategyWeightsHistory) -> dict[str, Any]:
        """Convert StrategyWeightsHistory DTO to DynamoDB item.

        Args:
            history: StrategyWeightsHistory instance

        Returns:
            DynamoDB item dictionary

        """
        weights_item = self._weights_dto_to_item(history.weights)

        item: dict[str, Any] = {
            "version": history.version,
            "reason": history.reason,
            "correlation_id": history.correlation_id,
            "created_at": history.created_at.isoformat(),
            # Flatten nested weights with prefix to avoid key conflicts
            "weights_created_at": weights_item["created_at"],
            "weights_updated_at": weights_item["updated_at"],
            **weights_item,
        }

        return item
