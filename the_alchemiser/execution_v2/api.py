"""Business Unit: execution_v2 | Status: current.

FastAPI surface for execution events.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from the_alchemiser.shared.events import EventBus, TradeExecuted
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.middleware import CorrelationIdMiddleware, resolve_trace_context
from the_alchemiser.shared.utils.timezone_utils import ensure_timezone_aware

logger = get_logger(__name__)


class ExecutionRequest(BaseModel):
    """Request schema for publishing a TradeExecuted event."""

    correlation_id: str | None = Field(
        default=None, description="Workflow correlation identifier (header or body)"
    )
    causation_id: str | None = Field(
        default=None, description="Causation identifier for traceability (header or body)"
    )
    event_id: str | None = Field(default=None, description="Optional event identifier override")
    timestamp: datetime | None = Field(
        default=None,
        description="Timestamp for the event; defaults to now if omitted",
    )
    source_module: str = Field(default="execution_v2", description="Event source module")
    source_component: str | None = Field(
        default="api",
        description="Specific component emitting the event",
    )
    execution_data: dict[str, Any] = Field(..., description="Execution details payload")
    success: bool = Field(..., description="Whether execution was successful")
    orders_placed: int = Field(..., description="Number of orders placed")
    orders_succeeded: int = Field(..., description="Number of orders that succeeded")
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Optional metadata forwarded with the event",
    )
    failure_reason: str | None = Field(
        default=None,
        description="Failure reason when execution fails",
    )
    failed_symbols: list[str] = Field(
        default_factory=list,
        description="Symbols that failed during execution",
    )


def _build_timestamp(request_timestamp: datetime | None) -> datetime:
    return ensure_timezone_aware(request_timestamp) if request_timestamp else datetime.now(UTC)


def create_app(event_bus: EventBus | None = None) -> FastAPI:
    """Create a FastAPI app for publishing TradeExecuted events."""
    bus = event_bus or EventBus()
    app = FastAPI(title="Execution v2 API", version="0.1.0")
    app.add_middleware(CorrelationIdMiddleware)
    app.state.event_bus = bus

    @app.get("/health")
    def health_check() -> dict[str, str]:
        """Health check endpoint for monitoring and load balancers."""
        return {"status": "healthy", "service": "execution_v2"}

    @app.get("/contracts")
    def contracts() -> dict[str, Any]:
        """Report contract versions supported by the service."""

        return {
            "service": "execution_v2",
            "supported_events": {"TradeExecuted": TradeExecuted.__event_version__},
        }

    @app.post("/executions")
    def publish_execution(payload: ExecutionRequest, request: Request) -> dict[str, Any]:
        try:
            correlation_id, causation_id = resolve_trace_context(
                payload.correlation_id, payload.causation_id, request
            )
            event = TradeExecuted(
                correlation_id=correlation_id,
                causation_id=causation_id,
                event_id=payload.event_id or str(uuid4()),
                timestamp=_build_timestamp(payload.timestamp),
                source_module=payload.source_module,
                source_component=payload.source_component,
                execution_data=payload.execution_data,
                success=payload.success,
                orders_placed=payload.orders_placed,
                orders_succeeded=payload.orders_succeeded,
                metadata=payload.metadata or {},
                failure_reason=payload.failure_reason,
                failed_symbols=payload.failed_symbols,
            )
            bus.publish(event)
            logger.info(
                "Execution event published successfully",
                event_id=event.event_id,
                correlation_id=correlation_id,
                success=payload.success,
                orders_placed=payload.orders_placed,
                orders_succeeded=payload.orders_succeeded,
            )
            return {"status": "published", "event": event.to_dict()}
        except Exception as e:
            logger.error(
                "Failed to publish execution event",
                correlation_id=payload.correlation_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise HTTPException(status_code=500, detail=f"Event publication failed: {e}") from e

    return app


__all__ = ["ExecutionRequest", "create_app"]
