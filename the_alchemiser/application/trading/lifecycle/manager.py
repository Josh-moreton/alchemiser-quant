"""Order lifecycle state machine manager."""

from __future__ import annotations

import logging
import threading
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any, Mapping

from the_alchemiser.domain.trading.value_objects.order_id import OrderId
from the_alchemiser.domain.trading.lifecycle import (
    InvalidOrderStateTransitionError,
    LifecycleEventType,
    OrderLifecycleEvent,
    OrderLifecycleState,
)

logger = logging.getLogger(__name__)


class OrderLifecycleManager:
    """
    Thread-safe order lifecycle state machine manager.
    
    This class manages the state transitions of orders through their lifecycle,
    enforcing valid transitions and providing a central point for state queries.
    
    The manager maintains per-order state and uses fine-grained locking to ensure
    thread safety without blocking unrelated order operations.
    """
    
    # Declarative transition map: (from_state, to_state) -> reason_code
    VALID_TRANSITIONS: dict[tuple[OrderLifecycleState, OrderLifecycleState], str] = {
        # From NEW
        (OrderLifecycleState.NEW, OrderLifecycleState.VALIDATED): "order_validated",
        (OrderLifecycleState.NEW, OrderLifecycleState.REJECTED): "validation_failed",
        
        # From VALIDATED  
        (OrderLifecycleState.VALIDATED, OrderLifecycleState.QUEUED): "queued_for_submission",
        (OrderLifecycleState.VALIDATED, OrderLifecycleState.SUBMITTED): "direct_submission",
        (OrderLifecycleState.VALIDATED, OrderLifecycleState.REJECTED): "pre_submission_rejection",
        
        # From QUEUED
        (OrderLifecycleState.QUEUED, OrderLifecycleState.SUBMITTED): "submitted_to_broker",
        (OrderLifecycleState.QUEUED, OrderLifecycleState.CANCELLED): "cancelled_while_queued",
        (OrderLifecycleState.QUEUED, OrderLifecycleState.EXPIRED): "expired_while_queued",
        
        # From SUBMITTED
        (OrderLifecycleState.SUBMITTED, OrderLifecycleState.ACKNOWLEDGED): "broker_acknowledged",
        (OrderLifecycleState.SUBMITTED, OrderLifecycleState.REJECTED): "broker_rejected",
        (OrderLifecycleState.SUBMITTED, OrderLifecycleState.CANCEL_PENDING): "cancel_requested",
        (OrderLifecycleState.SUBMITTED, OrderLifecycleState.ERROR): "submission_error",
        
        # From ACKNOWLEDGED
        (OrderLifecycleState.ACKNOWLEDGED, OrderLifecycleState.PARTIALLY_FILLED): "partial_execution",
        (OrderLifecycleState.ACKNOWLEDGED, OrderLifecycleState.FILLED): "full_execution",
        (OrderLifecycleState.ACKNOWLEDGED, OrderLifecycleState.CANCEL_PENDING): "cancel_requested",
        (OrderLifecycleState.ACKNOWLEDGED, OrderLifecycleState.REJECTED): "post_ack_rejection",
        (OrderLifecycleState.ACKNOWLEDGED, OrderLifecycleState.EXPIRED): "order_expired",
        (OrderLifecycleState.ACKNOWLEDGED, OrderLifecycleState.ERROR): "execution_error",
        
        # From PARTIALLY_FILLED
        (OrderLifecycleState.PARTIALLY_FILLED, OrderLifecycleState.PARTIALLY_FILLED): "additional_partial_fill",
        (OrderLifecycleState.PARTIALLY_FILLED, OrderLifecycleState.FILLED): "completion_fill",
        (OrderLifecycleState.PARTIALLY_FILLED, OrderLifecycleState.CANCEL_PENDING): "cancel_remaining",
        (OrderLifecycleState.PARTIALLY_FILLED, OrderLifecycleState.ERROR): "fill_processing_error",
        
        # From CANCEL_PENDING
        (OrderLifecycleState.CANCEL_PENDING, OrderLifecycleState.CANCELLED): "cancel_confirmed",
        (OrderLifecycleState.CANCEL_PENDING, OrderLifecycleState.PARTIALLY_FILLED): "late_partial_fill",
        (OrderLifecycleState.CANCEL_PENDING, OrderLifecycleState.FILLED): "late_full_fill",
        (OrderLifecycleState.CANCEL_PENDING, OrderLifecycleState.ERROR): "cancel_error",
        
        # Terminal states allow same-state transitions for idempotency
        (OrderLifecycleState.FILLED, OrderLifecycleState.FILLED): "idempotent_filled",
        (OrderLifecycleState.CANCELLED, OrderLifecycleState.CANCELLED): "idempotent_cancelled", 
        (OrderLifecycleState.REJECTED, OrderLifecycleState.REJECTED): "idempotent_rejected",
        (OrderLifecycleState.EXPIRED, OrderLifecycleState.EXPIRED): "idempotent_expired",
        (OrderLifecycleState.ERROR, OrderLifecycleState.ERROR): "idempotent_error",
    }
    
    def __init__(self) -> None:
        """Initialize the lifecycle manager."""
        self._order_states: dict[OrderId, OrderLifecycleState] = {}
        self._order_locks: dict[OrderId, threading.Lock] = defaultdict(threading.Lock)
        self._global_lock = threading.Lock()
        
    def get_state(self, order_id: OrderId) -> OrderLifecycleState | None:
        """
        Get the current lifecycle state of an order.
        
        Args:
            order_id: Unique identifier for the order
            
        Returns:
            Current lifecycle state, or None if order not tracked
        """
        with self._global_lock:
            return self._order_states.get(order_id)
    
    def is_valid_transition(
        self, 
        from_state: OrderLifecycleState,
        to_state: OrderLifecycleState,
    ) -> bool:
        """
        Check if a state transition is valid according to the state machine rules.
        
        Args:
            from_state: Current state
            to_state: Target state
            
        Returns:
            True if transition is valid, False otherwise
        """
        return (from_state, to_state) in self.VALID_TRANSITIONS
    
    def advance(
        self,
        order_id: OrderId,
        target_state: OrderLifecycleState,
        *,
        event_type: LifecycleEventType = LifecycleEventType.STATE_CHANGED,
        metadata: Mapping[str, Any] | None = None,
        dispatcher: Any = None,  # LifecycleEventDispatcher (avoid circular import)
    ) -> OrderLifecycleEvent:
        """
        Advance an order to a new lifecycle state.
        
        This method handles the complete state transition process:
        1. Validates the transition is allowed
        2. Updates internal state atomically
        3. Creates and dispatches lifecycle event
        
        Args:
            order_id: Unique identifier for the order
            target_state: Desired new state
            event_type: Type of lifecycle event triggering this transition
            metadata: Additional contextual data for the event
            dispatcher: Event dispatcher to notify observers (optional)
            
        Returns:
            OrderLifecycleEvent representing the state change
            
        Raises:
            InvalidOrderStateTransitionError: If transition is not allowed
        """
        if metadata is None:
            metadata = {}
            
        # Get per-order lock for thread safety
        order_lock = self._order_locks[order_id]
        
        with order_lock:
            # Get current state (None for new orders)
            current_state = self._order_states.get(order_id)
            
            # For new orders, start from NEW state
            if current_state is None:
                if target_state == OrderLifecycleState.NEW:
                    # Initialize new order
                    previous_state = None
                    current_state = OrderLifecycleState.NEW
                else:
                    # Skip NEW state and validate direct transition from None
                    previous_state = None
                    current_state = None
            else:
                previous_state = current_state
            
            # Validate transition (skip validation for same-state transitions)
            if current_state != target_state:
                if current_state is not None and not self.is_valid_transition(current_state, target_state):
                    raise InvalidOrderStateTransitionError(
                        from_state=current_state,
                        to_state=target_state,
                        order_id=str(order_id),
                        reason=f"Transition not allowed by state machine rules",
                        context={
                            "current_transitions": list(self.VALID_TRANSITIONS.keys()),
                            "event_type": event_type.value,
                            "metadata": dict(metadata),
                        }
                    )
            
            # Update state atomically
            self._order_states[order_id] = target_state
            
            # Create lifecycle event
            event = OrderLifecycleEvent.create_state_change(
                order_id=order_id,
                previous_state=previous_state,
                new_state=target_state,
                event_type=event_type,
                metadata=metadata,
                timestamp=datetime.now(UTC),
            )
            
            logger.debug(
                "Order %s transitioned from %s to %s (event: %s)",
                order_id,
                previous_state,
                target_state,
                event_type.value,
            )
            
            # Dispatch event to observers if dispatcher provided
            if dispatcher is not None:
                try:
                    dispatcher.dispatch(event)
                except Exception as e:
                    logger.warning(
                        "Failed to dispatch lifecycle event for order %s: %s",
                        order_id,
                        e,
                        exc_info=True,
                    )
            
            return event
    
    def get_all_orders(self) -> dict[OrderId, OrderLifecycleState]:
        """
        Get all tracked orders and their current states.
        
        Returns:
            Dictionary mapping order IDs to their current states
        """
        with self._global_lock:
            return dict(self._order_states)
    
    def cleanup_terminal_orders(self, max_age_hours: int = 24) -> int:
        """
        Remove terminal orders older than the specified age.
        
        This method helps prevent memory leaks by cleaning up orders that
        have reached terminal states and are no longer needed for processing.
        
        Args:
            max_age_hours: Maximum age in hours for terminal orders to keep
            
        Returns:
            Number of orders cleaned up
        """
        # For now, just return 0 since we don't track creation time
        # This is a placeholder for future implementation that tracks timestamps
        return 0