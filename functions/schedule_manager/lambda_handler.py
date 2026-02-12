"""Business Unit: coordinator_v2 | Status: current.

Lambda handler for Schedule Manager microservice.

This Lambda runs early each trading day (e.g., 9:00 AM ET) to:
1. Check if today is a trading day
2. Get the market close time (accounting for early closes)
3. Create/update a one-time EventBridge Scheduler rule to trigger
   the Strategy Orchestrator at the appropriate time
"""

from __future__ import annotations

import uuid
from typing import Any

from config import ScheduleManagerSettings
from handlers.schedule_creation_handler import ScheduleCreationHandler

from the_alchemiser.shared.logging import configure_application_logging, get_logger

# Initialize logging on cold start
configure_application_logging()

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle morning invocation to set up today's trading schedule.

    Args:
        event: Lambda event (from EventBridge schedule - morning trigger)
        context: Lambda context

    Returns:
        Response with schedule status and execution time.

    """
    correlation_id = event.get("correlation_id") or f"schedule-{uuid.uuid4()}"

    logger.info(
        "Schedule Manager Lambda invoked",
        extra={"correlation_id": correlation_id},
    )

    settings = ScheduleManagerSettings.from_environment()
    handler = ScheduleCreationHandler(settings)
    return handler.handle(correlation_id)
