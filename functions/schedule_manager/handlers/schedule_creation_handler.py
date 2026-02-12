"""Business Unit: coordinator_v2 | Status: current.

Handler for creating daily trading schedules.

Checks if today is a trading day, determines market close time
(accounting for early closes), and creates a one-time EventBridge
Scheduler rule to trigger the Strategy Orchestrator.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from typing import Any

import boto3
from config import ScheduleManagerSettings

from the_alchemiser.shared.brokers.alpaca_utils import create_trading_client
from the_alchemiser.shared.config.config import Settings
from the_alchemiser.shared.events import ScheduleCreated, WorkflowFailed
from the_alchemiser.shared.events.eventbridge_publisher import publish_to_eventbridge
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.services.market_calendar_service import (
    MarketCalendarService,
)

logger = get_logger(__name__)


class ScheduleCreationHandler:
    """Creates daily trading execution schedules via EventBridge Scheduler."""

    def __init__(self, settings: ScheduleManagerSettings) -> None:
        self._settings = settings

    def handle(self, correlation_id: str) -> dict[str, Any]:
        """Check market calendar and create today's execution schedule.

        Args:
            correlation_id: Workflow correlation ID.

        Returns:
            Response with schedule status and execution time.

        """
        today = datetime.now(UTC).date()

        try:
            return self._create_schedule(correlation_id, today)
        except Exception as e:
            logger.error(
                "Schedule Manager Lambda failed",
                extra={"correlation_id": correlation_id, "error": str(e)},
                exc_info=True,
            )
            self._publish_workflow_failed(correlation_id, today, e)
            return {
                "statusCode": 500,
                "body": {
                    "status": "error",
                    "correlation_id": correlation_id,
                    "error": str(e),
                },
            }

    def _create_schedule(self, correlation_id: str, today: date) -> dict[str, Any]:
        """Core scheduling logic."""
        if not self._settings.orchestrator_function_arn:
            raise ValueError("ORCHESTRATOR_FUNCTION_ARN environment variable is required")
        if not self._settings.scheduler_role_arn:
            raise ValueError("SCHEDULER_ROLE_ARN environment variable is required")

        app_settings = Settings()

        alpaca_key = app_settings.alpaca.key
        alpaca_secret = app_settings.alpaca.secret
        if not alpaca_key or not alpaca_secret:
            raise ValueError("Alpaca API credentials not configured")

        trading_client = create_trading_client(
            api_key=alpaca_key,
            secret_key=alpaca_secret,
            paper=app_settings.alpaca.endpoint != "https://api.alpaca.markets",
        )
        calendar_service = MarketCalendarService(trading_client)

        market_day = calendar_service.get_market_day(today, correlation_id=correlation_id)

        if not market_day:
            return self._handle_non_trading_day(correlation_id, today)

        execution_time = calendar_service.get_execution_time(
            today,
            minutes_before_close=self._settings.minutes_before_close,
            correlation_id=correlation_id,
        )
        if not execution_time:
            raise ValueError("Failed to calculate execution time")

        logger.info(
            "Creating schedule for today's execution",
            extra={
                "correlation_id": correlation_id,
                "date": today.isoformat(),
                "close_time": market_day.close_time.isoformat(),
                "is_early_close": market_day.is_early_close,
                "execution_time": execution_time.isoformat(),
            },
        )

        schedule_name = (
            f"alchemiser-{self._settings.app_stage}-trading-execution-{today.isoformat()}"
        )
        self._create_one_time_schedule(schedule_name, execution_time, correlation_id)

        logger.info(
            "Schedule created successfully",
            extra={
                "correlation_id": correlation_id,
                "schedule_name": schedule_name,
                "execution_time": execution_time.isoformat(),
                "is_early_close": market_day.is_early_close,
            },
        )

        schedule_status = "early_close" if market_day.is_early_close else "scheduled"
        self._publish_schedule_created(
            correlation_id=correlation_id,
            status=schedule_status,
            date=today.isoformat(),
            execution_time=execution_time.isoformat(),
            market_close_time=market_day.close_time.isoformat(),
            is_early_close=market_day.is_early_close,
            schedule_name=schedule_name,
        )

        return {
            "statusCode": 200,
            "body": {
                "status": "scheduled",
                "correlation_id": correlation_id,
                "date": today.isoformat(),
                "execution_time": execution_time.isoformat(),
                "close_time": market_day.close_time.isoformat(),
                "is_early_close": market_day.is_early_close,
                "schedule_name": schedule_name,
            },
        }

    def _handle_non_trading_day(self, correlation_id: str, today: date) -> dict[str, Any]:
        """Handle days when the market is closed."""
        day_of_week = today.weekday()
        is_weekend = day_of_week >= 5

        logger.info(
            "Today is not a trading day - no schedule created",
            extra={
                "correlation_id": correlation_id,
                "date": today.isoformat(),
                "is_weekend": is_weekend,
            },
        )

        if not is_weekend:
            self._publish_schedule_created(
                correlation_id=correlation_id,
                status="skipped_holiday",
                date=today.isoformat(),
                skip_reason="Market closed (holiday)",
            )

        return {
            "statusCode": 200,
            "body": {
                "status": "skipped",
                "correlation_id": correlation_id,
                "reason": "Not a trading day",
                "date": today.isoformat(),
            },
        }

    def _create_one_time_schedule(
        self,
        schedule_name: str,
        execution_time: datetime,
        correlation_id: str,
    ) -> None:
        """Create a one-time EventBridge Scheduler rule."""
        scheduler = boto3.client("scheduler")
        schedule_expression = f"at({execution_time.strftime('%Y-%m-%dT%H:%M:%S')})"

        try:
            try:
                scheduler.delete_schedule(
                    Name=schedule_name,
                    GroupName=self._settings.schedule_group_name,
                )
                logger.debug("Deleted existing schedule", schedule_name=schedule_name)
            except scheduler.exceptions.ResourceNotFoundException:
                pass

            scheduler.create_schedule(
                Name=schedule_name,
                GroupName=self._settings.schedule_group_name,
                ScheduleExpression=schedule_expression,
                ScheduleExpressionTimezone="America/New_York",
                FlexibleTimeWindow={"Mode": "OFF"},
                Target={
                    "Arn": self._settings.orchestrator_function_arn,
                    "RoleArn": self._settings.scheduler_role_arn,
                    "Input": (
                        f'{{"mode": "trade", "correlation_id": "{correlation_id}", '
                        f'"scheduled_by": "schedule_manager"}}'
                    ),
                },
                ActionAfterCompletion="DELETE",
            )

            logger.info(
                "Created one-time schedule",
                schedule_name=schedule_name,
                schedule_expression=schedule_expression,
                target_arn=self._settings.orchestrator_function_arn,
            )
        except Exception as e:
            logger.error(
                "Failed to create schedule",
                schedule_name=schedule_name,
                error=str(e),
            )
            raise

    def _publish_schedule_created(
        self,
        correlation_id: str,
        status: str,
        date: str,
        *,
        execution_time: str | None = None,
        market_close_time: str | None = None,
        is_early_close: bool = False,
        schedule_name: str | None = None,
        skip_reason: str | None = None,
    ) -> None:
        """Publish ScheduleCreated event to EventBridge."""
        try:
            schedule_event = ScheduleCreated(
                correlation_id=correlation_id,
                causation_id=f"schedule-manager-{date}",
                event_id=f"schedule-created-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="coordinator_v2",
                source_component="ScheduleCreationHandler",
                status=status,
                date=date,
                execution_time=execution_time,
                market_close_time=market_close_time,
                is_early_close=is_early_close,
                schedule_name=schedule_name,
                skip_reason=skip_reason,
            )
            publish_to_eventbridge(schedule_event)
            logger.info(
                "Published ScheduleCreated event",
                extra={
                    "correlation_id": correlation_id,
                    "status": status,
                    "date": date,
                    "is_early_close": is_early_close,
                },
            )
        except Exception as pub_error:
            logger.error(
                "Failed to publish ScheduleCreated event",
                extra={"error": str(pub_error), "correlation_id": correlation_id},
            )

    def _publish_workflow_failed(
        self,
        correlation_id: str,
        today: date,
        error: Exception,
    ) -> None:
        """Publish WorkflowFailed event. Non-fatal on failure."""
        try:
            failure_event = WorkflowFailed(
                correlation_id=correlation_id,
                causation_id=f"schedule-manager-{today.isoformat()}",
                event_id=f"schedule-failed-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="coordinator_v2",
                source_component="ScheduleCreationHandler",
                workflow_type="schedule_creation",
                failure_reason=str(error),
                failure_step="schedule_creation",
                error_details={
                    "exception_type": type(error).__name__,
                    "date": today.isoformat(),
                },
            )
            publish_to_eventbridge(failure_event)
        except Exception as pub_error:
            logger.error(
                "Failed to publish WorkflowFailed event",
                extra={"error": str(pub_error)},
            )
