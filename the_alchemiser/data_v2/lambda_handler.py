"""Business Unit: data | Status: current.

Lambda handler for data microservice.

This is the entry point for the Data Lambda which fetches new market data from
Alpaca and stores it in S3 Parquet format.

Triggered by:
- EventBridge Schedule (daily at 4:00 AM UTC, Tue-Sat to catch Mon-Fri data)
- MarketDataFetchRequested events (on-demand from strategy lambdas)
- Manual invocation for testing or initial seeding
"""

from __future__ import annotations

import contextlib
import os
import uuid
from datetime import UTC, datetime
from typing import Any

from the_alchemiser.shared.events import (
    DataValidationCompleted,
    MarketDataFetchCompleted,
    WorkflowFailed,
)
from the_alchemiser.shared.events.eventbridge_publisher import (
    publish_to_eventbridge,
)
from the_alchemiser.shared.logging import configure_application_logging, get_logger

from .data_quality_validator import DataQualityValidator
from .data_refresh_service import DataRefreshService
from .fetch_request_service import FetchRequestService
from .market_data_store import MarketDataStore

# Initialize logging on cold start (must be before get_logger)
configure_application_logging()

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle data Lambda invocations for market data refresh and validation.

    Handles four types of invocations:
    1. Scheduled refresh (EventBridge Schedule) - refreshes all configured symbols
    2. Scheduled validation (EventBridge Schedule) - validates data quality against yfinance
    3. MarketDataFetchRequested event - on-demand fetch for specific symbol with deduplication
    4. Manual invocation - specific symbols or full seed

    Args:
        event: Lambda event (varies by trigger type)
        context: Lambda context

    Returns:
        Response with refresh/validation statistics

    """
    # Check if this is a data validation event
    if _is_validation_event(event):
        return _handle_data_validation(event)

    # Check if this is a MarketDataFetchRequested event
    if _is_fetch_request_event(event):
        return _handle_fetch_request(event)

    # Otherwise, handle as scheduled refresh or manual invocation
    return _handle_scheduled_refresh(event)


def _is_validation_event(event: dict[str, Any]) -> bool:
    """Check if event is a scheduled data validation event."""
    # Check for explicit validation trigger
    if event.get("validation_trigger") is True:
        return True

    # Check EventBridge rule ID for validation schedule
    resources = event.get("resources", [])
    for resource in resources:
        if "DataValidationSchedule" in resource:
            return True

    return False


def _is_fetch_request_event(event: dict[str, Any]) -> bool:
    """Check if event is a MarketDataFetchRequested EventBridge event."""
    detail_type = event.get("detail-type")
    source = event.get("source", "")

    return detail_type == "MarketDataFetchRequested" and source.startswith("alchemiser.")


def _handle_fetch_request(event: dict[str, Any]) -> dict[str, Any]:
    """Handle MarketDataFetchRequested event with deduplication.

    Uses DynamoDB conditional writes to ensure only one fetch proceeds
    when multiple stages detect missing data simultaneously.

    Args:
        event: EventBridge event with MarketDataFetchRequested detail

    Returns:
        Response indicating whether fetch was performed or deduplicated

    """
    detail = event.get("detail", {})
    correlation_id = detail.get("correlation_id") or f"fetch-request-{uuid.uuid4()}"
    symbol = detail.get("symbol", "")
    requesting_stage = detail.get("requesting_stage", "unknown")
    requesting_component = detail.get("requesting_component", "unknown")
    lookback_days = detail.get("lookback_days", 400)

    logger.info(
        "MarketDataFetchRequested event received",
        extra={
            "correlation_id": correlation_id,
            "symbol": symbol,
            "requesting_stage": requesting_stage,
            "requesting_component": requesting_component,
        },
    )

    if not symbol:
        logger.error(
            "MarketDataFetchRequested missing symbol",
            extra={"correlation_id": correlation_id},
        )
        return {
            "statusCode": 400,
            "body": {"status": "error", "error": "Missing symbol in request"},
        }

    # Check if FETCH_REQUESTS_TABLE is configured (shared data infrastructure)
    fetch_table = os.environ.get("FETCH_REQUESTS_TABLE")

    if fetch_table:
        # Use deduplication service
        fetch_service = FetchRequestService()
        result = fetch_service.try_acquire_fetch_lock(
            symbol=symbol,
            requesting_stage=requesting_stage,
            requesting_component=requesting_component,
            correlation_id=correlation_id,
        )

        if not result.can_proceed:
            # Another recent request exists - skip this fetch
            logger.info(
                "Fetch request deduplicated",
                extra={
                    "correlation_id": correlation_id,
                    "symbol": symbol,
                    "existing_request_time": result.existing_request_time,
                    "cooldown_remaining_seconds": result.cooldown_remaining_seconds,
                },
            )

            # Publish completion event indicating deduplication
            _publish_fetch_completed(
                symbol=symbol,
                success=True,
                bars_fetched=0,
                was_deduplicated=True,
                correlation_id=correlation_id,
            )

            return {
                "statusCode": 200,
                "body": {
                    "status": "deduplicated",
                    "symbol": symbol,
                    "existing_request_time": result.existing_request_time,
                    "cooldown_remaining_seconds": result.cooldown_remaining_seconds,
                },
            }

    # Proceed with fetch
    try:
        service = DataRefreshService()

        # Check if symbol has any data - if not, seed initial data
        metadata = service.market_data_store.get_metadata(symbol)

        if metadata is None:
            # New symbol - seed initial data
            logger.info(
                "Seeding initial data for new symbol",
                extra={
                    "correlation_id": correlation_id,
                    "symbol": symbol,
                    "lookback_days": lookback_days,
                },
            )
            results = service.seed_initial_data([symbol], lookback_days=lookback_days)
            success = results.get(symbol, False)
            bars_fetched = lookback_days if success else 0  # Approximate
        else:
            # Existing symbol - refresh with latest bars
            success = service.refresh_symbol(symbol)
            bars_fetched = 1 if success else 0  # Approximate - could be more

        # Publish completion event
        _publish_fetch_completed(
            symbol=symbol,
            success=success,
            bars_fetched=bars_fetched,
            was_deduplicated=False,
            correlation_id=correlation_id,
            error_message=None if success else "Fetch failed",
        )

        if success:
            logger.info(
                "Fetch request completed successfully",
                extra={"correlation_id": correlation_id, "symbol": symbol},
            )
            return {
                "statusCode": 200,
                "body": {"status": "success", "symbol": symbol, "bars_fetched": bars_fetched},
            }
        # Release lock on failure so retries can proceed
        if fetch_table:
            fetch_service.release_fetch_lock(symbol, correlation_id)

        logger.error(
            "Fetch request failed",
            extra={"correlation_id": correlation_id, "symbol": symbol},
        )
        return {
            "statusCode": 500,
            "body": {"status": "failed", "symbol": symbol},
        }

    except Exception as e:
        # Release lock on exception so retries can proceed
        if fetch_table:
            with contextlib.suppress(Exception):
                fetch_service.release_fetch_lock(symbol, correlation_id)

        logger.error(
            "Fetch request exception",
            extra={"correlation_id": correlation_id, "symbol": symbol, "error": str(e)},
            exc_info=True,
        )

        _publish_fetch_completed(
            symbol=symbol,
            success=False,
            bars_fetched=0,
            was_deduplicated=False,
            correlation_id=correlation_id,
            error_message=str(e),
        )

        return {
            "statusCode": 500,
            "body": {"status": "error", "symbol": symbol, "error": str(e)},
        }


def _publish_fetch_completed(
    symbol: str,
    *,
    success: bool,
    bars_fetched: int,
    was_deduplicated: bool,
    correlation_id: str,
    error_message: str | None = None,
) -> None:
    """Publish MarketDataFetchCompleted event to EventBridge."""
    try:
        event = MarketDataFetchCompleted(
            correlation_id=correlation_id,
            causation_id=correlation_id,
            event_id=f"fetch-completed-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="data_v2",
            source_component="lambda_handler",
            symbol=symbol,
            success=success,
            bars_fetched=bars_fetched,
            was_deduplicated=was_deduplicated,
            error_message=error_message,
        )
        publish_to_eventbridge(event)
    except Exception as e:
        logger.warning(
            "Failed to publish MarketDataFetchCompleted event",
            extra={"error": str(e), "symbol": symbol},
        )


def _handle_scheduled_refresh(event: dict[str, Any]) -> dict[str, Any]:
    """Handle scheduled refresh or manual invocation.

    Args:
        event: Lambda event (schedule trigger or manual)

    Returns:
        Response with refresh statistics

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


