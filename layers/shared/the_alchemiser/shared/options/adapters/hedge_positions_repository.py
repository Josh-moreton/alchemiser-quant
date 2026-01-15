"""Business Unit: shared | Status: current.

DynamoDB repository for hedge positions.

Manages active options hedge positions with lifecycle tracking
and roll management queries.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.options.schemas.hedge_position import (
    HedgePosition,
    HedgePositionState,
)

logger = get_logger(__name__)

__all__ = ["HedgePositionsRepository"]

# DynamoDB exception types for error handling
DynamoDBException = (ClientError, BotoCoreError)


class HedgePositionsRepository:
    """Repository for hedge positions using DynamoDB single-table design.

    Table structure:
    - Main table: PK (partition key), SK (sort key)
    - GSI1: UnderlyingExpirationIndex for roll queries

    Key schema:
    - PK: HEDGE#{hedge_id}
    - SK: METADATA
    - GSI1PK: STATUS#{status}#UNDERLYING#{symbol}
    - GSI1SK: EXPIRATION#{expiration_date}
    """

    def __init__(self, table_name: str) -> None:
        """Initialize repository.

        Args:
            table_name: DynamoDB table name

        """
        self._dynamodb = boto3.resource("dynamodb")
        self._table = self._dynamodb.Table(table_name)
        logger.debug("Initialized hedge positions repository", table=table_name)

    def put_position(self, position: HedgePosition) -> None:
        """Write a hedge position to DynamoDB.

        Args:
            position: Hedge position DTO

        """
        now = datetime.now(UTC)
        ttl = int((now + timedelta(days=365)).timestamp())  # 1 year retention

        item: dict[str, Any] = {
            "PK": f"HEDGE#{position.hedge_id}",
            "SK": "METADATA",
            "EntityType": "HEDGE_POSITION",
            # Position identification
            "hedge_id": position.hedge_id,
            "correlation_id": position.correlation_id,
            # Contract details
            "option_symbol": position.option_symbol,
            "underlying_symbol": position.underlying_symbol,
            "option_type": position.option_type.value,
            "strike_price": str(position.strike_price),
            "expiration_date": position.expiration_date.isoformat(),
            "contracts": position.contracts,
            # Entry details
            "entry_price": str(position.entry_price),
            "entry_date": position.entry_date.isoformat(),
            "entry_delta": str(position.entry_delta),
            "total_premium_paid": str(position.total_premium_paid),
            # State tracking
            "status": position.state.value,
            "roll_state": position.roll_state.value,
            "last_updated": position.last_updated.isoformat()
            if position.last_updated
            else now.isoformat(),
            # Hedge metadata
            "hedge_template": position.hedge_template,
            "created_at": now.isoformat(),
            "ttl": ttl,
            # GSI1 keys for roll queries
            "GSI1PK": f"STATUS#{position.state.value}#UNDERLYING#{position.underlying_symbol}",
            "GSI1SK": f"EXPIRATION#{position.expiration_date.isoformat()}",
        }

        # Optional fields
        if position.current_price is not None:
            item["current_price"] = str(position.current_price)
        if position.current_delta is not None:
            item["current_delta"] = str(position.current_delta)
        if position.current_value is not None:
            item["current_value"] = str(position.current_value)
        if position.unrealized_pnl is not None:
            item["unrealized_pnl"] = str(position.unrealized_pnl)
        if position.nav_at_entry is not None:
            item["nav_at_entry"] = str(position.nav_at_entry)
        if position.nav_percentage is not None:
            item["nav_percentage"] = str(position.nav_percentage)

        try:
            self._table.put_item(Item=item)
            logger.info(
                "Hedge position written to DynamoDB",
                hedge_id=position.hedge_id,
                option_symbol=position.option_symbol,
                status=position.state.value,
            )
        except DynamoDBException as e:
            logger.error(
                "Failed to write hedge position",
                hedge_id=position.hedge_id,
                error=str(e),
                exc_info=True,
            )
            raise

    def get_position(self, hedge_id: str) -> HedgePosition | None:
        """Get a hedge position by ID.

        Args:
            hedge_id: Hedge identifier

        Returns:
            HedgePosition DTO or None if not found

        """
        try:
            response = self._table.get_item(Key={"PK": f"HEDGE#{hedge_id}", "SK": "METADATA"})
            item = response.get("Item")
            if not item:
                return None

            return self._item_to_position(item)
        except DynamoDBException as e:
            logger.error(
                "Failed to get hedge position",
                hedge_id=hedge_id,
                error=str(e),
                exc_info=True,
            )
            return None

    def query_active_positions(
        self,
        expiration_before: date | None = None,
        underlying_symbol: str | None = None,
    ) -> list[dict[str, Any]]:
        """Query active hedge positions.

        Args:
            expiration_before: Filter positions expiring before this date
            underlying_symbol: Filter by underlying symbol

        Returns:
            List of active position dicts (not full HedgePosition DTOs for performance)

        """
        try:
            # Build GSI1PK for active positions
            if underlying_symbol:
                gsi1pk = f"STATUS#active#UNDERLYING#{underlying_symbol.upper()}"
            else:
                # Scan all active positions across underlyings
                return self._scan_active_positions(expiration_before)

            # Query using GSI1
            kwargs: dict[str, Any] = {
                "IndexName": "GSI1-UnderlyingExpirationIndex",
                "KeyConditionExpression": "GSI1PK = :pk",
                "ExpressionAttributeValues": {":pk": gsi1pk},
            }

            # Add expiration filter if provided
            if expiration_before:
                kwargs["KeyConditionExpression"] += " AND GSI1SK < :exp"
                kwargs["ExpressionAttributeValues"][":exp"] = (
                    f"EXPIRATION#{expiration_before.isoformat()}"
                )

            response = self._table.query(**kwargs)
            items = response.get("Items", [])

            # Convert to simplified dicts
            return [self._item_to_dict(item) for item in items]

        except DynamoDBException as e:
            logger.error(
                "Failed to query active positions",
                underlying=underlying_symbol,
                error=str(e),
                exc_info=True,
            )
            return []

    def _scan_active_positions(self, expiration_before: date | None = None) -> list[dict[str, Any]]:
        """Scan for active positions across all underlyings.

        Args:
            expiration_before: Filter positions expiring before this date

        Returns:
            List of active position dicts

        """
        try:
            filter_expr = "#status = :active"
            expr_attr_names = {"#status": "status"}
            expr_attr_values = {":active": "active"}

            if expiration_before:
                filter_expr += " AND expiration_date < :exp"
                expr_attr_values[":exp"] = expiration_before.isoformat()

            response = self._table.scan(
                FilterExpression=filter_expr,
                ExpressionAttributeNames=expr_attr_names,
                ExpressionAttributeValues=expr_attr_values,
            )
            items = response.get("Items", [])

            return [self._item_to_dict(item) for item in items]

        except DynamoDBException as e:
            logger.error(
                "Failed to scan active positions",
                error=str(e),
                exc_info=True,
            )
            return []

    def update_position_status(
        self,
        hedge_id: str,
        new_status: HedgePositionState,
    ) -> bool:
        """Update hedge position status.

        Args:
            hedge_id: Hedge identifier
            new_status: New position status

        Returns:
            True if updated successfully

        """
        try:
            now = datetime.now(UTC)
            self._table.update_item(
                Key={"PK": f"HEDGE#{hedge_id}", "SK": "METADATA"},
                UpdateExpression="SET #status = :status, last_updated = :updated",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":status": new_status.value,
                    ":updated": now.isoformat(),
                },
            )
            logger.info(
                "Updated hedge position status",
                hedge_id=hedge_id,
                new_status=new_status.value,
            )
            return True
        except DynamoDBException as e:
            logger.error(
                "Failed to update position status",
                hedge_id=hedge_id,
                error=str(e),
                exc_info=True,
            )
            return False

    def mark_positions_expired(self, expiration_date: date) -> int:
        """Mark positions expiring on the given date as expired.

        Args:
            expiration_date: Expiration date to check

        Returns:
            Number of positions marked as expired

        """
        try:
            # Query active positions expiring on this date
            positions = self.query_active_positions()
            expired_count = 0

            for pos in positions:
                if pos.get("expiration_date") == expiration_date.isoformat():
                    hedge_id = pos.get("hedge_id", "")
                    if self.update_position_status(hedge_id, HedgePositionState.EXPIRED):
                        expired_count += 1

            logger.info(
                "Marked positions as expired",
                expiration_date=expiration_date.isoformat(),
                count=expired_count,
            )
            return expired_count

        except Exception as e:
            logger.error(
                "Failed to mark positions expired",
                expiration_date=expiration_date.isoformat(),
                error=str(e),
                exc_info=True,
            )
            return 0

    def mark_position_rolled(
        self,
        old_hedge_id: str,
        new_position: HedgePosition,
    ) -> bool:
        """Mark old position as rolled and create new position.

        Args:
            old_hedge_id: ID of position being rolled out
            new_position: New hedge position DTO

        Returns:
            True if both operations succeeded

        """
        try:
            # Update old position status
            if not self.update_position_status(old_hedge_id, HedgePositionState.ROLLING):
                return False

            # Create new position
            self.put_position(new_position)

            logger.info(
                "Position rolled successfully",
                old_hedge_id=old_hedge_id,
                new_hedge_id=new_position.hedge_id,
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to roll position",
                old_hedge_id=old_hedge_id,
                error=str(e),
                exc_info=True,
            )
            return False

    def _item_to_position(self, item: dict[str, Any]) -> HedgePosition:
        """Convert DynamoDB item to HedgePosition DTO.

        Args:
            item: DynamoDB item

        Returns:
            HedgePosition DTO

        """
        data = {
            "hedge_id": item["hedge_id"],
            "correlation_id": item["correlation_id"],
            "option_symbol": item["option_symbol"],
            "underlying_symbol": item["underlying_symbol"],
            "option_type": item["option_type"],
            "strike_price": Decimal(item["strike_price"]),
            "expiration_date": date.fromisoformat(item["expiration_date"]),
            "contracts": int(item["contracts"]),
            "entry_price": Decimal(item["entry_price"]),
            "entry_date": datetime.fromisoformat(item["entry_date"]),
            "entry_delta": Decimal(item["entry_delta"]),
            "total_premium_paid": Decimal(item["total_premium_paid"]),
            "state": HedgePositionState(item["status"]),
            "hedge_template": item.get("hedge_template", "tail_first"),
        }

        # Optional fields
        if "current_price" in item:
            data["current_price"] = Decimal(item["current_price"])
        if "current_delta" in item:
            data["current_delta"] = Decimal(item["current_delta"])
        if "current_value" in item:
            data["current_value"] = Decimal(item["current_value"])
        if "unrealized_pnl" in item:
            data["unrealized_pnl"] = Decimal(item["unrealized_pnl"])
        if "nav_at_entry" in item:
            data["nav_at_entry"] = Decimal(item["nav_at_entry"])
        if "nav_percentage" in item:
            data["nav_percentage"] = Decimal(item["nav_percentage"])
        if "last_updated" in item:
            data["last_updated"] = datetime.fromisoformat(item["last_updated"])

        return HedgePosition(**data)

    def _item_to_dict(self, item: dict[str, Any]) -> dict[str, Any]:
        """Convert DynamoDB item to simplified dict for roll manager.

        Args:
            item: DynamoDB item

        Returns:
            Simplified position dict

        """
        return {
            "hedge_id": item.get("hedge_id", ""),
            "option_symbol": item.get("option_symbol", ""),
            "underlying_symbol": item.get("underlying_symbol", ""),
            "expiration_date": item.get("expiration_date", ""),
            "contracts": int(item.get("contracts", 0)),
            "status": item.get("status", "active"),
            "strike_price": item.get("strike_price", "0"),
            "option_type": item.get("option_type", "put"),
            "entry_price": item.get("entry_price", "0"),
            "entry_date": item.get("entry_date", ""),
        }
