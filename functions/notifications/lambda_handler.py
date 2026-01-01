"""Business Unit: notifications | Status: current.

Lambda handler for event-driven notifications microservice.

Consumes AllTradesCompleted (from TradeAggregator) and WorkflowFailed events
from EventBridge and sends email notifications using the NotificationService.

This is a stateless handler - all aggregation logic lives in TradeAggregator.
Each event triggers exactly one notification, eliminating race conditions.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

from service import NotificationService
from strategy_report_service import generate_performance_report_url

from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.events.eventbridge_publisher import unwrap_eventbridge_event
from the_alchemiser.shared.events.schemas import (
    DataLakeNotificationRequested,
    ErrorNotificationRequested,
    TradingNotificationRequested,
)
from the_alchemiser.shared.logging import configure_application_logging, get_logger

# Initialize logging on cold start (must be before get_logger)
configure_application_logging()

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle AllTradesCompleted and WorkflowFailed events and send notifications.

    This Lambda is triggered by EventBridge:
    - AllTradesCompleted: From TradeAggregator when all trades in a run finish
    - WorkflowFailed: From any alchemiser module on failure

    Args:
        event: EventBridge event
        context: Lambda context

    Returns:
        Response with status code and message

    """
    correlation_id = str(uuid4())

    try:
        # Extract EventBridge envelope metadata
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
        if detail_type == "AllTradesCompleted":
            return _handle_all_trades_completed(detail, correlation_id)
        if detail_type == "WorkflowFailed":
            return _handle_workflow_failed(detail, correlation_id, source)
        if detail_type == "DataLakeUpdateCompleted":
            return _handle_data_lake_update(detail, correlation_id)

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


def _handle_all_trades_completed(detail: dict[str, Any], correlation_id: str) -> dict[str, Any]:
    """Handle AllTradesCompleted event from TradeAggregator.

    This is the primary handler - receives pre-aggregated trade data
    and sends a single notification. No racing or locking needed.

    Args:
        detail: The detail payload from AllTradesCompleted event
        correlation_id: Correlation ID for tracing

    Returns:
        Response with status code and message

    """
    run_id = detail.get("run_id", "unknown")
    total_trades = detail.get("total_trades", 0)
    succeeded_trades = detail.get("succeeded_trades", 0)
    failed_trades = detail.get("failed_trades", 0)

    logger.info(
        f"🏁 Processing AllTradesCompleted for run {run_id}",
        extra={
            "correlation_id": correlation_id,
            "run_id": run_id,
            "total_trades": total_trades,
            "succeeded_trades": succeeded_trades,
            "failed_trades": failed_trades,
        },
    )

    # Create minimal ApplicationContainer for notifications
    container = ApplicationContainer.create_for_notifications("production")

    # Generate strategy performance report and get presigned URL
    report_url = _generate_strategy_report(correlation_id)

    # Build TradingNotificationRequested from AllTradesCompleted event
    notification_event = _build_trading_notification_from_aggregated(
        detail, correlation_id, container, report_url
    )

    # Create NotificationService and process the event
    notification_service = NotificationService(container)
    notification_service.handle_event(notification_event)

    logger.info(
        "✅ Trading notification sent successfully",
        extra={
            "correlation_id": correlation_id,
            "run_id": run_id,
            "trading_success": notification_event.trading_success,
            "orders_placed": notification_event.orders_placed,
            "report_url_included": report_url is not None,
        },
    )

    return {
        "statusCode": 200,
        "body": f"Notification sent for run {run_id}",
    }


def _build_trading_notification_from_aggregated(
    all_trades_detail: dict[str, Any],
    correlation_id: str,
    container: ApplicationContainer,
    report_url: str | None = None,
) -> TradingNotificationRequested:
    """Build TradingNotificationRequested from AllTradesCompleted event.

    Args:
        all_trades_detail: The detail payload from AllTradesCompleted event
        correlation_id: Correlation ID for tracing
        container: Application container for config access
        report_url: Optional presigned URL for strategy performance CSV report

    Returns:
        TradingNotificationRequested event ready for processing

    """
    # Determine trading mode from container config
    mode_str = "LIVE" if not container.config.paper_trading() else "PAPER"

    # Extract fields from AllTradesCompleted event
    total_trades = all_trades_detail.get("total_trades", 0)
    succeeded_trades = all_trades_detail.get("succeeded_trades", 0)
    failed_trades = all_trades_detail.get("failed_trades", 0)
    skipped_trades = all_trades_detail.get("skipped_trades", 0)

    # Trading is successful if there are trades and none failed
    # Skipped trades don't count as failures
    trading_success = total_trades > 0 and failed_trades == 0

    # Get pre-aggregated execution data
    aggregated_data = all_trades_detail.get("aggregated_execution_data", {})

    # Get portfolio snapshot (always fetched from Alpaca by TradeAggregator)
    portfolio_snapshot = all_trades_detail.get("portfolio_snapshot", {})

    # Get timing info
    started_at = all_trades_detail.get("started_at", "")
    completed_at = all_trades_detail.get("completed_at", "")

    # Get data freshness (propagated from strategy workers if available)
    data_freshness = all_trades_detail.get("data_freshness", {})

    # Build execution data for email template with all enriched data
    execution_data: dict[str, Any] = {
        "orders_executed": aggregated_data.get("orders_executed", []),
        "execution_summary": aggregated_data.get("execution_summary", {}),
        # Portfolio snapshot for email template
        "equity": portfolio_snapshot.get("equity", 0),
        "cash": portfolio_snapshot.get("cash", 0),
        "gross_exposure": portfolio_snapshot.get("gross_exposure", 0),
        "net_exposure": portfolio_snapshot.get("net_exposure", 0),
        "top_positions": portfolio_snapshot.get("top_positions", []),
        # Timing info
        "start_time_utc": started_at,
        "end_time_utc": completed_at,
        # Data freshness
        "data_freshness": data_freshness,
    }

    # Add report URL to execution_data if available
    if report_url:
        execution_data["strategy_performance_report_url"] = report_url

    # Extract capital deployed percentage (already captured by TradeAggregator)
    capital_deployed_pct = _extract_capital_deployed_pct(all_trades_detail)

    # Get failed symbols for error reporting
    failed_symbols = all_trades_detail.get("failed_symbols", [])
    error_message = f"Failed symbols: {', '.join(failed_symbols)}" if failed_symbols else None

    return TradingNotificationRequested(
        correlation_id=correlation_id,
        causation_id=all_trades_detail.get("event_id", correlation_id),
        event_id=f"trading-notification-{uuid4()}",
        timestamp=datetime.now(UTC),
        source_module="notifications_v2.lambda_handler",
        source_component="NotificationsLambda",
        trading_success=trading_success,
        trading_mode=mode_str,
        orders_placed=total_trades,
        orders_succeeded=succeeded_trades,
        orders_skipped=skipped_trades,
        capital_deployed_pct=capital_deployed_pct,
        execution_data=execution_data,
        error_message=error_message,
        error_code=None,
    )


