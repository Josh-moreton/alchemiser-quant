"""Business Unit: Execution | Status: current.

DynamoDB repository for pending execution state.

This module provides persistence for time-aware execution state across
Lambda invocations. Each pending execution is stored with:
- Execution metadata (symbol, side, quantities)
- Child order history
- Phase and urgency tracking
- Audit notes

Implements optimistic locking via version field to prevent concurrent
modification issues when multiple ticks process the same execution.
"""

import json
import os
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

import boto3
from botocore.exceptions import ClientError

if TYPE_CHECKING:
    from mypy_boto3_dynamodb.client import DynamoDBClient

from the_alchemiser.execution_v2.time_aware.models import (
    ChildOrder,
    ExecutionPhase,
    ExecutionState,
    OrderStatus,
    PegType,
    PendingExecution,
)
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


class PendingExecutionRepository:
    """Repository for pending execution state in DynamoDB.

    Table Schema:
    - PK: execution_id (partition key)
    - SK: "EXECUTION" (sort key for future extensibility)
    - GSI1PK: state (for querying active executions)
    - GSI1SK: deadline (for ordering by urgency)
    - TTL: expires_at (auto-cleanup after 7 days)

    Implements optimistic locking to prevent concurrent updates.
    """

    def __init__(
        self,
        table_name: str | None = None,
        dynamodb_client: "DynamoDBClient | None" = None,
    ) -> None:
        """Initialize repository.

        Args:
            table_name: DynamoDB table name (defaults to env var)
            dynamodb_client: Optional pre-configured DynamoDB client

        """
        self.table_name = table_name or os.environ.get(
            "PENDING_EXECUTIONS_TABLE", "PendingExecutionsTable"
        )
        self._client = dynamodb_client or boto3.client("dynamodb")

    def save(self, execution: PendingExecution) -> bool:
        """Save or update a pending execution.

        Uses optimistic locking: update only succeeds if version matches.
        On success, increments version.

        Args:
            execution: Execution state to save

        Returns:
            True if save succeeded, False if version conflict

        """
        item = self._to_dynamo_item(execution)

        try:
            if execution.version == 1:
                # New execution: use PutItem with condition
                self._client.put_item(
                    TableName=self.table_name,
                    Item=item,
                    ConditionExpression="attribute_not_exists(PK)",
                )
            else:
                # Update: check version
                self._client.put_item(
                    TableName=self.table_name,
                    Item=item,
                    ConditionExpression="version_num = :expected_version",
                    ExpressionAttributeValues={
                        ":expected_version": {"N": str(execution.version - 1)}
                    },
                )

            logger.info(
                "Saved pending execution",
                extra={
                    "execution_id": execution.execution_id,
                    "version": execution.version,
                    "state": execution.state.value,
                },
            )
            return True

        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                logger.warning(
                    "Version conflict saving execution",
                    extra={
                        "execution_id": execution.execution_id,
                        "version": execution.version,
                    },
                )
                return False
            raise

    def get(self, execution_id: str) -> PendingExecution | None:
        """Retrieve a pending execution by ID.

        Args:
            execution_id: Unique execution identifier

        Returns:
            PendingExecution if found, None otherwise

        """
        try:
            response = self._client.get_item(
                TableName=self.table_name,
                Key={
                    "PK": {"S": execution_id},
                    "SK": {"S": "EXECUTION"},
                },
            )

            if "Item" not in response:
                return None

            return self._from_dynamo_item(response["Item"])

        except ClientError as e:
            logger.error(
                "Failed to get execution",
                extra={"execution_id": execution_id, "error": str(e)},
            )
            raise

    def list_active(self, limit: int = 100) -> list[PendingExecution]:
        """List all active (non-terminal) executions.

        Uses GSI1 to query by state.

        Args:
            limit: Maximum number of results

        Returns:
            List of active PendingExecution objects

        """
        results = []

        for state in (ExecutionState.PENDING, ExecutionState.ACTIVE, ExecutionState.PAUSED):
            try:
                response = self._client.query(
                    TableName=self.table_name,
                    IndexName="GSI1",
                    KeyConditionExpression="GSI1PK = :state",
                    ExpressionAttributeValues={":state": {"S": f"STATE#{state.value}"}},
                    Limit=limit,
                )

                for item in response.get("Items", []):
                    results.append(self._from_dynamo_item(item))

            except ClientError as e:
                logger.error(
                    "Failed to list active executions",
                    extra={"state": state.value, "error": str(e)},
                )
                raise

        return results

    def list_by_symbol(self, symbol: str) -> list[PendingExecution]:
        """List executions for a specific symbol.

        Args:
            symbol: Ticker symbol

        Returns:
            List of PendingExecution objects for symbol

        """
        try:
            response = self._client.query(
                TableName=self.table_name,
                IndexName="GSI2",
                KeyConditionExpression="GSI2PK = :symbol",
                ExpressionAttributeValues={":symbol": {"S": f"SYMBOL#{symbol}"}},
            )

            return [self._from_dynamo_item(item) for item in response.get("Items", [])]

        except ClientError as e:
            logger.error(
                "Failed to list by symbol",
                extra={"symbol": symbol, "error": str(e)},
            )
            raise

    def delete(self, execution_id: str) -> bool:
        """Delete a pending execution.

        Args:
            execution_id: Execution to delete

        Returns:
            True if deleted, False if not found

        """
        try:
            self._client.delete_item(
                TableName=self.table_name,
                Key={
                    "PK": {"S": execution_id},
                    "SK": {"S": "EXECUTION"},
                },
                ConditionExpression="attribute_exists(PK)",
            )
            return True

        except ClientError as e:
            if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                return False
            raise

    def _to_dynamo_item(self, execution: PendingExecution) -> dict[str, Any]:
        """Convert PendingExecution to DynamoDB item format."""
        # Calculate TTL (7 days from now)
        ttl = int((datetime.now(UTC).timestamp()) + (7 * 24 * 60 * 60))

        # Serialize child orders to JSON
        child_orders_json = json.dumps(
            [
                {
                    "child_order_id": o.child_order_id,
                    "broker_order_id": o.broker_order_id,
                    "symbol": o.symbol,
                    "side": o.side,
                    "quantity": str(o.quantity),
                    "filled_quantity": str(o.filled_quantity),
                    "limit_price": str(o.limit_price) if o.limit_price else None,
                    "peg_type": o.peg_type.value,
                    "time_in_force": o.time_in_force,
                    "status": o.status.value,
                    "submitted_at": o.submitted_at.isoformat() if o.submitted_at else None,
                    "filled_at": o.filled_at.isoformat() if o.filled_at else None,
                    "average_fill_price": str(o.average_fill_price)
                    if o.average_fill_price
                    else None,
                    "phase_at_submit": o.phase_at_submit.value if o.phase_at_submit else None,
                }
                for o in execution.child_orders
            ]
        )

        item: dict[str, Any] = {
            "PK": {"S": execution.execution_id},
            "SK": {"S": "EXECUTION"},
            "GSI1PK": {"S": f"STATE#{execution.state.value}"},
            "GSI1SK": {"S": execution.deadline.isoformat() if execution.deadline else "9999-12-31"},
            "GSI2PK": {"S": f"SYMBOL#{execution.symbol}"},
            "GSI2SK": {"S": execution.execution_id},
            "correlation_id": {"S": execution.correlation_id},
            "symbol": {"S": execution.symbol},
            "side": {"S": execution.side},
            "target_quantity": {"N": str(execution.target_quantity)},
            "filled_quantity": {"N": str(execution.filled_quantity)},
            "state": {"S": execution.state.value},
            "current_phase": {"S": execution.current_phase.value},
            "urgency_score": {"N": str(execution.urgency_score)},
            "child_orders": {"S": child_orders_json},
            "execution_policy_id": {"S": execution.execution_policy_id},
            "auction_eligible": {"BOOL": execution.auction_eligible},
            "notes": {"SS": execution.notes if execution.notes else ["_empty"]},
            "version_num": {"N": str(execution.version)},
            "created_at": {"S": execution.created_at.isoformat()},
            "updated_at": {"S": execution.updated_at.isoformat()},
            "ttl": {"N": str(ttl)},
        }

        # Optional fields
        if execution.causation_id:
            item["causation_id"] = {"S": execution.causation_id}
        if execution.average_fill_price:
            item["average_fill_price"] = {"N": str(execution.average_fill_price)}
        if execution.strategy_id:
            item["strategy_id"] = {"S": execution.strategy_id}
        if execution.portfolio_id:
            item["portfolio_id"] = {"S": execution.portfolio_id}
        if execution.deadline:
            item["deadline"] = {"S": execution.deadline.isoformat()}

        return item

    def _from_dynamo_item(self, item: dict[str, Any]) -> PendingExecution:
        """Convert DynamoDB item to PendingExecution."""
        # Parse child orders from JSON
        child_orders_json = json.loads(item["child_orders"]["S"])
        child_orders = [
            ChildOrder(
                child_order_id=o["child_order_id"],
                broker_order_id=o.get("broker_order_id"),
                symbol=o["symbol"],
                side=o["side"],
                quantity=Decimal(o["quantity"]),
                filled_quantity=Decimal(o["filled_quantity"]),
                limit_price=Decimal(o["limit_price"]) if o.get("limit_price") else None,
                peg_type=PegType(o["peg_type"]),
                time_in_force=o["time_in_force"],
                status=OrderStatus(o["status"]),
                submitted_at=datetime.fromisoformat(o["submitted_at"])
                if o.get("submitted_at")
                else None,
                filled_at=datetime.fromisoformat(o["filled_at"]) if o.get("filled_at") else None,
                average_fill_price=Decimal(o["average_fill_price"])
                if o.get("average_fill_price")
                else None,
                phase_at_submit=ExecutionPhase(o["phase_at_submit"])
                if o.get("phase_at_submit")
                else None,
            )
            for o in child_orders_json
        ]

        # Parse notes (handle placeholder)
        notes_set = item.get("notes", {}).get("SS", [])
        notes = [n for n in notes_set if n != "_empty"]

        return PendingExecution(
            execution_id=item["PK"]["S"],
            correlation_id=item["correlation_id"]["S"],
            causation_id=item.get("causation_id", {}).get("S"),
            symbol=item["symbol"]["S"],
            side=item["side"]["S"],
            target_quantity=Decimal(item["target_quantity"]["N"]),
            filled_quantity=Decimal(item["filled_quantity"]["N"]),
            average_fill_price=Decimal(item["average_fill_price"]["N"])
            if "average_fill_price" in item
            else None,
            strategy_id=item.get("strategy_id", {}).get("S"),
            portfolio_id=item.get("portfolio_id", {}).get("S"),
            deadline=datetime.fromisoformat(item["deadline"]["S"]) if "deadline" in item else None,
            created_at=datetime.fromisoformat(item["created_at"]["S"]),
            updated_at=datetime.fromisoformat(item["updated_at"]["S"]),
            state=ExecutionState(item["state"]["S"]),
            current_phase=ExecutionPhase(item["current_phase"]["S"]),
            urgency_score=float(item["urgency_score"]["N"]),
            child_orders=child_orders,
            execution_policy_id=item["execution_policy_id"]["S"],
            auction_eligible=item["auction_eligible"]["BOOL"],
            notes=notes,
            version=int(item["version_num"]["N"]),
        )
