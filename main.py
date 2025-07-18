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





def run_live_trading_bot():
    """
    Run the nuclear trading bot with Alpaca execution and send Telegram update instead of email.
    This mode generates signals, executes trades via Alpaca, and sends a Telegram notification summarizing the results.
    """
    print("🚀 NUCLEAR TRADING BOT - LIVE TRADING MODE")
    print("=" * 60)
    config = Config()
    trading_mode = 'PAPER' if config['alpaca'].get('paper', True) else 'LIVE'
    print(f"Running trading analysis with Alpaca {trading_mode} trading at {datetime.now()}")
    print()
    try:
        from core.telegram_utils import send_telegram_message
        from execution.alpaca_trader import AlpacaTradingBot
        print("📊 STEP 1: Generating Nuclear Trading Signals...")
        print("-" * 50)
        # Generate nuclear signals
        bot, signal = generate_signal()
        if not signal:
            print("❌ Failed to generate nuclear signals")
            send_telegram_message("❌ Failed to generate nuclear signals")
            return False
        print("✅ Nuclear trading signals generated successfully!")
        print()
        # Import and initialize Alpaca trading bot
        print(f"🏦 STEP 2: Connecting to Alpaca {trading_mode} Trading...")
        print("-" * 50)
        alpaca_bot = AlpacaTradingBot()
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
        msg = f"\U0001F680 Nuclear Alpaca Bot Execution\n\n"
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
        # Add order summary
        if orders:
            msg += "\nOrders Executed:\n"
            for order in orders:
                side = order.get('side')
                if hasattr(side, 'value'):
                    side = side.value
                msg += f"- {side.upper()} {order['qty']} {order['symbol']} (${order['estimated_value']:.2f})\n"
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


def main():
    """
    Main entry point for the Nuclear Trading Strategy CLI.
    Supports two modes:
      - 'bot': Only generates and logs signals.
      - 'live': Generates signals, executes trades, and sends Telegram notifications.
    """
    parser = argparse.ArgumentParser(description="Nuclear Trading Strategy - Unified Entry Point")
    parser.add_argument('mode', choices=['bot', 'live'], 
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
        elif args.mode == 'live':
            success = run_live_trading_bot()
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
