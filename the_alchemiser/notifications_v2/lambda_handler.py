"""Business Unit: notifications | Status: current.

Lambda handler for event-driven notifications microservice.

Consumes TradeExecuted and WorkflowFailed events from EventBridge and sends
email notifications using the NotificationService.

Supports two execution modes:
1. Legacy mode: Single TradeExecuted event per workflow - send notification immediately
2. Per-trade mode: Multiple TradeExecuted events per run - aggregate when all complete
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

from the_alchemiser.notifications_v2.service import NotificationService
from the_alchemiser.notifications_v2.strategy_report_service import (
    generate_performance_report_url,
)
from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.events.eventbridge_publisher import unwrap_eventbridge_event
from the_alchemiser.shared.events.schemas import (
    ErrorNotificationRequested,
    TradingNotificationRequested,
)
from the_alchemiser.shared.logging import configure_application_logging, get_logger
from the_alchemiser.shared.services.execution_run_service import (
    ExecutionRunService,
)

# Initialize logging on cold start (must be before get_logger)
configure_application_logging()

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle TradeExecuted and WorkflowFailed events and send notifications.

    This Lambda is triggered by EventBridge when TradeExecuted or WorkflowFailed
    events are published. It builds appropriate notification events and processes
    them through the NotificationService to send emails.

    Args:
        event: EventBridge event containing TradeExecuted or WorkflowFailed details
        context: Lambda context

    Returns:
        Response with status code and message

    """
    correlation_id = str(uuid4())

    try:
        # Extract EventBridge envelope metadata before unwrapping
        # Note: unwrap_eventbridge_event returns the 'detail' payload directly,
        # so we need to extract metadata from the original event
        detail_type = event.get("detail-type", "")
        source = event.get("source", "")

        # Unwrap EventBridge envelope to get the actual event payload
        detail = unwrap_eventbridge_event(event)

        # Extract correlation_id from event if available
        correlation_id = detail.get("correlation_id", correlation_id)

        logger.info(
            "Notifications Lambda invoked",
            extra={
                "correlation_id": correlation_id,
                "detail_type": detail_type,
                "source": source,
            },
        )

        # Route to appropriate handler based on event type
        if detail_type == "TradeExecuted":
            return _handle_trade_executed(detail, correlation_id)
        if detail_type == "WorkflowFailed":
            return _handle_workflow_failed(detail, correlation_id, source)
        logger.debug(
            f"Ignoring unsupported event type: {detail_type}",
            extra={"correlation_id": correlation_id},
        )
        return {
            "statusCode": 200,
            "body": f"Ignored event type: {detail_type}",
        }

    except Exception as e:
        logger.error(
            f"Notifications Lambda failed: {e}",
            exc_info=True,
            extra={
                "correlation_id": correlation_id,
                "error_type": type(e).__name__,
            },
        )
        # Don't raise - notifications shouldn't fail the workflow
        return {
            "statusCode": 500,
            "body": f"Notification failed: {e!s}",
        }


def _handle_trade_executed(detail: dict[str, Any], correlation_id: str) -> dict[str, Any]:
    """Handle TradeExecuted events by sending trading notifications.

    Supports two modes:
    1. Legacy mode: Single TradeExecuted event per workflow - send notification immediately
    2. Per-trade mode: Check if run is complete, aggregate results, send single notification

    Args:
        detail: The detail payload from TradeExecuted event
        correlation_id: Correlation ID for tracing

    Returns:
        Response with status code and message

    """
    # Check if this is a per-trade execution event
    metadata = detail.get("metadata", {})
    execution_mode = metadata.get("execution_mode", "legacy")
    run_id = metadata.get("run_id")

    if execution_mode == "per_trade" and run_id:
        return _handle_per_trade_executed(detail, correlation_id, run_id)

    # Legacy mode: Process single TradeExecuted event immediately
    return _handle_legacy_trade_executed(detail, correlation_id)


