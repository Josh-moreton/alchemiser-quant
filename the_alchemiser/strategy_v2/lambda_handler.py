"""Business Unit: strategy_v2 | Status: current.

Lambda handler for strategy microservice.

This is the entry point for the trading workflow. It can be triggered by:
1. EventBridge Schedule (daily at market open) - Legacy mode, runs all strategies
2. Coordinator Lambda (multi-node mode) - Runs single strategy file
3. Manual invocation for testing

Runs signal generation and publishes SignalGenerated (legacy) or
PartialSignalGenerated (multi-node) to EventBridge.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.events import (
    BaseEvent,
    PartialSignalGenerated,
    SignalGenerated,
    WorkflowFailed,
    WorkflowStarted,
)
from the_alchemiser.shared.events.eventbridge_publisher import (
    publish_to_eventbridge,
)
from the_alchemiser.shared.logging import configure_application_logging, get_logger
from the_alchemiser.strategy_v2.handlers.signal_generation_handler import (
    SignalGenerationHandler,
)
from the_alchemiser.strategy_v2.handlers.single_file_signal_handler import (
    SingleFileSignalHandler,
)

# Initialize logging on cold start (must be before get_logger)
configure_application_logging()

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle scheduled or manual invocation for signal generation.

    This handler supports two modes:
    1. LEGACY MODE (default): Runs all DSL strategies, publishes SignalGenerated
       Triggered by: EventBridge schedule or manual invocation
    2. SINGLE-FILE MODE: Runs one strategy file, publishes PartialSignalGenerated
       Triggered by: Coordinator Lambda with session_id and dsl_file in event

    Args:
        event: Lambda event (from schedule, coordinator, or manual invocation)
        context: Lambda context

    Returns:
        Response indicating success/failure

    """
    # Detect single-file mode (invoked by Coordinator)
    if "session_id" in event and "dsl_file" in event:
        return _handle_single_file_mode(event, context)

    # Legacy mode: run all strategies
    return _handle_legacy_mode(event, context)


