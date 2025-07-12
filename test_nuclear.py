#!/usr/bin/env python3
"""
Quick test of Nuclear bot
"""

from nuclear_trading_bot import NuclearTradingBot

def test_nuclear():
    print("🔬 Testing Nuclear Energy Bot...")
    
    try:
        bot = NuclearTradingBot()
        print("✅ Bot created successfully")
        
        # Test data fetching
        market_data = bot.strategy.get_market_data()
        print(f"📊 Fetched data for {len(market_data)} symbols")
        
        if market_data:
            print(f"📈 Available symbols: {list(market_data.keys())[:10]}...")
            
            # Test indicators
            indicators = bot.strategy.calculate_indicators(market_data)
            print(f"🧮 Calculated indicators for {len(indicators)} symbols")
            
            if 'SPY' in indicators:
                spy_rsi = indicators['SPY']['rsi_10']
                spy_price = indicators['SPY']['current_price']
                print(f"📊 SPY: ${spy_price:.2f}, RSI(10): {spy_rsi:.1f}")
            
            # Run full analysis
            alert = bot.run_analysis()
            if alert:
                print(f"🚨 RESULT: {alert.action} {alert.symbol} at ${alert.price:.2f}")
                print(f"   Confidence: {alert.confidence:.1%}")
                print(f"   Reason: {alert.reason}")
                return True
            else:
                print("❌ No alert generated")
                return False
        else:
            print("❌ No market data fetched")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_nuclear()
