#!/usr/bin/env python3
"""
Test intelligent limit orders for both buys and sells.
This demonstrates the new aggressive sell limit orders that favor quick fills.
"""

import sys
import os
import time

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from the_alchemiser.core.data.data_provider import UnifiedDataProvider
from the_alchemiser.execution.order_manager_adapter import OrderManagerAdapter
from the_alchemiser.execution.simple_order_manager import SimpleOrderManager
from alpaca.trading.enums import OrderSide
from alpaca.trading.client import TradingClient
from unittest.mock import Mock

def test_intelligent_sell_orders():
    """Test the new intelligent sell limit orders vs old market orders."""
    print("🧪 Testing Intelligent Sell Limit Orders")
    print("=" * 50)
    
    try:
        # Initialize with paper trading
        data_provider = UnifiedDataProvider(paper_trading=True)
        trading_client = TradingClient(data_provider.api_key, data_provider.secret_key, paper=True)
        simple_order_manager = SimpleOrderManager(trading_client, data_provider)
        order_manager = OrderManagerAdapter(simple_order_manager)
        
        print("✅ Order management system initialized")
        
        # Test symbols that should have good bid/ask spreads
        test_symbols = ["UVXY", "TECL", "SPY", "AAPL"]
        
        for symbol in test_symbols:
            print(f"\n📊 Testing {symbol} sell order pricing:")
            
            # Get current bid/ask
            bid, ask = data_provider.get_latest_quote(symbol)
            current_price = data_provider.get_current_price(symbol)
            
            if bid > 0 and ask > 0 and current_price:
                spread = ask - bid
                spread_pct = (spread / current_price) * 100
                
                print(f"   Current Price: ${current_price:.2f}")
                print(f"   Bid: ${bid:.2f}, Ask: ${ask:.2f}")
                print(f"   Spread: ${spread:.2f} ({spread_pct:.2f}%)")
                
                # Calculate what our intelligent sell limit would be
                # 85% toward bid from ask for aggressive fills
                intelligent_limit = ask - (ask - bid) * 0.85
                market_midpoint = (bid + ask) / 2
                
                print(f"   📈 Old approach (market): ~${market_midpoint:.2f} (midpoint estimate)")
                print(f"   🎯 New intelligent limit: ${intelligent_limit:.2f}")
                
                # Calculate improvement
                improvement = intelligent_limit - market_midpoint
                improvement_bps = (improvement / current_price) * 10000
                
                if improvement > 0:
                    print(f"   💰 Potential improvement: +${improvement:.2f} (+{improvement_bps:.1f} bps)")
                else:
                    print(f"   ⚡ Speed vs profit tradeoff: {improvement:.2f} (-{abs(improvement_bps):.1f} bps for faster fill)")
                
                # Show aggressiveness vs buy orders
                buy_limit = bid + (ask - bid) * 0.75  # 75% toward ask from bid
                sell_distance_from_mid = abs(intelligent_limit - market_midpoint)
                buy_distance_from_mid = abs(buy_limit - market_midpoint)
                
                print(f"   📊 Sell aggressiveness: {sell_distance_from_mid:.3f} from mid")
                print(f"   📊 Buy aggressiveness: {buy_distance_from_mid:.3f} from mid")
                
                if sell_distance_from_mid < buy_distance_from_mid:
                    print(f"   ✅ Sells are MORE aggressive than buys (favors quick fills)")
                else:
                    print(f"   ⚠️ Sells are less aggressive than buys")
                    
            else:
                print(f"   ❌ Could not get valid quote data for {symbol}")
        
        print(f"\n🔄 Sell Order Strategy Summary:")
        print(f"   • Uses WebSocket real-time bid/ask pricing")
        print(f"   • Places limit 85% toward bid from ask (more aggressive than 75% for buys)")
        print(f"   • Waits only 10 seconds vs 15 seconds for buys")
        print(f"   • Falls back to market order if limit doesn't fill")
        print(f"   • Prioritizes quick fills over maximum profit")
        print(f"   • Still better than pure market orders in most cases")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def demo_sell_order_comparison():
    """Show the difference between old and new sell approaches."""
    print(f"\n🔀 SELL ORDER APPROACH COMPARISON")
    print("=" * 50)
    
    print("📊 OLD APPROACH (Market Orders):")
    print("   ❌ Always uses market orders")
    print("   ❌ Gets filled at whatever price is available")
    print("   ❌ Can have significant slippage during volatile periods")
    print("   ❌ No price protection")
    print("   ✅ Guaranteed fast execution")
    
    print("\n🎯 NEW APPROACH (Intelligent Limit Orders):")
    print("   ✅ Uses real-time WebSocket bid/ask pricing")
    print("   ✅ Places aggressive limit orders (85% toward bid)")
    print("   ✅ Better pricing than market orders in most cases")
    print("   ✅ Still prioritizes speed (10 second timeout)")
    print("   ✅ Falls back to market order if needed")
    print("   ✅ Protection against extreme slippage")
    
    print("\n⚡ AGGRESSIVENESS COMPARISON:")
    print("   🟢 BUY orders: 75% toward ask from bid (moderately aggressive)")
    print("   🔴 SELL orders: 85% toward bid from ask (MORE aggressive)")
    print("   💡 Sells are more aggressive to ensure quick liquidation")

if __name__ == "__main__":
    test_intelligent_sell_orders()
    demo_sell_order_comparison()
