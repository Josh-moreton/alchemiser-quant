"""Business Unit: data | Status: current.

Handler for MarketDataFetchRequested events with deduplication.

Uses DynamoDB conditional writes to ensure only one fetch proceeds
when multiple stages detect missing data simultaneously.
"""

from __future__ import annotations

import contextlib
import os
import uuid
from datetime import UTC, datetime
from typing import Any

from data_refresh_service import DataRefreshService
from fetch_request_service import FetchRequestService

from the_alchemiser.shared.events import MarketDataFetchCompleted
from the_alchemiser.shared.events.eventbridge_publisher import publish_to_eventbridge
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


class FetchRequestHandler:
    """Handles on-demand market data fetch requests with deduplication."""

    def handle(self, event: dict[str, Any]) -> dict[str, Any]:
        """Handle a MarketDataFetchRequested event.

        Args:
            event: EventBridge event with MarketDataFetchRequested detail.

        Returns:
            Response indicating whether fetch was performed or deduplicated.

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

        fetch_table = os.environ.get("FETCH_REQUESTS_TABLE")
        fetch_service: FetchRequestService | None = None

        if fetch_table:
            fetch_service = FetchRequestService()
            result = fetch_service.try_acquire_fetch_lock(
                symbol=symbol,
                requesting_stage=requesting_stage,
                requesting_component=requesting_component,
                correlation_id=correlation_id,
            )

            if not result.can_proceed:
                logger.info(
                    "Fetch request deduplicated",
                    extra={
                        "correlation_id": correlation_id,
                        "symbol": symbol,
                        "existing_request_time": result.existing_request_time,
                        "cooldown_remaining_seconds": result.cooldown_remaining_seconds,
                    },
                )

                self._publish_fetch_completed(
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

        try:
            service = DataRefreshService()
            metadata = service.market_data_store.get_metadata(symbol)

            if metadata is None:
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
                bars_fetched = lookback_days if success else 0
            else:
                success, _metadata = service.refresh_symbol(symbol)
                bars_fetched = 1 if success else 0

            self._publish_fetch_completed(
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

            if fetch_service:
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
            if fetch_service:
                with contextlib.suppress(Exception):
                    fetch_service.release_fetch_lock(symbol, correlation_id)

            logger.error(
                "Fetch request exception",
                extra={"correlation_id": correlation_id, "symbol": symbol, "error": str(e)},
                exc_info=True,
            )

            self._publish_fetch_completed(
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
        self,
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
                source_component="FetchRequestHandler",
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
