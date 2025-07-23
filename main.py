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


def display_technical_indicators(strategy_signals):
    """
    Display key technical indicators used by all strategies in a clean boxed format
    """
    print("\n📊 TECHNICAL INDICATORS:")
    print("┌─" + "─" * 58 + "─┐")
    print("│ Key Market & Technical Indicators                        │")  
    print("├─" + "─" * 58 + "─┤")
    
    # Get indicators from both strategies - prefer Nuclear as it has more comprehensive data
    all_indicators = {}
    for strategy_type, signal_data in strategy_signals.items():
        if 'indicators' in signal_data and signal_data['indicators']:
            all_indicators.update(signal_data['indicators'])
    
    if not all_indicators:
        print("│ No indicator data available                              │")
        print("└─" + "─" * 58 + "─┘")
        return
    
    # Key symbols to display in order of importance
    key_symbols = [
        'SPY',      # Market trend filter
        'TQQQ',     # Tech momentum  
        'XLK',      # Tech sector
        'KMLM',     # Managed futures comparison
        'UVXY',     # Volatility indicator
        'SPXL',     # Broad market leverage
        'TECL',     # Tech leverage
        'BIL',      # Cash equivalent
        'SQQQ',     # Tech short
        'BSV'       # Bonds
    ]
    
    # Display indicators for available symbols
    displayed_count = 0
    for symbol in key_symbols:
        if symbol in all_indicators and displayed_count < 8:  # Limit display
            ind = all_indicators[symbol]
            price = ind.get('current_price', 0)
            rsi = ind.get('rsi_10', ind.get('rsi_9', 50))
            ma_200 = ind.get('ma_200')
            
            # Format price nicely
            if price < 10:
                price_str = f"${price:.3f}"
            elif price < 100:
                price_str = f"${price:.2f}"
            else:
                price_str = f"${price:.1f}"
            
            # Show trend vs 200MA if available
            trend_indicator = ""
            if ma_200 and price > 0:
                if price > ma_200:
                    trend_indicator = " ↗"  # Above 200MA
                else:
                    trend_indicator = " ↘"  # Below 200MA
            
            # RSI level indicator
            rsi_level = ""
            if rsi > 80:
                rsi_level = "🔴"  # Overbought
            elif rsi < 30:
                rsi_level = "🟢"  # Oversold  
            else:
                rsi_level = "⚪"  # Neutral
            
            # Format the line
            line = f"│ {symbol:>4}: {price_str:<8} RSI:{rsi:5.1f} {rsi_level}{trend_indicator}"
            # Pad to exact width
            line = line.ljust(61) + "│"
            print(line)
            displayed_count += 1
    
    # Add market regime summary
    if 'SPY' in all_indicators:
        spy_data = all_indicators['SPY']
        spy_price = spy_data.get('current_price', 0)
        spy_ma200 = spy_data.get('ma_200', 0)
        
        if spy_price > 0 and spy_ma200 > 0:
            print("├─" + "─" * 58 + "─┤")
            regime = "BULL MARKET" if spy_price > spy_ma200 else "BEAR MARKET"
            regime_line = f"│ Market Regime: {regime} (SPY {spy_price:.1f} vs 200MA {spy_ma200:.1f})"
            regime_line = regime_line.ljust(61) + "│"
            print(regime_line)
    
    print("└─" + "─" * 58 + "─┘")


def generate_multi_strategy_signals():
    """
    Generate signals for all strategies (Nuclear + TECL) and return consolidated results.
    """
    from core.strategy_manager import MultiStrategyManager, StrategyType
    from core.data_provider import UnifiedDataProvider
    
    print("🚀 MULTI-STRATEGY SIGNAL GENERATION")
    print("=" * 60)
    print(f"Running multi-strategy analysis at {datetime.now()}")
    print()
    
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
        display_technical_indicators(strategy_signals)
        
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
        nuclear_positions = 3 if strategy_signals.get(StrategyType.NUCLEAR, {}).get('action') == 'BUY' else 0
        tecl_positions = 1 if strategy_signals.get(StrategyType.TECL, {}).get('action') == 'BUY' else 0
        
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
            }
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
        display_technical_indicators(strategy_signals)
        
        # Execute multi-strategy
        result = trader.execute_multi_strategy()
        
        # Display results
        trader.display_multi_strategy_summary(result)
        
        # Send Telegram notification
        try:
            message = _build_multi_strategy_telegram_message(result, mode_str)
            send_telegram_message(message)
        except Exception as e:
            print(f"⚠️ Telegram notification failed: {e}")
        
        return result.success
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def _build_single_strategy_telegram_message(result, strategy_name, mode):
    """Build Telegram message for single strategy execution results"""
    if not result.success:
        return f"❌ {mode} {strategy_name} Strategy FAILED\n\nError: {result.execution_summary.get('error', 'Unknown error')}"
    
    summary = result.execution_summary
    
    # Build message
    lines = [
        f"🎯 {mode} {strategy_name} STRATEGY",
        f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
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
    
    # Build message
    lines = [
        f"🎯 {mode} MULTI-STRATEGY EXECUTION",
        f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
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
