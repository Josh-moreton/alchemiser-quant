"""Business Unit: coordinator | Status: current.

Lambda handler for Strategy Coordinator microservice.

The Coordinator orchestrates parallel execution of DSL strategy files by:
1. Reading strategy configuration (DSL files and allocations)
2. Invoking Strategy Lambda once per DSL file (async)

Each strategy worker independently evaluates DSL, calculates rebalance,
and enqueues trades. No aggregation session or planner step required.
"""

from __future__ import annotations

import uuid
from typing import Any

from handlers.dispatch_handler import DispatchHandler

from the_alchemiser.shared.logging import configure_application_logging, get_logger

# Initialize logging on cold start
configure_application_logging()

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle scheduled invocation to coordinate strategy execution.

    Args:
        event: Lambda event (from EventBridge schedule or direct invoke).
        context: Lambda context.

    Returns:
        Response with correlation_id and invocation count.

    """
    correlation_id = event.get("correlation_id") or f"workflow-{uuid.uuid4()}"
    scheduled_by = event.get("scheduled_by", "direct")

    logger.info(
        "Coordinator invoked - dispatching per-strategy execution",
        extra={
            "correlation_id": correlation_id,
            "event_source": event.get("source", "schedule"),
            "scheduled_by": scheduled_by,
        },
    )

    handler = DispatchHandler()
    return handler.handle(event, correlation_id)
