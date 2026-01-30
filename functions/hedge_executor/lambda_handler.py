"""Business Unit: hedge_executor | Status: current.

Lambda handler for hedge executor microservice.

Triggered by SQS when HedgeEvaluationCompleted is published.
Executes hedge orders and publishes HedgeExecuted to EventBridge.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from handlers.hedge_execution_handler import HedgeExecutionHandler
from wiring import register_hedge_executor

from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.events import BaseEvent
from the_alchemiser.shared.events.eventbridge_publisher import publish_to_eventbridge
from the_alchemiser.shared.events.schemas import (
    AllHedgesCompleted,
    HedgeEvaluationCompleted,
    HedgeExecuted,
)
from the_alchemiser.shared.logging import configure_application_logging, get_logger
from the_alchemiser.shared.utils.timezone_utils import ensure_timezone_aware

# Initialize logging on cold start
configure_application_logging()

logger = get_logger(__name__)


def _is_hedging_enabled() -> bool:
    """Check if options hedging is enabled via environment variable.

    Returns:
        True if OPTIONS_HEDGING_ENABLED is set to 'true' (case-insensitive),
        False otherwise. Defaults to False for safety.

    """
    import os

    return os.environ.get("OPTIONS_HEDGING_ENABLED", "false").lower() == "true"


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle SQS event for hedge execution.

    This handler:
    1. Processes SQS messages containing HedgeEvaluationCompleted
    2. Executes hedge orders via Alpaca Options API
    3. Publishes HedgeExecuted and AllHedgesCompleted to EventBridge

    Args:
        event: SQS event with HedgeEvaluationCompleted messages
        context: Lambda context (unused)

    Returns:
        Response with batch item failures for retry

    """
    # Feature flag check - skip execution if disabled
    if not _is_hedging_enabled():
        logger.info(
            "Options hedging DISABLED via feature flag - skipping execution",
            extra={
                "feature_flag": "OPTIONS_HEDGING_ENABLED",
                "status": "skipped",
                "record_count": len(event.get("Records", [])),
            },
        )
        # Return empty batch failures to acknowledge all messages without processing
        return {"batchItemFailures": []}

    records = event.get("Records", [])
    batch_item_failures: list[dict[str, str]] = []

    logger.info(
        "HedgeExecutor Lambda invoked",
        extra={"record_count": len(records)},
    )

    for record in records:
        message_id = record.get("messageId", "unknown")

        try:
            # Parse SQS message body
            body = json.loads(record.get("body", "{}"))

            # Handle EventBridge wrapped message
            detail = body.get("detail", body)

            correlation_id = detail.get("correlation_id", str(uuid.uuid4()))

            logger.info(
                "Processing hedge evaluation message",
                extra={
                    "message_id": message_id,
                    "correlation_id": correlation_id,
                },
            )

            # Validate required fields in HedgeEvaluationCompleted event
            required_fields = ["plan_id", "portfolio_nav", "recommendations"]
            missing_fields = [
                f for f in required_fields if f not in detail or detail.get(f) in (None, "")
            ]

            # Allow empty recommendations list but not missing
            if "recommendations" in missing_fields and detail.get("recommendations") == []:
                missing_fields.remove("recommendations")

            if missing_fields:
                logger.error(
                    "Invalid HedgeEvaluationCompleted event: missing required fields",
                    extra={
                        "message_id": message_id,
                        "correlation_id": correlation_id,
                        "missing_fields": missing_fields,
                        "detail_keys": list(detail.keys()),
                    },
                )
                raise ValueError(
                    f"Missing required fields in HedgeEvaluationCompleted: {missing_fields}"
                )

            # Validate plan_id is not empty string (invalid state)
            if detail.get("plan_id") == "":
                logger.error(
                    "Invalid HedgeEvaluationCompleted event: empty plan_id",
                    extra={"message_id": message_id, "correlation_id": correlation_id},
                )
                raise ValueError("Invalid HedgeEvaluationCompleted: plan_id cannot be empty")

            # Create application container
            container = ApplicationContainer()
            register_hedge_executor(container)

            # Parse timestamp
            timestamp = detail.get("timestamp")
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            else:
                timestamp = datetime.now(UTC)
            timestamp = ensure_timezone_aware(timestamp)

            # Reconstruct HedgeEvaluationCompleted event
            evaluation_event = HedgeEvaluationCompleted(
                correlation_id=detail.get("correlation_id", correlation_id),
                causation_id=detail.get("causation_id", correlation_id),
                event_id=detail.get("event_id", f"hedge-eval-{uuid.uuid4()}"),
                timestamp=timestamp,
                source_module=detail.get("source_module", "hedge_evaluator"),
                source_component=detail.get("source_component"),
                plan_id=detail.get("plan_id", ""),
                portfolio_nav=Decimal(str(detail.get("portfolio_nav", "0"))),
                recommendations=detail.get("recommendations", []),
                total_premium_budget=Decimal(str(detail.get("total_premium_budget", "0"))),
                budget_nav_pct=Decimal(str(detail.get("budget_nav_pct", "0"))),
                vix_tier=detail.get("vix_tier", "mid"),
                exposure_multiplier=Decimal(str(detail.get("exposure_multiplier", "1.0"))),
                skip_reason=detail.get("skip_reason"),
            )

            # Create handler
            handler = HedgeExecutionHandler(container)

            # Capture events for publishing
            executed_events: list[HedgeExecuted] = []
            completed_event_holder: list[AllHedgesCompleted] = []

            def capture_executed(evt: BaseEvent) -> None:
                if isinstance(evt, HedgeExecuted):
                    executed_events.append(evt)  # noqa: B023

            def capture_completed(evt: BaseEvent) -> None:
                if isinstance(evt, AllHedgesCompleted):
                    completed_event_holder.append(evt)  # noqa: B023

            handler.event_bus.subscribe("HedgeExecuted", capture_executed)
            handler.event_bus.subscribe("AllHedgesCompleted", capture_completed)

            # Execute hedges
            handler.handle_event(evaluation_event)

            # Publish events to EventBridge
            for exec_event in executed_events:
                publish_to_eventbridge(exec_event)

            if completed_event_holder:
                publish_to_eventbridge(completed_event_holder[0])

            logger.info(
                "Hedge execution completed for message",
                extra={
                    "message_id": message_id,
                    "correlation_id": correlation_id,
                    "hedges_executed": len(executed_events),
                },
            )

        except Exception as e:
            logger.error(
                "Failed to process hedge execution message",
                extra={
                    "message_id": message_id,
                    "error": str(e),
                },
                exc_info=True,
            )
            batch_item_failures.append({"itemIdentifier": message_id})

    return {"batchItemFailures": batch_item_failures}
