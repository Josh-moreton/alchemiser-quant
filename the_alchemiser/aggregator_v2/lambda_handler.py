"""Business Unit: aggregator_v2 | Status: current.

Lambda handler for Signal Aggregator microservice.

The Aggregator collects partial signals from parallel Strategy Lambda
invocations and merges them into a single SignalGenerated event that
triggers Portfolio Lambda (preserving the existing workflow).

Trigger: EventBridge rule matching PartialSignalGenerated events.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from the_alchemiser.coordinator_v2.services.aggregation_session_service import (
    AggregationSessionService,
)
from the_alchemiser.shared.events import SignalGenerated, WorkflowFailed
from the_alchemiser.shared.events.eventbridge_publisher import (
    publish_to_eventbridge,
    unwrap_eventbridge_event,
)
from the_alchemiser.shared.logging import configure_application_logging, get_logger

from .config.aggregator_settings import AggregatorSettings
from .services.portfolio_merger import PortfolioMerger

# Initialize logging on cold start
configure_application_logging()

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle PartialSignalGenerated events and aggregate signals.

    This handler:
    1. Extracts partial signal from EventBridge event
    2. Stores partial signal in DynamoDB
    3. Checks if all strategies have completed
    4. If complete: merges portfolios and publishes SignalGenerated

    Args:
        event: EventBridge event containing PartialSignalGenerated
        context: Lambda context

    Returns:
        Response indicating aggregation status.

    """
    # Unwrap EventBridge envelope
    detail = unwrap_eventbridge_event(event)

    session_id = detail.get("session_id", "")
    correlation_id = detail.get("correlation_id", "")
    dsl_file = detail.get("dsl_file", "")

    logger.info(
        "Aggregator received partial signal",
        extra={
            "session_id": session_id,
            "correlation_id": correlation_id,
            "dsl_file": dsl_file,
            "strategy_number": detail.get("strategy_number"),
            "total_strategies": detail.get("total_strategies"),
        },
    )

    try:
        # Load settings
        settings = AggregatorSettings.from_environment()

        # Initialize services
        session_service = AggregationSessionService(table_name=settings.aggregation_table_name)
        portfolio_merger = PortfolioMerger(allocation_tolerance=settings.allocation_tolerance)

        # Extract partial signal data
        allocation = Decimal(str(detail.get("allocation", "0")))
        consolidated_portfolio = detail.get("consolidated_portfolio", {})
        signals_data = detail.get("signals_data", {})
        signal_count = detail.get("signal_count", 0)

        # Store partial signal and get updated completion count
        completed_count = session_service.store_partial_signal(
            session_id=session_id,
            dsl_file=dsl_file,
            allocation=allocation,
            consolidated_portfolio=consolidated_portfolio,
            signals_data=signals_data,
            signal_count=signal_count,
        )

        # Get session to check total
        session = session_service.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        total_strategies = session["total_strategies"]

        logger.info(
            "Stored partial signal",
            extra={
                "session_id": session_id,
                "dsl_file": dsl_file,
                "completed_strategies": completed_count,
                "total_strategies": total_strategies,
            },
        )

        # Check if all strategies have completed
        if completed_count < total_strategies:
            return {
                "statusCode": 200,
                "body": {
                    "status": "waiting",
                    "session_id": session_id,
                    "completed_strategies": completed_count,
                    "total_strategies": total_strategies,
                },
            }

        # All strategies completed - aggregate!
        logger.info(
            "All strategies completed, starting aggregation",
            extra={
                "session_id": session_id,
                "correlation_id": correlation_id,
                "total_strategies": total_strategies,
            },
        )

        # Update session status
        session_service.update_session_status(session_id, "AGGREGATING")

        # Get all partial signals
        all_partial_signals = session_service.get_all_partial_signals(session_id)

        # Merge portfolios
        merged_portfolio = portfolio_merger.merge_portfolios(
            partial_signals=all_partial_signals,
            correlation_id=correlation_id,
        )

        # Merge signals data
        merged_signals_data = portfolio_merger.merge_signals_data(
            partial_signals=all_partial_signals
        )

        # Calculate total signal count
        total_signal_count = sum(p.get("signal_count", 0) for p in all_partial_signals)

        # Build consolidated SignalGenerated event
        signal_event = SignalGenerated(
            event_id=f"signal-generated-{uuid.uuid4()}",
            correlation_id=correlation_id,
            causation_id=session_id,
            timestamp=datetime.now(UTC),
            source_module="aggregator_v2",
            source_component="SignalAggregator",
            signals_data=merged_signals_data,
            consolidated_portfolio=merged_portfolio.model_dump(mode="json"),
            signal_count=total_signal_count,
            metadata={
                "aggregation_session_id": session_id,
                "strategies_aggregated": len(all_partial_signals),
                "aggregation_mode": "multi_node",
            },
        )

        # Publish to EventBridge (triggers Portfolio Lambda)
        publish_to_eventbridge(signal_event)

        # Mark session as completed
        session_service.update_session_status(session_id, "COMPLETED")

        logger.info(
            "Aggregation completed successfully",
            extra={
                "session_id": session_id,
                "correlation_id": correlation_id,
                "strategies_aggregated": len(all_partial_signals),
                "total_signals": total_signal_count,
                "symbols_in_portfolio": len(merged_portfolio.target_allocations),
            },
        )

        return {
            "statusCode": 200,
            "body": {
                "status": "aggregated",
                "session_id": session_id,
                "correlation_id": correlation_id,
                "strategies_aggregated": len(all_partial_signals),
                "total_signals": total_signal_count,
                "event_id": signal_event.event_id,
            },
        }

    except Exception as e:
        logger.error(
            "Aggregator failed",
            extra={
                "session_id": session_id,
                "correlation_id": correlation_id,
                "dsl_file": dsl_file,
                "error": str(e),
            },
            exc_info=True,
        )

        # Try to mark session as failed
        try:
            settings = AggregatorSettings.from_environment()
            session_service = AggregationSessionService(table_name=settings.aggregation_table_name)
            session_service.update_session_status(session_id, "FAILED")
        except Exception as status_error:
            logger.warning(
                "Failed to update session status to FAILED",
                extra={"session_id": session_id, "error": str(status_error)},
            )

        # Publish WorkflowFailed to EventBridge
        try:
            failure_event = WorkflowFailed(
                correlation_id=correlation_id,
                causation_id=session_id,
                event_id=f"workflow-failed-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="aggregator_v2",
                source_component="lambda_handler",
                workflow_type="signal_aggregation",
                failure_reason=str(e),
                failure_step="aggregation",
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
                "error": str(e),
            },
        }
