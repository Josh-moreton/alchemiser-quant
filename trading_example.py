#!/usr/bin/env python3
"""
Example integration of real-time pricing with trading strategy.

This shows how the enhanced data provider with WebSocket real-time pricing
would integrate with the existing trading bot architecture.
"""

import logging
import time
from the_alchemiser.core.data.data_provider import UnifiedDataProvider

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TradingExample:
    """Example trading class using real-time pricing."""
    
    def __init__(self):
        self.data_provider = UnifiedDataProvider(
            paper_trading=True, 
            enable_real_time=True
        )
        
    def place_limit_order(self, symbol: str, quantity: int, side: str = "buy"):
        """
        Place a limit order with real-time pricing for accuracy.
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares
            side: "buy" or "sell"
        """
        print(f"\n🎯 Placing {side} order for {quantity} shares of {symbol}")
        
        # Get real-time price for accurate limit order
        current_price = self.data_provider.get_current_price(symbol)
        if not current_price:
            print(f"❌ Could not get current price for {symbol}")
            return
            
        print(f"💰 Current price: ${current_price:.2f}")
        
        # Get bid/ask spread for more precise pricing
        if self.data_provider.real_time_pricing and self.data_provider.real_time_pricing.is_connected():
            bid_ask = self.data_provider.real_time_pricing.get_latest_quote(symbol)
            if bid_ask:
                bid, ask = bid_ask
                print(f"📊 Bid: ${bid:.2f}, Ask: ${ask:.2f}, Spread: ${ask - bid:.2f}")
                
                # Use more precise limit price based on real-time data
                if side == "buy":
                    # For buying, use bid price + small premium to increase fill probability
                    limit_price = bid + 0.01
                    print(f"🔵 Buy limit price set to ${limit_price:.2f} (bid + $0.01)")
                else:
                    # For selling, use ask price - small discount to increase fill probability  
                    limit_price = ask - 0.01
                    print(f"🔴 Sell limit price set to ${limit_price:.2f} (ask - $0.01)")
            else:
                print("📈 Using mid-price for limit order")
                limit_price = current_price
        else:
            print("📡 WebSocket not available, using REST API price")
            limit_price = current_price
            
        # Simulate order placement
        print(f"📋 Order Summary:")
        print(f"   Symbol: {symbol}")
        print(f"   Side: {side.upper()}")
        print(f"   Quantity: {quantity}")
        print(f"   Limit Price: ${limit_price:.2f}")
        print(f"   Estimated Value: ${limit_price * quantity:.2f}")
        print("✅ Order would be placed successfully")
        
    def run_trading_example(self):
        """Run a sample trading session."""
        print("🚀 Starting enhanced trading example with real-time pricing...")
        
        # Wait for WebSocket connection
        time.sleep(2)
        
        # Check connection status
        if self.data_provider.real_time_pricing and self.data_provider.real_time_pricing.is_connected():
            print("✅ Real-time pricing active - orders will use WebSocket data")
        else:
            print("⚠️ Using REST API fallback for pricing")
            
        # Realistic trading scenarios (≤5 symbols for subscription limits)
        trading_scenarios = [
            ("AAPL", 10, "buy"),
            ("MSFT", 5, "sell"), 
            # Keep it to 2 symbols to stay well under limits and demonstrate real-time data flow
        ]
        
        print(f"📊 Trading session: {len(trading_scenarios)} orders across {len(set(s[0] for s in trading_scenarios))} symbols")
        
        for i, (symbol, quantity, side) in enumerate(trading_scenarios, 1):
            print(f"\n--- Order {i}/{len(trading_scenarios)} ---")
            self.place_limit_order(symbol, quantity, side)
            
            # Allow time for real-time data to accumulate
            if i < len(trading_scenarios):
                print("⏳ Waiting for real-time data to flow...")
                time.sleep(2)
            
        # Show real-time pricing statistics
        if self.data_provider.real_time_pricing:
            print(f"\n📊 Trading Session Statistics:")
            stats = self.data_provider.real_time_pricing.get_stats()
            print(f"   Quotes received: {stats.get('quotes_received', 0)}")
            print(f"   Trades received: {stats.get('trades_received', 0)}")
            print(f"   Connection errors: {stats.get('connection_errors', 0)}")
            
            # Show subscribed symbols
            subscribed = self.data_provider.real_time_pricing.get_subscribed_symbols()
            print(f"   Active subscriptions: {len(subscribed)} symbols")
            if subscribed:
                print(f"   Subscribed to: {', '.join(subscribed)}")
                
            # Check if we're getting real-time data
            total_data_points = stats.get('quotes_received', 0) + stats.get('trades_received', 0)
            if total_data_points > 0:
                print(f"   ✅ Real-time data flowing successfully ({total_data_points} data points)")
            else:
                print(f"   ⚠️ No real-time data received (check market hours or subscription status)")
            
        print("\n✅ Trading example completed successfully!")
        print("💡 Tip: For production trading, limit to ≤5 symbols to avoid subscription limits")

if __name__ == "__main__":
    try:
        trader = TradingExample()
        trader.run_trading_example()
        
    except KeyboardInterrupt:
        print("\n⚡ Trading example interrupted by user")
    except Exception as e:
        print(f"❌ Trading example failed: {e}")
        logging.exception("Trading example error")
    finally:
        print("\n🏁 Trading example finished!")
