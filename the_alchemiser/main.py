#!/usr/bin/env python3
"""Main Entry Point for The Alchemiser Trading System.

A clean, focused entry point for the multi-strategy quantitative trading system.
Supports signal analysis and trading execution with dependency injection.
"""

import argparse
import os
import sys
from typing import Optional

from the_alchemiser.domain.strategies.strategy_manager import StrategyType
from the_alchemiser.infrastructure.config import Settings, load_settings
from the_alchemiser.logging import configure_logging, get_logger
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
            self.logger.info(
                "Dependency injection initialized",
                extra={"event": "di.initialized"},
            )
        else:
            self.logger.error(
                "DI not available - system requires dependency injection",
                extra={"event": "di.missing"},
            )
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
            self.logger.error(
                "Signal analysis failed",
                extra={"event": "signal.analysis.failed", "error": str(e)},
            )
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
            self.logger.error(
                "Trading execution failed",
                extra={"event": "trading.execution.failed", "error": str(e)},
            )
            return False


def configure_application_logging() -> None:
    """Configure structured logging for CLI usage."""
    env = os.getenv("ENV", "DEV")
    level = os.getenv("LOG_LEVEL")
    service = os.getenv("SERVICE_NAME", "alchemiser")
    region = os.getenv("REGION", "local")
    version = os.getenv("RELEASE_SHA", "dev")
    configure_logging(env=env, level=level, service=service, region=region, version=version)


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
        logger.error(
            "System error",
            extra={"event": "system.error", "error": str(e)},
        )
        render_footer("System error occurred!")
        return False


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
