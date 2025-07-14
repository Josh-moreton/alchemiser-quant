#!/usr/bin/env python3
"""
Nuclear Trading Bot with Alpaca Execution
Generates nuclear trading signals and automatically executes them via Alpaca paper trading
"""

import sys
import os
import time
import logging
from datetime import datetime

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.nuclear_trading_bot import NuclearTradingBot
from execution.alpaca_trader import AlpacaTradingBot

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/logs/nuclear_alpaca_execution.log'),
        logging.StreamHandler()
    ]
)

def run_nuclear_alpaca_bot():
    """Run the complete nuclear trading bot with Alpaca execution"""
    try:
        print("🚀 NUCLEAR TRADING BOT WITH ALPACA EXECUTION")
        print("=" * 70)
        print(f"Started at: {datetime.now()}")
        print()
        
        # Step 1: Generate Nuclear Trading Signals
        print("📊 STEP 1: Generating Nuclear Trading Signals...")
        print("-" * 50)
        
        nuclear_bot = NuclearTradingBot()
        signals = nuclear_bot.run_once()
        
        if not signals:
            print("❌ No trading signals generated. Exiting.")
            return False
        
        print("✅ Nuclear trading signals generated successfully!")
        print()
        
        # Wait a moment for signals to be written to file
        time.sleep(2)
        
        # Step 2: Initialize Alpaca Trading Bot
        print("🏦 STEP 2: Connecting to Alpaca Paper Trading...")
        print("-" * 50)
        
        alpaca_bot = AlpacaTradingBot(paper_trading=True)
        
        # Display account info before trading
        print("📋 Account Status Before Trading:")
        alpaca_bot.display_account_summary()
        print()
        
        # Step 3: Execute trades based on signals
        print("⚡ STEP 3: Executing Trades Based on Nuclear Signals...")
        print("-" * 50)
        
        success = alpaca_bot.execute_nuclear_strategy()
        
        if success:
            print("✅ Trade execution completed successfully!")
        else:
            print("❌ Trade execution failed!")
        
        print()
        
        # Step 4: Display final account status
        print("📊 STEP 4: Final Account Status...")
        print("-" * 50)
        
        alpaca_bot.display_account_summary()
        
        print("\n" + "=" * 70)
        print("🎯 NUCLEAR ALPACA BOT EXECUTION COMPLETE")
        print("=" * 70)
        
        return success
        
    except Exception as e:
        logging.error(f"Error in nuclear alpaca bot: {e}")
        print(f"❌ Error: {e}")
        return False

def run_continuous_monitoring(interval_minutes=60):
    """Run continuous monitoring and execution"""
    try:
        print("🔄 CONTINUOUS NUCLEAR ALPACA MONITORING")
        print("=" * 70)
        print(f"Checking every {interval_minutes} minutes...")
        print("Press Ctrl+C to stop")
        print()
        
        while True:
            try:
                print(f"\n⏰ Running at {datetime.now()}")
                success = run_nuclear_alpaca_bot()
                
                if success:
                    print(f"✅ Cycle completed successfully")
                else:
                    print(f"❌ Cycle failed")
                
                print(f"💤 Sleeping for {interval_minutes} minutes...")
                time.sleep(interval_minutes * 60)
                
            except KeyboardInterrupt:
                print("\n👋 Stopping continuous monitoring...")
                break
            except Exception as e:
                logging.error(f"Error in monitoring cycle: {e}")
                print(f"❌ Cycle error: {e}")
                print(f"💤 Sleeping for {interval_minutes} minutes before retry...")
                time.sleep(interval_minutes * 60)
        
    except Exception as e:
        logging.error(f"Error in continuous monitoring: {e}")
        print(f"❌ Monitoring error: {e}")

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Nuclear Trading Bot with Alpaca Execution')
    parser.add_argument('--continuous', action='store_true', 
                       help='Run in continuous monitoring mode')
    parser.add_argument('--interval', type=int, default=60,
                       help='Interval in minutes for continuous mode (default: 60)')
    
    args = parser.parse_args()
    
    if args.continuous:
        run_continuous_monitoring(args.interval)
    else:
        run_nuclear_alpaca_bot()

if __name__ == "__main__":
    main()
