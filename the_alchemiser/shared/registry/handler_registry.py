"""Business Unit: shared | Status: current.

Event handler registry implementation for event-driven orchestration.

Provides centralized registration and discovery of event handlers across modules
with support for priority ordering and metadata.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

from the_alchemiser.shared.events.base import BaseEvent


class EventHandler(Protocol):
    """Protocol for event handlers."""

    def can_handle(self, event_type: str) -> bool:
        """Check if handler can handle a specific event type."""
        ...

    def handle_event(self, event: BaseEvent) -> None:
        """Handle an event."""
        ...


# Type alias for handler factory functions
HandlerFactory = Callable[..., EventHandler]


@dataclass(frozen=True)
class HandlerRegistration:
    """Registration data for an event handler.

    Contains all metadata needed to register and instantiate handlers
    during the bootstrap process.
    """

    event_type: str
    handler_factory: HandlerFactory
    module_name: str
    priority: int = 100  # Lower numbers = higher priority
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate registration data."""
        if self.event_type is None or not self.event_type.strip():
            raise ValueError("event_type cannot be empty or whitespace")
        if self.module_name is None or not self.module_name.strip():
            raise ValueError("module_name cannot be empty or whitespace")
        if self.priority < 0:
            raise ValueError("priority must be non-negative")


class EventHandlerRegistry:
    """Registry for event handlers with priority ordering and metadata support.

    Manages handler registrations and provides access to handlers by event type
    and module. Supports priority ordering for multiple handlers per event.
    """

    def __init__(self) -> None:
        """Initialize empty registry."""
        self._registrations: list[HandlerRegistration] = []

    def register(self, registration: HandlerRegistration) -> None:
        """Register a handler.

        Args:
            registration: Handler registration data

        Raises:
            ValueError: If registration is invalid or duplicate

        """
        # Check for duplicates (same event_type and module_name)
        existing = self._find_registration(registration.event_type, registration.module_name)
        if existing:
            raise ValueError(
                f"Handler for event '{registration.event_type}' from module "
                f"'{registration.module_name}' already registered"
            )

        self._registrations.append(registration)

        # Keep registrations sorted by priority for efficient iteration
        self._registrations.sort(key=lambda r: (r.event_type, r.priority))

    def register_handler(
        self,
        event_type: str,
        handler_factory: HandlerFactory,
        module_name: str,
        *,
        priority: int = 100,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Register a handler with the registry.

        Args:
            event_type: Type of event the handler processes
            handler_factory: Factory function to create handler instance
            module_name: Name of the module registering the handler
            priority: Handler priority (lower = higher priority)
            metadata: Optional metadata for the handler

        """
        registration = HandlerRegistration(
            event_type=event_type,
            handler_factory=handler_factory,
            module_name=module_name,
            priority=priority,
            metadata=metadata or {},
        )
        self.register(registration)

    def get_handlers_for_event(self, event_type: str) -> list[HandlerRegistration]:
        """Get all handlers for a specific event type, ordered by priority.

        Args:
            event_type: Event type to get handlers for

        Returns:
            List of handler registrations ordered by priority (lower = higher)

        """
        return [reg for reg in self._registrations if reg.event_type == event_type]

    def get_handlers_for_module(self, module_name: str) -> list[HandlerRegistration]:
        """Get all handlers registered by a specific module.

        Args:
            module_name: Module name to get handlers for

        Returns:
            List of handler registrations from the module

        """
        return [reg for reg in self._registrations if reg.module_name == module_name]

    def get_all_registrations(self) -> list[HandlerRegistration]:
        """Get all handler registrations.

        Returns:
            List of all registrations ordered by event type and priority

        """
        return self._registrations.copy()

    def get_supported_events(self) -> set[str]:
        """Get set of all supported event types.

        Returns:
            Set of event types that have registered handlers

        """
        return {reg.event_type for reg in self._registrations}

    def clear(self) -> None:
        """Clear all registrations (mainly for testing)."""
        self._registrations.clear()

    def _find_registration(self, event_type: str, module_name: str) -> HandlerRegistration | None:
        """Find existing registration for event type and module."""
        for reg in self._registrations:
            if reg.event_type == event_type and reg.module_name == module_name:
                return reg
        return None
