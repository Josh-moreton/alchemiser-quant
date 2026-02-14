"""Business Unit: shared | Status: current.

Structlog configuration for the Alchemiser trading platform.

This module provides structlog configuration including custom processors for
Alchemiser-specific context, Decimal serialization, and output formatting.
Output format is either JSON (Lambda environments) or human-readable console
(local development), controlled by the use_json parameter.
"""

from __future__ import annotations

import logging
import sys
from collections.abc import MutableMapping
from dataclasses import asdict, is_dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

import structlog

from the_alchemiser.shared.value_objects.symbol import Symbol

from .context import (
    causation_id_context,
    correlation_id_context,
    error_id_context,
    request_id_context,
)


def add_alchemiser_context(
    logger: Any,  # noqa: ANN401
    method_name: str,
    event_dict: MutableMapping[str, Any],
) -> MutableMapping[str, Any]:
    """Add Alchemiser-specific context to log entries.

    Includes request tracking IDs and event-driven workflow tracing IDs for
    comprehensive observability across the trading platform.

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

    correlation_id = correlation_id_context.get()
    if correlation_id:
        event_dict["correlation_id"] = correlation_id

    causation_id = causation_id_context.get()
    if causation_id:
        event_dict["causation_id"] = causation_id

    # Add system identifier
    event_dict["system"] = "alchemiser"

    return event_dict


def decimal_serializer(obj: Any) -> Any:  # noqa: ANN401
    """Provide default JSON serialization for structlog JSONRenderer.

    Supports common domain types used in The Alchemiser so logging never crashes:
    - Decimal -> str (preserve precision)
    - Symbol (dataclass) -> underlying string value
    - Dataclass instances -> asdict conversion
    - Pydantic-like models (model_dump) -> dumped dict
    - Sets/Tuples -> list
    - datetime -> ISO 8601 string

    For unknown types, raise TypeError to let json detect unsupported objects (maintains tests).
    """
    # Precise numbers
    if isinstance(obj, Decimal):
        return str(obj)

    # Domain value objects
    if isinstance(obj, Symbol):
        return obj.value

    # Dataclasses
    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)

    # Pydantic-like objects without importing pydantic directly
    model_dump = getattr(obj, "model_dump", None)
    if callable(model_dump):
        try:
            return model_dump()
        except (TypeError, ValueError, AttributeError) as e:
            # Log the error for debugging but continue with fallback
            # Use stdlib logging since structlog may not be configured yet
            logging.getLogger(__name__).debug(
                "Failed to serialize Pydantic model via model_dump: %s. Falling back to str().",
                e,
                extra={"object_type": type(obj).__name__},
            )
            return str(obj)

    # Common container/temporal types
    if isinstance(obj, set | tuple):
        return list(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()

    # Exception instances - serialize to dict with type and message
    if isinstance(obj, Exception):
        result: dict[str, Any] = {
            "type": type(obj).__name__,
            "message": str(obj),
        }
        # Include context if available (e.g., AlchemiserError subclasses)
        if hasattr(obj, "context") and obj.context:
            result["context"] = obj.context
        return result

    # Keep strict behavior for unsupported types
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def configure_structlog_lambda() -> None:
    """Configure structlog for AWS Lambda with JSON output to CloudWatch.

    This is the only configuration needed for Lambda. All logs are emitted at DEBUG
    level and sent to CloudWatch. Use CloudWatch Insights to filter by level at
    query time (e.g., filter level in ["info", "warning", "error"]).

    Design:
        - Emit ALL logs (DEBUG+) to CloudWatch
        - JSON format for CloudWatch Insights queryability
        - No timestamps (CloudWatch adds its own)
        - No colors (CloudWatch doesn't render ANSI)
        - Filter at read-time in CloudWatch, not at write-time

    Environment Variables:
        ALCHEMISER_LOG_LEVEL: Override log level (DEBUG, INFO, WARNING, ERROR).
                              Useful for scripts/dashboards that want less noise.

    """
    import os

    # Check for log level override (useful for dashboard/scripts)
    level_name = os.environ.get("ALCHEMISER_LOG_LEVEL", "DEBUG").upper()
    log_level = getattr(logging, level_name, logging.DEBUG)

    # Set up stdlib logging - emit everything, let CloudWatch filter
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()

    # Single handler: stdout -> CloudWatch
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    handler.setFormatter(logging.Formatter("%(message)s"))
    root_logger.addHandler(handler)

    # Configure structlog with JSON output
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            add_alchemiser_context,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            # No timestamp - CloudWatch adds its own
            structlog.processors.JSONRenderer(default=decimal_serializer),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def configure_structlog_test(log_level: int = logging.WARNING) -> None:
    """Configure structlog for tests with human-readable output.

    Args:
        log_level: Minimum log level to display (default: WARNING to reduce noise).

    """
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    handler.setFormatter(logging.Formatter("%(message)s"))
    root_logger.addHandler(handler)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            add_alchemiser_context,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(colors=True),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
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
