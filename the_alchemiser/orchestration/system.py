#!/usr/bin/env python3
"""Business Unit: orchestration | Status: current.

Trading system orchestrator and bootstrap.

Provides the main TradingSystem class that coordinates application initialization,
dependency injection, and delegates trading execution to appropriate orchestrators.
"""

from __future__ import annotations

import uuid
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from the_alchemiser.orchestration.event_driven_orchestrator import (
        EventDrivenOrchestrator,
    )

from the_alchemiser.shared.config.config import Settings, load_settings
from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.errors.error_handler import TradingSystemErrorHandler
from the_alchemiser.shared.events import EventBus, StartupEvent
from the_alchemiser.shared.logging.logging_utils import (
    get_logger,
)
from the_alchemiser.shared.schemas.trade_result_factory import (
    create_failure_result,
    create_success_result,
)
from the_alchemiser.shared.schemas.trade_run_result import TradeRunResult
from the_alchemiser.shared.types.exceptions import (
    StrategyExecutionError,
    TradingClientError,
)
from the_alchemiser.shared.utils.service_factory import ServiceFactory


class MinimalOrchestrator:
    """Minimal orchestrator-like adapter for trading mode determination.

    Provides a minimal interface to satisfy result factory requirements
    when using event-driven orchestration without creating tight coupling.
    """

    def __init__(self, *, paper_trading: bool) -> None:
        """Initialize with paper trading mode.

        Args:
            paper_trading: Whether this is paper trading mode

        """
        self.live_trading = not paper_trading


