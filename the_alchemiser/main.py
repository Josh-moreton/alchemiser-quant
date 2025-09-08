#!/usr/bin/env python3
"""Business Unit: utilities; Status: current.

Main Entry Point for The Alchemiser Trading System.

A clean, focused entry point for the multi-strategy quantitative trading system.
Supports signal analysis and trading execution with dependency injection.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys

from the_alchemiser.shared.cli.signal_analyzer import SignalAnalyzer
from the_alchemiser.shared.config.config import Settings, load_settings
from the_alchemiser.shared.errors.error_handler import TradingSystemErrorHandler
from the_alchemiser.shared.logging.logging_utils import (
    configure_production_logging,
    generate_request_id,
    get_logger,
    set_request_id,
    setup_logging,
)
from the_alchemiser.shared.types.exceptions import (
    ConfigurationError,
    DataProviderError,
    StrategyExecutionError,
    TradingClientError,
)

# DI imports (optional)
try:
    from the_alchemiser.shared.config.container import (
        ApplicationContainer,
    )
    from the_alchemiser.shared.utils.service_factory import ServiceFactory

    DI_AVAILABLE = True
except ImportError:
    DI_AVAILABLE = False

# CLI formatter imports (moved from function-level)
from the_alchemiser.shared.cli.cli_formatter import render_footer, render_header

# Global DI container
# Use Optional for proper type inference by static type checkers
_di_container: ApplicationContainer | None = None


class TradingSystem:
    """Main trading system orchestrator."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or load_settings()
        self.logger = get_logger(__name__)
        self.error_handler = TradingSystemErrorHandler()
        self.container: ApplicationContainer | None = None
        self._initialize_di()

    def _initialize_di(self) -> None:
        """Initialize dependency injection system."""
        global _di_container

        if DI_AVAILABLE:
            self.container = ApplicationContainer()
            _di_container = (
                self.container
            )  # Keep global for backward compatibility during transition
            ServiceFactory.initialize(self.container)
            self.logger.info("Dependency injection initialized")
        else:
            self.logger.error("DI not available - system requires dependency injection")
            raise ConfigurationError("Dependency injection system is required but not available")

    def analyze_signals(self, show_tracking: bool = False) -> bool:
        """Generate and display strategy signals without trading.

        Args:
            show_tracking: When True include performance tracking table (opt-in to preserve
                legacy minimal output by default).

        """
        try:
            if self.container is None:
                raise RuntimeError("DI container not initialized")
            analyzer = SignalAnalyzer(self.settings, self.container)
            return analyzer.run(show_tracking=show_tracking)
        except (DataProviderError, StrategyExecutionError) as e:
            self.error_handler.handle_error(
                error=e,
                context="signal analysis operation",
                component="TradingSystem.analyze_signals",
                additional_data={"settings_loaded": True},
            )
            return False

    def execute_trading(
        self,
        ignore_market_hours: bool = False,
        show_tracking: bool = False,
        export_tracking_json: str | None = None,
    ) -> bool:
        """Execute multi-strategy trading.
        
        Note: Trading mode (live/paper) is now determined by deployment stage.
        """
        try:
            from the_alchemiser.shared.cli.trading_executor import TradingExecutor

            if self.container is None:
                raise RuntimeError("DI container not initialized")
            executor = TradingExecutor(
                settings=self.settings,
                container=self.container,
                ignore_market_hours=ignore_market_hours,
                show_tracking=show_tracking,
                export_tracking_json=export_tracking_json,
            )
            return executor.run()
        except (TradingClientError, StrategyExecutionError) as e:
            self.error_handler.handle_error(
                error=e,
                context="multi-strategy trading execution",
                component="TradingSystem.execute_trading",
                additional_data={
                    "ignore_market_hours": ignore_market_hours,
                    "show_tracking": show_tracking,
                    "export_tracking_json": export_tracking_json,
                },
            )
            return False


def _resolve_log_level(is_production: bool) -> int:
    """Resolve the desired log level from environment or settings."""
    # Environment override first
    level_str = os.getenv("LOGGING__LEVEL")
    if level_str:
        try:
            return int(getattr(logging, level_str.upper()))
        except Exception:
            pass

    # Then settings
    try:
        settings = load_settings()
        configured = getattr(logging, settings.logging.level.upper(), None)
        if isinstance(configured, int):
            return configured
    except Exception:
        pass

    # Fallback
    return logging.INFO if is_production else logging.WARNING


