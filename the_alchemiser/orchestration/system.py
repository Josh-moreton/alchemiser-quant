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
from the_alchemiser.shared.errors.exceptions import (
    ConfigurationError,
    StrategyExecutionError,
    TradingClientError,
)
from the_alchemiser.shared.events import EventBus, StartupEvent
from the_alchemiser.shared.logging import (
    get_logger,
    set_correlation_id,
)
from the_alchemiser.shared.schemas.trade_result_factory import (
    create_failure_result,
    create_success_result,
)
from the_alchemiser.shared.schemas.trade_run_result import TradeRunResult
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
    """Main trading system orchestrator for initialization and execution delegation.

    This class coordinates the initialization of the trading system including:
    - Dependency injection container setup
    - Event-driven orchestration initialization
    - Trading workflow execution coordination

    The system uses correlation IDs for distributed tracing across all operations.
    All trading executions are idempotent - duplicate correlation IDs return cached results.
    """

    # Workflow timeout in seconds (configurable via settings in future)
    WORKFLOW_TIMEOUT_SECONDS = 300

    def __init__(self, settings: Settings | None = None) -> None:
        """Initialize trading system with optional settings.

        Args:
            settings: Optional settings override (uses loaded settings if None)

        Pre-conditions:
            - None (initializes fresh state)

        Post-conditions:
            - container is initialized with all services
            - event_driven_orchestrator is ready for workflow execution
            - error_handler is ready to track errors

        Side effects:
            - Initializes global ServiceFactory singleton
            - Registers execution providers in container
            - Creates event bus and registers handlers

        Raises:
            ConfigurationError: If settings cannot be loaded or are invalid
            ConfigurationError: If DI container initialization fails

        """
        self.settings = settings or load_settings()
        self.logger = get_logger(__name__)
        self.error_handler = TradingSystemErrorHandler()
        self.container: ApplicationContainer | None = None
        self.event_driven_orchestrator: EventDrivenOrchestrator | None = None
        # Idempotency tracking: correlation_id -> TradeRunResult
        self._execution_cache: dict[str, TradeRunResult] = {}
        self._initialize_di()
        self._initialize_event_orchestration()

    def _initialize_di(self) -> None:
        """Initialize dependency injection system.

        Raises:
            ConfigurationError: If container initialization fails

        """
        try:
            # Use create_for_environment which properly initializes all providers
            # including execution providers through dynamic wiring
            self.container = ApplicationContainer.create_for_environment("development")
            ServiceFactory.initialize(self.container)
            self.logger.debug("Dependency injection initialized")
        except Exception as e:
            raise ConfigurationError(
                f"Failed to initialize dependency injection: {e}",
                config_key="container_initialization",
            ) from e

    def _initialize_event_orchestration(self) -> None:
        """Initialize event-driven orchestration system.

        Raises:
            ConfigurationError: If DI container is not initialized
            ConfigurationError: If EventDrivenOrchestrator creation fails

        """
        if self.container is None:
            raise ConfigurationError(
                "Cannot initialize event orchestration: DI container not ready",
                config_key="container",
            )

        # Initialize event-driven orchestrator - this is required for system operation
        try:
            from the_alchemiser.orchestration.event_driven_orchestrator import (
                EventDrivenOrchestrator,
            )

            self.event_driven_orchestrator = EventDrivenOrchestrator(self.container)
            self.logger.debug("Event-driven orchestration initialized successfully")
        except ImportError as e:
            raise ConfigurationError(
                f"Failed to import EventDrivenOrchestrator: {e}", config_key="event_orchestration"
            ) from e
        except Exception as e:
            raise ConfigurationError(
                f"Failed to initialize event orchestration: {e}", config_key="event_orchestration"
            ) from e

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
            self.logger.debug(
                "Emitted StartupEvent", event_id=event.event_id, startup_mode=startup_mode
            )

        except (AttributeError, ConfigurationError) as e:
            # Don't let startup event emission failure break the system
            self.logger.warning("Failed to emit StartupEvent", error=str(e))

    def execute_trading(
        self,
        *,
        show_tracking: bool = False,
        export_tracking_json: str | None = None,
        correlation_id: str | None = None,
    ) -> TradeRunResult:
        """Execute multi-strategy trading.

        Note: Trading mode (live/paper) is now determined by deployment stage.

        Args:
            show_tracking: Whether to display tracking after execution
            export_tracking_json: Path to export tracking JSON (optional)
            correlation_id: Optional correlation ID for idempotency (generates new UUID if None)

        Returns:
            TradeRunResult with complete execution results and metadata

        Pre-conditions:
            - container must be initialized (checked internally)
            - event_driven_orchestrator must be initialized (checked internally)

        Post-conditions:
            - Trading workflow is executed or cached result is returned
            - Result is stored in execution cache for idempotency
            - correlation_id is set in logging context for tracing

        Side effects:
            - Sets correlation_id in logging context for distributed tracing
            - May display tracking information if show_tracking=True
            - May export JSON file if export_tracking_json is provided
            - Caches execution result by correlation_id

        Raises:
            TradingClientError: If trading execution fails
            StrategyExecutionError: If strategy execution fails
            ConfigurationError: If system not properly initialized

        """
        # Start timing and correlation tracking
        started_at = datetime.now(UTC)
        exec_correlation_id = correlation_id or str(uuid.uuid4())
        warnings: list[str] = []

        # Set correlation_id in logging context for automatic propagation
        set_correlation_id(exec_correlation_id)

        # Check idempotency - return cached result if already executed
        if exec_correlation_id in self._execution_cache:
            self.logger.info(
                "Returning cached trading result (idempotency check)",
                correlation_id=exec_correlation_id,
                cached=True,
            )
            return self._execution_cache[exec_correlation_id]

        try:
            if self.container is None:
                result = create_failure_result(
                    "DI container not initialized", started_at, exec_correlation_id, warnings
                )
                self._execution_cache[exec_correlation_id] = result
                return result

            # Event-driven orchestration is the ONLY execution path
            if self.event_driven_orchestrator is None:
                result = create_failure_result(
                    "Event-driven orchestrator not initialized - check system configuration",
                    started_at,
                    exec_correlation_id,
                    warnings,
                )
                self._execution_cache[exec_correlation_id] = result
                return result

            self.logger.debug("Using event-driven orchestration for trading workflow")
            trading_result = self._execute_trading_event_driven(
                exec_correlation_id,
                started_at,
                show_tracking=show_tracking,
                export_tracking_json=export_tracking_json,
            )

            if trading_result is None:
                result = create_failure_result(
                    "Event-driven trading execution failed - check logs for details",
                    started_at,
                    exec_correlation_id,
                    warnings,
                )
                self._execution_cache[exec_correlation_id] = result
                return result

            # Cache successful result for idempotency
            self._execution_cache[exec_correlation_id] = trading_result
            return trading_result

        except (TradingClientError, StrategyExecutionError, ConfigurationError) as e:
            result = self._handle_trading_execution_error(
                e,
                correlation_id=exec_correlation_id,
                started_at=started_at,
            )
            self._execution_cache[exec_correlation_id] = result
            return result
        except Exception as e:
            # Unexpected errors - log and convert to proper exception type
            self.logger.error(
                "Unexpected error in trading execution", error=str(e), error_type=type(e).__name__
            )
            result = self._handle_trading_execution_error(
                TradingClientError(f"Unexpected error: {e}"),
                correlation_id=exec_correlation_id,
                started_at=started_at,
            )
            self._execution_cache[exec_correlation_id] = result
            return result

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

        Raises:
            ConfigurationError: If orchestrator is not available
            TradingClientError: If workflow execution fails

        """
        try:
            if not self.event_driven_orchestrator:
                self.logger.error("Event-driven orchestrator not available")
                return None

            # Start the event-driven workflow
            workflow_correlation_id = self.event_driven_orchestrator.start_trading_workflow(
                correlation_id=correlation_id
            )

            # Wait for workflow completion with configurable timeout
            workflow_result = self.event_driven_orchestrator.wait_for_workflow_completion(
                workflow_correlation_id, timeout_seconds=self.WORKFLOW_TIMEOUT_SECONDS
            )

            if not workflow_result.get("success"):
                self.logger.error(
                    "Event-driven workflow failed",
                    workflow_result=workflow_result,
                    correlation_id=correlation_id,
                )
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

        except (TradingClientError, StrategyExecutionError, ConfigurationError) as e:
            self.logger.error(
                "Event-driven trading execution failed with known error",
                error=str(e),
                error_type=type(e).__name__,
                correlation_id=correlation_id,
            )
            raise
        except Exception as e:
            self.logger.error(
                "Event-driven trading execution failed with unexpected error",
                error=str(e),
                error_type=type(e).__name__,
                correlation_id=correlation_id,
            )
            # Convert to TradingClientError for consistent error handling
            raise TradingClientError(f"Event-driven trading execution failed: {e}") from e

    def _display_post_execution_tracking(self, *, paper_trading: bool) -> None:
        """Display optional post-execution tracking information.

        Args:
            paper_trading: Whether this is paper trading mode

        """
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

        except ImportError as e:
            self.logger.warning("Strategy tracking utilities not available", error=str(e))
        except Exception as exc:
            self.logger.warning(
                "Failed to display post-execution tracking",
                error=str(exc),
                error_type=type(exc).__name__,
            )

    def _export_tracking_summary(
        self,
        trading_result: dict[str, Any],
        export_path: str,
        *,
        paper_trading: bool,
    ) -> None:
        """Export trading summary and tracking data to JSON.

        Args:
            trading_result: Trading execution results
            export_path: File path for JSON export
            paper_trading: Whether this is paper trading mode

        """
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

            self.logger.info("Trading summary exported", export_path=export_path)

        except OSError as exc:
            self.logger.error(
                "Failed to export tracking summary (file error)",
                error=str(exc),
                export_path=export_path,
            )
        except Exception as exc:
            self.logger.error(
                "Failed to export tracking summary",
                error=str(exc),
                error_type=type(exc).__name__,
                export_path=export_path,
            )

    def _handle_trading_execution_error(
        self,
        e: Exception,
        *,
        correlation_id: str,
        started_at: datetime,
    ) -> TradeRunResult:
        """Handle trading execution errors with proper error handling and notifications.

        Args:
            e: The exception that occurred
            correlation_id: Correlation ID for this execution (for tracing)
            started_at: When execution started

        Returns:
            TradeRunResult representing the failure

        """
        warnings: list[str] = []

        if isinstance(e, (TradingClientError, StrategyExecutionError)):
            self.error_handler.handle_error(
                error=e,
                context="multi-strategy trading execution",
                component="TradingSystem.execute_trading",
                additional_data={
                    "correlation_id": correlation_id,
                },
            )
            # Send error notifications for trading system errors
            try:
                from the_alchemiser.shared.errors.error_handler import (
                    send_error_notification_if_needed,
                )

                # Use the existing event bus from the container
                if self.container is not None and hasattr(self.container, "services"):
                    event_bus = self.container.services.event_bus()
                    send_error_notification_if_needed(event_bus)
                else:
                    self.logger.warning("Container not available for error notification")
            except (ImportError, AttributeError, ConfigurationError) as notification_error:
                self.logger.warning(
                    "Failed to send error notification",
                    error=str(notification_error),
                    error_type=type(notification_error).__name__,
                )

            return create_failure_result(f"System error: {e}", started_at, correlation_id, warnings)

        # Generic error handling
        self.logger.error(
            "Unexpected trading execution error",
            error=str(e),
            error_type=type(e).__name__,
            correlation_id=correlation_id,
        )
        return create_failure_result(f"Unexpected error: {e}", started_at, correlation_id, warnings)
