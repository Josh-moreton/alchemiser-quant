"""Business Unit: shared | Status: current.

DynamoDB repository for account snapshots.

Implements single-table design consistent with trade ledger repository,
using partition key (PK) and sort key (SK) for efficient querying.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.account_snapshot import AccountSnapshot

logger = get_logger(__name__)

__all__ = ["AccountSnapshotRepository"]

# Import boto3 exceptions for type hints and exception handling
from botocore.exceptions import BotoCoreError, ClientError

DynamoDBException = (ClientError, BotoCoreError)


class AccountSnapshotRepository:
    """Repository for account snapshots using DynamoDB single-table design.

    Table structure:
    - PK: SNAPSHOT#{account_id}
    - SK: SNAP#{ISO timestamp}
    - GSI4: Query by correlation_id + timestamp

    This repository stores and retrieves complete account snapshots for
    deterministic reporting without requiring live API calls.
    """

    def __init__(self, table_name: str) -> None:
        """Initialize repository.

        Args:
            table_name: DynamoDB table name (same as trade ledger table)

        """
        import boto3

        self._dynamodb = boto3.resource("dynamodb")
        self._table = self._dynamodb.Table(table_name)
        logger.debug("Initialized DynamoDB account snapshot repository", table=table_name)

    def put_snapshot(self, snapshot: AccountSnapshot) -> None:
        """Write an account snapshot to DynamoDB.

        Args:
            snapshot: Account snapshot to store

        """
        timestamp_str = snapshot.period_end.isoformat()

        # Convert snapshot to DynamoDB item
        item: dict[str, Any] = {
            "PK": f"SNAPSHOT#{snapshot.account_id}",
            "SK": f"SNAP#{timestamp_str}",
            "EntityType": "SNAPSHOT",
            "snapshot_id": snapshot.snapshot_id,
            "snapshot_version": snapshot.snapshot_version,
            "account_id": snapshot.account_id,
            "period_start": snapshot.period_start.isoformat(),
            "period_end": timestamp_str,
            "correlation_id": snapshot.correlation_id,
            "created_at": snapshot.created_at.isoformat(),
            # Store nested data as JSON (DynamoDB supports nested structures)
            "alpaca_account": self._serialize_nested_data(snapshot.alpaca_account),
            "alpaca_positions": [
                self._serialize_nested_data(pos) for pos in snapshot.alpaca_positions
            ],
            "alpaca_orders": [
                self._serialize_nested_data(order) for order in snapshot.alpaca_orders
            ],
            "internal_ledger": self._serialize_nested_data(snapshot.internal_ledger),
            "checksum": snapshot.checksum,
            "ttl": snapshot.ttl_timestamp,
            # GSI4 for correlation_id queries
            "GSI4PK": f"CORR#{snapshot.correlation_id}",
            "GSI4SK": f"SNAP#{timestamp_str}",
        }

        # Write snapshot item
        self._table.put_item(Item=item)

        logger.info(
            "Account snapshot written to DynamoDB",
            snapshot_id=snapshot.snapshot_id,
            account_id=snapshot.account_id,
            period_end=timestamp_str,
        )

    def _serialize_nested_data(self, data: Any) -> dict[str, Any]:
        """Serialize Pydantic model to dict with string representation of Decimals.

        Args:
            data: Pydantic model or dict to serialize

        Returns:
            Dictionary with Decimals converted to strings

        """
        if hasattr(data, "model_dump"):
            data_dict = data.model_dump()
        else:
            data_dict = dict(data) if isinstance(data, dict) else {}

        return self._convert_decimals_to_strings(data_dict)

    def _convert_decimals_to_strings(self, data: dict[str, Any]) -> dict[str, Any]:
        """Recursively convert Decimal values to strings for DynamoDB storage.

        Args:
            data: Dictionary potentially containing Decimal values

        Returns:
            Dictionary with Decimals converted to strings

        """
        from decimal import Decimal

        result: dict[str, Any] = {}
        for key, value in data.items():
            if isinstance(value, Decimal):
                result[key] = str(value)
            elif isinstance(value, dict):
                result[key] = self._convert_decimals_to_strings(value)
            elif isinstance(value, list):
                result[key] = [
                    self._convert_decimals_to_strings(item) if isinstance(item, dict) else item
                    for item in value
                ]
            elif isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result

    def get_snapshot(self, account_id: str, period_end: datetime) -> AccountSnapshot | None:
        """Get a specific snapshot by account_id and timestamp.

        Args:
            account_id: Account identifier
            period_end: Period end timestamp

        Returns:
            AccountSnapshot or None if not found

        """
        try:
            timestamp_str = period_end.isoformat()
            response = self._table.get_item(
                Key={"PK": f"SNAPSHOT#{account_id}", "SK": f"SNAP#{timestamp_str}"}
            )
            item = response.get("Item")
            if not item:
                return None

            return self._deserialize_snapshot(item)
        except DynamoDBException as e:
            logger.error(
                "Failed to get snapshot",
                account_id=account_id,
                period_end=period_end.isoformat(),
                error=str(e),
            )
            return None

    def get_latest_snapshot(self, account_id: str) -> AccountSnapshot | None:
        """Get the most recent snapshot for an account.

        Args:
            account_id: Account identifier

        Returns:
            Most recent AccountSnapshot or None if no snapshots exist

        """
        try:
            response = self._table.query(
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
                ExpressionAttributeValues={
                    ":pk": f"SNAPSHOT#{account_id}",
                    ":sk": "SNAP#",
                },
                ScanIndexForward=False,  # Most recent first
                Limit=1,
            )
            items = response.get("Items", [])
            if not items:
                return None

            return self._deserialize_snapshot(items[0])
        except DynamoDBException as e:
            logger.error("Failed to get latest snapshot", account_id=account_id, error=str(e))
            return None

    def query_snapshots_by_date_range(
        self,
        account_id: str,
        start_date: datetime,
        end_date: datetime,
        limit: int | None = None,
    ) -> list[AccountSnapshot]:
        """Query snapshots for an account within a date range.

        Args:
            account_id: Account identifier
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)
            limit: Maximum number of snapshots to return

        Returns:
            List of AccountSnapshot objects (most recent first)

        """
        try:
            start_str = start_date.isoformat()
            end_str = end_date.isoformat()

            kwargs: dict[str, Any] = {
                "KeyConditionExpression": "PK = :pk AND SK BETWEEN :start AND :end",
                "ExpressionAttributeValues": {
                    ":pk": f"SNAPSHOT#{account_id}",
                    ":start": f"SNAP#{start_str}",
                    ":end": f"SNAP#{end_str}",
                },
                "ScanIndexForward": False,  # Most recent first
            }

            if limit:
                kwargs["Limit"] = limit

            response = self._table.query(**kwargs)
            items = response.get("Items", [])

            return [self._deserialize_snapshot(item) for item in items]
        except DynamoDBException as e:
            logger.error(
                "Failed to query snapshots by date range",
                account_id=account_id,
                start_date=start_str,
                end_date=end_str,
                error=str(e),
            )
            return []

    def query_snapshots_by_correlation(
        self, correlation_id: str, limit: int | None = None
    ) -> list[AccountSnapshot]:
        """Query snapshots by correlation_id using GSI4.

        Args:
            correlation_id: Correlation identifier
            limit: Maximum number of snapshots to return

        Returns:
            List of AccountSnapshot objects (most recent first)

        """
        try:
            kwargs: dict[str, Any] = {
                "IndexName": "GSI4-CorrelationSnapshotIndex",
                "KeyConditionExpression": "GSI4PK = :pk",
                "ExpressionAttributeValues": {":pk": f"CORR#{correlation_id}"},
                "ScanIndexForward": False,  # Most recent first
            }

            if limit:
                kwargs["Limit"] = limit

            response = self._table.query(**kwargs)
            items = response.get("Items", [])

            return [self._deserialize_snapshot(item) for item in items]
        except DynamoDBException as e:
            logger.error(
                "Failed to query snapshots by correlation",
                correlation_id=correlation_id,
                error=str(e),
            )
            return []

    def _deserialize_snapshot(self, item: dict[str, Any]) -> AccountSnapshot:
        """Deserialize DynamoDB item to AccountSnapshot.

        Args:
            item: DynamoDB item dictionary

        Returns:
            AccountSnapshot instance

        """
        from decimal import Decimal

        from the_alchemiser.shared.schemas.account_snapshot import (
            AlpacaAccountData,
            AlpacaOrderData,
            AlpacaPositionData,
            InternalLedgerSummary,
            StrategyPerformanceData,
        )

        # Deserialize alpaca_account
        alpaca_account = AlpacaAccountData(
            **self._convert_strings_to_decimals(item["alpaca_account"])
        )

        # Deserialize alpaca_positions
        alpaca_positions = [
            AlpacaPositionData(**self._convert_strings_to_decimals(pos))
            for pos in item.get("alpaca_positions", [])
        ]

        # Deserialize alpaca_orders
        alpaca_orders = [
            AlpacaOrderData(**self._convert_strings_to_decimals(order))
            for order in item.get("alpaca_orders", [])
        ]

        # Deserialize internal_ledger with strategy_performance
        internal_ledger_data = self._convert_strings_to_decimals(item["internal_ledger"])
        strategy_performance = {}
        if "strategy_performance" in internal_ledger_data:
            for strategy_name, perf_data in internal_ledger_data["strategy_performance"].items():
                strategy_performance[strategy_name] = StrategyPerformanceData(
                    **self._convert_strings_to_decimals(perf_data)
                )
        internal_ledger_data["strategy_performance"] = strategy_performance
        internal_ledger = InternalLedgerSummary(**internal_ledger_data)

        # Build AccountSnapshot
        return AccountSnapshot(
            snapshot_id=item["snapshot_id"],
            snapshot_version=item.get("snapshot_version", "1.0"),
            account_id=item["account_id"],
            period_start=datetime.fromisoformat(item["period_start"]),
            period_end=datetime.fromisoformat(item["period_end"]),
            correlation_id=item["correlation_id"],
            created_at=datetime.fromisoformat(item["created_at"]),
            alpaca_account=alpaca_account,
            alpaca_positions=alpaca_positions,
            alpaca_orders=alpaca_orders,
            internal_ledger=internal_ledger,
            checksum=item["checksum"],
        )

    def _convert_strings_to_decimals(self, data: dict[str, Any]) -> dict[str, Any]:
        """Recursively convert string representations back to Decimals.

        Args:
            data: Dictionary with string representations of Decimals

        Returns:
            Dictionary with Decimals restored

        """
        from decimal import Decimal

        result: dict[str, Any] = {}
        for key, value in data.items():
            # Convert string to Decimal for known decimal fields
            if key in {
                "buying_power",
                "cash",
                "equity",
                "portfolio_value",
                "last_equity",
                "long_market_value",
                "short_market_value",
                "initial_margin",
                "maintenance_margin",
                "qty",
                "qty_available",
                "avg_entry_price",
                "current_price",
                "market_value",
                "cost_basis",
                "unrealized_pl",
                "unrealized_plpc",
                "unrealized_intraday_pl",
                "unrealized_intraday_plpc",
                "notional",
                "filled_qty",
                "filled_avg_price",
                "limit_price",
                "stop_price",
                "total_buy_value",
                "total_sell_value",
                "gross_pnl",
                "realized_pnl",
            }:
                if value is not None and isinstance(value, str):
                    result[key] = Decimal(value)
                else:
                    result[key] = value
            elif isinstance(value, dict):
                result[key] = self._convert_strings_to_decimals(value)
            elif isinstance(value, list):
                result[key] = [
                    self._convert_strings_to_decimals(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                result[key] = value
        return result
