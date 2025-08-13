#!/usr/bin/env python3
"""Debug market hours detection issue."""

import os
from datetime import datetime, timezone
import pytz


def debug_market_hours():
    """Debug the market hours detection issue."""
    print("=== MARKET HOURS DEBUG ===\n")

    # Check current time
    now_utc = datetime.now(timezone.utc)
    et_tz = pytz.timezone("US/Eastern")
    now_et = now_utc.astimezone(et_tz)

    print(f"Current UTC time: {now_utc}")
    print(f"Current ET time: {now_et}")
    print(f"Day of week: {now_et.weekday()} (0=Monday, 6=Sunday)")
    print(f"Is weekday: {now_et.weekday() < 5}")

    # Check if should be market hours
    market_open_time = datetime.min.time().replace(hour=9, minute=30)
    market_close_time = datetime.min.time().replace(hour=16, minute=0)

    current_time = now_et.time()
    should_be_open = (
        now_et.weekday() < 5  # Monday-Friday
        and market_open_time <= current_time <= market_close_time
    )

    print(f"\nMarket should be open: {should_be_open}")
    print(f"Market hours: {market_open_time} - {market_close_time} ET")
    print(f"Current time: {current_time} ET")

    # Test Alpaca API
    print("\n=== ALPACA API TEST ===")
    try:
        from alpaca.trading.client import TradingClient

        # Try to get API keys from environment
        api_key = os.environ.get("ALPACA_API_KEY")
        secret_key = os.environ.get("ALPACA_SECRET_KEY")

        if not api_key or not secret_key:
            print("❌ API keys not found in environment")
            # Try loading from settings
            try:
                from the_alchemiser.infrastructure.config import load_settings

                settings = load_settings()
                api_key = getattr(settings, "ALPACA_API_KEY", None) or getattr(
                    settings, "alpaca_api_key", None
                )
                secret_key = getattr(settings, "ALPACA_SECRET_KEY", None) or getattr(
                    settings, "alpaca_secret_key", None
                )

                if api_key and secret_key:
                    print("✅ API keys loaded from settings")
                else:
                    print("❌ API keys not found in settings either")
                    return
            except Exception as e:
                print(f"❌ Failed to load settings: {e}")
                return
        else:
            print("✅ API keys found in environment")

        # Create client and test
        client = TradingClient(api_key, secret_key, paper=True)
        clock = client.get_clock()

        print(f"\nAlpaca Clock Response:")
        print(f"  Timestamp: {clock.timestamp}")
        print(f"  Is Open: {clock.is_open}")
        print(f"  Next Open: {clock.next_open}")
        print(f"  Next Close: {clock.next_close}")

        # Compare with our logic
        print(f"\nComparison:")
        print(f"  Our logic says open: {should_be_open}")
        print(f"  Alpaca says open: {clock.is_open}")
        print(f"  Match: {should_be_open == clock.is_open}")

        if should_be_open != clock.is_open:
            print(f"\n⚠️  MISMATCH DETECTED!")
            if not clock.is_open:
                print(f"  Market should be open but Alpaca reports closed")
                print(f"  Next open according to Alpaca: {clock.next_open}")
                print(f"  This might be a holiday or market closure")

    except Exception as e:
        print(f"❌ Error testing Alpaca API: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    debug_market_hours()
