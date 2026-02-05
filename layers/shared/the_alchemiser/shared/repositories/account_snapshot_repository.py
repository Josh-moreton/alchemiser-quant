"""Business Unit: shared | Status: current.

Repository for account snapshots in DynamoDB.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import boto3

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.account_snapshot import AccountSnapshot

logger = get_logger(__name__)


class AccountSnapshotRepository:
    """Repository for storing and retrieving account snapshots from DynamoDB."""

    def __init__(self, table_name: str | None = None) -> None:
        """Initialize repository with DynamoDB table.
        
        Args:
            table_name: DynamoDB table name. If None, reads from ACCOUNT_SNAPSHOTS_TABLE env var.
        """
        self.table_name = table_name or os.environ.get("ACCOUNT_SNAPSHOTS_TABLE")
        if not self.table_name:
            raise ValueError("ACCOUNT_SNAPSHOTS_TABLE environment variable not set")
        
        self.dynamodb = boto3.resource("dynamodb")
        self.table = self.dynamodb.Table(self.table_name)

    def save_snapshot(self, snapshot: AccountSnapshot) -> None:
        """Save account snapshot to DynamoDB.
        
        Args:
            snapshot: Account snapshot to save.
        """
        try:
            # Convert Pydantic model to dict for DynamoDB
            # DynamoDB supports Decimal natively via boto3
            item = snapshot.model_dump()
            
            self.table.put_item(Item=item)
            
            logger.info(
                "Account snapshot saved",
                extra={
                    "snapshot_id": snapshot.snapshot_id,
                    "timestamp": snapshot.timestamp,
                    "equity": str(snapshot.equity),
                },
            )
        except Exception as e:
            logger.error(
                "Failed to save account snapshot",
                extra={
                    "snapshot_id": snapshot.snapshot_id,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise

    def get_latest_snapshot(self, snapshot_id: str = "ACCOUNT") -> AccountSnapshot | None:
        """Get the most recent account snapshot.
        
        Args:
            snapshot_id: Snapshot ID to query (default: "ACCOUNT").
            
        Returns:
            Latest AccountSnapshot or None if not found.
        """
        try:
            response = self.table.query(
                KeyConditionExpression="snapshot_id = :sid",
                ExpressionAttributeValues={":sid": snapshot_id},
                ScanIndexForward=False,  # Descending order (newest first)
                Limit=1,
            )
            
            items = response.get("Items", [])
            if not items:
                return None
            
            return AccountSnapshot(**items[0])
        except Exception as e:
            logger.error(
                "Failed to get latest account snapshot",
                extra={"snapshot_id": snapshot_id, "error": str(e)},
                exc_info=True,
            )
            return None

    def get_snapshots_since(
        self,
        start_timestamp: str,
        snapshot_id: str = "ACCOUNT",
    ) -> list[AccountSnapshot]:
        """Get all snapshots since a given timestamp.
        
        Args:
            start_timestamp: ISO 8601 timestamp to start from.
            snapshot_id: Snapshot ID to query (default: "ACCOUNT").
            
        Returns:
            List of AccountSnapshot objects in chronological order.
        """
        try:
            response = self.table.query(
                KeyConditionExpression="snapshot_id = :sid AND #ts >= :start",
                ExpressionAttributeNames={"#ts": "timestamp"},
                ExpressionAttributeValues={
                    ":sid": snapshot_id,
                    ":start": start_timestamp,
                },
                ScanIndexForward=True,  # Ascending order (oldest first)
            )
            
            items = response.get("Items", [])
            return [AccountSnapshot(**item) for item in items]
        except Exception as e:
            logger.error(
                "Failed to get account snapshots since timestamp",
                extra={
                    "snapshot_id": snapshot_id,
                    "start_timestamp": start_timestamp,
                    "error": str(e),
                },
                exc_info=True,
            )
            return []

    def get_snapshot_at_time(
        self,
        timestamp: str,
        snapshot_id: str = "ACCOUNT",
    ) -> AccountSnapshot | None:
        """Get snapshot at or before a specific timestamp.
        
        Args:
            timestamp: ISO 8601 timestamp to query.
            snapshot_id: Snapshot ID to query (default: "ACCOUNT").
            
        Returns:
            AccountSnapshot at or before the timestamp, or None if not found.
        """
        try:
            response = self.table.query(
                KeyConditionExpression="snapshot_id = :sid AND #ts <= :ts",
                ExpressionAttributeNames={"#ts": "timestamp"},
                ExpressionAttributeValues={
                    ":sid": snapshot_id,
                    ":ts": timestamp,
                },
                ScanIndexForward=False,  # Descending order (newest first)
                Limit=1,
            )
            
            items = response.get("Items", [])
            if not items:
                return None
            
            return AccountSnapshot(**items[0])
        except Exception as e:
            logger.error(
                "Failed to get account snapshot at time",
                extra={
                    "snapshot_id": snapshot_id,
                    "timestamp": timestamp,
                    "error": str(e),
                },
                exc_info=True,
            )
            return None
