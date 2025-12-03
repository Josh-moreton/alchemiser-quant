"""Business Unit: orchestration | Status: current.

Lambda handler for microservices orchestrator.

This handler publishes WorkflowStarted to EventBridge, triggering the
async event-driven workflow:
    Orchestrator → EventBridge(WorkflowStarted) → Strategy Lambda
    → EventBridge(SignalGenerated) → Portfolio Lambda
    → EventBridge(RebalancePlanned) → SQS → Execution Lambda
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.errors import MarketDataError, TradingClientError
from the_alchemiser.shared.events import WorkflowStarted
from the_alchemiser.shared.events.eventbridge_publisher import publish_to_eventbridge
from the_alchemiser.shared.logging import (
    configure_application_logging,
    generate_request_id,
    get_logger,
    set_request_id,
)

configure_application_logging()
logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: object | None = None) -> dict[str, Any]:
    """Lambda handler for orchestrator with EventBridge workflow.

    This handler:
    1. Optionally checks market status
    2. Publishes WorkflowStarted to EventBridge
    3. Returns immediately (workflow continues async via EventBridge)

    Args:
        event: Lambda event payload containing workflow parameters.
        context: Lambda context object.

    Returns:
        Response dict with status and correlation tracking.

    """
    request_id = getattr(context, "aws_request_id", "unknown") if context else "local"
    correlation_id = event.get("correlation_id") or generate_request_id()
    set_request_id(correlation_id)

    logger.info(
        "Orchestrator Lambda invoked (EventBridge mode)",
        extra={
            "request_id": request_id,
            "correlation_id": correlation_id,
        },
    )

    try:
        mode = event.get("mode", "trade")
        if mode != "trade":
            raise ValueError(f"Unsupported mode: {mode}. Only 'trade' is supported.")

        # Create container for market status check
        container = ApplicationContainer.create_for_environment("production")

        # Check market status (optional, workflow proceeds regardless)
        market_is_open = False
        market_status = "unknown"
        try:
            from the_alchemiser.shared.services.market_clock_service import (
                MarketClockService,
            )

            trading_client = container.infrastructure.alpaca_manager().trading_client
            market_clock_service = MarketClockService(trading_client)
            market_is_open = market_clock_service.is_market_open(correlation_id=correlation_id)
            market_status = "open" if market_is_open else "closed"

            if not market_is_open:
                logger.warning(
                    "Market is closed - signal generation will proceed but orders skipped",
                    extra={
                        "correlation_id": correlation_id,
                        "market_status": market_status,
                    },
                )
            else:
                logger.info(
                    "Market is open - full trading workflow will execute",
                    extra={
                        "correlation_id": correlation_id,
                        "market_status": market_status,
                    },
                )
        except (MarketDataError, TradingClientError) as e:
            logger.warning(
                "Market status check failed",
                extra={
                    "correlation_id": correlation_id,
                    "error": str(e),
                },
            )
        except Exception as e:
            logger.warning(
                "Unexpected error checking market status",
                extra={
                    "correlation_id": correlation_id,
                    "error": str(e),
                },
            )

        # Create and publish WorkflowStarted event to EventBridge
        workflow_event = WorkflowStarted(
            correlation_id=correlation_id,
            causation_id=f"system-request-{datetime.now(UTC).isoformat()}",
            event_id=f"workflow-started-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="orchestration.lambda_handler",
            source_component="OrchestratorLambda",
            workflow_type="trading",
            requested_by="EventBridgeSchedule",
            configuration={
                "live_trading": not container.config.paper_trading(),
                "market_is_open": market_is_open,
                "market_status": market_status,
            },
        )

        # Publish to EventBridge - this triggers Strategy Lambda asynchronously
        publish_to_eventbridge(workflow_event)

        logger.info(
            "WorkflowStarted published to EventBridge",
            extra={
                "correlation_id": correlation_id,
                "market_status": market_status,
            },
        )

        return {
            "status": "success",
            "mode": mode,
            "correlation_id": correlation_id,
            "request_id": request_id,
            "message": "Workflow started asynchronously via EventBridge",
        }

    except Exception as e:
        logger.error(
            "Orchestrator failed to start workflow",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "correlation_id": correlation_id,
            },
            exc_info=True,
        )
        return {
            "status": "failed",
            "error": str(e),
            "correlation_id": correlation_id,
            "request_id": request_id,
        }