def configure_application_logging() -> None:
    """Configure application logging with reduced complexity."""
    # Check for Lambda environment via runtime-specific environment variables
    is_production = any([
        os.getenv("AWS_EXECUTION_ENV"),
        os.getenv("AWS_LAMBDA_RUNTIME_API"),
        os.getenv("LAMBDA_RUNTIME_DIR")
    ])
    root_logger = logging.getLogger()
    if root_logger.hasHandlers() and not is_production:
        return

    resolved_level = _resolve_log_level(is_production)

    if is_production:
        log_file = None
        try:
            settings = load_settings()
            if settings.logging.enable_s3_logging and settings.logging.s3_log_uri:
                log_file = settings.logging.s3_log_uri
        except Exception:
            pass
        configure_production_logging(log_level=resolved_level, log_file=log_file)
        return

    setup_logging(
        log_level=resolved_level,
        console_level=resolved_level,
        suppress_third_party=True,
        structured_format=False,
        respect_existing_handlers=True,
    )


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the command line argument parser."""
    parser = argparse.ArgumentParser(
        description="The Alchemiser - Multi-Strategy Quantitative Trading System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  alchemiser signal                    # Analyze signals
  alchemiser trade                     # Execute trading (mode determined by stage)
        """,
    )

    parser.add_argument(
        "mode",
        choices=["signal", "trade"],
        help="Operation mode: signal (analyze only) or trade (execute)",
    )

    # Remove --live flag - trading mode now determined by deployment stage
    # parser.add_argument(
    #     "--live",
    #     action="store_true", 
    #     help="Execute live trading (default: paper trading)",
    # )

    parser.add_argument(
        "--ignore-market-hours", action="store_true", help="Override market hours check"
    )

    parser.add_argument(
        "--tracking",
        action="store_true",
        help="Include strategy performance tracking table (signal mode - deprecated)",
    )

    parser.add_argument(
        "--show-tracking",
        action="store_true",
        help="Display strategy performance tracking after trade execution",
    )

    parser.add_argument(
        "--export-tracking-json",
        type=str,
        help="Export tracking summary to JSON file after trade execution",
    )

    return parser


def main(argv: list[str] | None = None) -> bool:
    """Main entry point for The Alchemiser Trading System.

    Args:
        argv: Command line arguments (uses sys.argv if None)

    Returns:
        True if operation completed successfully, False otherwise

    """
    # Setup
    configure_application_logging()

    # Generate and set request ID for correlation
    request_id = generate_request_id()
    set_request_id(request_id)

    parser = create_argument_parser()
    args = parser.parse_args(argv)

    # Execute operation with proper error boundary for all phases
    try:
        # Initialize system
        system = TradingSystem()

        # Display header with simple trading mode detection
        if args.mode == "trade":
            from the_alchemiser.shared.config.secrets_adapter import get_alpaca_keys
            _, _, endpoint = get_alpaca_keys()
            is_live = endpoint and "paper" not in endpoint.lower()
            mode_label = "LIVE TRADING ⚠️" if is_live else "Paper Trading"
            render_header("The Alchemiser Trading System", f"{args.mode.upper()} | {mode_label}")
        else:
            render_header("The Alchemiser Trading System", f"{args.mode.upper()}")

        if args.mode == "signal":
            success = system.analyze_signals(show_tracking=getattr(args, "tracking", False))
        elif args.mode == "trade":
            success = system.execute_trading(
                ignore_market_hours=args.ignore_market_hours,
                show_tracking=getattr(args, "show_tracking", False),
                export_tracking_json=getattr(args, "export_tracking_json", None),
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
        # Use TradingSystemErrorHandler for boundary logging - exactly once
        error_handler = TradingSystemErrorHandler()
        error_handler.handle_error(
            error=e,
            context="application initialization and execution",
            component="main",
            additional_data={
                "mode": args.mode,
                "ignore_market_hours": getattr(args, "ignore_market_hours", False),
            },
        )
        render_footer("System error occurred!")
        return False


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
