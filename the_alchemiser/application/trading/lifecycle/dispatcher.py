"""Lifecycle event dispatcher with observer pattern."""

from __future__ import annotations

import logging
from typing import Any

from the_alchemiser.domain.trading.lifecycle import LifecycleObserver, OrderLifecycleEvent
from the_alchemiser.services.errors.handler import TradingSystemErrorHandler

logger = logging.getLogger(__name__)


class LifecycleEventDispatcher:
    """
    Thread-safe event dispatcher for order lifecycle events.
    
    This class implements the observer pattern, allowing multiple observers
    to be notified of order lifecycle events. The dispatcher ensures that
    exceptions in one observer do not prevent other observers from receiving
    events.
    """
    
    def __init__(self, error_handler: TradingSystemErrorHandler | None = None) -> None:
        """
        Initialize the event dispatcher.
        
        Args:
            error_handler: Optional error handler for observer exceptions
        """
        self._observers: list[LifecycleObserver] = []
        self._error_handler = error_handler or TradingSystemErrorHandler()
    
    def register(self, observer: LifecycleObserver) -> None:
        """
        Register an observer to receive lifecycle events.
        
        Observers are notified in the order they were registered (FIFO).
        The same observer instance can only be registered once.
        
        Args:
            observer: Observer to register for event notifications
        """
        if observer not in self._observers:
            self._observers.append(observer)
            logger.debug(
                "Registered lifecycle observer: %s (total: %d)",
                observer.__class__.__name__,
                len(self._observers),
            )
        else:
            logger.warning(
                "Observer %s already registered, ignoring duplicate registration",
                observer.__class__.__name__,
            )
    
    def unregister(self, observer: LifecycleObserver) -> bool:
        """
        Unregister an observer from receiving lifecycle events.
        
        Args:
            observer: Observer to unregister
            
        Returns:
            True if observer was found and removed, False if not found
        """
        try:
            self._observers.remove(observer)
            logger.debug(
                "Unregistered lifecycle observer: %s (remaining: %d)",
                observer.__class__.__name__,
                len(self._observers),
            )
            return True
        except ValueError:
            logger.warning(
                "Attempted to unregister observer %s that was not registered",
                observer.__class__.__name__,
            )
            return False
    
    def dispatch(self, event: OrderLifecycleEvent) -> None:
        """
        Dispatch a lifecycle event to all registered observers.
        
        This method ensures that exceptions in one observer do not prevent
        other observers from receiving the event. Observer exceptions are
        logged and reported through the error handling system.
        
        Args:
            event: Lifecycle event to dispatch to observers
        """
        if not self._observers:
            logger.debug(
                "No observers registered for lifecycle event: %s -> %s",
                event.previous_state,
                event.new_state,
            )
            return
        
        observer_errors: list[tuple[str, Exception]] = []
        
        for observer in self._observers:
            try:
                observer.on_lifecycle_event(event)
            except Exception as e:
                observer_name = observer.__class__.__name__
                observer_errors.append((observer_name, e))
                
                logger.warning(
                    "Observer %s failed to process lifecycle event for order %s: %s",
                    observer_name,
                    event.order_id,
                    e,
                    exc_info=True,
                )
                
                # Report to error handling system
                try:
                    self._error_handler.handle_error(
                        error=e,
                        component=f"LifecycleObserver.{observer_name}",
                        context=f"processing lifecycle event: {event.event_type.value}",
                        additional_data={
                            "order_id": str(event.order_id),
                            "previous_state": event.previous_state.value if event.previous_state else None,
                            "new_state": event.new_state.value,
                            "event_type": event.event_type.value,
                            "metadata": dict(event.metadata),
                        },
                    )
                except Exception as handler_error:
                    logger.error(
                        "Error handler failed while processing observer exception: %s",
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
                len(self._observers),
                event.order_id,
                event.previous_state,
                event.new_state,
            )
    
    def get_observer_count(self) -> int:
        """
        Get the number of registered observers.
        
        Returns:
            Number of currently registered observers
        """
        return len(self._observers)
    
    def get_observer_types(self) -> list[str]:
        """
        Get the class names of registered observers.
        
        Returns:
            List of observer class names
        """
        return [observer.__class__.__name__ for observer in self._observers]