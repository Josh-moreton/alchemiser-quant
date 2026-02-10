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


def _get_account_id() -> str:
    """Get the configured Alpaca account ID.

    Returns:
        Account ID string, or an empty string if no account ID is configured.

    """
    settings = get_dashboard_settings()
    if settings.account_id:
        return settings.account_id
    logger.warning("ALPACA_ACCOUNT_ID not configured -- all account queries will return empty")
    return ""


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
