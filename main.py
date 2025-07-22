#!/usr/bin/env python3
"""
Nuclear Trading Strategy - Main Entry Point
Unified launcher for all nuclear trading operations

This file is a thin runner. It only handles CLI, orchestration, and logging.
All business logic is delegated to orchestrator and service classes in core/.
No business logic should be added here.

Supported modes:
- bot: Single nuclear strategy signal generation only
- multi: Multi-strategy (Nuclear + TECL) signal generation only
- live: Multi-strategy live trading execution
- paper: Multi-strategy paper trading execution
- nuclear-live: Single nuclear strategy live trading (legacy)
- nuclear-paper: Single nuclear strategy paper trading (legacy)
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


def generate_multi_strategy_signals():
    """
    Generate signals for all strategies (Nuclear + TECL) and return consolidated results.
    """
    from core.strategy_manager import MultiStrategyManager, StrategyType
    
    print("🚀 MULTI-STRATEGY SIGNAL GENERATION")
    print("=" * 60)
    print(f"Running multi-strategy analysis at {datetime.now()}")
    print()
    
    try:
        # Initialize strategy manager with 50/50 allocation
        manager = MultiStrategyManager({
            StrategyType.NUCLEAR: 0.5,
            StrategyType.TECL: 0.5
        })
        
        print("📊 Running all strategies...")
        strategy_signals, consolidated_portfolio = manager.run_all_strategies()
        
        print("\n🎯 MULTI-STRATEGY RESULTS:")
        print("-" * 40)
        
        # Display individual strategy results
        for strategy_type, signal in strategy_signals.items():
            print(f"{strategy_type.value} Strategy:")
            print(f"  Action: {signal['action']} {signal['symbol']}")
            print(f"  Reason: {signal['reason']}")
            print()
        
        # Display consolidated portfolio
        print("📈 Consolidated Portfolio Allocation:")
        for symbol, weight in consolidated_portfolio.items():
            print(f"  {symbol}: {weight:.1%}")
        
        # Get performance summary
        summary = manager.get_strategy_performance_summary()
        print(f"\n📋 Strategy Summary:")
        for strategy, details in summary['strategies'].items():
            print(f"  {strategy}: {details['current_positions']} positions, {details['allocation']:.0%} allocation")
        
        return manager, strategy_signals, consolidated_portfolio
        
    except Exception as e:
        print(f"❌ Error running multi-strategy analysis: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None

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


def run_multi_strategy_bot():
    """
    Run multi-strategy signal generation only (no trading).
    This generates and logs signals from both Nuclear and TECL strategies.
    """
    print("🚀 MULTI-STRATEGY BOT - SIGNAL GENERATION MODE")
    print("=" * 60)
    try:
        manager, strategy_signals, consolidated_portfolio = generate_multi_strategy_signals()
        
        if strategy_signals and consolidated_portfolio:
            print("\n✅ Multi-strategy signals generated successfully!")
            config = Config()
            log_path = config['logging'].get('multi_strategy_alerts', 'data/logs/multi_strategy_alerts.json')
            print(f"📁 Signals logged to: {log_path}")
            return True
        else:
            print("\n⚠️  No clear signals generated from multi-strategy analysis")
            return False
    except Exception as e:
        print(f"❌ Error running multi-strategy bot: {e}")
        traceback.print_exc()
        return False


def run_multi_strategy_live_trading(ignore_market_hours=False):
    """
    Run multi-strategy live trading with Alpaca execution and Telegram updates.
    """
    print("🚀 MULTI-STRATEGY LIVE TRADING MODE")
    print("=" * 60)
    print(f"Running multi-strategy live trading at {datetime.now()}")
    print()
    
    try:
        from core.telegram_utils import send_telegram_message
        from execution.multi_strategy_trader import MultiStrategyAlpacaTrader, StrategyType
        from execution.alpaca_trader import is_market_open
        
        print("📊 STEP 1: Initializing Multi-Strategy Trader...")
        print("-" * 50)
        
        # Initialize multi-strategy trader (LIVE trading)
        trader = MultiStrategyAlpacaTrader(
            paper_trading=False,
            strategy_allocations={
                StrategyType.NUCLEAR: 0.5,
                StrategyType.TECL: 0.5
            }
        )
        
        # Check market hours
        if not ignore_market_hours and not is_market_open(trader.trading_client):
            print("❌ Market is CLOSED. No trades will be placed.")
            send_telegram_message("❌ Market is CLOSED. No trades will be placed.")
            return False
        
        if ignore_market_hours:
            print("⚠️  IGNORING MARKET HOURS (Testing Mode)")
            send_telegram_message("⚠️  IGNORING MARKET HOURS (Testing Mode)")
        else:
            print("✅ Market is OPEN. Proceeding with live trading.")
        
        print("\n⚡ STEP 2: Executing Multi-Strategy Trading...")
        print("-" * 50)
        
        # Execute multi-strategy
        result = trader.execute_multi_strategy()
        
        # Display results
        trader.display_multi_strategy_summary(result)
        
        # Send Telegram notification
        print("\n📲 STEP 3: Sending Telegram Notification...")
        print("-" * 50)
        
        try:
            message = _build_multi_strategy_telegram_message(result, "LIVE")
            send_telegram_message(message)
            print("✅ Telegram notification sent successfully!")
        except Exception as e:
            print(f"⚠️ Error sending Telegram notification: {e}")
        
        return result.success
        
    except Exception as e:
        print(f"❌ Error running multi-strategy live trading: {e}")
        traceback.print_exc()
        return False


def run_multi_strategy_paper_trading(ignore_market_hours=False):
    """
    Run multi-strategy paper trading with Alpaca execution and Telegram updates.
    """
    print("🚀 MULTI-STRATEGY PAPER TRADING MODE")
    print("=" * 60)
    print(f"Running multi-strategy paper trading at {datetime.now()}")
    print()
    
    try:
        from core.telegram_utils import send_telegram_message
        from execution.multi_strategy_trader import MultiStrategyAlpacaTrader, StrategyType
        from execution.alpaca_trader import is_market_open
        
        print("📊 STEP 1: Initializing Multi-Strategy Paper Trader...")
        print("-" * 50)
        
        # Initialize multi-strategy trader (PAPER trading)
        trader = MultiStrategyAlpacaTrader(
            paper_trading=True,
            strategy_allocations={
                StrategyType.NUCLEAR: 0.5,
                StrategyType.TECL: 0.5
            }
        )
        
        # Check market hours
        if not ignore_market_hours and not is_market_open(trader.trading_client):
            print("❌ Market is CLOSED. No trades will be placed.")
            send_telegram_message("❌ Market is CLOSED. No trades will be placed.")
            return False
        
        if ignore_market_hours:
            print("⚠️  IGNORING MARKET HOURS (Testing Mode)")
            send_telegram_message("⚠️  IGNORING MARKET HOURS (Testing Mode)")
        else:
            print("✅ Market is OPEN. Proceeding with paper trading.")
        
        print("\n⚡ STEP 2: Executing Multi-Strategy Paper Trading...")
        print("-" * 50)
        
        # Execute multi-strategy
        result = trader.execute_multi_strategy()
        
        # Display results
        trader.display_multi_strategy_summary(result)
        
        # Send Telegram notification
        print("\n📲 STEP 3: Sending Telegram Notification...")
        print("-" * 50)
        
        try:
            message = _build_multi_strategy_telegram_message(result, "PAPER")
            send_telegram_message(message)
            print("✅ Telegram notification sent successfully!")
        except Exception as e:
            print(f"⚠️ Error sending Telegram notification: {e}")
        
        return result.success
        
    except Exception as e:
        print(f"❌ Error running multi-strategy paper trading: {e}")
        traceback.print_exc()
        return False


def _build_multi_strategy_telegram_message(result, mode):
    """Build Telegram message for multi-strategy execution results"""
    if not result.success:
        return f"❌ {mode} Multi-Strategy Execution FAILED\n\nError: {result.execution_summary.get('error', 'Unknown error')}"
    
    summary = result.execution_summary
    account = summary['account_summary']
    
    # Build message
    lines = [
        f"🎯 {mode} MULTI-STRATEGY EXECUTION",
        f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"💰 Account Performance:",
        f"Portfolio: ${account['portfolio_value_before']:,.0f} → ${account['portfolio_value_after']:,.0f}",
        f"Change: ${account['value_change']:+,.0f} ({account['value_change_pct']:+.2f}%)",
        "",
        f"📊 Strategy Signals:"
    ]
    
    for strategy, details in summary['strategy_summary'].items():
        lines.append(f"{strategy} ({details['allocation']:.0%}): {details['signal']}")
    
    lines.extend([
        "",
        f"🎯 Portfolio Allocation:"
    ])
    
    for symbol, weight in result.consolidated_portfolio.items():
        lines.append(f"{symbol}: {weight:.1%}")
    
    trading = summary['trading_summary']
    if trading['total_trades'] > 0:
        lines.extend([
            "",
            f"⚡ Trading: {trading['total_trades']} orders",
            f"Buy: ${trading['total_buy_value']:,.0f} | Sell: ${trading['total_sell_value']:,.0f}"
        ])
    else:
        lines.append("\n⚡ No trades needed")
    
    return "\n".join(lines)





def run_live_trading_bot(ignore_market_hours=False):
    """
    Run the nuclear trading bot with Alpaca execution and send a Telegram update.
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
        # Execute nuclear strategy which returns whether it succeeded and any
        # orders that were executed
        success, orders = alpaca_bot.execute_nuclear_strategy()
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
        success, orders = alpaca_bot.execute_nuclear_strategy()
        
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
    Supports multiple modes:
      - 'bot': Nuclear strategy signal generation only
      - 'multi': Multi-strategy (Nuclear + TECL) signal generation only  
      - 'live': Multi-strategy live trading execution
      - 'paper': Multi-strategy paper trading execution
      - 'nuclear-live': Single nuclear strategy live trading (legacy)
      - 'nuclear-paper': Single nuclear strategy paper trading (legacy)
    """
    parser = argparse.ArgumentParser(description="Nuclear Trading Strategy - Unified Entry Point")
    parser.add_argument('mode', choices=['bot', 'multi', 'live', 'paper', 'nuclear-live', 'nuclear-paper'], 
                       help='Operation mode: bot (nuclear signals only), multi (multi-strategy signals), live (multi-strategy live trading), paper (multi-strategy paper trading), nuclear-live (legacy), nuclear-paper (legacy)')
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
        elif args.mode == 'multi':
            success = run_multi_strategy_bot()
        elif args.mode == 'live':
            success = run_multi_strategy_live_trading(ignore_market_hours=args.ignore_market_hours)
        elif args.mode == 'paper':
            success = run_multi_strategy_paper_trading(ignore_market_hours=args.ignore_market_hours)
        elif args.mode == 'nuclear-live':
            success = run_live_trading_bot(ignore_market_hours=args.ignore_market_hours)
        elif args.mode == 'nuclear-paper':
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
