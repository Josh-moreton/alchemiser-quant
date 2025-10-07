#!/usr/bin/env python3
"""Business Unit: orchestration | Status: current.

Trading system orchestrator and bootstrap.

Provides the main TradingSystem class that coordinates application initialization,
dependency injection, and delegates trading execution to appropriate orchestrators.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from the_alchemiser.orchestration.event_driven_orchestrator import (
        EventDrivenOrchestrator,
    )

from the_alchemiser.shared.config.config import Settings, load_settings
from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.errors.error_handler import TradingSystemErrorHandler
from the_alchemiser.shared.events import EventBus, StartupEvent
from the_alchemiser.shared.logging import (
    get_logger,
)
from the_alchemiser.shared.schemas.trade_result_factory import (
    create_failure_result,
    create_success_result,
)
from the_alchemiser.shared.schemas.trade_run_result import TradeRunResult
from the_alchemiser.shared.errors.exceptions import (
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
        if self.container is None:
            raise RuntimeError("Cannot initialize event orchestration: DI container not ready")

        # Initialize event-driven orchestrator - this is required for system operation
        from the_alchemiser.orchestration.event_driven_orchestrator import (
            EventDrivenOrchestrator,
        )

        self.event_driven_orchestrator = EventDrivenOrchestrator(self.container)
        self.logger.debug("Event-driven orchestration initialized successfully")

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
            self.logger.debug(f"Emitted StartupEvent {event.event_id} for mode: {startup_mode}")

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

            # Event-driven orchestration is the ONLY execution path
            if self.event_driven_orchestrator is None:
                return create_failure_result(
                    "Event-driven orchestrator not initialized - check system configuration",
                    started_at,
                    correlation_id,
                    warnings,
                )

            self.logger.debug("🚀 Using event-driven orchestration for trading workflow")
            trading_result = self._execute_trading_event_driven(
                correlation_id,
                started_at,
                show_tracking=show_tracking,
                export_tracking_json=export_tracking_json,
            )

            if trading_result is None:
                return create_failure_result(
                    "Event-driven trading execution failed - check logs for details",
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
            workflow_correlation_id = self.event_driven_orchestrator.start_trading_workflow(
                correlation_id=correlation_id
            )

            # Wait for workflow completion
            workflow_result = self.event_driven_orchestrator.wait_for_workflow_completion(
                workflow_correlation_id, timeout_seconds=300
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
                self._display_post_execution_tracking(paper_trading=paper_trading_mode)

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

    def _display_post_execution_tracking(self, *, paper_trading: bool) -> None:
        """Display optional post-execution tracking information."""
        try:
            import importlib

            mode_str = "paper trading" if paper_trading else "live trading"
            print(f"\n📊 Strategy Performance Tracking ({mode_str}):")

            module = importlib.import_module("the_alchemiser.shared.utils.strategy_utils")
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
                "stale_orders_canceled": trading_result.get("stale_orders_canceled", []),
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

                # Use the existing event bus from the container
                if self.container is not None:
                    event_bus = self.container.services.event_bus()
                    send_error_notification_if_needed(event_bus)
                else:
                    self.logger.warning("Container not available for error notification")
            except Exception as notification_error:
                self.logger.warning(f"Failed to send error notification: {notification_error}")

            return create_failure_result(f"System error: {e}", started_at, correlation_id, warnings)
        # Generic error handling
        self.logger.error(f"Unexpected trading execution error: {e}")
        return create_failure_result(f"Unexpected error: {e}", started_at, correlation_id, warnings)
