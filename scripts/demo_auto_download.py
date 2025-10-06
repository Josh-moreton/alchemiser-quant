#!/usr/bin/env python3
"""Demo script showing auto-download functionality.

This script demonstrates the new auto-download feature for missing historical data.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from scripts.backtest.storage.data_store import DataStore
from scripts.backtest.storage.providers.alpaca_historical import AlpacaHistoricalProvider
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


def demo_auto_download():
    """Demonstrate auto-download functionality."""
    print("=" * 80)
    print("Auto-Download Demo: Loading Historical Data")
    print("=" * 80)
    print()

    # Create data store with Alpaca provider
    print("1. Initializing DataStore with AlpacaHistoricalProvider...")
    try:
        provider = AlpacaHistoricalProvider()
        data_store = DataStore(
            base_path="data/historical_demo",
            data_provider=provider
        )
        print("   ✓ DataStore initialized with auto-download support")
    except ValueError as e:
        print(f"   ✗ Failed to initialize provider: {e}")
        print("   → Make sure ALPACA_API_KEY and ALPACA_SECRET_KEY are set")
        return
    
    print()

    # Try to load data for a symbol
    symbol = "AAPL"
    start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end_date = datetime(2024, 1, 5, tzinfo=timezone.utc)

    print(f"2. Loading bars for {symbol} from {start_date.date()} to {end_date.date()}...")
    print(f"   → If data is missing locally, it will be auto-downloaded from Alpaca")
    print()

    try:
        bars = data_store.load_bars(symbol, start_date, end_date)
        print(f"   ✓ Successfully loaded {len(bars)} bars for {symbol}")
        
        if bars:
            print()
            print("   Sample bars:")
            for i, bar in enumerate(bars[:3]):
                print(f"     [{i+1}] {bar.date.date()}: "
                      f"O={bar.open} H={bar.high} L={bar.low} C={bar.close} V={bar.volume}")
                
    except Exception as e:
        print(f"   ✗ Failed to load bars: {e}")
        print()
        return

    print()
    print("=" * 80)
    print("Demo Complete!")
    print()
    print("Key Features Demonstrated:")
    print("  • Auto-download missing data from Alpaca API")
    print("  • Local caching for future runs")
    print("  • Clear error messages when data unavailable")
    print("=" * 80)


if __name__ == "__main__":
    demo_auto_download()
