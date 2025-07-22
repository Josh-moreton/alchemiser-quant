#!/usr/bin/env python3
"""
Nuclear Trading Strategy - Main Entry Point
Unified launcher for all nuclear trading operations

This file is a thin runner. It only handles CLI, orchestration, and logging.
All business logic is delegated to orchestrator and service classes in core/.
No business logic should be added here.
"""

# Standard library imports
import argparse
from datetime import datetime
import traceback
import sys
import os
from core.config import Config


def generate_signal():
    """
    Helper function to create and run the NuclearTradingBot, returning the bot and the generated signal.
    Used to avoid code duplication in both bot and live trading modes.
    """
    from core.nuclear_trading_bot import NuclearTradingBot
    bot = NuclearTradingBot()
    print("Fetching live market data and generating signal...")
    print()
    signal = bot.run_once()
    return bot, signal

def run_trading_bot():
    """
    Run the main nuclear trading bot for live signals.
    This mode only generates signals and logs them, without executing trades or sending notifications.
    """
    print("🚀 NUCLEAR TRADING BOT - LIVE MODE")
    print("=" * 60)
    print(f"Running live trading analysis at {datetime.now()}")
    print()
    try:
        bot, signal = generate_signal()
        if signal:
            print()
            print("✅ Signal generated successfully!")
            config = Config()
            log_path = config['logging']['nuclear_alerts_json']
            print(f"📁 Alert logged to: {log_path}")
        else:
            print()
            print("⚠️  No clear signal generated")
        return True
    except Exception as e:
        print(f"❌ Error running trading bot: {e}")
        traceback.print_exc()
        return False





def run_live_trading_bot(ignore_market_hours=False):
    """
    Run the nuclear trading bot with Alpaca execution and send Telegram update instead of email.
    This mode generates signals, executes trades via Alpaca, and sends a Telegram notification summarizing the results.
    
    Args:
        ignore_market_hours (bool): If True, ignore market hours and run during closed market (for testing)
    """
    print("🚀 NUCLEAR TRADING BOT - LIVE TRADING MODE")
    print("=" * 60)
    print(f"Running trading analysis with Alpaca LIVE trading at {datetime.now()}")
    print("[INFO] Initializing Telegram and Alpaca modules...")
    print("[INFO] Importing send_telegram_message and AlpacaTradingBot. This may take a few seconds if cold starting.")
    print()
    try:
        from core.telegram_utils import send_telegram_message, build_execution_report
        from execution.alpaca_trader import AlpacaTradingBot, is_market_open
        print("📊 STEP 1: Checking Market Status...")
        print("-" * 50)
        alpaca_bot = AlpacaTradingBot(paper_trading=False)  # Explicitly set to live trading
        
        # Check if we should ignore market hours (from command line argument)
        if not ignore_market_hours and not is_market_open(alpaca_bot.trading_client):
            print("❌ Market is CLOSED. No trades will be placed.")
            send_telegram_message("❌ Market is CLOSED. No trades will be placed.")
            return False
        
        if ignore_market_hours:
            print("⚠️  IGNORING MARKET HOURS (Testing Mode)")
            send_telegram_message("⚠️  IGNORING MARKET HOURS (Testing Mode)")
        else:
            print("✅ Market is OPEN. Proceeding with trading.")
        print()
        print("📊 STEP 2: Generating Nuclear Trading Signals...")
        print("-" * 50)
        # Generate nuclear signals
        bot, signal = generate_signal()
        if not signal:
            print("❌ Failed to generate nuclear signals")
            send_telegram_message("❌ Failed to generate nuclear signals")
            return False
        print("✅ Nuclear trading signals generated successfully!")
        print()
        # Get account info before trading
        account_info_before = alpaca_bot.get_account_info()
        # Display account summary before trading
        print("📋 Account Status Before Trading:")
        alpaca_bot.display_account_summary()
        print("⚡ STEP 3: Executing Trades Based on Nuclear Signals...")
        print("-" * 50)
        # Execute nuclear strategy and capture orders
        orders = []
        success = False
        try:
            # Patch: capture orders from rebalance_portfolio
            # We'll monkeypatch the bot to store orders for reporting
            orig_rebalance = alpaca_bot.rebalance_portfolio
            def rebalance_and_capture(*args, **kwargs):
                result = orig_rebalance(*args, **kwargs)
                nonlocal orders
                orders = result
                return result
            alpaca_bot.rebalance_portfolio = rebalance_and_capture
            success = alpaca_bot.execute_nuclear_strategy()
        finally:
            alpaca_bot.rebalance_portfolio = orig_rebalance
        if success:
            print("✅ Trade execution completed successfully!")
        else:
            print("❌ Trade execution failed!")
        print()
        print("📊 STEP 4: Final Account Status...")
        print("-" * 50)
        # Get account info after trading
        account_info_after = alpaca_bot.get_account_info()
        # Display updated account summary
        alpaca_bot.display_account_summary()
        print()
        print("=" * 70)
        print("🎯 NUCLEAR ALPACA BOT EXECUTION COMPLETE")
        print("=" * 70)
        print()
        # Send Telegram notification about the execution
        print("📲 STEP 5: Sending Telegram Notification...")
        print("-" * 50)
        positions = alpaca_bot.get_positions()
        msg = build_execution_report(
            mode="LIVE",
            success=success,
            account_before=account_info_before,
            account_after=account_info_after,
            positions=positions,
            orders=orders,
            signal=signal,
        )
        try:
            send_telegram_message(msg)
            print("✅ Telegram notification sent successfully!")
        except Exception as e:
            print(f"⚠️ Error sending Telegram notification: {e}")
        return success
    except Exception as e:
        print(f"❌ Error running Alpaca Telegram bot: {e}")
        traceback.print_exc()
        return False