def _handle_data_validation(event: dict[str, Any]) -> dict[str, Any]:
    """Handle scheduled data validation run.

    Validates market data from S3 against external source (yfinance).
    Generates and uploads data quality report to S3.

    Args:
        event: Lambda event (schedule trigger or manual)

    Returns:
        Response with validation statistics

    """
    # Generate correlation ID for this workflow
    correlation_id = event.get("correlation_id") or f"data-validation-{uuid.uuid4()}"

    logger.info(
        "Data validation invoked",
        extra={
            "correlation_id": correlation_id,
            "event_source": event.get("source", "schedule"),
        },
    )

    try:
        # Initialize market data store and validator
        market_data_store = MarketDataStore()
        validator = DataQualityValidator(market_data_store=market_data_store)

        # Get symbols to validate (manual override or all symbols)
        symbols = event.get("symbols")
        lookback_days = event.get("lookback_days", 5)

        # Run validation
        logger.info(
            "Starting data quality validation",
            extra={
                "correlation_id": correlation_id,
                "symbols": symbols or "all",
                "lookback_days": lookback_days,
            },
        )

        validation_result = validator.validate_all_symbols(
            symbols=symbols, lookback_days=lookback_days
        )

        # Generate and upload report
        report_path = validator.generate_report_csv(validation_result)
        s3_key = validator.upload_report_to_s3(
            report_path=report_path,
            validation_date=validation_result.validation_date,
        )

        # Clean up temp file
        report_path.unlink()

        logger.info(
            "Data validation completed",
            extra={
                "correlation_id": correlation_id,
                "symbols_checked": validation_result.symbols_checked,
                "symbols_passed": validation_result.symbols_passed,
                "symbols_failed": validation_result.symbols_failed,
                "discrepancies_found": len(validation_result.discrepancies),
                "report_s3_key": s3_key,
            },
        )

        # Publish DataValidationCompleted event
        try:
            validation_event = DataValidationCompleted(
                correlation_id=correlation_id,
                causation_id=correlation_id,
                event_id=f"data-validation-completed-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="data_v2",
                source_component="lambda_handler",
                validation_date=validation_result.validation_date,
                symbols_checked=validation_result.symbols_checked,
                symbols_passed=validation_result.symbols_passed,
                symbols_failed=validation_result.symbols_failed,
                discrepancies_found=len(validation_result.discrepancies),
                report_s3_key=s3_key,
            )
            publish_to_eventbridge(validation_event)
        except Exception as pub_error:
            logger.warning(
                "Failed to publish DataValidationCompleted event",
                extra={"error": str(pub_error)},
            )

        return {
            "statusCode": 200,
            "body": {
                "status": "success",
                "correlation_id": correlation_id,
                "validation_date": validation_result.validation_date,
                "symbols_checked": validation_result.symbols_checked,
                "symbols_passed": validation_result.symbols_passed,
                "symbols_failed": validation_result.symbols_failed,
                "discrepancies_found": len(validation_result.discrepancies),
                "report_s3_key": s3_key,
            },
        }

    except Exception as e:
        logger.error(
            "Data validation failed with exception",
            extra={"correlation_id": correlation_id, "error": str(e)},
            exc_info=True,
        )

        # Publish WorkflowFailed to EventBridge
        try:
            failure_event = WorkflowFailed(
                correlation_id=correlation_id,
                causation_id=correlation_id,
                event_id=f"data-validation-failed-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="data_v2",
                source_component="lambda_handler",
                workflow_type="data_validation",
                failure_reason=str(e),
                failure_step="data_validation",
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
