#!/usr/bin/env python3
"""Deep dive into Alpaca P&L calculation to understand deposits."""

import _setup_imports  # noqa: F401

from datetime import UTC, datetime, timedelta

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetPortfolioHistoryRequest
import requests

from the_alchemiser.shared.config.config import load_settings
from the_alchemiser.shared.config.secrets_adapter import get_alpaca_keys


def format_ts(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=UTC).strftime("%Y-%m-%d")


load_settings()
api_key, secret_key, endpoint = get_alpaca_keys()
client = TradingClient(api_key=api_key, secret_key=secret_key, paper=False)
base_url = "https://api.alpaca.markets"
headers = {"APCA-API-KEY-ID": api_key, "APCA-API-SECRET-KEY": secret_key}

# Get December 2025 data
start = datetime(2025, 12, 1, tzinfo=UTC)
end = datetime(2025, 12, 31, 23, 59, 59, tzinfo=UTC)
request = GetPortfolioHistoryRequest(start=start, end=end, timeframe="1D")
history = client.get_portfolio_history(request)

# Get deposit info
resp_csd = requests.get(f"{base_url}/v2/account/activities/CSD", headers=headers)
csd_data = resp_csd.json()
deposits_by_date = {}
for act in csd_data:
    date_str = act.get('date', '')[:10]  # YYYY-MM-DD
    amt = float(act.get('net_amount', 0))
    deposits_by_date[date_str] = deposits_by_date.get(date_str, 0) + amt

print("=" * 80)
print("DETAILED P&L ANALYSIS - DECEMBER 2025")
print("=" * 80)
print()
print("Deposits in December 2025:")
for date, amt in sorted(deposits_by_date.items()):
    if date.startswith('2025-12'):
        print(f"  {date}: ${amt:+,.2f}")

print()
print("-" * 80)
print("Daily breakdown with deposit correlation:")
print("-" * 80)
print(f"{'Date':<12} {'Equity':>12} {'P&L':>12} {'Deposit?':>12} {'P&L matches deposit?':<25}")
print("-" * 80)

prev_equity = None
for i in range(len(history.timestamp)):
    date_str = format_ts(history.timestamp[i])
    eq = history.equity[i]
    pl = history.profit_loss[i]
    
    # Check if there was a deposit the previous day (settles next day)
    prev_date = (datetime.strptime(date_str, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    deposit = deposits_by_date.get(prev_date, 0) or deposits_by_date.get(date_str, 0)
    
    # Calculate equity change
    if prev_equity is not None:
        eq_change = eq - prev_equity
        # Does P&L match equity change minus deposit?
        trading_pnl = eq_change - deposit if deposit else eq_change
        match = abs(pl - trading_pnl) < 1
    else:
        eq_change = None
        match = None
    
    deposit_str = f"${deposit:,.0f}" if deposit else ""
    match_str = "✓ YES" if match else ("✗ NO" if match is not None else "")
    
    print(f"{date_str:<12} ${eq:>10,.2f} ${pl:>+10,.2f} {deposit_str:>12} {match_str:<25}")
    
    prev_equity = eq

print("-" * 80)
print()

# Recalculate with deposit exclusion
print("=" * 80)
print("P&L CALCULATION OPTIONS:")
print("=" * 80)
print()

# Option 1: Sum all P&L (includes deposits counted as gains)
sum_all = sum(history.profit_loss)
sum_skip_first = sum(history.profit_loss[1:])
print(f"1. Sum of all profit_loss: ${sum_all:+,.2f}")
print(f"2. Sum of profit_loss[1:] (skip first): ${sum_skip_first:+,.2f}")

# Option 3: Equity change
eq_change = history.equity[-1] - history.equity[0]
print(f"3. Equity change (first to last): ${eq_change:+,.2f}")

# Option 4: Subtract deposits from equity change
total_dec_deposits = sum(amt for date, amt in deposits_by_date.items() if date.startswith('2025-12'))
trading_pnl = eq_change - total_dec_deposits
print(f"4. Equity change minus deposits: ${eq_change:+,.2f} - ${total_dec_deposits:+,.2f} = ${trading_pnl:+,.2f}")

print()
print("=" * 80)
print("CONCLUSION:")
print("=" * 80)
print()
print("The Alpaca profit_loss values INCLUDE deposits as 'gains'.")
print("To get pure TRADING P&L, use: equity_change - deposits")
print(f"\nDecember 2025 Trading P&L (excluding deposits): ${trading_pnl:+,.2f}")

# Calculate percentage based on starting equity before deposits
starting_eq_before_deposits = history.equity[0] - deposits_by_date.get('2025-12-01', 0)
pct = (trading_pnl / starting_eq_before_deposits) * 100 if starting_eq_before_deposits else 0
print(f"Percentage return (vs starting equity): {pct:+.2f}%")
