"""Business Unit: strategy | Status: current.

Group history cache lookup for portfolio scoring.

This module provides utilities to query cached historical selections
and pre-computed portfolio daily returns for accurate filter scoring
of groups/portfolios.

When a filter operator needs to compute a metric like moving-average-return
on a group, it needs the historical return stream of that group over the
lookback window. The group history is now stored in S3 as Parquet files
(similar to individual ticker data), with DynamoDB as a legacy fallback.

Data Storage:
    - Primary: S3 Parquet files (via GroupHistoryStore)
    - Legacy: DynamoDB table (read-only fallback)

Invariants:
    - Returns are close-to-close daily percentage changes as Decimals
      (e.g. Decimal("0.0153") for +1.53%).
    - Dates are ISO-8601 strings (YYYY-MM-DD).
"""

from __future__ import annotations

import json
import os
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, InvalidOperation

import boto3
import pandas as pd
from botocore.exceptions import ClientError

from the_alchemiser.shared.data_v2.group_history_store import GroupHistoryStore
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)

# Environment variables
GROUP_HISTORY_TABLE = os.environ.get("GROUP_HISTORY_TABLE", "")
MARKET_DATA_BUCKET = os.environ.get("MARKET_DATA_BUCKET", "")

# Lazy-loaded clients
_dynamodb_table = None
_group_history_store = None


def get_dynamodb_table() -> object | None:
    """Get the DynamoDB table resource (lazy-loaded singleton).

    This is maintained for backward compatibility during migration.
    """
    global _dynamodb_table
    if _dynamodb_table is None and GROUP_HISTORY_TABLE:
        dynamodb = boto3.resource("dynamodb")
        _dynamodb_table = dynamodb.Table(GROUP_HISTORY_TABLE)
    return _dynamodb_table


def get_group_history_store() -> GroupHistoryStore | None:
    """Get the GroupHistoryStore instance (lazy-loaded singleton)."""
    global _group_history_store
    if _group_history_store is None and MARKET_DATA_BUCKET:
        try:
            _group_history_store = GroupHistoryStore(bucket_name=MARKET_DATA_BUCKET)
        except Exception as e:
            logger.warning(
                "Failed to initialize GroupHistoryStore",
                error=str(e),
            )
    return _group_history_store


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
    # Try S3 first
    selections = _lookup_selections_from_s3(group_id, lookback_days, end_date)
    if selections:
        return selections

    # Fall back to DynamoDB (legacy)
    return _lookup_selections_from_dynamodb(group_id, lookback_days, end_date)


def _lookup_selections_from_s3(
    group_id: str,
    lookback_days: int,
    end_date: date | None = None,
) -> dict[str, dict[str, Decimal]]:
    """Look up historical selections from S3 Parquet files."""
    store = get_group_history_store()
    if store is None:
        logger.debug("Group history store not available (MARKET_DATA_BUCKET not set)")
        return {}

    if end_date is None:
        end_date = datetime.now(UTC).date()

    start_date = end_date - timedelta(days=lookback_days)

    try:
        df = store.read_group_history(group_id)
        if df is None or df.empty:
            logger.debug(
                "No group history found in S3",
                group_id=group_id,
            )
            return {}

        # Filter to date range
        df["record_date"] = pd.to_datetime(df["record_date"])
        mask = (df["record_date"] >= pd.Timestamp(start_date)) & (
            df["record_date"] <= pd.Timestamp(end_date)
        )
        df = df[mask]

        # Convert to expected format using vectorized approach
        selections: dict[str, dict[str, Decimal]] = {}
        for record in df.to_dict("records"):
            record_date = record["record_date"].strftime("%Y-%m-%d")
            # Parse selections from JSON string or dict
            raw_selections = record.get("selections", {})
            if isinstance(raw_selections, str):
                raw_selections = json.loads(raw_selections)

            selections[record_date] = {
                symbol: Decimal(str(weight)) for symbol, weight in raw_selections.items()
            }

        logger.debug(
            "S3 cache lookup successful",
            group_id=group_id,
            lookback_days=lookback_days,
            dates_found=len(selections),
        )
        return selections

    except Exception as e:
        logger.warning(
            "Failed to query group history from S3",
            group_id=group_id,
            error=str(e),
        )
        return {}


def _lookup_selections_from_dynamodb(
    group_id: str,
    lookback_days: int,
    end_date: date | None = None,
) -> dict[str, dict[str, Decimal]]:
    """Look up historical selections from DynamoDB (legacy fallback)."""
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

        if len(selections) == 0:
            logger.warning(
                "Group history cache returned ZERO records -- cache may not "
                "be populated for this group",
                extra={
                    "group_id": group_id,
                    "lookback_days": lookback_days,
                    "dates_found": 0,
                },
            )
        else:
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

    Queries the group history (S3 or DynamoDB fallback) and extracts the
    ``portfolio_daily_return`` field. Returns a date-sorted list of Decimal
    returns suitable for direct metric computation (moving-average, stdev, etc.).

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
    # Try S3 first
    returns = _lookup_returns_from_s3(group_id, lookback_days, end_date)
    if returns:
        return returns

    # Fall back to DynamoDB (legacy)
    return _lookup_returns_from_dynamodb(group_id, lookback_days, end_date)


