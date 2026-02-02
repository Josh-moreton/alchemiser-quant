#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Detailed P&L report with deposit adjustments.

Pulls Alpaca portfolio history with cashflow data in a SINGLE API call,
then generates weekly and monthly P&L reports in dollars and percentages.

Optional Notion integration: Add --notion flag to push daily records to a Notion database.
Requires NOTION_TOKEN and NOTION_DATABASE_ID environment variables.
"""

from __future__ import annotations

import _setup_imports  # noqa: F401

import argparse
import os
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable, NamedTuple

import requests
from dotenv import load_dotenv

# Load .env file before importing modules that use os.getenv
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from the_alchemiser.shared.config.secrets_adapter import get_alpaca_keys


class DailyRecord(NamedTuple):
    """Single day's P&L data."""

    date: str
    equity: Decimal
    raw_pnl: Decimal
    deposit: Decimal  # Deposit that settled today (T+1)
    withdrawal: Decimal  # Withdrawal today
    adjusted_pnl: Decimal


def fetch_portfolio_history_with_cashflow(
    api_key: str, secret_key: str, period: str = "1A"
) -> dict[str, Any]:
    """Fetch portfolio history WITH cashflow data in a single API call.

    Uses the cashflow_types parameter to get deposits (CSD) and withdrawals (CSW)
    aligned with the timestamp array.

    Args:
        api_key: Alpaca API key
        secret_key: Alpaca secret key
        period: Period string (1W, 1M, 3M, 1A)

    Returns:
        Dictionary with timestamp, equity, profit_loss, profit_loss_pct, base_value, cashflow

    """
    url = "https://api.alpaca.markets/v2/account/portfolio/history"
    headers = {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": secret_key,
        "accept": "application/json",
    }
    params = {
        "period": period,
        "timeframe": "1D",  # Daily data points
        "intraday_reporting": "market_hours",
        "pnl_reset": "per_day",
        "cashflow_types": "CSD,CSW",  # Include deposits and withdrawals
    }

    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def format_ts(ts: int) -> str:
    """Convert Unix timestamp to YYYY-MM-DD."""
    return datetime.fromtimestamp(ts, tz=UTC).strftime("%Y-%m-%d")


