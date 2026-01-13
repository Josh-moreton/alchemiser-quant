#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Diagnostic script to test Alpaca Portfolio History API responses.

This script helps debug P&L calculation issues by showing raw API responses
for different period parameters (1M, 1A, explicit date ranges).
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime, timedelta

# Setup imports for Lambda layers architecture
import _setup_imports  # noqa: F401

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetPortfolioHistoryRequest

from the_alchemiser.shared.config.config import load_settings
from the_alchemiser.shared.config.secrets_adapter import get_alpaca_keys
from the_alchemiser.shared.logging import configure_application_logging


def format_timestamp(ts: int) -> str:
    """Convert Unix timestamp to readable date string."""
    return datetime.fromtimestamp(ts, tz=UTC).strftime("%Y-%m-%d %H:%M:%S %Z")


def print_portfolio_history(label: str, history: dict) -> None:
    """Print formatted portfolio history data."""
    print(f"\n{'=' * 60}")
    print(f"📊 {label}")
    print("=" * 60)

    timestamps = getattr(history, "timestamp", [])
    equity = getattr(history, "equity", [])
    profit_loss = getattr(history, "profit_loss", [])
    profit_loss_pct = getattr(history, "profit_loss_pct", [])
    base_value = getattr(history, "base_value", None)
    timeframe = getattr(history, "timeframe", "unknown")

    print(f"\n📈 Summary:")
    print(f"  Base Value: ${base_value:,.2f}" if base_value else "  Base Value: None")
    print(f"  Timeframe: {timeframe}")
    print(f"  Data Points: {len(timestamps)}")

    if timestamps:
        print(f"\n📅 Date Range:")
        print(f"  First: {format_timestamp(timestamps[0])}")
        print(f"  Last:  {format_timestamp(timestamps[-1])}")

        # Calculate actual duration
        first_date = datetime.fromtimestamp(timestamps[0], tz=UTC)
        last_date = datetime.fromtimestamp(timestamps[-1], tz=UTC)
        duration = last_date - first_date
        print(f"  Duration: {duration.days} days")

    if equity:
        print(f"\n💰 Equity:")
        print(f"  First: ${equity[0]:,.2f}")
        print(f"  Last:  ${equity[-1]:,.2f}")
        print(f"  Change: ${equity[-1] - equity[0]:+,.2f}")

    if profit_loss:
        print(f"\n📊 Profit/Loss (cumulative from base_value):")
        print(f"  First: ${profit_loss[0]:+,.2f}")
        print(f"  Last (TOTAL P&L): ${profit_loss[-1]:+,.2f}")

    if profit_loss_pct:
        last_pct = profit_loss_pct[-1]
        if last_pct is not None:
            # Alpaca returns as decimal (e.g., 0.05 for 5%)
            print(f"\n📈 Profit/Loss % (cumulative):")
            print(f"  First: {profit_loss_pct[0] * 100 if profit_loss_pct[0] else 0:+.4f}%")
            print(f"  Last (TOTAL %): {last_pct * 100:+.4f}%")
        else:
            print(f"\n📈 Profit/Loss %: None (not available)")

    # Show first few and last few data points
    if len(timestamps) > 0:
        print(f"\n📋 First 3 Data Points:")
        for i in range(min(3, len(timestamps))):
            ts = format_timestamp(timestamps[i])
            eq = equity[i] if i < len(equity) else "N/A"
            pl = profit_loss[i] if i < len(profit_loss) else "N/A"
            pl_pct = profit_loss_pct[i] if i < len(profit_loss_pct) else "N/A"
            print(f"  [{i}] {ts} | Equity: ${eq:,.2f} | P&L: ${pl:+,.2f} | P&L%: {pl_pct}")

        if len(timestamps) > 6:
            print(f"  ... ({len(timestamps) - 6} more data points) ...")

        if len(timestamps) > 3:
            print(f"\n📋 Last 3 Data Points:")
            for i in range(max(0, len(timestamps) - 3), len(timestamps)):
                ts = format_timestamp(timestamps[i])
                eq = equity[i] if i < len(equity) else "N/A"
                pl = profit_loss[i] if i < len(profit_loss) else "N/A"
                pl_pct = profit_loss_pct[i] if i < len(profit_loss_pct) else "N/A"
                print(f"  [{i}] {ts} | Equity: ${eq:,.2f} | P&L: ${pl:+,.2f} | P&L%: {pl_pct}")


def test_period_based_requests(client: TradingClient) -> None:
    """Test portfolio history with period-based requests (how emails currently work)."""
    print("\n" + "=" * 70)
    print("🔬 TESTING PERIOD-BASED REQUESTS (current email implementation)")
    print("=" * 70)

    # Test 1M period (monthly P&L in emails)
    print("\n⏳ Fetching 1M (monthly) portfolio history...")
    try:
        request_1m = GetPortfolioHistoryRequest(period="1M", timeframe="1D")
        history_1m = client.get_portfolio_history(request_1m)
        print_portfolio_history("Period: 1M (Past Month)", history_1m)
    except Exception as e:
        print(f"❌ Error fetching 1M history: {e}")

    # Test 1A period (yearly P&L in emails)
    print("\n⏳ Fetching 1A (yearly) portfolio history...")
    try:
        request_1a = GetPortfolioHistoryRequest(period="1A", timeframe="1D")
        history_1a = client.get_portfolio_history(request_1a)
        print_portfolio_history("Period: 1A (Past Year)", history_1a)
    except Exception as e:
        print(f"❌ Error fetching 1A history: {e}")


