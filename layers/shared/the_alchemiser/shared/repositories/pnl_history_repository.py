"""Business Unit: shared | Status: current.

Repository for P&L history in DynamoDB.
"""

from __future__ import annotations

import os
from decimal import Decimal

import boto3

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.pnl_history import PnLHistoryRecord

logger = get_logger(__name__)


class PnLHistoryRepository:
    """Repository for storing and retrieving P&L history from DynamoDB."""

    def __init__(self, table_name: str | None = None) -> None:
        """Initialize repository with DynamoDB table.
        
        Args:
            table_name: DynamoDB table name. If None, reads from PNL_HISTORY_TABLE env var.
        """
        self.table_name = table_name or os.environ.get("PNL_HISTORY_TABLE")
        if not self.table_name:
            raise ValueError("PNL_HISTORY_TABLE environment variable not set")
        
        self.dynamodb = boto3.resource("dynamodb")
        self.table = self.dynamodb.Table(self.table_name)

    def save_record(self, record: PnLHistoryRecord) -> None:
        """Save P&L history record to DynamoDB.
        
        Args:
            record: P&L history record to save.
        """
        try:
            # Convert Pydantic model to dict for DynamoDB
            item = record.model_dump()
            
            self.table.put_item(Item=item)
            
            logger.info(
                "P&L history record saved",
                extra={
                    "account_id": record.account_id,
                    "date": record.date,
                    "pnl": str(record.profit_loss),
                },
            )
        except Exception as e:
            logger.error(
                "Failed to save P&L history record",
                extra={
                    "account_id": record.account_id,
                    "date": record.date,
                    "error": str(e),
                },
                exc_info=True,
            )
            raise

    def save_batch(self, records: list[PnLHistoryRecord]) -> None:
        """Save multiple P&L history records in batch.
        
        Args:
            records: List of P&L history records to save.
        """
        if not records:
            return
        
        try:
            # DynamoDB BatchWriteItem supports up to 25 items per request
            batch_size = 25
            
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                
                with self.table.batch_writer() as writer:
                    for record in batch:
                        writer.put_item(Item=record.model_dump())
            
            logger.info(
                "P&L history batch saved",
                extra={
                    "account_id": records[0].account_id if records else "unknown",
                    "record_count": len(records),
                },
            )
        except Exception as e:
            logger.error(
                "Failed to save P&L history batch",
                extra={
                    "record_count": len(records),
                    "error": str(e),
                },
                exc_info=True,
            )
            raise

    def get_record(self, account_id: str, date: str) -> PnLHistoryRecord | None:
        """Get P&L history record for a specific date.
        
        Args:
            account_id: Alpaca account number.
            date: Date in YYYY-MM-DD format.
            
        Returns:
            PnLHistoryRecord or None if not found.
        """
        try:
            response = self.table.get_item(
                Key={
                    "account_id": account_id,
                    "date": date,
                }
            )
            
            item = response.get("Item")
            if not item:
                return None
            
            return PnLHistoryRecord(**item)
        except Exception as e:
            logger.error(
                "Failed to get P&L history record",
                extra={
                    "account_id": account_id,
                    "date": date,
                    "error": str(e),
                },
                exc_info=True,
            )
            return None

    def get_records_for_period(
        self,
        account_id: str,
        start_date: str,
        end_date: str,
    ) -> list[PnLHistoryRecord]:
        """Get all P&L history records for a date range.
        
        Args:
            account_id: Alpaca account number.
            start_date: Start date in YYYY-MM-DD format (inclusive).
            end_date: End date in YYYY-MM-DD format (inclusive).
            
        Returns:
            List of PnLHistoryRecord objects in chronological order.
        """
        try:
            response = self.table.query(
                KeyConditionExpression="account_id = :aid AND #dt BETWEEN :start AND :end",
                ExpressionAttributeNames={"#dt": "date"},
                ExpressionAttributeValues={
                    ":aid": account_id,
                    ":start": start_date,
                    ":end": end_date,
                },
                ScanIndexForward=True,  # Ascending order (oldest first)
            )
            
            items = response.get("Items", [])
            return [PnLHistoryRecord(**item) for item in items]
        except Exception as e:
            logger.error(
                "Failed to get P&L history for period",
                extra={
                    "account_id": account_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "error": str(e),
                },
                exc_info=True,
            )
            return []

    def get_all_records(self, account_id: str) -> list[PnLHistoryRecord]:
        """Get all P&L history records for an account.
        
        Args:
            account_id: Alpaca account number.
            
        Returns:
            List of PnLHistoryRecord objects in chronological order.
        """
        try:
            response = self.table.query(
                KeyConditionExpression="account_id = :aid",
                ExpressionAttributeValues={":aid": account_id},
                ScanIndexForward=True,  # Ascending order (oldest first)
            )
            
            items = response.get("Items", [])
            
            # Handle pagination if needed
            while "LastEvaluatedKey" in response:
                response = self.table.query(
                    KeyConditionExpression="account_id = :aid",
                    ExpressionAttributeValues={":aid": account_id},
                    ScanIndexForward=True,
                    ExclusiveStartKey=response["LastEvaluatedKey"],
                )
                items.extend(response.get("Items", []))
            
            return [PnLHistoryRecord(**item) for item in items]
        except Exception as e:
            logger.error(
                "Failed to get all P&L history records",
                extra={
                    "account_id": account_id,
                    "error": str(e),
                },
                exc_info=True,
            )
            return []

    def get_latest_record(self, account_id: str) -> PnLHistoryRecord | None:
        """Get the most recent P&L history record.
        
        Args:
            account_id: Alpaca account number.
            
        Returns:
            Latest PnLHistoryRecord or None if not found.
        """
        try:
            response = self.table.query(
                KeyConditionExpression="account_id = :aid",
                ExpressionAttributeValues={":aid": account_id},
                ScanIndexForward=False,  # Descending order (newest first)
                Limit=1,
            )
            
            items = response.get("Items", [])
            if not items:
                return None
            
            return PnLHistoryRecord(**items[0])
        except Exception as e:
            logger.error(
                "Failed to get latest P&L history record",
                extra={
                    "account_id": account_id,
                    "error": str(e),
                },
                exc_info=True,
            )
            return None
