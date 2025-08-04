#!/usr/bin/env python3
"""
Test script for real-time pricing implementation.
"""

import logging
import time

from the_alchemiser.core.data.data_provider import UnifiedDataProvider

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def test_real_time_pricing():
    """Test real-time pricing functionality with realistic symbol limits."""

    # Test with realistic number of symbols (≤5 for actual trading)
    test_symbols = ["AAPL", "MSFT"]  # Only 2 symbols to stay well under limits

    try:
        # Test data provider integration with real-time pricing
        print("🔗 Testing UnifiedDataProvider with real-time pricing...")
        print(f"📊 Testing with {len(test_symbols)} symbols (realistic trading scenario)")

        data_provider = UnifiedDataProvider(paper_trading=True, enable_real_time=True)

        # Wait for connection
        print("Waiting for WebSocket connection...")
        time.sleep(3)

        if data_provider.real_time_pricing and data_provider.real_time_pricing.is_connected():
            print("✅ Connected to real-time data stream")

            # Test sequential price retrieval (more realistic)
            print("\n📈 Sequential price testing (simulating real trading):")
            for i, symbol in enumerate(test_symbols, 1):
                print(f"\n   [{i}/{len(test_symbols)}] Processing {symbol}...")

                # Get price (this will auto-subscribe)
                price = data_provider.get_current_price(symbol)
                if price:
                    print(f"   💰 {symbol}: ${price:.2f}")
                else:
                    print(f"   ❌ No price data for {symbol}")

                # Brief pause to allow WebSocket data to flow
                time.sleep(1)

                # Check for real-time quote data
                if data_provider.real_time_pricing:
                    bid_ask = data_provider.real_time_pricing.get_latest_quote(symbol)
                    if bid_ask:
                        bid, ask = bid_ask
                        spread = ask - bid
                        print(
                            f"   📊 Real-time: Bid=${bid:.2f}, Ask=${ask:.2f}, Spread=${spread:.2f}"
                        )
                    else:
                        print(f"   📡 Real-time quote pending for {symbol}")

        else:
            print("⚠️ WebSocket not connected, will use REST API fallback")
            # Still test pricing with REST API
            for symbol in test_symbols:
                price = data_provider.get_current_price(symbol)
                if price:
                    print(f"💰 {symbol} (REST): ${price:.2f}")
                else:
                    print(f"❌ No price data for {symbol}")

        # Test real-time pricing stats if available
        if data_provider.real_time_pricing and data_provider.real_time_pricing.is_connected():
            # Wait a bit more for potential data
            print("\n⏳ Waiting for real-time data to accumulate...")
            time.sleep(2)

            stats = data_provider.real_time_pricing.get_stats()
            subscribed = data_provider.real_time_pricing.get_subscribed_symbols()

            print("\n📊 Real-time pricing session summary:")
            print(f"   Quotes received: {stats.get('quotes_received', 0)}")
            print(f"   Trades received: {stats.get('trades_received', 0)}")
            print(f"   Connection errors: {stats.get('connection_errors', 0)}")
            print(f"   Active subscriptions: {len(subscribed)} symbols")
            print(f"   Subscribed to: {', '.join(subscribed) if subscribed else 'None'}")

            # Success criteria
            total_data_points = stats.get("quotes_received", 0) + stats.get("trades_received", 0)
            if total_data_points > 0:
                print(f"   ✅ Real-time data flowing ({total_data_points} data points received)")
            else:
                print(
                    "   ⚠️ No real-time data received (likely subscription limits or market hours)"
                )

        print("\n✅ Realistic trading test completed successfully!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        logging.exception("Test error")

    finally:
        # Clean shutdown
        if "data_provider" in locals() and data_provider.real_time_pricing:
            data_provider.real_time_pricing.stop()
            print("🛑 Pricing service stopped")


def test_without_websocket():
    """Test fallback to REST API without WebSocket."""
    print("\n🔄 Testing REST API fallback...")

    # Initialize data provider without real-time pricing
    data_provider = UnifiedDataProvider(enable_real_time=False)

    test_symbols = ["AAPL", "MSFT"]

    for symbol in test_symbols:
        price = data_provider.get_current_price_rest(symbol)
        if price:
            print(f"📈 {symbol} (REST only): ${price:.2f}")
        else:
            print(f"❌ REST API failed for {symbol}")


if __name__ == "__main__":
    print("🚀 Starting real-time pricing tests...")

    # Test WebSocket real-time pricing
    try:
        test_real_time_pricing()
    except KeyboardInterrupt:
        print("\n⚡ Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logging.exception("Test error")

    # Test REST API fallback
    test_without_websocket()

    print("\n🏁 All tests completed!")
