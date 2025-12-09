"""Business Unit: data | Status: current.

Lambda handler for data microservice.

This is the entry point for the Data Lambda which supports two actions:
1. "refresh" (default): Fetch new market data from Alpaca and store in S3 Parquet
   - Triggered by EventBridge Schedule (daily at 10 PM UTC, Mon-Fri)
   - Triggered manually for testing or initial seeding

2. "get_bars": Read historical bars from S3 cache
   - Invoked synchronously by Indicators Lambda
   - Returns list of BarModel data for indicator computation

This design allows the Data Lambda to be the ONLY Lambda with pyarrow dependency,
keeping the Indicators Lambda lightweight.
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

from .cached_market_data_adapter import CachedMarketDataAdapter
from .data_refresh_service import DataRefreshService

# Initialize logging on cold start (must be before get_logger)
configure_application_logging()

logger = get_logger(__name__)

# Singleton adapter for warm starts (get_bars action)
_market_data_adapter: CachedMarketDataAdapter | None = None


def _get_market_data_adapter() -> CachedMarketDataAdapter:
    """Get or create singleton market data adapter."""
    global _market_data_adapter
    if _market_data_adapter is None:
        _market_data_adapter = CachedMarketDataAdapter()
    return _market_data_adapter


def _handle_get_bars(event: dict[str, Any]) -> dict[str, Any]:
    """Handle get_bars action for fetching historical data.

    Args:
        event: Request with symbol, period, timeframe

    Returns:
        Response with bars list or error

    """
    symbol = event.get("symbol")
    period = event.get("period", "1Y")
    timeframe = event.get("timeframe", "1Day")
    correlation_id = event.get("correlation_id", "unknown")

    if not symbol:
        return {
            "statusCode": 400,
            "body": {
                "error": "ValidationError",
                "message": "symbol is required",
                "correlation_id": correlation_id,
            },
        }

    logger.info(
        "get_bars request",
        symbol=symbol,
        period=period,
        timeframe=timeframe,
        correlation_id=correlation_id,
    )

    try:
        from the_alchemiser.shared.value_objects.symbol import Symbol

        adapter = _get_market_data_adapter()
        symbol_obj = Symbol(symbol)
        bars = adapter.get_bars(symbol=symbol_obj, period=period, timeframe=timeframe)

        # Serialize bars to dicts
        bars_data = [
            {
                "symbol": bar.symbol,
                "timestamp": bar.timestamp.isoformat(),
                "open": str(bar.open),
                "high": str(bar.high),
                "low": str(bar.low),
                "close": str(bar.close),
                "volume": bar.volume,
            }
            for bar in bars
        ]

        logger.info(
            "get_bars completed",
            symbol=symbol,
            bars_count=len(bars_data),
            correlation_id=correlation_id,
        )

        return {
            "statusCode": 200,
            "body": {
                "bars": bars_data,
                "symbol": symbol,
                "period": period,
                "timeframe": timeframe,
                "correlation_id": correlation_id,
            },
        }

    except Exception as e:
        logger.error(
            "get_bars failed",
            symbol=symbol,
            error=str(e),
            error_type=type(e).__name__,
            correlation_id=correlation_id,
        )
        return {
            "statusCode": 500,
            "body": {
                "error": type(e).__name__,
                "message": str(e),
                "correlation_id": correlation_id,
            },
        }


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle data Lambda invocations.

    Supports two actions:
    1. "get_bars": Read historical bars from S3 cache (sync, for Indicators Lambda)
    2. "refresh" (default): Fetch new data from Alpaca and store to S3

    Args:
        event: Lambda event
            - action: "get_bars" or "refresh" (default: "refresh")
            - For get_bars: symbol, period, timeframe, correlation_id
            - For refresh: correlation_id, symbols, full_seed

        context: Lambda context

    Returns:
        Response with bars data or refresh statistics

    """
    # Route based on action
    action = event.get("action", "refresh")

    if action == "get_bars":
        return _handle_get_bars(event)

    # Default: data refresh workflow
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