def _handle_per_trade_executed(
    detail: dict[str, Any], correlation_id: str, run_id: str
) -> dict[str, Any]:
    """Handle TradeExecuted events from per-trade execution mode.

    Checks if all trades in the run are complete. If so, aggregates results
    and sends a single notification. If not, returns without sending notification.

    Args:
        detail: The detail payload from TradeExecuted event
        correlation_id: Correlation ID for tracing
        run_id: Execution run identifier

    Returns:
        Response with status code and message

    """
    trade_id = detail.get("metadata", {}).get("trade_id", "unknown")

    logger.info(
        f"Per-trade execution: Checking run completion for trade {trade_id}",
        extra={
            "correlation_id": correlation_id,
            "run_id": run_id,
            "trade_id": trade_id,
        },
    )

    # Initialize ExecutionRunService
    table_name = os.environ.get("EXECUTION_RUNS_TABLE", "ExecutionRunsTable")
    run_service = ExecutionRunService(table_name=table_name)

    # Check if run is complete
    if not run_service.is_run_complete(run_id):
        # Not all trades complete yet - wait for more events
        logger.info(
            f"Run {run_id} not yet complete - waiting for more trades",
            extra={
                "correlation_id": correlation_id,
                "run_id": run_id,
                "trade_id": trade_id,
            },
        )
        return {
            "statusCode": 200,
            "body": f"Trade {trade_id} recorded, run not yet complete",
        }

    # Run is complete - try to finalize and send notification
    # Use conditional update to ensure only one invocation sends notification
    finalized = run_service.mark_run_completed(run_id)

    if not finalized:
        # Another invocation already finalized - skip notification
        logger.info(
            f"Run {run_id} already finalized by another invocation",
            extra={
                "correlation_id": correlation_id,
                "run_id": run_id,
            },
        )
        return {
            "statusCode": 200,
            "body": f"Run {run_id} already finalized",
        }

    # This invocation wins - aggregate and send notification
    logger.info(
        f"🏁 Run {run_id} complete - aggregating results and sending notification",
        extra={
            "correlation_id": correlation_id,
            "run_id": run_id,
        },
    )

    # Get run metadata and all trade results
    run_metadata = run_service.get_run(run_id)
    trade_results = run_service.get_all_trade_results(run_id)

    # Build aggregated TradeExecuted-like detail for notification
    aggregated_detail = _aggregate_trade_results(run_metadata, trade_results, correlation_id)

    # Process as legacy notification with aggregated data
    return _handle_legacy_trade_executed(aggregated_detail, correlation_id)


def _aggregate_trade_results(
    run_metadata: dict[str, Any] | None,
    trade_results: list[dict[str, Any]],
    correlation_id: str,
) -> dict[str, Any]:
    """Aggregate individual trade results into a single notification payload.

    Args:
        run_metadata: Run metadata from DynamoDB
        trade_results: List of individual trade results
        correlation_id: Correlation ID for tracing

    Returns:
        Aggregated detail dict in TradeExecuted format

    """
    if not run_metadata:
        run_metadata = {}

    total_trades = run_metadata.get("total_trades", len(trade_results))
    succeeded_trades = run_metadata.get("succeeded_trades", 0)
    failed_trades = run_metadata.get("failed_trades", 0)

    # Calculate total trade value
    total_trade_value = Decimal("0")
    orders_executed = []
    failed_symbols = []

    for trade in trade_results:
        trade_amount = trade.get("trade_amount", Decimal("0"))
        if isinstance(trade_amount, str):
            trade_amount = Decimal(trade_amount)
        total_trade_value += abs(trade_amount)

        # Build order summary for notification
        order_summary = {
            "symbol": trade.get("symbol"),
            "action": trade.get("action"),
            "status": trade.get("status"),
            "order_id": trade.get("order_id"),
            "trade_amount": str(trade_amount),
        }
        orders_executed.append(order_summary)

        # Track failed symbols
        if trade.get("status") == "FAILED":
            failed_symbols.append(trade.get("symbol", "unknown"))

    # Build aggregated payload
    return {
        "correlation_id": correlation_id,
        "event_id": f"aggregated-trade-executed-{run_metadata.get('run_id', 'unknown')}",
        "orders_placed": total_trades,
        "orders_succeeded": succeeded_trades,
        "success": failed_trades == 0,
        "metadata": {
            "execution_mode": "per_trade_aggregated",
            "run_id": run_metadata.get("run_id"),
            "plan_id": run_metadata.get("plan_id"),
            "total_trade_value": str(total_trade_value),
        },
        "execution_data": {
            "orders_executed": orders_executed,
            "execution_summary": {
                "total_trades": total_trades,
                "succeeded": succeeded_trades,
                "failed": failed_trades,
                "total_value": str(total_trade_value),
            },
        },
        "failure_reason": f"Failed symbols: {', '.join(failed_symbols)}"
        if failed_symbols
        else None,
        "failed_symbols": failed_symbols,
    }


