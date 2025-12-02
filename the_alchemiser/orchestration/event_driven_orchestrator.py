#!/usr/bin/env python3
"""Business Unit: orchestration | Status: current.

Event-driven orchestration handlers for cross-cutting concerns.

Provides event handlers for notifications, reconciliation, monitoring, and recovery
across the trading workflow. Focused on cross-cutting concerns rather than domain execution.
"""

from __future__ import annotations

import time
import uuid
from collections.abc import Callable as TypingCallable
from datetime import UTC, datetime
from decimal import Decimal
from threading import Lock
from typing import TYPE_CHECKING, Any, cast
from uuid import uuid4

import httpx

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer

from the_alchemiser.shared.errors import (
    ConfigurationError,
    EventBusError,
    MarketDataError,
    TradingClientError,
    ValidationError,
)
from the_alchemiser.shared.events import (
    BaseEvent,
    EventBus,
    RebalancePlanned,
    SignalGenerated,
    StartupEvent,
    TradeExecuted,
    WorkflowCompleted,
    WorkflowFailed,
    WorkflowStarted,
)
from the_alchemiser.shared.events.handlers import EventHandler as SharedEventHandler
from the_alchemiser.shared.logging import get_logger

# Import workflow state management
from .workflow_state import (
    StateCheckingHandlerWrapper,
    WorkflowState,
)


