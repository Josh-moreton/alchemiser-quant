"""Business Unit: execution | Status: current.

Simplified order lifecycle management replacing over-engineered state machine.

This module consolidates the complex 9-file lifecycle system into a single,
focused implementation that provides essential order state tracking without
unnecessary abstraction and observer overhead.
"""

from __future__ import annotations

import logging
import threading
from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any, ClassVar

from the_alchemiser.execution.orders.order_id import OrderId
from the_alchemiser.shared.utils.timezone_utils import ensure_timezone_aware

logger = logging.getLogger(__name__)


class OrderState(str, Enum):
    """Simplified order lifecycle states focused on essential transitions."""

    # Core workflow states
    NEW = "NEW"  # Order created
    VALIDATED = "VALIDATED"  # Order passed validation
    SUBMITTED = "SUBMITTED"  # Order sent to broker
    ACKNOWLEDGED = "ACKNOWLEDGED"  # Broker confirmed receipt

    # Execution states
    PARTIALLY_FILLED = "PARTIALLY_FILLED"  # Order partially executed
    FILLED = "FILLED"  # Order completely executed

    # Terminal states
    CANCELLED = "CANCELLED"  # Order cancelled
    REJECTED = "REJECTED"  # Order rejected by broker
    EXPIRED = "EXPIRED"  # Order expired
    ERROR = "ERROR"  # Unrecoverable error

    @classmethod
    def is_terminal(cls, state: OrderState) -> bool:
        """Check if state is terminal (no further transitions allowed)."""
        return state in {cls.FILLED, cls.CANCELLED, cls.REJECTED, cls.EXPIRED, cls.ERROR}

    @classmethod
    def is_successful(cls, state: OrderState) -> bool:
        """Check if state represents successful completion."""
        return state == cls.FILLED


@dataclass(frozen=True)
class StateTransition:
    """Immutable record of an order state transition."""

    order_id: OrderId
    from_state: OrderState | None
    to_state: OrderState
    timestamp: datetime
    reason: str | None = None
    metadata: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """Ensure timestamp is UTC."""
        timezone_aware_timestamp = ensure_timezone_aware(self.timestamp)
        object.__setattr__(self, "timestamp", timezone_aware_timestamp)


class OrderStateError(Exception):
    """Exception for invalid order state operations."""

    def __init__(self, message: str, order_id: OrderId | None = None) -> None:
        """Initialize exception with message and optional order ID."""
        super().__init__(message)
        self.order_id = order_id