def _extract_capital_deployed_pct(event_detail: dict[str, Any]) -> Decimal | None:
    """Extract capital deployed percentage from event.

    Args:
        event_detail: The detail payload from event

    Returns:
        Capital deployed percentage as Decimal, or None if not available

    """
    capital_pct = event_detail.get("capital_deployed_pct")
    if capital_pct is not None:
        try:
            return Decimal(str(capital_pct))
        except (TypeError, ValueError):
            pass
    return None


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
    logger.info(
        "Processing WorkflowFailed event",
        extra={"correlation_id": correlation_id, "source": source},
    )

    # Create minimal ApplicationContainer for notifications
    container = ApplicationContainer.create_for_notifications("production")

    # Build error notification event
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


def _handle_data_lake_update(detail: dict[str, Any], correlation_id: str) -> dict[str, Any]:
    """Handle DataLakeUpdateCompleted event.

    Sends detailed notification about data lake refresh with metrics.

    Args:
        detail: The detail payload from DataLakeUpdateCompleted event
        correlation_id: Correlation ID for tracing

    Returns:
        Response with status code and message

    """
    total_symbols = detail.get("total_symbols", 0)
    success_count = detail.get("symbols_updated_count", 0)
    failed_count = detail.get("symbols_failed_count", 0)

    logger.info(
        "Processing DataLakeUpdateCompleted",
        extra={
            "correlation_id": correlation_id,
            "total_symbols": total_symbols,
            "success_count": success_count,
            "failed_count": failed_count,
        },
    )

    container = ApplicationContainer.create_for_notifications("production")
    notification_event = _build_data_lake_notification(detail, correlation_id, container)
    notification_service = NotificationService(container)
    notification_service.handle_event(notification_event)

    return {
        "statusCode": 200,
        "body": f"Data lake notification sent for correlation_id: {correlation_id}",
    }


def _build_data_lake_notification(
    update_detail: dict[str, Any],
    correlation_id: str,
    container: ApplicationContainer,
) -> DataLakeNotificationRequested:
    """Build DataLakeNotificationRequested from DataLakeUpdateCompleted event.

    Args:
        update_detail: The detail payload from DataLakeUpdateCompleted event
        correlation_id: Correlation ID for tracing
        container: Application container for config access

    Returns:
        DataLakeNotificationRequested event ready for processing

    """
    status_code = update_detail.get("status_code", 500)
    if status_code == 200:
        status = "SUCCESS"
    elif status_code == 206:
        status = "SUCCESS_WITH_WARNINGS"
    else:
        status = "FAILURE"

    data_lake_context = {
        "total_symbols": update_detail.get("total_symbols", 0),
        "symbols_updated": update_detail.get("symbols_updated", []),
        "failed_symbols": update_detail.get("failed_symbols", []),
        "symbols_updated_count": update_detail.get("symbols_updated_count", 0),
        "symbols_failed_count": update_detail.get("symbols_failed_count", 0),
        "total_bars_fetched": update_detail.get("total_bars_fetched", 0),
        "data_source": update_detail.get("data_source", "alpaca_api"),
        "start_time_utc": update_detail.get("start_time_utc", ""),
        "end_time_utc": update_detail.get("end_time_utc", ""),
        "duration_seconds": update_detail.get("duration_seconds", 0),
        "error_message": update_detail.get("error_message"),
        "error_details": update_detail.get("error_details", {}),
    }

    return DataLakeNotificationRequested(
        correlation_id=correlation_id,
        causation_id=update_detail.get("event_id", correlation_id),
        event_id=f"data-lake-notification-{uuid4()}",
        timestamp=datetime.now(UTC),
        source_module="notifications_v2.lambda_handler",
        source_component="NotificationsLambda",
        status=status,
        data_lake_context=data_lake_context,
    )
