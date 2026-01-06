"""Business Unit: shared | Status: current.

DynamoDB repository for regime state persistence.

Provides read/write access to the cached regime state stored by the
regime detector Lambda. The Strategy Orchestrator reads from here
to get the current market regime for weight adjustment.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import boto3
from botocore.exceptions import ClientError

from .schemas import RegimeState, RegimeType


class RegimeStateRepository:
    """Repository for reading/writing regime state to DynamoDB.

    Table schema:
        PK: "REGIME#current" (singleton for latest regime)
        SK: "STATE"
        Additional GSI for historical queries by date

    Attributes:
        table_name: DynamoDB table name
        ttl_days: Days before automatic cleanup (default: 90)

    """

    # Singleton key for current regime
    CURRENT_REGIME_PK = "REGIME#current"
    CURRENT_REGIME_SK = "STATE"

    def __init__(self, table_name: str, ttl_days: int = 90) -> None:
        """Initialize the repository.

        Args:
            table_name: DynamoDB table name
            ttl_days: TTL in days for automatic cleanup

        """
        self.table_name = table_name
        self.ttl_days = ttl_days
        self._dynamodb = boto3.resource("dynamodb")
        self._table = self._dynamodb.Table(table_name)

    def get_current_regime(self) -> RegimeState | None:
        """Get the current cached regime state.

        Returns:
            RegimeState if found and not stale, None otherwise

        """
        try:
            response = self._table.get_item(
                Key={
                    "PK": self.CURRENT_REGIME_PK,
                    "SK": self.CURRENT_REGIME_SK,
                },
                ConsistentRead=True,
            )

            item = response.get("Item")
            if not item:
                return None

            return self._deserialize_regime_state(item)

        except ClientError:
            return None

    def put_regime_state(self, regime_state: RegimeState) -> None:
        """Store the current regime state.

        Stores as singleton "current" key and also writes a timestamped
        history record for auditing.

        Args:
            regime_state: Regime state to store

        """
        now = datetime.now(UTC)
        ttl = int((now + timedelta(days=self.ttl_days)).timestamp())

        item = self._serialize_regime_state(regime_state)
        item["PK"] = self.CURRENT_REGIME_PK
        item["SK"] = self.CURRENT_REGIME_SK
        item["ttl"] = ttl
        item["updated_at"] = now.isoformat()

        self._table.put_item(Item=item)

        # Also write history record
        history_pk = f"REGIME#history#{now.strftime('%Y-%m-%d')}"
        history_sk = now.isoformat()

        history_item = self._serialize_regime_state(regime_state)
        history_item["PK"] = history_pk
        history_item["SK"] = history_sk
        history_item["ttl"] = ttl

        self._table.put_item(Item=history_item)

    def get_regime_history(
        self,
        start_date: datetime,
        end_date: datetime | None = None,
    ) -> list[RegimeState]:
        """Get regime history for a date range.

        Args:
            start_date: Start of date range
            end_date: End of date range (default: now)

        Returns:
            List of RegimeState objects in chronological order

        """
        if end_date is None:
            end_date = datetime.now(UTC)

        results: list[RegimeState] = []
        current = start_date

        while current <= end_date:
            pk = f"REGIME#history#{current.strftime('%Y-%m-%d')}"

            try:
                response = self._table.query(
                    KeyConditionExpression="PK = :pk",
                    ExpressionAttributeValues={":pk": pk},
                    ScanIndexForward=True,
                )

                for item in response.get("Items", []):
                    state = self._deserialize_regime_state(item)
                    if state:
                        results.append(state)

            except ClientError:
                pass

            current += timedelta(days=1)

        return results

    def _serialize_regime_state(self, state: RegimeState) -> dict[str, Any]:
        """Convert RegimeState to DynamoDB item format.

        Args:
            state: RegimeState to serialize

        Returns:
            Dictionary suitable for DynamoDB

        """
        return {
            "regime": state.regime.value,
            "probability": str(state.probability),
            "bull_probability": str(state.bull_probability),
            "timestamp": state.timestamp.isoformat(),
            "spy_close": str(state.spy_close),
            "lookback_days": state.lookback_days,
            "model_score": str(state.model_score) if state.model_score else None,
            "schema_version": state.schema_version,
        }

    def _deserialize_regime_state(self, item: dict[str, Any]) -> RegimeState | None:
        """Convert DynamoDB item to RegimeState.

        Args:
            item: DynamoDB item dictionary

        Returns:
            RegimeState or None if parsing fails

        """
        try:
            return RegimeState(
                regime=RegimeType(item["regime"]),
                probability=Decimal(item["probability"]),
                bull_probability=Decimal(item["bull_probability"]),
                timestamp=datetime.fromisoformat(item["timestamp"]),
                spy_close=Decimal(item["spy_close"]),
                lookback_days=int(item.get("lookback_days", 20)),
                model_score=(
                    Decimal(item["model_score"])
                    if item.get("model_score")
                    else None
                ),
                schema_version=item.get("schema_version", "1.0.0"),
            )
        except (KeyError, ValueError, TypeError):
            return None

    def is_regime_stale(self, max_age_hours: int = 24) -> bool:
        """Check if the cached regime is stale (older than max_age_hours).

        Args:
            max_age_hours: Maximum age in hours before considered stale

        Returns:
            True if regime is stale or missing

        """
        regime = self.get_current_regime()
        if regime is None:
            return True

        age = datetime.now(UTC) - regime.timestamp
        return age > timedelta(hours=max_age_hours)
