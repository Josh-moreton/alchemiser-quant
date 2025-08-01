#!/usr/bin/env python3
"""Main Entry Point for The Alchemiser Trading Engine.

This module provides the command-line interface and orchestration for the multi-strategy
trading system. It handles argument parsing, logging configuration, and delegates business
logic to specialized components in the core/ package.

The main functions support:
    - Signal analysis mode: Display strategy signals without executing trades
    - Trading mode: Execute multi-strategy trading with Nuclear and TECL strategies
    - Paper and live trading modes with market hours validation
    - Rich console output with email notifications for live trading

Example:
    Run signal analysis only:
        $ python main.py bot
        
    Execute paper trading:
        $ python main.py trade
        
    Execute live trading:
        $ python main.py trade --live
"""

# Standard library imports
import argparse
from datetime import datetime
import traceback
import sys
import os
import logging
from the_alchemiser.core.config import get_config
from the_alchemiser.core.trading.strategy_manager import StrategyType

# Load config once at module level
config = get_config()
logging_config = config['logging']

def setup_file_logging():
    """Configure logging for both local and cloud environments.
    
    Sets up logging to send all logs to S3 in Lambda environments and files locally.
    Configures appropriate log levels for third-party libraries to reduce noise.
    
    Note:
        In production, logging is handled by CloudWatch and S3 for trades/signals JSON.
        File logging setup is removed in favor of cloud-based logging.
    """
    import os
    from the_alchemiser.core.utils.s3_utils import S3FileHandler
    root_logger = logging.getLogger()
    
    # Set to WARNING level for cleaner CLI output - important info shown via Rich
    root_logger.setLevel(logging.WARNING)
    root_logger.handlers.clear()  # Remove any existing handlers

    # Logging now handled by Cloudwatch and S3 trades/signals JSON. File logging setup removed.

    # Set appropriate levels for third-party loggers
    logging.getLogger('botocore').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('alpaca').setLevel(logging.WARNING)
    logging.getLogger('boto3').setLevel(logging.WARNING)
    logging.getLogger('s3transfer').setLevel(logging.WARNING)

# Initialize file-based logging
setup_file_logging()




def generate_multi_strategy_signals():
    """Generate signals for all strategies and return consolidated results.
    
    Creates a shared data provider and multi-strategy manager to generate signals
    for both Nuclear and TECL strategies with configurable allocation weights.
    
    Returns:
        tuple: A 3-tuple containing:
            - manager (MultiStrategyManager): The strategy manager instance
            - strategy_signals (dict): Individual strategy signals by type
            - consolidated_portfolio (dict): Consolidated portfolio allocation
            
        Returns (None, None, None) if signal generation fails.
        
    Example:
        >>> manager, signals, portfolio = generate_multi_strategy_signals()
        >>> if signals:
        ...     nuclear_signal = signals[StrategyType.NUCLEAR]
        ...     tecl_signal = signals[StrategyType.TECL]
        
    Raises:
        Exception: If data provider initialization or strategy execution fails.
    """
    from the_alchemiser.core.trading.strategy_manager import MultiStrategyManager, StrategyType
    from the_alchemiser.core.data.data_provider import UnifiedDataProvider
    
    try:
        # Create shared UnifiedDataProvider once
        shared_data_provider = UnifiedDataProvider(paper_trading=True)
        # Pass shared data provider to MultiStrategyManager - it will read config allocations automatically
        manager = MultiStrategyManager(shared_data_provider=shared_data_provider, config=config)
        strategy_signals, consolidated_portfolio, _ = manager.run_all_strategies()
        return manager, strategy_signals, consolidated_portfolio
    except Exception as e:
        return None, None, None

def run_all_signals_display():
    """Generate and display multi-strategy signals without executing trades.
    
    Shows comprehensive analysis including Nuclear and TECL strategy signals,
    technical indicators, and consolidated multi-strategy portfolio allocation.
    This is a read-only operation that performs analysis without trading.
    
    Returns:
        bool: True if signals were successfully generated and displayed,
              False if signal generation failed.
              
    Note:
        This function displays results using Rich console formatting with:
        - Technical indicators for all tracked symbols
        - Individual strategy signals and reasoning
        - Consolidated portfolio allocation
        - Strategy execution summary
    """
    from the_alchemiser.core.ui.cli_formatter import (
        render_header, render_footer, 
        render_strategy_signals, render_portfolio_allocation
    )
    
    render_header("MULTI-STRATEGY SIGNAL ANALYSIS", f"Analysis at {datetime.now()}")
    
    try:
        # Generate multi-strategy signals (this includes both Nuclear and TECL)
        manager, strategy_signals, consolidated_portfolio = generate_multi_strategy_signals()
        if not strategy_signals:
            from rich.console import Console
            Console().print("[bold red]Failed to generate multi-strategy signals[/bold red]")
            return False
            
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
        
        # Get actual allocation percentages from config
        from the_alchemiser.core.config import Config
        config = Config()
        allocations = config['strategy']['default_strategy_allocations']
        
        # Build strategy summary dynamically for all active strategies
        strategy_lines = []
        
        # Count positions for each strategy type
        nuclear_pct = int(allocations.get('nuclear', 0) * 100)
        tecl_pct = int(allocations.get('tecl', 0) * 100)
        klm_pct = int(allocations.get('klm', 0) * 100)
        
        if nuclear_pct > 0:
            strategy_lines.append(f"[bold cyan]NUCLEAR:[/bold cyan] {nuclear_positions} positions, {nuclear_pct}% allocation")
        if tecl_pct > 0:
            strategy_lines.append(f"[bold cyan]TECL:[/bold cyan] {tecl_positions} positions, {tecl_pct}% allocation")
        if klm_pct > 0:
            # Count KLM positions from consolidated portfolio
            klm_positions = 1  # Default to 1 position for KLM
            if consolidated_portfolio:
                # Count symbols that might be from KLM (if we can determine)
                klm_symbols = set()
                if StrategyType.KLM in strategy_signals:
                    klm_signal = strategy_signals[StrategyType.KLM]
                    if isinstance(klm_signal.get('symbol'), str):
                        klm_symbols.add(klm_signal['symbol'])
                    elif isinstance(klm_signal.get('symbol'), dict):
                        klm_symbols.update(klm_signal['symbol'].keys())
                klm_positions = len([s for s in klm_symbols if s in consolidated_portfolio]) or 1
            strategy_lines.append(f"[bold cyan]KLM:[/bold cyan] {klm_positions} positions, {klm_pct}% allocation")
        
        strategy_summary = "\n".join(strategy_lines)
        
        console.print(Panel(strategy_summary, title="Strategy Summary", border_style="blue"))
        
        render_footer("Signal analysis completed successfully!")
        return True
    except Exception as e:
        from rich.console import Console
        Console().print(f"[bold red]Error analyzing strategies: {e}[/bold red]")
        import traceback
        traceback.print_exc()
        return False


