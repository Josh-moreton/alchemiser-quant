#!/usr/bin/env python3
"""Business Unit: pnl_capture | Status: current.

Lambda handler for daily P&L capture to Notion.

This Lambda runs on a daily schedule to capture P&L data from Alpaca and push
it to a Notion database for visualization. Uses intelligent deposit matching
to correctly adjust P&L for cashflows.

Trigger: EventBridge schedule (daily, after market close).
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, NamedTuple

import requests

from the_alchemiser.shared.config.secrets_adapter import get_alpaca_keys
from the_alchemiser.shared.logging import configure_application_logging, get_logger

# Initialize logging on cold start
configure_application_logging()

logger = get_logger(__name__)


class DailyRecord(NamedTuple):
    """Single day's P&L data."""

    date: str
    equity: Decimal
    raw_pnl: Decimal
    deposit: Decimal
    withdrawal: Decimal
    adjusted_pnl: Decimal


def fetch_portfolio_history_with_cashflow(
    api_key: str, secret_key: str, period: str = "1M"
) -> dict[str, Any]:
    """Fetch portfolio history WITH cashflow data in a single API call.

    Uses the cashflow_types parameter to get deposits (CSD) and withdrawals (CSW)
    aligned with the timestamp array.

    Args:
        api_key: Alpaca API key
        secret_key: Alpaca secret key
        period: Period string (default: 1M for Lambda daily runs)

    Returns:
        Dictionary with timestamp, equity, profit_loss, cashflow.

    """
    url = "https://api.alpaca.markets/v2/account/portfolio/history"
    headers = {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": secret_key,
        "accept": "application/json",
    }
    params = {
        "period": period,
        "timeframe": "1D",
        "intraday_reporting": "market_hours",
        "pnl_reset": "per_day",
        "cashflow_types": "CSD,CSW",
    }

    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    result: dict[str, Any] = resp.json()
    return result


def format_ts(ts: int) -> str:
    """Convert Unix timestamp to YYYY-MM-DD."""
    return datetime.fromtimestamp(ts, tz=UTC).strftime("%Y-%m-%d")


def build_daily_records(data: dict[str, Any]) -> list[DailyRecord]:
    """Build daily records with deposit-adjusted P&L from unified API response.

    Uses intelligent matching: for each deposit, scan that day and prior days
    to find the inflated P&L (within 15% of deposit amount) and subtract it.

    Args:
        data: Alpaca portfolio history response with cashflow

    Returns:
        List of DailyRecord objects.

    """
    timestamps = data.get("timestamp", [])
    equities = data.get("equity", [])
    profit_losses = data.get("profit_loss", [])
    cashflow = data.get("cashflow", {})

    csd_values = cashflow.get("CSD", [0] * len(timestamps))
    csw_values = cashflow.get("CSW", [0] * len(timestamps))

    while len(csd_values) < len(timestamps):
        csd_values.append(0)
    while len(csw_values) < len(timestamps):
        csw_values.append(0)

    # Build deposits by index
    deposits_by_index: dict[int, Decimal] = {}
    for i in range(len(timestamps)):
        if csd_values[i] != 0:
            deposits_by_index[i] = Decimal(str(csd_values[i]))

    raw_pnl_values = [Decimal(str(pl)) for pl in profit_losses]

    # Match deposits to inflated P&L days (15% tolerance, 3-day lookback)
    deposit_adjustments: dict[int, Decimal] = {}
    lookback_days = 3
    tolerance = 0.15

    for deposit_idx, deposit_amount in deposits_by_index.items():
        best_match_idx = None
        best_match_diff = float("inf")

        for offset in range(lookback_days + 1):
            check_idx = deposit_idx - offset
            if check_idx < 0:
                break

            raw_pnl = raw_pnl_values[check_idx]
            diff = abs(float(raw_pnl) - float(deposit_amount))
            relative_diff = diff / float(deposit_amount) if deposit_amount != 0 else float("inf")

            if relative_diff <= tolerance and diff < best_match_diff:
                best_match_idx = check_idx
                best_match_diff = diff

        if best_match_idx is not None:
            if best_match_idx in deposit_adjustments:
                deposit_adjustments[best_match_idx] += deposit_amount
            else:
                deposit_adjustments[best_match_idx] = deposit_amount

    # Build records
    records = []
    for i, ts in enumerate(timestamps):
        date_str = format_ts(ts)
        equity = Decimal(str(equities[i]))
        raw_pnl = raw_pnl_values[i]
        withdrawal_today = abs(Decimal(str(csw_values[i]))) if csw_values[i] else Decimal("0")
        deposit_on_this_day = Decimal(str(csd_values[i])) if csd_values[i] != 0 else Decimal("0")

        adjustment = deposit_adjustments.get(i, Decimal("0"))
        adjusted_pnl = raw_pnl - adjustment

        records.append(
            DailyRecord(
                date=date_str,
                equity=equity,
                raw_pnl=raw_pnl,
                deposit=deposit_on_this_day,
                withdrawal=withdrawal_today,
                adjusted_pnl=adjusted_pnl,
            )
        )

    return records


