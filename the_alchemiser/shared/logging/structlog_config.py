"""Business Unit: shared | Status: current.

Structlog configuration for the Alchemiser trading platform.

This module provides structlog configuration including custom processors for
Alchemiser-specific context, Decimal serialization, and both JSON and console output.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

import structlog

from .context import error_id_context, request_id_context


def add_alchemiser_context(
    logger: Any,  # noqa: ANN401
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Add Alchemiser-specific context to log entries.

    Args:
        logger: The logger instance (unused but required by structlog)
        method_name: The method name (unused but required by structlog)
        event_dict: The event dictionary to augment

    Returns:
        Augmented event dictionary with context variables

    """
    # Add context variables from contextvars
    request_id = request_id_context.get()
    if request_id:
        event_dict["request_id"] = request_id

    error_id = error_id_context.get()
    if error_id:
        event_dict["error_id"] = error_id

    # Add system identifier
    event_dict["system"] = "alchemiser"

    return event_dict


def decimal_serializer(obj: Any) -> Any:  # noqa: ANN401
    """Serialize Decimal objects for JSON output.

    Args:
        obj: Object to serialize

    Returns:
        String representation of Decimal, or raises TypeError for unsupported types

    Raises:
        TypeError: If object type is not JSON serializable

    """
    if isinstance(obj, Decimal):
        return str(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def configure_structlog(
    *,
    structured_format: bool = True,
    log_level: int = logging.INFO,
) -> None:
    """Configure structlog with Alchemiser-specific processors.

    Args:
        structured_format: If True, use JSON output; if False, use human-readable console output
        log_level: Minimum log level to output

    """
    processors: list[Any] = [
        # Merge context variables automatically
        structlog.contextvars.merge_contextvars,
        # Add our custom context
        add_alchemiser_context,
        # Add timestamp in ISO format
        structlog.processors.TimeStamper(fmt="iso"),
        # Add log level
        structlog.processors.add_log_level,
        # Add caller info for debugging
        structlog.processors.StackInfoRenderer(),
        # Add exception info
        structlog.processors.format_exc_info,
    ]

    if structured_format:
        # JSON output for production
        processors.append(structlog.processors.JSONRenderer(default=decimal_serializer))
    else:
        # Human-readable output for development
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_structlog_logger(name: str) -> Any:  # noqa: ANN401
    """Get a structlog logger instance.

    Args:
        name: Logger name, typically __name__ for module-level logging

    Returns:
        Configured structlog logger instance

    """
    return structlog.get_logger(name)
