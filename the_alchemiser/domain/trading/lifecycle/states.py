"""Order lifecycle state enumeration."""

from __future__ import annotations

from enum import Enum


class OrderLifecycleState(str, Enum):
    """
    Comprehensive order lifecycle states covering the complete order progression.
    
    This enum defines the 12 possible states an order can be in during its lifecycle,
    from initial creation through final resolution. States are designed to enable
    rich observability and proper state transition validation.
    
    Terminal States: FILLED, CANCELLED, REJECTED, EXPIRED, ERROR
    - Orders in terminal states cannot transition to any other state
    
    State Progression Overview:
    NEW -> VALIDATED -> QUEUED -> SUBMITTED -> ACKNOWLEDGED -> PARTIALLY_FILLED/FILLED
    
    Error/Cancellation paths available from most non-terminal states.
    """
    
    # Initial states
    NEW = "NEW"                          # Order created but not yet validated
    VALIDATED = "VALIDATED"              # Order passed validation checks
    
    # Queueing and submission
    QUEUED = "QUEUED"                    # Order queued for submission (throttling, timing)
    SUBMITTED = "SUBMITTED"              # Order sent to broker/exchange
    ACKNOWLEDGED = "ACKNOWLEDGED"        # Broker confirmed receipt and accepted order
    
    # Execution states  
    PARTIALLY_FILLED = "PARTIALLY_FILLED"  # Order partially executed
    FILLED = "FILLED"                      # Order completely executed (terminal)
    
    # Cancellation states
    CANCEL_PENDING = "CANCEL_PENDING"    # Cancel request sent but not confirmed
    CANCELLED = "CANCELLED"              # Order successfully cancelled (terminal)
    
    # Error/rejection states
    REJECTED = "REJECTED"                # Broker/exchange rejected order (terminal)
    EXPIRED = "EXPIRED"                  # Order expired (GTC/Day expiry) (terminal)
    ERROR = "ERROR"                      # Unrecoverable error occurred (terminal)
    
    @classmethod
    def terminal_states(cls) -> set[OrderLifecycleState]:
        """Return the set of terminal states that allow no further transitions."""
        return {cls.FILLED, cls.CANCELLED, cls.REJECTED, cls.EXPIRED, cls.ERROR}
    
    @classmethod
    def is_terminal(cls, state: OrderLifecycleState) -> bool:
        """Check if the given state is terminal (no further transitions allowed)."""
        return state in cls.terminal_states()
    
    @classmethod
    def successful_terminal_states(cls) -> set[OrderLifecycleState]:
        """Return terminal states that represent successful order completion."""
        return {cls.FILLED}
    
    @classmethod 
    def failed_terminal_states(cls) -> set[OrderLifecycleState]:
        """Return terminal states that represent order failure."""
        return {cls.CANCELLED, cls.REJECTED, cls.EXPIRED, cls.ERROR}