def test_date_range_requests(client: TradingClient) -> None:
    """Test portfolio history with explicit date ranges."""
    print("\n" + "=" * 70)
    print("🔬 TESTING DATE RANGE REQUESTS (alternative approach)")
    print("=" * 70)

    today = datetime.now(UTC)

    # Test 30 days back (equivalent to 1M)
    start_30d = today - timedelta(days=30)
    print(f"\n⏳ Fetching last 30 days ({start_30d.date()} to {today.date()})...")
    try:
        request_30d = GetPortfolioHistoryRequest(
            start=start_30d,
            end=today,
            timeframe="1D",
        )
        history_30d = client.get_portfolio_history(request_30d)
        print_portfolio_history("Date Range: Last 30 Days", history_30d)
    except Exception as e:
        print(f"❌ Error fetching 30-day history: {e}")

    # Test 365 days back (equivalent to 1A)
    start_365d = today - timedelta(days=365)
    print(f"\n⏳ Fetching last 365 days ({start_365d.date()} to {today.date()})...")
    try:
        request_365d = GetPortfolioHistoryRequest(
            start=start_365d,
            end=today,
            timeframe="1D",
        )
        history_365d = client.get_portfolio_history(request_365d)
        print_portfolio_history("Date Range: Last 365 Days", history_365d)
    except Exception as e:
        print(f"❌ Error fetching 365-day history: {e}")


def test_various_periods(client: TradingClient) -> None:
    """Test multiple period values to understand API behavior."""
    print("\n" + "=" * 70)
    print("🔬 TESTING VARIOUS PERIOD VALUES")
    print("=" * 70)

    periods = ["1W", "1M", "3M", "6M", "1A"]

    for period in periods:
        print(f"\n⏳ Fetching {period} portfolio history...")
        try:
            request = GetPortfolioHistoryRequest(period=period, timeframe="1D")
            history = client.get_portfolio_history(request)

            timestamps = getattr(history, "timestamp", [])
            profit_loss = getattr(history, "profit_loss", [])
            base_value = getattr(history, "base_value", None)

            if timestamps:
                first_date = format_timestamp(timestamps[0])
                last_date = format_timestamp(timestamps[-1])
                duration = (
                    datetime.fromtimestamp(timestamps[-1], tz=UTC)
                    - datetime.fromtimestamp(timestamps[0], tz=UTC)
                ).days
                total_pnl = profit_loss[-1] if profit_loss else 0
                print(
                    f"  ✅ {period}: {len(timestamps)} points | "
                    f"{first_date[:10]} to {last_date[:10]} ({duration}d) | "
                    f"Base: ${base_value:,.2f if base_value else 0} | "
                    f"P&L: ${total_pnl:+,.2f}"
                )
            else:
                print(f"  ⚠️ {period}: No data returned")
        except Exception as e:
            print(f"  ❌ {period}: Error - {e}")


def get_account_info(client: TradingClient) -> None:
    """Get and display account information."""
    print("\n" + "=" * 70)
    print("🏦 ACCOUNT INFORMATION")
    print("=" * 70)

    try:
        account = client.get_account()
        print(f"\n  Account ID: {account.id}")
        print(f"  Account Number: {account.account_number}")
        print(f"  Status: {account.status}")
        print(f"  Created: {account.created_at}")
        print(f"  Equity: ${float(account.equity):,.2f}")
        print(f"  Cash: ${float(account.cash):,.2f}")
        print(f"  Portfolio Value: ${float(account.portfolio_value):,.2f}")

        # Calculate account age
        if account.created_at:
            created = account.created_at
            if created.tzinfo is None:
                created = created.replace(tzinfo=UTC)
            age = datetime.now(UTC) - created
            print(f"  Account Age: {age.days} days ({age.days // 30} months)")

    except Exception as e:
        print(f"❌ Error getting account info: {e}")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test Alpaca Portfolio History API responses",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all tests (period-based, date-range, various periods)",
    )
    parser.add_argument(
        "--periods",
        action="store_true",
        help="Test period-based requests (1M, 1A) - current email implementation",
    )
    parser.add_argument(
        "--dates",
        action="store_true",
        help="Test date-range requests (30d, 365d)",
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="Compare multiple period values (1W, 1M, 3M, 6M, 1A)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Default to --all if no specific test selected
    if not (args.all or args.periods or args.dates or args.compare):
        args.all = True

    # Configure logging
    if args.verbose:
        configure_application_logging()

    # Load config and get Alpaca credentials
    print("🔑 Loading configuration...")
    load_settings()
    api_key, secret_key, endpoint = get_alpaca_keys()

    if not api_key or not secret_key:
        print("❌ Alpaca API keys not found!")
        return 1

    # Determine if paper trading
    paper = True
    if endpoint:
        ep_lower = endpoint.lower()
        if "paper-api.alpaca.markets" in ep_lower:
            paper = True
        elif "api.alpaca.markets" in ep_lower and "paper" not in ep_lower:
            paper = False

    print(f"📡 Connecting to Alpaca ({'PAPER' if paper else 'LIVE'} trading)...")
    print(f"   Endpoint: {endpoint or 'default'}")

    # Create trading client
    client = TradingClient(api_key=api_key, secret_key=secret_key, paper=paper)

    # Get account info first
    get_account_info(client)

    # Run requested tests
    if args.all or args.periods:
        test_period_based_requests(client)

    if args.all or args.dates:
        test_date_range_requests(client)

    if args.all or args.compare:
        test_various_periods(client)

    print("\n" + "=" * 70)
    print("✅ Testing complete!")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
