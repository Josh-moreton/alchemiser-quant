"""Business Unit: orchestration | Status: current.

Lambda handler for microservices orchestrator.

This handler initializes the EventDrivenOrchestrator with HTTP workflow mode
enabled, allowing it to coordinate module Lambdas via Function URLs.
"""

from __future__ import annotations

import os
from typing import Any

from the_alchemiser.orchestration.event_driven_orchestrator import EventDrivenOrchestrator
from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.logging import (
    configure_application_logging,
    generate_request_id,
    get_logger,
    set_request_id,
)

configure_application_logging()
logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: object | None = None) -> dict[str, Any]:
    """Lambda handler for orchestrator with HTTP workflow enabled.

    Environment variables required:
        ORCHESTRATION__USE_HTTP_DOMAIN_WORKFLOW: "true"
        ORCHESTRATION__STRATEGY_ENDPOINT: Function URL for strategy
        ORCHESTRATION__PORTFOLIO_ENDPOINT: Function URL for portfolio
        ORCHESTRATION__EXECUTION_ENDPOINT: Function URL for execution

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
        "Orchestrator Lambda invoked (microservices mode)",
        request_id=request_id,
        correlation_id=correlation_id,
        lambda_event=event,
    )

    try:
        # Verify HTTP workflow is enabled
        use_http = os.environ.get("ORCHESTRATION__USE_HTTP_DOMAIN_WORKFLOW", "").lower()
        if use_http != "true":
            raise RuntimeError(
                "HTTP workflow must be enabled. Set ORCHESTRATION__USE_HTTP_DOMAIN_WORKFLOW=true"
            )

        # Create container and orchestrator
        container = ApplicationContainer.create_for_environment("production")
        orchestrator = EventDrivenOrchestrator(container)

        # Execute workflow
        mode = event.get("mode", "trade")
        if mode == "trade":
            orchestrator.start_trading_workflow(correlation_id=correlation_id)
        else:
            # Handle other modes (pnl_analysis, etc.)
            raise ValueError(f"Unsupported mode: {mode}")

        logger.info("Orchestrator workflow completed", correlation_id=correlation_id)

        return {
            "status": "success",
            "mode": mode,
            "correlation_id": correlation_id,
            "request_id": request_id,
        }

    except Exception as e:
        logger.error(
            "Orchestrator workflow failed",
            error=str(e),
            error_type=type(e).__name__,
            correlation_id=correlation_id,
            exc_info=True,
        )
        return {
            "status": "failed",
            "error": str(e),
            "correlation_id": correlation_id,
            "request_id": request_id,
        }
