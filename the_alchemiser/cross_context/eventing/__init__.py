"""Business Unit: utilities | Status: current

Eventing infrastructure for in-process publish/subscribe communication.

This module provides the EventBus abstraction and implementation for
synchronous in-memory event handling between bounded contexts.
"""

from .event_bus import EventBus
from .in_memory_event_bus import InMemoryEventBus

__all__ = [
    "EventBus",
    "InMemoryEventBus",
]