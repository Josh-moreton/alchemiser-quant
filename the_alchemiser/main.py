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
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from the_alchemiser.orchestration.event_driven_orchestrator import (
        EventDrivenOrchestrator,
    )
    from the_alchemiser.orchestration.trading_orchestrator import TradingOrchestrator

# CLI formatter imports (moved from function-level)
from the_alchemiser.orchestration.cli.cli_utilities import (
    render_footer,
)

# Import moved to where it's used to avoid early dependency loading
from the_alchemiser.shared.config.config import Settings, load_settings
from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.dto.trade_run_result_dto import (
    ExecutionSummaryDTO,
    OrderResultSummaryDTO,
    TradeRunResultDTO,
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
from the_alchemiser.shared.math.num import floats_equal
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
            from the_alchemiser.orchestration.event_driven_orchestrator import (
                EventDrivenOrchestrator,
            )

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
    ) -> TradeRunResultDTO:
        """Execute multi-strategy trading.

        Note: Trading mode (live/paper) is now determined by deployment stage.

        Returns:
            TradeRunResultDTO with complete execution results and metadata

        """
        import uuid
        from datetime import UTC, datetime

        # Start timing and correlation tracking
        started_at = datetime.now(UTC)
        correlation_id = str(uuid.uuid4())
        warnings: list[str] = []

        try:
            from the_alchemiser.orchestration.trading_orchestrator import (
                TradingOrchestrator,
            )

            if self.container is None:
                return self._create_failure_result(
                    "DI container not initialized", started_at, correlation_id, warnings
                )

            # Create trading orchestrator directly
            orchestrator = TradingOrchestrator(
                settings=self.settings,
                container=self.container,
            )

            # Header suppressed to reduce duplicate banners in CLI output

            # PHASE 1: Signals-only analysis (no trading yet)
            print("📊 Generating strategy signals...")
            signals_result = orchestrator.execute_strategy_signals()
            if signals_result is None:
                return self._create_failure_result(
                    "Signal analysis failed - check logs for details",
                    started_at,
                    correlation_id,
                    warnings,
                )

            # Show brief signals summary
            self._display_signals_summary(signals_result)

            # PHASE 2: Execute trading (may place orders)
            print("⚖️  Generating portfolio rebalance plan...")

            # Temporarily suppress verbose logs for cleaner CLI output
            self._configure_quiet_logging()

            try:
                # Execute trading with minimal output - no Rich progress spinner
                trading_result = orchestrator.execute_strategy_signals_with_trading()
            except Exception:
                # Fallback if anything fails
                trading_result = orchestrator.execute_strategy_signals_with_trading()
            finally:
                self._restore_logging()

            if trading_result is None:
                return self._create_failure_result(
                    "Trading execution failed - check logs for details",
                    started_at,
                    correlation_id,
                    warnings,
                )

            # Show rebalance plan details
            self._display_rebalance_plan(trading_result)

            # Show stale order cancellation info
            self._display_stale_order_info(trading_result)

            print("🚀 Executing rebalance plan...")

            # 5) Display tracking if requested
            if show_tracking:
                self._display_post_execution_tracking(paper_trading=not orchestrator.live_trading)

            # 6) Export tracking summary if requested
            if export_tracking_json:
                self._export_tracking_summary(
                    export_path=export_tracking_json,
                    paper_trading=not orchestrator.live_trading,
                )

            # 7) Send notification
            try:
                mode_str = "LIVE" if orchestrator.live_trading else "PAPER"
                orchestrator.send_trading_notification(trading_result, mode_str)
            except Exception as exc:
                warnings.append(f"Failed to send trading notification: {exc}")

            # Create successful result DTO
            completed_at = datetime.now(UTC)
            success = bool(trading_result.get("success", False))

            return self._create_success_result(
                trading_result=trading_result,
                orchestrator=orchestrator,
                started_at=started_at,
                completed_at=completed_at,
                correlation_id=correlation_id,
                warnings=warnings,
                success=success,
            )

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
            return self._create_failure_result(
                f"System error: {e}", started_at, correlation_id, warnings
            )

    def _display_signals_summary(self, signals_result: dict[str, Any]) -> None:
        """Display a brief summary of generated signals and target allocations."""
        try:
            # Extract and display individual strategy signals with their recommended symbols
            strategy_signals = signals_result.get("strategy_signals", {})
            if isinstance(strategy_signals, dict):
                signal_details = []
                for raw_name, data in strategy_signals.items():
                    name = str(raw_name)
                    if name.startswith("StrategyType."):
                        name = name.split(".", 1)[1]

                    if isinstance(data, dict):
                        action = str(data.get("action", "")).upper()
                        if action in {"BUY", "SELL"}:
                            if data.get("is_multi_symbol") and isinstance(
                                data.get("symbols"), list
                            ):
                                symbols = data.get("symbols", [])
                                if symbols:
                                    symbol_str = ", ".join(symbols)
                                    signal_details.append(f"{name}: {action} {symbol_str}")
                            elif data.get("symbol"):
                                signal_details.append(f"{name}: {action} {data.get('symbol')}")

                if signal_details:
                    print("📋 Strategy signals generated:")
                    for detail in signal_details:
                        print(f"   → {detail}")
                else:
                    print("📋 No actionable signals generated")

            # Show consolidated target allocations
            if "consolidated_portfolio" in signals_result:
                portfolio = signals_result["consolidated_portfolio"]
                if isinstance(portfolio, dict):
                    non_zero = [
                        (s, float(w))
                        for s, w in portfolio.items()
                        if not floats_equal(float(w), 0.0)
                    ]
                    if non_zero:
                        # Sort by allocation percentage descending
                        non_zero.sort(key=lambda x: x[1], reverse=True)
                        allocations = ", ".join(
                            f"{sym} {weight * 100:.1f}%" for sym, weight in non_zero
                        )
                        print(f"🎯 Final recommended allocations: {allocations}")
                    else:
                        print("🎯 Final recommended allocations: 100% cash")
        except Exception as e:
            # Non-fatal: summary display is best-effort
            self.logger.debug(f"Failed to display signals summary: {e}")

    def _display_rebalance_plan(self, trading_result: dict[str, Any]) -> None:
        """Display a concise BUY/SELL summary of the rebalance plan."""
        try:
            rebalance_plan = trading_result.get("rebalance_plan")

            if rebalance_plan is None:
                print("📋 No trades required (portfolio balanced)")
                return

            # If rebalance_plan is a DTO, get the items
            if hasattr(rebalance_plan, "items"):
                plan_items = rebalance_plan.items
            elif isinstance(rebalance_plan, dict) and "items" in rebalance_plan:
                plan_items = rebalance_plan["items"]
            else:
                # Fallback: no detailed plan available
                print("📋 Rebalance plan generated:")
                print("   → BUY: (details unavailable)")
                print("   → SELL: (details unavailable)")
                return

            if not plan_items:
                print("📋 No trades required (portfolio balanced)")
                return

            # Group items by action
            buy_orders = []
            sell_orders = []

            for item in plan_items:
                # Handle both DTO and dict representations
                if hasattr(item, "action"):
                    action = item.action
                    symbol = item.symbol
                    trade_amount = item.trade_amount
                elif isinstance(item, dict):
                    action = item.get("action", "").upper()
                    symbol = item.get("symbol", "")
                    trade_amount = item.get("trade_amount", 0)
                else:
                    continue

                if action == "BUY" and float(trade_amount) > 0:
                    buy_orders.append(f"{symbol} ${abs(float(trade_amount)):,.0f}")
                elif action == "SELL" and float(trade_amount) < 0:
                    sell_orders.append(f"{symbol} ${abs(float(trade_amount)):,.0f}")

            # Display the plan in a concise summary similar to signals
            if buy_orders or sell_orders:
                print("📋 Rebalance plan generated:")
                if sell_orders:
                    print(f"   → SELL: {', '.join(sell_orders)}")
                if buy_orders:
                    print(f"   → BUY: {', '.join(buy_orders)}")
            else:
                print("📋 No trades required (portfolio balanced)")

        except Exception as e:
            # Non-fatal: summary display is best-effort
            self.logger.debug(f"Failed to display rebalance plan: {e}")
            print("📋 Rebalance plan generated:")
            print("   → BUY: (details unavailable)")
            print("   → SELL: (details unavailable)")

    def _display_stale_order_info(self, trading_result: dict[str, Any]) -> None:
        """Display stale order cancellation information."""
        try:
            execution_result = trading_result.get("execution_result")
            if (
                execution_result
                and hasattr(execution_result, "metadata")
                and execution_result.metadata
            ):
                stale_count = execution_result.metadata.get("stale_orders_cancelled", 0)
                if stale_count > 0:
                    print(f"🗑️ Cancelled {stale_count} stale order(s)")
        except Exception as e:
            # Non-fatal: stale order display is best-effort
            self.logger.debug(f"Failed to display stale order info: {e}")

    def _display_post_execution_tracking(self, *, paper_trading: bool) -> None:
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

    def _export_tracking_summary(self, *, export_path: str, paper_trading: bool) -> None:
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

    def _create_failure_result(
        self,
        error_message: str,
        started_at: datetime,
        correlation_id: str,
        warnings: list[str],
    ) -> TradeRunResultDTO:
        """Create a failure result DTO."""
        from datetime import UTC, datetime

        completed_at = datetime.now(UTC)

        return TradeRunResultDTO(
            status="FAILURE",
            success=False,
            execution_summary=ExecutionSummaryDTO(
                orders_total=0,
                orders_succeeded=0,
                orders_failed=0,
                total_value=Decimal("0"),
                success_rate=0.0,
                execution_duration_seconds=(completed_at - started_at).total_seconds(),
            ),
            orders=[],
            warnings=[*warnings, error_message],
            trading_mode="UNKNOWN",
            started_at=started_at,
            completed_at=completed_at,
            correlation_id=correlation_id,
        )

    def _create_success_result(
        self,
        trading_result: dict[str, Any],
        orchestrator: TradingOrchestrator,
        started_at: datetime,
        completed_at: datetime,
        correlation_id: str,
        warnings: list[str],
        *,
        success: bool,
    ) -> TradeRunResultDTO:
        """Create a success result DTO from trading results."""
        orders_executed = trading_result.get("orders_executed", [])

        # Convert orders to DTOs with ID redaction
        order_dtos: list[OrderResultSummaryDTO] = []
        for order in orders_executed:
            order_id = order.get("order_id", "")
            order_id_redacted = f"...{order_id[-6:]}" if len(order_id) > 6 else order_id

            # Calculate trade amount from qty * price if notional not available
            qty = Decimal(str(order.get("qty", 0)))
            filled_price = order.get("filled_avg_price")

            if order.get("notional"):
                trade_amount = Decimal(str(order.get("notional")))
            elif filled_price and qty:
                trade_amount = qty * Decimal(str(filled_price))
            else:
                trade_amount = Decimal("0")

            order_dtos.append(
                OrderResultSummaryDTO(
                    symbol=order.get("symbol", ""),
                    action=order.get("side", "").upper(),
                    trade_amount=trade_amount,
                    shares=qty,
                    price=(Decimal(str(filled_price)) if filled_price else None),
                    order_id_redacted=order_id_redacted,
                    order_id_full=order_id,
                    success=order.get("status", "").upper() in ["FILLED", "COMPLETE"],
                    error_message=order.get("error_message"),
                    timestamp=order.get("filled_at") or completed_at,
                )
            )

        # Calculate summary metrics
        orders_total = len(order_dtos)
        orders_succeeded = sum(1 for order in order_dtos if order.success)
        orders_failed = orders_total - orders_succeeded
        total_value = sum((order.trade_amount for order in order_dtos), Decimal("0"))
        success_rate = orders_succeeded / orders_total if orders_total > 0 else 1.0

        if success and orders_failed == 0:
            status = "SUCCESS"
        elif orders_succeeded > 0:
            status = "PARTIAL"
        else:
            status = "FAILURE"

        return TradeRunResultDTO(
            status=status,
            success=success,
            execution_summary=ExecutionSummaryDTO(
                orders_total=orders_total,
                orders_succeeded=orders_succeeded,
                orders_failed=orders_failed,
                total_value=total_value,
                success_rate=success_rate,
                execution_duration_seconds=(completed_at - started_at).total_seconds(),
            ),
            orders=order_dtos,
            warnings=warnings,
            trading_mode=("LIVE" if getattr(orchestrator, "live_trading", False) else "PAPER"),
            started_at=started_at,
            completed_at=completed_at,
            correlation_id=correlation_id,
        )

    def _configure_quiet_logging(self) -> None:
        """Configure quiet logging to reduce CLI noise."""
        # Store original levels for restoration
        self._original_levels = {}

        # Modules to quiet down (these tend to be noisy during execution)
        noisy_modules = [
            "the_alchemiser.execution_v2",
            "the_alchemiser.portfolio_v2",
            "the_alchemiser.strategy_v2",
            "the_alchemiser.orchestration",
            "the_alchemiser.orchestration.trading_orchestrator",
            "the_alchemiser.orchestration.signal_orchestrator",
            "the_alchemiser.orchestration.strategy_orchestrator",
            "the_alchemiser.orchestration.portfolio_orchestrator",
            "the_alchemiser.orchestration.event_driven_orchestrator",
            "alpaca",
            "urllib3",
            "requests",
        ]

        for module_name in noisy_modules:
            logger = logging.getLogger(module_name)
            self._original_levels[module_name] = logger.level
            logger.setLevel(logging.WARNING)

    def _restore_logging(self) -> None:
        """Restore original logging levels."""
        if hasattr(self, "_original_levels"):
            for module_name, level in self._original_levels.items():
                logger = logging.getLogger(module_name)
                logger.setLevel(level)


