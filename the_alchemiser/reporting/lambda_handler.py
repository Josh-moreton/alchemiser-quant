"""Business Unit: reporting | Status: current.

AWS Lambda handler for PDF report generation.

This Lambda is triggered by TradingNotificationRequested events from the main
trading system and generates PDF reports from execution data. It operates in
isolation with minimal dependencies - no database queries, no business logic imports.

The report data is pre-computed by the main trading lambda as ExecutionReportData
and passed via event metadata. The report generator lambda only renders PDF and
uploads to S3.

Architecture Note:
    This lambda is strictly decoupled from the main codebase. It imports only:
    - shared.logging (stdlib-based)
    - shared.events (event schemas, lightweight)
    - shared.schemas.execution_report_data (frozen Pydantic model)
    - reporting.execution_report_service (local rendering logic)

    No database connections, no snapshots, no domain imports.
"""

from __future__ import annotations

import os
from typing import Any

from the_alchemiser.shared.errors.error_handler import (
    handle_trading_error,
    send_error_notification_if_needed,
)
from the_alchemiser.shared.errors.exceptions import NotificationError
from the_alchemiser.shared.events.bus import EventBus
from the_alchemiser.shared.logging import generate_request_id, get_logger, set_request_id
from the_alchemiser.shared.schemas.execution_report_data import ExecutionReportData

from .execution_report_service import ExecutionReportService

logger = get_logger(__name__)


def _create_event_bus() -> EventBus:
    """Create a lightweight EventBus instance for report generation.

    This function creates a standalone EventBus without going through
    ApplicationContainer, avoiding heavy dependencies like pandas/numpy
    that are not needed for PDF report generation.

    Returns:
        EventBus instance for publishing ReportReady events

    """
    return EventBus()


__all__ = ["_create_event_bus", "lambda_handler"]


def _validate_event(event: dict[str, Any]) -> None:
    """Validate Lambda event structure.

    Args:
        event: Lambda event to validate

    Raises:
        ValueError: If required fields are missing

    """
    # Execution reports require ExecutionReportData in metadata
    required_fields = ["metadata"]
    missing_fields = [field for field in required_fields if field not in event]
    if missing_fields:
        raise ValueError(
            f"Missing required fields for execution report event: {', '.join(missing_fields)}"
        )

    # Validate report data is present in metadata
    metadata = event.get("metadata", {})
    if "report_data" not in metadata:
        raise ValueError("Missing 'report_data' in event metadata")


