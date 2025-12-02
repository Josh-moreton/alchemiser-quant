"""Business Unit: shared | Status: current.

Correlation-aware middleware for FastAPI services.

The middleware standardizes propagation of request identifiers across logs and
emitted events by:
- Extracting correlation/causation IDs from incoming headers
- Falling back to generated identifiers when absent
- Storing identifiers on the request state for downstream handlers
- Injecting identifiers into the logging context for structured logs
"""

from __future__ import annotations

from uuid import uuid4

from fastapi import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send

from the_alchemiser.shared.logging import (
    set_causation_id,
    set_correlation_id,
    set_request_id,
)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Attach correlation and causation identifiers to request context."""

    def __init__(
        self,
        app: ASGIApp,
        correlation_header: str = "x-correlation-id",
        causation_header: str = "x-causation-id",
        request_header: str = "x-request-id",
    ) -> None:
        super().__init__(app)
        self.correlation_header = correlation_header
        self.causation_header = causation_header
        self.request_header = request_header

    async def dispatch(self, request: Request, call_next) -> object:
        correlation_id = request.headers.get(self.correlation_header) or request.headers.get(
            self.correlation_header.title()
        )
        causation_id = request.headers.get(self.causation_header) or request.headers.get(
            self.causation_header.title()
        )
        request_id = request.headers.get(self.request_header) or request.headers.get(
            self.request_header.title()
        )

        resolved_request_id = request_id or str(uuid4())
        resolved_correlation_id = correlation_id or resolved_request_id
        resolved_causation_id = causation_id or resolved_correlation_id

        set_request_id(resolved_request_id)
        set_correlation_id(resolved_correlation_id)
        set_causation_id(resolved_causation_id)

        request.state.request_id = resolved_request_id
        request.state.correlation_id = resolved_correlation_id
        request.state.causation_id = resolved_causation_id

        try:
            response = await call_next(request)
        finally:
            set_request_id(None)
            set_correlation_id(None)
            set_causation_id(None)

        response.headers.setdefault("X-Request-ID", resolved_request_id)
        response.headers.setdefault("X-Correlation-ID", resolved_correlation_id)
        response.headers.setdefault("X-Causation-ID", resolved_causation_id)
        return response

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:  # pragma: no cover
        await super().__call__(scope, receive, send)


def resolve_trace_context(
    payload_correlation_id: str | None, payload_causation_id: str | None, request: Request
) -> tuple[str, str]:
    """Resolve correlation and causation identifiers for an incoming request.

    The middleware populates request.state with identifiers when headers are not
    provided. Payload values take precedence when supplied.
    """
    correlation_id = payload_correlation_id or getattr(request.state, "correlation_id", None)
    causation_id = payload_causation_id or getattr(request.state, "causation_id", None)

    if not correlation_id:
        raise HTTPException(status_code=400, detail="correlation_id is required")
    if not causation_id:
        causation_id = correlation_id

    return correlation_id, causation_id