def push_to_notion(
    records: list[DailyRecord], database_id: str, notion_token: str
) -> dict[str, int]:
    """Push daily P&L records to a Notion database.

    Creates pages for new dates only (append-only). Auto-creates required
    properties if they don't exist.

    Args:
        records: List of DailyRecord objects
        database_id: Notion database ID
        notion_token: Notion integration token

    Returns:
        Dict with 'created', 'skipped', 'errors' counts.

    """
    headers = {
        "Authorization": f"Bearer {notion_token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28",
    }
    base_url = "https://api.notion.com/v1"

    # Required properties
    required_props = {
        "Date": {"date": {}},
        "Equity": {"number": {"format": "dollar"}},
        "P&L ($)": {"number": {"format": "dollar"}},
        "P&L (%)": {"number": {"format": "percent"}},
        "Raw P&L": {"number": {"format": "dollar"}},
        "Deposits": {"number": {"format": "dollar"}},
    }

    # Ensure schema exists
    try:
        resp = requests.get(f"{base_url}/databases/{database_id}", headers=headers, timeout=30)
        resp.raise_for_status()
        db_info = resp.json()
        existing_props = set(db_info.get("properties", {}).keys())
        missing_props = {k: v for k, v in required_props.items() if k not in existing_props}

        if missing_props:
            logger.info(f"Adding missing Notion properties: {list(missing_props.keys())}")
            requests.patch(
                f"{base_url}/databases/{database_id}",
                headers=headers,
                json={"properties": missing_props},
                timeout=30,
            ).raise_for_status()
    except Exception as e:
        logger.warning(f"Could not update database schema: {e}")

    # Get existing dates
    existing_dates: set[str] = set()
    try:
        has_more = True
        start_cursor = None
        while has_more:
            query_body: dict[str, Any] = {}
            if start_cursor:
                query_body["start_cursor"] = start_cursor

            resp = requests.post(
                f"{base_url}/databases/{database_id}/query",
                headers=headers,
                json=query_body,
                timeout=30,
            )
            resp.raise_for_status()
            results = resp.json()

            for page in results.get("results", []):
                props = page.get("properties", {})
                date_prop = props.get("Date", {})
                if date_prop.get("date") and date_prop["date"].get("start"):
                    existing_dates.add(date_prop["date"]["start"])

            has_more = results.get("has_more", False)
            start_cursor = results.get("next_cursor")
    except Exception as e:
        logger.warning(f"Could not query existing pages: {e}")

    logger.info(f"Found {len(existing_dates)} existing records in Notion")

    # Filter to active days only
    active_records = [r for r in records if r.equity > 0]

    created = 0
    skipped = 0
    errors = 0

    for rec in active_records:
        if rec.date in existing_dates:
            skipped += 1
            continue

        start_equity = rec.equity - rec.adjusted_pnl
        pnl_pct = float(rec.adjusted_pnl / start_equity * 100) if start_equity != 0 else 0.0

        try:
            page_data = {
                "parent": {"database_id": database_id},
                "properties": {
                    "Date": {"date": {"start": rec.date}},
                    "Equity": {"number": float(rec.equity)},
                    "P&L ($)": {"number": float(rec.adjusted_pnl)},
                    "P&L (%)": {"number": round(pnl_pct / 100, 4)},
                    "Raw P&L": {"number": float(rec.raw_pnl)},
                    "Deposits": {"number": float(rec.deposit)},
                },
            }
            resp = requests.post(
                f"{base_url}/pages",
                headers=headers,
                json=page_data,
                timeout=30,
            )
            resp.raise_for_status()
            created += 1
        except Exception as e:
            errors += 1
            if errors <= 3:
                logger.error(f"Error creating page for {rec.date}: {e}")

    return {"created": created, "skipped": skipped, "errors": errors}


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Capture daily P&L and push to Notion.

    This handler:
    1. Fetches portfolio history with cashflows from Alpaca (single API call)
    2. Builds daily records with intelligent deposit matching
    3. Pushes new records to Notion database (append-only)

    Args:
        event: Lambda event (may contain 'period' override, default 1M)
        context: Lambda context

    Returns:
        Response with sync status and metrics.

    """
    # Get configuration from environment
    notion_token = os.environ.get("NOTION_TOKEN", "")
    database_id = os.environ.get("NOTION_DATABASE_ID", "")
    period = event.get("period", "1M")

    if not notion_token or not database_id:
        logger.error("NOTION_TOKEN or NOTION_DATABASE_ID not configured")
        return {
            "statusCode": 500,
            "body": {"status": "error", "message": "Notion credentials not configured"},
        }

    try:
        # Get Alpaca credentials
        api_key, secret_key, _ = get_alpaca_keys()
        if not api_key or not secret_key:
            logger.error("ALPACA credentials not configured")
            return {
                "statusCode": 500,
                "body": {"status": "error", "message": "Alpaca credentials not configured"},
            }

        # Fetch data from Alpaca
        logger.info(f"Fetching portfolio history with cashflows (period={period})")
        data = fetch_portfolio_history_with_cashflow(api_key, secret_key, period=period)

        timestamps = data.get("timestamp", [])
        cashflow = data.get("cashflow", {})
        deposit_count = sum(1 for v in cashflow.get("CSD", []) if v != 0)

        logger.info(f"Retrieved {len(timestamps)} trading days, {deposit_count} deposits")

        # Build records with deposit matching
        records = build_daily_records(data)

        # Push to Notion
        result = push_to_notion(records, database_id, notion_token)

        logger.info(
            f"Notion sync complete: {result['created']} created, "
            f"{result['skipped']} skipped, {result['errors']} errors"
        )

        return {
            "statusCode": 200,
            "body": {
                "status": "success",
                "trading_days": len(timestamps),
                "deposits_found": deposit_count,
                "notion_created": result["created"],
                "notion_skipped": result["skipped"],
                "notion_errors": result["errors"],
            },
        }

    except Exception as e:
        logger.error(f"Failed to sync P&L to Notion: {e}", extra={"error_type": type(e).__name__})
        return {
            "statusCode": 500,
            "body": {"status": "error", "message": str(e)},
        }
