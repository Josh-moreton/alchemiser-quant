"""Logging context utilities for request/task scoped data."""

from __future__ import annotations

import contextlib
import contextvars
import uuid
from collections.abc import Iterator
from typing import Any

_context: contextvars.ContextVar[dict[str, Any] | None] = contextvars.ContextVar(
    "alchemiser_logging_context", default=None
)


def get_context() -> dict[str, Any]:
    """Return the current logging context."""
    ctx = _context.get()
    return {} if ctx is None else ctx


def bind(**kwargs: Any) -> None:
    """Bind key/value pairs to the logging context."""
    current = get_context().copy()
    current.update({k: v for k, v in kwargs.items() if v is not None})
    _context.set(current)


@contextlib.contextmanager
def context(**kwargs: Any) -> Iterator[None]:
    """Context manager to temporarily bind values to the logging context."""
    token = _context.set({**get_context(), **{k: v for k, v in kwargs.items() if v is not None}})
    try:
        yield
    finally:
        _context.reset(token)


def ensure_correlation_id() -> str:
    """Ensure a correlation_id exists in the context and return it."""
    ctx = get_context()
    cid = ctx.get("correlation_id")
    if cid is None:
        cid = str(uuid.uuid4())
        bind(correlation_id=cid)
    return cid