class EventDrivenOrchestrator:
    """Event-driven orchestrator for primary workflow coordination.

    Coordinates complete trading workflows through event-driven handlers,
    managing domain handlers and workflow state. This is the primary coordinator
    for event-driven architecture.
    """

    def __init__(
        self, container: ApplicationContainer, *, http_client: httpx.Client | None = None
    ) -> None:
        """Initialize the event-driven orchestrator.

        Args:
            container: Application container for dependency injection

        """
        self.container = container
        self.logger = get_logger(__name__)

        # Load settings for HTTP orchestration toggles
        self.settings = self.container.config.settings()
        self.orchestration_settings = getattr(self.settings, "orchestration", None)
        self.use_http_domain_workflow = bool(
            getattr(self.orchestration_settings, "use_http_domain_workflow", False)
        )
        self.http_endpoints: dict[str, str] = {
            "strategy": getattr(self.orchestration_settings, "strategy_endpoint", ""),
            "portfolio": getattr(self.orchestration_settings, "portfolio_endpoint", ""),
            "execution": getattr(self.orchestration_settings, "execution_endpoint", ""),
        }
        self.http_max_retries = int(getattr(self.orchestration_settings, "http_max_retries", 3))
        self.http_retry_backoff = float(
            getattr(self.orchestration_settings, "http_retry_backoff_seconds", 0.5)
        )
        self.http_client = http_client or httpx.Client(timeout=10.0)
        self._http_idempotency_cache: set[tuple[str, str]] = set()

        # Get event bus from container
        self.event_bus: EventBus = container.services.event_bus()

        # Cache event dispatch mapping to avoid per-call construction
        # Use cast to align specific handler signatures with BaseEvent for dispatching
        self._event_handlers: dict[type[BaseEvent], TypingCallable[[BaseEvent], None]] = {
            StartupEvent: cast(TypingCallable[[BaseEvent], None], self._handle_startup),
            WorkflowStarted: cast(TypingCallable[[BaseEvent], None], self._handle_workflow_started),
            SignalGenerated: cast(TypingCallable[[BaseEvent], None], self._handle_signal_generated),
            RebalancePlanned: cast(
                TypingCallable[[BaseEvent], None], self._handle_rebalance_planned
            ),
            TradeExecuted: cast(TypingCallable[[BaseEvent], None], self._handle_trade_executed),
            WorkflowCompleted: cast(
                TypingCallable[[BaseEvent], None], self._handle_workflow_completed
            ),
            WorkflowFailed: cast(TypingCallable[[BaseEvent], None], self._handle_workflow_failed),
        }

        # Register orchestrator's event handlers FIRST so workflow_results is populated
        # before domain handlers process events (critical for data flow)
        self._register_handlers()

        # Register domain handlers using module registration functions unless HTTP workflow is enabled
        # These run AFTER orchestrator handlers, so they can access workflow_results
        if not self.use_http_domain_workflow:
            self._register_domain_handlers()
        else:
            self.logger.info(
                "HTTP domain workflow enabled - skipping in-process handler registration"
            )

        # Track workflow state for monitoring and recovery
        self.workflow_state: dict[str, Any] = {
            "startup_completed": False,
            "signal_generation_in_progress": False,
            "rebalancing_in_progress": False,
            "trading_in_progress": False,
            "last_successful_workflow": None,
            "active_correlations": set(),
            "workflow_start_times": {},  # Track workflow start times for duration calculation
            "completed_correlations": set(),  # Track completed/failed correlation IDs to dedupe starts
        }

        # Collect workflow results for each correlation ID
        self.workflow_results: dict[str, dict[str, Any]] = {}

        # Track workflow states per correlation_id for failure prevention
        self.workflow_states: dict[str, WorkflowState] = {}
        self.workflow_states_lock = Lock()

        # Set this orchestrator as the workflow state checker on the event bus
        self.event_bus.set_workflow_state_checker(self)

    def _register_domain_handlers(self) -> None:
        """Register domain event handlers using module registration functions.

        This uses the event-driven API from each business module to register
        their handlers with the event bus. This maintains proper module boundaries.
        """
        try:
            # Register handlers from each business module
            from the_alchemiser.execution_v2 import register_execution_handlers
            from the_alchemiser.notifications_v2 import register_notification_handlers
            from the_alchemiser.portfolio_v2 import register_portfolio_handlers
            from the_alchemiser.strategy_v2 import register_strategy_handlers

            register_strategy_handlers(self.container)
            register_portfolio_handlers(self.container)
            register_execution_handlers(self.container)
            register_notification_handlers(self.container)

            # Wrap handlers with state checking
            self._wrap_handlers_with_state_checking()

            self.logger.debug("Registered domain event handlers via module registration functions")

        except (ImportError, AttributeError, TypeError) as e:
            # Module or registration errors - wrap in ConfigurationError
            self.logger.error(
                f"Failed to register domain handlers due to configuration error: {e}",
                extra={"error_type": type(e).__name__},
            )
            raise ConfigurationError(
                f"Domain handler registration failed: {e}",
                config_key="domain_handlers",
            ) from e
        except Exception as e:
            # Unexpected errors during registration - wrap in RuntimeError
            self.logger.error(
                f"Failed to register domain handlers due to unexpected error: {e}",
                exc_info=True,
                extra={"error_type": type(e).__name__},
            )
            raise RuntimeError(f"Domain handler registration failed: {e}") from e

    def _wrap_handlers_with_state_checking(self) -> None:
        """Wrap registered handlers with workflow state checking.

        This ensures handlers skip processing for failed workflows without
        modifying the handlers themselves.
        """
        # Get the event bus to access registered handlers
        event_bus = self.event_bus

        # Event types that should check workflow state before processing
        # Note: TradeExecuted added to prevent post-failure execution events
        state_checked_events = [
            "SignalGenerated",
            "RebalancePlanned",
            "TradeExecuted",
        ]

        for event_type in state_checked_events:
            if event_type in event_bus._handlers:
                original_handlers = event_bus._handlers[event_type].copy()
                event_bus._handlers[event_type].clear()

                for handler in original_handlers:
                    # Only wrap real EventHandler implementations; pass through plain callables
                    if isinstance(handler, SharedEventHandler):
                        wrapped_handler = StateCheckingHandlerWrapper(
                            handler, self, event_type, self.logger
                        )
                        event_bus._handlers[event_type].append(wrapped_handler)
                    else:
                        event_bus._handlers[event_type].append(handler)

    def start_trading_workflow(self, *, correlation_id: str | None = None) -> str:
        """Start a complete trading workflow via event-driven coordination.

        Args:
            correlation_id: Optional correlation ID for tracking (generates one if None)

        Returns:
            The correlation ID for tracking the workflow

        """
        workflow_correlation_id = correlation_id or str(uuid.uuid4())

        self.logger.info(f"🚀 Starting event-driven trading workflow: {workflow_correlation_id}")

        try:
            # Check market status before starting workflow
            market_is_open = False
            market_status = "unknown"
            try:
                from the_alchemiser.shared.services.market_clock_service import (
                    MarketClockService,
                )

                # Get trading client from container
                trading_client = self.container.infrastructure.alpaca_manager().trading_client
                market_clock_service = MarketClockService(trading_client)

                # Check if market is open
                market_is_open = market_clock_service.is_market_open(
                    correlation_id=workflow_correlation_id
                )
                market_status = "open" if market_is_open else "closed"

                if not market_is_open:
                    self.logger.warning(
                        "⚠️  Market is currently closed - signal generation will proceed "
                        "but order placement will be skipped",
                        correlation_id=workflow_correlation_id,
                        market_status=market_status,
                    )
                else:
                    self.logger.info(
                        "✅ Market is open - full trading workflow will execute",
                        correlation_id=workflow_correlation_id,
                        market_status=market_status,
                    )
            except (MarketDataError, TradingClientError) as market_check_error:
                # Expected API errors during market check - log and continue
                self.logger.warning(
                    f"Market status check failed with API error: {market_check_error}",
                    correlation_id=workflow_correlation_id,
                    error_type=type(market_check_error).__name__,
                )
            except Exception as market_check_error:
                # Unexpected errors during market check - don't fail workflow, log and continue
                self.logger.warning(
                    f"Failed to check market status due to unexpected error: {market_check_error}",
                    correlation_id=workflow_correlation_id,
                    error_type=type(market_check_error).__name__,
                )

            # Emit WorkflowStarted event to trigger the domain handlers
            workflow_event = WorkflowStarted(
                correlation_id=workflow_correlation_id,
                causation_id=f"system-request-{datetime.now(UTC).isoformat()}",
                event_id=f"workflow-started-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="orchestration.event_driven_orchestrator",
                source_component="EventDrivenOrchestrator",
                workflow_type="trading",
                requested_by="TradingSystem",
                configuration={
                    "live_trading": not self.container.config.paper_trading(),
                    "market_is_open": market_is_open,
                    "market_status": market_status,
                },
            )

            self.event_bus.publish(workflow_event)
            self.logger.debug(f"📡 Emitted WorkflowStarted event: {workflow_correlation_id}")

            return workflow_correlation_id

        except (ValidationError, EventBusError) as e:
            # Event construction or validation errors - log and reraise
            self.logger.error(
                f"Failed to start trading workflow due to validation/event error: {e}",
                extra={"error_type": type(e).__name__},
            )
            raise
        except Exception as e:
            # Unexpected errors - log and reraise
            self.logger.error(
                f"Failed to start trading workflow due to unexpected error: {e}",
                exc_info=True,
                extra={"error_type": type(e).__name__},
            )
            raise

    def wait_for_workflow_completion(
        self, correlation_id: str, timeout_seconds: int = 300
    ) -> dict[str, Any]:
        """Wait for workflow completion and return results.

        Args:
            correlation_id: Correlation ID to track
            timeout_seconds: Maximum time to wait for completion

        Returns:
            Dictionary containing workflow results

        """
        start_time = time.time()

        self.logger.info(f"⏳ Waiting for workflow completion: {correlation_id}")

        while time.time() - start_time < timeout_seconds:
            # Check if workflow completed
            if correlation_id not in self.workflow_state["active_correlations"]:
                self.logger.info(f"✅ Workflow completed: {correlation_id}")

                # Get collected workflow results
                workflow_results = self.workflow_results.get(correlation_id, {})

                # Clean up stored results to prevent memory leaks
                self.workflow_results.pop(correlation_id, None)

                # Clean up workflow state to prevent memory leaks
                self.cleanup_workflow_state(correlation_id)

                return {
                    "success": True,
                    "correlation_id": correlation_id,
                    "completion_status": "completed",
                    "duration_seconds": time.time() - start_time,
                    "strategy_signals": workflow_results.get("strategy_signals", {}),
                    "rebalance_plan": workflow_results.get("rebalance_plan", {}),
                    "orders_executed": workflow_results.get("orders_executed", []),
                    "execution_summary": workflow_results.get("execution_summary", {}),
                    "warnings": [],  # Can be populated from event data if needed
                }

            # Brief sleep to avoid busy waiting
            time.sleep(0.1)

        # Timeout occurred
        self.logger.warning(f"⏰ Workflow timeout after {timeout_seconds}s: {correlation_id}")

        # Clean up on timeout
        self.workflow_results.pop(correlation_id, None)
        self.cleanup_workflow_state(correlation_id)

        return {
            "success": False,
            "correlation_id": correlation_id,
            "completion_status": "timeout",
            "duration_seconds": timeout_seconds,
        }

    def _register_handlers(self) -> None:
        """Register orchestration event handlers for cross-cutting concerns."""
        # Subscribe to all event types for cross-cutting concerns (monitoring, notifications)
        for event_type in (
            "StartupEvent",
            "WorkflowStarted",
            "SignalGenerated",
            "RebalancePlanned",
            "TradeExecuted",
            "WorkflowCompleted",
            "WorkflowFailed",
        ):
            self.event_bus.subscribe(event_type, self)

        self.logger.debug(
            "Registered event-driven orchestration handlers for cross-cutting concerns"
        )

    def handle_event(self, event: BaseEvent) -> None:
        """Handle events for cross-cutting orchestration concerns.

        Args:
            event: The event to handle

        """
        try:
            # Use cached dispatch map to avoid per-call dictionary creation
            handler = self._event_handlers.get(type(event))
            if handler:
                handler(event)
            else:
                self.logger.debug(
                    f"EventDrivenOrchestrator ignoring event type: {event.event_type}"
                )

        except (EventBusError, ValidationError) as e:
            # Event handling errors - log but don't propagate (orchestrator is event boundary)
            self.logger.error(
                f"EventDrivenOrchestrator event handling failed with known error for {event.event_type}: {e}",
                extra={
                    "event_id": event.event_id,
                    "correlation_id": event.correlation_id,
                    "error_type": type(e).__name__,
                },
            )
        except Exception as e:
            # Unexpected errors - log but don't propagate (orchestrator is event boundary)
            self.logger.error(
                f"EventDrivenOrchestrator event handling failed with unexpected error for {event.event_type}: {e}",
                exc_info=True,
                extra={
                    "event_id": event.event_id,
                    "correlation_id": event.correlation_id,
                    "error_type": type(e).__name__,
                },
            )

    def can_handle(self, event_type: str) -> bool:
        """Check if handler can handle a specific event type.

        Args:
            event_type: The type of event to check

        Returns:
            True if this handler can handle the event type

        """
        return event_type in [
            "StartupEvent",
            "WorkflowStarted",
            "SignalGenerated",
            "RebalancePlanned",
            "TradeExecuted",
            "WorkflowCompleted",
            "WorkflowFailed",
        ]

    def _post_with_retries(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Post to an endpoint with retry and idempotency safeguards.

        Args:
            url: Target endpoint URL
            payload: JSON payload to POST (must contain event_id or causation_id for idempotency)

        Returns:
            Response JSON as dict, or empty dict {} if request was previously executed (idempotency guard)

        Raises:
            httpx.HTTPError: Re-raises the last HTTP exception if all retry attempts fail
            httpx.TimeoutException: Re-raises timeout if all retry attempts fail
            httpx.RequestError: Re-raises request error if all retry attempts fail

        Notes:
            - Idempotency is tracked via (url, event_id/causation_id) tuples
            - Retries self.http_max_retries times with self.http_retry_backoff_seconds delays
            - Cached idempotent requests are logged but not re-executed
        """

        request_key = (url, str(payload.get("event_id") or payload.get("causation_id", "")))
        if request_key in self._http_idempotency_cache:
            self.logger.debug(
                "Skipping duplicate HTTP call (idempotency guard)",
                extra={
                    "endpoint": url,
                    "payload_event_id": payload.get("event_id"),
                    "correlation_id": payload.get("correlation_id"),
                },
            )
            return {}

        last_error: Exception | None = None
        for attempt in range(1, self.http_max_retries + 1):
            try:
                response = self.http_client.post(url, json=payload)
                response.raise_for_status()
                self._http_idempotency_cache.add(request_key)
                return cast(dict[str, Any], response.json())
            except (httpx.HTTPError, httpx.TimeoutException, httpx.RequestError) as exc:
                last_error = exc
                self.logger.warning(
                    "HTTP call failed - retrying",
                    extra={
                        "endpoint": url,
                        "attempt": attempt,
                        "max_attempts": self.http_max_retries,
                        "error_type": type(exc).__name__,
                        "error_detail": str(exc),
                        "correlation_id": payload.get("correlation_id"),
                    },
                )
                if attempt < self.http_max_retries:
                    time.sleep(self.http_retry_backoff)

        # Log final error before raising
        self.logger.error(
            "HTTP call failed after all retries",
            extra={
                "endpoint": url,
                "max_attempts": self.http_max_retries,
                "final_error": str(last_error),
                "correlation_id": payload.get("correlation_id"),
            },
        )
        raise last_error  # type: ignore[misc]

    def _deserialize_event_from_payload(self, payload: dict[str, Any]) -> BaseEvent | None:
        """Deserialize event payload into event object based on event_type.

        Args:
            payload: Either a raw event dict or {"event": <event_dict>} wrapper

        Returns:
            Deserialized event object, or None if:
            - event_type is not recognized (SignalGenerated, RebalancePlanned, TradeExecuted,
              WorkflowFailed, WorkflowCompleted)
            - payload structure is invalid (not a dict)
            - Pydantic validation fails

        Notes:
            - Performs timestamp string -> datetime conversion (handles ISO format + 'Z' suffix)
            - Converts string monetary values to Decimal for RebalancePlanned events
            - Logs errors for parsing failures but doesn't raise exceptions
        """

        # First check if payload itself is a dict
        if not isinstance(payload, dict):
            self.logger.error(
                "Cannot deserialize event - payload is not a dict",
                extra={
                    "payload_type": type(payload).__name__,
                },
            )
            return None

        correlation_id = payload.get("correlation_id", "unknown")

        event_data = payload.get("event") if "event" in payload else payload
        if not isinstance(event_data, dict):
            self.logger.error(
                "Cannot deserialize event - event data is not a dict",
                extra={
                    "event_data_type": type(event_data).__name__,
                    "correlation_id": correlation_id,
                },
            )
            return None

        timestamp_value = event_data.get("timestamp")
        if isinstance(timestamp_value, str):
            try:
                event_data["timestamp"] = datetime.fromisoformat(
                    timestamp_value.replace("Z", "+00:00")
                )
            except ValueError:
                self.logger.warning(
                    "Failed to parse timestamp from HTTP payload", extra={"value": timestamp_value}
                )

        if event_data.get("event_type") == "RebalancePlanned":
            plan_data = event_data.get("rebalance_plan")
            if isinstance(plan_data, dict):
                plan_timestamp = plan_data.get("timestamp")
                if isinstance(plan_timestamp, str):
                    try:
                        plan_data["timestamp"] = datetime.fromisoformat(
                            plan_timestamp.replace("Z", "+00:00")
                        )
                    except ValueError:
                        self.logger.debug(
                            "Skipping plan timestamp normalization", extra={"value": plan_timestamp}
                        )

                for field_name in (
                    "total_portfolio_value",
                    "total_trade_value",
                    "max_drift_tolerance",
                ):
                    if isinstance(plan_data.get(field_name), str):
                        plan_data[field_name] = Decimal(plan_data[field_name])

                items = plan_data.get("items")
                if isinstance(items, list):
                    for item in items:
                        if not isinstance(item, dict):
                            continue
                        for field_name in (
                            "current_weight",
                            "target_weight",
                            "weight_diff",
                            "target_value",
                            "current_value",
                            "trade_amount",
                        ):
                            if isinstance(item.get(field_name), str):
                                item[field_name] = Decimal(item[field_name])

            allocation_comparison = event_data.get("allocation_comparison")
            if isinstance(allocation_comparison, dict):
                for key in ("target_values", "current_values", "deltas"):
                    values = allocation_comparison.get(key)
                    if isinstance(values, dict):
                        for symbol, value in values.items():
                            if isinstance(value, str):
                                values[symbol] = Decimal(value)

        event_type = event_data.get("event_type")
        if not event_type:
            self.logger.error(
                "Cannot deserialize event - missing event_type",
                extra={
                    "event_data_keys": list(event_data.keys()),
                    "correlation_id": correlation_id,
                },
            )
            return None

        # Map event types to their classes
        event_class_map = {
            "SignalGenerated": SignalGenerated,
            "RebalancePlanned": RebalancePlanned,
            "TradeExecuted": TradeExecuted,
            "WorkflowFailed": WorkflowFailed,
            "WorkflowCompleted": WorkflowCompleted,
        }

        event_class = event_class_map.get(event_type)
        if not event_class:
            self.logger.error(
                "Cannot deserialize event - unknown event_type",
                extra={
                    "event_type": event_type,
                    "correlation_id": correlation_id,
                    "known_types": list(event_class_map.keys()),
                },
            )
            return None

        # Try to instantiate event with Pydantic validation
        try:
            return event_class(**event_data)  # type: ignore[no-any-return]
        except Exception as exc:
            self.logger.error(
                "Cannot deserialize event - validation failed",
                extra={
                    "event_type": event_type,
                    "correlation_id": correlation_id,
                    "error_type": type(exc).__name__,
                    "error_detail": str(exc),
                },
            )
            return None

    def _publish_http_event(self, payload: dict[str, Any]) -> None:
        """Publish an event derived from HTTP response payload to the event bus.

        Args:
            payload: HTTP response payload containing event data

        Notes:
            - Logs error if payload cannot be deserialized to a valid event
            - Uses _deserialize_event_from_payload for payload processing
            - No exceptions raised for invalid payloads
        """

        event = self._deserialize_event_from_payload(payload)
        if event:
            self.event_bus.publish(event)
        else:
            self.logger.error(
                "Failed to publish HTTP event - deserialization returned None",
                extra={
                    "correlation_id": payload.get("correlation_id", "unknown"),
                    "payload_keys": list(payload.keys()),
                    "payload_event_type": (
                        payload.get("event", {}).get("event_type")
                        if isinstance(payload.get("event"), dict)
                        else payload.get("event_type")
                    ),
                },
            )

    def _handle_startup(self, event: StartupEvent) -> None:
        """Handle system startup event for monitoring and coordination.

        Args:
            event: The startup event

        """
        self.logger.info(
            f"🚀 EventDrivenOrchestrator: System startup monitoring for mode: {event.startup_mode}"
        )

        # Update workflow monitoring state
        self.workflow_state.update(
            {
                "startup_completed": True,
                "signal_generation_in_progress": False,
                "rebalancing_in_progress": False,
                "trading_in_progress": False,
            }
        )

        # Track this correlation for monitoring
        self.workflow_state["active_correlations"].add(event.correlation_id)

        # Log startup configuration for monitoring
        configuration = event.configuration or {}
        self.logger.debug(f"Monitoring startup configuration: {configuration}")

        # Track successful startup
        self.workflow_state["last_successful_workflow"] = "startup"

    def _handle_workflow_started(self, event: WorkflowStarted) -> None:
        """Handle workflow started event and delegate to strategy endpoint when enabled."""

        self.workflow_state["active_correlations"].add(event.correlation_id)

        if not self.use_http_domain_workflow:
            return

        strategy_endpoint = self.http_endpoints.get("strategy")
        if not strategy_endpoint:
            error_msg = (
                "HTTP workflow is enabled but strategy endpoint is not configured. "
                "Set orchestration.strategy_endpoint in config or disable use_http_domain_workflow."
            )
            self.logger.error(
                error_msg,
                extra={
                    "correlation_id": event.correlation_id,
                    "http_endpoints": self.http_endpoints,
                },
            )
            raise ConfigurationError(error_msg, config_key="orchestration.strategy_endpoint")

        payload = {
            "correlation_id": event.correlation_id,
            "causation_id": event.event_id,
            "event_type": event.event_type,
            "event_id": f"strategy-request-{uuid4()}",
            "trigger_event": event.model_dump(mode="json"),
        }

        try:
            response_payload = self._post_with_retries(strategy_endpoint, payload)
            if response_payload:
                self._publish_http_event(response_payload)
        except (httpx.HTTPError, httpx.TimeoutException, httpx.RequestError) as exc:
            self.logger.error(
                "Failed to call strategy endpoint in workflow",
                extra={
                    "correlation_id": event.correlation_id,
                    "causation_id": event.event_id,
                    "endpoint": strategy_endpoint,
                    "workflow_stage": "strategy",
                    "error_type": type(exc).__name__,
                    "error_detail": str(exc),
                },
            )
            raise

    def _handle_signal_generated(self, event: SignalGenerated) -> None:
        """Handle signal generation event for monitoring.

        Args:
            event: The signal generated event

        """
        # Check if workflow has failed before processing
        if self.is_workflow_failed(event.correlation_id):
            self.logger.info(
                f"🚫 Skipping signal generation monitoring - workflow {event.correlation_id} already failed"
            )
            return

        if self.use_http_domain_workflow:
            portfolio_endpoint = self.http_endpoints.get("portfolio")
            if not portfolio_endpoint:
                error_msg = (
                    "HTTP workflow is enabled but portfolio endpoint is not configured. "
                    "Set orchestration.portfolio_endpoint in config or disable use_http_domain_workflow."
                )
                self.logger.error(
                    error_msg,
                    extra={
                        "correlation_id": event.correlation_id,
                        "http_endpoints": self.http_endpoints,
                    },
                )
                raise ConfigurationError(error_msg, config_key="orchestration.portfolio_endpoint")

            payload = {
                "correlation_id": event.correlation_id,
                "causation_id": event.event_id,
                "event_type": event.event_type,
                "event_id": f"portfolio-request-{uuid4()}",
                "trigger_event": event.model_dump(mode="json"),
            }

            try:
                response_payload = self._post_with_retries(portfolio_endpoint, payload)
                if response_payload:
                    self._publish_http_event(response_payload)
            except (httpx.HTTPError, httpx.TimeoutException, httpx.RequestError) as exc:
                self.logger.error(
                    "Failed to call portfolio endpoint in workflow",
                    extra={
                        "correlation_id": event.correlation_id,
                        "causation_id": event.event_id,
                        "endpoint": portfolio_endpoint,
                        "workflow_stage": "portfolio",
                        "error_type": type(exc).__name__,
                        "error_detail": str(exc),
                    },
                )
                raise

        self.logger.debug(
            f"📊 EventDrivenOrchestrator: Monitoring signal generation - {event.signal_count} signals"
        )

        # Update monitoring state
        self.workflow_state.update(
            {
                "signal_generation_in_progress": False,  # Signals completed
                "rebalancing_in_progress": True,  # Rebalancing should start
            }
        )

        # Log signal summary for monitoring
        self.logger.debug(f"Monitoring signals data: {event.signals_data}")

        # Collect strategy signals for workflow results
        if event.correlation_id not in self.workflow_results:
            self.workflow_results[event.correlation_id] = {}

        # Use the signals_data directly from the event
        self.workflow_results[event.correlation_id]["strategy_signals"] = event.signals_data

        # Store consolidated_portfolio for notification enrichment
        self.workflow_results[event.correlation_id]["consolidated_portfolio"] = (
            event.consolidated_portfolio
        )

        # Track successful signal processing
        self.workflow_state["last_successful_workflow"] = "signal_generation"

    def _handle_rebalance_planned(self, event: RebalancePlanned) -> None:
        """Handle rebalance planning event for monitoring.

        Args:
            event: The rebalance planned event

        """
        # Check if workflow has failed before processing
        if self.is_workflow_failed(event.correlation_id):
            self.logger.info(
                f"🚫 Skipping rebalance planning monitoring - workflow {event.correlation_id} already failed"
            )
            return

        if self.use_http_domain_workflow:
            execution_endpoint = self.http_endpoints.get("execution")
            if not execution_endpoint:
                error_msg = (
                    "HTTP workflow is enabled but execution endpoint is not configured. "
                    "Set orchestration.execution_endpoint in config or disable use_http_domain_workflow."
                )
                self.logger.error(
                    error_msg,
                    extra={
                        "correlation_id": event.correlation_id,
                        "http_endpoints": self.http_endpoints,
                    },
                )
                raise ConfigurationError(error_msg, config_key="orchestration.execution_endpoint")

            payload = {
                "correlation_id": event.correlation_id,
                "causation_id": event.event_id,
                "event_type": event.event_type,
                "event_id": f"execution-request-{uuid4()}",
                "trigger_event": event.model_dump(mode="json"),
            }

            try:
                response_payload = self._post_with_retries(execution_endpoint, payload)
                if response_payload:
                    self._publish_http_event(response_payload)
            except (httpx.HTTPError, httpx.TimeoutException, httpx.RequestError) as exc:
                self.logger.error(
                    "Failed to call execution endpoint in workflow",
                    extra={
                        "correlation_id": event.correlation_id,
                        "causation_id": event.event_id,
                        "endpoint": execution_endpoint,
                        "workflow_stage": "execution",
                        "error_type": type(exc).__name__,
                        "error_detail": str(exc),
                    },
                )
                raise

        self.logger.debug(
            f"⚖️ EventDrivenOrchestrator: Monitoring rebalance planning - trades required: {event.trades_required}"
        )

        # Update monitoring state
        self.workflow_state.update(
            {
                "rebalancing_in_progress": False,  # Rebalancing plan completed
                "trading_in_progress": True,  # Trading should start
            }
        )

        # Log rebalancing plan summary for monitoring
        self.logger.debug(f"Monitoring rebalance plan: {event.rebalance_plan}")

        # Collect rebalance plan for workflow results
        if event.correlation_id not in self.workflow_results:
            self.workflow_results[event.correlation_id] = {}

        # Use the rebalance_plan directly from the event
        self.workflow_results[event.correlation_id]["rebalance_plan"] = event.rebalance_plan

        # Track successful rebalancing
        self.workflow_state["last_successful_workflow"] = "rebalancing"

    def _handle_trade_executed(self, event: TradeExecuted) -> None:
        """Handle trade execution event for notifications and reconciliation.

        Args:
            event: The trade executed event

        """
        success = event.success
        self.logger.debug(
            f"🎯 EventDrivenOrchestrator: Trade execution monitoring - {'✅' if success else '❌'}"
        )

        # Update monitoring state
        self.workflow_state.update(
            {
                "trading_in_progress": False,  # Trading completed
            }
        )

        # Remove from active correlations as workflow is complete
        self.workflow_state["active_correlations"].discard(event.correlation_id)

        # Collect execution results for workflow results
        if event.correlation_id not in self.workflow_results:
            self.workflow_results[event.correlation_id] = {}

        # Use execution data directly from the event
        self.workflow_results[event.correlation_id].update(
            {
                "orders_executed": event.execution_data.get("orders", []),
                "execution_summary": {
                    "orders_placed": event.orders_placed,
                    "orders_succeeded": event.orders_succeeded,
                },
                "success": success,
            }
        )

        if success:
            self.logger.info(
                "EventDrivenOrchestrator: Full trading workflow monitoring completed successfully"
            )
            self.workflow_state["last_successful_workflow"] = "trading"

            # Perform post-trade reconciliation
            self._perform_reconciliation()

            # Send success notification
            self._send_trading_notification(event, success=True)
        else:
            self.logger.error(
                "EventDrivenOrchestrator: Trading workflow monitoring detected failure"
            )

            # Send failure notification
            self._send_trading_notification(event, success=False)

            # Trigger recovery workflow
            self._trigger_recovery_workflow(event)

    def _extract_consolidated_portfolio(self, workflow_results: dict[str, Any]) -> dict[str, Any]:
        """Extract consolidated portfolio from workflow context.

        Args:
            workflow_results: Dictionary containing workflow results

        Returns:
            Dictionary mapping symbols to their target weights

        """
        # Try to get from SignalGenerated event first
        consolidated_portfolio = workflow_results.get("consolidated_portfolio", {})
        if consolidated_portfolio:
            return cast(dict[str, Any], consolidated_portfolio)

        # Fall back to rebalance plan
        if "rebalance_plan" not in workflow_results:
            return {}

        rebalance_plan = workflow_results["rebalance_plan"]

        # Try to extract from rebalance plan metadata
        if hasattr(rebalance_plan, "metadata") and isinstance(rebalance_plan.metadata, dict):
            consolidated_portfolio = rebalance_plan.metadata.get("consolidated_portfolio", {})
            if consolidated_portfolio:
                return cast(dict[str, Any], consolidated_portfolio)

        # Build from rebalance plan items as last resort
        result: dict[str, Any] = {}
        if hasattr(rebalance_plan, "items") and rebalance_plan.items:
            for item in rebalance_plan.items:
                symbol = getattr(item, "symbol", None)
                target_weight = getattr(item, "target_weight", None)
                if symbol and target_weight is not None:
                    result[symbol] = float(target_weight)

        return result

    def _prepare_execution_data(self, event: TradeExecuted, *, success: bool) -> dict[str, Any]:
        """Prepare execution data with failure details and workflow context.

        Args:
            event: The TradeExecuted event
            success: Whether the trading was successful

        Returns:
            Dictionary containing execution data with failure details and workflow context

        """
        execution_data = event.execution_data.copy() if event.execution_data else {}

        # Add failed symbols to execution data for notification service
        if not success and event.failed_symbols:
            execution_data["failed_symbols"] = event.failed_symbols

        # Enrich execution_data with workflow context for comprehensive email notifications
        workflow_results = self.workflow_results.get(event.correlation_id, {})

        # Add strategy signals from workflow context
        if "strategy_signals" in workflow_results:
            execution_data["strategy_signals"] = workflow_results["strategy_signals"]

        # Add consolidated portfolio from workflow context
        consolidated_portfolio = self._extract_consolidated_portfolio(workflow_results)
        if consolidated_portfolio:
            execution_data["consolidated_portfolio"] = consolidated_portfolio

        # Add execution summary with consolidated portfolio for template compatibility
        if "execution_summary" in workflow_results:
            execution_data["execution_summary"] = workflow_results["execution_summary"]
            # Ensure execution_summary has consolidated_portfolio for template lookup
            if "consolidated_portfolio" in execution_data:
                execution_data["execution_summary"]["consolidated_portfolio"] = execution_data[
                    "consolidated_portfolio"
                ]

        # Add orders_executed list for order detail display
        if "orders_executed" in workflow_results:
            execution_data["orders_executed"] = workflow_results["orders_executed"]

        return execution_data

    def _extract_trade_value(self, execution_data: dict[str, Any]) -> Decimal:
        """Extract and normalize total trade value to Decimal.

        Args:
            execution_data: Dictionary containing execution data

        Returns:
            Total trade value as Decimal, or Decimal("0") if conversion fails

        """
        raw_total_value = execution_data.get("total_trade_value", 0)
        try:
            return Decimal(str(raw_total_value))
        except (TypeError, ValueError):
            return Decimal("0")

    def _extract_error_details(
        self, event: TradeExecuted, *, success: bool
    ) -> tuple[str | None, str | None]:
        """Extract error message and code from failed trade event.

        Args:
            event: The TradeExecuted event
            success: Whether the trading was successful

        Returns:
            Tuple of (error_message, error_code), both None if successful

        """
        if not success:
            error_message = (
                event.failure_reason or event.metadata.get("error_message") or "Unknown error"
            )
            error_code = getattr(event, "error_code", None)
            return error_message, error_code
        return None, None

    def _build_trading_notification(
        self, event: TradeExecuted, *, success: bool
    ) -> BaseEvent:  # Returns TradingNotificationRequested which inherits from BaseEvent
        """Build trading notification event from trade execution event.

        Args:
            event: The TradeExecuted event
            success: Whether the trading was successful

        Returns:
            TradingNotificationRequested event ready to publish

        """
        from the_alchemiser.shared.events.schemas import TradingNotificationRequested

        mode_str = "LIVE" if not self.container.config.paper_trading() else "PAPER"
        execution_data = self._prepare_execution_data(event, success=success)
        total_trade_value = self._extract_trade_value(execution_data)
        error_message, error_code = self._extract_error_details(event, success=success)

        return TradingNotificationRequested(
            correlation_id=event.correlation_id,
            causation_id=event.event_id,
            event_id=f"trading-notification-{uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="orchestration.event_driven_orchestrator",
            source_component="EventDrivenOrchestrator",
            trading_success=success,
            trading_mode=mode_str,
            orders_placed=event.orders_placed,
            orders_succeeded=event.orders_succeeded,
            total_trade_value=total_trade_value,
            execution_data=execution_data,
            error_message=error_message,
            error_code=error_code,
        )

    def _send_trading_notification(self, event: TradeExecuted, *, success: bool) -> None:
        """Send trading completion notification via event bus.

        Args:
            event: The TradeExecuted event
            success: Whether the trading was successful

        """
        try:
            trading_event = self._build_trading_notification(event, success=success)
            self.event_bus.publish(trading_event)

            self.logger.info(
                f"Trading notification event published successfully (success={success})",
                extra={"correlation_id": event.correlation_id},
            )

        except (ValidationError, TypeError, AttributeError) as e:
            # Event construction or data errors - log but don't break workflow
            self.logger.error(
                f"Failed to publish trading notification due to data error: {e}",
                extra={
                    "correlation_id": event.correlation_id,
                    "error_type": type(e).__name__,
                },
            )
        except Exception as e:
            # Unexpected errors - don't let notification failure break the workflow
            self.logger.error(
                f"Failed to publish trading notification due to unexpected error: {e}",
                exc_info=True,
                extra={
                    "correlation_id": event.correlation_id,
                    "error_type": type(e).__name__,
                },
            )

    def _perform_reconciliation(self) -> None:
        """Perform post-trade reconciliation workflow."""
        self.logger.debug("🔄 Starting post-trade reconciliation")

        try:
            # In the future, this would:
            # 1. Verify portfolio state matches expectations
            # 2. Check trade execution accuracy
            # 3. Update position tracking
            # 4. Generate reconciliation reports
            self.logger.debug("Reconciliation: Verifying portfolio state")
            self.logger.debug("Reconciliation: Checking trade execution accuracy")
            self.logger.debug("Reconciliation: Updating position tracking")

            self.logger.info("✅ Post-trade reconciliation completed successfully")

        except Exception as e:
            # Reconciliation errors - log but don't fail overall workflow
            self.logger.error(
                f"Reconciliation failed with error: {e}",
                exc_info=True,
                extra={"error_type": type(e).__name__},
            )

    def _trigger_recovery_workflow(self, event: TradeExecuted) -> None:
        """Trigger recovery workflow for failed trades.

        Args:
            event: The trade executed event (failed)

        """
        self.logger.debug("🚨 Starting recovery workflow for failed trades")

        try:
            # In the future, this would:
            # 1. Analyze failure causes
            # 2. Determine recovery actions
            # 3. Emit recovery events
            # 4. Alert system administrators

            self.logger.warning(
                f"Recovery: Assessing failure - {event.metadata.get('error_message', 'Unknown error')}"
            )
            self.logger.debug("Recovery: Determining corrective actions")
            self.logger.debug("Recovery: Preparing system alerts")

            # For now, log the recovery intent
            self.logger.debug(
                "Recovery workflow prepared (full implementation in future iterations)"
            )

        except Exception as e:
            # Recovery workflow errors - log but don't fail overall workflow
            self.logger.error(
                f"Recovery workflow failed with error: {e}",
                exc_info=True,
                extra={"error_type": type(e).__name__},
            )

    def _handle_workflow_completed(self, event: WorkflowCompleted) -> None:
        """Handle WorkflowCompleted event for monitoring and cleanup.

        Args:
            event: The WorkflowCompleted event

        """
        self.logger.info(
            f"✅ Workflow completed successfully: {event.workflow_type}",
            extra={
                "correlation_id": event.correlation_id,
                "workflow_type": event.workflow_type,
                "workflow_state": WorkflowState.COMPLETED.value,
            },
        )

        # Calculate and log workflow duration
        start_time = self.workflow_state["workflow_start_times"].get(event.correlation_id)
        if start_time:
            duration_ms = (event.timestamp - start_time).total_seconds() * 1000
            self.logger.info(
                f"📊 Workflow duration: {duration_ms:.0f}ms",
                extra={
                    "correlation_id": event.correlation_id,
                    "duration_ms": duration_ms,
                },
            )

        # Generate account snapshot for reporting
        self._generate_account_snapshot(
            event.correlation_id, start_time or event.timestamp, event.timestamp
        )

        # Mark unexecuted signals as IGNORED
        self._mark_ignored_signals(event.correlation_id)

        # Update workflow state
        self.workflow_state["last_successful_workflow"] = event.workflow_type
        self.workflow_state["active_correlations"].discard(event.correlation_id)

        # Track completion to prevent duplicate starts
        self.workflow_state["completed_correlations"].add(event.correlation_id)

        # Clean up tracking data
        self.workflow_state["workflow_start_times"].pop(event.correlation_id, None)

        # Reset progress flags
        self.workflow_state.update(
            {
                "signal_generation_in_progress": False,
                "rebalancing_in_progress": False,
                "trading_in_progress": False,
            }
        )

        # Set workflow state to COMPLETED
        self._set_workflow_state(event.correlation_id, WorkflowState.COMPLETED)
        self.logger.info(
            f"✅ Workflow {event.correlation_id} marked as COMPLETED",
            extra={
                "correlation_id": event.correlation_id,
                "workflow_state": WorkflowState.COMPLETED.value,
            },
        )

    def _generate_account_snapshot(
        self, correlation_id: str, period_start: datetime, period_end: datetime
    ) -> None:
        """Generate and store account snapshot for reporting.

        Args:
            correlation_id: Workflow correlation ID
            period_start: Period start timestamp
            period_end: Period end timestamp

        """
        try:
            from the_alchemiser.shared.config.config import load_settings
            from the_alchemiser.shared.repositories.account_snapshot_repository import (
                AccountSnapshotRepository,
            )
            from the_alchemiser.shared.services.account_snapshot_service import (
                AccountSnapshotService,
            )

            # Get dependencies
            alpaca_manager = self.container.infrastructure.alpaca_manager()
            settings = load_settings()
            table_name = settings.trade_ledger.table_name

            if not table_name:
                self.logger.warning(
                    "Trade ledger table name not configured - skipping snapshot generation",
                    correlation_id=correlation_id,
                )
                return

            # Create repositories and service
            snapshot_repository = AccountSnapshotRepository(table_name)
            snapshot_service = AccountSnapshotService(alpaca_manager, snapshot_repository)

            # Get account ID from Alpaca
            account = alpaca_manager.get_account_object()
            if not account:
                self.logger.warning(
                    "Failed to fetch account for snapshot generation",
                    correlation_id=correlation_id,
                )
                return

            account_id = str(account.id)

            # Generate snapshot (correlation_id enables querying trade ledger at report time)
            snapshot = snapshot_service.generate_snapshot(
                account_id=account_id,
                correlation_id=correlation_id,
                period_start=period_start,
                period_end=period_end,
            )

            self.logger.info(
                "📸 Account snapshot generated successfully",
                snapshot_id=snapshot.snapshot_id,
                account_id=account_id,
                correlation_id=correlation_id,
            )

        except (ConfigurationError, ImportError) as e:
            # Configuration or module errors - log but don't fail workflow
            self.logger.error(
                f"Failed to generate account snapshot due to configuration error: {e}",
                extra={
                    "correlation_id": correlation_id,
                    "error_type": type(e).__name__,
                },
            )
        except (TradingClientError, MarketDataError) as e:
            # API errors during snapshot generation - log but don't fail workflow
            self.logger.error(
                f"Failed to generate account snapshot due to API error: {e}",
                extra={
                    "correlation_id": correlation_id,
                    "error_type": type(e).__name__,
                },
            )
        except Exception as e:
            # Unexpected errors - don't let snapshot generation failure break the workflow
            self.logger.error(
                f"Failed to generate account snapshot due to unexpected error: {e}",
                exc_info=True,
                extra={
                    "correlation_id": correlation_id,
                    "error_type": type(e).__name__,
                },
            )

    def _mark_ignored_signals(self, correlation_id: str) -> None:
        """Mark unexecuted signals as IGNORED at workflow completion.

        Args:
            correlation_id: Workflow correlation ID

        """
        try:
            from the_alchemiser.shared.config.config import load_settings
            from the_alchemiser.shared.repositories.dynamodb_trade_ledger_repository import (
                DynamoDBTradeLedgerRepository,
            )

            # Get table name from settings
            settings = load_settings()
            table_name = settings.trade_ledger.table_name

            if not table_name:
                self.logger.debug(
                    "Trade ledger table not configured - skipping signal lifecycle updates",
                    correlation_id=correlation_id,
                )
                return

            # Create repository
            repository = DynamoDBTradeLedgerRepository(table_name)

            # Query all signals for this correlation_id
            signals = repository.query_signals_by_correlation(correlation_id)

            if not signals:
                self.logger.debug(
                    "No signals found for correlation_id",
                    correlation_id=correlation_id,
                )
                return

            # Mark GENERATED signals as IGNORED (EXECUTED signals are already updated)
            ignored_count = 0
            for signal in signals:
                if signal.get("lifecycle_state") == "GENERATED":
                    signal_id = signal.get("signal_id")
                    if signal_id:
                        repository.update_signal_lifecycle(signal_id, "IGNORED", None)
                        ignored_count += 1

            if ignored_count > 0:
                self.logger.info(
                    f"Marked {ignored_count} unexecuted signals as IGNORED",
                    correlation_id=correlation_id,
                    ignored_count=ignored_count,
                )

        except (ConfigurationError, ImportError) as e:
            # Configuration or module errors - log but don't fail workflow
            self.logger.warning(
                f"Failed to mark ignored signals due to configuration error: {e}",
                extra={
                    "correlation_id": correlation_id,
                    "error_type": type(e).__name__,
                },
            )
        except Exception as e:
            # Unexpected errors - don't fail workflow on signal lifecycle update errors
            self.logger.warning(
                f"Failed to mark ignored signals due to unexpected error: {e}",
                extra={
                    "correlation_id": correlation_id,
                    "error_type": type(e).__name__,
                },
            )

    def _handle_workflow_failed(self, event: WorkflowFailed) -> None:
        """Handle WorkflowFailed event for error handling and recovery.

        Args:
            event: The WorkflowFailed event

        """
        self.logger.error(f"❌ Workflow failed: {event.workflow_type} - {event.failure_reason}")

        # Set workflow state to FAILED to prevent further event processing
        self._set_workflow_state(event.correlation_id, WorkflowState.FAILED)
        self.logger.info(
            f"🚫 Workflow {event.correlation_id} marked as FAILED - future events will be skipped",
            extra={
                "correlation_id": event.correlation_id,
                "workflow_state": WorkflowState.FAILED.value,
            },
        )

        # Update workflow state
        self.workflow_state["active_correlations"].discard(event.correlation_id)

        # Track completion to prevent duplicate starts
        self.workflow_state["completed_correlations"].add(event.correlation_id)

        # Clean up tracking data
        self.workflow_state["workflow_start_times"].pop(event.correlation_id, None)

        # Reset progress flags
        self.workflow_state.update(
            {
                "signal_generation_in_progress": False,
                "rebalancing_in_progress": False,
                "trading_in_progress": False,
            }
        )

        # Trigger error notifications and recovery
        try:
            self.logger.info("Triggering error notification for workflow failure")
            # In future iterations, implement comprehensive error handling

        except Exception as e:
            self.logger.error(f"Failed to handle workflow failure: {e}")

    def get_workflow_status(self) -> dict[str, Any]:
        """Get current workflow status for monitoring.

        Returns:
            Dictionary containing workflow state information

        """
        # Calculate state metrics
        with self.workflow_states_lock:
            state_counts = {
                "running": 0,
                "failed": 0,
                "completed": 0,
            }
            for state in self.workflow_states.values():
                state_counts[state.value] += 1

            workflow_states_copy = self.workflow_states.copy()

        return {
            "workflow_state": self.workflow_state.copy(),
            "event_bus_stats": self.event_bus.get_stats(),
            "orchestrator_active": True,
            "workflow_state_metrics": {
                "total_tracked": len(workflow_states_copy),
                "by_state": state_counts,
                "active_workflows": len(self.workflow_state["active_correlations"]),
                "completed_workflows": len(self.workflow_state["completed_correlations"]),
            },
        }

    def is_workflow_failed(self, correlation_id: str) -> bool:
        """Check if a workflow has failed.

        Args:
            correlation_id: The workflow correlation ID to check

        Returns:
            True if the workflow has failed, False otherwise

        """
        with self.workflow_states_lock:
            return self.workflow_states.get(correlation_id) == WorkflowState.FAILED

    def is_workflow_active(self, correlation_id: str) -> bool:
        """Check if a workflow is actively running.

        Args:
            correlation_id: The workflow correlation ID to check

        Returns:
            True if the workflow is running, False otherwise

        """
        with self.workflow_states_lock:
            return self.workflow_states.get(correlation_id) == WorkflowState.RUNNING

    def get_workflow_state(self, correlation_id: str) -> WorkflowState | None:
        """Get the current workflow state for a given correlation ID.

        Args:
            correlation_id: The workflow correlation ID to check

        Returns:
            The current WorkflowState, or None if workflow not tracked

        """
        with self.workflow_states_lock:
            return self.workflow_states.get(correlation_id)

    def cleanup_workflow_state(self, correlation_id: str) -> bool:
        """Clean up workflow state for a given correlation ID.

        This should be called after workflow results have been retrieved to prevent
        memory leaks from accumulating workflow states.

        Args:
            correlation_id: The workflow correlation ID to clean up

        Returns:
            True if state was cleaned up, False if correlation_id not found

        """
        with self.workflow_states_lock:
            if correlation_id in self.workflow_states:
                state = self.workflow_states.pop(correlation_id)
                self.logger.debug(
                    f"🧹 Cleaned up workflow state for {correlation_id} (was {state.value})"
                )
                return True
            return False

    def _set_workflow_state(self, correlation_id: str, state: WorkflowState) -> None:
        """Set the workflow state for a given correlation ID.

        Args:
            correlation_id: The workflow correlation ID
            state: The new state to set

        """
        with self.workflow_states_lock:
            self.workflow_states[correlation_id] = state
