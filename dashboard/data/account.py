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


def _discover_account_id_via_dynamodb() -> str:
    """Discover the account ID from the DynamoDB registry entry.

    The account_data Lambda writes a well-known item at
    ``PK=REGISTRY``, ``SK=ACCOUNT_ID``.  This is the preferred
    discovery path because it requires only a single GetItem --
    no Scan and no external API call.

    Returns:
        Account ID string, or empty string if the registry entry
        does not exist or the table is unreachable.

    """
    try:
        table = _get_account_data_table()
        return AccountDataReader.discover_account_id(table)
    except Exception:
        logger.warning("Failed to discover account ID from DynamoDB registry", exc_info=True)
        return ""


def _discover_account_id_via_alpaca() -> str:
    """Discover the account ID by calling the Alpaca REST API.

    Uses ``ALPACA_KEY`` and ``ALPACA_SECRET`` from Streamlit secrets
    to query the broker ``/v2/account`` endpoint.  The endpoint is
    chosen based on the active stage (paper for dev/staging, live for
    prod).

    This avoids a ``dynamodb:Scan`` call which the dashboard-readonly
    IAM user is not authorised to perform.

    Returns:
        Account ID string, or empty string if credentials are missing
        or the API call fails.

    """
    import json
    import urllib.error
    import urllib.request

    from settings import _get_secret

    api_key = _get_secret("ALPACA_KEY", "")
    api_secret = _get_secret("ALPACA_SECRET", "")

    if not api_key or not api_secret:
        logger.warning(
            "ALPACA_KEY / ALPACA_SECRET not configured -- "
            "cannot auto-discover account ID via Alpaca API"
        )
        return ""

    settings = get_dashboard_settings()
    base_url = (
        "https://api.alpaca.markets"
        if settings.stage == "prod"
        else "https://paper-api.alpaca.markets"
    )

    url = f"{base_url}/v2/account"
    req = urllib.request.Request(url)  # noqa: S310 -- URL is hardcoded https
    req.add_header("APCA-API-KEY-ID", api_key)
    req.add_header("APCA-API-SECRET-KEY", api_secret)

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
            data = json.loads(resp.read().decode())
            account_id: str = data.get("id", "")
            if account_id:
                logger.info("Discovered account_id=%s via Alpaca API", account_id)
            return account_id
    except Exception:
        logger.warning("Failed to discover account ID via Alpaca API", exc_info=True)
        return ""


# Module-level cache so we discover at most once per settings reload
_cached_account_id: str | None = None


def _get_account_id() -> str:
    """Get the Alpaca account ID.

    Discovery chain (first non-empty wins):
        1. Streamlit secret / environment variable ``ACCOUNT_ID``
        2. DynamoDB registry entry (``PK=REGISTRY``, ``SK=ACCOUNT_ID``)
        3. Alpaca REST API ``/v2/account`` (legacy fallback)

    The result is cached for the process lifetime (cleared when the
    user switches environment via ``reset_account_cache``).

    Returns:
        Account ID string, or empty string if all discovery methods fail.

    """
    global _cached_account_id

    # Return cached discovery result if available
    if _cached_account_id is not None:
        return _cached_account_id

    # 1. Explicit secret / env var
    settings = get_dashboard_settings()
    if settings.account_id:
        logger.info("Using account_id from settings: %s", settings.account_id)
        _cached_account_id = settings.account_id
        return _cached_account_id

    # 2. DynamoDB registry (written by account_data Lambda)
    discovered = _discover_account_id_via_dynamodb()
    if discovered:
        _cached_account_id = discovered
        return _cached_account_id

    # 3. Legacy fallback -- Alpaca REST API
    discovered = _discover_account_id_via_alpaca()

    if discovered:
        _cached_account_id = discovered
        return _cached_account_id

    # Don't cache failure -- leave as None so next call retries discovery
    logger.warning("No account data found in %s", settings.account_data_table)
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
