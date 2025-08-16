"""Structured logging configuration for The Alchemiser."""

from __future__ import annotations

import json
import logging
import os
import platform
import re
import socket
from datetime import UTC, datetime
from typing import Any

from opentelemetry.trace import get_current_span
from pythonjsonlogger import jsonlogger

from .context import bind, ensure_correlation_id, get_context

# Redaction patterns for secrets/PII
_REDACTION_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS access key
    re.compile(r"(?i)bearer\s+[A-Za-z0-9\-\.]+"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    re.compile(r"\b(?:\d[ -]*?){13,16}\b"),  # credit card like
    re.compile(r"[A-Z]{2}[0-9A-Z]{13,32}"),  # IBAN-ish
]


def _redact(value: str) -> str:
    for pattern in _REDACTION_PATTERNS:
        value = pattern.sub("***REDACTED***", value)
    return value


def _redact_dict(data: dict[str, Any]) -> None:
    for key, val in list(data.items()):
        if isinstance(val, dict):
            _redact_dict(val)
        elif isinstance(val, str):
            data[key] = _redact(val)


def _ensure_serialisable(value: Any) -> Any:
    try:
        json.dumps(value)
        return value
    except Exception:
        return repr(value)


class ECSJsonFormatter(jsonlogger.JsonFormatter):  # type: ignore[misc]
    """JSON formatter emitting ECS-ish records."""

    def add_fields(
        self, log_record: dict[str, Any], record: logging.LogRecord, message_dict: dict[str, Any]
    ) -> None:
        super().add_fields(log_record, record, message_dict)

        log_record["@timestamp"] = (
            datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        )
        log_record["log.level"] = record.levelname
        log_record.setdefault("message", record.getMessage())

        # Merge context vars
        ctx = get_context()
        for key, val in ctx.items():
            if val is not None:
                log_record[key] = val

        # Service/environment metadata
        log_record.setdefault("process.pid", os.getpid())
        log_record.setdefault("host.name", socket.gethostname())
        log_record.setdefault("runtime", platform.python_version())

        # Trace / correlation
        span = get_current_span()
        span_ctx = span.get_span_context()
        if span_ctx and span_ctx.is_valid:
            log_record["trace.id"] = f"{span_ctx.trace_id:032x}"
            log_record["span.id"] = f"{span_ctx.span_id:016x}"
        else:
            log_record.setdefault("correlation_id", ensure_correlation_id())

        # Exception info
        if record.exc_info:
            exc_type, exc_val, exc_tb = record.exc_info
            log_record["error.kind"] = exc_type.__name__ if exc_type else None
            log_record["error.message"] = str(exc_val) if exc_val else None
            log_record["error.stack"] = self.formatException(record.exc_info)

        # Drop None values
        for key in list(log_record.keys()):
            if log_record[key] is None:
                del log_record[key]

        # Redact secrets
        _redact_dict(log_record)

        # Ensure serialisable
        for key, val in list(log_record.items()):
            log_record[key] = _ensure_serialisable(val)


def configure_logging(
    env: str = "DEV",
    level: str | None = None,
    service: str = "alchemiser",
    version: str = "",
    region: str = "",
) -> None:
    """Configure root logger for structured JSON output."""
    resolved_level = level or ("DEBUG" if env.upper() != "PROD" else "INFO")
    numeric_level = getattr(logging, resolved_level.upper(), logging.INFO)

    # Clear existing handlers
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)

    formatter = ECSJsonFormatter()
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.setLevel(numeric_level)
    root.addHandler(handler)
    root.setLevel(numeric_level)

    # Bind static context
    bind(
        service=service,
        env=env,
        region=region,
        version=version,
        **{"event.dataset": f"{service}.app"},
    )


def get_logger(name: str) -> logging.Logger:
    """Return a logger configured for the application."""
    return logging.getLogger(name)
