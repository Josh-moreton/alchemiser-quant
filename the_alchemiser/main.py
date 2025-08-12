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
import logging
import os
import sys
from datetime import datetime

# TODO: Add these imports once types are fully implemented:
# from .core.types import StrategySignal
# from .core.trading.strategy_manager import MultiStrategyManager, StrategyType

# Optional rich import - only for CLI usage
try:
    # Check if rich is available
    import importlib.util

    HAS_RICH = importlib.util.find_spec("rich") is not None
except ImportError:
    HAS_RICH = False

# DI imports
from the_alchemiser.container.application_container import ApplicationContainer
from the_alchemiser.domain.strategies.strategy_manager import StrategyType
from the_alchemiser.infrastructure.config import Settings, load_settings
from the_alchemiser.infrastructure.logging.logging_utils import get_logger, setup_logging
from the_alchemiser.services.exceptions import (
    ConfigurationError,
    DataProviderError,
    NotificationError,
    StrategyExecutionError,
    TradingClientError,
)
from the_alchemiser.services.service_factory import ServiceFactory

# Global DI container
_di_container = None


def initialize_dependency_injection() -> None:
    """Initialize dependency injection system."""
    global _di_container

    _di_container = ApplicationContainer()
    ServiceFactory.initialize(_di_container)
    logger = get_logger(__name__)
    logger.info("Dependency injection initialized")


def configure_application_logging() -> None:
    """Configure centralized logging for the application."""

    # Check if we're in production (AWS Lambda or similar)
    is_production = os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None

    if is_production:
        from the_alchemiser.infrastructure.logging.logging_utils import configure_production_logging

        configure_production_logging(
            log_level=logging.INFO,
            log_file=None,  # Use CloudWatch in Lambda
        )
    else:
        # Development/CLI environment
        setup_logging(
            log_level=logging.WARNING,  # Cleaner CLI output
            console_level=logging.WARNING,
            suppress_third_party=True,
            structured_format=False,  # Human-readable for CLI
        )


def run_all_signals_display(
    settings: Settings | None = None,
) -> bool:
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
    from the_alchemiser.interface.cli.cli_formatter import (
        render_footer,
        render_header,
        render_portfolio_allocation,
        render_strategy_signals,
    )

    render_header("MULTI-STRATEGY SIGNAL ANALYSIS", f"Analysis at {datetime.now()}")

    settings = settings or load_settings()
    try:
        from the_alchemiser.application.trading_engine import TradingEngine

        # Generate multi-strategy signals using DI
        trader = TradingEngine.create_with_di(container=_di_container)
        strategy_signals, consolidated_portfolio, _ = trader.strategy_manager.run_all_strategies()
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
        if nuclear_signal.get("action") == "BUY":
            if nuclear_signal.get("symbol") == "UVXY_BTAL_PORTFOLIO":
                nuclear_positions = 2  # UVXY and BTAL
            elif nuclear_signal.get("symbol") == "UVXY":
                nuclear_positions = 1  # Just UVXY
            else:
                nuclear_positions = 3  # Default for other portfolios
        else:
            nuclear_positions = 0
        tecl_positions = 1 if tecl_signal.get("action") == "BUY" else 0

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
        nuclear_pct = int(allocations.get("nuclear", 0) * 100)
        tecl_pct = int(allocations.get("tecl", 0) * 100)
        klm_pct = int(allocations.get("klm", 0) * 100)

        if nuclear_pct > 0:
            strategy_lines.append(
                f"[bold cyan]NUCLEAR:[/bold cyan] {nuclear_positions} positions, {nuclear_pct}% allocation"
            )
        if tecl_pct > 0:
            strategy_lines.append(
                f"[bold cyan]TECL:[/bold cyan] {tecl_positions} positions, {tecl_pct}% allocation"
            )
        if klm_pct > 0:
            # Count KLM positions from consolidated portfolio
            klm_positions = 1  # Default to 1 position for KLM
            if consolidated_portfolio:
                # Count symbols that might be from KLM (if we can determine)
                klm_symbols = set()
                if StrategyType.KLM in strategy_signals:
                    klm_signal = strategy_signals[StrategyType.KLM]
                    if isinstance(klm_signal.get("symbol"), str):
                        klm_symbols.add(klm_signal["symbol"])
                    elif isinstance(klm_signal.get("symbol"), dict):
                        klm_symbols.update(klm_signal["symbol"].keys())
                klm_positions = len([s for s in klm_symbols if s in consolidated_portfolio]) or 1
            strategy_lines.append(
                f"[bold cyan]KLM:[/bold cyan] {klm_positions} positions, {klm_pct}% allocation"
            )

        strategy_summary = "\n".join(strategy_lines)

        # Display strategy summary (if rich is available)
        if HAS_RICH and "console" in locals():
            console.print(Panel(strategy_summary, title="Strategy Summary", border_style="blue"))
        else:
            # Use logger from module-level import
            local_logger = get_logger(__name__)
            local_logger.info(f"Strategy Summary:\n{strategy_summary}")

        render_footer("Signal analysis completed successfully!")
        return True
    except (DataProviderError, StrategyExecutionError) as e:
        from the_alchemiser.infrastructure.logging.logging_utils import log_error_with_context

        logger = get_logger(__name__)
        log_error_with_context(
            logger,
            e,
            "strategy_analysis",
            function="run_all_signals_display",
            error_type=type(e).__name__,
        )
        logger.exception("Error analyzing strategies: %s", e)
        return False
    except (ImportError, AttributeError, ValueError, OSError) as e:
        from the_alchemiser.infrastructure.logging.logging_utils import log_error_with_context

        logger = get_logger(__name__)
        log_error_with_context(
            logger,
            e,
            "strategy_display_error",
            function="run_all_signals_display",
            error_type=type(e).__name__,
        )
        logger.exception("Display error analyzing strategies: %s", e)
        return False


