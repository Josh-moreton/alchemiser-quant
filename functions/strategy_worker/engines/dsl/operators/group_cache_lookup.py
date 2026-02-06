"""Business Unit: strategy | Status: current.

Group history cache lookup for portfolio scoring.

This module provides utilities to query cached historical selections
from DynamoDB for accurate filter scoring of groups/portfolios.

When a filter operator needs to compute a metric like moving-average-return
on a group, it needs the historical selections from that group over the
lookback window. This cache provides those selections.
"""

from __future__ import annotations

import os
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

import boto3
from botocore.exceptions import ClientError

from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)

# Environment variable for table name
GROUP_HISTORY_TABLE = os.environ.get("GROUP_HISTORY_TABLE", "")

# Lazy-loaded DynamoDB client
_dynamodb_table = None


def get_dynamodb_table() -> object | None:
    """Get the DynamoDB table resource (lazy-loaded singleton)."""
    global _dynamodb_table
    if _dynamodb_table is None and GROUP_HISTORY_TABLE:
        dynamodb = boto3.resource("dynamodb")
        _dynamodb_table = dynamodb.Table(GROUP_HISTORY_TABLE)
    return _dynamodb_table


def lookup_historical_selections(
    group_id: str,
    lookback_days: int,
    end_date: date | None = None,
) -> dict[str, dict[str, Decimal]]:
    """Look up historical selections for a group from the cache.

    Args:
        group_id: The group identifier (e.g., "ftl_starburst__yinn_yang_mean_reversion")
        lookback_days: Number of days of historical selections to retrieve
        end_date: End date for the lookback window (default: today)

    Returns:
        Dictionary mapping date strings (YYYY-MM-DD) to selection maps.
        Each selection map is {symbol: weight} for that day's portfolio.
        Returns empty dict if cache is unavailable or no data found.

    Example:
        >>> selections = lookup_historical_selections(
        ...     "ftl_starburst__yinn_yang_mean_reversion",
        ...     lookback_days=10
        ... )
        >>> # Returns: {"2026-02-05": {"TQQQ": Decimal("1.0")}, ...}

    """
    table = get_dynamodb_table()
    if table is None:
        logger.debug("Group history cache not available (GROUP_HISTORY_TABLE not set)")
        return {}

    if end_date is None:
        end_date = datetime.now(UTC).date()

    # Calculate date range
    start_date = end_date - timedelta(days=lookback_days)

    # Query for all dates in range
    selections: dict[str, dict[str, Decimal]] = {}

    try:
        # Query using KeyConditionExpression
        # Note: table is typed as object but is a DynamoDB Table resource
        response = table.query(  # type: ignore[attr-defined]
            KeyConditionExpression=("group_id = :gid AND record_date BETWEEN :start AND :end"),
            ExpressionAttributeValues={
                ":gid": group_id,
                ":start": start_date.isoformat(),
                ":end": end_date.isoformat(),
            },
        )

        for item in response.get("Items", []):
            record_date = item.get("record_date", "")
            raw_selections = item.get("selections", {})
            # Convert string weights back to Decimal
            selections[record_date] = {
                symbol: Decimal(weight) for symbol, weight in raw_selections.items()
            }

        logger.debug(
            "Cache lookup successful",
            extra={
                "group_id": group_id,
                "lookback_days": lookback_days,
                "dates_found": len(selections),
            },
        )

    except ClientError as e:
        logger.warning(
            "Failed to query group history cache",
            extra={
                "group_id": group_id,
                "error": str(e),
            },
        )
    except Exception as e:
        logger.warning(
            "Unexpected error querying group history cache",
            extra={
                "group_id": group_id,
                "error": str(e),
            },
        )

    return selections


def is_cache_available() -> bool:
    """Check if the group history cache is configured and available."""
    return bool(GROUP_HISTORY_TABLE and get_dynamodb_table() is not None)
