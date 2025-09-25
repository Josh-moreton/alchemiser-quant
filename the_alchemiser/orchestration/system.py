#!/usr/bin/env python3
"""Business Unit: orchestration | Status: current.

Trading system orchestrator and bootstrap.

Provides the main TradingSystem class that coordinates application initialization,
dependency injection, and delegates trading execution to appropriate orchestrators.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from the_alchemiser.orchestration.event_driven_orchestrator import (
        EventDrivenOrchestrator,
    )

from the_alchemiser.orchestration.display_utils import (
    display_post_execution_tracking,
    display_rebalance_plan,
    display_signals_summary,
    display_stale_order_info,
    export_tracking_summary,
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
                self.logger.warning("Cannot initialize event orchestration: DI container not ready")
                return

            # Build the registry and register handlers from each module
            self._build_handler_registry()

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
    
    def _build_handler_registry(self) -> None:
        """Build the event handler registry by invoking module registration functions."""
        if self.container is None:
            self.logger.warning("Cannot build handler registry: DI container not ready")
            return
            
        try:
            # Get the registry from the container
            registry = self.container.services.event_handler_registry()
            
            # Import module registration functions and invoke them
            from the_alchemiser.execution_v2 import register_execution_handlers
            from the_alchemiser.portfolio_v2 import register_portfolio_handlers
            from the_alchemiser.strategy_v2 import register_strategy_handlers
            
            # Register handlers from each module
            register_strategy_handlers(self.container, registry)
            register_portfolio_handlers(self.container, registry)
            register_execution_handlers(self.container, registry)
            
            supported_events = registry.get_supported_events()
            self.logger.debug(
                f"Handler registry built with {len(registry.get_all_registrations())} "
                f"registrations for events: {sorted(supported_events)}"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to build handler registry: {e}")
            raise

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

            # Try event-driven approach first, fallback to traditional orchestrator
            use_event_driven = self.event_driven_orchestrator is not None

            if use_event_driven:
                self.logger.info("🚀 Using event-driven orchestration for trading workflow")
                trading_result = self._execute_trading_event_driven(
                    correlation_id,
                    started_at,
                    show_tracking=show_tracking,
                    export_tracking_json=export_tracking_json,
                )
            else:
                self.logger.info("🔄 Using traditional orchestration (event-driven not available)")
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
                self.logger.error("DI container not available for traditional orchestrator")
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
            display_signals_summary(trading_result)
            display_rebalance_plan(trading_result)

            # Show stale order cancellation info
            display_stale_order_info(trading_result)

            # Display tracking if requested
            if show_tracking:
                display_post_execution_tracking(paper_trading=not orchestrator.live_trading)

            # Export tracking summary if requested
            if export_tracking_json:
                export_tracking_summary(
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
                self.logger.warning(f"Failed to send error notification: {notification_error}")

            return create_failure_result(f"System error: {e}", started_at, correlation_id, warnings)
        # Generic error handling
        self.logger.error(f"Unexpected trading execution error: {e}")
        return create_failure_result(f"Unexpected error: {e}", started_at, correlation_id, warnings)
