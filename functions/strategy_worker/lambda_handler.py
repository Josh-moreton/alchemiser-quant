"""Business Unit: strategy_v2 | Status: current.

Lambda handler for strategy microservice.

This is the entry point for the trading workflow. Triggered by:
1. Coordinator Lambda (multi-node mode) - Runs single strategy file
2. EventBridge Schedule (direct invocation for testing)

Runs signal generation and publishes PartialSignalGenerated to EventBridge
for aggregation by the Aggregator Lambda.
"""

from __future__ import annotations

import sys
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from handlers.single_file_signal_handler import SingleFileSignalHandler
from wiring import register_strategy

from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.events import (
    PartialSignalGenerated,
    WorkflowFailed,
)
from the_alchemiser.shared.events.eventbridge_publisher import (
    publish_to_eventbridge,
)
from the_alchemiser.shared.logging import configure_application_logging, get_logger

# Increase recursion limit for deeply nested DSL strategies.
# Some strategies like ftl_starburst_gen2.clj have 288+ levels of nesting
# which exceeds Python's default limit of 1000 when combined with evaluator
# recursion. 10000 provides ample headroom for complex strategies.
sys.setrecursionlimit(10000)

# Initialize logging on cold start (must be before get_logger)
configure_application_logging()

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle invocation for signal generation.

    This handler runs a single DSL strategy file and publishes
    PartialSignalGenerated for aggregation. Always invoked by the
    Coordinator Lambda with session_id and dsl_file in the event.

    Args:
        event: Lambda event containing session_id, dsl_file, allocation, etc.
        context: Lambda context

    Returns:
        Response indicating success/failure

    """
    session_id = event.get("session_id", "")
    correlation_id = event.get("correlation_id", session_id)
    dsl_file = event.get("dsl_file", "")
    allocation = Decimal(str(event.get("allocation", "0")))
    strategy_number = event.get("strategy_number", 0)
    total_strategies = event.get("total_strategies", 1)
    debug_mode = event.get("debug_mode", False)

    # Validate required fields
    if not session_id or not dsl_file:
        error_msg = "Missing required fields: session_id and dsl_file are required"
        logger.error(
            error_msg,
            extra={
                "session_id": session_id,
                "dsl_file": dsl_file,
            },
        )
        return {
            "statusCode": 400,
            "body": {
                "status": "error",
                "error": error_msg,
            },
        }

    logger.info(
        "Strategy Lambda invoked",
        extra={
            "session_id": session_id,
            "correlation_id": correlation_id,
            "dsl_file": dsl_file,
            "allocation": str(allocation),
            "strategy_number": strategy_number,
            "total_strategies": total_strategies,
            "debug_mode": debug_mode,
        },
    )

    try:
        # Create application container (minimal - no auto-wiring)
        container = ApplicationContainer()
        # Wire strategy-specific dependencies
        register_strategy(container)

        # Use single-file handler
        handler = SingleFileSignalHandler(
            container=container,
            dsl_file=dsl_file,
            allocation=allocation,
            debug_mode=debug_mode,
        )

        # Generate signals for this single file
        result = handler.generate_signals(correlation_id)

        if result is None:
            raise ValueError(f"No signals generated for {dsl_file}")

        # Build PartialSignalGenerated event
        partial_signal = PartialSignalGenerated(
            event_id=f"partial-signal-{uuid.uuid4()}",
            correlation_id=correlation_id,
            causation_id=session_id,
            timestamp=datetime.now(UTC),
            source_module="strategy_v2",
            source_component="StrategyWorker",
            session_id=session_id,
            dsl_file=dsl_file,
            allocation=allocation,
            strategy_number=strategy_number,
            total_strategies=total_strategies,
            signals_data=result["signals_data"],
            consolidated_portfolio=result["consolidated_portfolio"],
            signal_count=result["signal_count"],
            metadata={"single_file_mode": True},
            data_freshness=result.get("data_freshness") or {},
        )

        # Publish to EventBridge (triggers Aggregator)
        publish_to_eventbridge(partial_signal)

        logger.info(
            "Signal generation completed",
            extra={
                "session_id": session_id,
                "correlation_id": correlation_id,
                "dsl_file": dsl_file,
                "signal_count": result["signal_count"],
            },
        )

        return {
            "statusCode": 200,
            "body": {
                "status": "success",
                "session_id": session_id,
                "correlation_id": correlation_id,
                "dsl_file": dsl_file,
                "signal_count": result["signal_count"],
            },
        }

    except Exception as e:
        logger.error(
            "Strategy execution failed",
            extra={
                "session_id": session_id,
                "correlation_id": correlation_id,
                "dsl_file": dsl_file,
                "error": str(e),
            },
            exc_info=True,
        )

        # Publish WorkflowFailed to EventBridge
        try:
            failure_event = WorkflowFailed(
                correlation_id=correlation_id,
                causation_id=session_id,
                event_id=f"workflow-failed-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="strategy_v2",
                source_component="StrategyWorker",
                workflow_type="signal_generation",
                failure_reason=str(e),
                failure_step="signal_generation",
                error_details={
                    "exception_type": type(e).__name__,
                    "dsl_file": dsl_file,
                    "session_id": session_id,
                },
            )
            publish_to_eventbridge(failure_event)
        except Exception as pub_error:
            logger.error(
                "Failed to publish WorkflowFailed event",
                extra={"error": str(pub_error)},
            )

        return {
            "statusCode": 500,
            "body": {
                "status": "error",
                "session_id": session_id,
                "correlation_id": correlation_id,
                "dsl_file": dsl_file,
                "error": str(e),
            },
        }
