"""Business Unit: coordinator_v2 | Status: current.

Lambda handler for Schedule Manager microservice.

This Lambda runs early each trading day (e.g., 9:00 AM ET) to:
1. Check if today is a trading day
2. Get the market close time (accounting for early closes)
3. Create/update a one-time EventBridge Scheduler rule to trigger
   the Strategy Orchestrator at the appropriate time

This enables dynamic scheduling that handles early close days automatically.
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime
from typing import Any

import boto3

from the_alchemiser.shared.brokers.alpaca_utils import create_trading_client
from the_alchemiser.shared.config.config import Settings
from the_alchemiser.shared.events import ScheduleCreated, WorkflowFailed
from the_alchemiser.shared.events.eventbridge_publisher import publish_to_eventbridge
from the_alchemiser.shared.logging import configure_application_logging, get_logger
from the_alchemiser.shared.services.market_calendar_service import (
    MarketCalendarService,
)

# Initialize logging on cold start
configure_application_logging()

logger = get_logger(__name__)

# Environment variables
ORCHESTRATOR_FUNCTION_ARN = os.environ.get("ORCHESTRATOR_FUNCTION_ARN", "")
SCHEDULER_ROLE_ARN = os.environ.get("SCHEDULER_ROLE_ARN", "")
SCHEDULE_GROUP_NAME = os.environ.get("SCHEDULE_GROUP_NAME", "default")
MINUTES_BEFORE_CLOSE = int(os.environ.get("MINUTES_BEFORE_CLOSE", "15"))
APP_STAGE = os.environ.get("APP__STAGE", "dev")


def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle morning invocation to set up today's trading schedule.

    This handler:
    1. Checks if today is a trading day
    2. Gets the market close time (handles early closes)
    3. Creates a one-time EventBridge Scheduler rule for today's execution

    Args:
        event: Lambda event (from EventBridge schedule - morning trigger)
        context: Lambda context

    Returns:
        Response with schedule status and execution time.

    """
    correlation_id = event.get("correlation_id") or f"schedule-{uuid.uuid4()}"
    today = datetime.now(UTC).date()

    logger.info(
        "Schedule Manager Lambda invoked",
        extra={
            "correlation_id": correlation_id,
            "date": today.isoformat(),
        },
    )

    try:
        # Validate required environment variables
        if not ORCHESTRATOR_FUNCTION_ARN:
            raise ValueError("ORCHESTRATOR_FUNCTION_ARN environment variable is required")
        if not SCHEDULER_ROLE_ARN:
            raise ValueError("SCHEDULER_ROLE_ARN environment variable is required")

        # Load settings and create calendar service
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

        # Get today's market info
        market_day = calendar_service.get_market_day(today, correlation_id=correlation_id)

        if not market_day:
            # Check if it's a weekend (don't notify) or a holiday (notify)
            day_of_week = today.weekday()  # 0=Monday, 6=Sunday
            is_weekend = day_of_week >= 5

            logger.info(
                "Today is not a trading day - no schedule created",
                extra={
                    "correlation_id": correlation_id,
                    "date": today.isoformat(),
                    "is_weekend": is_weekend,
                },
            )

            # Only notify on holidays, not regular weekends
            if not is_weekend:
                _publish_schedule_created(
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

        # Calculate execution time
        execution_time = calendar_service.get_execution_time(
            today,
            minutes_before_close=MINUTES_BEFORE_CLOSE,
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

        # Create one-time EventBridge Scheduler rule
        schedule_name = f"alchemiser-{APP_STAGE}-trading-execution-{today.isoformat()}"

        _create_one_time_schedule(
            schedule_name=schedule_name,
            execution_time=execution_time,
            correlation_id=correlation_id,
        )

        logger.info(
            "Schedule created successfully",
            extra={
                "correlation_id": correlation_id,
                "schedule_name": schedule_name,
                "execution_time": execution_time.isoformat(),
                "is_early_close": market_day.is_early_close,
            },
        )

        # Publish ScheduleCreated event for notifications
        # Use 'early_close' status if it's an early close day, otherwise 'scheduled'
        schedule_status = "early_close" if market_day.is_early_close else "scheduled"
        _publish_schedule_created(
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

    except Exception as e:
        logger.error(
            "Schedule Manager Lambda failed",
            extra={
                "correlation_id": correlation_id,
                "error": str(e),
            },
            exc_info=True,
        )

        # Publish WorkflowFailed to EventBridge for notification
        try:
            failure_event = WorkflowFailed(
                correlation_id=correlation_id,
                causation_id=f"schedule-manager-{today.isoformat()}",
                event_id=f"schedule-failed-{uuid.uuid4()}",
                timestamp=datetime.now(UTC),
                source_module="coordinator_v2",
                source_component="ScheduleManager",
                workflow_type="schedule_creation",
                failure_reason=str(e),
                failure_step="schedule_creation",
                error_details={
                    "exception_type": type(e).__name__,
                    "date": today.isoformat(),
                },
            )
            publish_to_eventbridge(failure_event)
            logger.info(
                "Published WorkflowFailed event for schedule manager failure",
                extra={"correlation_id": correlation_id},
            )
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


def _create_one_time_schedule(
    schedule_name: str,
    execution_time: datetime,
    correlation_id: str,
) -> None:
    """Create a one-time EventBridge Scheduler rule.

    Args:
        schedule_name: Name for the schedule
        execution_time: When to execute (naive datetime in ET)
        correlation_id: Correlation ID for tracing

    """
    scheduler = boto3.client("scheduler")

    # Format: at(yyyy-mm-ddThh:mm:ss)
    # The execution_time is in ET (from market calendar)
    schedule_expression = f"at({execution_time.strftime('%Y-%m-%dT%H:%M:%S')})"

    try:
        # Try to delete existing schedule for today (in case of re-run)
        try:
            scheduler.delete_schedule(
                Name=schedule_name,
                GroupName=SCHEDULE_GROUP_NAME,
            )
            logger.debug(
                "Deleted existing schedule",
                schedule_name=schedule_name,
            )
        except scheduler.exceptions.ResourceNotFoundException:
            pass  # Schedule doesn't exist, that's fine

        # Create new one-time schedule
        scheduler.create_schedule(
            Name=schedule_name,
            GroupName=SCHEDULE_GROUP_NAME,
            ScheduleExpression=schedule_expression,
            ScheduleExpressionTimezone="America/New_York",
            FlexibleTimeWindow={"Mode": "OFF"},
            Target={
                "Arn": ORCHESTRATOR_FUNCTION_ARN,
                "RoleArn": SCHEDULER_ROLE_ARN,
                "Input": f'{{"mode": "trade", "correlation_id": "{correlation_id}", "scheduled_by": "schedule_manager"}}',
            },
            ActionAfterCompletion="DELETE",  # Clean up after execution
        )

        logger.info(
            "Created one-time schedule",
            schedule_name=schedule_name,
            schedule_expression=schedule_expression,
            target_arn=ORCHESTRATOR_FUNCTION_ARN,
        )

    except Exception as e:
        logger.error(
            "Failed to create schedule",
            schedule_name=schedule_name,
            error=str(e),
        )
        raise


def _publish_schedule_created(
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
    """Publish ScheduleCreated event to EventBridge.

    Args:
        correlation_id: Correlation ID for tracing
        status: Schedule status ('scheduled', 'early_close', 'skipped_holiday')
        date: Trading date (ISO format)
        execution_time: Scheduled execution time (ISO format)
        market_close_time: Market close time (ISO format)
        is_early_close: Whether this is an early close day
        schedule_name: Name of the created schedule
        skip_reason: Reason for skipping (for holidays)

    """
    try:
        schedule_event = ScheduleCreated(
            correlation_id=correlation_id,
            causation_id=f"schedule-manager-{date}",
            event_id=f"schedule-created-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="coordinator_v2",
            source_component="ScheduleManager",
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
