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
from the_alchemiser.shared.dto.result_factory import (
    create_failure_result,
    create_success_result,
)
from the_alchemiser.shared.dto.trade_run_result_dto import TradeRunResultDTO
from the_alchemiser.shared.errors.error_handler import TradingSystemErrorHandler
from the_alchemiser.shared.events import EventBus, StartupEvent
from the_alchemiser.shared.logging.logging_utils import (
    get_logger,
)
from the_alchemiser.shared.types.exceptions import (
    StrategyExecutionError,
    TradingClientError,
)
from the_alchemiser.shared.utils.service_factory import ServiceFactory


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
    ) -> TradeRunResultDTO:
        """Execute multi-strategy trading.

        Note: Trading mode (live/paper) is now determined by deployment stage.

        Args:
            show_tracking: Whether to display tracking after execution
            export_tracking_json: Path to export tracking JSON (optional)

        Returns:
            TradeRunResultDTO with complete execution results and metadata

        """
        # Start timing and correlation tracking
        started_at = datetime.now(UTC)
        correlation_id = str(uuid.uuid4())
        warnings: list[str] = []

        try:
            from the_alchemiser.orchestration.trading_orchestrator import (
                TradingOrchestrator,
            )

            if self.container is None:
                return create_failure_result(
                    "DI container not initialized", started_at, correlation_id, warnings
                )

            # Create trading orchestrator directly
            orchestrator = TradingOrchestrator(
                settings=self.settings,
                container=self.container,
            )

            # Execute full workflow once: generate signals, analyze portfolio, and trade

            try:
                # Execute complete workflow once (signals + analysis + trading)
                trading_result = orchestrator.execute_strategy_signals_with_trading()
            except Exception:
                # Fallback if anything fails
                trading_result = orchestrator.execute_strategy_signals_with_trading()

            if trading_result is None:
                return create_failure_result(
                    "Trading execution failed - check logs for details",
                    started_at,
                    correlation_id,
                    warnings,
                )

            # Show brief signals summary and the rebalance plan details
            display_signals_summary(trading_result)
            display_rebalance_plan(trading_result)

            # Show stale order cancellation info
            display_stale_order_info(trading_result)

            # Display tracking if requested
            if show_tracking:
                display_post_execution_tracking(
                    paper_trading=not orchestrator.live_trading
                )

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