def run_multi_strategy_trading(
    live_trading: bool = False,
    ignore_market_hours: bool = False,
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
    from the_alchemiser.interface.cli.cli_formatter import render_header

    mode_str = "LIVE" if live_trading else "PAPER"

    try:
        from the_alchemiser.application.smart_execution import is_market_open
        from the_alchemiser.application.trading_engine import TradingEngine

        trader = TradingEngine.create_with_di(
            container=_di_container, ignore_market_hours=ignore_market_hours
        )
        trader.paper_trading = not live_trading

        # Check market hours unless ignore_market_hours is set
        if not ignore_market_hours and not is_market_open(trader.trading_client):
            logger = get_logger(__name__)
            logger.warning("Market is closed. No trades will be placed.")

            from the_alchemiser.interface.email.email_utils import (
                build_error_email_html,
                send_email_notification,
            )

            html_content = build_error_email_html(
                "Market Closed Alert", "Market is currently closed. No trades will be placed."
            )
            send_email_notification(
                subject="📈 The Alchemiser - Market Closed Alert",
                html_content=html_content,
                text_content="Market is CLOSED. No trades will be placed.",
            )
            return "market_closed"

        # Generate strategy signals for display
        render_header("Analyzing market conditions...", "Multi-Strategy Trading")
        strategy_signals, consolidated_portfolio, strategy_attribution = (
            trader.strategy_manager.run_all_strategies()
        )

        # Display strategy signals
        from the_alchemiser.interface.cli.cli_formatter import render_strategy_signals

        render_strategy_signals(strategy_signals)

        # Display portfolio rebalancing summary before execution
        try:
            account_info = trader.get_account_info()
            current_positions = trader.get_positions_dict()
            if account_info and consolidated_portfolio:
                trader.display_target_vs_current_allocations(
                    consolidated_portfolio, account_info, current_positions
                )
        except Exception as e:
            logging.warning(f"Could not display portfolio rebalancing summary: {e}")

        # Execute multi-strategy with clean progress indication
        if HAS_RICH:
            from rich.console import Console

            console = Console()
            console.print("[dim]🔄 Executing trading strategy...[/dim]")
        else:
            # Use logger from module-level import
            local_logger = get_logger(__name__)
            local_logger.info("🔄 Executing trading strategy...")

        result = trader.execute_multi_strategy()

        # Display results
        trader.display_multi_strategy_summary(result)

        # Send email notification for both paper and live trading
        try:
            from the_alchemiser.interface.email.email_utils import send_email_notification
            from the_alchemiser.interface.email.templates import EmailTemplates

            # Enrich result with fresh position data for email templates
            try:
                fresh_positions = trader.get_positions_dict()
                # Add fresh positions to result object for email template access
                if (
                    hasattr(result, "final_portfolio_state")
                    and result.final_portfolio_state is not None
                ):
                    result.final_portfolio_state["current_positions"] = fresh_positions
                else:
                    result.final_portfolio_state = {"current_positions": fresh_positions}
            except Exception as e:
                logging.warning(f"Could not add fresh position data to result: {e}")

            # Always use neutral multi-strategy template (no financial values)
            html_content = EmailTemplates.build_multi_strategy_report_neutral(result, mode_str)

            send_email_notification(
                subject=f"📈 The Alchemiser - {mode_str.upper()} Multi-Strategy Report",
                html_content=html_content,
                text_content=f"Multi-strategy execution completed. Success: {result.success}",
            )
        except NotificationError as e:
            from the_alchemiser.infrastructure.logging.logging_utils import log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "email_notification",
                function="run_multi_strategy_trading",
                notification_type="trading_report",
            )
            logger.warning("Email notification failed: %s", e)
        except (ConnectionError, TimeoutError, ValueError, AttributeError) as e:
            from the_alchemiser.infrastructure.logging.logging_utils import log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "email_formatting_error",
                function="run_multi_strategy_trading",
                error_type=type(e).__name__,
            )
            logger.warning("Email formatting/connection error: %s", e)

        return result.success

    except (DataProviderError, StrategyExecutionError, TradingClientError) as e:
        from the_alchemiser.infrastructure.logging.logging_utils import log_error_with_context

        logger = get_logger(__name__)
        log_error_with_context(
            logger,
            e,
            "multi_strategy_trading",
            function="run_multi_strategy_trading",
            error_type=type(e).__name__,
            live_trading=live_trading,
            ignore_market_hours=ignore_market_hours,
        )
        logger.exception("Error in multi-strategy trading: %s", e)

        # Enhanced error handling with detailed reporting
        try:
            from the_alchemiser.services.error_handler import (
                handle_trading_error,
                send_error_notification_if_needed,
            )

            handle_trading_error(
                error=e,
                context="multi-strategy trading execution",
                component="main.run_multi_strategy_trading",
                additional_data={
                    "mode": mode_str,
                    "live_trading": live_trading,
                    "ignore_market_hours": ignore_market_hours,
                },
            )

            # Send detailed error notification if needed
            send_error_notification_if_needed()

        except NotificationError as notification_error:
            logger.warning("Failed to send error notification: %s", notification_error)

        return False
    except (OSError, ImportError, ConfigurationError, ValueError) as e:
        from the_alchemiser.infrastructure.logging.logging_utils import log_error_with_context

        logger = get_logger(__name__)
        log_error_with_context(
            logger,
            e,
            "system_configuration_error",
            function="run_multi_strategy_trading",
            error_type=type(e).__name__,
            live_trading=live_trading,
            ignore_market_hours=ignore_market_hours,
        )
        logger.exception("System/configuration error in multi-strategy trading: %s", e)

        # For system errors, still try to send notification
        try:
            from the_alchemiser.services.error_handler import (
                handle_trading_error,
                send_error_notification_if_needed,
            )

            handle_trading_error(
                error=e,
                context="multi-strategy trading execution - unexpected error",
                component="main.run_multi_strategy_trading",
                additional_data={
                    "mode": mode_str,
                    "live_trading": live_trading,
                    "ignore_market_hours": ignore_market_hours,
                    "original_error": type(e).__name__,
                },
            )

            send_error_notification_if_needed()

        except (
            NotificationError,
            ConnectionError,
            TimeoutError,
            AttributeError,
        ) as notification_error:
            logger.warning("Failed to send error notification: %s", notification_error)

        return False