def get_week_key(date_str: str) -> str:
    """Get ISO week key (YYYY-WNN)."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    year, week, _ = dt.isocalendar()
    return f"{year}-W{week:02d}"


def get_month_key(date_str: str) -> str:
    """Get month key (YYYY-MM)."""
    return date_str[:7]


def get_deposit_dates_for_settlement(
    prev_trading_day: str, today: str, all_trading_days: set[str]
) -> list[str]:
    """Get all calendar dates where deposits would settle on 'today'.

    Deposits settle T+1 (next trading day after they're made). So:
    - Deposit made on trading day P settles on the next trading day after P
    - Deposit made on non-trading day (weekend/holiday) settles on the next trading day

    For trading day D with previous trading day P:
    - Only include deposits made on days AFTER P (exclusive) and BEFORE D (exclusive)
    - These are non-trading days where deposits would settle on D
    - Do NOT include P itself - deposits on P settled on the trading day after P
      (which might be D, or might be an intermediate trading day)

    Returns dates from prev_trading_day (exclusive) to today (exclusive).
    """
    start = datetime.strptime(prev_trading_day, "%Y-%m-%d")
    end = datetime.strptime(today, "%Y-%m-%d")
    dates = []

    # Start from day AFTER prev_trading_day
    current = start + timedelta(days=1)
    while current < end:  # exclusive of today
        date_str = current.strftime("%Y-%m-%d")
        # Only include if it's NOT a trading day (deposits on trading days
        # settle on their own next trading day, not necessarily today)
        if date_str not in all_trading_days:
            dates.append(date_str)
        current += timedelta(days=1)

    # Also include prev_trading_day ONLY if it's immediately before today
    # (i.e., consecutive trading days, deposit on P settles on D)
    if (end - start).days == 1:
        # Consecutive calendar days means consecutive trading days
        dates.insert(0, prev_trading_day)
    elif not dates:
        # No non-trading days between them, so P's deposit settles on D
        dates.append(prev_trading_day)

    return dates


def build_daily_records(data: dict[str, Any]) -> tuple[list[DailyRecord], dict[str, Decimal]]:
    """Build daily records with deposit-adjusted P&L from unified API response.

    The cashflow arrays (CSD, CSW) are aligned 1:1 with timestamps.

    Key insight: Alpaca's equity includes deposits, but deposits settle T+1.
    A deposit made on day D appears in equity on the next trading day.

    To get true trading P&L:
    - Calculate equity change from previous trading day
    - Subtract deposits that settled today (made on prev trading day or weekend days before today)

    Returns:
        Tuple of (daily_records, deposits_by_date)

    """
    timestamps = data.get("timestamp", [])
    equities = data.get("equity", [])
    profit_losses = data.get("profit_loss", [])
    cashflow = data.get("cashflow", {})

    # Extract cashflow arrays (aligned with timestamps, default to zeros)
    csd_values = cashflow.get("CSD", [0] * len(timestamps))
    csw_values = cashflow.get("CSW", [0] * len(timestamps))

    # Pad arrays if shorter than timestamps
    while len(csd_values) < len(timestamps):
        csd_values.append(0)
    while len(csw_values) < len(timestamps):
        csw_values.append(0)

    # Build list of all trading dates and deposits_by_date
    all_dates = [format_ts(ts) for ts in timestamps]
    all_trading_days = set(all_dates)

    # Build deposits_by_date from cashflow array
    deposits_by_date: dict[str, Decimal] = {}
    for i, date_str in enumerate(all_dates):
        if csd_values[i] != 0:
            deposits_by_date[date_str] = Decimal(str(csd_values[i]))

    records = []

    for i, ts in enumerate(timestamps):
        date_str = format_ts(ts)
        equity = Decimal(str(equities[i]))
        raw_pnl = Decimal(str(profit_losses[i]))
        withdrawal_today = abs(Decimal(str(csw_values[i]))) if csw_values[i] else Decimal("0")

        # Get all calendar days where deposits would settle today
        deposit_settled_today = Decimal("0")
        if i > 0:
            prev_trading_day = all_dates[i - 1]
            # Deposits made between prev trading day and today settle today
            days_to_check = get_deposit_dates_for_settlement(
                prev_trading_day, date_str, all_trading_days
            )
            for d in days_to_check:
                if d in deposits_by_date:
                    deposit_settled_today += deposits_by_date[d]

            prev_equity = Decimal(str(equities[i - 1]))
            equity_change = equity - prev_equity
            # True trading P&L = equity change minus deposits that settled
            adjusted_pnl = equity_change - deposit_settled_today
        else:
            # First day - no previous data to compare
            adjusted_pnl = raw_pnl

        records.append(
            DailyRecord(
                date=date_str,
                equity=equity,
                raw_pnl=raw_pnl,
                deposit=deposit_settled_today,
                withdrawal=withdrawal_today,
                adjusted_pnl=adjusted_pnl,
            )
        )

    return records, deposits_by_date


def aggregate_periods(
    records: list[DailyRecord], key_func: Callable[[str], str]
) -> dict[str, dict]:
    """Aggregate records by period (week or month)."""
    periods: dict[str, dict] = {}

    for rec in records:
        key = key_func(rec.date)

        if key not in periods:
            periods[key] = {
                "start_equity": rec.equity - rec.adjusted_pnl,
                "end_equity": rec.equity,
                "total_pnl": Decimal("0"),
                "total_deposits": Decimal("0"),
                "days": 0,
                "first_date": rec.date,
                "last_date": rec.date,
            }

        periods[key]["total_pnl"] += rec.adjusted_pnl
        periods[key]["total_deposits"] += rec.deposit
        periods[key]["end_equity"] = rec.equity
        periods[key]["days"] += 1
        periods[key]["last_date"] = rec.date

    return periods


def print_section_header(title: str) -> None:
    """Print a formatted section header."""
    print()
    print("=" * 90)
    print(f"  {title}")
    print("=" * 90)


def print_daily_report(records: list[DailyRecord]) -> None:
    """Print detailed daily P&L report (only days with activity)."""
    # Filter to only show days with equity > 0
    active_records = [r for r in records if r.equity > 0]

    print_section_header("DAILY P&L REPORT")
    print()
    print(
        f"{'Date':<12} {'Equity':>14} {'Raw P&L':>12} {'Deposit':>12} "
        f"{'Adj P&L':>12} {'% Return':>10}"
    )
    print("-" * 90)

    for rec in active_records:
        # Calculate % based on previous day's equity (start of day equity)
        start_equity = rec.equity - rec.adjusted_pnl
        pct = (
            (rec.adjusted_pnl / start_equity * 100)
            if start_equity != 0
            else Decimal("0")
        )

        deposit_str = f"${rec.deposit:>+10,.2f}" if rec.deposit else " " * 12

        print(
            f"{rec.date:<12} ${rec.equity:>12,.2f} ${rec.raw_pnl:>+10,.2f} "
            f"{deposit_str} ${rec.adjusted_pnl:>+10,.2f} {pct:>+9.2f}%"
        )

    print("-" * 90)
    print(f"  (Showing {len(active_records)} active days, filtered {len(records) - len(active_records)} days with $0 equity)")


def print_period_report(periods: dict[str, dict], period_name: str) -> None:
    """Print aggregated period (weekly/monthly) report."""
    # Filter to only periods with activity
    active_periods = {k: v for k, v in periods.items() if v["end_equity"] > 0}

    print_section_header(f"{period_name.upper()} P&L REPORT")
    print()
    print(
        f"{'Period':<12} {'Start Eq':>14} {'End Eq':>14} {'P&L ($)':>14} "
        f"{'% Return':>10} {'Deposits':>12} {'Days':>6}"
    )
    print("-" * 90)

    total_pnl = Decimal("0")
    total_deposits = Decimal("0")

    for period_key in sorted(active_periods.keys()):
        data = active_periods[period_key]
        pnl = data["total_pnl"]
        start_eq = data["start_equity"]
        end_eq = data["end_equity"]
        deposits = data["total_deposits"]

        # Calculate % based on start equity of the period
        pct = (pnl / start_eq * 100) if start_eq != 0 else Decimal("0")

        deposit_str = f"${deposits:>+10,.2f}" if deposits else " " * 12

        print(
            f"{period_key:<12} ${start_eq:>12,.2f} ${end_eq:>12,.2f} ${pnl:>+12,.2f} "
            f"{pct:>+9.2f}% {deposit_str} {data['days']:>6}"
        )

        total_pnl += pnl
        total_deposits += deposits

    print("-" * 90)
    print(
        f"{'TOTAL':<12} {' ':>14} {' ':>14} ${total_pnl:>+12,.2f} "
        f"{' ':>10} ${total_deposits:>+10,.2f}"
    )


def print_summary(records: list[DailyRecord], deposits_by_date: dict[str, Decimal]) -> None:
    """Print overall summary statistics."""
    print_section_header("SUMMARY STATISTICS")

    # Filter to only active trading days (equity > 0)
    active_records = [r for r in records if r.equity > 0]

    if not active_records:
        print("No data available.")
        return

    total_pnl = sum(r.adjusted_pnl for r in active_records)
    total_deposits = sum(deposits_by_date.values())

    # Find first non-zero equity day for starting point
    first_active = active_records[0]
    end_equity = active_records[-1].equity

    # Total return based on first meaningful equity (after first deposit)
    # Use equity after first deposit as base
    first_deposit_equity = first_active.equity - first_active.adjusted_pnl
    total_pct = (
        (total_pnl / first_deposit_equity * 100)
        if first_deposit_equity > 0
        else Decimal("0")
    )

    # Stats only on active trading days
    positive_days = sum(1 for r in active_records if r.adjusted_pnl > 0)
    negative_days = sum(1 for r in active_records if r.adjusted_pnl < 0)
    flat_days = sum(1 for r in active_records if r.adjusted_pnl == 0)
    win_rate = (positive_days / len(active_records) * 100) if active_records else 0

    # Best/worst day excluding deposit-heavy days
    # Filter out days where deposit > abs(adjusted_pnl) to get true trading performance
    trading_days = [r for r in active_records if abs(r.deposit) < abs(r.adjusted_pnl) or r.deposit == 0]
    if trading_days:
        best_day = max(trading_days, key=lambda r: r.adjusted_pnl)
        worst_day = min(trading_days, key=lambda r: r.adjusted_pnl)
    else:
        best_day = max(active_records, key=lambda r: r.adjusted_pnl)
        worst_day = min(active_records, key=lambda r: r.adjusted_pnl)

    avg_daily_pnl = total_pnl / len(active_records) if active_records else Decimal("0")

    print()
    print(f"  Period:              {active_records[0].date} to {active_records[-1].date}")
    print(f"  Active Trading Days: {len(active_records)}")
    print()
    print(f"  Initial Deposit:     ${first_deposit_equity:>14,.2f}")
    print(f"  Ending Equity:       ${end_equity:>14,.2f}")
    print(f"  Total Deposits:      ${total_deposits:>+14,.2f}")
    print()
    print(f"  Trading P&L:         ${total_pnl:>+14,.2f}")
    print(f"  Return on Deposits:  {total_pct:>+14.2f}%")
    print()
    print(f"  Avg Daily P&L:       ${avg_daily_pnl:>+14,.2f}")
    print(f"  Best Trading Day:    {best_day.date}  ${best_day.adjusted_pnl:>+12,.2f}")
    print(f"  Worst Trading Day:   {worst_day.date}  ${worst_day.adjusted_pnl:>+12,.2f}")
    print()
    print(f"  Positive Days:       {positive_days:>6} ({win_rate:.1f}%)")
    print(f"  Negative Days:       {negative_days:>6}")
    print(f"  Flat Days:           {flat_days:>6}")
    print()


def push_to_notion(records: list[DailyRecord], database_id: str, notion_token: str) -> None:
    """Push daily P&L records to a Notion database.

    Creates or updates pages in the Notion database. Uses date as the unique
    identifier to prevent duplicates on re-runs.

    Expected Notion database properties:
    - Date (date): The trading date
    - Equity (number): End-of-day equity
    - P&L ($) (number): Adjusted P&L in dollars
    - P&L (%) (number): P&L as percentage
    - Raw P&L (number): Raw P&L from Alpaca (before deposit adjustment)
    - Deposits (number): Deposits that settled on this day

    Args:
        records: List of DailyRecord objects
        database_id: Notion database ID
        notion_token: Notion integration token

    """
    try:
        from notion_client import Client
    except ImportError:
        print("ERROR: notion-client package not installed. Run: poetry add notion-client")
        return

    print_section_header("NOTION EXPORT")

    notion = Client(auth=notion_token)

    # Filter to only active days (equity > 0)
    active_records = [r for r in records if r.equity > 0]
    print(f"  Pushing {len(active_records)} daily records to Notion...")

    # First, query existing pages to find duplicates by date
    existing_dates: set[str] = set()
    try:
        # Query all pages in the database
        results = notion.databases.query(database_id=database_id)
        for page in results.get("results", []):
            props = page.get("properties", {})
            date_prop = props.get("Date", {})
            if date_prop.get("date") and date_prop["date"].get("start"):
                existing_dates.add(date_prop["date"]["start"])
    except Exception as e:
        print(f"  Warning: Could not query existing pages: {e}")

    created = 0
    skipped = 0

    for rec in active_records:
        if rec.date in existing_dates:
            skipped += 1
            continue

        # Calculate P&L percentage
        start_equity = rec.equity - rec.adjusted_pnl
        pnl_pct = float(rec.adjusted_pnl / start_equity * 100) if start_equity != 0 else 0.0

        try:
            notion.pages.create(
                parent={"database_id": database_id},
                properties={
                    "Date": {"date": {"start": rec.date}},
                    "Equity": {"number": float(rec.equity)},
                    "P&L ($)": {"number": float(rec.adjusted_pnl)},
                    "P&L (%)": {"number": round(pnl_pct, 4)},
                    "Raw P&L": {"number": float(rec.raw_pnl)},
                    "Deposits": {"number": float(rec.deposit)},
                },
            )
            created += 1
        except Exception as e:
            print(f"  Error creating page for {rec.date}: {e}")

    print(f"  Created: {created} records")
    print(f"  Skipped (existing): {skipped} records")
    print()


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Alpaca P&L Report with deposit adjustments")
    parser.add_argument(
        "--notion",
        action="store_true",
        help="Push daily records to Notion database (requires NOTION_TOKEN and NOTION_DATABASE_ID)",
    )
    parser.add_argument(
        "--period",
        default="1A",
        choices=["1W", "1M", "3M", "1A"],
        help="Period to fetch (default: 1A = 1 year)",
    )
    args = parser.parse_args()

    print()
    print("=" * 90)
    print("  ALPACA P&L REPORT - Deposit Adjusted (Single API Call)")
    print("=" * 90)
    print()
    print("Loading credentials from .env...")

    api_key, secret_key, _ = get_alpaca_keys()
    if not api_key or not secret_key:
        print("ERROR: Missing ALPACA_KEY or ALPACA_SECRET in .env file")
        return

    print(f"Fetching portfolio history with cashflow ({args.period} period)...")
    data = fetch_portfolio_history_with_cashflow(api_key, secret_key, period=args.period)

    timestamps = data.get("timestamp", [])
    cashflow = data.get("cashflow", {})
    csd_values = cashflow.get("CSD", [])
    csw_values = cashflow.get("CSW", [])

    print(f"  Found {len(timestamps)} trading days")
    print(f"  Cashflow types in response: {list(cashflow.keys())}")

    # Count days with deposits/withdrawals
    deposit_days = sum(1 for v in csd_values if v != 0)
    withdrawal_days = sum(1 for v in csw_values if v != 0)
    total_deposits = sum(Decimal(str(v)) for v in csd_values if v != 0)
    total_withdrawals = sum(Decimal(str(abs(v))) for v in csw_values if v != 0)

    print(f"  Days with deposits (CSD): {deposit_days}, total: ${total_deposits:,.2f}")
    print(f"  Days with withdrawals (CSW): {withdrawal_days}, total: ${total_withdrawals:,.2f}")

    print("Building daily records with deposit adjustments...")
    records, deposits_by_date = build_daily_records(data)

    # Generate reports
    print_daily_report(records)

    weekly_data = aggregate_periods(records, get_week_key)
    print_period_report(weekly_data, "Weekly")

    monthly_data = aggregate_periods(records, get_month_key)
    print_period_report(monthly_data, "Monthly")

    print_summary(records, deposits_by_date)

    # Notion export if requested
    if args.notion:
        notion_token = os.environ.get("NOTION_TOKEN")
        database_id = os.environ.get("NOTION_DATABASE_ID")

        if not notion_token or not database_id:
            print("ERROR: --notion flag requires NOTION_TOKEN and NOTION_DATABASE_ID in .env")
            return

        push_to_notion(records, database_id, notion_token)


if __name__ == "__main__":
    main()
