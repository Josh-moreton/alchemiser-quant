"""Business Unit: shared | Status: current.

Event handler registry for event-driven orchestration.

Provides centralized registration and discovery of event handlers across modules.
"""

from __future__ import annotations

from .handler_registry import EventHandlerRegistry, HandlerRegistration

__all__ = [
    "EventHandlerRegistry",
    "HandlerRegistration",
]