def _lookup_returns_from_s3(
    group_id: str,
    lookback_days: int,
    end_date: date | None = None,
) -> list[Decimal]:
    """Look up historical returns from S3 Parquet files."""
    store = get_group_history_store()
    if store is None:
        logger.debug("Group history store not available for return lookup")
        return []

    if end_date is None:
        end_date = datetime.now(UTC).date()

    start_date = end_date - timedelta(days=lookback_days)

    try:
        df = store.read_group_history(group_id)
        if df is None or df.empty:
            logger.debug(
                "No group history found in S3 for returns",
                group_id=group_id,
            )
            return []

        # Filter to date range and sort
        df["record_date"] = pd.to_datetime(df["record_date"])
        mask = (df["record_date"] >= pd.Timestamp(start_date)) & (
            df["record_date"] <= pd.Timestamp(end_date)
        )
        df = df[mask].sort_values("record_date")

        # Extract returns using vectorized conversion
        raw_series = df["portfolio_daily_return"].dropna()
        returns: list[Decimal] = []
        for raw_return in raw_series:
            try:
                returns.append(Decimal(str(raw_return)))
            except (InvalidOperation, ValueError):
                logger.warning(
                    "Invalid portfolio_daily_return value",
                    group_id=group_id,
                    raw_value=str(raw_return),
                )

        logger.debug(
            "S3 historical returns lookup successful",
            group_id=group_id,
            lookback_days=lookback_days,
            returns_found=len(returns),
        )
        return returns

    except Exception as e:
        logger.warning(
            "Failed to query historical returns from S3",
            group_id=group_id,
            error=str(e),
        )
        return []


def _lookup_returns_from_dynamodb(
    group_id: str,
    lookback_days: int,
    end_date: date | None = None,
) -> list[Decimal]:
    """Look up historical returns from DynamoDB (legacy fallback)."""
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

        if len(returns) == 0:
            logger.warning(
                "Historical returns lookup returned ZERO records -- group "
                "cache is empty or unpopulated for the requested window",
                extra={
                    "group_id": group_id,
                    "lookback_days": lookback_days,
                    "returns_found": 0,
                },
            )
        else:
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
    """Check if the group history cache is configured and available.

    Returns True if either S3 (preferred) or DynamoDB (legacy) is available.
    """
    # Check S3 first
    if MARKET_DATA_BUCKET and get_group_history_store() is not None:
        return True
    # Fall back to DynamoDB
    return bool(GROUP_HISTORY_TABLE and get_dynamodb_table() is not None)


def write_historical_return(
    group_id: str,
    record_date: str,
    selections: dict[str, str],
    portfolio_daily_return: Decimal,
    *,
    ttl_days: int = 30,
) -> bool:
    """Write a single historical return entry to the group cache.

    Used by on-demand backfill when the strategy worker detects a cache miss
    during portfolio scoring and re-evaluates the group for historical dates.

    Args:
        group_id: Group identifier (hash-based, e.g. "max_dd_tqqq_vs_uvxy_a1b2c3d4e5f6")
        record_date: ISO date string (YYYY-MM-DD)
        selections: Symbol-to-weight mapping (weights as strings)
        portfolio_daily_return: Daily return as Decimal (e.g. Decimal("0.0153"))
        ttl_days: TTL in days for the DynamoDB item (default: 30)

    Returns:
        True if write succeeded, False otherwise.

    """
    table = get_dynamodb_table()
    if table is None:
        logger.warning("Cannot write to group cache: table not available")
        return False

    ttl_epoch = int((datetime.now(UTC) + timedelta(days=ttl_days)).timestamp())

    try:
        table.put_item(  # type: ignore[attr-defined]
            Item={
                "group_id": group_id,
                "record_date": record_date,
                "selections": selections,
                "selection_count": len(selections),
                "portfolio_daily_return": str(portfolio_daily_return),
                "evaluated_at": datetime.now(UTC).isoformat(),
                "source": "on_demand_backfill",
                "ttl": ttl_epoch,
            },
        )
        logger.debug(
            "Wrote historical return to cache",
            extra={
                "group_id": group_id,
                "record_date": record_date,
                "portfolio_daily_return": str(portfolio_daily_return),
            },
        )
        return True

    except ClientError as e:
        logger.warning(
            "Failed to write historical return to cache",
            extra={
                "group_id": group_id,
                "record_date": record_date,
                "error": str(e),
            },
        )
        return False
    except Exception as e:
        logger.warning(
            "Unexpected error writing historical return to cache",
            extra={
                "group_id": group_id,
                "record_date": record_date,
                "error": str(e),
            },
        )
        return False
