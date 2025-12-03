"""Business Unit: execution_v2 | Status: current.

FastAPI surface for execution events.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from the_alchemiser.shared.events import EventBus, TradeExecuted
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.middleware import CorrelationIdMiddleware, resolve_trace_context
from the_alchemiser.shared.utils.timezone_utils import ensure_timezone_aware

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer

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


class ExecuteRequest(BaseModel):
    """Request schema for executing trades from a rebalance plan.

    This accepts a RebalancePlanned event and triggers trade execution.
    """

    correlation_id: str | None = Field(default=None, description="Workflow correlation identifier")
    causation_id: str | None = Field(
        default=None, description="Causation identifier for traceability"
    )
    event_type: str | None = Field(
        default="RebalancePlanned", description="Type of triggering event"
    )
    event: dict[str, Any] = Field(
        ..., description="RebalancePlanned event data from portfolio service"
    )


def _build_timestamp(request_timestamp: datetime | None) -> datetime:
    return ensure_timezone_aware(request_timestamp) if request_timestamp else datetime.now(UTC)


def create_app(
    event_bus: EventBus | None = None,
    container: ApplicationContainer | None = None,
) -> FastAPI:
    """Create a FastAPI app for publishing TradeExecuted events.

    Args:
        event_bus: Optional EventBus instance for publishing events.
        container: Optional ApplicationContainer for trade execution.

    Returns:
        FastAPI application instance.

    """
    bus = event_bus or EventBus()
    app = FastAPI(title="Execution v2 API", version="0.1.0")
    app.add_middleware(CorrelationIdMiddleware)
    app.state.event_bus = bus
    app.state.container = container

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

    @app.post("/execute")
    def execute_trades(payload: ExecuteRequest, request: Request) -> dict[str, Any]:
        """Execute trades based on a rebalance plan.

        This endpoint takes a RebalancePlanned event, executes the trades,
        and returns a TradeExecuted event payload.
        """
        # Import here to avoid circular imports at module load time
        from the_alchemiser.execution_v2.handlers.trading_execution_handler import (
            TradingExecutionHandler,
        )
        from the_alchemiser.shared.config.container import ApplicationContainer
        from the_alchemiser.shared.events import RebalancePlanned
        from the_alchemiser.shared.events.base import BaseEvent
        from the_alchemiser.shared.schemas.common import AllocationComparison
        from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlan
        from the_alchemiser.shared.utils.data_conversion import (
            convert_datetime_fields_from_dict,
            convert_decimal_fields_from_dict,
            convert_nested_rebalance_item_data,
        )

        correlation_id, causation_id = resolve_trace_context(
            payload.correlation_id, payload.causation_id, request
        )

        try:
            # Get or create container
            app_container = app.state.container
            if app_container is None:
                logger.info("Creating ApplicationContainer for trade execution")
                app_container = ApplicationContainer.create_for_environment("production")

            # Reconstruct RebalancePlanned event from payload
            event_data = payload.event

            # Prepare rebalance plan from nested dict
            plan_data = dict(event_data.get("rebalance_plan", {}))
            convert_datetime_fields_from_dict(plan_data, ["timestamp"])
            plan_data["items"] = [
                convert_nested_rebalance_item_data(dict(item))
                for item in plan_data.get("items", [])
            ]
            convert_decimal_fields_from_dict(
                plan_data,
                ["total_portfolio_value", "total_trade_value", "max_drift_tolerance"],
            )
            rebalance_plan = RebalancePlan(**plan_data)

            # Prepare allocation comparison
            alloc_data = event_data.get("allocation_comparison", {})
            allocation_comparison = AllocationComparison(
                target_values=alloc_data.get("target_values", {}),
                current_values=alloc_data.get("current_values", {}),
                deltas=alloc_data.get("deltas", {}),
            )

            # Build the RebalancePlanned event
            rebalance_event = RebalancePlanned(
                correlation_id=event_data.get("correlation_id", correlation_id),
                causation_id=event_data.get("causation_id", causation_id or str(uuid4())),
                event_id=event_data.get("event_id", str(uuid4())),
                timestamp=ensure_timezone_aware(
                    datetime.fromisoformat(event_data["timestamp"].replace("Z", "+00:00"))
                    if isinstance(event_data.get("timestamp"), str)
                    else event_data.get("timestamp", datetime.now(UTC))
                ),
                source_module=event_data.get("source_module", "portfolio_v2"),
                source_component=event_data.get("source_component"),
                rebalance_plan=rebalance_plan,
                allocation_comparison=allocation_comparison,
                trades_required=event_data.get("trades_required", False),
                metadata=event_data.get("metadata", {}),
            )

            # Create handler
            handler = TradingExecutionHandler(app_container)

            # Capture generated event
            generated_event: TradeExecuted | None = None

            def capture_event(event: BaseEvent) -> None:
                nonlocal generated_event
                if isinstance(event, TradeExecuted):
                    generated_event = event

            handler.event_bus.subscribe("TradeExecuted", capture_event)

            # Run trade execution
            logger.info(
                "Triggering trade execution",
                correlation_id=correlation_id,
                causation_id=causation_id,
                trades_required=rebalance_event.trades_required,
            )
            handler.handle_event(rebalance_event)

            if generated_event is None:
                raise HTTPException(
                    status_code=500,
                    detail="Trade execution completed but no TradeExecuted event was published",
                )

            logger.info(
                "Trade execution completed successfully",
                correlation_id=correlation_id,
                success=generated_event.success,
                orders_placed=generated_event.orders_placed,
                orders_succeeded=generated_event.orders_succeeded,
            )

            return {
                "status": "executed",
                "event_type": "TradeExecuted",
                "event": generated_event.to_dict(),
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(
                "Trade execution failed",
                correlation_id=correlation_id,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            raise HTTPException(status_code=500, detail=f"Trade execution failed: {e}") from e

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


__all__ = ["ExecuteRequest", "ExecutionRequest", "create_app"]
