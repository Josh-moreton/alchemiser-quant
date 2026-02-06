"""Business Unit: strategy | Status: current.

Group history cache lookup for portfolio scoring.

This module provides utilities to query cached historical selections
and pre-computed portfolio daily returns from DynamoDB for accurate
filter scoring of groups/portfolios.

When a filter operator needs to compute a metric like moving-average-return
on a group, it needs the historical return stream of that group over the
lookback window. The Group Cache Lambda evaluates each group daily and stores
both the selections and the portfolio daily return. This module queries
that cache.

Invariants:
    - DynamoDB items contain ``portfolio_daily_return`` (Decimal string) when
      available, alongside ``selections`` ({symbol: weight}).
    - Returns are close-to-close daily percentage changes as Decimals
      (e.g. Decimal("0.0153") for +1.53%).
    - Dates are ISO-8601 strings (YYYY-MM-DD).
"""

from __future__ import annotations

import os
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, InvalidOperation

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


def lookup_historical_returns(
    group_id: str,
    lookback_days: int,
    end_date: date | None = None,
) -> list[Decimal]:
    """Look up pre-computed historical portfolio daily returns from the cache.

    Queries the same DynamoDB table as ``lookup_historical_selections`` but
    extracts the ``portfolio_daily_return`` field written by the Group Cache
    Lambda.  Returns a date-sorted list of Decimal returns suitable for
    direct metric computation (moving-average, stdev, etc.).

    Args:
        group_id: Group identifier (e.g. "ftl_starburst__yinn_yang_mean_reversion")
        lookback_days: Calendar days to look back. The actual number of
            returns will be fewer because weekends/holidays have no entries.
        end_date: End of lookback window (default: today UTC).

    Returns:
        List of Decimal daily returns sorted oldest-first. Each value is
        a fractional return (e.g. Decimal("0.0153") = +1.53%). Empty list
        if cache unavailable or no data.

    Example:
        >>> returns = lookup_historical_returns(
        ...     "ftl_starburst__yinn_yang_mean_reversion",
        ...     lookback_days=15,
        ... )
        >>> len(returns)  # ~10 trading days
        10

    """
    table = get_dynamodb_table()
    if table is None:
        logger.debug("Group history table not available for return lookup")
        return []

    if end_date is None:
        end_date = datetime.now(UTC).date()

    start_date = end_date - timedelta(days=lookback_days)

    try:
        response = table.query(  # type: ignore[attr-defined]
            KeyConditionExpression=("group_id = :gid AND record_date BETWEEN :start AND :end"),
            ExpressionAttributeValues={
                ":gid": group_id,
                ":start": start_date.isoformat(),
                ":end": end_date.isoformat(),
            },
            # Only fetch what we need
            ProjectionExpression="record_date, portfolio_daily_return",
        )

        items = response.get("Items", [])

        # Sort by date (oldest first) and extract returns
        items.sort(key=lambda x: x.get("record_date", ""))

        returns: list[Decimal] = []
        for item in items:
            raw_return = item.get("portfolio_daily_return")
            if raw_return is not None:
                try:
                    returns.append(Decimal(str(raw_return)))
                except (InvalidOperation, ValueError):
                    logger.warning(
                        "Invalid portfolio_daily_return value",
                        extra={
                            "group_id": group_id,
                            "record_date": item.get("record_date"),
                            "raw_value": str(raw_return),
                        },
                    )

        logger.debug(
            "Historical returns lookup successful",
            extra={
                "group_id": group_id,
                "lookback_days": lookback_days,
                "returns_found": len(returns),
            },
        )
        return returns

    except ClientError as e:
        logger.warning(
            "Failed to query historical returns",
            extra={"group_id": group_id, "error": str(e)},
        )
    except Exception as e:
        logger.warning(
            "Unexpected error querying historical returns",
            extra={"group_id": group_id, "error": str(e)},
        )

    return []


def is_cache_available() -> bool:
    """Check if the group history cache is configured and available."""
    return bool(GROUP_HISTORY_TABLE and get_dynamodb_table() is not None)