class SimplifiedLifecycleManager:
    """Simplified, thread-safe order lifecycle state manager.

    This replaces the complex 9-file lifecycle system with essential
    functionality: state tracking, transition validation, and basic logging.
    Removes unnecessary observer patterns and event dispatching overhead.
    """

    # Valid state transitions (simplified from complex transition matrix)
    VALID_TRANSITIONS: ClassVar[dict[tuple[OrderState, OrderState], str]] = {
        # From NEW
        (OrderState.NEW, OrderState.VALIDATED): "validation_passed",
        (OrderState.NEW, OrderState.REJECTED): "validation_failed",
        # From VALIDATED
        (OrderState.VALIDATED, OrderState.SUBMITTED): "submitted_to_broker",
        (OrderState.VALIDATED, OrderState.REJECTED): "pre_submission_rejection",
        # From SUBMITTED
        (OrderState.SUBMITTED, OrderState.ACKNOWLEDGED): "broker_acknowledged",
        (OrderState.SUBMITTED, OrderState.FILLED): "immediate_fill",
        (OrderState.SUBMITTED, OrderState.PARTIALLY_FILLED): "immediate_partial_fill",
        (OrderState.SUBMITTED, OrderState.REJECTED): "broker_rejected",
        (OrderState.SUBMITTED, OrderState.CANCELLED): "cancelled_before_ack",
        (OrderState.SUBMITTED, OrderState.ERROR): "submission_error",
        # From ACKNOWLEDGED
        (OrderState.ACKNOWLEDGED, OrderState.PARTIALLY_FILLED): "partial_execution",
        (OrderState.ACKNOWLEDGED, OrderState.FILLED): "full_execution",
        (OrderState.ACKNOWLEDGED, OrderState.CANCELLED): "cancelled_after_ack",
        (OrderState.ACKNOWLEDGED, OrderState.EXPIRED): "order_expired",
        (OrderState.ACKNOWLEDGED, OrderState.ERROR): "execution_error",
        # From PARTIALLY_FILLED
        (OrderState.PARTIALLY_FILLED, OrderState.FILLED): "completion_fill",
        (OrderState.PARTIALLY_FILLED, OrderState.CANCELLED): "cancelled_partial",
        (OrderState.PARTIALLY_FILLED, OrderState.ERROR): "partial_fill_error",
        # Terminal state idempotent transitions
        (OrderState.FILLED, OrderState.FILLED): "idempotent",
        (OrderState.CANCELLED, OrderState.CANCELLED): "idempotent",
        (OrderState.REJECTED, OrderState.REJECTED): "idempotent",
        (OrderState.EXPIRED, OrderState.EXPIRED): "idempotent",
        (OrderState.ERROR, OrderState.ERROR): "idempotent",
    }

    def __init__(self) -> None:
        """Initialize the simplified lifecycle manager."""
        self._order_states: dict[OrderId, OrderState] = {}
        self._order_transitions: dict[OrderId, list[StateTransition]] = defaultdict(list)
        self._lock = threading.RLock()

    def get_state(self, order_id: OrderId) -> OrderState | None:
        """Get current state of an order."""
        with self._lock:
            return self._order_states.get(order_id)

    def get_transition_history(self, order_id: OrderId) -> list[StateTransition]:
        """Get the transition history for an order."""
        with self._lock:
            return list(self._order_transitions[order_id])  # Return copy

    def transition_to(
        self,
        order_id: OrderId,
        new_state: OrderState,
        reason: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> StateTransition:
        """Transition an order to a new state with validation.

        Args:
            order_id: Order identifier
            new_state: Target state
            reason: Optional reason for transition
            metadata: Optional additional context

        Returns:
            StateTransition record

        Raises:
            OrderStateError: If transition is invalid

        """
        with self._lock:
            current_state = self._order_states.get(order_id)

            # Validate transition
            if not self._is_valid_transition(current_state, new_state):
                raise OrderStateError(
                    f"Invalid transition from {current_state} to {new_state} for order {order_id}",
                    order_id=order_id,
                )

            # Create transition record
            transition = StateTransition(
                order_id=order_id,
                from_state=current_state,
                to_state=new_state,
                timestamp=datetime.now(UTC),
                reason=reason,
                metadata=metadata,
            )

            # Update state and record transition
            self._order_states[order_id] = new_state
            self._order_transitions[order_id].append(transition)

            # Simple logging (replaces complex observer system)
            logger.info(
                "Order %s transitioned %s -> %s%s",
                order_id,
                current_state or "None",
                new_state,
                f" ({reason})" if reason else "",
                extra={
                    "order_id": str(order_id),
                    "from_state": current_state.value if current_state else None,
                    "to_state": new_state.value,
                    "reason": reason,
                    "metadata": metadata,
                },
            )

            return transition

    def initialize_order(self, order_id: OrderId) -> StateTransition:
        """Initialize a new order in NEW state."""
        return self.transition_to(order_id, OrderState.NEW, reason="order_created")

    def is_terminal_state(self, order_id: OrderId) -> bool:
        """Check if order is in a terminal state."""
        state = self.get_state(order_id)
        return state is not None and OrderState.is_terminal(state)

    def get_orders_in_state(self, state: OrderState) -> list[OrderId]:
        """Get all orders currently in the specified state."""
        with self._lock:
            return [
                order_id
                for order_id, order_state in self._order_states.items()
                if order_state == state
            ]

    def _is_valid_transition(self, from_state: OrderState | None, to_state: OrderState) -> bool:
        """Check if a state transition is valid."""
        # Initial state (None -> any state) is always valid for NEW
        if from_state is None:
            return to_state == OrderState.NEW

        # Check against transition matrix
        return (from_state, to_state) in self.VALID_TRANSITIONS


# Compatibility aliases for existing code during transition
OrderLifecycleState = OrderState
OrderLifecycleManager = SimplifiedLifecycleManager
InvalidOrderStateTransitionError = OrderStateError

__all__ = [
    "InvalidOrderStateTransitionError",
    "OrderLifecycleManager",
    "OrderLifecycleState",
    "OrderState",
    "OrderStateError",
    "SimplifiedLifecycleManager",
    "StateTransition",
]