def lambda_handler(event: dict[str, Any], context: object | None = None) -> dict[str, Any]:
    """AWS Lambda handler for PDF execution report generation.

    Decoupled handler that consumes TradingNotificationRequested events with embedded
    ExecutionReportData and generates PDF reports without database queries or business
    logic imports.

    Expected event structure:
    {
        "metadata": {
            "report_data": {
                "schema_version": "1.0",
                "correlation_id": "req-123",
                "timestamp": "2024-11-29T12:00:00+00:00",
                "trading_mode": "PAPER",
                "trading_success": true,
                "orders_placed": 5,
                "orders_succeeded": 5,
                "total_trade_value": "10000.00",
                "strategy_signals": {...},
                "portfolio_allocations": {...},
                "orders_executed": [...],
                "execution_summary": {...},
                ...
            }
        },
        // other event fields
    }

    Args:
        event: Lambda event containing ExecutionReportData in metadata
        context: Lambda context object

    Returns:
        Dictionary with status, report metadata, and S3 URI

    Examples:
        Generate report from execution event:
        >>> event = {
        ...     "metadata": {
        ...         "report_data": {...}
        ...     }
        ... }
        >>> result = lambda_handler(event, None)
        >>> print(result['status'])
        'success'

    """
    # Extract request ID for tracking
    request_id = getattr(context, "aws_request_id", "unknown") if context else "local"

    # Extract correlation ID from report data
    metadata = event.get("metadata", {})
    report_data_dict = metadata.get("report_data", {})
    correlation_id = report_data_dict.get("correlation_id", generate_request_id())
    set_request_id(correlation_id)

    logger.info(
        "Report generation Lambda invoked (execution report from event)",
        aws_request_id=request_id,
        correlation_id=correlation_id,
        lambda_event_keys=list(event.keys()),
    )

    try:
        # Validate event
        _validate_event(event)

        # Parse ExecutionReportData from metadata
        report_data = ExecutionReportData.model_validate(report_data_dict)

        # Get S3 configuration from environment
        s3_bucket = os.environ.get("REPORTS_S3_BUCKET", "the-alchemiser-reports")
        bucket_owner_account_id = os.environ.get("AWS_ACCOUNT_ID")

        logger.info(
            "Generating execution report from event",
            correlation_id=correlation_id,
            trading_mode=report_data.trading_mode,
            trading_success=report_data.trading_success,
        )

        # Initialize services with lightweight EventBus (no heavy dependencies)
        event_bus = _create_event_bus()

        execution_report_service = ExecutionReportService(
            event_bus=event_bus,
            s3_bucket=s3_bucket,
            bucket_owner_account_id=bucket_owner_account_id,
        )

        # Generate execution report
        report_ready_event = execution_report_service.generate_execution_report(
            execution_data=report_data.model_dump(),
            trading_mode=report_data.trading_mode,
            correlation_id=correlation_id,
        )

        # Build success response
        response = {
            "status": "success",
            "report_id": report_ready_event.report_id,
            "s3_uri": report_ready_event.s3_uri,
            "s3_bucket": report_ready_event.s3_bucket,
            "s3_key": report_ready_event.s3_key,
            "file_size_bytes": report_ready_event.file_size_bytes,
            "generation_time_ms": report_ready_event.generation_time_ms,
            "snapshot_id": report_ready_event.snapshot_id,
            "correlation_id": correlation_id,
            "request_id": request_id,
        }

        logger.info("Report generation completed successfully", response=response)
        return response

    except ValueError as e:
        # Validation or data errors
        error_message = f"Report generation validation error: {e!s}"
        logger.error("Validation error", error=error_message, exc_info=True)

        _handle_error(e, event, request_id, correlation_id)

        return {
            "status": "failed",
            "error": "ValidationError",
            "message": str(e),
            "correlation_id": correlation_id,
            "request_id": request_id,
        }

    except (ImportError, AttributeError, KeyError, TypeError, OSError) as e:
        # System/critical errors
        error_message = f"Report generation critical error: {e!s}"
        logger.error("Critical error", error=error_message, exc_info=True)

        _handle_error(e, event, request_id, correlation_id, is_critical=True)

        return {
            "status": "failed",
            "error": "SystemError",
            "message": str(e),
            "correlation_id": correlation_id,
            "request_id": request_id,
        }


def _handle_error(
    error: Exception,
    event: dict[str, Any],
    request_id: str,
    correlation_id: str,
    *,
    is_critical: bool = False,
) -> None:
    """Handle errors with detailed reporting and notification.

    Args:
        error: The exception that occurred
        event: Original Lambda event
        request_id: Request ID
        correlation_id: Correlation ID
        is_critical: Whether this is a critical system error

    """
    try:
        context = "report generation lambda execution"
        additional_data = {
            "event": event,
            "request_id": request_id,
            "correlation_id": correlation_id,
        }

        if is_critical:
            additional_data["original_error"] = type(error).__name__

        handle_trading_error(
            error=error,
            context=context,
            component="reporting.lambda_handler",
            additional_data=additional_data,
        )

        # Send error notification using lightweight EventBus
        try:
            event_bus = _create_event_bus()
            send_error_notification_if_needed(event_bus)
        except Exception as setup_error:
            logger.warning(
                "Failed to setup event bus for error notification", error=str(setup_error)
            )

    except NotificationError as notification_error:
        logger.warning("Failed to send error notification: %s", notification_error)
    except (ImportError, AttributeError, ValueError, KeyError, TypeError) as notification_error:
        if is_critical:
            logger.warning("Failed to send error notification: %s", notification_error)
        else:
            # Re-raise for non-critical errors if notification system itself fails
            raise
