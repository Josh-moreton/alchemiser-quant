#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Event bus implementation for event-driven architecture.

Provides in-memory pub/sub event bus for inter-module communication.
Designed to be extensible to external message brokers (Kafka, RabbitMQ) if needed.

Thread Safety:
    This EventBus implementation is designed for single-threaded usage in AWS Lambda
    environments. It does not provide thread-safety guarantees for concurrent access.
    If using in a multi-threaded context, external synchronization is required.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from inspect import signature
from typing import Protocol

from ..errors import EventBusError, HandlerInvocationError
from ..logging import get_logger
from .base import BaseEvent
from .handlers import EventHandler

# Type alias for handler types to improve readability
HandlerType = EventHandler | Callable[[BaseEvent], None]


class WorkflowStateChecker(Protocol):
    """Protocol for workflow state checking."""

    def is_workflow_failed(self, correlation_id: str) -> bool:
        """Check if a workflow has failed."""
        ...

    def is_workflow_active(self, correlation_id: str) -> bool:
        """Check if a workflow is active."""
        ...


class EventBus:
    """In-memory event bus for pub/sub messaging.

    Provides event publishing and subscription capabilities with handler registration
    and event routing based on event types.
    
    Thread Safety:
        This implementation is NOT thread-safe. Designed for single-threaded usage
        (e.g., AWS Lambda). If using in multi-threaded contexts, external 
        synchronization is required.
    
    Error Handling:
        Handler exceptions are caught, logged, and wrapped in HandlerInvocationError.
        One handler failure does not prevent other handlers from receiving events.
        Subscription validation errors (empty event type, invalid handler) raise
        ValueError immediately.
    """

    def __init__(
        self, workflow_state_checker: WorkflowStateChecker | None = None
    ) -> None:
        """Initialize the event bus.
        
        Args:
            workflow_state_checker: Optional workflow state checker for integration
                with orchestrator. Can also be set later via set_workflow_state_checker.
        
        """
        self.logger = get_logger(__name__)
        self._handlers: dict[str, list[HandlerType]] = defaultdict(list)
        self._global_handlers: list[HandlerType] = []
        self._event_count = 0
        self._workflow_state_checker: WorkflowStateChecker | None = workflow_state_checker

    def subscribe(
        self, event_type: str, handler: HandlerType
    ) -> None:
        """Subscribe a handler to a specific event type.

        Args:
            event_type: The type of events to subscribe to
            handler: The handler to receive events (EventHandler or callable accepting BaseEvent)

        Raises:
            ValueError: If event_type is empty or handler is invalid
            EventBusError: If handler signature validation fails

        """
        if not event_type or not event_type.strip():
            raise ValueError("Event type cannot be empty")

        # Accept either an EventHandler implementation or a plain callable(event)
        if not (isinstance(handler, EventHandler) or callable(handler)):
            raise ValueError("Handler must implement EventHandler protocol or be a callable(event)")
        
        # Validate callable signature if it's a plain callable
        if callable(handler) and not isinstance(handler, EventHandler):
            self._validate_callable_signature(handler)

        self._handlers[event_type].append(handler)
        self.logger.debug(
            f"Subscribed handler to event type: {event_type}",
            extra={
                "event_type": event_type,
                "handler": type(handler).__name__,
            },
        )

    def subscribe_global(self, handler: HandlerType) -> None:
        """Subscribe a handler to all events.

        Args:
            handler: The handler to receive all events

        Raises:
            ValueError: If handler is invalid
            EventBusError: If handler signature validation fails

        """
        if not (isinstance(handler, EventHandler) or callable(handler)):
            raise ValueError("Handler must implement EventHandler protocol or be a callable(event)")
        
        # Validate callable signature if it's a plain callable
        if callable(handler) and not isinstance(handler, EventHandler):
            self._validate_callable_signature(handler)

        self._global_handlers.append(handler)
        self.logger.debug(
            "Subscribed global event handler",
            extra={"handler": type(handler).__name__},
        )

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Unsubscribe a handler from a specific event type.

        Args:
            event_type: The type of events to unsubscribe from
            handler: The handler to remove

        """
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                self.logger.debug(
                    f"Unsubscribed handler from event type: {event_type}",
                    extra={
                        "event_type": event_type,
                        "handler": type(handler).__name__,
                    },
                )
            except ValueError:
                self.logger.warning(
                    f"Handler not found for event type: {event_type}",
                    extra={
                        "event_type": event_type,
                        "handler": type(handler).__name__,
                    },
                )

    def unsubscribe_global(self, handler: EventHandler) -> None:
        """Unsubscribe a global handler.

        Args:
            handler: The handler to remove

        """
        try:
            self._global_handlers.remove(handler)
            self.logger.debug(
                "Unsubscribed global event handler",
                extra={"handler": type(handler).__name__},
            )
        except ValueError:
            self.logger.warning(
                "Global handler not found",
                extra={"handler": type(handler).__name__},
            )

    def _collect_handlers(
        self, event_type: str
    ) -> list[HandlerType]:
        """Collect all handlers that should receive an event.

        Args:
            event_type: The type of event being published

        Returns:
            List of handlers to notify

        """
        handlers_to_notify: list[HandlerType] = []

        # Add specific handlers for this event type
        if event_type in self._handlers:
            handlers_to_notify.extend(self._handlers[event_type])

        # Add global handlers
        handlers_to_notify.extend(self._global_handlers)

        return handlers_to_notify

    def _invoke_handler(
        self, handler: HandlerType, event: BaseEvent
    ) -> tuple[bool, bool]:
        """Invoke a single handler with an event.

        Args:
            handler: The handler to invoke
            event: The event to pass to the handler

        Returns:
            Tuple of (was_invoked, had_error) where:
            - was_invoked: True if handler was called, False if skipped (e.g., can_handle=False)
            - had_error: True if handler raised an exception, False otherwise
        
        Raises:
            HandlerInvocationError: Wraps any exception from handler execution

        """
        event_type = event.event_type

        try:
            if isinstance(handler, EventHandler):
                # Check if this handler wants this event type
                if not self._can_handle_event(handler, event_type):
                    return (False, False)  # Skipped, no error

                # Delegate to handler implementation with robust calling
                self._safe_call_method(handler, "handle_event", event)
            elif callable(handler):
                # Plain callable passed directly to subscribe
                handler(event)
            else:
                # Unknown handler type
                raise TypeError("Unsupported handler type")
            return (True, False)  # Successfully invoked, no error

        except Exception as e:
            # Wrap in typed error and log, but don't propagate to avoid stopping other handlers
            handler_error = HandlerInvocationError(
                message=f"Handler {type(handler).__name__} failed to process event {event.event_id}",
                event_type=event_type,
                handler_name=type(handler).__name__,
                correlation_id=event.correlation_id,
                original_error=e,
            )
            self._log_handler_failure(handler, event, handler_error)
            return (True, True)  # Was invoked but had error

    def _can_handle_event(self, handler: EventHandler, event_type: str) -> bool:
        """Check if handler can handle an event type.

        Args:
            handler: The handler to check
            event_type: The event type to check

        Returns:
            True if handler can handle the event, False otherwise
        
        Raises:
            HandlerInvocationError: If can_handle raises an unexpected exception

        """
        try:
            # Some dynamically-created handlers may define can_handle without 'self';
            # use a robust invocation that works for both styles.
            return bool(
                self._safe_call_method(handler, "can_handle", event_type)
            )  # pragma: no cover - structural
        except Exception as exc:
            # Wrap in typed error and log warning, but proceed to handle
            # (some handlers may have buggy can_handle but working handle_event)
            handler_error = HandlerInvocationError(
                message=f"Handler {type(handler).__name__} can_handle() raised exception for event type {event_type}",
                event_type=event_type,
                handler_name=type(handler).__name__,
                original_error=exc,
            )
            self.logger.warning(
                "can_handle() raised exception; proceeding to handle",
                extra={
                    "event_type": event_type,
                    "handler": type(handler).__name__,
                    "error": str(exc),
                    "error_type": type(exc).__name__,
                },
            )
            return True  # Assume can handle if can_handle fails

    def _log_handler_failure(
        self,
        handler: HandlerType,
        event: BaseEvent,
        error: Exception,
    ) -> None:
        """Log handler failure with comprehensive context.

        Args:
            handler: The handler that failed
            event: The event that was being processed
            error: The exception that was raised (may be HandlerInvocationError wrapping original)

        """
        self.logger.error(
            f"Handler {type(handler).__name__} failed to process event {event.event_id}: {error}",
            extra={
                "event_id": event.event_id,
                "event_type": event.event_type,
                "handler": type(handler).__name__,
                "correlation_id": event.correlation_id,
                "causation_id": event.causation_id,
                "error_type": type(error).__name__,
            },
        )

    def publish(self, event: BaseEvent) -> None:
        """Publish an event to all relevant handlers.
        
        Handler exceptions are caught, logged, and do not prevent other handlers
        from receiving the event. Each handler failure is wrapped in 
        HandlerInvocationError for proper error tracking.

        Args:
            event: The event to publish

        Raises:
            ValueError: If event is invalid (not a BaseEvent instance)

        """
        if not isinstance(event, BaseEvent):
            raise ValueError("Event must be a BaseEvent instance")

        self._event_count += 1
        event_type = event.event_type

        self.logger.debug(
            f"Publishing event {event.event_id} of type {event_type} from {event.source_module}",
            extra={
                "event_id": event.event_id,
                "event_type": event_type,
                "source_module": event.source_module,
                "correlation_id": event.correlation_id,
                "causation_id": event.causation_id,
            },
        )

        # Collect all handlers for this event type
        handlers_to_notify = self._collect_handlers(event_type)

        # Notify all handlers
        successful_deliveries = 0
        failed_deliveries = 0

        for handler in handlers_to_notify:
            was_invoked, had_error = self._invoke_handler(handler, event)
            if was_invoked:
                if had_error:
                    failed_deliveries += 1
                else:
                    successful_deliveries += 1

        self.logger.debug(
            f"Event {event.event_id} delivered to {successful_deliveries} handlers, "
            f"{failed_deliveries} failures",
            extra={
                "event_id": event.event_id,
                "event_type": event_type,
                "correlation_id": event.correlation_id,
                "successful_deliveries": successful_deliveries,
                "failed_deliveries": failed_deliveries,
            },
        )

    def get_handler_count(self, event_type: str | None = None) -> int:
        """Get the number of handlers for an event type.

        Args:
            event_type: The event type to check, or None for total handlers

        Returns:
            Number of handlers

        """
        if event_type is None:
            # Return total handlers across all types plus global handlers
            total = len(self._global_handlers)
            for handlers in self._handlers.values():
                total += len(handlers)
            return total
        return len(self._handlers.get(event_type, []))

    def get_event_count(self) -> int:
        """Get the total number of events published through this bus.

        Returns:
            Total number of events published

        """
        return self._event_count

    def clear_handlers(self) -> None:
        """Clear all handlers from the event bus.

        This is primarily for testing purposes.
        """
        self._handlers.clear()
        self._global_handlers.clear()
        self.logger.debug("Cleared all event handlers")

    def get_stats(self) -> dict[str, int | list[str] | dict[str, int]]:
        """Get event bus statistics.
        
        Returns a point-in-time snapshot of current statistics. Stats are
        returned as copies, not live references.

        Returns:
            Dictionary containing bus statistics:
            - total_events_published: Total number of events published
            - event_types_registered: List of registered event types
            - handlers_by_type: Handler count per event type
            - global_handlers: Number of global handlers
            - total_handlers: Total handler count

        """
        return {
            "total_events_published": self._event_count,
            "event_types_registered": list(self._handlers.keys()),
            "handlers_by_type": {
                event_type: len(handlers) for event_type, handlers in self._handlers.items()
            },
            "global_handlers": len(self._global_handlers),
            "total_handlers": self.get_handler_count(),
        }

    def set_workflow_state_checker(self, state_checker: WorkflowStateChecker | None) -> None:
        """Set the workflow state checker (orchestrator).
        
        Note: This setter exists for backward compatibility with code that constructs
        EventBus without the state checker and sets it later. Consider using 
        constructor injection via __init__ for new code.

        Args:
            state_checker: Object that provides workflow state checking methods

        """
        self._workflow_state_checker = state_checker
        self.logger.debug(
            "Set workflow state checker on event bus",
            extra={"has_state_checker": state_checker is not None},
        )

    def is_workflow_failed(self, correlation_id: str) -> bool:
        """Check if a workflow has failed.

        Args:
            correlation_id: The workflow correlation ID to check

        Returns:
            True if the workflow has failed, False if active or if no state checker available

        """
        if self._workflow_state_checker is None:
            self.logger.debug(
                f"No workflow state checker available for {correlation_id}",
                extra={"correlation_id": correlation_id},
            )
            return False

        result = self._workflow_state_checker.is_workflow_failed(correlation_id)
        self.logger.debug(
            f"Workflow state check result: {correlation_id} -> failed={result}",
            extra={"correlation_id": correlation_id, "failed": result},
        )
        return result

    def is_workflow_active(self, correlation_id: str) -> bool:
        """Check if a workflow is actively running.

        Args:
            correlation_id: The workflow correlation ID to check

        Returns:
            True if the workflow is running, False if failed/completed or if no state checker available

        """
        if self._workflow_state_checker is None:
            return True  # Assume active if no state checker

        return self._workflow_state_checker.is_workflow_active(correlation_id)

    # --- Internal utilities -------------------------------------------------

    def _safe_call_method(
        self, obj: object, method_name: str, *args: object, **kwargs: object
    ) -> object:
        """Safely call a method on an object, tolerating missing 'self' in signature.

        Some test handlers are created dynamically with methods defined as functions
        that only accept the domain argument (e.g., event) and not 'self'. When these
        are attached to a class, Python will bind them and implicitly pass 'self',
        which leads to a "takes 1 positional argument but 2 were given" TypeError.

        This helper first tries a normal bound call. If that fails with a TypeError,
        it attempts to call the underlying function (method.__func__) with the same
        arguments, which omits 'self'. If both fail, the original error is raised.

        Args:
            obj: The object containing the method.
            method_name: The method name to invoke.
            *args: Positional arguments for the call.
            **kwargs: Keyword arguments for the call.

        Returns:
            The return value of the method call.

        Raises:
            AttributeError: If the method does not exist on the object.
            Exception: Propagates any exception from the underlying call if retries fail.

        """
        method = getattr(obj, method_name, None)
        if method is None:
            raise AttributeError(f"Object {type(obj).__name__} has no attribute '{method_name}'")

        # First attempt: normal bound call
        try:
            return method(*args, **kwargs)
        except TypeError as e:
            # Inspect the underlying function if available and retry without 'self'
            underlying = getattr(method, "__func__", None)
            if underlying is not None:
                try:
                    # Heuristic: If the underlying function has fewer positional parameters
                    # than the bound method would expect (i.e., defined without 'self'),
                    # call it directly with provided args to avoid implicit 'self'.
                    sig = signature(underlying)
                    params = [
                        p
                        for p in sig.parameters.values()
                        if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
                        and p.default is p.empty
                    ]
                    if len(params) <= len(args):
                        return underlying(*args, **kwargs)
                except Exception as exc:
                    # Log and fall through to re-raise original TypeError
                    self.logger.debug(
                        "Fallback to underlying function failed",
                        extra={
                            "method": method_name,
                            "object": type(obj).__name__,
                            "error": str(exc),
                        },
                    )
            # Re-raise the original error if we can't safely recover
            raise e

    def _validate_callable_signature(self, handler: Callable[[BaseEvent], None]) -> None:
        """Validate that a callable has the correct signature to handle events.
        
        Args:
            handler: The callable to validate
        
        Raises:
            EventBusError: If signature validation fails
        
        """
        try:
            sig = signature(handler)
            params = list(sig.parameters.values())
            
            # Should have exactly one parameter (the event)
            if len(params) != 1:
                raise EventBusError(
                    f"Handler callable must accept exactly 1 parameter (event), "
                    f"but {handler.__name__ if hasattr(handler, '__name__') else 'callable'} "
                    f"has {len(params)} parameters",
                    handler_name=getattr(handler, '__name__', 'callable'),
                )
        except (ValueError, TypeError) as e:
            # If we can't inspect signature, log warning but allow it
            # (some built-in or compiled functions can't be inspected)
            self.logger.warning(
                f"Could not validate callable signature: {e}",
                extra={
                    "handler": getattr(handler, '__name__', 'callable'),
                    "error": str(e),
                },
            )
