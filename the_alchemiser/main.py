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
from the_alchemiser.infrastructure.logging.logging_utils import (
    generate_request_id,
    get_logger,
    set_request_id,
    setup_logging,
)
from the_alchemiser.services.errors.exceptions import (
    ConfigurationError,
    DataProviderError,
    StrategyExecutionError,
    TradingClientError,
)
from the_alchemiser.services.errors.handler import TradingSystemErrorHandler

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
        self.error_handler = TradingSystemErrorHandler()
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
            self.error_handler.handle_error(
                error=e,
                context="signal analysis operation",
                component="TradingSystem.analyze_signals",
                additional_data={"settings_loaded": True}
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
            self.error_handler.handle_error(
                error=e,
                context="multi-strategy trading execution",
                component="TradingSystem.execute_trading",
                additional_data={
                    "live_trading": live_trading,
                    "ignore_market_hours": ignore_market_hours
                }
            )
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
            respect_existing_handlers=True,  # Respect CLI-configured handlers in dev
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

    # Generate and set request ID for correlation
    request_id = generate_request_id()
    set_request_id(request_id)

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
        # Create error handler instance for boundary logging
        # Use the TradingSystem instance's error handler for boundary logging
        error_handler = getattr(system, "error_handler", TradingSystemErrorHandler())
        error_handler.handle_error(
            error=e,
            context="application initialization and execution",
            component="main",
            additional_data={
                "mode": args.mode,
                "live_trading": getattr(args, 'live', False),
                "ignore_market_hours": getattr(args, 'ignore_market_hours', False)
            }
        )
        render_footer("System error occurred!")
        return False


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
