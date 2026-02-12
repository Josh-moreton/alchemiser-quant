"""Business Unit: account_data | Status: current.

Lambda handler for the Account Data service.

Runs on a 6-hourly EventBridge schedule (4 AM, 10 AM, 4 PM, 10 PM ET) to
fetch account information, positions, and deposit-adjusted PnL history from
Alpaca, then persist everything to a single-table DynamoDB design.

The Streamlit dashboard reads from this table instead of calling Alpaca directly,
eliminating all broker API calls from the frontend.

Three data collection phases:
    1. Account snapshot   -> ACCOUNT#<id> / SNAPSHOT#<ts>
    2. Positions snapshot  -> POSITIONS#<id> / SNAPSHOT#<ts>
    3. PnL history (1 yr)  -> PNL#<id> / DATE#<YYYY-MM-DD>
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

import boto3
from dynamodb_writer import (
    update_latest_pointer,
    write_account_registry,
    write_account_snapshot,
    write_pnl_records,
    write_positions_snapshot,
)

from the_alchemiser.shared.brokers.alpaca_manager import (
    AlpacaManager,
    create_alpaca_manager,
)
from the_alchemiser.shared.config.secrets_adapter import get_alpaca_keys
from the_alchemiser.shared.errors.exceptions import ConfigurationError
from the_alchemiser.shared.logging import configure_application_logging, get_logger
from the_alchemiser.shared.services.pnl_service import PnLService

# Initialise logging on cold start (must be before get_logger)
configure_application_logging()

logger = get_logger(__name__)

# Environment variables
ACCOUNT_DATA_TABLE = os.environ.get("ACCOUNT_DATA_TABLE", "")

# DynamoDB resource (re-used across invocations)
dynamodb = boto3.resource("dynamodb")


def handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Lambda entry point for the account data collection service.

    Args:
        event: Lambda event (from EventBridge Scheduler or manual invocation).
        context: Lambda context object.

    Returns:
        Response dict with status, phases completed, and any errors.

    """
    correlation_id = event.get(
        "correlation_id",
        f"account-data-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}",
    )
    timestamp = datetime.now(UTC).isoformat()

    logger.info(
        "Account data Lambda invoked",
        extra={
            "correlation_id": correlation_id,
            "source": event.get("source", "manual"),
        },
    )

    if not ACCOUNT_DATA_TABLE:
        error_msg = "ACCOUNT_DATA_TABLE environment variable not set"
        logger.error(error_msg)
        return {"statusCode": 500, "body": {"status": "error", "error": error_msg}}

    table = dynamodb.Table(ACCOUNT_DATA_TABLE)

    # Build Alpaca clients
    try:
        alpaca_manager, account_service = _create_alpaca_clients()
    except ConfigurationError as exc:
        logger.error(
            "Alpaca configuration error",
            extra={"correlation_id": correlation_id, "error": str(exc)},
        )
        return {"statusCode": 500, "body": {"status": "error", "error": str(exc)}}

    phases: dict[str, str] = {}
    account_id = ""

    # ------------------------------------------------------------------
    # Phase 1: Account Snapshot
    # ------------------------------------------------------------------
    try:
        account_dict = account_service.get_account_dict()
        if account_dict:
            account_id = str(account_dict.get("id", "unknown"))
            write_account_snapshot(table, account_id, account_dict, timestamp)
            update_latest_pointer(table, account_id, "ACCOUNT", timestamp)
            write_account_registry(table, account_id, timestamp)
            phases["account_snapshot"] = "success"
            logger.info(
                "Phase 1 complete: account snapshot",
                extra={"correlation_id": correlation_id, "account_id": account_id},
            )
        else:
            phases["account_snapshot"] = "skipped_no_data"
            logger.warning(
                "Phase 1 skipped: no account data returned",
                extra={"correlation_id": correlation_id},
            )
    except Exception as exc:
        phases["account_snapshot"] = f"error: {exc}"
        logger.error(
            "Phase 1 failed: account snapshot",
            extra={"correlation_id": correlation_id, "error": str(exc)},
            exc_info=True,
        )

    # ------------------------------------------------------------------
    # Phase 2: Positions Snapshot
    # ------------------------------------------------------------------
    try:
        positions = account_service.get_positions()
        if account_id:
            position_dicts = _serialise_positions(positions)
            write_positions_snapshot(table, account_id, position_dicts, timestamp)
            update_latest_pointer(table, account_id, "POSITIONS", timestamp)
            phases["positions_snapshot"] = "success"
            logger.info(
                "Phase 2 complete: positions snapshot",
                extra={
                    "correlation_id": correlation_id,
                    "position_count": len(position_dicts),
                },
            )
        else:
            phases["positions_snapshot"] = "skipped_no_account_id"
    except Exception as exc:
        phases["positions_snapshot"] = f"error: {exc}"
        logger.error(
            "Phase 2 failed: positions snapshot",
            extra={"correlation_id": correlation_id, "error": str(exc)},
            exc_info=True,
        )

    # ------------------------------------------------------------------
    # Phase 3: PnL History (Full 1-Year Refresh)
    # ------------------------------------------------------------------
    try:
        if account_id:
            pnl_service = PnLService(
                alpaca_manager=alpaca_manager,
                correlation_id=correlation_id,
            )
            daily_records, deposits_by_date = pnl_service.get_all_daily_records(period="1A")

            # Filter out inactive days (equity == 0)
            active_records = [r for r in daily_records if r.equity > 0]

            write_pnl_records(table, account_id, active_records)
            phases["pnl_history"] = "success"
            logger.info(
                "Phase 3 complete: PnL history",
                extra={
                    "correlation_id": correlation_id,
                    "total_records": len(daily_records),
                    "active_records": len(active_records),
                    "deposits_found": len(deposits_by_date),
                },
            )
        else:
            phases["pnl_history"] = "skipped_no_account_id"
    except Exception as exc:
        phases["pnl_history"] = f"error: {exc}"
        logger.error(
            "Phase 3 failed: PnL history",
            extra={"correlation_id": correlation_id, "error": str(exc)},
            exc_info=True,
        )

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    all_success = all(v == "success" for v in phases.values())
    status = "success" if all_success else "partial_failure"
    status_code = 200 if all_success else 207

    logger.info(
        "Account data Lambda completed",
        extra={
            "correlation_id": correlation_id,
            "status": status,
            "phases": phases,
            "account_id": account_id,
        },
    )

    return {
        "statusCode": status_code,
        "body": {
            "status": status,
            "account_id": account_id,
            "timestamp": timestamp,
            "phases": phases,
        },
    }


