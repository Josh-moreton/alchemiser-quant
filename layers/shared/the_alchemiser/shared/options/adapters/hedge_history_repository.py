"""Business Unit: shared | Status: current.

DynamoDB repository for hedge history audit trail.

Manages audit trail records for all hedge actions with querying
capabilities for compliance and historical analysis.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.options.schemas.hedge_history_record import (
    HedgeAction,
    HedgeHistoryRecord,
)

logger = get_logger(__name__)

__all__ = ["HedgeHistoryRepository"]

# DynamoDB exception types for error handling
DynamoDBException = (ClientError, BotoCoreError)


class HedgeHistoryRepository:
    """Repository for hedge history audit trail using DynamoDB.

    Table structure:
    - PK (partition key): account_id
    - SK (sort key): timestamp_action (ISO timestamp + action type)

    This design allows efficient querying of:
    - All actions for an account (query by PK)
    - Actions within a time range (query by PK with SK condition)
    - Latest actions (query descending on SK)
    """

    def __init__(self, table_name: str) -> None:
        """Initialize repository.

        Args:
            table_name: DynamoDB table name

        """
        self._dynamodb = boto3.resource("dynamodb")
        self._table = self._dynamodb.Table(table_name)
        logger.debug("Initialized hedge history repository", table=table_name)

    def record_action(
        self,
        account_id: str,
        action: HedgeAction,
        hedge_id: str,
        correlation_id: str,
        underlying_symbol: str,
        option_symbol: str = "",
        contracts: int = 0,
        premium: Decimal = Decimal("0"),
        details: dict[str, Any] | None = None,
        timestamp: datetime | None = None,
    ) -> bool:
        """Record a hedge action to the audit trail.

        Args:
            account_id: Account ID
            action: Action type
            hedge_id: Hedge identifier
            correlation_id: Correlation ID for tracing
            underlying_symbol: Underlying ETF symbol
            option_symbol: OCC option symbol (optional)
            contracts: Number of contracts (default 0)
            premium: Premium amount (default 0)
            details: Action-specific metadata (optional)
            timestamp: Action timestamp (default: now UTC)

        Returns:
            True if successful, False on error

        """
        if timestamp is None:
            timestamp = datetime.now(UTC)

        if details is None:
            details = {}

        # Create history record
        record = HedgeHistoryRecord(
            account_id=account_id,
            timestamp=timestamp,
            action=action,
            hedge_id=hedge_id,
            option_symbol=option_symbol,
            underlying_symbol=underlying_symbol,
            contracts=contracts,
            premium=premium,
            details=details,
            correlation_id=correlation_id,
        )

        # Calculate TTL (365 days retention)
        ttl = int((timestamp + timedelta(days=365)).timestamp())

        # Build DynamoDB item
        # SK format: ISO timestamp + # + action for sortability and uniqueness
        timestamp_action = f"{timestamp.isoformat()}#{action.value}"

        item: dict[str, Any] = {
            "account_id": record.account_id,
            "timestamp_action": timestamp_action,
            "EntityType": "HEDGE_HISTORY",
            "timestamp": record.timestamp.isoformat(),
            "action": record.action.value,
            "hedge_id": record.hedge_id,
            "option_symbol": record.option_symbol,
            "underlying_symbol": record.underlying_symbol,
            "contracts": record.contracts,
            "premium": str(record.premium),
            "details": record.details,
            "correlation_id": record.correlation_id,
            "ttl": ttl,
        }

        try:
            self._table.put_item(Item=item)
            logger.info(
                "Hedge history record written to DynamoDB",
                account_id=account_id,
                action=action.value,
                hedge_id=hedge_id,
                timestamp=timestamp.isoformat(),
            )
            return True
        except DynamoDBException as e:
            logger.error(
                "Failed to write hedge history record",
                account_id=account_id,
                action=action.value,
                hedge_id=hedge_id,
                error=str(e),
                exc_info=True,
            )
            return False

    def query_history(
        self,
        account_id: str,
        limit: int = 100,
        descending: bool = True,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[HedgeHistoryRecord]:
        """Query hedge history for an account.

        Args:
            account_id: Account ID
            limit: Maximum number of records to return (default 100)
            descending: Sort by time descending (newest first) if True (default)
            start_time: Optional start time filter (inclusive)
            end_time: Optional end time filter (inclusive)

        Returns:
            List of hedge history records

        """
        try:
            query_kwargs: dict[str, Any] = {
                "KeyConditionExpression": "account_id = :account_id",
                "ExpressionAttributeValues": {":account_id": account_id},
                "Limit": limit,
                "ScanIndexForward": not descending,
            }

            # Add time range filter if specified
            if start_time or end_time:
                conditions = []
                if start_time:
                    query_kwargs["ExpressionAttributeValues"][":start"] = start_time.isoformat()
                    conditions.append("timestamp_action >= :start")
                if end_time:
                    # Add a high character to ensure we include all actions at end_time
                    query_kwargs["ExpressionAttributeValues"][":end"] = f"{end_time.isoformat()}~"
                    conditions.append("timestamp_action <= :end")

                if conditions:
                    key_condition = query_kwargs["KeyConditionExpression"]
                    query_kwargs["KeyConditionExpression"] = f"{key_condition} AND {' AND '.join(conditions)}"

            response = self._table.query(**query_kwargs)
            items = response.get("Items", [])

            logger.info(
                "Queried hedge history from DynamoDB",
                account_id=account_id,
                count=len(items),
            )

            return [self._item_to_record(item) for item in items]

        except DynamoDBException as e:
            logger.error(
                "Failed to query hedge history",
                account_id=account_id,
                error=str(e),
                exc_info=True,
            )
            return []

    def query_by_hedge_id(
        self,
        account_id: str,
        hedge_id: str,
    ) -> list[HedgeHistoryRecord]:
        """Query history records for a specific hedge.

        Args:
            account_id: Account ID
            hedge_id: Hedge identifier

        Returns:
            List of hedge history records for the specified hedge

        """
        try:
            response = self._table.query(
                KeyConditionExpression="account_id = :account_id",
                FilterExpression="hedge_id = :hedge_id",
                ExpressionAttributeValues={
                    ":account_id": account_id,
                    ":hedge_id": hedge_id,
                },
            )
            items = response.get("Items", [])

            logger.info(
                "Queried hedge history by hedge_id from DynamoDB",
                account_id=account_id,
                hedge_id=hedge_id,
                count=len(items),
            )

            return [self._item_to_record(item) for item in items]

        except DynamoDBException as e:
            logger.error(
                "Failed to query hedge history by hedge_id",
                account_id=account_id,
                hedge_id=hedge_id,
                error=str(e),
                exc_info=True,
            )
            return []

    def _item_to_record(self, item: dict[str, Any]) -> HedgeHistoryRecord:
        """Convert DynamoDB item to HedgeHistoryRecord DTO.

        Args:
            item: DynamoDB item

        Returns:
            HedgeHistoryRecord DTO

        """
        data = {
            "account_id": item["account_id"],
            "timestamp": datetime.fromisoformat(item["timestamp"]),
            "action": HedgeAction(item["action"]),
            "hedge_id": item["hedge_id"],
            "option_symbol": item.get("option_symbol", ""),
            "underlying_symbol": item["underlying_symbol"],
            "contracts": item.get("contracts", 0),
            "premium": Decimal(item.get("premium", "0")),
            "details": item.get("details", {}),
            "correlation_id": item["correlation_id"],
        }

        return HedgeHistoryRecord(**data)
