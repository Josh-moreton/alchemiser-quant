#!/usr/bin/env python3
"""
Nuclear Trading Strategy - Main Entry Point
Unified launcher for all nuclear trading operations

This file is a thin runner. It only handles CLI, orchestration, and logging.
All business logic is delegated to orchestrator and service classes in core/.
No business logic should be added here.

Supported modes:
- bot: Generate and display all strategy signals (no trading)
- single: Run single strategy trading (requires --nuclear or --tecl)
- multi: Run multi-strategy trading (Nuclear + TECL combined)

Trading modes:
- Default: Paper trading (safe default)
- --live: Live trading (requires explicit flag)

Examples:
  python main.py bot                    # Show all strategy signals
  python main.py single --nuclear       # Nuclear strategy paper trading
  python main.py single --tecl --live   # TECL strategy live trading
  python main.py multi                  # Multi-strategy paper trading
  python main.py multi --live           # Multi-strategy live trading
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

def run_all_signals_display():
    """
    Generate and display all strategy signals without any trading.
    Shows Nuclear, TECL, and consolidated multi-strategy results.
    """
    print("🤖 STRATEGY SIGNAL ANALYSIS")
    print("=" * 60)
    print(f"Analyzing all strategies at {datetime.now()}")
    print()
    
    try:
        # Generate Nuclear signal
        print("🔥 NUCLEAR STRATEGY ANALYSIS")
        print("-" * 40)
        nuclear_bot, nuclear_signal = generate_signal()
        
        if nuclear_signal:
            print(f"✅ Nuclear Signal: {nuclear_signal['action']} {nuclear_signal['symbol']}")
            print(f"   Reason: {nuclear_signal['reason']}")
        else:
            print("⚠️  No clear nuclear signal")
        print()
        
        # Generate multi-strategy signals
        print("🎯 MULTI-STRATEGY ANALYSIS")
        print("-" * 40)
        manager, strategy_signals, consolidated_portfolio = generate_multi_strategy_signals()
        
        if not strategy_signals:
            print("⚠️  Failed to generate multi-strategy signals")
            return False
        
        # Summary
        print("\n📋 STRATEGY SIGNALS SUMMARY")
        print("=" * 40)
        for strategy_type, signal in strategy_signals.items():
            status = "✅" if signal['action'] != 'HOLD' else "⏸️"
            print(f"{status} {strategy_type.value}: {signal['action']} {signal['symbol']}")
            print(f"    └─ {signal['reason']}")
        
        print(f"\n🎯 Consolidated Portfolio:")
        if consolidated_portfolio:
            for symbol, weight in consolidated_portfolio.items():
                print(f"    {symbol}: {weight:.1%}")
        else:
            print("    No portfolio recommendations")
        
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing strategies: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_single_strategy_trading(strategy_name: str, live_trading: bool = False):
    """
    Run single strategy trading (Nuclear or TECL)
    
    Args:
        strategy_name: 'nuclear' or 'tecl'
        live_trading: True for live trading, False for paper trading
    """
    mode_str = "LIVE" if live_trading else "PAPER"
    strategy_display = strategy_name.upper()
    
    print(f"🎯 {strategy_display} STRATEGY - {mode_str} TRADING")
    print("=" * 60)
    print(f"Running {strategy_display} strategy {mode_str.lower()} trading at {datetime.now()}")
    print()
    
    try:
        if strategy_name.lower() == 'nuclear':
            return _run_nuclear_strategy(live_trading)
        elif strategy_name.lower() == 'tecl':
            return _run_tecl_strategy(live_trading)
        else:
            print(f"❌ Unknown strategy: {strategy_name}")
            return False
            
    except Exception as e:
        print(f"❌ Error running {strategy_name} strategy: {e}")
        import traceback
        traceback.print_exc()
        return False


def _run_nuclear_strategy(live_trading: bool) -> bool:
    """Run Nuclear strategy trading"""
    try:
        from core.telegram_utils import send_telegram_message, build_execution_report
        from execution.alpaca_trader import AlpacaTradingBot, is_market_open
        
        print("📊 STEP 1: Checking Market Status...")
        print("-" * 50)
        alpaca_bot = AlpacaTradingBot(paper_trading=not live_trading)
        
        # Check market hours
        if not is_market_open(alpaca_bot.trading_client):
            print("❌ Market is CLOSED. No trades will be placed.")
            send_telegram_message("❌ Market is CLOSED. No trades will be placed.")
            return False
        
        print("✅ Market is OPEN. Proceeding with trading.")
        
        print("\n📊 STEP 2: Generating Nuclear Trading Signals...")
        print("-" * 50)
        bot, signal = generate_signal()
        if not signal:
            print("❌ Failed to generate nuclear signals")
            return False
        print("✅ Nuclear trading signals generated successfully!")
        
        # Get account info before trading
        account_info_before = alpaca_bot.get_account_info()
        print("\n📋 Account Status Before Trading:")
        alpaca_bot.display_account_summary()
        
        print("\n⚡ STEP 3: Executing Nuclear Strategy...")
        print("-" * 50)
        success, orders = alpaca_bot.execute_nuclear_strategy()
        
        if success:
            print("✅ Nuclear strategy execution completed successfully!")
        else:
            print("❌ Nuclear strategy execution failed!")
        
        print("\n📊 STEP 4: Final Account Status...")
        print("-" * 50)
        account_info_after = alpaca_bot.get_account_info()
        alpaca_bot.display_account_summary()
        
        # Send Telegram notification
        print("\n� STEP 5: Sending Telegram Notification...")
        print("-" * 50)
        positions = alpaca_bot.get_positions()
        mode_str = "LIVE" if live_trading else "PAPER"
        msg = build_execution_report(
            mode=mode_str,
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
        print(f"❌ Error running Nuclear strategy: {e}")
        return False


def _run_tecl_strategy(live_trading: bool) -> bool:
    """Run TECL strategy trading"""
    try:
        from core.telegram_utils import send_telegram_message
        from execution.multi_strategy_trader import MultiStrategyAlpacaTrader, StrategyType
        from execution.alpaca_trader import is_market_open
        
        print("📊 STEP 1: Initializing TECL Strategy Trader...")
        print("-" * 50)
        
        # Initialize trader with 100% TECL allocation
        trader = MultiStrategyAlpacaTrader(
            paper_trading=not live_trading,
            strategy_allocations={
                StrategyType.TECL: 1.0  # 100% TECL strategy
            }
        )
        
        # Check market hours
        if not is_market_open(trader.trading_client):
            print("❌ Market is CLOSED. No trades will be placed.")
            send_telegram_message("❌ Market is CLOSED. No trades will be placed.")
            return False
        
        print("✅ Market is OPEN. Proceeding with TECL trading.")
        
        print("\n⚡ STEP 2: Executing TECL Strategy...")
        print("-" * 50)
        
        # Execute TECL-only strategy
        result = trader.execute_multi_strategy()
        
        # Display results
        trader.display_multi_strategy_summary(result)
        
        # Send Telegram notification
        print("\n📲 STEP 3: Sending Telegram Notification...")
        print("-" * 50)
        
        try:
            mode_str = "LIVE" if live_trading else "PAPER"
            message = _build_single_strategy_telegram_message(result, "TECL", mode_str)
            send_telegram_message(message)
            print("✅ Telegram notification sent successfully!")
        except Exception as e:
            print(f"⚠️ Error sending Telegram notification: {e}")
        
        return result.success
        
    except Exception as e:
        print(f"❌ Error running TECL strategy: {e}")
        return False


def run_multi_strategy_trading(live_trading: bool = False):
    """
    Run multi-strategy trading with both Nuclear and TECL strategies
    
    Args:
        live_trading: True for live trading, False for paper trading
    """
    mode_str = "LIVE" if live_trading else "PAPER"
    
    print(f"🚀 MULTI-STRATEGY TRADING - {mode_str}")
    print("=" * 60)
    print(f"Running multi-strategy {mode_str.lower()} trading at {datetime.now()}")
    print()
    
    try:
        from core.telegram_utils import send_telegram_message
        from execution.multi_strategy_trader import MultiStrategyAlpacaTrader, StrategyType
        from execution.alpaca_trader import is_market_open
        
        print("📊 STEP 1: Initializing Multi-Strategy Trader...")
        print("-" * 50)
        
        # Initialize multi-strategy trader
        trader = MultiStrategyAlpacaTrader(
            paper_trading=not live_trading,
            strategy_allocations={
                StrategyType.NUCLEAR: 0.5,
                StrategyType.TECL: 0.5
            }
        )
        
        # Check market hours
        if not is_market_open(trader.trading_client):
            print("❌ Market is CLOSED. No trades will be placed.")
            send_telegram_message("❌ Market is CLOSED. No trades will be placed.")
            return False
        
        print("✅ Market is OPEN. Proceeding with multi-strategy trading.")
        
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
            message = _build_multi_strategy_telegram_message(result, mode_str)
            send_telegram_message(message)
            print("✅ Telegram notification sent successfully!")
        except Exception as e:
            print(f"⚠️ Error sending Telegram notification: {e}")
        
        return result.success
        
    except Exception as e:
        print(f"❌ Error running multi-strategy trading: {e}")
        import traceback
        traceback.print_exc()
        return False


def _build_single_strategy_telegram_message(result, strategy_name, mode):
    """Build Telegram message for single strategy execution results"""
    if not result.success:
        return f"❌ {mode} {strategy_name} Strategy FAILED\n\nError: {result.execution_summary.get('error', 'Unknown error')}"
    
    summary = result.execution_summary
    account = summary['account_summary']
    
    # Build message
    lines = [
        f"🎯 {mode} {strategy_name} STRATEGY",
        f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        f"💰 Account Performance:",
        f"Portfolio: ${account['portfolio_value_before']:,.0f} → ${account['portfolio_value_after']:,.0f}",
        f"Change: ${account['value_change']:+,.0f} ({account['value_change_pct']:+.2f}%)",
        "",
        f"🎯 Portfolio Allocation:"
    ]
    
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


def main():
    """
    Main entry point for the Nuclear Trading Strategy CLI.
    
    Modes:
      - 'bot': Display all strategy signals (no trading)
      - 'single': Run single strategy trading (requires --nuclear or --tecl)
      - 'multi': Run multi-strategy trading (Nuclear + TECL combined)
    
    Trading modes:
      - Default: Paper trading (safe default)
      - --live: Live trading (requires explicit flag)
    """
    parser = argparse.ArgumentParser(description="Nuclear Trading Strategy - Unified Entry Point")
    parser.add_argument('mode', choices=['bot', 'single', 'multi'], 
                       help='Operation mode: bot (show signals), single (single strategy), multi (multi-strategy)')
    
    # Strategy selection for single mode
    parser.add_argument('--nuclear', action='store_true',
                       help='Use Nuclear strategy (for single mode)')
    parser.add_argument('--tecl', action='store_true',
                       help='Use TECL strategy (for single mode)')
    
    # Trading mode selection
    parser.add_argument('--live', action='store_true',
                       help='Use live trading (default is paper trading)')
    
    # Legacy support
    parser.add_argument('--ignore-market-hours', action='store_true',
                       help='Ignore market hours and run during closed market (for testing)')

    args = parser.parse_args()

    print("🚀 NUCLEAR TRADING STRATEGY")
    print("=" * 60)
    print(f"Mode: {args.mode}")
    if args.mode == 'single':
        if args.nuclear:
            print("Strategy: Nuclear")
        elif args.tecl:
            print("Strategy: TECL")
        else:
            print("❌ Single mode requires --nuclear or --tecl flag")
            print("Example: python main.py single --nuclear")
            sys.exit(1)
    
    if args.live:
        print("Trading Mode: LIVE TRADING ⚠️")
    else:
        print("Trading Mode: Paper Trading (Safe Default)")
    
    print(f"Timestamp: {datetime.now()}")
    print()
    
    success = False
    try:
        if args.mode == 'bot':
            # Display all strategy signals (no trading)
            success = run_all_signals_display()
            
        elif args.mode == 'single':
            # Single strategy trading
            if args.nuclear:
                success = run_single_strategy_trading('nuclear', live_trading=args.live)
            elif args.tecl:
                success = run_single_strategy_trading('tecl', live_trading=args.live)
            
        elif args.mode == 'multi':
            # Multi-strategy trading
            success = run_multi_strategy_trading(live_trading=args.live)
            
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
