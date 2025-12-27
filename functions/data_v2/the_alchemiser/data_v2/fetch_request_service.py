"""Business Unit: data | Status: current.

Fetch request deduplication service.

Prevents duplicate market data fetches when multiple stages detect missing data
simultaneously. Uses DynamoDB conditional writes to ensure only one fetch proceeds
within a configurable cooldown window.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import boto3
from botocore.exceptions import ClientError

from the_alchemiser.shared.logging import get_logger

if TYPE_CHECKING:
    from mypy_boto3_dynamodb import DynamoDBClient

logger = get_logger(__name__)

# Default cooldown: 15 minutes before allowing another fetch for the same symbol
DEFAULT_COOLDOWN_MINUTES = 15


@dataclass(frozen=True)
class FetchRequestResult:
    """Result of attempting to acquire a fetch lock.

    Attributes:
        can_proceed: Whether this request should proceed with the fetch
        symbol: The symbol that was requested
        was_deduplicated: True if another recent request already exists
        existing_request_time: Timestamp of existing request if deduplicated
        cooldown_remaining_seconds: Seconds until cooldown expires

    """

    can_proceed: bool
    symbol: str
    was_deduplicated: bool
    existing_request_time: str | None = None
    cooldown_remaining_seconds: int = 0


class FetchRequestService:
    """Service for deduplicating market data fetch requests.

    Uses DynamoDB conditional writes to implement a distributed lock with TTL.
    When multiple stages detect missing data for the same symbol simultaneously,
    only the first request within the cooldown window will proceed.

    Attributes:
        table_name: DynamoDB table name for fetch requests
        cooldown_minutes: Minutes before allowing another fetch for same symbol

    """

    def __init__(
        self,
        table_name: str | None = None,
        cooldown_minutes: int | None = None,
        dynamodb_client: DynamoDBClient | None = None,
    ) -> None:
        """Initialize fetch request service.

        Args:
            table_name: DynamoDB table name. If None, reads from FETCH_REQUESTS_TABLE env var.
            cooldown_minutes: Cooldown period. If None, reads from FETCH_COOLDOWN_MINUTES env var.
            dynamodb_client: Optional DynamoDB client for dependency injection (testing).

        Raises:
            ValueError: If table_name is not provided and env var is not set.

        """
        resolved_table = table_name or os.environ.get("FETCH_REQUESTS_TABLE")
        if not resolved_table:
            raise ValueError(
                "table_name required: provide via parameter or FETCH_REQUESTS_TABLE env var"
            )

        self.table_name = resolved_table

        if cooldown_minutes is not None:
            self.cooldown_minutes = cooldown_minutes
        else:
            self.cooldown_minutes = int(
                os.environ.get("FETCH_COOLDOWN_MINUTES", str(DEFAULT_COOLDOWN_MINUTES))
            )

        self._dynamodb_client = dynamodb_client

        logger.info(
            "FetchRequestService initialized",
            table_name=self.table_name,
            cooldown_minutes=self.cooldown_minutes,
        )

    @property
    def dynamodb_client(self) -> DynamoDBClient:
        """Lazy-initialized DynamoDB client."""
        if self._dynamodb_client is None:
            self._dynamodb_client = boto3.client("dynamodb")
        return self._dynamodb_client

    def _get_partition_key(self, symbol: str) -> str:
        """Get partition key for a symbol fetch request."""
        return f"FETCH#{symbol}"

    def _get_ttl(self) -> int:
        """Get TTL timestamp (cooldown period from now)."""
        return int(time.time()) + (self.cooldown_minutes * 60)

    def try_acquire_fetch_lock(
        self,
        symbol: str,
        requesting_stage: str,
        requesting_component: str,
        correlation_id: str,
    ) -> FetchRequestResult:
        """Attempt to acquire a lock for fetching data for a symbol.

        Uses DynamoDB conditional write to ensure only one fetch proceeds
        within the cooldown window. If a recent request exists, returns
        immediately without blocking.

        Args:
            symbol: Ticker symbol to fetch
            requesting_stage: Stage that detected missing data
            requesting_component: Component that detected missing data
            correlation_id: Correlation ID for tracing

        Returns:
            FetchRequestResult indicating whether this request should proceed

        """
        pk = self._get_partition_key(symbol)
        now = datetime.now(UTC)
        now_iso = now.isoformat()
        ttl = self._get_ttl()

        try:
            # Attempt conditional put - fails if item exists and not expired
            self.dynamodb_client.put_item(
                TableName=self.table_name,
                Item={
                    "PK": {"S": pk},
                    "symbol": {"S": symbol},
                    "requesting_stage": {"S": requesting_stage},
                    "requesting_component": {"S": requesting_component},
                    "correlation_id": {"S": correlation_id},
                    "requested_at": {"S": now_iso},
                    "ttl": {"N": str(ttl)},
                },
                ConditionExpression="attribute_not_exists(PK)",
            )

            logger.info(
                "Acquired fetch lock",
                symbol=symbol,
                requesting_stage=requesting_stage,
                correlation_id=correlation_id,
                ttl_minutes=self.cooldown_minutes,
            )

            return FetchRequestResult(
                can_proceed=True,
                symbol=symbol,
                was_deduplicated=False,
            )

        except ClientError as e:
            error_response = e.response.get("Error", {})
            error_code = error_response.get("Code", "")
            if error_code == "ConditionalCheckFailedException":
                # Lock already exists - check when it was created
                existing = self._get_existing_request(pk)

                if existing:
                    # Calculate remaining cooldown
                    existing_ttl = int(existing.get("ttl", {}).get("N", "0"))
                    remaining = max(0, existing_ttl - int(time.time()))

                    logger.info(
                        "Fetch request deduplicated",
                        symbol=symbol,
                        requesting_stage=requesting_stage,
                        existing_stage=existing.get("requesting_stage", {}).get("S", "unknown"),
                        existing_time=existing.get("requested_at", {}).get("S", "unknown"),
                        cooldown_remaining_seconds=remaining,
                        correlation_id=correlation_id,
                    )

                    return FetchRequestResult(
                        can_proceed=False,
                        symbol=symbol,
                        was_deduplicated=True,
                        existing_request_time=existing.get("requested_at", {}).get("S"),
                        cooldown_remaining_seconds=remaining,
                    )

                # Item may have been deleted between check and now - try again
                logger.warning(
                    "Race condition detected, allowing fetch",
                    symbol=symbol,
                    correlation_id=correlation_id,
                )
                return FetchRequestResult(
                    can_proceed=True,
                    symbol=symbol,
                    was_deduplicated=False,
                )

            # Other DynamoDB errors - log and allow fetch to avoid blocking
            logger.error(
                "DynamoDB error acquiring fetch lock",
                symbol=symbol,
                error=str(e),
                correlation_id=correlation_id,
            )
            return FetchRequestResult(
                can_proceed=True,
                symbol=symbol,
                was_deduplicated=False,
            )

    def _get_existing_request(self, pk: str) -> dict[str, Any] | None:
        """Get existing fetch request item if it exists."""
        try:
            response = self.dynamodb_client.get_item(
                TableName=self.table_name,
                Key={"PK": {"S": pk}},
            )
            return response.get("Item")
        except ClientError as e:
            logger.warning(
                "Failed to get existing fetch request",
                pk=pk,
                error=str(e),
            )
            return None

    def release_fetch_lock(self, symbol: str, correlation_id: str) -> bool:
        """Release a fetch lock after completion (optional early release).

        Normally locks expire via TTL. Call this to allow immediate retries
        after a failed fetch.

        Args:
            symbol: Ticker symbol
            correlation_id: Correlation ID for tracing

        Returns:
            True if lock was released, False otherwise

        """
        pk = self._get_partition_key(symbol)

        try:
            self.dynamodb_client.delete_item(
                TableName=self.table_name,
                Key={"PK": {"S": pk}},
            )

            logger.info(
                "Released fetch lock",
                symbol=symbol,
                correlation_id=correlation_id,
            )
            return True

        except ClientError as e:
            logger.warning(
                "Failed to release fetch lock",
                symbol=symbol,
                error=str(e),
                correlation_id=correlation_id,
            )
            return False
