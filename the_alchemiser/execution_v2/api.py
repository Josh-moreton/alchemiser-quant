"""FastAPI surface for execution events."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel, Field

from the_alchemiser.shared.events import EventBus, TradeExecuted
from the_alchemiser.shared.utils.timezone_utils import ensure_timezone_aware


class ExecutionRequest(BaseModel):
    """Request schema for publishing a TradeExecuted event."""

    correlation_id: str = Field(..., description="Workflow correlation identifier")
    causation_id: str = Field(..., description="Causation identifier for traceability")
    event_id: str | None = Field(default=None, description="Optional event identifier override")
    timestamp: datetime | None = Field(
        default=None, description="Timestamp for the event; defaults to now if omitted",
    )
    source_module: str = Field(default="execution_v2", description="Event source module")
    source_component: str | None = Field(
        default="api", description="Specific component emitting the event",
    )
    execution_data: dict[str, Any] = Field(..., description="Execution details payload")
    success: bool = Field(..., description="Whether execution was successful")
    orders_placed: int = Field(..., description="Number of orders placed")
    orders_succeeded: int = Field(..., description="Number of orders that succeeded")
    metadata: dict[str, Any] | None = Field(
        default=None, description="Optional metadata forwarded with the event",
    )
    failure_reason: str | None = Field(
        default=None, description="Failure reason when execution fails",
    )
    failed_symbols: list[str] = Field(
        default_factory=list, description="Symbols that failed during execution",
    )


def _build_timestamp(request_timestamp: datetime | None) -> datetime:
    return ensure_timezone_aware(request_timestamp) if request_timestamp else datetime.now(UTC)


def create_app(event_bus: EventBus | None = None) -> FastAPI:
    """Create a FastAPI app for publishing TradeExecuted events."""

    bus = event_bus or EventBus()
    app = FastAPI(title="Execution v2 API", version="0.1.0")
    app.state.event_bus = bus

    @app.post("/executions")
    def publish_execution(request: ExecutionRequest) -> dict[str, Any]:
        event = TradeExecuted(
            correlation_id=request.correlation_id,
            causation_id=request.causation_id,
            event_id=request.event_id or str(uuid4()),
            timestamp=_build_timestamp(request.timestamp),
            source_module=request.source_module,
            source_component=request.source_component,
            execution_data=request.execution_data,
            success=request.success,
            orders_placed=request.orders_placed,
            orders_succeeded=request.orders_succeeded,
            metadata=request.metadata or {},
            failure_reason=request.failure_reason,
            failed_symbols=request.failed_symbols,
        )
        bus.publish(event)
        return {"status": "published", "event": event.to_dict()}

    return app


__all__ = ["create_app", "ExecutionRequest"]
