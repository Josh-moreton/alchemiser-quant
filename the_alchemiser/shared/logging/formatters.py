"""Business Unit: shared | Status: current.

Custom formatters and adapters for logging system.

This module provides custom logging formatters including JSON structured logging
and the AlchemiserLoggerAdapter for consistent message formatting across the system.
"""

from __future__ import annotations

import json
import logging
from collections.abc import MutableMapping
from datetime import UTC, datetime

from .context import error_id_context, request_id_context


class AlchemiserLoggerAdapter(logging.LoggerAdapter[logging.Logger]):
    """Custom logger adapter for the Alchemiser quantitative trading system."""

    def process(
        self, msg: object, kwargs: MutableMapping[str, object]
    ) -> tuple[str, MutableMapping[str, object]]:
        """Prefix log messages with system identifier and add context IDs."""
        # Get context variables
        request_id = request_id_context.get()
        error_id = error_id_context.get()

        # Build context suffix
        context_parts = []
        if request_id:
            context_parts.append(f"req_id={request_id}")
        if error_id:
            context_parts.append(f"error_id={error_id}")

        context_suffix = f" [{', '.join(context_parts)}]" if context_parts else ""

        return f"[ALCHEMISER]{context_suffix} {msg}", kwargs


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Convert a log record into a JSON string."""
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add request_id and error_id from context vars if present
        request_id = request_id_context.get()
        if request_id:
            log_entry["request_id"] = request_id

        error_id = error_id_context.get()
        if error_id:
            log_entry["error_id"] = error_id

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info),
            }

        # Add extra fields if present
        extra_fields = getattr(record, "extra_fields", None)
        if extra_fields:
            log_entry.update(extra_fields)

        return json.dumps(log_entry, default=str)


def _create_formatter(*, structured_format: bool) -> logging.Formatter:
    """Create appropriate formatter based on format setting."""
    if structured_format:
        return StructuredFormatter()
    log_format = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    return logging.Formatter(log_format)
