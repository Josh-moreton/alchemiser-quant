"""Business Unit: data | Status: current.

Handler for scheduled data refresh and manual invocation.

Refreshes all configured symbols from Alpaca and publishes
DataLakeUpdateCompleted events for notifications.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from data_refresh_service import DataRefreshService
from symbol_extractor import get_all_configured_symbols

from the_alchemiser.shared.events import DataLakeUpdateCompleted, WorkflowFailed
from the_alchemiser.shared.events.eventbridge_publisher import publish_to_eventbridge
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


class ScheduledRefreshHandler:
    """Handles scheduled data refresh for all configured symbols."""

    def handle(self, event: dict[str, Any]) -> dict[str, Any]:
        """Handle scheduled or manual data refresh invocation.

        Args:
            event: Lambda event (schedule trigger or manual).

        Returns:
            Response with refresh statistics.

        """
        correlation_id = event.get("correlation_id") or f"data-refresh-{uuid.uuid4()}"
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
            return self._refresh(event, correlation_id, start_time)
        except Exception as e:
            logger.error(
                "Data Lambda failed with exception",
                extra={"correlation_id": correlation_id, "error": str(e)},
                exc_info=True,
            )
            self._publish_workflow_failed(correlation_id, e)
            return {
                "statusCode": 500,
                "body": {
                    "status": "error",
                    "correlation_id": correlation_id,
                    "error": str(e),
                },
            }

    def _refresh(
        self,
        event: dict[str, Any],
        correlation_id: str,
        start_time: datetime,
    ) -> dict[str, Any]:
        """Core refresh logic."""
        service = DataRefreshService()

        specific_symbols = event.get("symbols")
        full_seed = event.get("full_seed", False)
        process_markers = event.get("process_markers", True)

        results_dict: dict[str, bool] = {}
        adjustments_dict: dict[str, dict[str, Any]] = {}
        symbols_adjusted_list: list[str] = []
        all_metadata_dict: dict[str, dict[str, Any]] = {}

        if full_seed:
            seed_symbols = specific_symbols or sorted(get_all_configured_symbols())
            logger.info(
                "Full seed requested",
                extra={
                    "correlation_id": correlation_id,
                    "symbol_count": len(seed_symbols),
                    "symbols": seed_symbols,
                },
            )
            results_dict = service.seed_initial_data(seed_symbols)
        elif specific_symbols:
            logger.info(
                "Refreshing specific symbols",
                extra={"correlation_id": correlation_id, "symbols": specific_symbols},
            )
            for symbol in specific_symbols:
                success, metadata = service.refresh_symbol(symbol)
                results_dict[symbol] = success
                all_metadata_dict[symbol] = metadata
                if metadata.get("adjusted", False):
                    adjustments_dict[symbol] = metadata
                    symbols_adjusted_list.append(symbol)
        else:
            if process_markers:
                refresh_data = service.refresh_all_with_markers()
            else:
                refresh_data = service.refresh_all_symbols()
            results_dict = refresh_data["results"]
            adjustments_dict = refresh_data["adjustments"]
            symbols_adjusted_list = refresh_data["symbols_adjusted"]
            all_metadata_dict = refresh_data.get("all_metadata", {})

        return self._build_response(
            correlation_id,
            start_time,
            results_dict,
            adjustments_dict,
            symbols_adjusted_list,
            all_metadata_dict,
        )

    def _build_response(
        self,
        correlation_id: str,
        start_time: datetime,
        results_dict: dict[str, bool],
        adjustments_dict: dict[str, dict[str, Any]],
        symbols_adjusted_list: list[str],
        all_metadata_dict: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        """Calculate statistics and build response."""
        total = len(results_dict)
        success_count = sum(results_dict.values())
        failed_count = total - success_count
        failed_symbols = [s for s, ok in results_dict.items() if not ok]
        success_symbols = [s for s, ok in results_dict.items() if ok]

        adjustment_count = sum(adj.get("adjustment_count", 0) for adj in adjustments_dict.values())
        adjusted_dates_by_symbol = {
            symbol: adj.get("adjusted_dates", [])
            for symbol, adj in adjustments_dict.items()
            if adj.get("adjusted_dates")
        }

        successful_metadata = [
            all_metadata_dict[symbol]
            for symbol, ok in results_dict.items()
            if ok and symbol in all_metadata_dict
        ]
        total_bars_fetched = sum(metadata.get("new_bars", 0) for metadata in successful_metadata)

        all_bar_dates: set[str] = set()
        for metadata in successful_metadata:
            all_bar_dates.update(metadata.get("bar_dates", []))
        sorted_bar_dates = sorted(all_bar_dates)

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
                "adjusted_count": len(symbols_adjusted_list),
                "adjusted_symbols": symbols_adjusted_list,
                "duration_seconds": duration,
            },
        )

        if failed_count == 0:
            status_code = 200
            overall_success = True
        elif success_count > 0:
            status_code = 206
            overall_success = False
        else:
            status_code = 500
            overall_success = False

        self._publish_data_lake_update(
            correlation_id=correlation_id,
            overall_success=overall_success,
            status_code=status_code,
            total=total,
            success_symbols=success_symbols,
            failed_symbols=failed_symbols,
            total_bars_fetched=total_bars_fetched,
            sorted_bar_dates=sorted_bar_dates,
            symbols_adjusted_list=symbols_adjusted_list,
            adjustment_count=adjustment_count,
            adjusted_dates_by_symbol=adjusted_dates_by_symbol,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
        )

        response_body: dict[str, Any] = {
            "correlation_id": correlation_id,
            "total_symbols": total,
            "refreshed": success_count,
        }

        if failed_count > 0:
            response_body.update({"failed": failed_count, "failed_symbols": failed_symbols})

        if status_code == 200:
            response_body["status"] = "success"
        elif status_code == 206:
            response_body["status"] = "partial_success"
        else:
            response_body["status"] = "failed"

        return {"statusCode": status_code, "body": response_body}

    def _publish_data_lake_update(
        self,
        correlation_id: str,
        *,
        overall_success: bool,
        status_code: int,
        total: int,
        success_symbols: list[str],
        failed_symbols: list[str],
        total_bars_fetched: int,
        sorted_bar_dates: list[str],
        symbols_adjusted_list: list[str],
        adjustment_count: int,
        adjusted_dates_by_symbol: dict[str, list[str]],
        start_time: datetime,
        end_time: datetime,
        duration: float,
    ) -> None:
        """Publish DataLakeUpdateCompleted event for notifications."""
        try:
            update_event = DataLakeUpdateCompleted(
                correlation_id=correlation_id,
                causation_id=correlation_id,
                event_id=f"data-lake-update-{uuid.uuid4()}",
                timestamp=end_time,
                source_module="data_v2",
                source_component="ScheduledRefreshHandler",
                success=overall_success,
                status_code=status_code,
                total_symbols=total,
                symbols_updated=success_symbols,
                failed_symbols=failed_symbols,
                symbols_updated_count=len(success_symbols),
                symbols_failed_count=len(failed_symbols),
                total_bars_fetched=total_bars_fetched,
                bar_dates=sorted_bar_dates,
                data_source="alpaca_api",
                symbols_adjusted=symbols_adjusted_list,
                adjustment_count=adjustment_count,
                adjusted_dates_by_symbol=adjusted_dates_by_symbol,
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
                    "adjustments_detected": len(symbols_adjusted_list) > 0,
                },
            )
        except Exception as pub_error:
            logger.error(
                "Failed to publish DataLakeUpdateCompleted event",
                extra={"correlation_id": correlation_id, "error": str(pub_error)},
            )

    def _publish_workflow_failed(self, correlation_id: str, error: Exception) -> None:
        """Publish WorkflowFailed event. Non-fatal on failure."""
        try:
            failure_event = WorkflowFailed(
                correlation_id=correlation_id,
                causation_id=correlation_id,
                event_id=f"data-refresh-failed-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="data_v2",
                source_component="ScheduledRefreshHandler",
                workflow_type="data_refresh",
                failure_reason=str(error),
                failure_step="data_refresh",
                error_details={"exception_type": type(error).__name__},
            )
            publish_to_eventbridge(failure_event)
        except Exception as pub_error:
            logger.error(
                "Failed to publish WorkflowFailed event",
                extra={"error": str(pub_error)},
            )
