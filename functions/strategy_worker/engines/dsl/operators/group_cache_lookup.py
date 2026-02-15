"""Business Unit: strategy | Status: current.

Group history cache lookup for portfolio scoring.

This module provides utilities to query cached historical selections
and pre-computed portfolio daily returns from S3 for accurate
filter scoring of groups/portfolios.

When a filter operator needs to compute a metric like moving-average-return
on a group, it needs the historical return stream of that group over the
lookback window. Group history is stored in S3 as Parquet files, mirroring
the MarketDataStore pattern.

Invariants:
    - Parquet files contain ``portfolio_daily_return`` (Decimal) alongside
      ``selections`` (dict serialized as string).
    - Returns are close-to-close daily percentage changes as Decimals
      (e.g. Decimal("0.0153") for +1.53%).
    - Dates are in ``record_date`` column as ISO-8601 strings (YYYY-MM-DD).
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, InvalidOperation

import pandas as pd

from the_alchemiser.shared.data_v2.group_history_store import GroupHistoryStore
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)

# Lazy-loaded GroupHistoryStore
_group_history_store: GroupHistoryStore | None = None


def get_group_history_store() -> GroupHistoryStore | None:
    """Get the GroupHistoryStore instance (lazy-loaded singleton)."""
    global _group_history_store
    if _group_history_store is None:
        try:
            _group_history_store = GroupHistoryStore()
        except ValueError as e:
            logger.warning(
                "GroupHistoryStore not available",
                error=str(e),
            )
            return None
    return _group_history_store


def lookup_historical_selections(
    group_id: str,
    lookback_days: int,
    end_date: date | None = None,
) -> dict[str, dict[str, Decimal]]:
    """Look up historical selections for a group from S3.

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
    store = get_group_history_store()
    if store is None:
        logger.debug("Group history store not available")
        return {}

    if end_date is None:
        end_date = datetime.now(UTC).date()

    # Calculate date range
    start_date = end_date - timedelta(days=lookback_days)

    # Read group data from S3
    df = store.read_group_data(group_id)
    if df is None or df.empty:
        logger.warning(
            "Group history returned ZERO records -- cache may not "
            "be populated for this group",
            group_id=group_id,
            lookback_days=lookback_days,
            dates_found=0,
        )
        return {}

    # Filter by date range
    df["record_date"] = pd.to_datetime(df["record_date"])
    mask = (df["record_date"].dt.date >= start_date) & (df["record_date"].dt.date <= end_date)
    df_filtered = df[mask]

    # Build selections dictionary
    selections: dict[str, dict[str, Decimal]] = {}
    for _, row in df_filtered.iterrows():
        record_date_str = row["record_date"].strftime("%Y-%m-%d")
        # Parse selections from JSON string if needed
        raw_selections = row.get("selections", {})
        if isinstance(raw_selections, str):
            import json

            raw_selections = json.loads(raw_selections)

        selections[record_date_str] = {
            symbol: Decimal(str(weight)) for symbol, weight in raw_selections.items()
        }

    if len(selections) == 0:
        logger.warning(
            "Group history filtered to ZERO records for date range",
            group_id=group_id,
            lookback_days=lookback_days,
            dates_found=0,
        )
    else:
        logger.debug(
            "Cache lookup successful",
            group_id=group_id,
            lookback_days=lookback_days,
            dates_found=len(selections),
        )

    return selections


def lookup_historical_returns(
    group_id: str,
    lookback_days: int,
    end_date: date | None = None,
) -> list[Decimal]:
    """Look up pre-computed historical portfolio daily returns from S3.

    Reads from S3 Parquet files and extracts the ``portfolio_daily_return``
    column for accurate metric computation (moving-average, stdev, etc.).

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
    store = get_group_history_store()
    if store is None:
        logger.debug("Group history store not available for return lookup")
        return []

    if end_date is None:
        end_date = datetime.now(UTC).date()

    start_date = end_date - timedelta(days=lookback_days)

    # Read group data from S3
    df = store.read_group_data(group_id)
    if df is None or df.empty:
        logger.warning(
            "Historical returns lookup returned ZERO records -- group "
            "cache is empty or unpopulated for the requested window",
            group_id=group_id,
            lookback_days=lookback_days,
            returns_found=0,
        )
        return []

    # Filter by date range
    df["record_date"] = pd.to_datetime(df["record_date"])
    mask = (df["record_date"].dt.date >= start_date) & (df["record_date"].dt.date <= end_date)
    df_filtered = df[mask]

    # Sort by date (oldest first)
    df_filtered = df_filtered.sort_values("record_date")

    # Extract returns
    returns: list[Decimal] = []
    for _, row in df_filtered.iterrows():
        raw_return = row.get("portfolio_daily_return")
        if raw_return is not None:
            try:
                returns.append(Decimal(str(raw_return)))
            except (InvalidOperation, ValueError):
                logger.warning(
                    "Invalid portfolio_daily_return value",
                    group_id=group_id,
                    record_date=row.get("record_date"),
                    raw_value=str(raw_return),
                )

    if len(returns) == 0:
        logger.warning(
            "Historical returns lookup returned ZERO records after filtering",
            group_id=group_id,
            lookback_days=lookback_days,
            returns_found=0,
        )
    else:
        logger.debug(
            "Historical returns lookup successful",
            group_id=group_id,
            lookback_days=lookback_days,
            returns_found=len(returns),
        )

    return returns


def is_cache_available() -> bool:
    """Check if the group history cache is configured and available."""
    return get_group_history_store() is not None


def write_historical_return(
    group_id: str,
    record_date: str,
    selections: dict[str, str],
    portfolio_daily_return: Decimal,
    *,
    ttl_days: int = 30,
) -> bool:
    """Write a single historical return entry to the group cache in S3.

    Used by on-demand backfill when the strategy worker detects a cache miss
    during portfolio scoring and re-evaluates the group for historical dates.

    Args:
        group_id: Group identifier (hash-based, e.g. "max_dd_tqqq_vs_uvxy_a1b2c3d4e5f6")
        record_date: ISO date string (YYYY-MM-DD)
        selections: Symbol-to-weight mapping (weights as strings)
        portfolio_daily_return: Daily return as Decimal (e.g. Decimal("0.0153"))
        ttl_days: Deprecated (unused for S3 storage, kept for API compatibility)

    Returns:
        True if write succeeded, False otherwise.

    """
    store = get_group_history_store()
    if store is None:
        logger.warning("Cannot write to group cache: store not available")
        return False

    try:
        # Create a single-row DataFrame with the new record
        import json

        new_record = pd.DataFrame(
            [
                {
                    "record_date": record_date,
                    "selections": json.dumps(selections),
                    "selection_count": len(selections),
                    "portfolio_daily_return": str(portfolio_daily_return),
                    "evaluated_at": datetime.now(UTC).isoformat(),
                    "source": "on_demand_backfill_script",
                }
            ]
        )

        # Append to existing data
        success = store.append_records(group_id, new_record)

        if success:
            logger.debug(
                "Wrote historical return to cache",
                group_id=group_id,
                record_date=record_date,
                portfolio_daily_return=str(portfolio_daily_return),
            )

        return success

    except Exception as e:
        logger.warning(
            "Unexpected error writing historical return to cache",
            group_id=group_id,
            record_date=record_date,
            error=str(e),
        )
        return False
