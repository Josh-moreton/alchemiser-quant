"""Business Unit: order execution/placement; Status: current.

Lifecycle event dispatcher with thread-safe observer pattern.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Iterable

from the_alchemiser.domain.trading.lifecycle import (
    LifecycleObserver,
    OrderLifecycleEvent,
)
# TODO: Error handler needs to be migrated

logger = logging.getLogger(__name__)


class LifecycleEventDispatcher:
    """Thread-safe observer dispatcher for order lifecycle events."""

    def __init__(self, error_handler: TradingSystemErrorHandler | None = None) -> None:
        self._observers: list[LifecycleObserver] = []
        self._lock = threading.RLock()
        self._error_handler = error_handler or TradingSystemErrorHandler()

    def register(self, observer: LifecycleObserver) -> None:
        """Register an observer (idempotent)."""
        with self._lock:
            if observer in self._observers:
                logger.warning(
                    "Observer %s already registered, ignoring duplicate",
                    observer.__class__.__name__,
                )
                return
            self._observers.append(observer)
            logger.debug(
                "Registered lifecycle observer: %s (total: %d)",
                observer.__class__.__name__,
                len(self._observers),
            )

    def unregister(self, observer: LifecycleObserver) -> bool:
        """Unregister an observer; return True if removed."""
        with self._lock:
            try:
                self._observers.remove(observer)
            except ValueError:
                logger.warning(
                    "Attempted to unregister non-registered observer %s",
                    observer.__class__.__name__,
                )
                return False
            logger.debug(
                "Unregistered lifecycle observer: %s (remaining: %d)",
                observer.__class__.__name__,
                len(self._observers),
            )
            return True

    def dispatch(self, event: OrderLifecycleEvent) -> None:
        """Dispatch event to observers; isolate observer failures."""
        with self._lock:
            observers_snapshot = tuple(self._observers)
        if not observers_snapshot:
            logger.debug(
                "No observers registered for lifecycle event: %s -> %s",
                event.previous_state,
                event.new_state,
            )
            return

        observer_errors: list[tuple[str, Exception]] = []
        for observer in observers_snapshot:
            try:
                observer.on_lifecycle_event(event)
            except Exception as e:
                name = observer.__class__.__name__
                observer_errors.append((name, e))
                logger.warning(
                    "Observer %s failed processing lifecycle event for order %s: %s",
                    name,
                    event.order_id,
                    e,
                    exc_info=True,
                )
                try:
                    self._error_handler.handle_error(
                        error=e,
                        component=f"LifecycleObserver.{name}",
                        context=f"processing lifecycle event: {event.event_type.value}",
                        additional_data={
                            "order_id": str(event.order_id),
                            "previous_state": (
                                event.previous_state.value if event.previous_state else None
                            ),
                            "new_state": event.new_state.value,
                            "event_type": event.event_type.value,
                            "metadata": dict(event.metadata),
                        },
                    )
                except Exception as handler_error:
                    logger.error(
                        "Error handler failed processing observer exception: %s",
                        handler_error,
                        exc_info=True,
                    )

        if observer_errors:
            logger.warning(
                "Lifecycle event dispatch completed with %d observer errors (order: %s)",
                len(observer_errors),
                event.order_id,
            )
        else:
            logger.debug(
                "Successfully dispatched lifecycle event to %d observers (order: %s, %s -> %s)",
                len(observers_snapshot),
                event.order_id,
                event.previous_state,
                event.new_state,
            )

    def get_observer_count(self) -> int:
        with self._lock:
            return len(self._observers)

    def get_observer_types(self) -> list[str]:
        with self._lock:
            return [o.__class__.__name__ for o in self._observers]

    def iter_observers(self) -> Iterable[LifecycleObserver]:
        """Return a snapshot iterable of observers (thread-safe)."""
        with self._lock:
            return tuple(self._observers)
