#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Lambda handler for EventBridge-triggered events.

Provides the entry point for AWS Lambda functions triggered by EventBridge events,
routing events to appropriate handlers based on event type.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.events import BaseEvent, EventHandler
from the_alchemiser.shared.logging import get_logger, set_request_id

logger = get_logger(__name__)


def eventbridge_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle EventBridge event by routing to appropriate handler.

    This function is invoked by AWS Lambda when an EventBridge rule triggers.
    It extracts event details from the EventBridge payload, reconstructs the
    event object, and routes it to the appropriate handler.

    Args:
        event: EventBridge event payload containing:
            - detail-type: Event type (e.g., "SignalGenerated")
            - detail: Event data as JSON string or dict
            - source: Event source (e.g., "alchemiser.strategy")
        context: Lambda context object

    Returns:
        Response dict with statusCode and body

    Raises:
        Exception: Re-raises exceptions to trigger Lambda retry mechanism

    """
    # Set request ID for tracing
    set_request_id(context.request_id if hasattr(context, "request_id") else "unknown")

    try:
        # Extract event details from EventBridge payload
        detail_type = event.get("detail-type", "")
        detail = event.get("detail", {})
        source = event.get("source", "")

        logger.info(
            "Received EventBridge event",
            detail_type=detail_type,
            source=source,
            event_id=detail.get("event_id") if isinstance(detail, dict) else "unknown",
            lambda_request_id=context.request_id if hasattr(context, "request_id") else "unknown",
        )

        # Parse detail as event object
        if isinstance(detail, str):
            detail = json.loads(detail)

        # Parse timestamp if it's a string (EventBridge serializes as ISO string)
        # Handle both ISO 8601 with 'Z' suffix and '+00:00' timezone format
        if "timestamp" in detail and isinstance(detail["timestamp"], str):
            from datetime import datetime

            # Replace 'Z' with '+00:00' to handle all ISO 8601 formats correctly
            detail["timestamp"] = datetime.fromisoformat(detail["timestamp"].replace("Z", "+00:00"))

        # Reconstruct event from detail
        event_class = _get_event_class(detail_type)
        if not event_class:
            logger.warning(f"Unknown event type: {detail_type}")
            return {"statusCode": 400, "body": f"Unknown event type: {detail_type}"}

        event_obj = event_class.model_validate(detail)

        # Initialize container and get appropriate handler
        container = ApplicationContainer.create_for_environment("production")
        handler = _get_handler_for_event(container, detail_type)

        if not handler:
            logger.warning(f"No handler configured for event type: {detail_type}")
            return {"statusCode": 404, "body": f"No handler for: {detail_type}"}

        # Invoke handler
        handler.handle_event(event_obj)

        logger.info(
            "Event handled successfully",
            detail_type=detail_type,
            event_id=event_obj.event_id,
            correlation_id=event_obj.correlation_id,
        )

        return {"statusCode": 200, "body": "Event processed successfully"}

    except Exception as e:
        logger.error(
            "Failed to handle EventBridge event",
            error=str(e),
            error_type=type(e).__name__,
            detail_type=event.get("detail-type", "unknown"),
            exc_info=True,
        )
        # Re-raise to trigger retry
        raise


def _get_event_class(detail_type: str) -> type[BaseEvent] | None:
    """Map detail-type to event class.

    Args:
        detail_type: EventBridge detail-type field

    Returns:
        Event class or None if unknown

    """
    from the_alchemiser.shared.events import (
        RebalancePlanned,
        SignalGenerated,
        TradeExecuted,
        WorkflowCompleted,
        WorkflowFailed,
    )

    event_map: dict[str, type[BaseEvent]] = {
        "SignalGenerated": SignalGenerated,
        "RebalancePlanned": RebalancePlanned,
        "TradeExecuted": TradeExecuted,
        "WorkflowCompleted": WorkflowCompleted,
        "WorkflowFailed": WorkflowFailed,
    }

    return event_map.get(detail_type)


def _get_handler_for_event(
    container: ApplicationContainer, detail_type: str
) -> EventHandler | None:
    """Get appropriate handler for event type.

    Args:
        container: Application container with wired dependencies
        detail_type: EventBridge detail-type field

    Returns:
        Handler instance or None if not found.
        Returns None for event types that are only handled by the orchestrator
        (TradeExecuted, WorkflowCompleted, WorkflowFailed).

    """
    # Import handlers
    from the_alchemiser.execution_v2.handlers import TradingExecutionHandler
    from the_alchemiser.portfolio_v2.handlers import PortfolioAnalysisHandler

    # Map event types to their handlers
    # Orchestrator-only events (TradeExecuted, WorkflowCompleted, WorkflowFailed)
    # are not included here and will return None
    handler_map: dict[str, Callable[[], EventHandler]] = {
        "SignalGenerated": lambda: PortfolioAnalysisHandler(container),
        "RebalancePlanned": lambda: TradingExecutionHandler(container),
    }

    factory = handler_map.get(detail_type)
    return factory() if factory else None
