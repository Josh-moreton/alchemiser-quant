#!/usr/bin/env python3
"""Business Unit: orchestration | Status: current.

Workflow state management for event-driven orchestration.

Provides workflow state tracking, state checking wrappers, and state management
utilities for preventing post-failure event processing.
"""

from __future__ import annotations

from enum import Enum
from logging import Logger
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from the_alchemiser.orchestration.event_driven_orchestrator import (
        EventDrivenOrchestrator,
    )

from the_alchemiser.shared.events import BaseEvent
from the_alchemiser.shared.events.handlers import EventHandler as SharedEventHandler


class WorkflowState(Enum):
    """Workflow execution state for tracking and preventing post-failure processing."""

    RUNNING = "running"
    FAILED = "failed"
    COMPLETED = "completed"


class EventHandlerProtocol(Protocol):
    """Structural type for event handlers registered on the EventBus."""

    def handle_event(self, event: BaseEvent) -> None:
        """Process a single event."""

    def can_handle(self, event_type: str) -> bool:
        """Return True if this handler supports the given event type."""


class StateCheckingHandlerWrapper:
    """Wrapper that checks workflow state before delegating to actual handler.

    This prevents handlers from processing events for failed workflows without
    requiring changes to the handlers themselves.
    """

    def __init__(
        self,
        wrapped_handler: SharedEventHandler,
        orchestrator: EventDrivenOrchestrator,
        event_type: str,
        logger: Logger,
    ) -> None:
        """Initialize the wrapper.

        Args:
            wrapped_handler: The actual handler to wrap
            orchestrator: The orchestrator to check workflow state
            event_type: The event type this wrapper handles
            logger: Logger instance

        """
        self.wrapped_handler: SharedEventHandler = wrapped_handler
        self.orchestrator: EventDrivenOrchestrator = orchestrator
        self.event_type: str = event_type
        self.logger: Logger = logger

    def handle_event(self, event: BaseEvent) -> None:
        """Handle event with workflow state checking.

        Args:
            event: The event to handle

        """
        # Check if workflow has failed before processing
        if self.orchestrator.is_workflow_failed(event.correlation_id):
            handler_name = type(self.wrapped_handler).__name__
            self.logger.info(
                f"🚫 Skipping {handler_name} - workflow {event.correlation_id} already failed"
            )
            return

        # Delegate to actual handler
        self.wrapped_handler.handle_event(event)

    def can_handle(self, event_type: str) -> bool:
        """Check if wrapped handler can handle event type.

        Args:
            event_type: The event type to check

        Returns:
            True if the wrapped handler can handle this event type

        """
        if hasattr(self.wrapped_handler, "can_handle"):
            return self.wrapped_handler.can_handle(event_type)
        return True


__all__ = [
    "WorkflowState",
    "EventHandlerProtocol",
    "StateCheckingHandlerWrapper",
]
