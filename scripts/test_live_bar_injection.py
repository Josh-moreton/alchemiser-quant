#!/usr/bin/env python3
"""Test script to verify live bar injection works with CachedMarketDataAdapter."""

import os

os.environ["STRATEGY_APPEND_LIVE_BAR"] = "true"

from dotenv import load_dotenv

load_dotenv()

from the_alchemiser.data_v2.cached_market_data_adapter import CachedMarketDataAdapter
from the_alchemiser.data_v2.live_bar_provider import LiveBarProvider
from the_alchemiser.shared.value_objects.symbol import Symbol


def test_live_bar_injection():
    """Test that live bar is appended to historical data."""
    # Create adapter with live bar injection enabled
    adapter = CachedMarketDataAdapter(
        append_live_bar=True,
        live_bar_provider=LiveBarProvider(),
    )

    # Get bars for SPY
    symbol = Symbol("SPY")
    bars = adapter.get_bars(symbol, "1Y", "1Day")

    print(f"Total bars: {len(bars)}")
    if bars:
        print(f"\nFirst bar (oldest):")
        print(f"  Date:  {bars[0].timestamp.date()}")
        print(f"  Close: ${float(bars[0].close):.2f}")

        print(f"\nLast bar (today's live):")
        print(f"  Date:  {bars[-1].timestamp.date()}")
        print(f"  Close: ${float(bars[-1].close):.2f}")
        print(f"  Volume: {bars[-1].volume:,}")

        # Verify we have enough bars for 200-day SMA
        if len(bars) >= 200:
            print(f"\n✅ Have {len(bars)} bars - sufficient for 200-day SMA")
            # Calculate simple 200-day SMA
            closes = [float(bar.close) for bar in bars[-200:]]
            sma_200 = sum(closes) / 200
            print(f"   200-day SMA: ${sma_200:.2f}")
            print(f"   Current price: ${float(bars[-1].close):.2f}")
            if float(bars[-1].close) > sma_200:
                print("   📈 Price ABOVE 200-day SMA (bullish)")
            else:
                print("   📉 Price BELOW 200-day SMA (bearish)")
        else:
            print(f"\n⚠️ Only {len(bars)} bars - need 200 for full SMA")
    else:
        print("❌ No bars returned")


if __name__ == "__main__":
    test_live_bar_injection()