def _handle_legacy_trade_executed(detail: dict[str, Any], correlation_id: str) -> dict[str, Any]:
    """Handle TradeExecuted events in legacy mode (single event per workflow).

    Args:
        detail: The detail payload from TradeExecuted event
        correlation_id: Correlation ID for tracing

    Returns:
        Response with status code and message

    """
    # Create minimal ApplicationContainer for notifications (no pandas/business modules)
    container = ApplicationContainer.create_for_notifications("production")

    # Generate strategy performance report and get presigned URL
    report_url = _generate_strategy_report(correlation_id)

    # Build TradingNotificationRequested from TradeExecuted event
    notification_event = _build_trading_notification(detail, correlation_id, container, report_url)

    # Create NotificationService and process the event
    notification_service = NotificationService(container)
    notification_service.handle_event(notification_event)

    logger.info(
        "Trading notification processed successfully",
        extra={
            "correlation_id": correlation_id,
            "trading_success": notification_event.trading_success,
            "orders_placed": notification_event.orders_placed,
            "report_url_included": report_url is not None,
        },
    )

    return {
        "statusCode": 200,
        "body": f"Notification sent for correlation_id: {correlation_id}",
    }


def _handle_workflow_failed(
    detail: dict[str, Any], correlation_id: str, source: str
) -> dict[str, Any]:
    """Handle WorkflowFailed events by sending error notifications.

    Args:
        detail: The detail payload from WorkflowFailed event
        correlation_id: Correlation ID for tracing
        source: Event source (e.g., alchemiser.strategy, alchemiser.portfolio)

    Returns:
        Response with status code and message

    """
    # Create ApplicationContainer for dependencies
    logger.info(
        "Creating minimal ApplicationContainer for notifications (no pandas/business modules)"
    )
    container = ApplicationContainer.create_for_notifications("production")
    logger.info("Processing WorkflowFailed event")
    notification_event = _build_error_notification(detail, correlation_id, source)

    # Create NotificationService and process the event
    notification_service = NotificationService(container)
    notification_service.handle_event(notification_event)

    logger.info(
        "Error notification processed successfully",
        extra={
            "correlation_id": correlation_id,
            "failure_step": detail.get("failure_step", "unknown"),
            "workflow_type": detail.get("workflow_type", "unknown"),
        },
    )

    return {
        "statusCode": 200,
        "body": f"Error notification sent for correlation_id: {correlation_id}",
    }


def _build_error_notification(
    workflow_failed_detail: dict[str, Any],
    correlation_id: str,
    source: str,
) -> ErrorNotificationRequested:
    """Build ErrorNotificationRequested from WorkflowFailed event detail.

    Args:
        workflow_failed_detail: The detail payload from WorkflowFailed event
        correlation_id: Correlation ID for tracing
        source: Event source for context

    Returns:
        ErrorNotificationRequested event ready for processing

    """
    # Extract fields from WorkflowFailed event
    workflow_type = workflow_failed_detail.get("workflow_type", "unknown")
    failure_reason = workflow_failed_detail.get("failure_reason", "Unknown error")
    failure_step = workflow_failed_detail.get("failure_step", "unknown")
    error_details = workflow_failed_detail.get("error_details", {})

    # Determine source module from event source
    source_module = source.replace("alchemiser.", "") if source else "unknown"

    # Build error report content
    error_report = f"""
Workflow Failure Report
=======================

Workflow Type: {workflow_type}
Failed Step: {failure_step}
Source Module: {source_module}
Correlation ID: {correlation_id}

Failure Reason:
{failure_reason}

Error Details:
{_format_error_details(error_details)}
"""

    return ErrorNotificationRequested(
        correlation_id=correlation_id,
        causation_id=workflow_failed_detail.get("event_id", correlation_id),
        event_id=f"error-notification-{uuid4()}",
        timestamp=datetime.now(UTC),
        source_module="notifications_v2.lambda_handler",
        source_component="NotificationsLambda",
        error_severity="CRITICAL",
        error_priority="HIGH",
        error_title=f"Workflow Failed: {failure_step}",
        error_report=error_report.strip(),
        error_code=error_details.get("exception_type"),
    )


