#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Detailed P&L report with deposit adjustments.

Pulls Alpaca portfolio history and deposit activities, then generates
weekly and monthly P&L reports in dollars and percentages.
"""

from __future__ import annotations

import _setup_imports  # noqa: F401

from collections import defaultdict
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Callable, NamedTuple

from dotenv import load_dotenv
import requests

# Load .env file before importing modules that use os.getenv
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

from the_alchemiser.shared.config.secrets_adapter import get_alpaca_keys


class DailyRecord(NamedTuple):
    """Single day's P&L data."""

    date: str
    equity: Decimal
    raw_pnl: Decimal
    deposit: Decimal
    adjusted_pnl: Decimal


def fetch_deposits(api_key: str, secret_key: str) -> dict[str, Decimal]:
    """Fetch all CSD (cash deposit) activities from Alpaca."""
    # Use the activity-type-specific endpoint (more reliable)
    url = "https://api.alpaca.markets/v2/account/activities/CSD"
    headers = {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": secret_key,
        "accept": "application/json",
    }

    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    deposits_by_date: dict[str, Decimal] = defaultdict(Decimal)

    print(f"  Raw API returned {len(data)} CSD activities")

    for activity in data:
        date_str = activity.get("date", "")[:10]
        amount = Decimal(str(activity.get("net_amount", "0")))
        deposits_by_date[date_str] += amount
        print(f"    {date_str}: ${amount:,.2f}")

    return dict(deposits_by_date)


def fetch_portfolio_history(
    api_key: str, secret_key: str
) -> tuple[list[int], list[float], list[float]]:
    """Fetch portfolio history with 1-year period, per-day P&L reset."""
    url = "https://api.alpaca.markets/v2/account/portfolio/history"
    headers = {
        "APCA-API-KEY-ID": api_key,
        "APCA-API-SECRET-KEY": secret_key,
        "accept": "application/json",
    }
    params = {
        "period": "1A",
        "intraday_reporting": "market_hours",
        "pnl_reset": "per_day",
    }

    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    return data["timestamp"], data["equity"], data["profit_loss"]


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
    from datetime import timedelta

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


def build_daily_records(
    timestamps: list[int],
    equities: list[float],
    profit_losses: list[float],
    deposits: dict[str, Decimal],
) -> list[DailyRecord]:
    """Build daily records with deposit-adjusted P&L.

    Key insight: Alpaca's equity includes deposits, but deposits settle T+1.
    A deposit made on day D appears in equity on the next trading day.

    To get true trading P&L:
    - Calculate equity change from previous trading day
    - Subtract deposits that settled today (made on prev trading day or weekend days before today)
    """
    # Build list of all trading dates first
    all_dates = [format_ts(ts) for ts in timestamps]
    all_trading_days = set(all_dates)
    records = []

    for i, ts in enumerate(timestamps):
        date_str = format_ts(ts)
        equity = Decimal(str(equities[i]))
        raw_pnl = Decimal(str(profit_losses[i]))

        # Get all calendar days where deposits would settle today
        deposit_settled_today = Decimal("0")
        if i > 0:
            prev_trading_day = all_dates[i - 1]
            # Deposits made between prev trading day and today settle today
            days_to_check = get_deposit_dates_for_settlement(
                prev_trading_day, date_str, all_trading_days
            )
            for d in days_to_check:
                if d in deposits:
                    deposit_settled_today += deposits[d]

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
                adjusted_pnl=adjusted_pnl,
            )
        )

    return records


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


def print_daily_report(records: list[DailyRecord], deposits: dict[str, Decimal]) -> None:
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


def print_summary(records: list[DailyRecord], deposits: dict[str, Decimal]) -> None:
    """Print overall summary statistics."""
    print_section_header("SUMMARY STATISTICS")

    # Filter to only active trading days (equity > 0)
    active_records = [r for r in records if r.equity > 0]

    if not active_records:
        print("No data available.")
        return

    total_pnl = sum(r.adjusted_pnl for r in active_records)
    total_deposits = sum(deposits.values())

    # Find first non-zero equity day for starting point
    first_active = active_records[0]
    first_equity = first_active.equity - first_active.adjusted_pnl - first_active.deposit
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


def main() -> None:
    """Main entry point."""
    print()
    print("=" * 90)
    print("  ALPACA P&L REPORT - Deposit Adjusted")
    print("=" * 90)
    print()
    print("Loading credentials from .env...")

    api_key, secret_key, _ = get_alpaca_keys()
    if not api_key or not secret_key:
        print("ERROR: Missing ALPACA_KEY or ALPACA_SECRET in .env file")
        return

    print("Fetching deposit history (CSD activities)...")
    deposits = fetch_deposits(api_key, secret_key)
    print(f"  Found {len(deposits)} days with deposits, total: ${sum(deposits.values()):,.2f}")

    print("Fetching portfolio history (1 year, per-day P&L)...")
    timestamps, equities, profit_losses = fetch_portfolio_history(api_key, secret_key)
    print(f"  Found {len(timestamps)} trading days")

    print("Building daily records with deposit adjustments...")
    records = build_daily_records(timestamps, equities, profit_losses, deposits)

    # Generate reports
    print_daily_report(records, deposits)

    weekly_data = aggregate_periods(records, get_week_key)
    print_period_report(weekly_data, "Weekly")

    monthly_data = aggregate_periods(records, get_month_key)
    print_period_report(monthly_data, "Monthly")

    print_summary(records, deposits)


if __name__ == "__main__":
    main()
