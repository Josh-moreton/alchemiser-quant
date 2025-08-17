#!/usr/bin/env python3
"""Main Entry Point for The Alchemiser Trading System.

A clean, focused entry point for the multi-strategy quantitative trading system.
Supports signal analysis and trading execution with dependency injection.
"""

import argparse
import logging
import os
import sys
from typing import Optional

from the_alchemiser.domain.strategies.strategy_manager import StrategyType
from the_alchemiser.infrastructure.config import Settings, load_settings
from the_alchemiser.infrastructure.logging.logging_utils import get_logger, setup_logging
from the_alchemiser.services.errors.exceptions import (
    ConfigurationError,
    DataProviderError,
    StrategyExecutionError,
    TradingClientError,
)

# DI imports (optional)
try:
    from the_alchemiser.container.application_container import ApplicationContainer
    from the_alchemiser.services.shared.service_factory import ServiceFactory

    DI_AVAILABLE = True
except ImportError:
    DI_AVAILABLE = False

# Global DI container
# Use Optional for proper type inference by static type checkers
_di_container: Optional["ApplicationContainer"] = None


class TradingSystem:
    """Main trading system orchestrator."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or load_settings()
        self.logger = get_logger(__name__)
        self._initialize_di()

    def _initialize_di(self) -> None:
        """Initialize dependency injection system."""
        global _di_container

        if DI_AVAILABLE:
            _di_container = ApplicationContainer()
            ServiceFactory.initialize(_di_container)
            self.logger.info("Dependency injection initialized")
        else:
            self.logger.error("DI not available - system requires dependency injection")
            raise ConfigurationError("Dependency injection system is required but not available")

    def _get_strategy_allocations(self) -> dict[StrategyType, float]:
        """Extract strategy allocations from configuration."""
        return {
            StrategyType.NUCLEAR: self.settings.strategy.default_strategy_allocations["nuclear"],
            StrategyType.TECL: self.settings.strategy.default_strategy_allocations["tecl"],
            StrategyType.KLM: self.settings.strategy.default_strategy_allocations["klm"],
        }

    def analyze_signals(self) -> bool:
        """Generate and display strategy signals without trading."""
        from the_alchemiser.interface.cli.signal_analyzer import SignalAnalyzer

        try:
            analyzer = SignalAnalyzer(self.settings)
            return analyzer.run()
        except (DataProviderError, StrategyExecutionError) as e:
            self.logger.error(f"Signal analysis failed: {e}")
            return False

    def execute_trading(
        self, live_trading: bool = False, ignore_market_hours: bool = False
    ) -> bool:
        """Execute multi-strategy trading."""
        from the_alchemiser.interface.cli.trading_executor import TradingExecutor

        try:
            executor = TradingExecutor(
                settings=self.settings,
                live_trading=live_trading,
                ignore_market_hours=ignore_market_hours,
            )
            return executor.run()
        except (TradingClientError, StrategyExecutionError) as e:
            self.logger.error(f"Trading execution failed: {e}")
            return False

    def generate_monthly_summary(
        self, target_month: str | None = None, live_trading: bool = False
    ) -> bool:
        """Generate and send monthly trading summary."""
        from datetime import datetime

        from the_alchemiser.application.reporting.monthly_summary_service import (
            MonthlySummaryService,
        )
        from the_alchemiser.interface.email.client import send_email_notification
        from the_alchemiser.interface.email.templates.monthly_summary import MonthlySummaryBuilder

        try:
            # Parse target month if provided
            target_month_dt = None
            if target_month:
                try:
                    target_month_dt = datetime.strptime(target_month, "%Y-%m")
                except ValueError:
                    self.logger.error(f"Invalid month format: {target_month}. Use YYYY-MM format.")
                    return False

            paper_trading = not live_trading

            # Get API credentials
            from the_alchemiser.services.shared.secrets_service import SecretsService

            secrets_service = SecretsService()
            alpaca_api_key, alpaca_secret_key = secrets_service.get_alpaca_credentials(
                paper_trading
            )

            self.logger.info(f"Generating monthly summary - Paper trading: {paper_trading}")

            # Generate monthly summary
            summary_service = MonthlySummaryService(
                api_key=alpaca_api_key, secret_key=alpaca_secret_key, paper=paper_trading
            )

            summary_data = summary_service.generate_monthly_summary(target_month_dt)

            # Build email content
            email_html = MonthlySummaryBuilder.build_monthly_summary_email(summary_data)

            # Send email notification
            month_name = summary_data.get("month", "Unknown")
            subject = f"The Alchemiser - Monthly Summary ({month_name})"

            # Add trading mode to subject if paper trading
            if paper_trading:
                subject += " [PAPER]"

            send_email_notification(
                subject=subject,
                html_content=email_html,
                text_content=f"Monthly trading summary for {month_name}. Please view HTML version for full details.",
            )

            self.logger.info(f"Monthly summary for {month_name} generated and sent successfully")
            return True

        except (DataProviderError, TradingClientError) as e:
            self.logger.error(f"Monthly summary generation failed: {e}")
            return False


def configure_application_logging() -> None:
    """Configure application logging.

    Honors any logging already configured by the CLI (root handlers present),
    and supports environment/config-driven log level via Settings.logging.level
    or LOGGING__LEVEL env var. Avoids overriding CLI --verbose behavior.
    """
    is_production = os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None

    # If logging already configured (e.g., by Typer CLI callback), don't override it
    root_logger = logging.getLogger()
    if root_logger.hasHandlers() and not is_production:
        return

    # Resolve desired level from env or settings; fallback to WARNING in dev, INFO in prod
    level_str = os.getenv("LOGGING__LEVEL")
    resolved_level = None
    if level_str:
        try:
            resolved_level = getattr(logging, level_str.upper())
        except Exception:
            resolved_level = None

    if resolved_level is None:
        try:
            # Load settings lazily to avoid circular imports
            from the_alchemiser.infrastructure.config import load_settings  # local import

            settings = load_settings()
            resolved_level = getattr(logging, settings.logging.level.upper(), None)
        except Exception:
            resolved_level = None

    if resolved_level is None:
        resolved_level = logging.INFO if is_production else logging.WARNING

    if is_production:
        from the_alchemiser.infrastructure.logging.logging_utils import configure_production_logging

        configure_production_logging(log_level=resolved_level, log_file=None)
    else:
        setup_logging(
            log_level=resolved_level,
            console_level=resolved_level,
            suppress_third_party=True,
            structured_format=False,
        )


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the command line argument parser."""
    parser = argparse.ArgumentParser(
        description="The Alchemiser - Multi-Strategy Quantitative Trading System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  alchemiser signal                    # Analyze signals
  alchemiser trade                     # Paper trading
  alchemiser trade --live              # Live trading
  alchemiser monthly-summary           # Generate monthly summary
  alchemiser monthly-summary --month 2024-01  # Summary for specific month
        """,
    )

    parser.add_argument(
        "mode",
        choices=["signal", "trade", "monthly-summary"],
        help="Operation mode: signal (analyze only), trade (execute), or monthly-summary (generate monthly report)",
    )

    parser.add_argument(
        "--live", action="store_true", help="Execute live trading (default: paper trading)"
    )

    parser.add_argument(
        "--ignore-market-hours", action="store_true", help="Override market hours check"
    )

    parser.add_argument(
        "--month",
        help="Target month for monthly summary (YYYY-MM format, defaults to previous month)",
    )

    return parser


def main(argv: list[str] | None = None) -> bool:
    """Main entry point for The Alchemiser Trading System.

    Args:
        argv: Command line arguments (uses sys.argv if None)

    Returns:
        True if operation completed successfully, False otherwise
    """
    from the_alchemiser.interface.cli.cli_formatter import render_footer, render_header

    # Setup
    configure_application_logging()
    parser = create_argument_parser()
    args = parser.parse_args(argv)

    # Initialize system
    system = TradingSystem()

    # Display header
    if args.mode == "monthly-summary":
        mode_label = "LIVE MODE ⚠️" if args.live else "Paper Mode"
        render_header("The Alchemiser Trading System", f"MONTHLY SUMMARY | {mode_label}")
    else:
        mode_label = "LIVE TRADING ⚠️" if args.mode == "trade" and args.live else "Paper Trading"
        render_header("The Alchemiser Trading System", f"{args.mode.upper()} | {mode_label}")

    # Execute operation
    try:
        if args.mode == "signal":
            success = system.analyze_signals()
        elif args.mode == "trade":
            success = system.execute_trading(
                live_trading=args.live, ignore_market_hours=args.ignore_market_hours
            )
        elif args.mode == "monthly-summary":
            success = system.generate_monthly_summary(
                target_month=args.month, live_trading=args.live
            )
        else:
            success = False

        # Display result
        if success:
            render_footer("Operation completed successfully!")
        else:
            render_footer("Operation failed!")

        return success

    except (ConfigurationError, ValueError, ImportError) as e:
        logger = get_logger(__name__)
        logger.error(f"System error: {e}")
        render_footer("System error occurred!")
        return False


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
