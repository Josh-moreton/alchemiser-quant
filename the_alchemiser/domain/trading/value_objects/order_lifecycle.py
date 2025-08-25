"""Order lifecycle state management for trading operations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from the_alchemiser.domain.shared_kernel.value_objects.money import Money
from the_alchemiser.domain.trading.value_objects.order_id import OrderId
from the_alchemiser.domain.trading.value_objects.quantity import Quantity
from the_alchemiser.domain.trading.value_objects.symbol import Symbol


class OrderLifecycleState(str, Enum):
    """Comprehensive order lifecycle states."""

    # Initial states
    NEW = "new"
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"

    # Active states
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"

    # Modification states
    PENDING_REPLACE = "pending_replace"
    REPLACED = "replaced"

    # Terminal states
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"

    # Error states
    ERROR = "error"
    TIMEOUT = "timeout"

    @property
    def is_terminal(self) -> bool:
        """Check if this is a terminal state."""
        return self in {
            OrderLifecycleState.FILLED,
            OrderLifecycleState.CANCELLED,
            OrderLifecycleState.REJECTED,
            OrderLifecycleState.EXPIRED,
            OrderLifecycleState.ERROR,
            OrderLifecycleState.TIMEOUT,
        }

    @property
    def is_active(self) -> bool:
        """Check if order is actively trading."""
        return self in {
            OrderLifecycleState.SUBMITTED,
            OrderLifecycleState.ACKNOWLEDGED,
            OrderLifecycleState.PARTIALLY_FILLED,
            OrderLifecycleState.PENDING_REPLACE,
        }


class OrderEventType(str, Enum):
    """Types of order lifecycle events."""

    SUBMIT = "submit"
    ACK = "ack"
    PARTIAL_FILL = "partial_fill"
    FILL = "fill"
    CANCEL = "cancel"
    REPLACE = "replace"
    REJECT = "reject"
    EXPIRE = "expire"
    ERROR = "error"
    TIMEOUT = "timeout"


@dataclass(frozen=True)
class OrderLifecycleEvent:
    """Immutable order lifecycle event."""

    event_type: OrderEventType
    order_id: OrderId
    timestamp: datetime
    state_before: OrderLifecycleState
    state_after: OrderLifecycleState
    details: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None

    def __post_init__(self) -> None:
        """Validate event consistency."""
        if self.event_type == OrderEventType.ERROR and self.error_message is None:
            raise ValueError("Error events must include error_message")


@dataclass
class OrderLifecycle:
    """Mutable order lifecycle tracker with comprehensive state management."""

    order_id: OrderId
    symbol: Symbol
    side: str
    quantity: Quantity
    order_type: str
    limit_price: Money | None = None
    
    # Lifecycle state
    current_state: OrderLifecycleState = OrderLifecycleState.NEW
    
    # Execution tracking
    filled_quantity: Quantity = field(default_factory=lambda: Quantity(Decimal("0")))
    average_fill_price: Money | None = None
    
    # Timing
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_updated: datetime = field(default_factory=lambda: datetime.now(UTC))
    
    # Event history
    events: list[OrderLifecycleEvent] = field(default_factory=list)
    
    # Retry tracking
    attempt_count: int = 0
    repeg_count: int = 0
    
    # Error tracking
    last_error: str | None = None
    error_count: int = 0

    def transition_to(
        self,
        new_state: OrderLifecycleState,
        event_type: OrderEventType,
        details: dict[str, Any] | None = None,
        error_message: str | None = None,
    ) -> None:
        """Transition to a new state with proper event logging."""
        old_state = self.current_state
        
        # Validate transition
        if not self._is_valid_transition(old_state, new_state):
            raise ValueError(f"Invalid transition from {old_state} to {new_state}")
        
        # Create event
        event = OrderLifecycleEvent(
            event_type=event_type,
            order_id=self.order_id,
            timestamp=datetime.now(UTC),
            state_before=old_state,
            state_after=new_state,
            details=details or {},
            error_message=error_message,
        )
        
        # Update state
        self.current_state = new_state
        self.last_updated = event.timestamp
        self.events.append(event)
        
        # Update error tracking
        if event_type == OrderEventType.ERROR:
            self.error_count += 1
            self.last_error = error_message

    def add_partial_fill(
        self,
        fill_quantity: Quantity,
        fill_price: Money,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Record a partial fill."""
        if fill_quantity.value <= 0:
            raise ValueError("Fill quantity must be positive")
        
        new_filled = Quantity(self.filled_quantity.value + fill_quantity.value)
        if new_filled.value > self.quantity.value:
            raise ValueError("Total filled quantity cannot exceed order quantity")
        
        # Update filled quantity and average price
        self.filled_quantity = new_filled
        if self.average_fill_price is None:
            self.average_fill_price = fill_price
        else:
            # Calculate new weighted average
            total_value = (
                self.average_fill_price.value * (self.filled_quantity.value - fill_quantity.value) +
                fill_price.value * fill_quantity.value
            )
            self.average_fill_price = Money(total_value / self.filled_quantity.value)
        
        # Determine new state
        if self.filled_quantity.value == self.quantity.value:
            new_state = OrderLifecycleState.FILLED
            event_type = OrderEventType.FILL
        else:
            new_state = OrderLifecycleState.PARTIALLY_FILLED
            event_type = OrderEventType.PARTIAL_FILL
        
        # Add fill details
        fill_details = {
            "fill_quantity": str(fill_quantity.value),
            "fill_price": str(fill_price.value),
            "total_filled": str(self.filled_quantity.value),
            "average_price": str(self.average_fill_price.value),
            **(details or {}),
        }
        
        self.transition_to(new_state, event_type, fill_details)

    def increment_repeg(self) -> None:
        """Increment re-peg counter."""
        self.repeg_count += 1

    def increment_attempt(self) -> None:
        """Increment attempt counter."""
        self.attempt_count += 1

    @property
    def remaining_quantity(self) -> Quantity:
        """Calculate remaining unfilled quantity."""
        return Quantity(self.quantity.value - self.filled_quantity.value)

    @property
    def fill_percentage(self) -> Decimal:
        """Calculate fill percentage."""
        if self.quantity.value == 0:
            return Decimal("0")
        return (self.filled_quantity.value / self.quantity.value) * Decimal("100")

    @property
    def is_terminal(self) -> bool:
        """Check if order is in terminal state."""
        return self.current_state.is_terminal

    @property
    def is_active(self) -> bool:
        """Check if order is actively trading."""
        return self.current_state.is_active

    def _is_valid_transition(
        self, from_state: OrderLifecycleState, to_state: OrderLifecycleState
    ) -> bool:
        """Validate state transition rules."""
        # Terminal states cannot transition
        if from_state.is_terminal:
            return False
        
        # Define valid transitions
        valid_transitions = {
            OrderLifecycleState.NEW: {
                OrderLifecycleState.SUBMITTED,
                OrderLifecycleState.ERROR,
            },
            OrderLifecycleState.SUBMITTED: {
                OrderLifecycleState.ACKNOWLEDGED,
                OrderLifecycleState.REJECTED,
                OrderLifecycleState.ERROR,
                OrderLifecycleState.TIMEOUT,
            },
            OrderLifecycleState.ACKNOWLEDGED: {
                OrderLifecycleState.PARTIALLY_FILLED,
                OrderLifecycleState.FILLED,
                OrderLifecycleState.CANCELLED,
                OrderLifecycleState.PENDING_REPLACE,
                OrderLifecycleState.ERROR,
                OrderLifecycleState.TIMEOUT,
            },
            OrderLifecycleState.PARTIALLY_FILLED: {
                OrderLifecycleState.FILLED,
                OrderLifecycleState.CANCELLED,
                OrderLifecycleState.PENDING_REPLACE,
                OrderLifecycleState.ERROR,
                OrderLifecycleState.TIMEOUT,
            },
            OrderLifecycleState.PENDING_REPLACE: {
                OrderLifecycleState.REPLACED,
                OrderLifecycleState.ACKNOWLEDGED,
                OrderLifecycleState.REJECTED,
                OrderLifecycleState.ERROR,
                OrderLifecycleState.TIMEOUT,
            },
            OrderLifecycleState.REPLACED: {
                OrderLifecycleState.ACKNOWLEDGED,
                OrderLifecycleState.REJECTED,
                OrderLifecycleState.ERROR,
            },
        }
        
        return to_state in valid_transitions.get(from_state, set())