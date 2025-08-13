#!/usr/bin/env python3
"""Main Entry Point for The Alchemiser Trading System.

A clean, focused entry point for the multi-strategy quantitative trading system.
Supports signal analysis and trading execution with dependency injection.
"""

import argparse
import logging
import os
import sys

from the_alchemiser.domain.strategies.strategy_manager import StrategyType
from the_alchemiser.infrastructure.config import Settings, load_settings
from the_alchemiser.infrastructure.logging.logging_utils import get_logger, setup_logging
from the_alchemiser.services.exceptions import (
    ConfigurationError,
    DataProviderError,
    StrategyExecutionError,
    TradingClientError,
)

# DI imports (optional)
try:
    from the_alchemiser.container.application_container import ApplicationContainer
    from the_alchemiser.services.service_factory import ServiceFactory

    DI_AVAILABLE = True
except ImportError:
    DI_AVAILABLE = False

# Global DI container
_di_container = None


class TradingSystem:
    """Main trading system orchestrator."""

    def __init__(self, settings: Settings | None = None, use_legacy: bool = False):
        self.settings = settings or load_settings()
        self.use_legacy = use_legacy
        self.logger = get_logger(__name__)
        self._initialize_di()

    def _initialize_di(self) -> None:
        """Initialize dependency injection if available and not using legacy mode."""
        global _di_container

        if not self.use_legacy and DI_AVAILABLE:
            _di_container = ApplicationContainer()
            ServiceFactory.initialize(_di_container)
            self.logger.info("Dependency injection initialized")
        else:
            if not self.use_legacy and not DI_AVAILABLE:
                self.logger.warning("DI not available - falling back to legacy mode")
            else:
                self.logger.info("Using legacy initialization")

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
            analyzer = SignalAnalyzer(self.settings, use_legacy=self.use_legacy)
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
                use_legacy=self.use_legacy,
                live_trading=live_trading,
                ignore_market_hours=ignore_market_hours,
            )
            return executor.run()
        except (TradingClientError, StrategyExecutionError) as e:
            self.logger.error(f"Trading execution failed: {e}")
            return False


def configure_application_logging() -> None:
    """Configure application logging."""
    is_production = os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None

    if is_production:
        from the_alchemiser.infrastructure.logging.logging_utils import configure_production_logging

        configure_production_logging(log_level=logging.INFO, log_file=None)
    else:
        setup_logging(
            log_level=logging.WARNING,
            console_level=logging.WARNING,
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
  alchemiser signal                    # Analyze signals (DI mode)
  alchemiser trade                     # Paper trading (DI mode)
  alchemiser trade --live              # Live trading (DI mode)
  alchemiser signal --legacy           # Legacy mode
        """,
    )

    parser.add_argument(
        "mode",
        choices=["signal", "trade"],
        help="Operation mode: signal (analyze only) or trade (execute)",
    )

    parser.add_argument(
        "--live", action="store_true", help="Execute live trading (default: paper trading)"
    )

    parser.add_argument(
        "--ignore-market-hours", action="store_true", help="Override market hours check"
    )

    parser.add_argument(
        "--legacy", action="store_true", help="Use legacy mode (disable dependency injection)"
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
    system = TradingSystem(use_legacy=args.legacy)

    # Display header
    mode_label = "LIVE TRADING ⚠️" if args.mode == "trade" and args.live else "Paper Trading"
    legacy_label = " (Legacy)" if args.legacy else ""
    render_header(
        "The Alchemiser Trading System", f"{args.mode.upper()} | {mode_label}{legacy_label}"
    )

    # Execute operation
    try:
        if args.mode == "signal":
            success = system.analyze_signals()
        elif args.mode == "trade":
            success = system.execute_trading(
                live_trading=args.live, ignore_market_hours=args.ignore_market_hours
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
