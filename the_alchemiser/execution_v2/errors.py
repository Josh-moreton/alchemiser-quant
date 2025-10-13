"""Business Unit: execution | Status: current.

Execution-specific error types for typed exception handling.

This module provides execution_v2-specific error types that extend the shared
error hierarchy. These errors support correlation_id and causation_id for
event-driven workflows and provide structured context for observability.

All exceptions extend AlchemiserError and support:
- correlation_id: Track requests across the system
- causation_id: Link events in event-driven workflows
- context: Additional error metadata (symbol, quantity, price, etc.)
- to_dict(): Serialize for structured logging

Example:
    >>> try:
    ...     raise ExecutionValidationError(
    ...         "Invalid order quantity",
    ...         symbol="AAPL",
    ...         quantity="0",
    ...         correlation_id="order-123",
    ...     )
    ... except ExecutionError as e:
    ...     logger.error("Execution error", extra=e.to_dict())

"""

from __future__ import annotations

from typing import Any

from the_alchemiser.shared.errors.exceptions import AlchemiserError


class ExecutionError(AlchemiserError):
    """Base error for execution_v2 module.

    All execution_v2-specific errors should inherit from this class.
    Supports correlation tracking and structured context for observability.
    """

    def __init__(
        self,
        message: str,
        correlation_id: str | None = None,
        causation_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Initialize execution error with tracking IDs.

        Args:
            message: Human-readable error description
            correlation_id: Correlation ID for request tracing
            causation_id: Causation ID for event tracing
            context: Additional error context (symbol, quantity, etc.)

        """
        context = context or {}
        if correlation_id:
            context["correlation_id"] = correlation_id
        if causation_id:
            context["causation_id"] = causation_id
        super().__init__(message, context)
        self.correlation_id = correlation_id
        self.causation_id = causation_id


class ExecutionValidationError(ExecutionError):
    """Error during order validation before execution.

    Raised when order validation fails (quantity, price, symbol checks).
    """


class QuoteValidationError(ExecutionError):
    """Error during quote validation or acquisition.

    Raised when market quote validation fails or quotes cannot be obtained.
    """


class OrderPlacementError(ExecutionError):
    """Error during order placement with broker.

    Raised when broker order placement fails (timeout, rejection, API error).
    """


class ExecutionTimeoutError(ExecutionError):
    """Error when execution operations exceed timeout limits.

    Raised when order placement, quote retrieval, or other operations timeout.
    """