class TradingSystem:
    """Main trading system orchestrator for initialization and execution delegation."""

    BULLET_LOG_TEMPLATE = "  • %s"

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize trading system with optional settings.

        Args:
            settings: Optional settings override (uses loaded settings if None)

        """
        self.settings = settings or load_settings()
        self.logger = get_logger(__name__)
        self.error_handler = TradingSystemErrorHandler()
        self.container: ApplicationContainer | None = None
        self.event_driven_orchestrator: EventDrivenOrchestrator | None = None
        self._initialize_di()
        self._initialize_event_orchestration()

    def _initialize_di(self) -> None:
        """Initialize dependency injection system."""
        self.container = ApplicationContainer()
        # Initialize execution providers with late binding to avoid circular imports
        ApplicationContainer.initialize_execution_providers(self.container)
        ServiceFactory.initialize(self.container)
        self.logger.debug("Dependency injection initialized")

    def _initialize_event_orchestration(self) -> None:
        """Initialize event-driven orchestration system."""
        try:
            if self.container is None:
                self.logger.warning(
                    "Cannot initialize event orchestration: DI container not ready"
                )
                return

            # Initialize event-driven orchestrator
            from the_alchemiser.orchestration.event_driven_orchestrator import (
                EventDrivenOrchestrator,
            )

            self.event_driven_orchestrator = EventDrivenOrchestrator(self.container)
            self.logger.debug("Event-driven orchestration initialized")

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
                self.logger.warning(
                    "Cannot emit StartupEvent: DI container not initialized"
                )
                return

            # Get event bus from container
            event_bus: EventBus = self.container.services.event_bus()

            # Create StartupEvent
            event = StartupEvent(
                correlation_id=str(uuid.uuid4()),
                causation_id=f"system-startup-{datetime.now(UTC).isoformat()}",
                event_id=f"startup-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="orchestration.system",
                source_component="TradingSystem",
                startup_mode=startup_mode,
                configuration={
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

    def execute_trading(
        self,
        *,
        show_tracking: bool = False,
        export_tracking_json: str | None = None,
    ) -> TradeRunResult:
        """Execute multi-strategy trading.

        Note: Trading mode (live/paper) is now determined by deployment stage.

        Args:
            show_tracking: Whether to display tracking after execution
            export_tracking_json: Path to export tracking JSON (optional)

        Returns:
            TradeRunResult with complete execution results and metadata

        """
        # Start timing and correlation tracking
        started_at = datetime.now(UTC)
        correlation_id = str(uuid.uuid4())
        warnings: list[str] = []

        try:
            if self.container is None:
                return create_failure_result(
                    "DI container not initialized", started_at, correlation_id, warnings
                )

            # Try event-driven approach first, fallback to traditional orchestrator
            use_event_driven = self.event_driven_orchestrator is not None

            if use_event_driven:
                self.logger.info(
                    "🚀 Using event-driven orchestration for trading workflow"
                )
                trading_result = self._execute_trading_event_driven(
                    correlation_id,
                    started_at,
                    show_tracking=show_tracking,
                    export_tracking_json=export_tracking_json,
                )
            else:
                self.logger.info(
                    "🔄 Using traditional orchestration (event-driven not available)"
                )
                trading_result = self._execute_trading_traditional(
                    correlation_id,
                    started_at,
                    show_tracking=show_tracking,
                    export_tracking_json=export_tracking_json,
                )

            if trading_result is None:
                return create_failure_result(
                    "Trading execution failed - check logs for details",
                    started_at,
                    correlation_id,
                    warnings,
                )

            return trading_result

        except Exception as e:
            return self._handle_trading_execution_error(
                e,
                show_tracking=show_tracking,
                export_tracking_json=export_tracking_json,
            )

    def _execute_trading_event_driven(
        self,
        correlation_id: str,
        started_at: datetime,
        *,
        show_tracking: bool,
        export_tracking_json: str | None,
    ) -> TradeRunResult | None:
        """Execute trading using event-driven orchestration.

        Args:
            correlation_id: Correlation ID for tracking
            started_at: Start timestamp
            show_tracking: Whether to display tracking
            export_tracking_json: Path to export tracking JSON

        Returns:
            TradeRunResult or None if failed

        """
        try:
            if not self.event_driven_orchestrator:
                self.logger.error("Event-driven orchestrator not available")
                return None

            # Start the event-driven workflow
            workflow_correlation_id = (
                self.event_driven_orchestrator.start_trading_workflow(
                    correlation_id=correlation_id
                )
            )

            # Wait for workflow completion
            workflow_result = (
                self.event_driven_orchestrator.wait_for_workflow_completion(
                    workflow_correlation_id, timeout_seconds=300
                )
            )

            if not workflow_result.get("success"):
                self.logger.error(f"Event-driven workflow failed: {workflow_result}")
                return None

            # Collect results from workflow events
            completed_at = datetime.now(UTC)

            # Extract actual results from workflow_result
            trading_result = {
                "success": workflow_result.get("success", True),
                "strategy_signals": workflow_result.get("strategy_signals", {}),
                "rebalance_plan": workflow_result.get("rebalance_plan", {}),
                "orders_executed": workflow_result.get("orders_executed", []),
                "execution_summary": workflow_result.get("execution_summary", {}),
            }

            # Create a minimal orchestrator-like object for trading mode determination
            minimal_orchestrator = MinimalOrchestrator(
                paper_trading=self.settings.alpaca.paper_trading
            )

            paper_trading_mode = self.settings.alpaca.paper_trading

            if show_tracking:
                self._display_post_execution_tracking(
                    paper_trading=paper_trading_mode
                )

            if export_tracking_json:
                self._export_tracking_summary(
                    trading_result,
                    export_tracking_json,
                    paper_trading=paper_trading_mode,
                )

            return create_success_result(
                trading_result=trading_result,
                orchestrator=minimal_orchestrator,
                started_at=started_at,
                completed_at=completed_at,
                correlation_id=correlation_id,
                warnings=workflow_result.get("warnings", []),
                success=workflow_result.get("success", True),
            )

        except Exception as e:
            self.logger.error(f"Event-driven trading execution failed: {e}")
            return None

    def _execute_trading_traditional(
        self,
        correlation_id: str,
        started_at: datetime,
        *,
        show_tracking: bool,
        export_tracking_json: str | None,
    ) -> TradeRunResult | None:
        """Execute trading using traditional orchestration (fallback).

        Args:
            correlation_id: Correlation ID for tracking
            started_at: Start timestamp
            show_tracking: Whether to display tracking
            export_tracking_json: Path to export tracking JSON

        Returns:
            TradeRunResult or None if failed

        """
        try:
            from the_alchemiser.orchestration.trading_orchestrator import (
                TradingOrchestrator,
            )

            # Ensure container is available
            if self.container is None:
                self.logger.error(
                    "DI container not available for traditional orchestrator"
                )
                return None

            # Create trading orchestrator directly
            orchestrator = TradingOrchestrator(
                settings=self.settings,
                container=self.container,
            )

            # Execute complete workflow once (signals + analysis + trading)
            try:
                trading_result = orchestrator.execute_strategy_signals_with_trading()
            except Exception:
                # Fallback if anything fails
                trading_result = orchestrator.execute_strategy_signals_with_trading()

            if trading_result is None:
                return None

            # Show brief signals summary and the rebalance plan details
            self._log_traditional_signals_summary(trading_result)
            self._log_traditional_rebalance_plan(trading_result)

            # Show stale order cancellation info
            self._log_traditional_stale_orders(trading_result)

            # Display tracking if requested
            if show_tracking:
                self._display_post_execution_tracking(
                    paper_trading=not orchestrator.live_trading
                )

            # Export tracking summary if requested
            if export_tracking_json:
                self._export_tracking_summary(
                    trading_result,
                    export_tracking_json,
                    paper_trading=not orchestrator.live_trading,
                )

            # Create successful result DTO
            completed_at = datetime.now(UTC)
            success = bool(trading_result.get("success", False))

            return create_success_result(
                trading_result=trading_result,
                orchestrator=orchestrator,
                started_at=started_at,
                completed_at=completed_at,
                correlation_id=correlation_id,
                warnings=[],
                success=success,
            )

        except Exception as e:
            self.logger.error(f"Traditional trading execution failed: {e}")
            return None

    def _log_traditional_signals_summary(self, trading_result: dict[str, Any]) -> None:
        """Log strategy signals summary for traditional orchestrator output."""
        signal_details = self._collect_signal_details(trading_result)
        if not signal_details:
            return

        self.logger.info("📡 Final Strategy Signals (traditional path):")
        for detail in signal_details:
            self.logger.info(self.BULLET_LOG_TEMPLATE, detail)

        allocations = self._collect_target_allocations(trading_result)
        if allocations:
            self._log_target_allocations(allocations)

    def _collect_signal_details(
        self, trading_result: Mapping[str, object]
    ) -> list[str]:
        """Collect formatted signal details from the trading result."""
        signals = trading_result.get("strategy_signals")
        if not isinstance(signals, Mapping):
            return []

        details: list[str] = []
        for raw_name, raw_data in signals.items():
            detail = self._format_signal_detail(str(raw_name), raw_data)
            if detail is not None:
                details.append(detail)
        return details

    def _format_signal_detail(self, name: str, raw_data: object) -> str | None:
        """Format a single signal entry for logging."""
        if not isinstance(raw_data, Mapping):
            return None

        action_raw = raw_data.get("action", "")
        action = str(action_raw).upper() or "UNKNOWN"

        symbols_value = raw_data.get("symbols")
        if (
            raw_data.get("is_multi_symbol")
            and isinstance(symbols_value, Iterable)
            and not isinstance(symbols_value, (str, bytes))
        ):
            symbols = [
                str(symbol).strip()
                for symbol in symbols_value
                if str(symbol).strip()
            ]
            if symbols:
                joined_symbols = ", ".join(symbols)
                return f"{name}: {action} {joined_symbols}"
            return f"{name}: {action}"

        symbol = raw_data.get("symbol")
        if isinstance(symbol, str) and symbol.strip():
            return f"{name}: {action} {symbol.strip()}"
        return f"{name}: {action}"

    def _collect_target_allocations(
        self, trading_result: Mapping[str, object]
    ) -> Mapping[str, object] | None:
        """Extract target allocations from trading result if present."""
        consolidated = trading_result.get("consolidated_portfolio")
        if not isinstance(consolidated, Mapping):
            return None

        allocations = consolidated.get("target_allocations")
        if isinstance(allocations, Mapping):
            return allocations

        return consolidated

    def _log_target_allocations(self, allocations: Mapping[str, object]) -> None:
        """Log portfolio target allocations."""
        if not allocations:
            return

        self.logger.info("🎯 Target Portfolio Allocations:")
        for symbol, allocation in allocations.items():
            symbol_str = str(symbol)
            percent = self._format_percentage(allocation)
            self.logger.info("  • %s: %s%%", symbol_str, percent)

    def _log_traditional_rebalance_plan(self, trading_result: dict[str, Any]) -> None:
        """Log rebalance plan summary for traditional orchestrator output."""
        plan = trading_result.get("rebalance_plan")
        if plan is None:
            return

        if self._log_rebalance_plan_items(plan):
            return

        if isinstance(plan, Mapping):
            self._log_legacy_rebalance_plan(plan)

    def _log_rebalance_plan_items(self, plan: object) -> bool:
        """Log rebalance plan information when represented as a DTO."""
        if not hasattr(plan, "items"):
            return False

        raw_items = getattr(plan, "items", None)
        if raw_items is None:
            items: list[object] = []
        elif isinstance(raw_items, Iterable) and not isinstance(
            raw_items, (str, bytes)
        ):
            items = list(raw_items)
        else:
            items = []

        if not items:
            self.logger.info("⚖️ Final rebalance plan: no trades required")
            return True

        total_value = self._format_currency(
            getattr(plan, "total_trade_value", 0), absolute=True
        )
        self.logger.info(
            "⚖️ Final rebalance plan: %s trades | total value $%s",
            len(items),
            total_value,
        )

        for item in items:
            detail = self._format_rebalance_item(item)
            if detail:
                self.logger.info(self.BULLET_LOG_TEMPLATE, detail)

        return True

    def _format_rebalance_item(self, item: object) -> str | None:
        """Format a single rebalance item entry for logging."""
        if item is None:
            return None

        action_raw = getattr(item, "action", "")
        action = str(action_raw).upper() or "UNKNOWN"
        symbol = getattr(item, "symbol", "Unknown")

        trade_amount = self._format_currency(
            getattr(item, "trade_amount", 0), absolute=True
        )
        target_weight = self._format_percentage(getattr(item, "target_weight", 0))
        current_weight = self._format_percentage(getattr(item, "current_weight", 0))

        return (
            f"{action} {symbol} | ${trade_amount} | "
            f"target {target_weight}% vs current {current_weight}%"
        )

    def _log_legacy_rebalance_plan(self, plan: Mapping[str, object]) -> None:
        """Log rebalance plan details when using legacy dictionary structure."""
        trades = plan.get("trades")
        if not isinstance(trades, Iterable) or isinstance(trades, (str, bytes)):
            return

        trades_list = list(trades)
        if not trades_list:
            return

        self.logger.info("⚖️ Final rebalance plan: %s trades", len(trades_list))
        for trade in trades_list:
            detail = self._format_legacy_trade(trade)
            if detail:
                self.logger.info(self.BULLET_LOG_TEMPLATE, detail)

    def _format_legacy_trade(self, trade: object) -> str | None:
        """Format a single legacy trade entry for logging."""
        if not isinstance(trade, Mapping):
            return None

        symbol = trade.get("symbol", "Unknown")
        action = str(trade.get("side", "")).upper() or "UNKNOWN"
        qty = trade.get("qty", 0)

        return f"{action} {qty} shares of {symbol}"

    def _format_percentage(self, value: object) -> str:
        """Convert a ratio into a percentage string with two decimal places."""
        percent = self._decimal_from_value(value) * Decimal("100")
        return f"{percent:.2f}"

    def _format_currency(self, value: object, *, absolute: bool = False) -> str:
        """Format a monetary value to two decimal places."""
        amount = self._decimal_from_value(value)
        if absolute:
            amount = abs(amount)
        return f"{amount:.2f}"

    def _decimal_from_value(self, value: object) -> Decimal:
        """Safely convert arbitrary values into Decimal."""
        if isinstance(value, Decimal):
            return value

        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            return Decimal("0")

    def _log_traditional_stale_orders(self, trading_result: dict[str, Any]) -> None:
        """Log stale order cancellations for traditional orchestrator output."""
        stale_orders = trading_result.get("stale_orders_canceled")
        if not isinstance(stale_orders, list) or not stale_orders:
            return

        self.logger.info("🗑️ Canceled %s stale orders:", len(stale_orders))
        for order in stale_orders:
            if not isinstance(order, dict):
                continue

            symbol = order.get("symbol", "Unknown")
            side = str(order.get("side", "")).upper() or "UNKNOWN"
            qty = order.get("qty", 0)
            self.logger.info("  • %s %s shares of %s", side, qty, symbol)

    def _display_post_execution_tracking(self, *, paper_trading: bool) -> None:
        """Display optional post-execution tracking information."""
        try:
            import importlib

            mode_str = "paper trading" if paper_trading else "live trading"
            print(f"\n📊 Strategy Performance Tracking ({mode_str}):")

            module = importlib.import_module(
                "the_alchemiser.shared.utils.strategy_utils"
            )
            func = getattr(module, "display_strategy_performance_tracking", None)

            if callable(func):
                func()
            else:
                self.logger.warning("Strategy tracking utilities not available")

        except ImportError:
            self.logger.warning("Strategy tracking utilities not available")
        except Exception as exc:
            self.logger.warning(f"Failed to display post-execution tracking: {exc}")

    def _export_tracking_summary(
        self,
        trading_result: dict[str, Any],
        export_path: str,
        *,
        paper_trading: bool,
    ) -> None:
        """Export trading summary and tracking data to JSON."""
        try:
            import json
            from pathlib import Path

            summary = {
                "timestamp": datetime.now(UTC).isoformat(),
                "mode": "paper_trading" if paper_trading else "live_trading",
                "status": trading_result.get("status", "unknown"),
                "execution_summary": trading_result.get("execution_summary", {}),
                "rebalance_plan": trading_result.get("rebalance_plan"),
                "stale_orders_canceled": trading_result.get(
                    "stale_orders_canceled", []
                ),
            }

            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)

            with export_file.open("w", encoding="utf-8") as file_pointer:
                json.dump(summary, file_pointer, indent=2, default=str)

            self.logger.info("💾 Trading summary exported to: %s", export_path)

        except Exception as exc:
            self.logger.error(f"Failed to export tracking summary: {exc}")

    def _handle_trading_execution_error(
        self, e: Exception, *, show_tracking: bool, export_tracking_json: str | None
    ) -> TradeRunResult:
        """Handle trading execution errors with proper error handling and notifications.

        Args:
            e: The exception that occurred
            show_tracking: Whether tracking was requested
            export_tracking_json: Export path for tracking JSON

        Returns:
            TradeRunResult representing the failure

        """
        started_at = datetime.now(UTC)
        correlation_id = str(uuid.uuid4())
        warnings: list[str] = []

        if isinstance(e, (TradingClientError, StrategyExecutionError)):
            self.error_handler.handle_error(
                error=e,
                context="multi-strategy trading execution",
                component="TradingSystem.execute_trading",
                additional_data={
                    "show_tracking": show_tracking,
                    "export_tracking_json": export_tracking_json,
                },
            )
            # Send error notifications for trading system errors
            try:
                from the_alchemiser.shared.errors.error_handler import (
                    send_error_notification_if_needed,
                )

                send_error_notification_if_needed()
            except Exception as notification_error:
                self.logger.warning(
                    f"Failed to send error notification: {notification_error}"
                )

            return create_failure_result(
                f"System error: {e}", started_at, correlation_id, warnings
            )
        # Generic error handling
        self.logger.error(f"Unexpected trading execution error: {e}")
        return create_failure_result(
            f"Unexpected error: {e}", started_at, correlation_id, warnings
        )