def run_multi_strategy_trading(live_trading: bool = False, ignore_market_hours: bool = False):
    """Execute multi-strategy trading with both Nuclear and TECL strategies.
    
    Initializes the trading engine with equal allocation between Nuclear and TECL
    strategies, checks market hours, generates signals, and executes trades.
    
    Args:
        live_trading: True for live trading, False for paper trading.
            Defaults to False for safety.
        ignore_market_hours: Whether to ignore market hours and trade
            during closed market periods. Defaults to False.
                                  
    Returns:
        Union[bool, str]: Returns True if trading was successful, False if failed,
            or "market_closed" if market is closed and trading was skipped.
                         
    Note:
        - Market hours are checked unless ignore_market_hours is True
        - Email notifications are only sent in live trading mode
        - Technical indicators and strategy signals are displayed before execution
        - Error notifications are sent via email if configured
    """
    from the_alchemiser.core.ui.cli_formatter import render_header
    
    mode_str = "LIVE" if live_trading else "PAPER"
    
    try:
        from the_alchemiser.execution.trading_engine import TradingEngine, StrategyType
        from the_alchemiser.execution.smart_execution import is_market_open
        
        # Initialize multi-strategy trader - TradingEngine will read config allocations automatically
        trader = TradingEngine(
            paper_trading=not live_trading,
            ignore_market_hours=ignore_market_hours,
            config=config
        )
        
        # Check market hours unless ignore_market_hours is set
        if not ignore_market_hours and not is_market_open(trader.trading_client):
            from rich.console import Console
            from the_alchemiser.core.ui.email_utils import send_email_notification, build_error_email_html
            Console().print("[bold red]Market is CLOSED. No trades will be placed.[/bold red]")
            html_content = build_error_email_html(
                "Market Closed Alert", 
                "Market is currently closed. No trades will be placed."
            )
            send_email_notification(
                subject="📈 The Alchemiser - Market Closed Alert",
                html_content=html_content,
                text_content="Market is CLOSED. No trades will be placed."
            )
            return "market_closed"
        
        # Generate strategy signals for display
        render_header("Analyzing market conditions...", "Multi-Strategy Trading")
        strategy_signals = trader.strategy_manager.run_all_strategies()[0]
        
        # Display strategy signals
        from the_alchemiser.core.ui.cli_formatter import render_strategy_signals
        render_strategy_signals(strategy_signals)
        
        # Execute multi-strategy with clean progress indication
        from rich.console import Console
        
        console = Console()
        console.print("[dim]🔄 Executing trading strategy...[/dim]")
        
        result = trader.execute_multi_strategy()
        
        # Display results
        trader.display_multi_strategy_summary(result)
        
        # Only send email notification in live trading mode
        if live_trading:
            try:
                from the_alchemiser.core.ui.email_utils import send_email_notification, build_multi_strategy_email_html
                html_content = build_multi_strategy_email_html(result, mode_str)
                send_email_notification(
                    subject=f"📈 The Alchemiser - {mode_str.upper()} Multi-Strategy Report",
                    html_content=html_content,
                    text_content=f"Multi-strategy execution completed. Success: {result.success}"
                )
            except Exception as e:
                from rich.console import Console
                Console().print(f"[bold yellow]Email notification failed: {e}[/bold yellow]")
        
        return result.success
        
    except Exception as e:
        from rich.console import Console
        Console().print(f"[bold red]Error: {e}[/bold red]")
        return False



def main(argv=None):
    """Main entry point for the Multi-Strategy Nuclear Trading Bot.
    
    Provides command-line interface for running the trading bot in different modes.
    Supports both signal analysis and actual trading execution.
    
    Args:
        argv: Command line arguments. If None, uses sys.argv.
        
    Returns:
        True if operation completed successfully, False otherwise.
        
    Modes:
        bot: Display multi-strategy signals without trading
        trade: Execute multi-strategy trading (Nuclear + TECL combined)
    
    Trading Modes:
        Default: Paper trading (safe default)
        --live: Live trading (requires explicit flag)
        
    Options:
        --ignore-market-hours: Override market hours check for testing
        
    Examples:
        $ python main.py bot                    # Show signals only
        $ python main.py trade                  # Paper trading
        $ python main.py trade --live           # Live trading
        $ python main.py trade --ignore-market-hours  # Test during market close
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
        Console().print(f"[bold red]Error: {e}[/bold red]")
        success = False
    
    if success:
        render_footer("Operation completed successfully!")
        return True
    else:
        render_footer("Operation failed!")
        return False

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