def run_paper_trading_bot(ignore_market_hours=False):
    """
    Run the nuclear trading bot with Alpaca PAPER trading execution and send Telegram update.
    This mode generates signals, executes trades via Alpaca PAPER trading, and sends a Telegram notification summarizing the results.
    
    Args:
        ignore_market_hours (bool): If True, ignore market hours and run during closed market (for testing)
    """
    print("🚀 NUCLEAR TRADING BOT - PAPER TRADING MODE")
    print("=" * 60)
    print(f"Running trading analysis with Alpaca PAPER trading at {datetime.now()}")
    print()
    try:
        from core.telegram_utils import send_telegram_message, build_execution_report
        from execution.alpaca_trader import AlpacaTradingBot, is_market_open
        print("📊 STEP 1: Checking Market Status...")
        print("-" * 50)
        
        # Initialize with paper trading enabled
        alpaca_bot = AlpacaTradingBot(paper_trading=True)
        
        # Check if we should ignore market hours (from command line argument)
        if not ignore_market_hours and not is_market_open(alpaca_bot.trading_client):
            print("❌ Market is CLOSED. No trades will be placed.")
            send_telegram_message("❌ Market is CLOSED. No trades will be placed.")
            return False
        
        if ignore_market_hours:
            print("⚠️  IGNORING MARKET HOURS (Testing Mode)")
            send_telegram_message("⚠️  IGNORING MARKET HOURS (Testing Mode)")
        else:
            print("✅ Market is OPEN. Proceeding with paper trading.")
        print()
        
        print("📊 STEP 2: Generating Nuclear Trading Signals...")
        print("-" * 50)
        # Generate nuclear signals
        bot, signal = generate_signal()
        if not signal:
            print("❌ Failed to generate nuclear signals")
            send_telegram_message("❌ Failed to generate nuclear signals")
            return False
        print("✅ Nuclear trading signals generated successfully!")
        print()
        
        print("📋 Account Status Before Trading:")
        print()
        # Get account info before trading
        account_info_before = alpaca_bot.get_account_info()
        # Display account summary
        alpaca_bot.display_account_summary()
        
        print("⚡ STEP 3: Executing Paper Trades Based on Nuclear Signals...")
        print("-" * 50)
        
        # Execute nuclear strategy via Alpaca paper trading
        success = alpaca_bot.execute_nuclear_strategy()
        orders = alpaca_bot.read_nuclear_signals()  # Get executed orders
        
        if success:
            print("✅ Paper trade execution completed successfully!")
        else:
            print("❌ Paper trade execution failed!")
        print()
        
        print("📊 STEP 4: Final Account Status...")
        print("-" * 50)
        # Get account info after trading
        account_info_after = alpaca_bot.get_account_info()
        # Display updated account summary
        alpaca_bot.display_account_summary()
        print()
        
        print("=" * 70)
        print("🎯 NUCLEAR PAPER TRADING BOT EXECUTION COMPLETE")
        print("=" * 70)
        print()
        
        # Send Telegram notification about the execution
        print("📲 STEP 5: Sending Telegram Notification...")
        print("-" * 50)
        positions = alpaca_bot.get_positions()
        msg = build_execution_report(
            mode="PAPER",
            success=success,
            account_before=account_info_before,
            account_after=account_info_after,
            positions=positions,
            orders=orders,
            signal=signal,
        )

        try:
            send_telegram_message(msg)
            print("✅ Telegram notification sent successfully!")
        except Exception as e:
            print(f"⚠️ Error sending Telegram notification: {e}")
        
        return success
    except Exception as e:
        print(f"❌ Error running Paper Trading bot: {e}")
        traceback.print_exc()
        return False


def main():
    """
    Main entry point for the Nuclear Trading Strategy CLI.
    Supports three modes:
      - 'bot': Only generates and logs signals.
      - 'live': Generates signals, executes trades, and sends Telegram notifications.
      - 'paper': Generates signals, executes paper trades, and sends Telegram notifications.
    """
    parser = argparse.ArgumentParser(description="Nuclear Trading Strategy - Unified Entry Point")
    parser.add_argument('mode', choices=['bot', 'live', 'paper'], 
                       help='Operation mode to run: bot (signals only), live (real trading), paper (paper trading)')
    parser.add_argument('--ignore-market-hours', action='store_true',
                       help='Ignore market hours and run during closed market (for testing)')

    args = parser.parse_args()

    print("🚀 NUCLEAR TRADING STRATEGY")
    print("=" * 60)
    print(f"Mode: {args.mode}")
    print(f"Timestamp: {datetime.now()}")
    success = False
    try:
        if args.mode == 'bot':
            success = run_trading_bot()
        elif args.mode == 'live':
            success = run_live_trading_bot(ignore_market_hours=args.ignore_market_hours)
        elif args.mode == 'paper':
            success = run_paper_trading_bot(ignore_market_hours=args.ignore_market_hours)
    except Exception as e:
        print(f"\n💥 Operation failed due to error: {e}")
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
