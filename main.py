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
import logging
from logging.handlers import RotatingFileHandler
from core.config import Config
from core.ui.cli_formatter import render_technical_indicators
from core.ui.telegram_formatter import build_single_strategy_message, build_multi_strategy_message

# Load config and set logging level from config
config = Config()
logging_config = config['logging']

# Ensure logs directory exists
os.makedirs('data/logs', exist_ok=True)

# Set up file-based logging for all system logs
def setup_file_logging():
    """Configure logging to send all logs to files, keeping terminal clean"""
    
    # Create file handler with rotation
    file_handler = RotatingFileHandler(
        'data/logs/trading_bot.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    
    # Create detailed formatter for file logs
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    # Configure root logger to use file handler only
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()  # Remove any existing handlers
    root_logger.addHandler(file_handler)
    
    # Set appropriate levels for third-party loggers
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('alpaca').setLevel(logging.INFO)
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('s3transfer').setLevel(logging.WARNING)
    
    return file_handler

# Initialize file-based logging
setup_file_logging()




def generate_multi_strategy_signals():
    """
    Generate signals for all strategies (Nuclear + TECL) and return consolidated results.
    """
    from core.strategy_manager import MultiStrategyManager, StrategyType
    from core.data_provider import UnifiedDataProvider
    
    try:
        # Create shared UnifiedDataProvider once
        shared_data_provider = UnifiedDataProvider(paper_trading=True)
        
        # Pass shared data provider to MultiStrategyManager
        manager = MultiStrategyManager({
            StrategyType.NUCLEAR: 0.5,
            StrategyType.TECL: 0.5
        }, shared_data_provider=shared_data_provider)
        
        print("📊 Running all strategies...")
        strategy_signals, consolidated_portfolio = manager.run_all_strategies()
        
        # Display technical indicators before strategy results
        print(render_technical_indicators(strategy_signals))
        
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
        
        # Calculate actual position counts from signals
        nuclear_signal = strategy_signals.get(StrategyType.NUCLEAR, {})
        tecl_signal = strategy_signals.get(StrategyType.TECL, {})
        
        # Determine position count based on the specific signal
        if nuclear_signal.get('action') == 'BUY':
            if nuclear_signal.get('symbol') == 'UVXY_BTAL_PORTFOLIO':
                nuclear_positions = 2  # UVXY and BTAL
            elif nuclear_signal.get('symbol') == 'UVXY':
                nuclear_positions = 1  # Just UVXY
            else:
                nuclear_positions = 3  # Default for other portfolios
        else:
            nuclear_positions = 0
            
        tecl_positions = 1 if tecl_signal.get('action') == 'BUY' else 0
        
        print(f"  NUCLEAR: {nuclear_positions} positions, 50% allocation")
        print(f"  TECL: {tecl_positions} positions, 50% allocation")
        
        return manager, strategy_signals, consolidated_portfolio
        
    except Exception as e:
        print(f"❌ Error running multi-strategy analysis: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None

def run_all_signals_display():
    """
    Generate and display multi-strategy signals without any trading.
    Shows Nuclear, TECL, and consolidated multi-strategy results.
    """
    print("🤖 MULTI-STRATEGY SIGNAL ANALYSIS")
    print("=" * 60)
    print(f"Analyzing all strategies at {datetime.now()}")
    print()
    
    try:
        # Generate multi-strategy signals (this includes both Nuclear and TECL)
        manager, strategy_signals, consolidated_portfolio = generate_multi_strategy_signals()
        
        if not strategy_signals:
            print("⚠️  Failed to generate multi-strategy signals")
            return False
        
        
        # Summary
        # The redundant summary block has been removed.
        
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing strategies: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_multi_strategy_trading(live_trading: bool = False, ignore_market_hours: bool = False):
    """
    Run multi-strategy trading with both Nuclear and TECL strategies
    
    Args:
        live_trading: True for live trading, False for paper trading
    """
    mode_str = "LIVE" if live_trading else "PAPER"
    
    try:
        from core.telegram_utils import send_telegram_message
        from execution.multi_strategy_trader import MultiStrategyAlpacaTrader, StrategyType
        from execution.alpaca_trader import is_market_open
        
        # Initialize multi-strategy trader
        trader = MultiStrategyAlpacaTrader(
            paper_trading=not live_trading,
            strategy_allocations={
                StrategyType.NUCLEAR: 0.5,
                StrategyType.TECL: 0.5
            },
            ignore_market_hours=ignore_market_hours
        )
        
        # Check market hours unless ignore_market_hours is set
        if not ignore_market_hours and not is_market_open(trader.trading_client):
            print("❌ Market is CLOSED. No trades will be placed.")
            send_telegram_message("❌ Market is CLOSED. No trades will be placed.")
            return "market_closed"
        
        # Generate strategy signals to get technical indicators for display
        print("📊 Analyzing market conditions...")
        strategy_signals = trader.strategy_manager.run_all_strategies()[0]
        
        # Display technical indicators
        print(render_technical_indicators(strategy_signals))
        
        # Execute multi-strategy
        result = trader.execute_multi_strategy()
        
        # Display results
        trader.display_multi_strategy_summary(result)
        
        # Send Telegram notification
        try:
            message = build_multi_strategy_message(result, mode_str)
            send_telegram_message(message)
        except Exception as e:
            print(f"⚠️ Telegram notification failed: {e}")
        
        return result.success
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False



def main(argv=None):
    """
    Main entry point for the Multi-Strategy Nuclear Trading Bot.
    
    Modes:
      - 'bot': Display multi-strategy signals (no trading)
      - 'trade': Execute multi-strategy trading (Nuclear + TECL combined)
    
    Trading modes:
      - Default: Paper trading (safe default)
      - --live: Live trading (requires explicit flag)
    """
    parser = argparse.ArgumentParser(description="Multi-Strategy Nuclear Trading Bot")
    parser.add_argument('mode', choices=['bot', 'trade'],
                       help='Operation mode: bot (show signals), trade (execute trading)')
    
    # Trading mode selection
    parser.add_argument('--live', action='store_true',
                       help='Use live trading (default is paper trading)')
    
    # Market hours override
    parser.add_argument('--ignore-market-hours', action='store_true',
                       help='Ignore market hours and run during closed market (for testing)')

    args = parser.parse_args(argv)
    
    mode_label = "LIVE TRADING ⚠️" if args.mode == 'trade' and args.live else "Paper Trading"
    print(f"🚀 Multi-Strategy Nuclear Bot | {args.mode.upper()} | {mode_label}")
    print()
    
    success = False
    try:
        if args.mode == 'bot':
            # Display multi-strategy signals (no trading)
            success = run_all_signals_display()
        elif args.mode == 'trade':
            # Multi-strategy trading
            result = run_multi_strategy_trading(live_trading=args.live, ignore_market_hours=args.ignore_market_hours)
            if result == "market_closed":
                print("✅ Market closed - no action taken")
                return True
            else:
                success = result
    except Exception as e:
        print(f"❌ Error: {e}")
        success = False
    
    if success:
        print("\n✅ Operation completed successfully!")
        return True
    else:
        print("\n❌ Operation failed!")
        return False

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