def main(argv: list[str] | None = None, settings: Settings | None = None) -> bool:
    """Main entry point for the Multi-Strategy Quantitative Trading System.

    Provides command-line interface for running the trading system in different modes.
    Supports both signal analysis and actual trading execution.

    Args:
        argv: Command line arguments. If None, uses sys.argv.

    Returns:
        True if operation completed successfully, False otherwise.

    Modes:
        signal: Display multi-strategy signals without trading
        trade: Execute multi-strategy trading (Nuclear + TECL combined)

    Trading Modes:
        Default: Paper trading (safe default)
        --live: Live trading (requires explicit flag)

    Options:
        --ignore-market-hours: Override market hours check for testing

    Examples:
        $ python main.py signal                 # Show signals only
        $ python main.py trade                  # Paper trading
        $ python main.py trade --live           # Live trading
        $ python main.py trade --ignore-market-hours  # Test during market close
    """
    from the_alchemiser.interface.cli.cli_formatter import render_footer, render_header

    # Setup logging early to suppress chattiness
    configure_application_logging()

    settings = settings or load_settings()
    parser = argparse.ArgumentParser(description="Multi-Strategy Quantitative Trading System")
    parser.add_argument(
        "mode",
        choices=["signal", "trade"],
        help="Operation mode: signal (show signals), trade (execute trading)",
    )

    # Trading mode selection
    parser.add_argument(
        "--live", action="store_true", help="Use live trading (default is paper trading)"
    )

    # Market hours override
    parser.add_argument(
        "--ignore-market-hours",
        action="store_true",
        help="Ignore market hours and run during closed market (for testing)",
    )

    args = parser.parse_args(argv)

    # Initialize DI
    initialize_dependency_injection()

    mode_label = "LIVE TRADING ⚠️" if args.mode == "trade" and args.live else "Paper Trading"
    render_header(
        "Multi-Strategy Quantitative Trading System",
        f"{args.mode.upper()} | {mode_label}",
    )

    success: bool | str = False
    try:
        if args.mode == "signal":
            # Display multi-strategy signals (no trading)
            success = run_all_signals_display(settings)
        elif args.mode == "trade":
            # Multi-strategy trading
            result = run_multi_strategy_trading(
                live_trading=args.live,
                ignore_market_hours=args.ignore_market_hours,
            )
            if result == "market_closed":
                render_footer("Market closed - no action taken")
                return True
            else:
                success = result
    except (DataProviderError, StrategyExecutionError, TradingClientError) as e:
        from the_alchemiser.infrastructure.logging.logging_utils import log_error_with_context

        logger = get_logger(__name__)
        log_error_with_context(
            logger,
            e,
            "main_application",
            function="main",
            error_type=type(e).__name__,
            mode=args.mode,
            live_trading=getattr(args, "live", False),
        )
        logger.exception("Known error in main application: %s", e)
        success = False
    except (ConfigurationError, ValueError, AttributeError, OSError, ImportError) as e:
        from the_alchemiser.infrastructure.logging.logging_utils import log_error_with_context

        logger = get_logger(__name__)
        log_error_with_context(
            logger,
            e,
            "main_application_system_error",
            function="main",
            error_type=type(e).__name__,
            mode=args.mode,
            live_trading=getattr(args, "live", False),
        )
        logger.exception("System error in main application: %s", e)
        success = False

    if success:
        render_footer("Operation completed successfully!")
        return True
    else:
        render_footer("Operation failed!")
        return False


if __name__ == "__main__":
    sys.exit(0 if main(settings=load_settings()) else 1)
