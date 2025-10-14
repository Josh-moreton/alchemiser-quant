#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Idempotency support for event-driven architecture.

Provides DynamoDB-backed idempotency checks to prevent duplicate event
processing on Lambda retries, replays, or manual re-invocations.

Key Features:
- DynamoDB-backed deduplication with TTL
- Deterministic event ID extraction
- Error handling for DynamoDB failures
- Graceful degradation when table unavailable

Usage:
    >>> if is_duplicate_event(event_id, table_name="alchemiser-event-dedup-dev"):
    ...     logger.info("Duplicate event, skipping")
    ...     return
    >>> # Process event
    >>> mark_event_processed(event_id, table_name="alchemiser-event-dedup-dev")

"""

from __future__ import annotations

import os
import time
from typing import Any

from .logging import get_logger

logger = get_logger(__name__)

# Default TTL for idempotency records (24 hours in seconds)
DEFAULT_TTL_SECONDS = 86400


def _get_dynamodb_client() -> Any:
    """Get DynamoDB client (lazy initialization).

    Returns:
        DynamoDB client instance

    """
    import boto3
    
    return boto3.client("dynamodb")


def _get_table_name(stage: str = "dev") -> str:
    """Get idempotency table name for the current stage.

    Args:
        stage: Deployment stage (dev/prod)

    Returns:
        DynamoDB table name

    """
    return os.environ.get(
        "IDEMPOTENCY_TABLE_NAME",
        f"alchemiser-event-dedup-{stage}"
    )


def is_duplicate_event(
    event_id: str,
    *,
    table_name: str | None = None,
    stage: str = "dev",
) -> bool:
    """Check if event has already been processed.

    Queries DynamoDB idempotency table to determine if the event_id
    has been seen before. Returns False if table doesn't exist or
    query fails (fail-open for availability).

    Args:
        event_id: Unique event identifier to check
        table_name: DynamoDB table name (defaults to stage-based name)
        stage: Deployment stage for default table name

    Returns:
        True if event has been processed before, False otherwise
        or if check fails (fail-open)

    Examples:
        >>> if is_duplicate_event("evt-123", stage="prod"):
        ...     logger.info("Skipping duplicate event")
        ...     return

    """
    if not event_id:
        logger.warning("Cannot check idempotency: event_id is empty")
        return False
    
    table_name = table_name or _get_table_name(stage)
    
    try:
        client = _get_dynamodb_client()
        response = client.get_item(
            TableName=table_name,
            Key={"event_id": {"S": event_id}},
            ConsistentRead=True,
        )
        
        exists = "Item" in response
        if exists:
            logger.info(
                "Duplicate event detected",
                event_id=event_id,
                table_name=table_name,
            )
        
        return exists
    
    except Exception as e:
        # Fail-open: treat as new event if check fails
        logger.warning(
            "Failed to check idempotency (treating as new event)",
            event_id=event_id,
            table_name=table_name,
            error=str(e),
            error_type=type(e).__name__,
        )
        return False


def mark_event_processed(
    event_id: str,
    *,
    table_name: str | None = None,
    stage: str = "dev",
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> bool:
    """Mark event as processed in idempotency table.

    Writes event_id to DynamoDB with TTL expiration. Returns False
    if write fails but does not raise exception (best-effort).

    Args:
        event_id: Unique event identifier to mark as processed
        table_name: DynamoDB table name (defaults to stage-based name)
        stage: Deployment stage for default table name
        ttl_seconds: Time-to-live in seconds (default: 24 hours)

    Returns:
        True if successfully marked, False if failed

    Examples:
        >>> mark_event_processed("evt-123", stage="prod")
        True

    """
    if not event_id:
        logger.warning("Cannot mark event processed: event_id is empty")
        return False
    
    table_name = table_name or _get_table_name(stage)
    
    try:
        client = _get_dynamodb_client()
        expiry_time = int(time.time()) + ttl_seconds
        
        client.put_item(
            TableName=table_name,
            Item={
                "event_id": {"S": event_id},
                "processed_at": {"N": str(int(time.time()))},
                "ttl": {"N": str(expiry_time)},
            },
        )
        
        logger.debug(
            "Event marked as processed",
            event_id=event_id,
            table_name=table_name,
            ttl_seconds=ttl_seconds,
        )
        return True
    
    except Exception as e:
        # Best-effort: log but don't fail the handler
        logger.error(
            "Failed to mark event as processed",
            event_id=event_id,
            table_name=table_name,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True,
        )
        return False
