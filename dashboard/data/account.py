"""Business Unit: dashboard | Status: current.

Dashboard account data access layer.

Provides a thin wrapper around AccountDataReader that handles boto3 Table
construction using DashboardSettings credentials. All dashboard pages import
from here instead of calling Alpaca directly.
"""

from __future__ import annotations

import logging
from typing import Any

import _setup_imports  # noqa: F401  -- side-effect: configures sys.path for the_alchemiser imports
import boto3
from settings import get_dashboard_settings

from the_alchemiser.shared.services.account_data_reader import AccountDataReader

logger = logging.getLogger(__name__)


def reset_account_cache() -> None:
    """Clear the cached account ID.

    Call when the user switches environment so the next lookup
    re-discovers the account ID from the new DynamoDB table.
    """
    global _cached_account_id
    _cached_account_id = None


def _get_account_data_table() -> Any:  # noqa: ANN401
    """Get a boto3 DynamoDB Table resource for the account data table.

    Returns:
        boto3 DynamoDB Table resource.

    """
    settings = get_dashboard_settings()
    kwargs = settings.get_boto3_client_kwargs()
    table_name = settings.account_data_table
    logger.info("Using account data table: %s (stage=%s)", table_name, settings.stage)
    dynamodb = boto3.resource("dynamodb", **kwargs)
    return dynamodb.Table(table_name)


def _discover_account_id(table: Any) -> str:  # noqa: ANN401
    """Discover the account ID by scanning for LATEST# partition keys.

    The account_data Lambda writes ``LATEST#{account_id}`` pointers.
    We query for one of these to extract the account ID dynamically,
    so no static ``ALPACA_ACCOUNT_ID`` environment variable is needed.

    Args:
        table: boto3 DynamoDB Table resource for the account-data table.

    Returns:
        Account ID string, or empty string if no data exists.

    """
    from boto3.dynamodb.conditions import Key

    try:
        # Scan is expensive but we only need 1 item and the table is small.
        # We look for LATEST# prefix which always exists if data was written.
        response = table.scan(
            FilterExpression=Key("PK").begins_with("LATEST#"),
            ProjectionExpression="PK",
            Limit=10,
        )
        items = response.get("Items", [])
        for item in items:
            pk: str = item.get("PK", "")
            if pk.startswith("LATEST#"):
                discovered = pk.removeprefix("LATEST#")
                logger.info("Auto-discovered account_id=%s from DynamoDB", discovered)
                return discovered
    except Exception:
        logger.warning("Failed to auto-discover account ID from DynamoDB", exc_info=True)

    return ""


# Module-level cache so we discover at most once per settings reload
_cached_account_id: str | None = None


def _get_account_id() -> str:
    """Get the Alpaca account ID.

    Resolution order:
        1. Explicit ``ALPACA_ACCOUNT_ID`` from secrets / env (if set).
        2. Auto-discovered from the DynamoDB account-data table.

    The discovered value is cached for the lifetime of the current
    settings singleton (cleared when the user switches environment).

    Returns:
        Account ID string, or an empty string if none can be resolved.

    """
    global _cached_account_id

    settings = get_dashboard_settings()
    if settings.account_id:
        return settings.account_id

    # Return cached discovery result if available
    if _cached_account_id is not None:
        return _cached_account_id

    # Attempt auto-discovery from DynamoDB
    try:
        table = _get_account_data_table()
        _cached_account_id = _discover_account_id(table)
    except Exception:
        logger.warning("Could not connect to DynamoDB for account ID discovery", exc_info=True)
        _cached_account_id = ""

    if not _cached_account_id:
        logger.warning("No account data found in %s", settings.account_data_table)

    return _cached_account_id


def get_latest_account_data() -> dict[str, Any] | None:
    """Get the latest account snapshot from DynamoDB.

    Returns:
        Account dict matching AlpacaAccountService.get_account_dict() shape,
        or None if no data available.

    """
    table = _get_account_data_table()
    account_id = _get_account_id()
    if not account_id:
        return None
    result = AccountDataReader.get_latest_account_snapshot(table, account_id)
    if result is None:
        logger.warning("No account snapshot found for account_id=%s", account_id)
    return result


def get_latest_positions() -> list[Any]:
    """Get the latest positions snapshot from DynamoDB.

    Returns:
        List of PositionSnapshot DTOs.

    """
    table = _get_account_data_table()
    account_id = _get_account_id()
    if not account_id:
        return []
    positions = AccountDataReader.get_latest_positions(table, account_id)
    logger.info("Loaded %d positions for account_id=%s", len(positions), account_id)
    return positions


def get_pnl_records(
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[Any]:
    """Get daily PnL records from DynamoDB.

    Args:
        start_date: Optional start date filter (YYYY-MM-DD).
        end_date: Optional end date filter (YYYY-MM-DD).

    Returns:
        Chronologically sorted list of DailyPnLEntry DTOs.

    """
    table = _get_account_data_table()
    account_id = _get_account_id()
    if not account_id:
        return []
    records = AccountDataReader.get_pnl_history(table, account_id, start_date, end_date)
    logger.info(
        "Loaded %d PnL records for account_id=%s (range=%s..%s)",
        len(records),
        account_id,
        start_date,
        end_date,
    )
    return records


def get_all_pnl_records() -> list[Any]:
    """Get all daily PnL records from DynamoDB.

    Returns:
        Chronologically sorted list of DailyPnLEntry DTOs.

    """
    table = _get_account_data_table()
    account_id = _get_account_id()
    if not account_id:
        return []
    records = AccountDataReader.get_all_pnl_records(table, account_id)
    logger.info("Loaded %d total PnL records for account_id=%s", len(records), account_id)
    return records


def get_data_last_updated() -> str | None:
    """Get the timestamp of the most recent account data snapshot.

    Returns:
        ISO timestamp string or None.

    """
    table = _get_account_data_table()
    account_id = _get_account_id()
    if not account_id:
        return None
    return AccountDataReader.get_snapshot_timestamp(table, account_id)