# ======================================================================
# Private helpers
# ======================================================================


def _create_alpaca_clients() -> tuple[AlpacaManager, Any]:
    """Create Alpaca manager and account service from environment config.

    Returns:
        Tuple of (AlpacaManager, AlpacaAccountService).

    Raises:
        ConfigurationError: If API keys are missing.

    """
    from the_alchemiser.shared.services.alpaca_account_service import (
        AlpacaAccountService,
    )

    api_key, secret_key, endpoint = get_alpaca_keys()
    if not api_key or not secret_key:
        raise ConfigurationError(
            "Alpaca API keys not found in configuration",
            config_key="ALPACA__KEY/ALPACA__SECRET",
        )

    # Determine paper vs live
    paper = True
    if endpoint:
        ep_lower = endpoint.lower()
        if "api.alpaca.markets" in ep_lower and "paper" not in ep_lower:
            paper = False

    manager = create_alpaca_manager(api_key=api_key, secret_key=secret_key, paper=paper)

    # Create a TradingClient for the account service
    from alpaca.trading.client import TradingClient

    trading_client = TradingClient(api_key=api_key, secret_key=secret_key, paper=paper)
    account_service = AlpacaAccountService(trading_client)

    return manager, account_service


def _serialise_positions(positions: list[Any]) -> list[dict[str, Any]]:
    """Convert Alpaca Position SDK objects to plain dicts for storage.

    Args:
        positions: List of alpaca Position objects.

    Returns:
        List of dicts with string-typed financial values.

    """
    result: list[dict[str, Any]] = []
    for pos in positions:
        result.append(
            {
                "symbol": str(getattr(pos, "symbol", "")),
                "qty": str(getattr(pos, "qty", "0")),
                "avg_entry_price": str(getattr(pos, "avg_entry_price", "0")),
                "current_price": str(getattr(pos, "current_price", "0")),
                "market_value": str(getattr(pos, "market_value", "0")),
                "cost_basis": str(getattr(pos, "cost_basis", "0")),
                "unrealized_pl": str(getattr(pos, "unrealized_pl", "0")),
                "unrealized_plpc": str(getattr(pos, "unrealized_plpc", "0")),
                "side": str(getattr(pos, "side", "long")),
                "asset_class": str(getattr(pos, "asset_class", "us_equity")),
            }
        )
    return result
