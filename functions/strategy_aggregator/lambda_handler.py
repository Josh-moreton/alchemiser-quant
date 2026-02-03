"""Business Unit: aggregator_v2 | Status: current.

Lambda handler for Signal Aggregator microservice.

The Aggregator collects partial signals from parallel Strategy Lambda
invocations and merges them into a single SignalGenerated event that
triggers Portfolio Lambda (preserving the existing workflow).

Supports partial failure resilience: if some strategies fail, the workflow
proceeds with the successful ones and sends an alert notification.

Trigger: EventBridge rule matching PartialSignalGenerated events.
"""

from __future__ import annotations

import html
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from aggregator_settings import AggregatorSettings
from portfolio_merger import PortfolioMerger

from the_alchemiser.shared.events import (
    SignalGenerated,
    SystemNotificationRequested,
    WorkflowFailed,
)
from the_alchemiser.shared.events.eventbridge_publisher import (
    publish_to_eventbridge,
    unwrap_eventbridge_event,
)
from the_alchemiser.shared.logging import configure_application_logging, get_logger
from the_alchemiser.shared.services.aggregation_session_service import (
    AggregationSessionService,
)

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

        # Emit stuck sessions metric on each invocation for monitoring
        # This feeds the StuckAggregationSessionsAlarm in CloudWatch
        try:
            stuck_count = session_service.emit_stuck_sessions_metric(max_age_minutes=30)
            if stuck_count > 0:
                logger.warning(
                    f"Detected {stuck_count} stuck aggregation sessions",
                    extra={"correlation_id": correlation_id, "stuck_count": stuck_count},
                )
        except Exception as metric_error:
            logger.debug(
                f"Failed to emit stuck sessions metric: {metric_error}",
                extra={"correlation_id": correlation_id},
            )

        # Extract partial signal data
        allocation = Decimal(str(detail.get("allocation", "0")))
        consolidated_portfolio = detail.get("consolidated_portfolio", {})
        signals_data = detail.get("signals_data", {})
        signal_count = detail.get("signal_count", 0)
        data_freshness = detail.get("data_freshness", {})
        success = detail.get("success", True)  # Default True for backward compatibility
        error_message = detail.get("error_message")

        if not success:
            logger.warning(
                "Received failed partial signal",
                extra={
                    "session_id": session_id,
                    "correlation_id": correlation_id,
                    "dsl_file": dsl_file,
                    "error_message": error_message,
                },
            )

        # Store partial signal and get updated completion count
        completed_count = session_service.store_partial_signal(
            session_id=session_id,
            dsl_file=dsl_file,
            allocation=allocation,
            consolidated_portfolio=consolidated_portfolio,
            signals_data=signals_data,
            signal_count=signal_count,
            data_freshness=data_freshness,
            success=success,
            error_message=error_message,
        )

        # Get session to check total
        session = session_service.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        total_strategies = session["total_strategies"]
        failed_strategies = session.get("failed_strategies", 0)

        logger.info(
            "Stored partial signal",
            extra={
                "session_id": session_id,
                "dsl_file": dsl_file,
                "completed_strategies": completed_count,
                "total_strategies": total_strategies,
                "failed_strategies": failed_strategies,
                "success": success,
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
                    "failed_strategies": failed_strategies,
                },
            }

        # All strategies completed - aggregate!
        logger.info(
            "All strategies completed, starting aggregation",
            extra={
                "session_id": session_id,
                "correlation_id": correlation_id,
                "total_strategies": total_strategies,
                "failed_strategies": failed_strategies,
            },
        )

        # Update session status
        session_service.update_session_status(session_id, "AGGREGATING")

        # Get all partial signals
        all_partial_signals = session_service.get_all_partial_signals(session_id)

        # Separate successful and failed signals
        successful_signals = [s for s in all_partial_signals if s.get("success", True)]
        failed_signals = [s for s in all_partial_signals if not s.get("success", True)]

        # If ALL strategies failed, publish WorkflowFailed and exit
        if not successful_signals:
            logger.error(
                "All strategies failed - cannot create portfolio",
                extra={
                    "session_id": session_id,
                    "correlation_id": correlation_id,
                    "total_strategies": total_strategies,
                    "failed_count": len(failed_signals),
                },
            )

            session_service.update_session_status(session_id, "FAILED")

            failure_details = [
                {"dsl_file": s["dsl_file"], "error": s.get("error_message", "Unknown")}
                for s in failed_signals
            ]

            failure_event = WorkflowFailed(
                correlation_id=correlation_id,
                causation_id=session_id,
                event_id=f"workflow-failed-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="aggregator_v2",
                source_component="SignalAggregator",
                workflow_type="signal_aggregation",
                failure_reason=f"All {total_strategies} strategies failed evaluation",
                failure_step="aggregation",
                error_details={
                    "session_id": session_id,
                    "total_strategies": total_strategies,
                    "failed_strategies": failure_details,
                },
            )
            publish_to_eventbridge(failure_event)

            return {
                "statusCode": 500,
                "body": {
                    "status": "all_strategies_failed",
                    "session_id": session_id,
                    "correlation_id": correlation_id,
                    "failed_count": len(failed_signals),
                },
            }

        # Log if we have partial failures but can proceed
        has_partial_failures = len(failed_signals) > 0
        if has_partial_failures:
            logger.warning(
                "Aggregating with partial failures",
                extra={
                    "session_id": session_id,
                    "correlation_id": correlation_id,
                    "successful_count": len(successful_signals),
                    "failed_count": len(failed_signals),
                    "failed_files": [s["dsl_file"] for s in failed_signals],
                },
            )

        # Merge portfolios (only from successful signals)
        merged_portfolio = portfolio_merger.merge_portfolios(
            partial_signals=successful_signals,
            correlation_id=correlation_id,
        )

        # Merge signals data (lightweight - just strategy names for Portfolio Lambda)
        merged_signals_data = portfolio_merger.merge_signals_data(
            partial_signals=successful_signals,
            lightweight=True,  # Reduce payload size for EventBridge
        )

        # Calculate total signal count (only from successful signals)
        total_signal_count = sum(p.get("signal_count", 0) for p in successful_signals)

        # Aggregate data freshness from successful partial signals (use worst case)
        aggregated_data_freshness = _aggregate_data_freshness(successful_signals)

        # Serialize portfolio for EventBridge including strategy_contributions
        # Strategy contributions are essential for per-strategy P&L attribution
        # Payload size is minimal: ~15 strategies * ~50 symbols = ~2KB well under 256KB limit
        portfolio_for_event = {
            "target_allocations": {
                k: str(v) for k, v in merged_portfolio.target_allocations.items()
            },
            "strategy_contributions": {
                strategy: {symbol: str(weight) for symbol, weight in allocations.items()}
                for strategy, allocations in merged_portfolio.strategy_contributions.items()
            },
            "correlation_id": merged_portfolio.correlation_id,
            "timestamp": merged_portfolio.timestamp.isoformat(),
            "strategy_count": merged_portfolio.strategy_count,
            "source_strategies": merged_portfolio.source_strategies,
            "schema_version": merged_portfolio.schema_version,
            # Set is_partial=True if some strategies failed (partial failure resilience)
            "is_partial": has_partial_failures or merged_portfolio.is_partial,
        }

        # Build metadata with failure info if applicable
        event_metadata: dict[str, Any] = {
            "aggregation_session_id": session_id,
            "strategies_aggregated": len(successful_signals),
            "aggregation_mode": "multi_node",
        }

        if has_partial_failures:
            event_metadata["partial_failure"] = True
            event_metadata["failed_strategies_count"] = len(failed_signals)
            event_metadata["failed_dsl_files"] = [s["dsl_file"] for s in failed_signals]

        # Build consolidated SignalGenerated event
        signal_event = SignalGenerated(
            event_id=f"signal-generated-{uuid.uuid4()}",
            correlation_id=correlation_id,
            causation_id=session_id,
            timestamp=datetime.now(UTC),
            source_module="aggregator_v2",
            source_component="SignalAggregator",
            signals_data=merged_signals_data,
            consolidated_portfolio=portfolio_for_event,
            signal_count=total_signal_count,
            metadata=event_metadata,
            data_freshness=aggregated_data_freshness,
        )

        # Publish to EventBridge (triggers Portfolio Lambda)
        publish_to_eventbridge(signal_event)

        # Store merged signal in DynamoDB for dashboard visibility
        session_service.store_merged_signal(
            session_id=session_id,
            merged_signal=portfolio_for_event,
        )

        # Mark session as completed
        session_service.update_session_status(session_id, "COMPLETED")

        # Send partial failure notification if there were any failures
        if has_partial_failures:
            _send_partial_failure_notification(
                correlation_id=correlation_id,
                session_id=session_id,
                successful_count=len(successful_signals),
                failed_signals=failed_signals,
                total_strategies=total_strategies,
            )

        log_level = "warning" if has_partial_failures else "info"
        log_message = (
            "Aggregation completed with partial failures"
            if has_partial_failures
            else "Aggregation completed successfully"
        )
        getattr(logger, log_level)(
            log_message,
            extra={
                "session_id": session_id,
                "correlation_id": correlation_id,
                "strategies_aggregated": len(successful_signals),
                "strategies_failed": len(failed_signals),
                "total_signals": total_signal_count,
                "symbols_in_portfolio": len(merged_portfolio.target_allocations),
                "is_partial": has_partial_failures,
            },
        )

        return {
            "statusCode": 200,
            "body": {
                "status": "aggregated",
                "session_id": session_id,
                "correlation_id": correlation_id,
                "strategies_aggregated": len(successful_signals),
                "strategies_failed": len(failed_signals),
                "total_signals": total_signal_count,
                "event_id": signal_event.event_id,
                "is_partial": has_partial_failures,
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


def _send_partial_failure_notification(
    correlation_id: str,
    session_id: str,
    successful_count: int,
    failed_signals: list[dict[str, Any]],
    total_strategies: int,
) -> None:
    """Send notification about partial strategy failures.

    Publishes a SystemNotificationRequested event to notify operators
    that some strategies failed but the workflow proceeded with the
    successful ones.

    Args:
        correlation_id: Workflow correlation ID.
        session_id: Aggregation session ID.
        successful_count: Number of strategies that succeeded.
        failed_signals: List of failed partial signal dicts.
        total_strategies: Total number of strategies in this session.

    """
    try:
        failed_count = len(failed_signals)

        # Build failure details for the notification
        # HTML-escape user-provided values to prevent XSS in email clients
        failure_rows = []
        for signal in failed_signals:
            dsl_file = html.escape(str(signal.get("dsl_file", "Unknown")))
            error = html.escape(str(signal.get("error_message", "Unknown error")))
            allocation = html.escape(str(signal.get("allocation", "?")))
            failure_rows.append(
                f"<tr><td>{dsl_file}</td><td>{allocation}</td><td>{error}</td></tr>"
            )

        failure_table = "\n".join(failure_rows)

        html_content = f"""
<h2>⚠️ Partial Strategy Failure Alert</h2>

<p><strong>Workflow proceeding with partial results.</strong></p>

<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse;" role="table" aria-label="Session metrics">
<tr><th scope="col">Metric</th><th scope="col">Value</th></tr>
<tr><td>Session ID</td><td>{session_id}</td></tr>
<tr><td>Correlation ID</td><td>{correlation_id}</td></tr>
<tr><td>Total Strategies</td><td>{total_strategies}</td></tr>
<tr><td>Succeeded</td><td style="color: green;">{successful_count}</td></tr>
<tr><td>Failed</td><td style="color: red;">{failed_count}</td></tr>
</table>

<h3>Failed Strategies</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse;" role="table" aria-label="Failed strategy details">
<tr><th scope="col">DSL File</th><th scope="col">Allocation</th><th scope="col">Error</th></tr>
{failure_table}
</table>

<p><em>The trading workflow will continue with the {successful_count} successful strategies.
Failed strategy allocations will be excluded from the portfolio (not redistributed).</em></p>

<p>Review CloudWatch logs for full error details.</p>
"""

        notification = SystemNotificationRequested(
            event_id=f"notification-{uuid.uuid4()}",
            correlation_id=correlation_id,
            causation_id=session_id,
            timestamp=datetime.now(UTC),
            source_module="aggregator_v2",
            source_component="SignalAggregator",
            notification_type="WARNING",
            subject=f"⚠️ Alchemiser Partial Failure: {successful_count}/{total_strategies} strategies succeeded",
            html_content=html_content,
            text_content=f"Partial failure: {failed_count}/{total_strategies} strategies failed. "
            f"Workflow proceeding with {successful_count} successful strategies.",
        )

        publish_to_eventbridge(notification)

        logger.info(
            "Sent partial failure notification",
            extra={
                "correlation_id": correlation_id,
                "session_id": session_id,
                "failed_count": failed_count,
                "successful_count": successful_count,
            },
        )

    except Exception as e:
        # Don't fail aggregation if notification fails
        logger.error(
            "Failed to send partial failure notification",
            extra={
                "correlation_id": correlation_id,
                "session_id": session_id,
                "error": str(e),
            },
        )


def _aggregate_data_freshness(partial_signals: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate data freshness info from all partial signals.

    Uses worst-case approach: reports the oldest data timestamp and
    FAIL gate status if any partial signal failed freshness check.

    Args:
        partial_signals: List of partial signal dicts from DynamoDB

    Returns:
        Aggregated data freshness dict with latest_timestamp, age_days, gate_status

    """
    if not partial_signals:
        return {
            "latest_timestamp": "N/A",
            "age_days": 0,
            "gate_status": "UNKNOWN",
        }

    oldest_timestamp = None
    max_age_days = 0
    any_failed = False

    for partial in partial_signals:
        freshness = partial.get("data_freshness", {})
        if not freshness:
            continue

        timestamp = freshness.get("latest_timestamp")
        age_days = freshness.get("age_days", 0)
        gate_status = freshness.get("gate_status", "UNKNOWN")

        # Track oldest timestamp (worst case)
        if (
            timestamp
            and timestamp != "N/A"
            and (oldest_timestamp is None or timestamp < oldest_timestamp)
        ):
            oldest_timestamp = timestamp

        # Track max age
        if age_days > max_age_days:
            max_age_days = age_days

        # Track any failures
        if gate_status == "FAIL":
            any_failed = True

    return {
        "latest_timestamp": oldest_timestamp or "N/A",
        "age_days": max_age_days,
        "gate_status": "FAIL" if any_failed else "PASS",
    }
