#!/usr/bin/env python3
"""Test the cashflow_types parameter for portfolio history."""

import sys
sys.path.insert(0, "/Users/joshua.moreton/Documents/GitHub/alchemiser-quant/scripts")
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

start = datetime(2025, 12, 1, tzinfo=UTC)
end = datetime(2025, 12, 31, 23, 59, 59, tzinfo=UTC)

print("=" * 70)
print("Testing cashflow_types parameter")
print("=" * 70)

# Test 1: Default (no cashflow_types - includes ALL)
print("\n1. DEFAULT (no cashflow_types parameter):")
req_default = GetPortfolioHistoryRequest(start=start, end=end, timeframe="1D")
history_default = client.get_portfolio_history(req_default)
print(f"   Data points: {len(history_default.timestamp)}")
print(f"   Base value: ${history_default.base_value:,.2f}")
print(f"   First equity: ${history_default.equity[0]:,.2f}")
print(f"   Last equity: ${history_default.equity[-1]:,.2f}")
print(f"   Equity change: ${history_default.equity[-1] - history_default.equity[0]:+,.2f}")
sum_pnl_default = sum(history_default.profit_loss[1:])
print(f"   Sum P&L (skip first): ${sum_pnl_default:+,.2f}")

# Test 2: cashflow_types='NONE' (excludes all cashflows)
print("\n2. cashflow_types='NONE' (excludes all cashflows):")
try:
    # The SDK might not support this directly, let's check
    req_none = GetPortfolioHistoryRequest(start=start, end=end, timeframe="1D")
    # Check if we can pass cashflow_types
    print("   Checking GetPortfolioHistoryRequest attributes...")
    print(f"   Available fields: {req_none.model_fields.keys()}")
except Exception as e:
    print(f"   Error: {e}")

# Let's try with the raw API instead
print("\n3. Using raw HTTP request to test cashflow_types:")
import requests

base_url = "https://api.alpaca.markets"
headers = {
    "APCA-API-KEY-ID": api_key,
    "APCA-API-SECRET-KEY": secret_key,
}

# Default request
params_default = {
    "start": "2025-12-01",
    "end": "2025-12-31", 
    "timeframe": "1D",
}
resp_default = requests.get(
    f"{base_url}/v2/account/portfolio/history",
    headers=headers,
    params=params_default,
)
data_default = resp_default.json()
print(f"   Default response keys: {data_default.keys()}")

# With cashflow_types=NONE
params_none = {
    "start": "2025-12-01",
    "end": "2025-12-31",
    "timeframe": "1D",
    "cashflow_types": "NONE",
}
resp_none = requests.get(
    f"{base_url}/v2/account/portfolio/history",
    headers=headers,
    params=params_none,
)
data_none = resp_none.json()

if "equity" in data_none:
    print(f"\n   With cashflow_types='NONE':")
    print(f"   Base value: ${data_none.get('base_value', 0):,.2f}")
    print(f"   First equity: ${data_none['equity'][0]:,.2f}")
    print(f"   Last equity: ${data_none['equity'][-1]:,.2f}")
    print(f"   Equity change: ${data_none['equity'][-1] - data_none['equity'][0]:+,.2f}")
    sum_pnl_none = sum(data_none['profit_loss'][1:])
    print(f"   Sum P&L (skip first): ${sum_pnl_none:+,.2f}")
    
    # Compare
    print(f"\n   COMPARISON (Default vs NONE):")
    print(f"   Equity change diff: ${(data_none['equity'][-1] - data_none['equity'][0]) - (history_default.equity[-1] - history_default.equity[0]):+,.2f}")
    print(f"   Sum P&L diff: ${sum_pnl_none - sum_pnl_default:+,.2f}")
else:
    print(f"   Error response: {data_none}")

# Also fetch account activities to see deposits
print("\n" + "=" * 70)
print("Fetching deposit activities in December 2025:")
print("=" * 70)
from alpaca.trading.enums import ActivityType

try:
    activities = client.get_account_activities(activity_types=[ActivityType.CSD])
    print(f"\nCSD (Cash Disbursement) activities: {len(activities)}")
    for act in activities[:5]:
        print(f"  {act}")
except Exception as e:
    print(f"  Error: {e}")

# Compare day by day: default vs NONE
print("\n" + "=" * 70)
print("DAILY COMPARISON: Default vs cashflow_types='NONE'")
print("=" * 70)

# Get NONE data with same date range
params_none_dec = {
    "start": "2025-12-01",
    "end": "2025-12-31",
    "timeframe": "1D",
    "cashflow_types": "NONE",
}
resp_none_dec = requests.get(
    f"{base_url}/v2/account/portfolio/history",
    headers=headers,
    params=params_none_dec,
)
data_none_dec = resp_none_dec.json()

print(f"\nData points - Default: {len(history_default.timestamp)}, NONE: {len(data_none_dec['timestamp'])}")
print("\nDay-by-day comparison (showing differences only):")
print("-" * 70)

for i in range(min(len(history_default.timestamp), len(data_none_dec['timestamp']))):
    date_default = format_ts(history_default.timestamp[i])
    eq_default = history_default.equity[i]
    pl_default = history_default.profit_loss[i]
    
    eq_none = data_none_dec['equity'][i]
    pl_none = data_none_dec['profit_loss'][i]
    
    eq_diff = eq_none - eq_default
    pl_diff = pl_none - pl_default
    
    if abs(eq_diff) > 0.01 or abs(pl_diff) > 0.01:
        print(f"  {date_default}:")
        print(f"    Equity: ${eq_default:,.2f} vs ${eq_none:,.2f} (diff: ${eq_diff:+,.2f})")
        print(f"    P&L:    ${pl_default:+,.2f} vs ${pl_none:+,.2f} (diff: ${pl_diff:+,.2f})")

print()
print("If no differences shown, cashflow_types='NONE' doesn't change daily P&L values.")
print("It may only affect the base_value or overall calculation.")

# Check base_value difference
print(f"\nBase value - Default: ${history_default.base_value:,.2f}, NONE: ${data_none_dec.get('base_value', 0):,.2f}")

print()
print("=" * 70)
