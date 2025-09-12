#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Event handler protocols and utilities.

Defines the interface for event handlers and utilities for event handling
in the event-driven architecture.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .base import BaseEvent


@runtime_checkable
class EventHandler(Protocol):
    """Protocol for event handlers.

    All event handlers must implement this interface to receive events
    from the event bus.
    """

    def handle_event(self, event: BaseEvent) -> None:
        """Handle an event.

        Args:
            event: The event to handle

        Raises:
            Exception: If event handling fails

        """
        ...

    def can_handle(self, event_type: str) -> bool:
        """Check if handler can handle a specific event type.

        Args:
            event_type: The type of event to check

        Returns:
            True if this handler can handle the event type, False otherwise

        """
        ...