def _handle_single_file_mode(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle single-file mode invocation from Coordinator Lambda.

    Runs a single DSL strategy file and publishes PartialSignalGenerated event.

    Args:
        event: Lambda event containing session_id, dsl_file, allocation, etc.
        context: Lambda context

    Returns:
        Response with session_id and signal status.

    """
    session_id = event.get("session_id", "")
    correlation_id = event.get("correlation_id", session_id)
    dsl_file = event.get("dsl_file", "")
    allocation = Decimal(str(event.get("allocation", "0")))
    strategy_number = event.get("strategy_number", 0)
    total_strategies = event.get("total_strategies", 1)

    logger.info(
        "Strategy Lambda invoked in SINGLE-FILE mode",
        extra={
            "session_id": session_id,
            "correlation_id": correlation_id,
            "dsl_file": dsl_file,
            "allocation": str(allocation),
            "strategy_number": strategy_number,
            "total_strategies": total_strategies,
        },
    )

    try:
        # Create application container
        container = ApplicationContainer.create_for_strategy("production")

        # Use single-file handler
        handler = SingleFileSignalHandler(
            container=container,
            dsl_file=dsl_file,
            allocation=allocation,
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
        )

        # Publish to EventBridge (triggers Aggregator)
        publish_to_eventbridge(partial_signal)

        logger.info(
            "Single-file signal generation completed",
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
                "mode": "single_file",
                "session_id": session_id,
                "correlation_id": correlation_id,
                "dsl_file": dsl_file,
                "signal_count": result["signal_count"],
            },
        }

    except Exception as e:
        logger.error(
            "Single-file strategy execution failed",
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
                workflow_type="single_file_signal_generation",
                failure_reason=str(e),
                failure_step="single_file_signal_generation",
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
                "mode": "single_file",
                "session_id": session_id,
                "correlation_id": correlation_id,
                "dsl_file": dsl_file,
                "error": str(e),
            },
        }


def _handle_legacy_mode(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle legacy mode: run all strategies in single invocation.

    This is the original behavior, triggered by EventBridge schedule.

    Args:
        event: Lambda event (from schedule or manual invocation)
        context: Lambda context

    Returns:
        Response indicating success/failure

    """
    # Generate correlation ID for this workflow
    correlation_id = event.get("correlation_id") or f"workflow-{uuid.uuid4()}"

    logger.info(
        "Strategy Lambda invoked - workflow entry point",
        extra={
            "correlation_id": correlation_id,
            "event_source": event.get("source", "schedule"),
        },
    )

    try:
        # Create application container (Strategy-only to avoid alpaca-py dependency)
        container = ApplicationContainer.create_for_strategy("production")

        # Note: Market status check removed - Strategy runs on schedule (Mon-Fri 9:35 AM).
        # If market is closed, Portfolio/Execution will handle gracefully.
        # This removes alpaca-py dependency from Strategy Lambda.

        # Create the WorkflowStarted event (used internally by handler)
        workflow_event = WorkflowStarted(
            correlation_id=correlation_id,
            causation_id=f"schedule-{datetime.now(UTC).isoformat()}",
            event_id=f"workflow-started-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="strategy_v2.lambda_handler",
            source_component="StrategyLambda",
            workflow_type="trading",
            requested_by="EventBridgeSchedule",
            configuration={
                "live_trading": not container.config.paper_trading(),
            },
        )

        # Create handler
        handler = SignalGenerationHandler(container)

        # Capture the generated event
        generated_event: SignalGenerated | None = None
        failed_event: WorkflowFailed | None = None

        def capture_signal(evt: BaseEvent) -> None:
            nonlocal generated_event
            if isinstance(evt, SignalGenerated):
                generated_event = evt

        def capture_failure(evt: BaseEvent) -> None:
            nonlocal failed_event
            if isinstance(evt, WorkflowFailed):
                failed_event = evt

        # Subscribe to capture events
        handler.event_bus.subscribe("SignalGenerated", capture_signal)
        handler.event_bus.subscribe("WorkflowFailed", capture_failure)

        # Run signal generation
        handler.handle_event(workflow_event)

        # Publish result to EventBridge
        if generated_event is not None:
            publish_to_eventbridge(generated_event)
            logger.info(
                "Signal generation completed successfully",
                extra={
                    "correlation_id": correlation_id,
                    "signal_count": generated_event.signal_count,
                },
            )
            return {
                "statusCode": 200,
                "body": {
                    "status": "success",
                    "correlation_id": correlation_id,
                    "signal_count": generated_event.signal_count,
                },
            }

        if failed_event is not None:
            publish_to_eventbridge(failed_event)
            logger.error(
                "Signal generation failed",
                extra={
                    "correlation_id": correlation_id,
                    "failure_reason": failed_event.failure_reason,
                },
            )
            return {
                "statusCode": 500,
                "body": {
                    "status": "failed",
                    "correlation_id": correlation_id,
                    "error": failed_event.failure_reason,
                },
            }

        # No event captured - unexpected state
        logger.error(
            "Signal generation completed but no event was published",
            extra={"correlation_id": correlation_id},
        )
        return {
            "statusCode": 500,
            "body": {
                "status": "error",
                "correlation_id": correlation_id,
                "error": "No SignalGenerated or WorkflowFailed event was published",
            },
        }

    except Exception as e:
        logger.error(
            "Strategy Lambda failed with exception",
            extra={"correlation_id": correlation_id, "error": str(e)},
            exc_info=True,
        )

        # Publish WorkflowFailed to EventBridge
        try:
            failure_event = WorkflowFailed(
                correlation_id=correlation_id,
                causation_id=correlation_id,
                event_id=f"workflow-failed-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="strategy_v2",
                source_component="lambda_handler",
                workflow_type="signal_generation",
                failure_reason=str(e),
                failure_step="signal_generation",
                error_details={"exception_type": type(e).__name__},
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
                "correlation_id": correlation_id,
                "error": str(e),
            },
        }
