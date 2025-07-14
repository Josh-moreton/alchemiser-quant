#!/usr/bin/env python3
"""
Nuclear Trading Bot - Direct Launcher
Simple way to run the live trading bot and get current signals
"""

import sys
import os

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
sys.path.insert(0, os.path.join(current_dir, 'src'))

def main():
    """Run the nuclear trading bot directly"""
    try:
        from src.core.nuclear_trading_bot import NuclearTradingBot
        
        print("🚀 NUCLEAR TRADING BOT - LIVE SIGNAL")
        print("=" * 50)
        
        # Create and run the bot
        bot = NuclearTradingBot()
        bot.run_once()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
