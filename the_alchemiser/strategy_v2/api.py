"""Business Unit: strategy_v2 | Status: current.

FastAPI surface for emitting strategy signals.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from the_alchemiser.shared.events import EventBus, SignalGenerated
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.utils.timezone_utils import ensure_timezone_aware

logger = get_logger(__name__)


class SignalRequest(BaseModel):
    """Request schema for publishing a SignalGenerated event."""

    correlation_id: str = Field(..., description="Workflow correlation identifier")
    causation_id: str = Field(..., description="Causation identifier for traceability")
    event_id: str | None = Field(default=None, description="Optional event identifier override")
    timestamp: datetime | None = Field(
        default=None,
        description="Timestamp for the event; defaults to now if omitted",
    )
    source_module: str = Field(default="strategy_v2", description="Event source module")
    source_component: str | None = Field(
        default="api",
        description="Specific component emitting the event",
    )
    signals_data: dict[str, Any] = Field(..., description="Strategy signals payload")
    consolidated_portfolio: dict[str, Any] = Field(
        ...,
        description="Consolidated portfolio allocation details",
    )
    signal_count: int = Field(..., description="Number of signals generated")
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Optional metadata forwarded with the event",
    )


def _build_timestamp(request_timestamp: datetime | None) -> datetime:
    return ensure_timezone_aware(request_timestamp) if request_timestamp else datetime.now(UTC)


def create_app(event_bus: EventBus | None = None) -> FastAPI:
    """Create a FastAPI app for publishing SignalGenerated events."""
    bus = event_bus or EventBus()
    app = FastAPI(title="Strategy v2 API", version="0.1.0")
    app.state.event_bus = bus

    @app.get("/health")
    def health_check() -> dict[str, str]:
        """Health check endpoint for monitoring and load balancers."""
        return {"status": "healthy", "service": "strategy_v2"}

    @app.post("/signals")
    def publish_signal(request: SignalRequest) -> dict[str, Any]:
        try:
            event = SignalGenerated(
                correlation_id=request.correlation_id,
                causation_id=request.causation_id,
                event_id=request.event_id or str(uuid4()),
                timestamp=_build_timestamp(request.timestamp),
                source_module=request.source_module,
                source_component=request.source_component,
                signals_data=request.signals_data,
                consolidated_portfolio=request.consolidated_portfolio,
                signal_count=request.signal_count,
                metadata=request.metadata or {},
            )
            bus.publish(event)
            logger.info(
                "Signal event published successfully",
                event_id=event.event_id,
                correlation_id=request.correlation_id,
                signal_count=request.signal_count,
            )
            return {"status": "published", "event": event.to_dict()}
        except Exception as e:
            logger.error(
                "Failed to publish signal event",
                correlation_id=request.correlation_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise HTTPException(status_code=500, detail=f"Event publication failed: {e}") from e

    return app


__all__ = ["SignalRequest", "create_app"]
