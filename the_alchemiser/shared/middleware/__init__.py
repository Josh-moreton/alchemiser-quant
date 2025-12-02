"""Business Unit: shared | Status: current.

FastAPI middleware utilities shared across services.
"""

from .correlation import CorrelationIdMiddleware, resolve_trace_context

__all__ = ["CorrelationIdMiddleware", "resolve_trace_context"]
