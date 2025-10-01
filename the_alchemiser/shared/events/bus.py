#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Event bus implementation for event-driven architecture.

Provides in-memory pub/sub event bus for inter-module communication.
Designed to be extensible to external message brokers (Kafka, RabbitMQ) if needed.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Protocol

from ..logging.logging_utils import get_logger
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
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._global_handlers: list[EventHandler] = []
        self._event_count = 0
        self._workflow_state_checker: WorkflowStateChecker | None = None  # Reference to orchestrator for workflow state checking

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe a handler to a specific event type.

        Args:
            event_type: The type of events to subscribe to
            handler: The handler to receive events

        Raises:
            ValueError: If event_type is empty or handler is invalid

        """
        if not event_type or not event_type.strip():
            raise ValueError("Event type cannot be empty")

        if not isinstance(handler, EventHandler):
            raise ValueError("Handler must implement EventHandler protocol")

        self._handlers[event_type].append(handler)
        self.logger.debug(f"Subscribed handler to event type: {event_type}")

    def subscribe_global(self, handler: EventHandler) -> None:
        """Subscribe a handler to all events.

        Args:
            handler: The handler to receive all events

        Raises:
            ValueError: If handler is invalid

        """
        if not isinstance(handler, EventHandler):
            raise ValueError("Handler must implement EventHandler protocol")

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
        handlers_to_notify = []

        # Add specific handlers for this event type
        if event_type in self._handlers:
            handlers_to_notify.extend(self._handlers[event_type])

        # Add global handlers
        handlers_to_notify.extend(self._global_handlers)

        # Notify all handlers
        successful_deliveries = 0
        failed_deliveries = 0

        for handler in handlers_to_notify:
            try:
                # Check if handler can handle this event type
                if hasattr(handler, "can_handle") and not handler.can_handle(event_type):
                    continue

                handler.handle_event(event)
                successful_deliveries += 1

            except Exception as e:
                failed_deliveries += 1
                self.logger.error(
                    f"Handler {type(handler).__name__} failed to process event "
                    f"{event.event_id}: {e}",
                    extra={
                        "event_id": event.event_id,
                        "event_type": event_type,
                        "handler": type(handler).__name__,
                        "correlation_id": event.correlation_id,
                    },
                )

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

    def get_stats(self) -> dict[str, Any]:
        """Get event bus statistics.

        Returns:
            Dictionary containing bus statistics

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
            self.logger.debug(f"🔍 No workflow state checker available for {correlation_id}")
            return False

        result = self._workflow_state_checker.is_workflow_failed(correlation_id)
        self.logger.debug(f"🔍 Workflow state check result: {correlation_id} -> failed={result}")
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
