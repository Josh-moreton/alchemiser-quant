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
from decimal import Decimal
from typing import Any

# CLI formatter imports (moved from function-level)
from the_alchemiser.orchestration.cli.cli_formatter import render_footer, render_header
from the_alchemiser.orchestration.event_driven_orchestrator import (
    EventDrivenOrchestrator,
)

# DTO imports
from the_alchemiser.execution_v2.models.execution_result import ExecutionResultDTO

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
from the_alchemiser.shared.schemas.common import AllocationComparisonDTO
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
        _di_container = self.container  # Keep global for backward compatibility during transition
        ServiceFactory.initialize(self.container)
        self.logger.info("Dependency injection initialized")

    def _initialize_event_orchestration(self) -> None:
        """Initialize event-driven orchestration system."""
        try:
            if self.container is None:
                self.logger.warning("Cannot initialize event orchestration: DI container not ready")
                return

            # Initialize event-driven orchestrator
            self.event_driven_orchestrator = EventDrivenOrchestrator(self.container)
            self.logger.info("Event-driven orchestration initialized")

        except Exception as e:
            # Don't let event orchestration failure break the traditional system
            self.logger.warning(f"Failed to initialize event orchestration: {e}")
            self.event_driven_orchestrator = None

    def _emit_startup_event(self, startup_mode: str) -> None:
        """Emit StartupEvent to trigger event-driven workflows.

        Args:
            startup_mode: The mode the system is starting in (signal, trade, etc.)

        """
        try:
            if self.container is None:
                self.logger.warning("Cannot emit StartupEvent: DI container not initialized")
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
                    "settings_loaded": True,
                },
            )

            # Emit the event
            event_bus.publish(event)
            self.logger.debug(f"Emitted StartupEvent {event.event_id} for mode: {startup_mode}")

        except Exception as e:
            # Don't let startup event emission failure break the system
            self.logger.warning(f"Failed to emit StartupEvent: {e}")

    # Signal analysis method removed - use execute_trading() instead which includes signal analysis

    def execute_trading(
        self,
        *,
        show_tracking: bool = False,
        export_tracking_json: str | None = None,
    ) -> bool:
        """Execute multi-strategy trading.

        Note: Trading mode (live/paper) is now determined by deployment stage.
        """
        try:
            from the_alchemiser.orchestration.trading_orchestrator import (
                TradingOrchestrator,
            )

            if self.container is None:
                raise RuntimeError("DI container not initialized")
            # Create trading orchestrator directly
            orchestrator = TradingOrchestrator(
                settings=self.settings,
                container=self.container,
            )

            # Display header
            render_header("Analyzing market conditions...", "Multi-Strategy Trading")

            # PHASE 1: Signals-only analysis (no trading yet)
            signals_result = orchestrator.execute_strategy_signals()
            if signals_result is None:
                render_footer("Signal analysis failed - check logs for details")
                return False

            # Show pure strategy outputs first, then rebalance plan
            self._display_signals_and_rebalance(signals_result)

            # PHASE 2: Execute trading (may place orders)
            trading_result = orchestrator.execute_strategy_signals_with_trading()
            if trading_result is None:
                render_footer("Trading execution failed - check logs for details")
                return False

            # Show execution results only (avoid re-printing signals/plan)
            orders_executed = trading_result.get("orders_executed", [])
            if orders_executed:
                self._display_execution_results(
                    orders_executed, trading_result.get("execution_result")
                )

            # 5) Display tracking if requested
            if show_tracking:
                self._display_post_execution_tracking(not orchestrator.live_trading)

            # 6) Export tracking summary if requested
            if export_tracking_json:
                self._export_tracking_summary(export_tracking_json, not orchestrator.live_trading)

            # 7) Send notification
            try:
                mode_str = "LIVE" if orchestrator.live_trading else "PAPER"
                orchestrator.send_trading_notification(trading_result, mode_str)
            except Exception as exc:
                self.logger.warning(f"Failed to send trading notification: {exc}")

            success = bool(trading_result.get("success", False))
            if success:
                render_footer("Trading execution completed successfully!")
            else:
                render_footer("Trading execution failed - check logs for details")

            return success
        except (TradingClientError, StrategyExecutionError) as e:
            self.error_handler.handle_error(
                error=e,
                context="multi-strategy trading execution",
                component="TradingSystem.execute_trading",
                additional_data={
                    "show_tracking": show_tracking,
                    "export_tracking_json": export_tracking_json,
                },
            )
            render_footer("System error occurred!")
            return False

    def _display_signals_and_rebalance(self, result: dict[str, Any]) -> None:
        """Display strategy signals followed by rebalance plan."""
        from the_alchemiser.orchestration.cli.cli_formatter import (
            render_comprehensive_trading_results,
            render_strategy_signals,
        )

        try:
            strategy_signals = result.get("strategy_signals", {})
            if strategy_signals:
                render_strategy_signals(strategy_signals)

            # Show only account + allocation sections (no open orders, no strategy signals again)
            render_comprehensive_trading_results(
                {},
                result.get("consolidated_portfolio", {}),
                result.get("account_info"),
                result.get("current_positions"),
                result.get("allocation_comparison"),
                [],
            )
        except Exception as e:
            self.logger.warning(f"Failed to display signals/rebalance: {e}")

    def _display_comprehensive_results(
        self,
        strategy_signals: dict[str, Any],
        consolidated_portfolio: dict[str, float],
        account_info: dict[str, Any] | None = None,
        current_positions: dict[str, Any] | None = None,
        allocation_comparison: AllocationComparisonDTO | None = None,
        open_orders: list[dict[str, Any]] | None = None,
    ) -> None:
        """Display comprehensive trading results."""
        from the_alchemiser.orchestration.cli.cli_formatter import (
            render_comprehensive_trading_results,
        )

        try:
            render_comprehensive_trading_results(
                strategy_signals,
                consolidated_portfolio,
                account_info,
                current_positions,
                allocation_comparison,
                open_orders,
            )
        except Exception as e:
            self.logger.warning(f"Failed to display comprehensive results: {e}")

    def _display_execution_results(
        self,
        orders_executed: list[dict[str, Any]],
        execution_result: ExecutionResultDTO | None = None,
    ) -> None:
        """Display execution results including order details and summary."""
        try:
            from rich.console import Console
            from rich.panel import Panel
            from rich.table import Table

            from the_alchemiser.orchestration.cli.cli_formatter import (
                render_orders_executed,
            )

            console = Console()

            # Display orders executed using existing formatter
            render_orders_executed(orders_executed)

            # Display detailed order status information
            if orders_executed:
                status_table = Table(title="Order Execution Details", show_lines=True)
                status_table.add_column("Symbol", style="cyan", justify="center")
                status_table.add_column("Action", style="bold", justify="center")
                status_table.add_column("Status", style="bold", justify="center")
                status_table.add_column("Order ID", style="dim", justify="center")
                status_table.add_column("Error Details", style="red", justify="left")

                for order in orders_executed:
                    status = order.get("status", "UNKNOWN")
                    order_id = order.get("order_id") or "N/A"
                    error = order.get("error") or ""

                    # Style status
                    if status == "FILLED":
                        status_display = "[bold green]✅ FILLED[/bold green]"
                    elif status == "FAILED":
                        status_display = "[bold red]❌ FAILED[/bold red]"
                    else:
                        status_display = f"[yellow]{status}[/yellow]"

                    # Style action
                    action = order.get("side", "").upper()
                    if action == "BUY":
                        action_display = "[green]BUY[/green]"
                    elif action == "SELL":
                        action_display = "[red]SELL[/red]"
                    else:
                        action_display = action

                    status_table.add_row(
                        order.get("symbol", "N/A"),
                        action_display,
                        status_display,
                        order_id,
                        error[:50] + "..." if len(error) > 50 else error,
                    )

                console.print(status_table)

            # Display execution summary if available
            if execution_result:
                try:
                    success_rate = getattr(execution_result, "success_rate", 1.0)
                    total_value = getattr(execution_result, "total_trade_value", Decimal(0))

                    summary_content = [
                        f"[bold green]Execution Success Rate:[/bold green] {success_rate:.1%}",
                        f"[bold blue]Orders Placed:[/bold blue] {execution_result.orders_placed}",
                        f"[bold green]Orders Succeeded:[/bold green] {execution_result.orders_succeeded}",
                        f"[bold yellow]Total Trade Value:[/bold yellow] ${float(total_value):,.2f}",
                    ]

                    if (
                        hasattr(execution_result, "failure_count")
                        and execution_result.failure_count > 0
                    ):
                        summary_content.append(
                            f"[bold red]Orders Failed:[/bold red] {execution_result.failure_count}"
                        )

                    console.print(
                        Panel(
                            "\n".join(summary_content),
                            title="Execution Summary",
                            style="bold white",
                        )
                    )
                except Exception as e:
                    self.logger.warning(f"Failed to display execution summary: {e}")

        except Exception as e:
            self.logger.warning(f"Failed to display execution results: {e}")

    def _display_post_execution_tracking(self, paper_trading: bool) -> None:  # noqa: FBT001
        """Display strategy performance tracking after execution."""
        try:
            from rich.console import Console

            from the_alchemiser.orchestration.cli.strategy_tracking_utils import (
                display_strategy_tracking,
            )

            console = Console()
            console.print("\n")
            display_strategy_tracking(paper_trading=paper_trading)

        except Exception as e:
            self.logger.warning(f"Failed to display post-execution tracking: {e}")
            try:
                from rich.console import Console
                from rich.panel import Panel

                Console().print(
                    Panel(
                        f"[dim yellow]Strategy tracking display unavailable: {e}[/dim yellow]",
                        title="Strategy Performance Tracking",
                        border_style="yellow",
                    )
                )
            except ImportError:
                self.logger.warning("Strategy tracking display unavailable (rich not available)")

    def _export_tracking_summary(self, export_path: str, paper_trading: bool) -> None:  # noqa: FBT001
        """Export tracking summary to JSON file."""
        try:
            import json
            from pathlib import Path

            from the_alchemiser.orchestration.cli.strategy_tracking_utils import (
                _get_strategy_order_tracker,
            )

            # Create tracker using same mode as execution
            tracker = _get_strategy_order_tracker(paper_trading=paper_trading)

            # Collect strategy data
            strategy_data = {}
            for strategy_name in ["nuclear", "tecl", "klm"]:
                try:
                    strategy_summary = tracker.get_strategy_summary(strategy_name)
                    if strategy_summary:
                        strategy_data[strategy_name] = {
                            "total_profit_loss": float(strategy_summary.total_profit_loss),
                            "total_orders": strategy_summary.total_orders,
                            "success_rate": strategy_summary.success_rate,
                            "avg_profit_per_trade": float(strategy_summary.avg_profit_per_trade),
                        }
                except Exception as e:
                    self.logger.debug(f"Could not get summary for {strategy_name}: {e}")

            # Export to JSON
            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)

            with export_file.open("w") as f:
                json.dump(strategy_data, f, indent=2)

            self.logger.info(f"Tracking summary exported to: {export_path}")

        except Exception as e:
            self.logger.warning(f"Failed to export tracking summary: {e}")


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
        # system._emit_startup_event(args.mode)

        # Display header with simple trading mode detection
        if args.mode == "trade":
            from the_alchemiser.shared.config.secrets_adapter import get_alpaca_keys

            _, _, endpoint = get_alpaca_keys()
            is_live = endpoint and "paper" not in endpoint.lower()
            mode_label = "LIVE TRADING ⚠️" if is_live else "Paper Trading"
            render_header("The Alchemiser Trading System", f"{args.mode.upper()} | {mode_label}")

        # Execute trading with integrated signal analysis
        if args.mode == "trade":
            success = system.execute_trading(
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
            },
        )
        render_footer("System error occurred!")
        return False


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
