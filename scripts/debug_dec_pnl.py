#!/usr/bin/env python3
"""Debug December 2025 P&L data."""

import _setup_imports  # noqa: F401

from datetime import UTC, datetime

from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetPortfolioHistoryRequest

from the_alchemiser.shared.config.config import load_settings
from the_alchemiser.shared.config.secrets_adapter import get_alpaca_keys


def format_ts(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=UTC).strftime("%Y-%m-%d")


load_settings()
api_key, secret_key, endpoint = get_alpaca_keys()
client = TradingClient(api_key=api_key, secret_key=secret_key, paper=False)

# Get December 2025 data
start = datetime(2025, 12, 1, tzinfo=UTC)
end = datetime(2025, 12, 31, 23, 59, 59, tzinfo=UTC)
request = GetPortfolioHistoryRequest(start=start, end=end, timeframe="1D")
history = client.get_portfolio_history(request)

print("=" * 70)
print("December 2025 Raw Data from Alpaca")
print("=" * 70)
print(f"Base Value: ${history.base_value:,.2f}" if history.base_value else "Base Value: None")
print(f"Data Points: {len(history.timestamp)}")
print()

# Show all data points
print("Daily breakdown:")
print("-" * 70)
for i in range(len(history.timestamp)):
    ts = format_ts(history.timestamp[i])
    eq = history.equity[i]
    pl = history.profit_loss[i]
    pl_pct = history.profit_loss_pct[i] if history.profit_loss_pct[i] else 0
    print(f"  {ts} | Equity: ${eq:>10,.2f} | P&L: ${pl:>+10,.2f} | P&L%: {pl_pct:>+8.4f}")

print("-" * 70)
print()
print("Analysis of pnl_reset behavior (1D timeframe):")
print()
print("Per Alpaca docs: 'For 1D resolution all PnL values are calculated")
print("relative to the base_value, we are not resetting the base value.'")
print()

# Verify: base_value + profit_loss[i] should equal equity[i] if no deposits
print("Checking if base_value + profit_loss = equity:")
for i in [0, 1, 2, 10, -1]:
    idx = i if i >= 0 else len(history.equity) + i
    implied_equity = history.base_value + history.profit_loss[idx]
    actual_equity = history.equity[idx]
    diff = actual_equity - implied_equity
    date_str = format_ts(history.timestamp[idx])
    print(f"  {date_str}: base({history.base_value:.2f}) + pnl({history.profit_loss[idx]:+.2f}) = {implied_equity:.2f}")
    print(f"              actual equity = {actual_equity:.2f}, diff = ${diff:+,.2f}")
    if abs(diff) > 1:
        print(f"              ^^^ DEPOSIT/WITHDRAWAL of ~${diff:,.0f} detected!")
    print()

# Calculate implied base for each day: equity[i] - profit_loss[i]
print("Implied base (equity - profit_loss) for each day:")
implied_bases = [history.equity[i] - history.profit_loss[i] for i in range(len(history.equity))]
for i in range(min(5, len(implied_bases))):
    print(f"  Day {i+1}: implied_base = ${implied_bases[i]:,.2f}")
print("  ...")
for i in range(-3, 0):
    idx = len(implied_bases) + i
    print(f"  Day {idx+1}: implied_base = ${implied_bases[idx]:,.2f}")

print()
print("-" * 70)
print()
print("CORRECT P&L CALCULATION FOR PERIOD:")
print()

# Method 1: Equity change (includes deposits/withdrawals)
equity_change = history.equity[-1] - history.equity[0]
equity_pct = equity_change / history.equity[0] * 100
print("Method 1: Equity Change (INCLUDES deposits/withdrawals)")
print(f"  equity[-1] - equity[0] = ${history.equity[-1]:,.2f} - ${history.equity[0]:,.2f} = ${equity_change:+,.2f}")
print(f"  Percentage: {equity_pct:+.2f}%")
print()

# Method 2: Use last cumulative P&L (per Alpaca docs, no-reset is cumulative)
# With pnl_reset='no_reset', profit_loss[-1] is cumulative P&L from base_value
cumulative_pnl = history.profit_loss[-1]
cumulative_pnl_pct = cumulative_pnl / history.equity[0] * 100
print("Method 2: Cumulative P&L (TRADING P&L, before adjusting for deposits)")
print(f"  profit_loss[-1] = ${cumulative_pnl:+,.2f}")
print(f"  Cumulative P&L % (vs equity[0]): {cumulative_pnl_pct:+.2f}%")
print()

# Method 3: TRUE Trading P&L = cumulative P&L minus deposits
# Fetch deposits from Alpaca API
import requests
base_url = "https://api.alpaca.markets"
headers = {"APCA-API-KEY-ID": api_key, "APCA-API-SECRET-KEY": secret_key}
resp_csd = requests.get(f"{base_url}/v2/account/activities/CSD", headers=headers)
csd_data = resp_csd.json()

# Sum December 2025 deposits only
dec_deposits = sum(
    float(act.get('net_amount', 0))
    for act in csd_data
    if act.get('date', '')[:7] == '2025-12'
)
print("Method 3: TRUE Trading P&L = cumulative P&L - deposits")
print(f"  Deposits in December 2025: ${dec_deposits:+,.2f}")
true_trading_pnl = cumulative_pnl - dec_deposits
true_trading_pnl_pct = true_trading_pnl / history.equity[0] * 100
print(f"  TRUE Trading P&L = ${cumulative_pnl:+,.2f} - ${dec_deposits:+,.2f} = ${true_trading_pnl:+,.2f}")
print(f"  TRUE Trading P&L %: {true_trading_pnl_pct:+.2f}%")
print()

# Verify: equity change = deposits + cumulative trading P&L
print("Verification: equity_change = trading_pnl + deposits")
print(f"  ${equity_change:+,.2f} ≈ ${true_trading_pnl:+,.2f} + ${dec_deposits:+,.2f}")
print()

print("=" * 70)
print("CONCLUSION:")
print("  For TRUE TRADING P&L: use profit_loss[-1] - deposits (CSD)")
print(f"  December 2025 TRUE Trading P&L: ${true_trading_pnl:+,.2f} ({true_trading_pnl_pct:+.2f}%)")
print("=" * 70)
