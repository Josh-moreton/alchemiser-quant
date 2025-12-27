"""Business Unit: data_quality_monitor | Status: current.

Lambda handler for data quality monitoring microservice.

This is the entry point for the Data Quality Monitor Lambda which validates
market data stored in S3 against external sources.

Triggered by:
- EventBridge Schedule (daily at 4:30 AM UTC, after data refresh completes)
- Manual invocation for testing or ad-hoc validation
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime
from typing import Any

from the_alchemiser.shared.events import WorkflowFailed
from the_alchemiser.shared.events.eventbridge_publisher import (
    publish_to_eventbridge,
)
from the_alchemiser.shared.logging import configure_application_logging, get_logger

from .quality_checker import DataQualityChecker

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
    # Generate correlation ID for this workflow
    correlation_id = event.get("correlation_id") or f"quality-check-{uuid.uuid4()}"

    logger.info(
        "Data Quality Monitor invoked",
        extra={
            "correlation_id": correlation_id,
            "event_source": event.get("source", "schedule"),
        },
    )

    try:
        # Create quality checker
        checker = DataQualityChecker()

        # Check for specific symbols (manual invocation)
        specific_symbols = event.get("symbols")
        lookback_days = event.get("lookback_days", 5)  # Default: check last 5 days

        if specific_symbols:
            # Validate only specified symbols
            logger.info(
                "Validating specific symbols",
                extra={
                    "correlation_id": correlation_id,
                    "symbols": specific_symbols,
                    "lookback_days": lookback_days,
                },
            )
            results = checker.validate_symbols(
                symbols=specific_symbols,
                lookback_days=lookback_days,
            )
        else:
            # Validate all symbols from strategy configs
            logger.info(
                "Validating all symbols",
                extra={
                    "correlation_id": correlation_id,
                    "lookback_days": lookback_days,
                },
            )
            results = checker.validate_all_symbols(lookback_days=lookback_days)

        # Calculate statistics
        total = len(results)
        passed_count = sum(1 for r in results.values() if r.passed)
        failed_count = total - passed_count
        failed_symbols = [s for s, r in results.items() if not r.passed]

        # Aggregate issues
        all_issues = []
        for symbol, result in results.items():
            for issue in result.issues:
                all_issues.append({"symbol": symbol, "issue": issue})

        logger.info(
            "Data quality validation completed",
            extra={
                "correlation_id": correlation_id,
                "total_symbols": total,
                "passed_count": passed_count,
                "failed_count": failed_count,
                "failed_symbols": failed_symbols,
                "total_issues": len(all_issues),
            },
        )

        # Log warnings for any failures
        if failed_count > 0:
            logger.warning(
                "Data quality issues detected",
                extra={
                    "correlation_id": correlation_id,
                    "failed_symbols": failed_symbols,
                    "issues": all_issues[:10],  # First 10 issues
                },
            )

        # Return success even if some symbols failed
        # (individual failures are logged and can be investigated)
        if failed_count == 0:
            return {
                "statusCode": 200,
                "body": {
                    "status": "success",
                    "correlation_id": correlation_id,
                    "total_symbols": total,
                    "passed": passed_count,
                    "issues_found": 0,
                },
            }
        return {
            "statusCode": 200,  # Quality check succeeded even if data has issues
            "body": {
                "status": "issues_detected",
                "correlation_id": correlation_id,
                "total_symbols": total,
                "passed": passed_count,
                "failed": failed_count,
                "failed_symbols": failed_symbols,
                "issues": all_issues,
            },
        }

    except Exception as e:
        logger.error(
            "Data Quality Monitor failed with exception",
            extra={"correlation_id": correlation_id, "error": str(e)},
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
                failure_reason=str(e),
                failure_step="quality_validation",
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
