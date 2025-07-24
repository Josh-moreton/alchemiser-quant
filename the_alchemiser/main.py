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
from the_alchemiser.core.config import Config
from the_alchemiser.core.ui.cli_formatter import render_technical_indicators
from the_alchemiser.core.ui.telegram_formatter import build_single_strategy_message, build_multi_strategy_message
from the_alchemiser.core.strategy_manager import StrategyType

# Load config and set logging level from config
config = Config()
logging_config = config['logging']

def setup_file_logging():
    """Configure logging to send all logs to S3 in Lambda, file locally."""
    import os
    from the_alchemiser.core.s3_utils import S3FileHandler
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()  # Remove any existing handlers

    if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        # Lambda: log to S3 only
        s3_log_path = logging_config.get('alpaca_log')
        s3_handler = S3FileHandler(s3_log_path)
        s3_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        root_logger.addHandler(s3_handler)
    else:
        # Local/dev: Ensure logs directory exists and log to file
        os.makedirs('the_alchemiser/data/logs', exist_ok=True)
        log_path = "the_alchemiser/data/logs/trading_bot.log"
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        root_logger.addHandler(file_handler)

    # Set appropriate levels for third-party loggers
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('alpaca').setLevel(logging.INFO)
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('s3transfer').setLevel(logging.WARNING)

# Initialize file-based logging
setup_file_logging()




def generate_multi_strategy_signals():
    """
    Generate signals for all strategies (Nuclear + TECL) and return consolidated results.
    """
    from the_alchemiser.core.strategy_manager import MultiStrategyManager, StrategyType
    from the_alchemiser.core.data_provider import UnifiedDataProvider
    
    try:
        # Create shared UnifiedDataProvider once
        shared_data_provider = UnifiedDataProvider(paper_trading=True)
        # Pass shared data provider to MultiStrategyManager
        manager = MultiStrategyManager({
            StrategyType.NUCLEAR: 0.5,
            StrategyType.TECL: 0.5
        }, shared_data_provider=shared_data_provider)
        strategy_signals, consolidated_portfolio = manager.run_all_strategies()
        return manager, strategy_signals, consolidated_portfolio
    except Exception as e:
        return None, None, None

def run_all_signals_display():
    """
    Generate and display multi-strategy signals without any trading.
    Shows Nuclear, TECL, and consolidated multi-strategy results.
    """
    from the_alchemiser.core.ui.cli_formatter import (
        render_header, render_footer, render_technical_indicators, 
        render_strategy_signals, render_portfolio_allocation
    )
    
    render_header("MULTI-STRATEGY SIGNAL ANALYSIS", f"Analysis at {datetime.now()}")
    
    try:
        # Generate multi-strategy signals (this includes both Nuclear and TECL)
        manager, strategy_signals, consolidated_portfolio = generate_multi_strategy_signals()
        if not strategy_signals:
            from rich.console import Console
            Console().print("[bold red]⚠️  Failed to generate multi-strategy signals[/bold red]")
            return False
            
        # Display technical indicators
        render_technical_indicators(strategy_signals)
        
        # Display strategy signals
        render_strategy_signals(strategy_signals)
        
        # Display consolidated portfolio
        if consolidated_portfolio:
            render_portfolio_allocation(consolidated_portfolio)
        
        # Calculate actual position counts from signals
        nuclear_signal = (strategy_signals or {}).get(StrategyType.NUCLEAR, {})
        tecl_signal = (strategy_signals or {}).get(StrategyType.TECL, {})
        
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
        
        from rich.console import Console
        from rich.panel import Panel
        console = Console()
        
        strategy_summary = f"""[bold cyan]NUCLEAR:[/bold cyan] {nuclear_positions} positions, 50% allocation
[bold cyan]TECL:[/bold cyan] {tecl_positions} positions, 50% allocation"""
        
        console.print(Panel(strategy_summary, title="📋 Strategy Summary", border_style="blue"))
        
        render_footer("Signal analysis completed successfully!")
        return True
    except Exception as e:
        from rich.console import Console
        Console().print(f"[bold red]❌ Error analyzing strategies: {e}[/bold red]")
        import traceback
        traceback.print_exc()
        return False


def run_multi_strategy_trading(live_trading: bool = False, ignore_market_hours: bool = False):
    """
    Run multi-strategy trading with both Nuclear and TECL strategies
    
    Args:
        live_trading: True for live trading, False for paper trading
    """
    from the_alchemiser.core.ui.cli_formatter import render_header, render_technical_indicators
    
    mode_str = "LIVE" if live_trading else "PAPER"
    
    try:
        from the_alchemiser.core.telegram_utils import send_telegram_message
        from the_alchemiser.execution.multi_strategy_trader import MultiStrategyAlpacaTrader, StrategyType
        from the_alchemiser.execution.alpaca_trader import is_market_open
        
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
            from rich.console import Console
            Console().print("[bold red]❌ Market is CLOSED. No trades will be placed.[/bold red]")
            send_telegram_message("❌ Market is CLOSED. No trades will be placed.")
            return "market_closed"
        
        # Generate strategy signals to get technical indicators for display
        render_header("Analyzing market conditions...", "Multi-Strategy Trading")
        strategy_signals = trader.strategy_manager.run_all_strategies()[0]
        
        # Display technical indicators
        render_technical_indicators(strategy_signals)
        
        # Execute multi-strategy
        result = trader.execute_multi_strategy()
        
        # Display results
        trader.display_multi_strategy_summary(result)
        
        # Only send Telegram notification in live trading mode
        if live_trading:
            try:
                message = build_multi_strategy_message(result, mode_str)
                send_telegram_message(message)
            except Exception as e:
                from rich.console import Console
                Console().print(f"[bold yellow]⚠️ Telegram notification failed: {e}[/bold yellow]")
        
        return result.success
        
    except Exception as e:
        from rich.console import Console
        Console().print(f"[bold red]❌ Error: {e}[/bold red]")
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
    from the_alchemiser.core.ui.cli_formatter import render_header, render_footer
    
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
    render_header("Multi-Strategy Nuclear Bot", f"{args.mode.upper()} | {mode_label}")
    
    success = False
    try:
        if args.mode == 'bot':
            # Display multi-strategy signals (no trading)
            success = run_all_signals_display()
        elif args.mode == 'trade':
            # Multi-strategy trading
            result = run_multi_strategy_trading(live_trading=args.live, ignore_market_hours=args.ignore_market_hours)
            if result == "market_closed":
                render_footer("Market closed - no action taken")
                return True
            else:
                success = result
    except Exception as e:
        from rich.console import Console
        Console().print(f"[bold red]❌ Error: {e}[/bold red]")
        success = False
    
    if success:
        render_footer("Operation completed successfully!")
        return True
    else:
        render_footer("Operation failed!")
        return False

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
