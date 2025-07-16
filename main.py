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
        alpaca_bot = AlpacaTradingBot(paper_trading=True)
        
        # Get account info before trading
        account_info_before = alpaca_bot.get_account_info()
        
        # Display account summary before trading
        print("📋 Account Status Before Trading:")
        alpaca_bot.display_account_summary()
        
        print("⚡ STEP 3: Executing Trades Based on Nuclear Signals...")
        print("-" * 50)
        
        # Execute nuclear strategy with Alpaca
        success = alpaca_bot.execute_nuclear_strategy()
        
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
        
        # Send email notification about the execution
        print("📧 STEP 5: Sending Email Notification...")
        print("-" * 50)
        
        send_alpaca_email_notification(success, account_info_before, account_info_after, alpaca_bot)
        
        return success
        
    except Exception as e:
        print(f"❌ Error running Alpaca bot: {e}")
        traceback.print_exc()
        return False


def send_alpaca_email_notification(success, account_before, account_after, alpaca_bot):
    """Send email notification about Alpaca bot execution"""
    try:
        from core.email_utils import send_alpaca_notification
        # Get current positions for portfolio summary
        positions = alpaca_bot.get_positions()
        # Send notification using email_utils
        send_alpaca_notification(success, account_before, account_after, positions)
    except Exception as e:
        print(f"⚠️ Error sending email notification: {e}")
        traceback.print_exc()


def run_email_bot(test_mode=False):
    """Run the nuclear trading bot and send an email notification with the signal."""
    print("🚀 NUCLEAR TRADING BOT - EMAIL MODE")
    print("=" * 60)
    print(f"Running live trading analysis with email notifications at {datetime.now()}")
    print()
    try:
        from core.nuclear_trading_bot import NuclearTradingBot
        from core.email_utils import send_signal_notification
        
        # Run the bot and get the signal
        bot = NuclearTradingBot()
        print("Fetching live market data and generating signal...")
        print()
        
        signal = bot.run_once()
        
        if not signal:
            print("❌ Failed to generate nuclear signals")
            return False
            
        print("✅ Nuclear trading signals generated successfully!")
        print()
        
        # Send email notification using email_utils
        email_sent = send_signal_notification(signal, test_mode)
        
        return email_sent
        
    except Exception as e:
        print(f"❌ Error running email bot: {e}")
        traceback.print_exc()
        return False


def run_alpaca_telegram_bot():
    """Run the nuclear trading bot with Alpaca execution and send Telegram update instead of email."""
    print("🚀 NUCLEAR TRADING BOT - ALPACA TELEGRAM MODE")
    print("=" * 60)
    print(f"Running live trading analysis with Alpaca paper trading at {datetime.now()}")
    print()
    
    try:
        # Import and run the core nuclear trading bot first to generate signals
        from core.nuclear_trading_bot import NuclearTradingBot
        from core.telegram_utils import send_telegram_message
        
        print("📊 STEP 1: Generating Nuclear Trading Signals...")
        print("-" * 50)
        
        # Generate nuclear signals
        bot = NuclearTradingBot()
        print("Fetching live market data and generating signal...")
        print()
        
        signal = bot.run_once()
        
        if not signal:
            print("❌ Failed to generate nuclear signals")
            send_telegram_message("❌ Failed to generate nuclear signals")
            return False
        
        print("✅ Nuclear trading signals generated successfully!")
        print()
        
        # Import and initialize Alpaca trading bot
        print("🏦 STEP 2: Connecting to Alpaca Paper Trading...")
        print("-" * 50)
        
        from execution.alpaca_trader import AlpacaTradingBot
        
        # Initialize bot with paper trading
        alpaca_bot = AlpacaTradingBot(paper_trading=True)
        
        # Get account info before trading
        account_info_before = alpaca_bot.get_account_info()
        
        # Display account summary before trading
        print("📋 Account Status Before Trading:")
        alpaca_bot.display_account_summary()
        
        print("⚡ STEP 3: Executing Trades Based on Nuclear Signals...")
        print("-" * 50)
        
        # Execute nuclear strategy with Alpaca
        success = alpaca_bot.execute_nuclear_strategy()
        
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
        
        try:
            positions = alpaca_bot.get_positions()
            msg = f"🚀 Nuclear Alpaca Bot Execution\n\n"
            msg += f"Status: {'✅ Success' if success else '❌ Failed'}\n"
            msg += f"Portfolio Value Before: ${account_info_before.get('portfolio_value', 0):,.2f}\n"
            msg += f"Portfolio Value After:  ${account_info_after.get('portfolio_value', 0):,.2f}\n"
            msg += f"Cash Before: ${account_info_before.get('cash', 0):,.2f}\n"
            msg += f"Cash After:  ${account_info_after.get('cash', 0):,.2f}\n"
            
            if positions:
                msg += "\nPositions:\n"
                for symbol, pos in positions.items():
                    qty = pos.get('qty', 0)
                    price = pos.get('current_price', 0)
                    market_value = pos.get('market_value', 0)
                    msg += f"- {symbol}: {qty} @ ${price:.2f} = ${market_value:.2f}\n"
            
            send_telegram_message(msg)
            print("✅ Telegram notification sent successfully!")
            
        except Exception as e:
            print(f"⚠️ Error sending Telegram notification: {e}")
        
        return success
        
    except Exception as e:
        print(f"❌ Error running Alpaca Telegram bot: {e}")
        traceback.print_exc()
        return False


def main():
    parser = argparse.ArgumentParser(description="Nuclear Trading Strategy - Unified Entry Point")
    parser.add_argument('mode', choices=['bot', 'email', 'alpaca', 'telegram'], 
                       help='Operation mode to run')
    parser.add_argument('--test-email', action='store_true', help='Always send email in email mode (for testing)')

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
            success = run_email_bot(test_mode=args.test_email)
        elif args.mode == 'alpaca':
            success = run_alpaca_bot()
        elif args.mode == 'telegram':
            success = run_alpaca_telegram_bot()
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
