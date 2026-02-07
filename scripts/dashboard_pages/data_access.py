"""Business Unit: scripts | Status: current.

Dashboard data access layer.

Provides a thin wrapper around AccountDataReader that handles boto3 Table
construction using DashboardSettings credentials. All dashboard pages import
from here instead of calling Alpaca directly.
"""

from __future__ import annotations

from typing import Any

import _setup_imports  # noqa: F401  -- side-effect: configures sys.path for the_alchemiser imports
import boto3
from dashboard_settings import get_dashboard_settings

from the_alchemiser.shared.services.account_data_reader import AccountDataReader


def _get_account_data_table() -> Any:  # noqa: ANN401
    """Get a boto3 DynamoDB Table resource for the account data table.

    Returns:
        boto3 DynamoDB Table resource.

    """
    settings = get_dashboard_settings()
    kwargs = settings.get_boto3_client_kwargs()
    dynamodb = boto3.resource("dynamodb", **kwargs)
    return dynamodb.Table(settings.account_data_table)


def _get_account_id() -> str:
    """Get the configured Alpaca account ID.

    Returns:
        Account ID string, or an empty string if no account ID is configured.

    """
    settings = get_dashboard_settings()
    if settings.account_id:
        return settings.account_id
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
    return AccountDataReader.get_latest_account_snapshot(table, account_id)


def get_latest_positions() -> list[Any]:
    """Get the latest positions snapshot from DynamoDB.

    Returns:
        List of PositionSnapshot DTOs.

    """
    table = _get_account_data_table()
    account_id = _get_account_id()
    if not account_id:
        return []
    return AccountDataReader.get_latest_positions(table, account_id)


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
    return AccountDataReader.get_pnl_history(table, account_id, start_date, end_date)


def get_all_pnl_records() -> list[Any]:
    """Get all daily PnL records from DynamoDB.

    Returns:
        Chronologically sorted list of DailyPnLEntry DTOs.

    """
    table = _get_account_data_table()
    account_id = _get_account_id()
    if not account_id:
        return []
    return AccountDataReader.get_all_pnl_records(table, account_id)


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
