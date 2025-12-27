"""Business Unit: data | Status: current.

Bad data marker service for tracking symbols that need data re-fetch.

This service manages DynamoDB markers that flag symbols with bad/stale data.
The validation script (run locally) writes markers, and the Data Lambda
consumes them during scheduled refreshes to re-fetch affected data.

Key design decisions:
- Uses DynamoDB for cross-environment visibility (local script → Lambda)
- Markers have a 30-day TTL for auto-cleanup
- Supports symbol-level marking (full re-fetch) or date-specific marking
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

import boto3
from botocore.exceptions import ClientError

from the_alchemiser.shared.logging import get_logger

if TYPE_CHECKING:
    from mypy_boto3_dynamodb.client import DynamoDBClient

logger = get_logger(__name__)

# Default TTL: 30 days (markers should be processed quickly)
DEFAULT_MARKER_TTL_DAYS = 30


@dataclass(frozen=True)
class BadDataMarker:
    """A marker indicating a symbol needs data re-fetch.

    Attributes:
        symbol: Ticker symbol that needs re-fetch
        reason: Why the data is bad (e.g., "split_adjusted", "missing_data")
        created_at: When the marker was created
        start_date: Optional start date for re-fetch range
        end_date: Optional end date for re-fetch range
        detected_ratio: For split issues, the detected price ratio
        source: What created this marker (e.g., "validation_script", "manual")

    """

    symbol: str
    reason: str
    created_at: datetime
    start_date: str | None = None  # YYYY-MM-DD for partial re-fetch
    end_date: str | None = None  # YYYY-MM-DD for partial re-fetch
    detected_ratio: float | None = None  # For split detection
    source: str = "validation_script"

    @property
    def needs_full_refetch(self) -> bool:
        """Whether this marker requires a full re-fetch vs partial."""
        return self.start_date is None or self.end_date is None


class BadDataMarkerService:
    """Service for reading/writing bad data markers to DynamoDB.

    The markers table uses a simple key structure:
    - PK: SYMBOL#{symbol}
    - SK: MARKER#{created_at_iso}

    This allows querying all markers for a symbol, or scanning all markers.

    Environment Variables:
        BAD_DATA_MARKERS_TABLE: DynamoDB table name
        AWS_REGION: AWS region (default: us-east-1)

    """

    def __init__(
        self,
        table_name: str | None = None,
        dynamodb_client: DynamoDBClient | None = None,
    ) -> None:
        """Initialize bad data marker service.

        Args:
            table_name: DynamoDB table name. If None, uses BAD_DATA_MARKERS_TABLE env var.
            dynamodb_client: DynamoDB client. If None, creates from boto3.

        """
        self.table_name = table_name or os.environ.get("BAD_DATA_MARKERS_TABLE", "")
        self.region = os.environ.get("AWS_REGION", "us-east-1")

        if dynamodb_client is None:
            self._client = boto3.client("dynamodb", region_name=self.region)
        else:
            self._client = dynamodb_client

        if not self.table_name:
            logger.warning("BAD_DATA_MARKERS_TABLE not set - marker operations will be no-ops")

    def _is_configured(self) -> bool:
        """Check if the service is properly configured."""
        return bool(self.table_name)

    def mark_symbol_for_refetch(
        self,
        symbol: str,
        reason: str,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        detected_ratio: float | None = None,
        source: str = "validation_script",
    ) -> bool:
        """Mark a symbol as needing data re-fetch.

        Args:
            symbol: Ticker symbol to mark
            reason: Reason for marking (e.g., "split_adjusted", "missing_data")
            start_date: Optional start of bad data range (YYYY-MM-DD)
            end_date: Optional end of bad data range (YYYY-MM-DD)
            detected_ratio: For split issues, the price ratio detected
            source: What created this marker

        Returns:
            True if marker was created, False otherwise

        """
        if not self._is_configured():
            logger.debug(f"Skipping marker creation for {symbol} - table not configured")
            return False

        now = datetime.now(UTC)
        ttl = int((now + timedelta(days=DEFAULT_MARKER_TTL_DAYS)).timestamp())

        item = {
            "PK": {"S": f"SYMBOL#{symbol}"},
            "SK": {"S": f"MARKER#{now.isoformat()}"},
            "symbol": {"S": symbol},
            "reason": {"S": reason},
            "created_at": {"S": now.isoformat()},
            "source": {"S": source},
            "TTL": {"N": str(ttl)},
        }

        # Add optional fields
        if start_date:
            item["start_date"] = {"S": start_date}
        if end_date:
            item["end_date"] = {"S": end_date}
        if detected_ratio is not None:
            item["detected_ratio"] = {"N": str(detected_ratio)}

        try:
            self._client.put_item(TableName=self.table_name, Item=item)
            logger.info(
                "Created bad data marker",
                symbol=symbol,
                reason=reason,
                start_date=start_date,
                end_date=end_date,
            )
            return True
        except ClientError as e:
            logger.error(
                "Failed to create bad data marker",
                symbol=symbol,
                error=str(e),
            )
            return False

    def get_markers_for_symbol(self, symbol: str) -> list[BadDataMarker]:
        """Get all markers for a specific symbol.

        Args:
            symbol: Ticker symbol

        Returns:
            List of BadDataMarker objects

        """
        if not self._is_configured():
            return []

        try:
            response = self._client.query(
                TableName=self.table_name,
                KeyConditionExpression="PK = :pk",
                ExpressionAttributeValues={":pk": {"S": f"SYMBOL#{symbol}"}},
            )
            return [self._item_to_marker(item) for item in response.get("Items", [])]
        except ClientError as e:
            logger.error(
                "Failed to query markers for symbol",
                symbol=symbol,
                error=str(e),
            )
            return []

    def get_all_pending_markers(self) -> list[BadDataMarker]:
        """Get all pending markers across all symbols.

        Returns:
            List of BadDataMarker objects

        """
        if not self._is_configured():
            return []

        try:
            # Scan is OK here - table should be small (only pending re-fetches)
            response = self._client.scan(TableName=self.table_name)
            return [self._item_to_marker(item) for item in response.get("Items", [])]
        except ClientError as e:
            logger.error("Failed to scan all markers", error=str(e))
            return []

    def get_symbols_needing_refetch(self) -> set[str]:
        """Get set of all symbols with pending markers.

        Returns:
            Set of ticker symbols that need re-fetch

        """
        markers = self.get_all_pending_markers()
        return {m.symbol for m in markers}

    def delete_marker(self, symbol: str, created_at_iso: str) -> bool:
        """Delete a specific marker after it's been processed.

        Args:
            symbol: Ticker symbol
            created_at_iso: ISO timestamp from marker's created_at

        Returns:
            True if deleted, False otherwise

        """
        if not self._is_configured():
            return False

        try:
            self._client.delete_item(
                TableName=self.table_name,
                Key={
                    "PK": {"S": f"SYMBOL#{symbol}"},
                    "SK": {"S": f"MARKER#{created_at_iso}"},
                },
            )
            logger.info("Deleted bad data marker", symbol=symbol, created_at=created_at_iso)
            return True
        except ClientError as e:
            logger.error(
                "Failed to delete marker",
                symbol=symbol,
                created_at=created_at_iso,
                error=str(e),
            )
            return False

    def clear_all_markers_for_symbol(self, symbol: str) -> int:
        """Delete all markers for a symbol after successful re-fetch.

        Args:
            symbol: Ticker symbol

        Returns:
            Number of markers deleted

        """
        markers = self.get_markers_for_symbol(symbol)
        deleted = 0
        for marker in markers:
            if self.delete_marker(symbol, marker.created_at.isoformat()):
                deleted += 1
        return deleted

    def _item_to_marker(self, item: dict[str, Any]) -> BadDataMarker:
        """Convert DynamoDB item to BadDataMarker dataclass."""
        return BadDataMarker(
            symbol=item["symbol"]["S"],
            reason=item["reason"]["S"],
            created_at=datetime.fromisoformat(item["created_at"]["S"]),
            start_date=item.get("start_date", {}).get("S"),
            end_date=item.get("end_date", {}).get("S"),
            detected_ratio=float(item["detected_ratio"]["N"]) if "detected_ratio" in item else None,
            source=item.get("source", {}).get("S", "unknown"),
        )
