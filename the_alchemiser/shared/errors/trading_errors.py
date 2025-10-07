"""Business Unit: shared | Status: current.

Trading error classification for error handling.

This module provides OrderError for order-specific exceptions and classify_exception
for runtime exception categorization. For order execution errors with richer context
(symbol, quantity, price), consider using OrderExecutionError from shared.errors.exceptions.
"""

from __future__ import annotations

from typing import Any, Literal

from .exceptions import AlchemiserError


class OrderError(AlchemiserError):
    """Error related to order processing and execution.

    Use this exception for general order-related failures when you need to track
    an order_id. For more detailed order execution failures with symbol, quantity,
    and price information, use OrderExecutionError from shared.errors.exceptions.

    Pre-conditions:
        - message must be a non-empty string describing the error
        - order_id should be the broker's order identifier when available
        - context dict should not contain sensitive data (tokens, keys, etc.)

    Post-conditions:
        - order_id is stored both as an attribute and in the context dict (if provided)
        - context dict is never None (defaults to empty dict)
        - timestamp is set by parent AlchemiserError class

    Examples:
        >>> error = OrderError("Order timeout", order_id="abc-123")
        >>> print(error.order_id)
        abc-123
        >>> print(error.context)
        {'order_id': 'abc-123'}

        >>> context = {"symbol": "AAPL", "reason": "insufficient_funds"}
        >>> error = OrderError("Order rejected", order_id="xyz-789", context=context)
        >>> error.context["symbol"]
        'AAPL'

    """

    def __init__(
        self, message: str, order_id: str | None = None, context: dict[str, Any] | None = None
    ) -> None:
        """Initialize order error with optional order identifier and context.

        Args:
            message: Human-readable error description
            order_id: Optional order identifier from broker/exchange
            context: Additional error context (symbol, quantity, etc.). Will be
                    updated with order_id if provided.

        Raises:
            No exceptions raised during initialization. Invalid types will cause
            runtime errors in parent class or attribute access.

        Note:
            If order_id is provided, it will be added to the context dict with
            key "order_id", potentially overwriting any existing value.

        """
        context = context or {}
        if order_id:
            context["order_id"] = order_id
        super().__init__(message, context)
        self.order_id = order_id


def classify_exception(
    exception: Exception,
) -> Literal["order_error", "alchemiser_error", "general_error"]:
    """Classify an exception into error categories for error handling.

    This function provides runtime exception classification for use in error
    handlers and logging. The classification follows the exception hierarchy,
    checking most specific types first.

    Args:
        exception: Exception instance to classify

    Returns:
        One of:
        - "order_error": For OrderError instances
        - "alchemiser_error": For AlchemiserError instances (excluding OrderError)
        - "general_error": For all other exceptions (ValueError, RuntimeError, etc.)

    Examples:
        >>> classify_exception(OrderError("test"))
        'order_error'
        >>> classify_exception(AlchemiserError("test"))
        'alchemiser_error'
        >>> classify_exception(ValueError("test"))
        'general_error'

    Note:
        Classification checks are ordered by specificity. OrderError is checked
        before AlchemiserError since OrderError extends AlchemiserError.

    """
    if isinstance(exception, OrderError):
        return "order_error"
    if isinstance(exception, AlchemiserError):
        return "alchemiser_error"
    return "general_error"
