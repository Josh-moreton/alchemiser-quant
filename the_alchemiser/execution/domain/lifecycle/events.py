"""Business Unit: order execution/placement; Status: current.

Order lifecycle events and event types.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from the_alchemiser.domain.trading.value_objects.order_id import OrderId

from .states import OrderLifecycleState


class LifecycleEventType(str, Enum):
    """Semantic event types that provide business meaning to lifecycle transitions.

    These event types capture the business reason for a state transition,
    enabling richer observability and event-driven workflows.
    """

    STATE_CHANGED = "STATE_CHANGED"  # Generic state transition
    PARTIAL_FILL = "PARTIAL_FILL"  # Order partially filled
    CANCEL_REQUESTED = "CANCEL_REQUESTED"  # Cancel operation initiated
    CANCEL_CONFIRMED = "CANCEL_CONFIRMED"  # Cancel operation completed
    REJECTED = "REJECTED"  # Order rejected by broker/exchange
    EXPIRED = "EXPIRED"  # Order expired (time/condition)
    ERROR = "ERROR"  # Error occurred during processing
    TIMEOUT = "TIMEOUT"  # Operation timed out
    ESCALATED = "ESCALATED"  # Issue escalated for attention


@dataclass(frozen=True)
class OrderLifecycleEvent:
    """Immutable event representing an order lifecycle transition.

    This event captures all relevant information about a state transition,
    including contextual metadata that can be used for debugging, auditing,
    and business intelligence.

    Attributes:
        order_id: Unique identifier for the order
        previous_state: State before the transition (None for initial state)
        new_state: State after the transition
        timestamp: When the transition occurred (UTC)
        event_type: Semantic type of the event
        metadata: Additional contextual information (immutable)

    """

    order_id: OrderId
    previous_state: OrderLifecycleState | None
    new_state: OrderLifecycleState
    timestamp: datetime
    event_type: LifecycleEventType
    metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        """Validate event data after initialization."""
        # Ensure timestamp is timezone-aware (UTC)
        if self.timestamp.tzinfo is None:
            # Replace with UTC timezone if naive
            object.__setattr__(self, "timestamp", self.timestamp.replace(tzinfo=UTC))

        # Validate state transition logic
        if self.previous_state is not None:
            # Check that we're not transitioning out of a terminal state
            if OrderLifecycleState.is_terminal(self.previous_state):
                if self.previous_state != self.new_state:
                    raise ValueError(
                        f"Cannot transition from terminal state {self.previous_state} "
                        f"to {self.new_state}"
                    )

    @classmethod
    def create_state_change(
        cls,
        order_id: OrderId,
        previous_state: OrderLifecycleState | None,
        new_state: OrderLifecycleState,
        event_type: LifecycleEventType = LifecycleEventType.STATE_CHANGED,
        metadata: Mapping[str, Any] | None = None,
        timestamp: datetime | None = None,
    ) -> OrderLifecycleEvent:
        """Convenience factory method for creating state change events.

        Args:
            order_id: Unique identifier for the order
            previous_state: Previous lifecycle state (None for initial)
            new_state: New lifecycle state
            event_type: Type of lifecycle event (defaults to STATE_CHANGED)
            metadata: Additional contextual data
            timestamp: Event timestamp (defaults to current UTC time)

        Returns:
            New OrderLifecycleEvent instance

        """
        if timestamp is None:
            timestamp = datetime.now(UTC)

        if metadata is None:
            metadata = {}

        return cls(
            order_id=order_id,
            previous_state=previous_state,
            new_state=new_state,
            timestamp=timestamp,
            event_type=event_type,
            metadata=metadata,
        )

    def is_terminal_transition(self) -> bool:
        """Check if this event represents a transition to a terminal state."""
        return OrderLifecycleState.is_terminal(self.new_state)

    def is_error_transition(self) -> bool:
        """Check if this event represents an error transition."""
        return self.event_type in {
            LifecycleEventType.ERROR,
            LifecycleEventType.REJECTED,
            LifecycleEventType.TIMEOUT,
        }

    def is_success_transition(self) -> bool:
        """Check if this event represents successful order completion."""
        return (
            self.new_state in OrderLifecycleState.successful_terminal_states()
            and not self.is_error_transition()
        )
