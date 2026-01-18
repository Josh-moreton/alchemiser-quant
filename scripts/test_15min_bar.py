#!/usr/bin/env python3
"""Test script to verify 15-minute bar fetching from Alpaca."""

from dotenv import load_dotenv
load_dotenv()

import os
from datetime import date

# Import from trace script
from scripts.trace_strategy_routes import _fetch_simulated_live_bar

print("Testing _fetch_simulated_live_bar function\n")

# Test NBIS on Jan 15, 2026
result = _fetch_simulated_live_bar("NBIS", date(2026, 1, 15))
print(f"NBIS 2026-01-15:")
if result:
    print(f"  Close: {result['close']}")
    print(f"  Timestamp: {result['timestamp']}")
else:
    print("  No data returned")

# Test CORD
result2 = _fetch_simulated_live_bar("CORD", date(2026, 1, 15))
print(f"\nCORD 2026-01-15:")
if result2:
    print(f"  Close: {result2['close']}")
    print(f"  Timestamp: {result2['timestamp']}")
else:
    print("  No data returned")

# Test SOXS
result3 = _fetch_simulated_live_bar("SOXS", date(2026, 1, 15))
print(f"\nSOXS 2026-01-15:")
if result3:
    print(f"  Close: {result3['close']}")
    print(f"  Timestamp: {result3['timestamp']}")
else:
    print("  No data returned")
