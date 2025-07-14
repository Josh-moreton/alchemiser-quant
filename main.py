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

def run_backtest(backtest_type="comprehensive"):
    """Run backtesting system"""
    print("📈 NUCLEAR STRATEGY BACKTEST")
    print("=" * 60)
    print(f"Running {backtest_type} backtest...")
    print()
    
    try:
        if backtest_type == "comprehensive":
            from backtest.simplified_comprehensive_backtest import run_comprehensive_nuclear_backtest
            results = run_comprehensive_nuclear_backtest()
        elif backtest_type == "hourly":
            from execution.hourly_execution_engine import run_hourly_analysis
            results = run_hourly_analysis()
        else:
            print(f"❌ Unknown backtest type: {backtest_type}")
            return False
            
        print(f"\n✅ {backtest_type.title()} backtest completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error running backtest: {e}")
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

def main():
    parser = argparse.ArgumentParser(description="Nuclear Trading Strategy - Unified Entry Point")
    parser.add_argument('mode', choices=['bot', 'backtest', 'dashboard', 'hourly-test'], 
                       help='Operation mode to run')
    parser.add_argument('--backtest-type', choices=['comprehensive', 'hourly'], 
                       default='comprehensive',
                       help='Type of backtest to run (only for backtest mode)')
    
    args = parser.parse_args()
    
    print("🚀 NUCLEAR TRADING STRATEGY")
    print("=" * 60)
    print(f"Mode: {args.mode}")
    print(f"Timestamp: {datetime.now()}")
    print()
    
    success = False
    
    if args.mode == 'bot':
        success = run_trading_bot()
    elif args.mode == 'backtest':
        success = run_backtest(args.backtest_type)
    elif args.mode == 'dashboard':
        success = run_dashboard()
    elif args.mode == 'hourly-test':
        success = run_backtest('hourly')
    
    if success:
        print("\n🎉 Operation completed successfully!")
        sys.exit(0)
    else:
        print("\n💥 Operation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
