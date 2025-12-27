"""Business Unit: shared | Status: current.

Context management for logging system.

This module provides context variable management for request tracking and error tracking
across the logging infrastructure. Context variables are used to propagate request IDs
and error IDs through the logging system without requiring them to be passed explicitly.
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar

# Context variables for request tracking
request_id_context: ContextVar[str | None] = ContextVar("request_id", default=None)
error_id_context: ContextVar[str | None] = ContextVar("error_id", default=None)

# Context variables for event-driven workflow tracing
correlation_id_context: ContextVar[str | None] = ContextVar("correlation_id", default=None)
causation_id_context: ContextVar[str | None] = ContextVar("causation_id", default=None)


def set_request_id(request_id: str | None) -> None:
    """Set the request ID in the logging context.

    Args:
        request_id: The request ID to set, or None to clear

    Raises:
        This function does not raise exceptions.

    """
    request_id_context.set(request_id)


def set_error_id(error_id: str | None) -> None:
    """Set the error ID in the logging context.

    Args:
        error_id: The error ID to set, or None to clear

    Raises:
        This function does not raise exceptions.

    """
    error_id_context.set(error_id)


def get_request_id() -> str | None:
    """Get the current request ID from the logging context.

    Returns:
        The current request ID, or None if not set

    Raises:
        This function does not raise exceptions.

    """
    return request_id_context.get()


def get_error_id() -> str | None:
    """Get the current error ID from the logging context.

    Returns:
        The current error ID, or None if not set

    Raises:
        This function does not raise exceptions.

    """
    return error_id_context.get()


def set_correlation_id(correlation_id: str | None) -> None:
    """Set the correlation ID in the logging context.

    Args:
        correlation_id: The correlation ID to set, or None to clear

    Raises:
        This function does not raise exceptions.

    """
    correlation_id_context.set(correlation_id)


def get_correlation_id() -> str | None:
    """Get the current correlation ID from the logging context.

    Returns:
        The current correlation ID, or None if not set

    Raises:
        This function does not raise exceptions.

    """
    return correlation_id_context.get()


def set_causation_id(causation_id: str | None) -> None:
    """Set the causation ID in the logging context.

    Args:
        causation_id: The causation ID to set, or None to clear

    Raises:
        This function does not raise exceptions.

    """
    causation_id_context.set(causation_id)


def get_causation_id() -> str | None:
    """Get the current causation ID from the logging context.

    Returns:
        The current causation ID, or None if not set

    Raises:
        This function does not raise exceptions.

    """
    return causation_id_context.get()


def generate_request_id() -> str:
    """Generate a new request ID.

    Returns:
        A unique request ID string (UUID v4 format)

    Raises:
        This function does not raise exceptions.

    """
    return str(uuid.uuid4())