def _format_error_details(error_details: dict[str, Any]) -> str:
    """Format error details dictionary for email display.

    Args:
        error_details: Dictionary of error details

    Returns:
        Formatted string representation

    """
    if not error_details:
        return "No additional details available"

    lines = []
    for key, value in error_details.items():
        lines.append(f"  - {key}: {value}")
    return "\n".join(lines)


def _generate_strategy_report(correlation_id: str) -> str | None:
    """Generate strategy performance report and return presigned URL.

    Args:
        correlation_id: Correlation ID for tracing

    Returns:
        Presigned URL for CSV download, or None if generation fails

    """
    try:
        report_url = generate_performance_report_url(correlation_id=correlation_id)

        if report_url:
            logger.info(
                "Strategy performance report generated",
                extra={"correlation_id": correlation_id},
            )
        else:
            logger.debug(
                "Strategy performance report not generated (no data or not configured)",
                extra={"correlation_id": correlation_id},
            )

        return report_url

    except Exception as e:
        # Don't fail the notification if report generation fails
        logger.warning(
            f"Failed to generate strategy performance report: {e}",
            extra={
                "correlation_id": correlation_id,
                "error_type": type(e).__name__,
            },
        )
        return None


def _build_trading_notification(
    trade_executed_detail: dict[str, Any],
    correlation_id: str,
    container: ApplicationContainer,
    report_url: str | None = None,
) -> TradingNotificationRequested:
    """Build TradingNotificationRequested from TradeExecuted event detail.

    Args:
        trade_executed_detail: The detail payload from TradeExecuted event
        correlation_id: Correlation ID for tracing
        container: Application container for config access
        report_url: Optional presigned URL for strategy performance CSV report

    Returns:
        TradingNotificationRequested event ready for processing

    """
    # Determine trading mode from container config
    mode_str = "LIVE" if not container.config.paper_trading() else "PAPER"

    # Extract fields from TradeExecuted event
    orders_placed = trade_executed_detail.get("orders_placed", 0)
    orders_succeeded = trade_executed_detail.get("orders_succeeded", 0)
    trading_success = orders_succeeded > 0 and orders_succeeded == orders_placed

    # Build execution data for email template
    execution_data: dict[str, Any] = {
        "orders_executed": trade_executed_detail.get("orders_executed", []),
        "execution_summary": trade_executed_detail.get("execution_summary", {}),
    }

    # Add report URL to execution_data if available
    if report_url:
        execution_data["strategy_performance_report_url"] = report_url

    # Extract capital deployed percentage from event metadata
    capital_deployed_pct = _extract_capital_deployed_pct(trade_executed_detail)

    # Extract error details if present
    error_message = trade_executed_detail.get("error_message")
    error_code = trade_executed_detail.get("error_code")

    return TradingNotificationRequested(
        correlation_id=correlation_id,
        causation_id=trade_executed_detail.get("event_id", correlation_id),
        event_id=f"trading-notification-{uuid4()}",
        timestamp=datetime.now(UTC),
        source_module="notifications_v2.lambda_handler",
        source_component="NotificationsLambda",
        trading_success=trading_success,
        trading_mode=mode_str,
        orders_placed=orders_placed,
        orders_succeeded=orders_succeeded,
        capital_deployed_pct=capital_deployed_pct,
        execution_data=execution_data,
        error_message=error_message,
        error_code=error_code,
    )


def _extract_capital_deployed_pct(trade_executed_detail: dict[str, Any]) -> Decimal | None:
    """Extract capital deployed percentage from TradeExecuted event.

    Args:
        trade_executed_detail: The detail payload from TradeExecuted event

    Returns:
        Capital deployed percentage as Decimal, or None if not available

    """
    # Try metadata first (where execution handler stores it)
    metadata = trade_executed_detail.get("metadata", {})
    if isinstance(metadata, dict):
        capital_pct = metadata.get("capital_deployed_pct")
        if capital_pct is not None:
            try:
                return Decimal(str(capital_pct))
            except (TypeError, ValueError):
                pass

    return None
