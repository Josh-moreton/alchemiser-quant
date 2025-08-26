"""Observer protocol for order lifecycle events."""

from __future__ import annotations

from typing import Protocol

from .events import OrderLifecycleEvent


class LifecycleObserver(Protocol):
    """
    Protocol for observing order lifecycle events.

    Implementations of this protocol can be registered with the
    LifecycleEventDispatcher to receive notifications when order
    lifecycle events occur.

    Observer implementations should be defensive and handle exceptions
    gracefully, as they should not disrupt the core order processing flow.
    """

    def on_lifecycle_event(self, event: OrderLifecycleEvent) -> None:
        """
        Handle an order lifecycle event.

        This method is called whenever an order transitions between lifecycle
        states. Implementations should process the event quickly and avoid
        blocking operations that could slow down order processing.

        Args:
            event: The lifecycle event that occurred

        Note:
            Implementations should not raise exceptions. If an exception occurs,
            it will be caught by the dispatcher and handled via the error system,
            but the event will still be delivered to other observers.
        """
        ...
