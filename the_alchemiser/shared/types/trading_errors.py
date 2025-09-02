"""Business Unit: shared | Status: current

Trading error classification for error handling.
"""

from __future__ import annotations

from typing import Any

from the_alchemiser.shared.types.exceptions import AlchemiserError


class OrderError(AlchemiserError):
    """Error related to order processing and execution."""

    def __init__(
        self, message: str, order_id: str | None = None, context: dict[str, Any] | None = None
    ) -> None:
        """Initialize order error.

        Args:
            message: Error message
            order_id: Optional order identifier
            context: Additional error context

        """
        context = context or {}
        if order_id:
            context["order_id"] = order_id
        super().__init__(message, context)
        self.order_id = order_id


def classify_exception(exception: Exception) -> str:
    """Classify an exception for error handling.

    Args:
        exception: Exception to classify

    Returns:
        Classification string

    """
    if isinstance(exception, OrderError):
        return "order_error"
    if isinstance(exception, AlchemiserError):
        return "alchemiser_error"
    return "general_error"
