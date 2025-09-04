"""Business Unit: execution | Status: current

Lifecycle coordinator managing order lifecycle tracking and event dispatching.
"""

from __future__ import annotations

import logging
from typing import Any

from the_alchemiser.execution.lifecycle import (
    LifecycleEventDispatcher,
    LifecycleEventType,
    LoggingObserver,
    MetricsObserver,
    OrderLifecycleManager,
    OrderLifecycleState,
)
from the_alchemiser.execution.orders.order_id import OrderId


class LifecycleCoordinator:
    """Service responsible for order lifecycle management and event coordination.
    
    Handles lifecycle state tracking, event dispatching, and lifecycle metrics.
    """

    def __init__(self) -> None:
        """Initialize the lifecycle coordinator."""
        self.logger = logging.getLogger(__name__)
        
        # Initialize order lifecycle management
        self.lifecycle_manager = OrderLifecycleManager()
        self.lifecycle_dispatcher = LifecycleEventDispatcher()
        
        # Register default observers
        self.lifecycle_dispatcher.register(LoggingObserver(use_rich_logging=True))
        self.lifecycle_dispatcher.register(MetricsObserver())

    def create_order_id(self, client_order_id: str | None = None) -> OrderId:
        """Create an OrderId for lifecycle tracking.

        Args:
            client_order_id: Optional client-specified order ID

        Returns:
            OrderId for lifecycle tracking
        """
        if client_order_id:
            try:
                return OrderId.from_string(client_order_id)
            except ValueError:
                # If client_order_id is not a valid UUID, generate a new one
                pass
        return OrderId.generate()

    def emit_lifecycle_event(
        self,
        order_id: OrderId,
        target_state: OrderLifecycleState,
        event_type: LifecycleEventType = LifecycleEventType.STATE_CHANGED,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Emit a lifecycle event for an order.

        Args:
            order_id: Order identifier
            target_state: Target lifecycle state
            event_type: Type of lifecycle event
            metadata: Additional event metadata
        """
        try:
            self.lifecycle_manager.advance(
                order_id=order_id,
                target_state=target_state,
                event_type=event_type,
                metadata=metadata or {},
                dispatcher=self.lifecycle_dispatcher,
            )
        except Exception as e:
            self.logger.warning(
                "Failed to emit lifecycle event for order %s: %s",
                order_id,
                e,
                exc_info=True,
            )

    def get_order_lifecycle_state(self, order_id: OrderId) -> OrderLifecycleState | None:
        """Get the current lifecycle state of an order.

        Args:
            order_id: Order identifier

        Returns:
            Current lifecycle state, or None if order not tracked
        """
        return self.lifecycle_manager.get_state(order_id)

    def get_all_tracked_orders(self) -> dict[OrderId, OrderLifecycleState]:
        """Get all tracked orders and their current lifecycle states.

        Returns:
            Dictionary mapping order IDs to their current states
        """
        return self.lifecycle_manager.get_all_orders()

    def get_lifecycle_metrics(self) -> dict[str, Any]:
        """Get lifecycle metrics from the metrics observer.

        Returns:
            Dictionary containing lifecycle event and transition metrics
        """
        # Find the metrics observer
        for observer in self.lifecycle_dispatcher.iter_observers():
            if hasattr(observer, "get_event_counts") and hasattr(observer, "get_transition_counts"):
                return {
                    "event_counts": observer.get_event_counts(),
                    "transition_counts": observer.get_transition_counts(),
                    "total_observers": self.lifecycle_dispatcher.get_observer_count(),
                    "observer_types": self.lifecycle_dispatcher.get_observer_types(),
                }

        return {
            "event_counts": {},
            "transition_counts": {},
            "total_observers": self.lifecycle_dispatcher.get_observer_count(),
            "observer_types": self.lifecycle_dispatcher.get_observer_types(),
        }