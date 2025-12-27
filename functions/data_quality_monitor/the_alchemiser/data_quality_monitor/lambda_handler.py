"""Business Unit: data_quality_monitor | Status: current.

Lambda handler for data quality monitoring microservice.

This is the entry point for the Data Quality Monitor Lambda which validates
market data stored in S3 against external sources.

Triggered by:
- EventBridge Schedule (daily at 4:30 AM UTC, after data refresh completes)
- Manual invocation for testing or ad-hoc validation
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from the_alchemiser.shared.events import WorkflowFailed
from the_alchemiser.shared.events.eventbridge_publisher import (
    publish_to_eventbridge,
)
from the_alchemiser.shared.logging import configure_application_logging, get_logger

from .quality_checker import DataQualityChecker, DataQualityError

# Initialize logging on cold start (must be before get_logger)
configure_application_logging()

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle data quality monitoring Lambda invocations.

    Validates market data in S3 parquet datalake by comparing against
    external data sources (Yahoo Finance) to detect:
    - Missing data gaps
    - Timestamp misalignment
    - Price discrepancies
    - Data freshness issues

    Args:
        event: Lambda event (schedule trigger or manual)
        context: Lambda context

    Returns:
        Response with validation statistics

    """
    correlation_id = event.get("correlation_id") or f"quality-check-{uuid.uuid4()}"

    logger.info(
        "Data Quality Monitor invoked",
        extra={
            "correlation_id": correlation_id,
            "event_source": event.get("source", "schedule"),
        },
    )

    try:
        # Parse event parameters
        validation_params = _determine_validation_params(event, correlation_id)

        # Execute validation
        results = _run_validation(validation_params, correlation_id)

        # Calculate statistics
        stats = _calculate_statistics(results)

        # Build and return response
        return _build_response(stats, correlation_id)

    except (DataQualityError, Exception) as e:
        return _handle_validation_failure(e, correlation_id)


def _determine_validation_params(
    event: dict[str, Any],
    correlation_id: str,
) -> dict[str, Any]:
    """Parse and validate event parameters.

    Args:
        event: Lambda event
        correlation_id: Correlation ID for tracking

    Returns:
        Dictionary with validation parameters

    """
    specific_symbols = event.get("symbols")
    lookback_days = event.get("lookback_days", 5)

    logger.info(
        "Validation parameters determined",
        extra={
            "correlation_id": correlation_id,
            "specific_symbols": bool(specific_symbols),
            "lookback_days": lookback_days,
        },
    )

    return {
        "specific_symbols": specific_symbols,
        "lookback_days": lookback_days,
    }


def _run_validation(
    params: dict[str, Any],
    correlation_id: str,
) -> dict[str, Any]:
    """Execute data quality validation.

    Args:
        params: Validation parameters
        correlation_id: Correlation ID for tracking

    Returns:
        Validation results

    Raises:
        DataQualityError: If validation fails

    """
    checker = DataQualityChecker()

    if params["specific_symbols"]:
        logger.info(
            "Validating specific symbols",
            extra={
                "correlation_id": correlation_id,
                "symbols": params["specific_symbols"],
                "lookback_days": params["lookback_days"],
            },
        )
        return checker.validate_symbols(
            symbols=params["specific_symbols"],
            lookback_days=params["lookback_days"],
        )

    logger.info(
        "Validating all symbols",
        extra={
            "correlation_id": correlation_id,
            "lookback_days": params["lookback_days"],
        },
    )
    return checker.validate_all_symbols(lookback_days=params["lookback_days"])


def _calculate_statistics(results: dict[str, Any]) -> dict[str, Any]:
    """Calculate validation statistics from results.

    Args:
        results: Validation results

    Returns:
        Statistics dictionary

    """
    total = len(results)
    passed_count = sum(1 for r in results.values() if r.passed)
    failed_count = total - passed_count
    failed_symbols = [s for s, r in results.items() if not r.passed]

    # Aggregate issues
    all_issues = []
    for symbol, result in results.items():
        for issue in result.issues:
            all_issues.append({"symbol": symbol, "issue": issue})

    return {
        "total": total,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "failed_symbols": failed_symbols,
        "all_issues": all_issues,
    }


def _build_response(
    stats: dict[str, Any],
    correlation_id: str,
) -> dict[str, Any]:
    """Build success response from statistics.

    Args:
        stats: Validation statistics
        correlation_id: Correlation ID for tracking

    Returns:
        Lambda response dictionary

    """
    logger.info(
        "Data quality validation completed",
        extra={
            "correlation_id": correlation_id,
            "total_symbols": stats["total"],
            "passed_count": stats["passed_count"],
            "failed_count": stats["failed_count"],
            "failed_symbols": stats["failed_symbols"],
            "total_issues": len(stats["all_issues"]),
        },
    )

    if stats["failed_count"] > 0:
        logger.warning(
            "Data quality issues detected",
            extra={
                "correlation_id": correlation_id,
                "failed_symbols": stats["failed_symbols"],
                "issues": stats["all_issues"][:10],
            },
        )

    if stats["failed_count"] == 0:
        return {
            "statusCode": 200,
            "body": {
                "status": "success",
                "correlation_id": correlation_id,
                "total_symbols": stats["total"],
                "passed": stats["passed_count"],
                "issues_found": 0,
            },
        }

    return {
        "statusCode": 200,
        "body": {
            "status": "issues_detected",
            "correlation_id": correlation_id,
            "total_symbols": stats["total"],
            "passed": stats["passed_count"],
            "failed": stats["failed_count"],
            "failed_symbols": stats["failed_symbols"],
            "issues": stats["all_issues"],
        },
    }


def _handle_validation_failure(
    error: Exception,
    correlation_id: str,
) -> dict[str, Any]:
    """Handle validation failure and publish event.

    Args:
        error: Exception that occurred
        correlation_id: Correlation ID for tracking

    Returns:
        Error response dictionary

    """
    logger.error(
        "Data Quality Monitor failed with exception",
        extra={"correlation_id": correlation_id, "error": str(error)},
        exc_info=True,
    )

    # Publish WorkflowFailed to EventBridge
    try:
        failure_event = WorkflowFailed(
            correlation_id=correlation_id,
            causation_id=correlation_id,
            event_id=f"quality-check-failed-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="data_quality_monitor",
            source_component="lambda_handler",
            workflow_type="data_quality_check",
            failure_reason=str(error),
            failure_step="quality_validation",
            error_details={"exception_type": type(error).__name__},
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
            "error": str(error),
        },
    }
