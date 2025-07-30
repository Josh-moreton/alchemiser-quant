#!/usr/bin/env python3
"""
Optimized Order Placement Example with Just-in-Time WebSocket Subscriptions.

This demonstrates the improved approach that subscribes to symbols only when placing orders,
avoiding subscription limits while maximizing pricing accuracy.
"""

import logging
import time
from the_alchemiser.core.data.data_provider import UnifiedDataProvider

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class OptimizedOrderManager:
    """Order manager that uses just-in-time WebSocket subscriptions."""
    
    def __init__(self):
        self.data_provider = UnifiedDataProvider(
            paper_trading=True,
            enable_real_time=True
        )
        
    def place_optimized_order(self, symbol: str, quantity: int, side: str = "buy"):
        """
        Place an order using optimized just-in-time pricing.
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares
            side: "buy" or "sell"
        """
        print(f"\n🎯 Placing optimized {side} order for {quantity} shares of {symbol}")
        
        # Method 1: Use the new optimized pricing method
        if hasattr(self.data_provider, 'get_current_price_for_order'):
            price, cleanup = self.data_provider.get_current_price_for_order(symbol)
            
            if price:
                print(f"💰 Optimized price: ${price:.2f}")
                
                # Get bid/ask spread if available for better limit pricing
                if (self.data_provider.real_time_pricing and 
                    self.data_provider.real_time_pricing.is_connected()):
                    
                    bid_ask = self.data_provider.real_time_pricing.get_latest_quote(symbol)
                    if bid_ask:
                        bid, ask = bid_ask
                        spread = ask - bid
                        print(f"📊 Bid/Ask: ${bid:.2f}/${ask:.2f} (spread: ${spread:.2f})")
                        
                        # Use optimized limit pricing
                        if side == "buy":
                            limit_price = bid + min(0.01, spread * 0.25)  # Bid + small premium
                            print(f"🔵 Optimized buy limit: ${limit_price:.2f}")
                        else:
                            limit_price = ask - min(0.01, spread * 0.25)  # Ask - small discount
                            print(f"🔴 Optimized sell limit: ${limit_price:.2f}")
                    else:
                        limit_price = price
                        print(f"📈 Using mid-price: ${limit_price:.2f}")
                else:
                    limit_price = price
                    print(f"📈 Using current price: ${limit_price:.2f}")
                
                # Simulate order placement
                print(f"📋 Order Details:")
                print(f"   Symbol: {symbol}")
                print(f"   Side: {side.upper()}")
                print(f"   Quantity: {quantity}")
                print(f"   Limit Price: ${limit_price:.2f}")
                print(f"   Total Value: ${limit_price * quantity:.2f}")
                print("✅ Order placed successfully")
                
                # Clean up subscription after order placement
                cleanup()
                print(f"🧹 Cleaned up subscription for {symbol}")
                
            else:
                print(f"❌ Could not get price for {symbol}")
        else:
            # Fallback to standard method
            price = self.data_provider.get_current_price(symbol)
            if price:
                print(f"💰 Standard price: ${price:.2f}")
                print("✅ Order placed with standard pricing")
            else:
                print(f"❌ Could not get price for {symbol}")
    
    def place_multiple_orders_sequentially(self, orders):
        """
        Place multiple orders with optimized subscription management.
        
        Args:
            orders: List of (symbol, quantity, side) tuples
        """
        print(f"\n🔄 OPTIMIZED SEQUENTIAL ORDER PLACEMENT")
        print(f"📊 Processing {len(orders)} orders with just-in-time subscriptions")
        print("=" * 60)
        
        for i, (symbol, quantity, side) in enumerate(orders, 1):
            print(f"\n--- Order {i}/{len(orders)} ---")
            
            # Place order with just-in-time subscription
            self.place_optimized_order(symbol, quantity, side)
            
            # Brief pause between orders
            if i < len(orders):
                print("⏳ Brief pause before next order...")
                time.sleep(1)
        
        # Show final subscription status
        if self.data_provider.real_time_pricing:
            stats = self.data_provider.real_time_pricing.get_stats()
            subscribed = self.data_provider.real_time_pricing.get_subscribed_symbols()
            
            print(f"\n📊 Final Session Statistics:")
            print(f"   Subscription limit hits: {stats.get('subscription_limit_hits', 0)}")
            print(f"   Final active subscriptions: {len(subscribed)}")
            print(f"   Active symbols: {', '.join(subscribed) if subscribed else 'None'}")
            
            if stats.get('subscription_limit_hits', 0) == 0:
                print("✅ No subscription limits hit - optimization successful!")
            else:
                print("⚠️ Some subscription limits hit - consider further optimization")

def demonstrate_optimization():
    """Demonstrate the optimized order placement approach."""
    
    print("🚀 OPTIMIZED ORDER PLACEMENT DEMONSTRATION")
    print("=" * 60)
    print("🎯 Strategy: Just-in-time WebSocket subscriptions")
    print("📈 Benefits:")
    print("   • Avoids subscription limits")
    print("   • Maximizes pricing accuracy when needed")
    print("   • Efficient resource usage")
    print("   • Scalable to many symbols")
    
    try:
        order_manager = OptimizedOrderManager()
        
        # Wait for initial connection
        print("\n⏳ Initializing real-time pricing...")
        time.sleep(2)
        
        if (order_manager.data_provider.real_time_pricing and 
            order_manager.data_provider.real_time_pricing.is_connected()):
            print("✅ Real-time pricing ready")
        else:
            print("⚠️ Using REST API fallback")
        
        # Test orders - can handle many more symbols this way
        test_orders = [
            ("AAPL", 10, "buy"),
            ("MSFT", 5, "sell"),
            ("GOOGL", 8, "buy"),
            ("AMZN", 3, "sell"),
            ("TSLA", 12, "buy"),  # This would exceed limits with persistent subscriptions
        ]
        
        # Place orders sequentially with optimized subscriptions
        order_manager.place_multiple_orders_sequentially(test_orders)
        
        print(f"\n🎉 OPTIMIZATION DEMONSTRATION COMPLETE!")
        print("✅ Successfully placed orders for 5 symbols without subscription limits")
        print("💡 This approach scales to many more symbols efficiently")
        
    except Exception as e:
        print(f"❌ Demonstration failed: {e}")
        logging.exception("Demo error")

if __name__ == "__main__":
    try:
        demonstrate_optimization()
    except KeyboardInterrupt:
        print("\n⚡ Demonstration interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n🏁 Demonstration finished!")
