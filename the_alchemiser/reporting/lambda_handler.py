"""Business Unit: reporting | Status: current.

AWS Lambda handler for PDF report generation.

This Lambda is triggered by Step Functions or direct invocation
and generates PDF reports from account snapshots stored in DynamoDB
or from execution data for trading notifications.

Architecture Note:
    This lambda avoids importing ApplicationContainer to keep dependencies minimal.
    The ApplicationContainer pulls in heavy dependencies (pandas, numpy) via its
    import chain (market data services, strategy wiring) that are not needed for
    PDF report generation. Instead, we create a lightweight EventBus directly.
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
from the_alchemiser.shared.repositories.account_snapshot_repository import (
    AccountSnapshotRepository,
)

from .execution_report_service import ExecutionReportService
from .service import ReportGeneratorService

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


def _extract_correlation_id(event: dict[str, Any]) -> str:
    """Extract or generate correlation ID from event.

    Args:
        event: Lambda event that may contain a correlation_id

    Returns:
        Correlation ID string

    """
    if event.get("correlation_id"):
        return str(event["correlation_id"])
    return generate_request_id()


def _validate_event(event: dict[str, Any]) -> None:
    """Validate Lambda event structure.

    Args:
        event: Lambda event to validate

    Raises:
        ValueError: If required fields are missing

    """
    # Check if this is an execution report generation
    if event.get("generate_from_execution", False):
        required_fields = ["execution_data", "trading_mode"]
        missing_fields = [field for field in required_fields if field not in event]
        if missing_fields:
            raise ValueError(
                f"Missing required fields for execution report: {', '.join(missing_fields)}"
            )
    else:
        # Account snapshot report
        required_fields = ["account_id"]
        missing_fields = [field for field in required_fields if field not in event]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")


def lambda_handler(event: dict[str, Any], context: object | None = None) -> dict[str, Any]:
    """AWS Lambda handler for PDF report generation.

    Expected event structure for account reports:
    {
        "account_id": "account123",        # Required
        "snapshot_id": "2024-...",         # Optional (ISO timestamp)
        "report_type": "account_summary",  # Optional (default: account_summary)
        "correlation_id": "req-123",       # Optional (for tracing)
        "use_latest": true                 # Optional (use latest snapshot if true)
    }

    Expected event structure for execution reports:
    {
        "generate_from_execution": true,   # Required for execution reports
        "report_type": "trading_execution",# Optional (default: trading_execution)
        "execution_data": {...},           # Required - execution data payload
        "trading_mode": "PAPER",           # Required - PAPER or LIVE
        "correlation_id": "req-123"        # Optional (for tracing)
    }

    Args:
        event: Lambda event containing report generation parameters
        context: Lambda context object

    Returns:
        Dictionary with status and report metadata

    Examples:
        Generate report from specific snapshot:
        >>> event = {
        ...     "account_id": "PA123",
        ...     "snapshot_id": "2024-10-25T12:00:00+00:00"
        ... }
        >>> result = lambda_handler(event, None)
        >>> print(result['status'])
        'success'

        Generate report from execution data:
        >>> event = {
        ...     "generate_from_execution": True,
        ...     "execution_data": {...},
        ...     "trading_mode": "PAPER"
        ... }
        >>> result = lambda_handler(event, None)

    """
    # Extract request ID for tracking
    request_id = getattr(context, "aws_request_id", "unknown") if context else "local"

    # Extract correlation ID
    correlation_id = _extract_correlation_id(event)
    set_request_id(correlation_id)

    logger.info(
        "Report generation Lambda invoked",
        aws_request_id=request_id,
        correlation_id=correlation_id,
        lambda_event=event,
    )

    try:
        # Validate event
        _validate_event(event)

        # Check if this is an execution report
        if event.get("generate_from_execution", False):
            return _handle_execution_report(event, request_id, correlation_id)

        # Otherwise, handle as account snapshot report
        # Extract parameters
        account_id = event["account_id"]
        snapshot_id = event.get("snapshot_id")
        report_type = event.get("report_type", "account_summary")
        use_latest = event.get("use_latest", False)

        # Get configuration from environment
        table_name = os.environ.get("TRADE_LEDGER__TABLE_NAME", "alchemiser-trade-ledger-dev")
        s3_bucket = os.environ.get("REPORTS_S3_BUCKET", "the-alchemiser-reports")
        bucket_owner_account_id = os.environ.get("AWS_ACCOUNT_ID")

        logger.info(
            "Initializing report generation",
            account_id=account_id,
            snapshot_id=snapshot_id,
            report_type=report_type,
            use_latest=use_latest,
        )

        # Initialize services with lightweight EventBus (no heavy dependencies)
        event_bus = _create_event_bus()

        snapshot_repository = AccountSnapshotRepository(table_name=table_name)
        report_service = ReportGeneratorService(
            snapshot_repository=snapshot_repository,
            event_bus=event_bus,
            s3_bucket=s3_bucket,
            bucket_owner_account_id=bucket_owner_account_id,
        )

        # Generate report
        if use_latest or snapshot_id is None:
            report_ready_event = report_service.generate_report_from_latest_snapshot(
                account_id=account_id,
                report_type=report_type,
                correlation_id=correlation_id,
            )
        else:
            report_ready_event = report_service.generate_report_from_snapshot_id(
                account_id=account_id,
                snapshot_id=snapshot_id,
                report_type=report_type,
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


def _handle_execution_report(
    event: dict[str, Any], request_id: str, correlation_id: str
) -> dict[str, Any]:
    """Handle execution report generation from trading data.

    Args:
        event: Lambda event containing execution data
        request_id: AWS request ID
        correlation_id: Correlation ID for tracing

    Returns:
        Dictionary with status and report metadata

    Raises:
        ValueError: If execution data is invalid

    """
    execution_data = event["execution_data"]
    trading_mode = event["trading_mode"]
    report_type = event.get("report_type", "trading_execution")

    # Get S3 bucket from environment
    s3_bucket = os.environ.get("REPORTS_S3_BUCKET", "the-alchemiser-reports")
    bucket_owner_account_id = os.environ.get("AWS_ACCOUNT_ID")

    logger.info(
        "Generating execution report",
        trading_mode=trading_mode,
        report_type=report_type,
        correlation_id=correlation_id,
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
        execution_data=execution_data,
        trading_mode=trading_mode,
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

    logger.info("Execution report generation completed successfully", response=response)
    return response


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
