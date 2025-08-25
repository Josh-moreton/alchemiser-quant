"""Order lifecycle management with event dispatching."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Protocol

from the_alchemiser.domain.trading.value_objects.order_id import OrderId
from the_alchemiser.domain.trading.value_objects.order_lifecycle import (
    OrderEventType,
    OrderLifecycle,
    OrderLifecycleEvent,
    OrderLifecycleState,
)


class OrderLifecycleObserver(Protocol):
    """Observer protocol for order lifecycle events."""

    def on_order_event(self, event: OrderLifecycleEvent) -> None:
        """Handle an order lifecycle event."""
        ...


class LifecycleEventDispatcher:
    """Event dispatcher for order lifecycle events using observer pattern."""

    def __init__(self) -> None:
        """Initialize the event dispatcher."""
        self._observers: Dict[OrderEventType, List[OrderLifecycleObserver]] = {}
        self._global_observers: List[OrderLifecycleObserver] = []
        self.logger = logging.getLogger(__name__)

    def subscribe(
        self,
        observer: OrderLifecycleObserver,
        event_types: List[OrderEventType] | None = None,
    ) -> None:
        """Subscribe an observer to specific event types or all events."""
        if event_types is None:
            # Subscribe to all events
            self._global_observers.append(observer)
        else:
            # Subscribe to specific event types
            for event_type in event_types:
                if event_type not in self._observers:
                    self._observers[event_type] = []
                self._observers[event_type].append(observer)

    def unsubscribe(
        self,
        observer: OrderLifecycleObserver,
        event_types: List[OrderEventType] | None = None,
    ) -> None:
        """Unsubscribe an observer from specific event types or all events."""
        if event_types is None:
            # Remove from global observers
            if observer in self._global_observers:
                self._global_observers.remove(observer)
            # Remove from all specific event type observers
            for observers in self._observers.values():
                if observer in observers:
                    observers.remove(observer)
        else:
            # Remove from specific event types
            for event_type in event_types:
                if event_type in self._observers and observer in self._observers[event_type]:
                    self._observers[event_type].remove(observer)

    def dispatch(self, event: OrderLifecycleEvent) -> None:
        """Dispatch an event to all relevant observers."""
        # Log the event with structured data
        self.logger.info(
            "order_lifecycle_event",
            extra={
                "event_type": event.event_type.value,
                "order_id": str(event.order_id.value),
                "state_before": event.state_before.value,
                "state_after": event.state_after.value,
                "timestamp": event.timestamp.isoformat(),
                "details": event.details,
                "error_message": event.error_message,
            },
        )

        # Dispatch to global observers
        for observer in self._global_observers:
            try:
                observer.on_order_event(event)
            except Exception as e:
                self.logger.error(
                    "observer_error",
                    extra={
                        "observer": type(observer).__name__,
                        "event_type": event.event_type.value,
                        "order_id": str(event.order_id.value),
                        "error": str(e),
                    },
                )

        # Dispatch to specific event type observers
        if event.event_type in self._observers:
            for observer in self._observers[event.event_type]:
                try:
                    observer.on_order_event(event)
                except Exception as e:
                    self.logger.error(
                        "observer_error",
                        extra={
                            "observer": type(observer).__name__,
                            "event_type": event.event_type.value,
                            "order_id": str(event.order_id.value),
                            "error": str(e),
                        },
                    )


class OrderLifecycleManager:
    """Central manager for order lifecycle state and events."""

    def __init__(self, event_dispatcher: LifecycleEventDispatcher | None = None) -> None:
        """Initialize the lifecycle manager."""
        self.event_dispatcher = event_dispatcher or LifecycleEventDispatcher()
        self._orders: Dict[OrderId, OrderLifecycle] = {}
        self.logger = logging.getLogger(__name__)

    def create_order_lifecycle(
        self,
        order_id: OrderId,
        symbol: Any,
        side: str,
        quantity: Any,
        order_type: str,
        limit_price: Any | None = None,
    ) -> OrderLifecycle:
        """Create a new order lifecycle tracker."""
        if order_id in self._orders:
            raise ValueError(f"Order lifecycle already exists for {order_id}")

        lifecycle = OrderLifecycle(
            order_id=order_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=order_type,
            limit_price=limit_price,
        )

        self._orders[order_id] = lifecycle
        return lifecycle

    def get_order_lifecycle(self, order_id: OrderId) -> OrderLifecycle | None:
        """Get order lifecycle by ID."""
        return self._orders.get(order_id)

    def transition_order(
        self,
        order_id: OrderId,
        new_state: OrderLifecycleState,
        event_type: OrderEventType,
        details: Dict[str, Any] | None = None,
        error_message: str | None = None,
    ) -> None:
        """Transition an order to a new state and dispatch event."""
        lifecycle = self._orders.get(order_id)
        if lifecycle is None:
            self.logger.warning(
                "order_not_found",
                extra={"order_id": str(order_id.value), "operation": "transition_order"},
            )
            return

        try:
            lifecycle.transition_to(new_state, event_type, details, error_message)
            
            # Dispatch the most recent event
            if lifecycle.events:
                self.event_dispatcher.dispatch(lifecycle.events[-1])
                
        except ValueError as e:
            self.logger.error(
                "invalid_state_transition",
                extra={
                    "order_id": str(order_id.value),
                    "current_state": lifecycle.current_state.value,
                    "target_state": new_state.value,
                    "error": str(e),
                },
            )
            # Transition to error state
            lifecycle.transition_to(
                OrderLifecycleState.ERROR, OrderEventType.ERROR, error_message=str(e)
            )
            if lifecycle.events:
                self.event_dispatcher.dispatch(lifecycle.events[-1])

    def record_partial_fill(
        self,
        order_id: OrderId,
        fill_quantity: Any,
        fill_price: Any,
        details: Dict[str, Any] | None = None,
    ) -> None:
        """Record a partial fill for an order."""
        lifecycle = self._orders.get(order_id)
        if lifecycle is None:
            self.logger.warning(
                "order_not_found",
                extra={"order_id": str(order_id.value), "operation": "record_partial_fill"},
            )
            return

        try:
            lifecycle.add_partial_fill(fill_quantity, fill_price, details)
            
            # Dispatch the most recent event
            if lifecycle.events:
                self.event_dispatcher.dispatch(lifecycle.events[-1])
                
        except ValueError as e:
            self.logger.error(
                "invalid_partial_fill",
                extra={
                    "order_id": str(order_id.value),
                    "fill_quantity": str(fill_quantity),
                    "fill_price": str(fill_price),
                    "error": str(e),
                },
            )

    def increment_repeg(self, order_id: OrderId) -> None:
        """Increment repeg counter for an order."""
        lifecycle = self._orders.get(order_id)
        if lifecycle is not None:
            lifecycle.increment_repeg()

    def increment_attempt(self, order_id: OrderId) -> None:
        """Increment attempt counter for an order."""
        lifecycle = self._orders.get(order_id)
        if lifecycle is not None:
            lifecycle.increment_attempt()

    def get_active_orders(self) -> List[OrderLifecycle]:
        """Get all orders in active states."""
        return [order for order in self._orders.values() if order.is_active]

    def get_terminal_orders(self) -> List[OrderLifecycle]:
        """Get all orders in terminal states."""
        return [order for order in self._orders.values() if order.is_terminal]

    def get_orders_by_state(self, state: OrderLifecycleState) -> List[OrderLifecycle]:
        """Get all orders in a specific state."""
        return [order for order in self._orders.values() if order.current_state == state]

    def cleanup_terminal_orders(self, max_age_hours: int = 24) -> int:
        """Clean up old terminal orders to prevent memory leaks."""
        from datetime import UTC, datetime, timedelta

        cutoff_time = datetime.now(UTC) - timedelta(hours=max_age_hours)
        orders_to_remove = []

        for order_id, lifecycle in self._orders.items():
            if lifecycle.is_terminal and lifecycle.last_updated < cutoff_time:
                orders_to_remove.append(order_id)

        for order_id in orders_to_remove:
            del self._orders[order_id]

        if orders_to_remove:
            self.logger.info(
                "terminal_orders_cleaned",
                extra={
                    "orders_removed": len(orders_to_remove),
                    "cutoff_time": cutoff_time.isoformat(),
                },
            )

        return len(orders_to_remove)

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics of managed orders."""
        state_counts: Dict[str, int] = {}
        for lifecycle in self._orders.values():
            state = lifecycle.current_state.value
            state_counts[state] = state_counts.get(state, 0) + 1

        return {
            "total_orders": len(self._orders),
            "active_orders": len(self.get_active_orders()),
            "terminal_orders": len(self.get_terminal_orders()),
            "state_breakdown": state_counts,
        }