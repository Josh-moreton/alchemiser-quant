"""Business Unit: data | Status: current.

Lambda handler for data refresh microservice.

This is the entry point for the nightly data refresh workflow. It is triggered by:
1. EventBridge Schedule (daily at 10 PM UTC, Mon-Fri)
2. Manual invocation for testing or initial seeding

Fetches new market data from Alpaca and stores in S3 Parquet format.
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

from .data_refresh_service import DataRefreshService

# Initialize logging on cold start (must be before get_logger)
configure_application_logging()

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle scheduled or manual invocation for data refresh.

    This handler:
    1. Identifies all symbols from strategy configurations
    2. Fetches incremental data from Alpaca for each symbol
    3. Stores updated data in S3 as Parquet files

    Args:
        event: Lambda event (from schedule or manual invocation)
            - correlation_id: Optional correlation ID for tracing
            - symbols: Optional list of specific symbols to refresh (for testing)
            - full_seed: Optional boolean to force full data seeding

        context: Lambda context

    Returns:
        Response indicating success/failure with refresh statistics

    """
    # Generate correlation ID for this workflow
    correlation_id = event.get("correlation_id") or f"data-refresh-{uuid.uuid4()}"

    logger.info(
        "Data Lambda invoked - starting data refresh",
        extra={
            "correlation_id": correlation_id,
            "event_source": event.get("source", "schedule"),
        },
    )

    try:
        # Create data refresh service
        service = DataRefreshService()

        # Check for specific symbols (manual invocation)
        specific_symbols = event.get("symbols")
        full_seed = event.get("full_seed", False)

        if specific_symbols:
            # Refresh only specified symbols
            logger.info(
                "Refreshing specific symbols",
                extra={
                    "correlation_id": correlation_id,
                    "symbols": specific_symbols,
                },
            )

            if full_seed:
                results = service.seed_initial_data(specific_symbols)
            else:
                results = {}
                for symbol in specific_symbols:
                    results[symbol] = service.refresh_symbol(symbol)
        else:
            # Refresh all symbols from strategy configs
            results = service.refresh_all_symbols()

        # Calculate statistics
        total = len(results)
        success_count = sum(results.values())
        failed_count = total - success_count
        failed_symbols = [s for s, ok in results.items() if not ok]

        logger.info(
            "Data refresh completed",
            extra={
                "correlation_id": correlation_id,
                "total_symbols": total,
                "success_count": success_count,
                "failed_count": failed_count,
                "failed_symbols": failed_symbols,
            },
        )

        # Return success even if some symbols failed
        # (individual failures are logged and can be retried)
        if failed_count == 0:
            return {
                "statusCode": 200,
                "body": {
                    "status": "success",
                    "correlation_id": correlation_id,
                    "total_symbols": total,
                    "refreshed": success_count,
                },
            }
        if success_count > 0:
            return {
                "statusCode": 206,  # Partial Content
                "body": {
                    "status": "partial_success",
                    "correlation_id": correlation_id,
                    "total_symbols": total,
                    "refreshed": success_count,
                    "failed": failed_count,
                    "failed_symbols": failed_symbols,
                },
            }
        # All symbols failed
        return {
            "statusCode": 500,
            "body": {
                "status": "failed",
                "correlation_id": correlation_id,
                "total_symbols": total,
                "failed": failed_count,
                "failed_symbols": failed_symbols,
            },
        }

    except Exception as e:
        logger.error(
            "Data Lambda failed with exception",
            extra={"correlation_id": correlation_id, "error": str(e)},
            exc_info=True,
        )

        # Publish WorkflowFailed to EventBridge
        try:
            failure_event = WorkflowFailed(
                correlation_id=correlation_id,
                causation_id=correlation_id,
                event_id=f"data-refresh-failed-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="data_v2",
                source_component="lambda_handler",
                workflow_type="data_refresh",
                failure_reason=str(e),
                failure_step="data_refresh",
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
