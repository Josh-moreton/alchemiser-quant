"""Business Unit: portfolio_v2 | Status: current.

FastAPI surface for portfolio rebalance events.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from the_alchemiser.shared.events import EventBus, RebalancePlanned
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.middleware import CorrelationIdMiddleware, resolve_trace_context
from the_alchemiser.shared.schemas.common import AllocationComparison
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlan
from the_alchemiser.shared.utils.data_conversion import (
    convert_datetime_fields_from_dict,
    convert_decimal_fields_from_dict,
    convert_nested_rebalance_item_data,
    convert_string_to_decimal,
)
from the_alchemiser.shared.utils.timezone_utils import ensure_timezone_aware

logger = get_logger(__name__)


class RebalanceRequest(BaseModel):
    """Request schema for publishing a RebalancePlanned event."""

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
    source_module: str = Field(default="portfolio_v2", description="Event source module")
    source_component: str | None = Field(
        default="api",
        description="Specific component emitting the event",
    )
    rebalance_plan: dict[str, Any] = Field(
        ...,
        description="Calculated rebalance plan payload (raw data)",
    )
    allocation_comparison: dict[str, Any] = Field(
        ...,
        description="Allocation comparison accompanying the rebalance plan",
    )
    trades_required: bool = Field(..., description="Indicates if trades are required")
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Optional metadata forwarded with the event",
    )


def _build_timestamp(request_timestamp: datetime | None) -> datetime:
    return ensure_timezone_aware(request_timestamp) if request_timestamp else datetime.now(UTC)


def _prepare_allocation_comparison(data: dict[str, Any]) -> AllocationComparison:
    target_values = {
        key: convert_string_to_decimal(value, f"target_values[{key}]")
        if isinstance(value, str)
        else value
        for key, value in data.get("target_values", {}).items()
    }
    current_values = {
        key: convert_string_to_decimal(value, f"current_values[{key}]")
        if isinstance(value, str)
        else value
        for key, value in data.get("current_values", {}).items()
    }
    deltas = {
        key: convert_string_to_decimal(value, f"deltas[{key}]") if isinstance(value, str) else value
        for key, value in data.get("deltas", {}).items()
    }
    return AllocationComparison(
        target_values=target_values, current_values=current_values, deltas=deltas
    )


def _prepare_rebalance_plan(
    data: dict[str, Any], correlation_id: str | None, causation_id: str | None
) -> RebalancePlan:
    plan_data = dict(data)
    if correlation_id is not None:
        plan_data.setdefault("correlation_id", correlation_id)
    if causation_id is not None:
        plan_data.setdefault("causation_id", causation_id)
    convert_datetime_fields_from_dict(plan_data, ["timestamp"])
    plan_data["items"] = [
        convert_nested_rebalance_item_data(dict(item)) for item in plan_data.get("items", [])
    ]
    plan_decimal_fields = [
        "total_portfolio_value",
        "total_trade_value",
        "max_drift_tolerance",
    ]
    convert_decimal_fields_from_dict(plan_data, plan_decimal_fields)
    return RebalancePlan(**plan_data)


def create_app(event_bus: EventBus | None = None) -> FastAPI:
    """Create a FastAPI app for publishing RebalancePlanned events."""
    bus = event_bus or EventBus()
    app = FastAPI(title="Portfolio v2 API", version="0.1.0")
    app.add_middleware(CorrelationIdMiddleware)
    app.state.event_bus = bus

    @app.get("/health")
    def health_check() -> dict[str, str]:
        """Health check endpoint for monitoring and load balancers."""
        return {"status": "healthy", "service": "portfolio_v2"}

    @app.get("/contracts")
    def contracts() -> dict[str, Any]:
        """Report contract versions supported by the service."""
        return {
            "service": "portfolio_v2",
            "supported_events": {"RebalancePlanned": RebalancePlanned.__event_version__},
        }

    @app.post("/rebalance")
    def publish_rebalance(payload: RebalanceRequest, request: Request) -> dict[str, Any]:
        try:
            correlation_id, causation_id = resolve_trace_context(
                payload.correlation_id, payload.causation_id, request
            )
            plan = _prepare_rebalance_plan(
                payload.rebalance_plan, correlation_id=correlation_id, causation_id=causation_id
            )
            allocation_comparison = _prepare_allocation_comparison(payload.allocation_comparison)
            event = RebalancePlanned(
                correlation_id=correlation_id,
                causation_id=causation_id,
                event_id=payload.event_id or str(uuid4()),
                timestamp=_build_timestamp(payload.timestamp),
                source_module=payload.source_module,
                source_component=payload.source_component,
                rebalance_plan=plan,
                allocation_comparison=allocation_comparison,
                trades_required=payload.trades_required,
                metadata=payload.metadata or {},
            )
            bus.publish(event)
            logger.info(
                "Rebalance event published successfully",
                event_id=event.event_id,
                correlation_id=correlation_id,
                trades_required=payload.trades_required,
                plan_id=plan.plan_id,
            )
            return {"status": "published", "event": event.to_dict()}
        except Exception as e:
            logger.error(
                "Failed to publish rebalance event",
                correlation_id=payload.correlation_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise HTTPException(status_code=500, detail=f"Event publication failed: {e}") from e

    return app


__all__ = ["RebalanceRequest", "create_app"]
