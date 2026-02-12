"""Business Unit: notifications | Status: current.

Handlers for DataLakeUpdateCompleted and ScheduleCreated events.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from service import NotificationService

from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.events.schemas import (
    DataLakeNotificationRequested,
    ScheduleNotificationRequested,
)
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


class OperationalHandler:
    """Handles DataLakeUpdateCompleted and ScheduleCreated events."""

    def handle_data_lake_update(
        self,
        detail: dict[str, Any],
        correlation_id: str,
    ) -> dict[str, Any]:
        """Handle DataLakeUpdateCompleted event.

        Args:
            detail: The detail payload from DataLakeUpdateCompleted event.
            correlation_id: Correlation ID for tracing.

        Returns:
            Response with status code and message.

        """
        total_symbols = detail.get("total_symbols", 0)
        success_count = detail.get("symbols_updated_count", 0)
        failed_count = detail.get("symbols_failed_count", 0)

        logger.info(
            "Processing DataLakeUpdateCompleted",
            extra={
                "correlation_id": correlation_id,
                "total_symbols": total_symbols,
                "success_count": success_count,
                "failed_count": failed_count,
            },
        )

        container = ApplicationContainer.create_for_notifications("production")
        notification_event = _build_data_lake_notification(detail, correlation_id)
        notification_service = NotificationService(container)
        notification_service.handle_event(notification_event)

        return {
            "statusCode": 200,
            "body": f"Data lake notification sent for correlation_id: {correlation_id}",
        }

    def handle_schedule_created(
        self,
        detail: dict[str, Any],
        correlation_id: str,
    ) -> dict[str, Any]:
        """Handle ScheduleCreated event.

        Args:
            detail: The detail payload from ScheduleCreated event.
            correlation_id: Correlation ID for tracing.

        Returns:
            Response with status code and message.

        """
        status = detail.get("status", "scheduled")
        date = detail.get("date", "unknown")
        is_early_close = detail.get("is_early_close", False)

        logger.info(
            "Processing ScheduleCreated",
            extra={
                "correlation_id": correlation_id,
                "status": status,
                "date": date,
                "is_early_close": is_early_close,
            },
        )

        container = ApplicationContainer.create_for_notifications("production")
        notification_event = _build_schedule_notification(detail, correlation_id)
        notification_service = NotificationService(container)
        notification_service.handle_event(notification_event)

        return {
            "statusCode": 200,
            "body": f"Schedule notification sent for correlation_id: {correlation_id}",
        }


def _build_data_lake_notification(
    update_detail: dict[str, Any],
    correlation_id: str,
) -> DataLakeNotificationRequested:
    """Build DataLakeNotificationRequested from DataLakeUpdateCompleted event."""
    status_code = update_detail.get("status_code", 500)
    if status_code == 200:
        status = "SUCCESS"
    elif status_code == 206:
        status = "SUCCESS_WITH_WARNINGS"
    else:
        status = "FAILURE"

    data_lake_context = {
        "total_symbols": update_detail.get("total_symbols", 0),
        "symbols_updated": update_detail.get("symbols_updated", []),
        "failed_symbols": update_detail.get("failed_symbols", []),
        "symbols_updated_count": update_detail.get("symbols_updated_count", 0),
        "symbols_failed_count": update_detail.get("symbols_failed_count", 0),
        "total_bars_fetched": update_detail.get("total_bars_fetched", 0),
        "bar_dates": update_detail.get("bar_dates", []),
        "data_source": update_detail.get("data_source", "alpaca_api"),
        "start_time_utc": update_detail.get("start_time_utc", ""),
        "end_time_utc": update_detail.get("end_time_utc", ""),
        "duration_seconds": update_detail.get("duration_seconds", 0),
        "error_message": update_detail.get("error_message"),
        "error_details": update_detail.get("error_details", {}),
    }

    return DataLakeNotificationRequested(
        correlation_id=correlation_id,
        causation_id=update_detail.get("event_id", correlation_id),
        event_id=f"data-lake-notification-{uuid4()}",
        timestamp=datetime.now(UTC),
        source_module="notifications_v2.lambda_handler",
        source_component="NotificationsLambda",
        status=status,
        data_lake_context=data_lake_context,
    )


def _build_schedule_notification(
    schedule_detail: dict[str, Any],
    correlation_id: str,
) -> ScheduleNotificationRequested:
    """Build ScheduleNotificationRequested from ScheduleCreated event."""
    schedule_context = {
        "status": schedule_detail.get("status", "scheduled"),
        "date": schedule_detail.get("date", "unknown"),
        "execution_time": schedule_detail.get("execution_time"),
        "market_close_time": schedule_detail.get("market_close_time"),
        "is_early_close": schedule_detail.get("is_early_close", False),
        "schedule_name": schedule_detail.get("schedule_name"),
        "skip_reason": schedule_detail.get("skip_reason"),
        "env": os.environ.get("APP__STAGE", "dev"),
    }

    return ScheduleNotificationRequested(
        correlation_id=correlation_id,
        causation_id=schedule_detail.get("event_id", correlation_id),
        event_id=f"schedule-notification-{uuid4()}",
        timestamp=datetime.now(UTC),
        source_module="notifications_v2.lambda_handler",
        source_component="NotificationsLambda",
        schedule_context=schedule_context,
    )
