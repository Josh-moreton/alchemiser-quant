"""Business Unit: execution | Status: current.

Simplified lifecycle coordinator using streamlined state management.

Updated in Phase 3 to use simplified lifecycle manager, removing complex
observer patterns and event dispatching overhead while preserving essential
lifecycle tracking functionality.
"""

from __future__ import annotations

import logging
from typing import Any

from the_alchemiser.execution.lifecycle_simplified import (
    OrderState,
    SimplifiedLifecycleManager,
    StateTransition,
)
from the_alchemiser.execution.orders.order_types import OrderId


class LifecycleCoordinator:
    """Simplified service for order lifecycle management.

    Phase 3 redesign focusing on essential lifecycle tracking without
    over-engineered observer patterns and event dispatching complexity.
    """

    def __init__(self) -> None:
        """Initialize the simplified lifecycle coordinator."""
        self.logger = logging.getLogger(__name__)

        # Use simplified lifecycle management (replaces complex 9-file system)
        self.lifecycle_manager = SimplifiedLifecycleManager()

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

    def initialize_order(self, order_id: OrderId) -> StateTransition:
        """Initialize a new order for lifecycle tracking.

        Args:
            order_id: Order identifier

        Returns:
            StateTransition record of initialization

        """
        return self.lifecycle_manager.initialize_order(order_id)

    def transition_order_state(
        self,
        order_id: OrderId,
        target_state: OrderState,
        reason: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StateTransition:
        """Transition an order to a new state.

        Args:
            order_id: Order identifier
            target_state: Target lifecycle state
            reason: Reason for state transition
            metadata: Additional context metadata

        Returns:
            StateTransition record

        """
        return self.lifecycle_manager.transition_to(
            order_id=order_id,
            new_state=target_state,
            reason=reason,
            metadata=metadata,
        )

    def get_order_state(self, order_id: OrderId) -> OrderState | None:
        """Get the current lifecycle state of an order.

        Args:
            order_id: Order identifier

        Returns:
            Current lifecycle state, or None if order not tracked

        """
        return self.lifecycle_manager.get_state(order_id)

    def get_transition_history(self, order_id: OrderId) -> list[StateTransition]:
        """Get the transition history for an order.

        Args:
            order_id: Order identifier

        Returns:
            List of state transitions for the order

        """
        return self.lifecycle_manager.get_transition_history(order_id)

    def is_order_terminal(self, order_id: OrderId) -> bool:
        """Check if an order is in a terminal state.

        Args:
            order_id: Order identifier

        Returns:
            True if order is in terminal state, False otherwise

        """
        return self.lifecycle_manager.is_terminal_state(order_id)

    def get_orders_in_state(self, state: OrderState) -> list[OrderId]:
        """Get all orders currently in the specified state.

        Args:
            state: Target state to query

        Returns:
            List of order IDs in the specified state

        """
        return self.lifecycle_manager.get_orders_in_state(state)
