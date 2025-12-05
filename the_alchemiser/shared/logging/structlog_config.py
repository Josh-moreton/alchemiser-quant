"""Business Unit: shared | Status: current.

Structlog configuration for the Alchemiser trading platform.

This module provides structlog configuration including custom processors for
Alchemiser-specific context, Decimal serialization, and output formatting.
Output format is always human-readable (ConsoleRenderer) across all
environments.
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
    """Serialize common domain types into human-friendly forms.

    Supports common domain types used in The Alchemiser so logging never crashes:
    - Decimal -> str (preserve precision)
    - Symbol (dataclass) -> underlying string value
    - Dataclass instances -> asdict conversion
    - Pydantic-like models (model_dump) -> dumped dict
    - Sets/Tuples -> list
    - datetime -> ISO 8601 string

    For unknown types, return the original object (ConsoleRenderer can handle many
    builtin types and we prefer not to throw while logging).
    """
    if isinstance(obj, Decimal):
        return str(obj)

    if isinstance(obj, Symbol):
        return obj.value

    if is_dataclass(obj) and not isinstance(obj, type):
        return asdict(obj)

    model_dump = getattr(obj, "model_dump", None)
    if callable(model_dump):
        try:
            return model_dump()
        except (TypeError, ValueError, AttributeError) as e:
            logging.getLogger(__name__).debug(
                "Failed to serialize Pydantic model via model_dump: %s. Falling back to str().",
                e,
                extra={"object_type": type(obj).__name__},
            )
            return str(obj)

    if isinstance(obj, set | tuple):
        return list(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()

    return obj


def normalize_event_values(
    logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Normalize event values for human-readable logging without failing serialization."""
    normalized: dict[str, Any] = {}
    for key, value in event_dict.items():
        try:
            normalized[key] = decimal_serializer(value)
        except Exception:
            normalized[key] = value
    return normalized


def configure_structlog(
    *,
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
    file_path: str | None = None,
) -> None:
    """Configure structlog with human-readable output for console and optional file.

    Args:
        console_level: Log level for console output (INFO keeps terminal clean)
        file_level: Log level for file output (DEBUG captures everything)
        file_path: Optional file path for logging. If None, only console logging is used.
                   In development, typically set to 'logs/trade_run.log'.

    """
    root_logger = logging.getLogger()
    min_level = min(console_level, file_level) if file_path else console_level
    root_logger.setLevel(min_level)
    root_logger.handlers.clear()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(logging.Formatter("%(message)s"))
    root_logger.addHandler(console_handler)

    if file_path:
        try:
            log_path = Path(file_path)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(file_path)
            file_handler.setLevel(file_level)
            file_handler.setFormatter(logging.Formatter("%(message)s"))
            root_logger.addHandler(file_handler)
        except OSError as e:
            root_logger.warning(
                "Failed to configure file logging at %s: %s. Falling back to console-only logging.",
                file_path,
                e,
            )

    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        add_alchemiser_context,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        normalize_event_values,
        structlog.dev.ConsoleRenderer(),
    ]

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
