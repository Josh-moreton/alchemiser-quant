"""Business Unit: order execution/placement; Status: current.

Order Lifecycle Management Domain Components.

This package contains the core domain objects for order lifecycle management,
including states, events, and protocols for observing lifecycle transitions.

All components follow domain-driven design principles with no external
framework dependencies.
"""

from .events import LifecycleEventType, OrderLifecycleEvent
from .exceptions import InvalidOrderStateTransitionError
from .protocols import LifecycleObserver
from .states import OrderLifecycleState

__all__ = [
    "InvalidOrderStateTransitionError",
    "LifecycleEventType",
    "LifecycleObserver",
    "OrderLifecycleEvent",
    "OrderLifecycleState",
]