def _resolve_log_level(*, is_production: bool) -> int:
    """Resolve the desired log level from environment or settings."""
    # Environment override first
    level_str = os.getenv("LOGGING__LEVEL")
    if level_str:
        # Support both names (e.g. DEBUG) and numeric strings (e.g. 10)
        lvl_upper = level_str.strip().upper()
        # Numeric string
        if lvl_upper.isdigit():
            try:
                return int(lvl_upper)
            except ValueError:
                pass
        # Named level
        named = getattr(logging, lvl_upper, None)
        if isinstance(named, int):
            return named

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


def main(argv: list[str] | None = None) -> TradeRunResultDTO | bool:
    """Serve as main entry point for The Alchemiser Trading System.

    Args:
        argv: Command line arguments (uses sys.argv if None)

    Returns:
        TradeRunResultDTO for trade execution, or bool for other operations

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

        # Header suppressed to reduce duplicate banners in CLI output

        # Execute trading with integrated signal analysis
        if args.mode == "trade":
            # NOTE: CLI handles all footer rendering now - clean separation
            return system.execute_trading(
                show_tracking=getattr(args, "show_tracking", False),
                export_tracking_json=getattr(args, "export_tracking_json", None),
            )
        # This should never happen since we only accept "trade" mode now
        return False

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
