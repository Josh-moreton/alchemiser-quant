"""Business Unit: hedge_roll_manager | Status: current.

Lambda handler for hedge roll manager microservice.

Triggered daily by EventBridge schedule to check for expiring hedges
and trigger roll operations.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from handlers.roll_schedule_handler import RollScheduleHandler
from wiring import register_hedge_roll_manager

from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.events import BaseEvent
from the_alchemiser.shared.events.eventbridge_publisher import publish_to_eventbridge
from the_alchemiser.shared.events.schemas import HedgeRollTriggered
from the_alchemiser.shared.logging import configure_application_logging, get_logger

# Initialize logging on cold start
configure_application_logging()

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle scheduled event for hedge roll management.

    This handler:
    1. Scans DynamoDB for active hedge positions
    2. Checks DTE against roll threshold (45 days)
    3. Publishes HedgeRollTriggered for positions needing roll

    Args:
        event: EventBridge scheduled event
        context: Lambda context (unused)

    Returns:
        Response with roll check summary

    """
    correlation_id = f"roll-check-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}"

    logger.info(
        "HedgeRollManager Lambda invoked",
        extra={
            "correlation_id": correlation_id,
            "event_source": event.get("source", "unknown"),
        },
    )

    try:
        # Create application container
        container = ApplicationContainer()
        register_hedge_roll_manager(container)

        # Create handler
        handler = RollScheduleHandler(container)

        # Capture roll events for publishing
        roll_events: list[HedgeRollTriggered] = []

        def capture_roll(evt: BaseEvent) -> None:
            if isinstance(evt, HedgeRollTriggered):
                roll_events.append(evt)

        handler.event_bus.subscribe("HedgeRollTriggered", capture_roll)

        # Run roll check
        result = handler.handle_scheduled_event(correlation_id)

        # Publish roll events to EventBridge
        for roll_event in roll_events:
            publish_to_eventbridge(roll_event)
            logger.info(
                "Published HedgeRollTriggered event",
                extra={
                    "hedge_id": roll_event.hedge_id,
                    "current_dte": roll_event.current_dte,
                },
            )

        logger.info(
            "HedgeRollManager completed",
            extra={
                "correlation_id": correlation_id,
                "positions_checked": result.get("positions_checked", 0),
                "rolls_triggered": result.get("rolls_triggered", 0),
            },
        )

        return {
            "statusCode": 200,
            "body": {
                "status": "success",
                "correlation_id": correlation_id,
                **result,
            },
        }

    except Exception as e:
        logger.error(
            "HedgeRollManager failed",
            extra={
                "correlation_id": correlation_id,
                "error": str(e),
            },
            exc_info=True,
        )

        return {
            "statusCode": 500,
            "body": {
                "status": "error",
                "correlation_id": correlation_id,
                "error": str(e),
            },
        }
