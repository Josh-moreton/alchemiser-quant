"""Business Unit: shared | Status: current.

Structlog configuration for the Alchemiser trading platform.

This module provides structlog configuration including custom processors for
Alchemiser-specific context, Decimal serialization, and output formatting.
Output format is either JSON (production) or console (development), controlled
by the structured_format parameter - these formats are mutually exclusive.
"""

from __future__ import annotations

import logging
import sys
from dataclasses import asdict, is_dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
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
    event_dict: dict[str, Any],
) -> dict[str, Any]:
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

    # Keep strict behavior for unsupported types
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def configure_structlog(
    *,
    structured_format: bool = True,
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
    file_path: str | None = None,
) -> None:
    """Configure structlog with stdlib logging handlers for proper console/file separation.

    This follows the proper pattern: let stdlib logging handle routing to different
    handlers with different levels, while structlog handles formatting.

    Args:
        structured_format: If True, use JSON for file output; if False, use human-readable
        console_level: Log level for console output (INFO keeps terminal clean)
        file_level: Log level for file output (DEBUG captures everything)
        file_path: Optional file path for logging. If None, only console logging is used.
                   In development, typically set to 'logs/trade_run.log'.

    """
    # Set up stdlib logging handlers first
    root_logger = logging.getLogger()

    # Set root logger to the minimum of configured levels to allow filtering at handler level
    # If no file logging, only console level matters
    effective_min_level = console_level if file_path is None else min(console_level, file_level)
    root_logger.setLevel(effective_min_level)
    root_logger.handlers.clear()  # Clear any existing handlers

    # Console handler with configured level
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(logging.Formatter("%(message)s"))  # Just the message
    root_logger.addHandler(console_handler)

    # File handler (DEBUG+ for detailed logs)
    # In AWS Lambda, the filesystem is read-only except for /tmp. Avoid creating files unless
    # a writable path is explicitly provided via environment or caller.
    if file_path:
        try:
            log_path = Path(file_path)
            # Only attempt to create dirs if parent is writable
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(file_path)
            file_handler.setLevel(file_level)
            file_handler.setFormatter(logging.Formatter("%(message)s"))  # Structlog formats
            root_logger.addHandler(file_handler)
        except OSError as e:
            # Fall back to console-only if file logging setup fails (e.g., read-only FS)
            # Log to console handler which is already configured
            root_logger.warning(
                "Failed to configure file logging at %s: %s. Falling back to console-only logging.",
                file_path,
                e,
            )

    # Configure structlog processors
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
        # Pretty exceptions are handled by renderers; include exc_info via logger when needed
    ]

    if structured_format:
        # JSON output for production/file logging
        processors.append(structlog.processors.JSONRenderer(default=decimal_serializer))
    else:
        # Human-readable output for development
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
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
