#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Event bus implementation for event-driven architecture.

Provides in-memory pub/sub event bus for inter-module communication.
Designed to be extensible to external message brokers (Kafka, RabbitMQ) if needed.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from inspect import signature
from typing import Protocol

from ..logging import get_logger
from .base import BaseEvent
from .handlers import EventHandler


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
    """

    def __init__(self) -> None:
        """Initialize the event bus."""
        self.logger = get_logger(__name__)
        self._handlers: dict[str, list[EventHandler | Callable[[BaseEvent], None]]] = (
            defaultdict(list)
        )
        self._global_handlers: list[EventHandler | Callable[[BaseEvent], None]] = []
        self._event_count = 0
        self._workflow_state_checker: WorkflowStateChecker | None = (
            None  # Reference to orchestrator for workflow state checking
        )

    def subscribe(
        self, event_type: str, handler: EventHandler | Callable[[BaseEvent], None]
    ) -> None:
        """Subscribe a handler to a specific event type.

        Args:
            event_type: The type of events to subscribe to
            handler: The handler to receive events

        Raises:
            ValueError: If event_type is empty or handler is invalid

        """
        if not event_type or not event_type.strip():
            raise ValueError("Event type cannot be empty")

        # Accept either an EventHandler implementation or a plain callable(event)
        if not (isinstance(handler, EventHandler) or callable(handler)):
            raise ValueError(
                "Handler must implement EventHandler protocol or be a callable(event)"
            )

        self._handlers[event_type].append(handler)
        self.logger.debug(f"Subscribed handler to event type: {event_type}")

    def subscribe_global(
        self, handler: EventHandler | Callable[[BaseEvent], None]
    ) -> None:
        """Subscribe a handler to all events.

        Args:
            handler: The handler to receive all events

        Raises:
            ValueError: If handler is invalid

        """
        if not (isinstance(handler, EventHandler) or callable(handler)):
            raise ValueError(
                "Handler must implement EventHandler protocol or be a callable(event)"
            )

        self._global_handlers.append(handler)
        self.logger.debug("Subscribed global event handler")

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Unsubscribe a handler from a specific event type.

        Args:
            event_type: The type of events to unsubscribe from
            handler: The handler to remove

        """
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                self.logger.debug(f"Unsubscribed handler from event type: {event_type}")
            except ValueError:
                self.logger.warning(f"Handler not found for event type: {event_type}")

    def unsubscribe_global(self, handler: EventHandler) -> None:
        """Unsubscribe a global handler.

        Args:
            handler: The handler to remove

        """
        try:
            self._global_handlers.remove(handler)
            self.logger.debug("Unsubscribed global event handler")
        except ValueError:
            self.logger.warning("Global handler not found")

    def _collect_handlers(
        self, event_type: str
    ) -> list[EventHandler | Callable[[BaseEvent], None]]:
        """Collect all handlers that should receive an event.

        Args:
            event_type: The type of event being published

        Returns:
            List of handlers to notify

        """
        handlers_to_notify: list[EventHandler | Callable[[BaseEvent], None]] = []

        # Add specific handlers for this event type
        if event_type in self._handlers:
            handlers_to_notify.extend(self._handlers[event_type])

        # Add global handlers
        handlers_to_notify.extend(self._global_handlers)

        return handlers_to_notify

    def _invoke_handler(
        self, handler: EventHandler | Callable[[BaseEvent], None], event: BaseEvent
    ) -> tuple[bool, bool]:
        """Invoke a single handler with an event.

        Args:
            handler: The handler to invoke
            event: The event to pass to the handler

        Returns:
            Tuple of (was_invoked, had_error) where:
            - was_invoked: True if handler was called, False if skipped (e.g., can_handle=False)
            - had_error: True if handler raised an exception, False otherwise

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
            self._log_handler_failure(handler, event, e)
            return (True, True)  # Was invoked but had error

    def _can_handle_event(self, handler: EventHandler, event_type: str) -> bool:
        """Check if handler can handle an event type.

        Args:
            handler: The handler to check
            event_type: The event type to check

        Returns:
            True if handler can handle the event, False otherwise

        """
        try:
            # Some dynamically-created handlers may define can_handle without 'self';
            # use a robust invocation that works for both styles.
            return bool(
                self._safe_call_method(handler, "can_handle", event_type)
            )  # pragma: no cover - structural
        except Exception as exc:
            # If can_handle raises, proceed but log
            self.logger.warning(
                "can_handle() raised exception; proceeding to handle",
                extra={
                    "event_type": event_type,
                    "handler": type(handler).__name__,
                    "error": str(exc),
                },
            )
            return True

    def _log_handler_failure(
        self,
        handler: EventHandler | Callable[[BaseEvent], None],
        event: BaseEvent,
        error: Exception,
    ) -> None:
        """Log handler failure.

        Args:
            handler: The handler that failed
            event: The event that was being processed
            error: The exception that was raised

        """
        self.logger.error(
            f"Handler {type(handler).__name__} failed to process event {event.event_id}: {error}",
            extra={
                "event_id": event.event_id,
                "event_type": event.event_type,
                "handler": type(handler).__name__,
                "correlation_id": event.correlation_id,
            },
        )

    def publish(self, event: BaseEvent) -> None:
        """Publish an event to all relevant handlers.

        Args:
            event: The event to publish

        Raises:
            ValueError: If event is invalid

        """
        if not isinstance(event, BaseEvent):
            raise ValueError("Event must be a BaseEvent instance")

        self._event_count += 1
        event_type = event.event_type

        self.logger.debug(
            f"Publishing event {event.event_id} of type {event_type} from {event.source_module}"
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
            f"{failed_deliveries} failures"
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

        Returns:
            Dictionary containing bus statistics

        """
        return {
            "total_events_published": self._event_count,
            "event_types_registered": list(self._handlers.keys()),
            "handlers_by_type": {
                event_type: len(handlers)
                for event_type, handlers in self._handlers.items()
            },
            "global_handlers": len(self._global_handlers),
            "total_handlers": self.get_handler_count(),
        }

    def set_workflow_state_checker(
        self, state_checker: WorkflowStateChecker | None
    ) -> None:
        """Set the workflow state checker (orchestrator).

        Args:
            state_checker: Object that provides workflow state checking methods

        """
        self._workflow_state_checker = state_checker
        self.logger.debug("Set workflow state checker on event bus")

    def is_workflow_failed(self, correlation_id: str) -> bool:
        """Check if a workflow has failed.

        Args:
            correlation_id: The workflow correlation ID to check

        Returns:
            True if the workflow has failed, False if active or if no state checker available

        """
        if self._workflow_state_checker is None:
            self.logger.debug(
                f"🔍 No workflow state checker available for {correlation_id}"
            )
            return False

        result = self._workflow_state_checker.is_workflow_failed(correlation_id)
        self.logger.debug(
            f"🔍 Workflow state check result: {correlation_id} -> failed={result}"
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
            raise AttributeError(
                f"Object {type(obj).__name__} has no attribute '{method_name}'"
            )

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
