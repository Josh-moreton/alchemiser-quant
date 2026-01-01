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

from data_refresh_service import DataRefreshService
from fetch_request_service import FetchRequestService

from the_alchemiser.shared.events import (
    DataLakeUpdateCompleted,
    MarketDataFetchCompleted,
    WorkflowFailed,
)
from the_alchemiser.shared.events.eventbridge_publisher import (
    publish_to_eventbridge,
)
from the_alchemiser.shared.logging import configure_application_logging, get_logger

# Initialize logging on cold start (must be before get_logger)
configure_application_logging()

logger = get_logger(__name__)


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle data Lambda invocations for market data refresh.

    Handles three types of invocations:
    1. Scheduled refresh (EventBridge Schedule) - refreshes all configured symbols
    2. MarketDataFetchRequested event - on-demand fetch for specific symbol with deduplication
    3. Manual invocation - specific symbols or full seed

    Args:
        event: Lambda event (varies by trigger type)
        context: Lambda context

    Returns:
        Response with refresh statistics

    """
    # Check if this is a MarketDataFetchRequested event
    if _is_fetch_request_event(event):
        return _handle_fetch_request(event)

    # Otherwise, handle as scheduled refresh or manual invocation
    return _handle_scheduled_refresh(event)


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

    # Capture start time for metrics
    start_time = datetime.now(UTC)

    logger.info(
        "Data Lambda invoked - starting data refresh",
        extra={
            "correlation_id": correlation_id,
            "event_source": event.get("source", "schedule"),
            "start_time_utc": start_time.isoformat(),
        },
    )

    try:
        # Create data refresh service
        service = DataRefreshService()

        # Check for specific symbols (manual invocation)
        specific_symbols = event.get("symbols")
        full_seed = event.get("full_seed", False)
        process_markers = event.get("process_markers", True)  # Default: process bad data markers

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
            # Use refresh_all_with_markers to also process bad data markers
            if process_markers:
                results = service.refresh_all_with_markers()
            else:
                results = service.refresh_all_symbols()

        # Calculate statistics
        total = len(results)
        success_count = sum(results.values())
        failed_count = total - success_count
        failed_symbols = [s for s, ok in results.items() if not ok]
        success_symbols = [s for s, ok in results.items() if ok]

        # Calculate duration
        end_time = datetime.now(UTC)
        duration = (end_time - start_time).total_seconds()

        logger.info(
            "Data refresh completed",
            extra={
                "correlation_id": correlation_id,
                "total_symbols": total,
                "success_count": success_count,
                "failed_count": failed_count,
                "failed_symbols": failed_symbols,
                "duration_seconds": duration,
            },
        )

        # Determine status code and success flag
        if failed_count == 0:
            status_code = 200
            overall_success = True
        elif success_count > 0:
            status_code = 206  # Partial success
            overall_success = False
        else:
            status_code = 500  # All failed
            overall_success = False

        # Publish DataLakeUpdateCompleted event for notifications
        try:
            update_event = DataLakeUpdateCompleted(
                correlation_id=correlation_id,
                causation_id=correlation_id,
                event_id=f"data-lake-update-{uuid.uuid4()}",
                timestamp=end_time,
                source_module="data_v2",
                source_component="lambda_handler",
                success=overall_success,
                status_code=status_code,
                total_symbols=total,
                symbols_updated=success_symbols,
                failed_symbols=failed_symbols,
                symbols_updated_count=success_count,
                symbols_failed_count=failed_count,
                total_bars_fetched=0,  # TODO: Track if needed
                data_source="alpaca_api",
                start_time_utc=start_time.isoformat(),
                end_time_utc=end_time.isoformat(),
                duration_seconds=duration,
                error_message=f"Failed symbols: {', '.join(failed_symbols)}"
                if failed_symbols
                else None,
                error_details={"failed_symbols": failed_symbols} if failed_symbols else {},
            )
            publish_to_eventbridge(update_event)

            logger.info(
                "DataLakeUpdateCompleted event published",
                extra={
                    "correlation_id": correlation_id,
                    "event_id": update_event.event_id,
                    "overall_success": overall_success,
                },
            )
        except Exception as pub_error:
            logger.error(
                "Failed to publish DataLakeUpdateCompleted event",
                extra={
                    "correlation_id": correlation_id,
                    "error": str(pub_error),
                },
            )

        # Return response based on status
        response_body: dict[str, Any] = {
            "correlation_id": correlation_id,
            "total_symbols": total,
            "refreshed": success_count,
        }

        if failed_count > 0:
            response_body.update(
                {
                    "failed": failed_count,
                    "failed_symbols": failed_symbols,
                }
            )

        if status_code == 200:
            response_body["status"] = "success"
        elif status_code == 206:
            response_body["status"] = "partial_success"
        else:
            response_body["status"] = "failed"

        return {
            "statusCode": status_code,
            "body": response_body,
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
