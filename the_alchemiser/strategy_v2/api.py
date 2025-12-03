"""Business Unit: strategy_v2 | Status: current.

FastAPI surface for emitting strategy signals.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from the_alchemiser.shared.events import EventBus, SignalGenerated
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.middleware import CorrelationIdMiddleware, resolve_trace_context
from the_alchemiser.shared.utils.timezone_utils import ensure_timezone_aware

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer

logger = get_logger(__name__)


class SignalRequest(BaseModel):
    """Request schema for publishing a SignalGenerated event."""

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


class GenerateRequest(BaseModel):
    """Request schema for triggering signal generation."""

    correlation_id: str | None = Field(default=None, description="Workflow correlation identifier")
    causation_id: str | None = Field(
        default=None, description="Causation identifier for traceability"
    )
    event_type: str | None = Field(
        default="WorkflowStarted", description="Type of triggering event"
    )
    event_id: str | None = Field(default=None, description="Optional event identifier")
    trigger_event: dict[str, Any] | None = Field(
        default=None, description="Original trigger event data"
    )


def _build_timestamp(request_timestamp: datetime | None) -> datetime:
    return ensure_timezone_aware(request_timestamp) if request_timestamp else datetime.now(UTC)


def create_app(
    event_bus: EventBus | None = None,
    container: ApplicationContainer | None = None,
) -> FastAPI:
    """Create a FastAPI app for publishing SignalGenerated events.

    Args:
        event_bus: Optional EventBus instance for publishing events.
        container: Optional ApplicationContainer for signal generation.

    Returns:
        FastAPI application instance.

    """
    bus = event_bus or EventBus()
    app = FastAPI(title="Strategy v2 API", version="0.1.0")
    app.add_middleware(CorrelationIdMiddleware)
    app.state.event_bus = bus
    app.state.container = container

    @app.get("/health")
    def health_check() -> dict[str, str]:
        """Health check endpoint for monitoring and load balancers."""
        return {"status": "healthy", "service": "strategy_v2"}

    @app.get("/contracts")
    def contracts() -> dict[str, Any]:
        """Report contract versions supported by the service."""
        return {
            "service": "strategy_v2",
            "supported_events": {"SignalGenerated": SignalGenerated.__event_version__},
        }

    @app.post("/generate")
    def generate_signals(payload: GenerateRequest, request: Request) -> dict[str, Any]:
        """Trigger signal generation and return generated signals.

        This endpoint runs the full signal generation pipeline and returns
        a SignalGenerated event payload that can be forwarded to portfolio.
        """
        # Import here to avoid circular imports at module load time
        from the_alchemiser.shared.config.container import ApplicationContainer
        from the_alchemiser.shared.events import WorkflowStarted
        from the_alchemiser.shared.events.base import BaseEvent
        from the_alchemiser.strategy_v2.handlers.signal_generation_handler import (
            SignalGenerationHandler,
        )

        correlation_id, causation_id = resolve_trace_context(
            payload.correlation_id, payload.causation_id, request
        )

        try:
            # Get or create container
            app_container = app.state.container
            if app_container is None:
                logger.info("Creating ApplicationContainer for signal generation")
                app_container = ApplicationContainer.create_for_environment("production")

            # Create handler and workflow event
            handler = SignalGenerationHandler(app_container)
            workflow_event = WorkflowStarted(
                correlation_id=correlation_id,
                causation_id=causation_id or str(uuid4()),
                event_id=payload.event_id or str(uuid4()),
                timestamp=datetime.now(UTC),
                source_module="strategy_v2",
                workflow_type="trading",
                requested_by="api",
            )

            # Capture generated event - handler publishes to its bus
            generated_event: SignalGenerated | None = None

            def capture_event(event: BaseEvent) -> None:
                nonlocal generated_event
                if isinstance(event, SignalGenerated):
                    generated_event = event

            handler.event_bus.subscribe("SignalGenerated", capture_event)

            # Run signal generation
            logger.info(
                "Triggering signal generation",
                correlation_id=correlation_id,
                causation_id=causation_id,
            )
            handler.handle_event(workflow_event)

            if generated_event is None:
                raise HTTPException(
                    status_code=500,
                    detail="Signal generation completed but no SignalGenerated event was published",
                )

            logger.info(
                "Signal generation completed successfully",
                correlation_id=correlation_id,
                signal_count=generated_event.signal_count,
            )

            return {
                "status": "generated",
                "event_type": "SignalGenerated",
                "event": generated_event.to_dict(),
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Signal generation failed",
                correlation_id=correlation_id,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            raise HTTPException(status_code=500, detail=f"Signal generation failed: {e}") from e

    @app.post("/signals")
    def publish_signal(payload: SignalRequest, request: Request) -> dict[str, Any]:
        try:
            correlation_id, causation_id = resolve_trace_context(
                payload.correlation_id, payload.causation_id, request
            )
            event = SignalGenerated(
                correlation_id=correlation_id,
                causation_id=causation_id,
                event_id=payload.event_id or str(uuid4()),
                timestamp=_build_timestamp(payload.timestamp),
                source_module=payload.source_module,
                source_component=payload.source_component,
                signals_data=payload.signals_data,
                consolidated_portfolio=payload.consolidated_portfolio,
                signal_count=payload.signal_count,
                metadata=payload.metadata or {},
            )
            bus.publish(event)
            logger.info(
                "Signal event published successfully",
                event_id=event.event_id,
                correlation_id=correlation_id,
                signal_count=payload.signal_count,
            )
            return {"status": "published", "event": event.to_dict()}
        except Exception as e:
            logger.error(
                "Failed to publish signal event",
                correlation_id=payload.correlation_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise HTTPException(status_code=500, detail=f"Event publication failed: {e}") from e

    return app


__all__ = ["GenerateRequest", "SignalRequest", "create_app"]
