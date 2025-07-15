#!/usr/bin/env python3
"""
Nuclear Trading Strategy - Main Entry Point
Unified launcher for all nuclear trading operations
"""

import sys
import os
import argparse
from datetime import datetime

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def run_trading_bot():
    """Run the main nuclear trading bot for live signals"""
    print("🚀 NUCLEAR TRADING BOT - LIVE MODE")
    print("=" * 60)
    print(f"Running live trading analysis at {datetime.now()}")
    print()
    
    try:
        from core.nuclear_trading_bot import NuclearTradingBot
        
        # Create and run the bot
        bot = NuclearTradingBot()
        print("Fetching live market data and generating signal...")
        print()
        
        signal = bot.run_once()
        
        if signal:
            print()
            print("✅ Signal generated successfully!")
            print(f"📁 Alert logged to: data/logs/nuclear_alerts.json")
        else:
            print()
            print("⚠️  No clear signal generated")
        
        return True
        
    except Exception as e:
        print(f"❌ Error running trading bot: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_dashboard():
    """Launch the nuclear trading dashboard"""
    print("📊 NUCLEAR TRADING DASHBOARD")
    print("=" * 60)
    print("Starting dashboard server...")
    print()
    
    try:
        from core.nuclear_dashboard import run_dashboard_server
        run_dashboard_server()
        return True
        
    except Exception as e:
        print(f"❌ Error running dashboard: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_alpaca_bot():
    """Run the nuclear trading bot with Alpaca execution"""
    print("🚀 NUCLEAR TRADING BOT - ALPACA EXECUTION MODE")
    print("=" * 60)
    print(f"Running live trading analysis with Alpaca paper trading at {datetime.now()}")
    print()
    
    try:
        # Import and run the core nuclear trading bot first to generate signals
        from core.nuclear_trading_bot import NuclearTradingBot
        
        print("📊 STEP 1: Generating Nuclear Trading Signals...")
        print("-" * 50)
        
        # Generate nuclear signals
        bot = NuclearTradingBot()
        print("Fetching live market data and generating signal...")
        print()
        
        signal = bot.run_once()
        
        if not signal:
            print("❌ Failed to generate nuclear signals")
            return False
        
        print("✅ Nuclear trading signals generated successfully!")
        print()
        
        # Import and initialize Alpaca trading bot
        print("🏦 STEP 2: Connecting to Alpaca Paper Trading...")
        print("-" * 50)
        
        from execution.alpaca_trader import AlpacaTradingBot
        
        # Initialize bot with paper trading
        bot = AlpacaTradingBot(paper_trading=True)
        
        # Display account summary before trading
        print("📋 Account Status Before Trading:")
        bot.display_account_summary()
        
        print("⚡ STEP 3: Executing Trades Based on Nuclear Signals...")
        print("-" * 50)
        
        # Execute nuclear strategy with Alpaca
        success = bot.execute_nuclear_strategy()
        
        if success:
            print("✅ Trade execution completed successfully!")
        else:
            print("❌ Trade execution failed!")
        
        print()
        print("📊 STEP 4: Final Account Status...")
        print("-" * 50)
        
        # Display updated account summary
        bot.display_account_summary()
        
        print()
        print("=" * 70)
        print("🎯 NUCLEAR ALPACA BOT EXECUTION COMPLETE")
        print("=" * 70)
        print()
        
        return success
        
    except Exception as e:
        print(f"❌ Error running Alpaca bot: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_email_bot():
    """Run the nuclear trading bot with email notifications"""
    print("🚀 NUCLEAR TRADING BOT - EMAIL MODE")
    print("=" * 60)
    print(f"Running live trading analysis with email notifications at {datetime.now()}")
    print()
    
    try:
        from core.nuclear_signal_email import main as email_main
        
        # Run the email bot
        print("📧 Starting email-enabled nuclear trading bot...")
        email_main()
        
        return True
        
    except Exception as e:
        print(f"❌ Error running email bot: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description="Nuclear Trading Strategy - Unified Entry Point")
    parser.add_argument('mode', choices=['bot', 'email', 'alpaca', 'dashboard'], 
                       help='Operation mode to run')

    args = parser.parse_args()

    print("🚀 NUCLEAR TRADING STRATEGY")
    print("=" * 60)
    print(f"Mode: {args.mode}")
    print(f"Timestamp: {datetime.now()}")
    success = False
    try:
        if args.mode == 'bot':
            success = run_trading_bot()
        elif args.mode == 'email':
            success = run_email_bot()
        elif args.mode == 'alpaca':
            success = run_alpaca_bot()
        elif args.mode == 'dashboard':
            success = run_dashboard()
    except Exception as e:
        print(f"\n💥 Operation failed due to error: {e}")
        import traceback
        traceback.print_exc()
        success = False
    if success:
        print("\n🎉 Operation completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Operation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
