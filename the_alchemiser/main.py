#!/usr/bin/env python3
"""Main Entry Point for The Alchemiser Trading Engine.

This module provides the command-line interface and orchestration for the multi-strategy
trading system. It handles argument parsing, logging configuration, and delegates business
logic to specialized components in the core/ package.

The main functions support:
    - Signal analysis mode: Display strategy signals without executing trades
    - Trading mode: Execute multi-strategy trading with Nuclear and TECL strategies
    - Paper and live trading modes with market hours validation
    - Rich console output with email notifications for both paper and live trading

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

# Optional rich import - only for CLI usage
try:
    from rich.console import Console
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

from the_alchemiser.core.config import load_settings, Settings
from the_alchemiser.core.trading.strategy_manager import StrategyType
from the_alchemiser.core.logging.logging_utils import setup_logging, get_logger


def configure_application_logging():
    """Configure centralized logging for the application."""
    import os
    
    # Check if we're in production (AWS Lambda or similar)
    is_production = os.getenv('AWS_LAMBDA_FUNCTION_NAME') is not None
    
    if is_production:
        from the_alchemiser.core.logging.logging_utils import configure_production_logging
        configure_production_logging(
            log_level=logging.INFO,
            log_file=None  # Use CloudWatch in Lambda
        )
    else:
        # Development/CLI environment
        setup_logging(
            log_level=logging.WARNING,  # Cleaner CLI output
            console_level=logging.WARNING,
            suppress_third_party=True,
            structured_format=False  # Human-readable for CLI
        )






def generate_multi_strategy_signals(settings: Settings) -> tuple:
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
        manager = MultiStrategyManager(shared_data_provider=shared_data_provider, config=settings)
        strategy_signals, consolidated_portfolio, _ = manager.run_all_strategies()
        return manager, strategy_signals, consolidated_portfolio
    except Exception as e:
        return None, None, None

def run_all_signals_display(settings: Settings | None = None):
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
    
    settings = settings or load_settings()
    try:
        # Generate multi-strategy signals (this includes both Nuclear and TECL)
        manager, strategy_signals, consolidated_portfolio = generate_multi_strategy_signals(settings)
        if not strategy_signals:
            logger = get_logger(__name__)
            logger.error("Failed to generate multi-strategy signals")
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
        
        # Rich console for CLI output (optional)
        if HAS_RICH:
        # Rich console for CLI output (optional)
        if HAS_RICH:
            from rich.console import Console
            from rich.panel import Panel
            console = Console()
        
        # Get actual allocation percentages from config
        allocations = settings.strategy.default_strategy_allocations
        
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
        
        # Display strategy summary (if rich is available)
        if HAS_RICH and 'console' in locals():
            console.print(Panel(strategy_summary, title="Strategy Summary", border_style="blue"))
        else:
            # Use logger from function scope
            from the_alchemiser.core.logging.logging_utils import get_logger
            local_logger = get_logger(__name__)
            local_logger.info(f"Strategy Summary:\n{strategy_summary}")
        
        render_footer("Signal analysis completed successfully!")
        return True
    except Exception as e:
        logger = get_logger(__name__)
        logger.exception("Error analyzing strategies: %s", e)
        return False


def run_multi_strategy_trading(
    live_trading: bool = False, ignore_market_hours: bool = False, settings: Settings | None = None
) -> bool | str:
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
        - Email notifications are sent for both paper and live trading modes
        - Technical indicators and strategy signals are displayed before execution
        - Error notifications are sent via email if configured
    """
    from the_alchemiser.core.ui.cli_formatter import render_header
    
    mode_str = "LIVE" if live_trading else "PAPER"
    
    settings = settings or load_settings()
    try:
        from the_alchemiser.execution.trading_engine import TradingEngine, StrategyType
        from the_alchemiser.execution.smart_execution import is_market_open

        trader = TradingEngine(
            paper_trading=not live_trading,
            ignore_market_hours=ignore_market_hours,
            config=settings
        )
        
        # Check market hours unless ignore_market_hours is set
        if not ignore_market_hours and not is_market_open(trader.trading_client):
            logger = get_logger(__name__)
            logger.warning("Market is closed. No trades will be placed.")
            
            from the_alchemiser.core.ui.email_utils import send_email_notification, build_error_email_html
            from the_alchemiser.core.ui.email.config import is_neutral_mode_enabled
            
            # Check if neutral mode is enabled
            neutral_mode = is_neutral_mode_enabled()
            subject_suffix = " (Neutral Mode)" if neutral_mode else ""
            
            html_content = build_error_email_html(
                "Market Closed Alert", 
                "Market is currently closed. No trades will be placed."
            )
            send_email_notification(
                subject=f"📈 The Alchemiser - Market Closed Alert{subject_suffix}",
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
        if HAS_RICH:
            from rich.console import Console
            console = Console()
            console.print("[dim]🔄 Executing trading strategy...[/dim]")
        else:
            from the_alchemiser.core.logging.logging_utils import get_logger
            local_logger = get_logger(__name__)
            local_logger.info("🔄 Executing trading strategy...")
        
        result = trader.execute_multi_strategy()
        
        # Display results
        trader.display_multi_strategy_summary(result)
        
        # Send email notification for both paper and live trading
        try:
            from the_alchemiser.core.ui.email_utils import send_email_notification, build_multi_strategy_email_html
            from the_alchemiser.core.ui.email.config import is_neutral_mode_enabled
            from the_alchemiser.core.ui.email.templates import EmailTemplates
            
            # Check if neutral mode is enabled
            neutral_mode = is_neutral_mode_enabled()
            
            if neutral_mode:
                # Use neutral template - build the data in the same format
                account_before = getattr(result, 'account_info_before', {})
                account_after = getattr(result, 'account_info_after', {})
                orders_executed = getattr(result, 'orders_executed', [])
                final_portfolio_state = getattr(result, 'final_portfolio_state', {})
                open_positions = account_after.get('open_positions', [])
                
                html_content = EmailTemplates.build_trading_report_neutral(
                    mode=mode_str,
                    success=result.success,
                    account_before=account_before,
                    account_after=account_after,
                    positions=final_portfolio_state,
                    orders=orders_executed,
                    signal=None,  # We can add strategy signals later if needed
                    portfolio_history=None,
                    open_positions=open_positions
                )
                subject_suffix = " (Neutral Mode)"
            else:
                # Use regular template with dollar values
                html_content = build_multi_strategy_email_html(result, mode_str)
                subject_suffix = ""
            
            send_email_notification(
                subject=f"📈 The Alchemiser - {mode_str.upper()} Multi-Strategy Report{subject_suffix}",
                html_content=html_content,
                text_content=f"Multi-strategy execution completed. Success: {result.success}"
            )
        except Exception as e:
            logger = get_logger(__name__)
            logger.warning("Email notification failed: %s", e)
        
        return result.success
        
    except Exception as e:
        logger = get_logger(__name__)
        logger.exception("Error in multi-strategy trading: %s", e)
        return False



def main(argv=None, settings: Settings | None = None):
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
    
    # Setup logging early to suppress chattiness
    configure_application_logging()
    
    settings = settings or load_settings()
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
            success = run_all_signals_display(settings)
        elif args.mode == 'trade':
            # Multi-strategy trading
            result = run_multi_strategy_trading(
                live_trading=args.live,
                ignore_market_hours=args.ignore_market_hours,
                settings=settings,
            )
            if result == "market_closed":
                render_footer("Market closed - no action taken")
                return True
            else:
                success = result
    except Exception as e:
        logger = get_logger(__name__)
        logger.exception("Error in main application: %s", e)
        success = False
    
    if success:
        render_footer("Operation completed successfully!")
        return True
    else:
        render_footer("Operation failed!")
        return False

if __name__ == "__main__":
    sys.exit(0 if main(settings=load_settings()) else 1)
