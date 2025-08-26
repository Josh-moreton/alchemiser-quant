"""Order lifecycle management exceptions."""

from __future__ import annotations

from typing import Any

from .states import OrderLifecycleState


class InvalidOrderStateTransitionError(Exception):
    """
    Exception raised when an invalid order state transition is attempted.

    This exception is raised when code attempts to transition an order from
    one lifecycle state to another when that transition is not allowed by
    the state machine rules.
    """

    def __init__(
        self,
        from_state: OrderLifecycleState,
        to_state: OrderLifecycleState,
        order_id: str | None = None,
        reason: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize the invalid transition exception.

        Args:
            from_state: The state being transitioned from
            to_state: The state being transitioned to
            order_id: Optional order identifier for context
            reason: Optional human-readable reason for the failure
            context: Optional additional context data
        """
        self.from_state = from_state
        self.to_state = to_state
        self.order_id = order_id
        self.reason = reason
        self.context = context or {}

        # Build descriptive error message
        message_parts = [f"Invalid order state transition from {from_state} to {to_state}"]

        if order_id:
            message_parts.append(f"for order {order_id}")

        if reason:
            message_parts.append(f": {reason}")
        else:
            message_parts.append(": transition not allowed by state machine rules")

        message = " ".join(message_parts)
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert exception to structured data for logging/reporting.

        Returns:
            Dictionary representation of the exception
        """
        return {
            "error_type": self.__class__.__name__,
            "from_state": self.from_state.value,
            "to_state": self.to_state.value,
            "order_id": self.order_id,
            "reason": self.reason,
            "context": self.context,
        }
