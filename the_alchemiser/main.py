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

from the_alchemiser.orchestration.event_driven_orchestrator import (
    EventDrivenOrchestrator,
)

# CLI formatter imports (moved from function-level)
from the_alchemiser.orchestration.cli.cli_formatter import render_footer, render_header

# Signal analyzer import removed - signal functionality integrated into trading workflow
from the_alchemiser.shared.config.config import Settings, load_settings

# DI imports (required for v2 architecture)
from the_alchemiser.shared.config.container import (
    ApplicationContainer,
)
from the_alchemiser.shared.errors.error_handler import TradingSystemErrorHandler
from the_alchemiser.shared.events import EventBus, StartupEvent
from the_alchemiser.shared.logging.logging_utils import (
    configure_production_logging,
    generate_request_id,
    get_logger,
    set_request_id,
    setup_logging,
)
from the_alchemiser.shared.types.exceptions import (
    ConfigurationError,
    StrategyExecutionError,
    TradingClientError,
)
from the_alchemiser.shared.utils.service_factory import ServiceFactory

# Global DI container
# Use Optional for proper type inference by static type checkers
_di_container: ApplicationContainer | None = None


class TradingSystem:
    """Main trading system orchestrator."""

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize trading system with optional settings."""
        self.settings = settings or load_settings()
        self.logger = get_logger(__name__)
        self.error_handler = TradingSystemErrorHandler()
        self.container: ApplicationContainer | None = None
        self.event_driven_orchestrator: EventDrivenOrchestrator | None = None
        self._initialize_di()
        self._initialize_event_orchestration()

    def _initialize_di(self) -> None:
        """Initialize dependency injection system."""
        global _di_container

        self.container = ApplicationContainer()
        _di_container = (
            self.container
        )  # Keep global for backward compatibility during transition
        ServiceFactory.initialize(self.container)
        self.logger.info("Dependency injection initialized")

    def _initialize_event_orchestration(self) -> None:
        """Initialize event-driven orchestration system."""
        try:
            if self.container is None:
                self.logger.warning(
                    "Cannot initialize event orchestration: DI container not ready"
                )
                return

            # Initialize event-driven orchestrator
            self.event_driven_orchestrator = EventDrivenOrchestrator(self.container)
            self.logger.info("Event-driven orchestration initialized")

        except Exception as e:
            # Don't let event orchestration failure break the traditional system
            self.logger.warning(f"Failed to initialize event orchestration: {e}")
            self.event_driven_orchestrator = None

    def _emit_startup_event(
        self, startup_mode: str, *, ignore_market_hours: bool = False
    ) -> None:
        """Emit StartupEvent to trigger event-driven workflows.

        Args:
            startup_mode: The mode the system is starting in (signal, trade, etc.)
            ignore_market_hours: Whether market hours are being ignored

        """
        try:
            if self.container is None:
                self.logger.warning(
                    "Cannot emit StartupEvent: DI container not initialized"
                )
                return

            # Get event bus from container
            event_bus: EventBus = self.container.services.event_bus()

            # Create StartupEvent
            import uuid
            from datetime import UTC, datetime

            event = StartupEvent(
                correlation_id=str(uuid.uuid4()),
                causation_id=f"system-startup-{datetime.now(UTC).isoformat()}",
                event_id=f"startup-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="main",
                source_component="TradingSystem",
                startup_mode=startup_mode,
                configuration={
                    "ignore_market_hours": ignore_market_hours,
                    "settings_loaded": True,
                },
            )

            # Emit the event
            event_bus.publish(event)
            self.logger.debug(
                f"Emitted StartupEvent {event.event_id} for mode: {startup_mode}"
            )

        except Exception as e:
            # Don't let startup event emission failure break the system
            self.logger.warning(f"Failed to emit StartupEvent: {e}")

    # Signal analysis method removed - use execute_trading() instead which includes signal analysis

    def execute_trading(
        self,
        *,
        ignore_market_hours: bool = False,
        show_tracking: bool = False,
        export_tracking_json: str | None = None,
    ) -> bool:
        """Execute multi-strategy trading.

        Note: Trading mode (live/paper) is now determined by deployment stage.
        """
        try:
            from the_alchemiser.orchestration.cli.trading_executor import TradingExecutor

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


def _resolve_log_level(*, is_production: bool) -> int:
    """Resolve the desired log level from environment or settings."""
    # Environment override first
    level_str = os.getenv("LOGGING__LEVEL")
    if level_str:
        try:
            return int(getattr(logging, level_str.upper()))
        except (AttributeError, TypeError):
            # Invalid log level string, fall back to default
            pass

    # Then settings
    try:
        settings = load_settings()
        configured = getattr(logging, settings.logging.level.upper(), None)
        if isinstance(configured, int):
            return configured
    except (AttributeError, TypeError, ImportError):
        # Settings loading failed or invalid log level, fall back to default
        pass

    # Fallback
    return logging.INFO if is_production else logging.WARNING


def configure_application_logging() -> None:
    """Configure application logging with reduced complexity."""
    # Check for Lambda environment via runtime-specific environment variables
    is_production = any(
        [
            os.getenv("AWS_EXECUTION_ENV"),
            os.getenv("AWS_LAMBDA_RUNTIME_API"),
            os.getenv("LAMBDA_RUNTIME_DIR"),
        ]
    )
    root_logger = logging.getLogger()
    if root_logger.hasHandlers() and not is_production:
        return

    resolved_level = _resolve_log_level(is_production=is_production)

    if is_production:
        log_file = None
        try:
            settings = load_settings()
            if settings.logging.enable_s3_logging and settings.logging.s3_log_uri:
                log_file = settings.logging.s3_log_uri
        except (AttributeError, ImportError):
            # Settings loading failed, use default log file setting
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
  alchemiser trade                     # Execute trading (mode determined by stage)
        """,
    )

    parser.add_argument(
        "mode",
        choices=["trade"],
        help="Operation mode: trade (execute trading with integrated signal analysis)",
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
    """Serve as main entry point for The Alchemiser Trading System.

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

        # PHASE 6: Emit StartupEvent to trigger event-driven workflows
        # NOTE: Disabled for now since TradingOrchestrator emits its own StartupEvent
        # system._emit_startup_event(
        #     args.mode, ignore_market_hours=getattr(args, "ignore_market_hours", False)
        # )

        # Display header with simple trading mode detection
        if args.mode == "trade":
            from the_alchemiser.shared.config.secrets_adapter import get_alpaca_keys

            _, _, endpoint = get_alpaca_keys()
            is_live = endpoint and "paper" not in endpoint.lower()
            mode_label = "LIVE TRADING ⚠️" if is_live else "Paper Trading"
            render_header(
                "The Alchemiser Trading System", f"{args.mode.upper()} | {mode_label}"
            )

        # Execute trading with integrated signal analysis
        if args.mode == "trade":
            success = system.execute_trading(
                ignore_market_hours=args.ignore_market_hours,
                show_tracking=getattr(args, "show_tracking", False),
                export_tracking_json=getattr(args, "export_tracking_json", None),
            )
        else:
            # This should never happen since we only accept "trade" mode now
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
