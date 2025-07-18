#!/usr/bin/env python3
"""
Nuclear Trading Strategy - Main Entry Point
Unified launcher for all nuclear trading operations

This file is a thin runner. It only handles CLI, orchestration, and logging.
All business logic is delegated to orchestrator and service classes in core/.
No business logic should be added here.
"""

import argparse
from datetime import datetime
import traceback
import sys
def run_alpaca_trading_bot(paper_trading=False, ignore_market_hours=False):
    """
    Run the nuclear trading bot with Alpaca execution and send Telegram update instead of email.
    This mode generates signals, executes trades via Alpaca, and sends a Telegram notification summarizing the results.
    """
    mode_str = 'PAPER' if paper_trading else 'LIVE'
    print(f"🚀 NUCLEAR TRADING BOT - {mode_str} TRADING MODE")
    print("=" * 60)
    print(f"Running trading analysis with Alpaca {mode_str} trading at {datetime.now()}")
    print()
    try:
        from core.telegram_utils import send_telegram_message
        from execution.alpaca_trader import AlpacaTradingBot, is_market_open
        print("📊 STEP 1: Checking Market Status...")
        print("-" * 50)
        alpaca_bot = AlpacaTradingBot(paper_trading=paper_trading)
        market_open = is_market_open(alpaca_bot.trading_client)
        if not market_open and not ignore_market_hours:
            print("❌ Market is CLOSED. No trades will be placed.")
            send_telegram_message("❌ Market is CLOSED. No trades will be placed.")
            return False
        if not market_open and ignore_market_hours:
            print("⚠️ Market is CLOSED, but running anyway due to --ignore-market-hours flag.")
        else:
            print("✅ Market is OPEN. Proceeding with trading.")
        print()
        print("📊 STEP 2: Generating Nuclear Trading Signals...")
        print("-" * 50)
        # Generate nuclear signals
        from core.nuclear_trading_bot import NuclearTradingBot
        bot = NuclearTradingBot()
        signal = bot.run_once()
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
    parser.add_argument('mode', choices=['bot', 'live', 'paper'], 
                       help='Operation mode to run')
    parser.add_argument('--ignore-market-hours', action='store_true',
                        help='Ignore market open check and run trading logic regardless of market hours (live/paper modes only)')

    args = parser.parse_args()

    print("🚀 NUCLEAR TRADING STRATEGY")
    print("=" * 60)
    print(f"Mode: {args.mode}")
    print(f"Timestamp: {datetime.now()}")
    success = False
    try:
        if args.mode == 'live':
            success = run_alpaca_trading_bot(paper_trading=False, ignore_market_hours=args.ignore_market_hours)
        elif args.mode == 'paper':
            success = run_alpaca_trading_bot(paper_trading=True, ignore_market_hours=args.ignore_market_hours)
        elif args.mode == 'bot':
            print("📊 STEP 1: Generating Nuclear Trading Signals (BOT MODE)...")
            print("-" * 50)
            from core.nuclear_trading_bot import NuclearTradingBot
            bot = NuclearTradingBot()
            signal = bot.run_once()
            if not signal:
                print("❌ Failed to generate nuclear signals")
                success = False
            else:
                print("✅ Nuclear trading signals generated successfully!")
                print(signal)
                success = True
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
