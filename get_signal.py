#!/usr/bin/env python3
"""
Quick Nuclear Signal - Get Current Live Trading Signal
Simplest way to run the nuclear strategy and get current recommendations
"""

import sys
import os

# Add paths for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'src', 'core'))

if __name__ == "__main__":
    try:
        from nuclear_trading_bot import NuclearTradingBot
        
        print("🚀 NUCLEAR ENERGY TRADING SIGNAL")
        print("=" * 40)
        print("Fetching live market data and generating signal...")
        print()
        
        # Create and run bot
        bot = NuclearTradingBot()
        signal = bot.run_once()
        
        if signal:
            print()
            print("✅ Signal generated successfully!")
            print(f"📁 Logged to: data/logs/nuclear_alerts.json")
        else:
            print()
            print("⚠️  No signal generated")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
