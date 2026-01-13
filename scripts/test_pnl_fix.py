#!/usr/bin/env python3
"""Test script to verify the P&L calculation fix."""

import _setup_imports  # noqa: F401

from the_alchemiser.shared.config.config import load_settings
from the_alchemiser.shared.services.pnl_service import PnLService

load_settings()

print("=" * 70)
print("Testing P&L Service with Deposit Adjustment")
print("=" * 70)

# Create PnL service
pnl_service = PnLService()

# Test December 2025
print("\n1. December 2025 P&L:")
print("-" * 70)
try:
    dec_pnl = pnl_service.get_calendar_month_pnl(2025, 12)
    print(f"   Period: {dec_pnl.period}")
    print(f"   Start Value: ${dec_pnl.start_value:,.2f}" if dec_pnl.start_value else "   Start Value: N/A")
    print(f"   End Value: ${dec_pnl.end_value:,.2f}" if dec_pnl.end_value else "   End Value: N/A")
    print(f"   Total P&L: ${dec_pnl.total_pnl:+,.2f}" if dec_pnl.total_pnl else "   Total P&L: N/A")
    print(f"   Total P&L %: {dec_pnl.total_pnl_pct:+.2f}%" if dec_pnl.total_pnl_pct else "   Total P&L %: N/A")
except Exception as e:
    print(f"   Error: {e}")

# Test November 2025
print("\n2. November 2025 P&L:")
print("-" * 70)
try:
    nov_pnl = pnl_service.get_calendar_month_pnl(2025, 11)
    print(f"   Period: {nov_pnl.period}")
    print(f"   Start Value: ${nov_pnl.start_value:,.2f}" if nov_pnl.start_value else "   Start Value: N/A")
    print(f"   End Value: ${nov_pnl.end_value:,.2f}" if nov_pnl.end_value else "   End Value: N/A")
    print(f"   Total P&L: ${nov_pnl.total_pnl:+,.2f}" if nov_pnl.total_pnl else "   Total P&L: N/A")
    print(f"   Total P&L %: {nov_pnl.total_pnl_pct:+.2f}%" if nov_pnl.total_pnl_pct else "   Total P&L %: N/A")
except Exception as e:
    print(f"   Error: {e}")

# Test January 2026 (MTD)
print("\n3. January 2026 (MTD) P&L:")
print("-" * 70)
try:
    jan_pnl = pnl_service.get_calendar_month_pnl(2026, 1)
    print(f"   Period: {jan_pnl.period}")
    print(f"   Start Value: ${jan_pnl.start_value:,.2f}" if jan_pnl.start_value else "   Start Value: N/A")
    print(f"   End Value: ${jan_pnl.end_value:,.2f}" if jan_pnl.end_value else "   End Value: N/A")
    print(f"   Total P&L: ${jan_pnl.total_pnl:+,.2f}" if jan_pnl.total_pnl else "   Total P&L: N/A")
    print(f"   Total P&L %: {jan_pnl.total_pnl_pct:+.2f}%" if jan_pnl.total_pnl_pct else "   Total P&L %: N/A")
except Exception as e:
    print(f"   Error: {e}")

# Test last 3 months
print("\n4. Last 3 Calendar Months:")
print("-" * 70)
try:
    months = pnl_service.get_last_n_calendar_months_pnl(3)
    for m in months:
        pnl_str = f"${m.total_pnl:+,.2f}" if m.total_pnl else "N/A"
        pct_str = f"({m.total_pnl_pct:+.2f}%)" if m.total_pnl_pct else ""
        print(f"   {m.period}: {pnl_str} {pct_str}")
except Exception as e:
    print(f"   Error: {e}")

print()
print("=" * 70)
print("EXPECTED RESULTS for December 2025:")
print("=" * 70)
print("""
Based on your API test:
- Cumulative P&L at start (Dec 2): $1,314.70
- Cumulative P&L at end (Dec 31): $2,974.30
- Raw period P&L = $2,974.30 - $1,314.70 = $1,659.60

Deposits in December:
- Dec 1: $1,313.09
- Dec 4: $1,500.00
- Dec 24: $200.00
- Total: $3,013.09

TRUE Trading P&L = $1,659.60 - $3,013.09 = -$1,353.49

This means we LOST money trading in December, but deposits masked it!
""")
