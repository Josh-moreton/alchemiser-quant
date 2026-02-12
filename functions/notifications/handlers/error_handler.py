"""Business Unit: notifications | Status: current.

Handlers for WorkflowFailed, Lambda async failures, and CloudWatch alarms.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from handlers.session_lookup import get_notification_session
from service import NotificationService

from the_alchemiser.shared.config.container import ApplicationContainer
from the_alchemiser.shared.events.schemas import ErrorNotificationRequested
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


class ErrorHandler:
    """Handles WorkflowFailed, Lambda async failure, and CloudWatch alarm events."""

    def handle_workflow_failed(
        self,
        detail: dict[str, Any],
        correlation_id: str,
        source: str,
    ) -> dict[str, Any]:
        """Handle WorkflowFailed events by sending error notifications.

        Defers strategy-related failures to consolidated handler when a session exists.

        Args:
            detail: The detail payload from WorkflowFailed event.
            correlation_id: Correlation ID for tracing.
            source: Event source (e.g., alchemiser.strategy).

        Returns:
            Response with status code and message.

        """
        workflow_type = detail.get("workflow_type", "unknown")

        logger.info(
            "Processing WorkflowFailed event",
            extra={
                "correlation_id": correlation_id,
                "source": source,
                "workflow_type": workflow_type,
            },
        )

        strategy_workflow_types = {
            "strategy_coordination",
            "trade_aggregation",
            "portfolio_analysis",
        }
        if workflow_type in strategy_workflow_types:
            session = get_notification_session(correlation_id)
            if session is not None:
                logger.info(
                    "Notification session found - deferring error email to consolidated handler",
                    extra={
                        "correlation_id": correlation_id,
                        "workflow_type": workflow_type,
                        "total_strategies": session.get("total_strategies"),
                        "completed_strategies": session.get("completed_strategies"),
                    },
                )
                return {
                    "statusCode": 200,
                    "body": f"Deferred to consolidated notification for {correlation_id}",
                }

        container = ApplicationContainer.create_for_notifications("production")
        notification_event = _build_error_notification(detail, correlation_id, source)
        notification_service = NotificationService(container)
        notification_service.handle_event(notification_event)

        logger.info(
            "Error notification processed successfully",
            extra={
                "correlation_id": correlation_id,
                "failure_step": detail.get("failure_step", "unknown"),
                "workflow_type": workflow_type,
            },
        )

        return {
            "statusCode": 200,
            "body": f"Error notification sent for correlation_id: {correlation_id}",
        }

    def handle_lambda_async_failure(
        self,
        detail: dict[str, Any],
        correlation_id: str,
        source: str,
    ) -> dict[str, Any]:
        """Handle Lambda async invocation failure events from Lambda Destinations.

        Args:
            detail: The detail payload from Lambda Destination failure event.
            correlation_id: Correlation ID for tracing.
            source: Event source (typically "lambda").

        Returns:
            Response with status code and message.

        """
        request_context = detail.get("requestContext", {})
        response_payload = detail.get("responsePayload", {})

        function_arn = request_context.get("functionArn", "unknown")
        condition = request_context.get("condition", "unknown")
        request_id = request_context.get("requestId", "")

        error_type = response_payload.get("errorType", "UnknownError")
        error_message = response_payload.get("errorMessage", "No error message available")
        function_name = function_arn.split(":")[-1] if ":" in function_arn else function_arn

        logger.warning(
            "Processing Lambda async invocation failure",
            extra={
                "correlation_id": correlation_id,
                "source": source,
                "function_name": function_name,
                "function_arn": function_arn,
                "condition": condition,
                "error_type": error_type,
                "request_id": request_id,
            },
        )

        container = ApplicationContainer.create_for_notifications("production")

        error_report = f"""
Lambda Async Invocation Failure
===============================

Function: {function_name}
Condition: {condition}
Request ID: {request_id}
Correlation ID: {correlation_id}

Error Type: {error_type}
Error Message: {error_message}

Full Function ARN:
{function_arn}

This failure occurred after all AWS retry attempts were exhausted.
The async invocation (likely from StrategyOrchestratorFunction) failed
without the target function being able to publish a WorkflowFailed event.
"""

        notification_event = ErrorNotificationRequested(
            correlation_id=correlation_id,
            causation_id=request_id or correlation_id,
            event_id=f"lambda-async-failure-{uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="notifications_v2.lambda_handler",
            source_component="NotificationsLambda",
            error_severity="CRITICAL",
            error_priority="HIGH",
            error_title=f"Lambda Async Failure: {function_name} ({condition})",
            error_report=error_report.strip(),
            error_code=error_type,
        )

        notification_service = NotificationService(container)
        notification_service.handle_event(notification_event)

        logger.info(
            "Lambda async failure notification sent",
            extra={
                "correlation_id": correlation_id,
                "function_name": function_name,
                "condition": condition,
            },
        )

        return {
            "statusCode": 200,
            "body": f"Lambda async failure notification sent for {function_name}",
        }

    def handle_cloudwatch_alarm(
        self,
        event: dict[str, Any],
        correlation_id: str,
    ) -> dict[str, Any]:
        """Handle CloudWatch Alarm State Change events.

        Args:
            event: The full EventBridge event (not unwrapped detail).
            correlation_id: Correlation ID for tracing.

        Returns:
            Response with status code and message.

        """
        detail = event.get("detail", {})
        alarm_name = detail.get("alarmName", "Unknown Alarm")
        alarm_description = detail.get("configuration", {}).get("description", "")
        state = detail.get("state", {})
        state_value = state.get("value", "UNKNOWN")
        state_reason = state.get("reason", "No reason provided")
        state_timestamp = state.get("timestamp", "")

        if state_value != "ALARM":
            logger.debug(
                "Ignoring CloudWatch alarm state change",
                extra={
                    "correlation_id": correlation_id,
                    "alarm_name": alarm_name,
                    "state_value": state_value,
                },
            )
            return {
                "statusCode": 200,
                "body": f"Ignored alarm state: {state_value}",
            }

        logger.warning(
            "Processing CloudWatch alarm",
            extra={
                "correlation_id": correlation_id,
                "alarm_name": alarm_name,
                "state_value": state_value,
                "state_reason": state_reason,
            },
        )

        error_title, impact = _classify_alarm(alarm_name)

        container = ApplicationContainer.create_for_notifications("production")

        error_report = f"""
CloudWatch Alarm Alert
======================

Alarm Name: {alarm_name}
State: {state_value}
Timestamp: {state_timestamp}
Correlation ID: {correlation_id}

Description:
{alarm_description or "No description provided"}

Reason:
{state_reason}

Impact:
{impact}

Quick Actions:
- Check CloudWatch Logs for related Lambda functions
- Review DynamoDB tables for stuck sessions/runs
- Inspect SQS DLQ for failed messages
- Verify recent deployments for potential regressions
"""

        notification_event = ErrorNotificationRequested(
            correlation_id=correlation_id,
            causation_id=correlation_id,
            event_id=f"cloudwatch-alarm-{uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="notifications_v2.lambda_handler",
            source_component="NotificationsLambda",
            error_severity="CRITICAL",
            error_priority="HIGH",
            error_title=error_title,
            error_report=error_report.strip(),
            error_code="CloudWatchAlarm",
        )

        notification_service = NotificationService(container)
        notification_service.handle_event(notification_event)

        logger.info(
            "CloudWatch alarm notification sent",
            extra={
                "correlation_id": correlation_id,
                "alarm_name": alarm_name,
                "error_title": error_title,
            },
        )

        return {
            "statusCode": 200,
            "body": f"CloudWatch alarm notification sent for {alarm_name}",
        }


def _classify_alarm(alarm_name: str) -> tuple[str, str]:
    """Classify alarm by name and return (title, impact) tuple."""
    alarm_lower = alarm_name.lower()
    if "dlq" in alarm_lower:
        return (
            "DLQ Alert: Failed Messages Detected",
            "Messages have landed in the dead letter queue after exhausting retries.",
        )
    if "stuck" in alarm_lower and "aggregation" in alarm_lower:
        return (
            "Stuck Aggregation Session Alert",
            "An aggregation session has been stuck in PENDING state for over 30 minutes. "
            "Strategy workers may have failed silently.",
        )
    if "stuck" in alarm_lower:
        return (
            "Stuck Execution Run Alert",
            "An execution run has been stuck in RUNNING state for over 30 minutes. "
            "Trades may not have completed.",
        )
    if "error" in alarm_lower or "orchestrator" in alarm_lower:
        return (
            "Lambda Error Alert",
            "A Lambda function has encountered errors (timeouts, crashes, or unhandled exceptions).",
        )
    return (f"CloudWatch Alarm: {alarm_name}", "A CloudWatch alarm has triggered.")


def _build_error_notification(
    workflow_failed_detail: dict[str, Any],
    correlation_id: str,
    source: str,
) -> ErrorNotificationRequested:
    """Build ErrorNotificationRequested from WorkflowFailed event detail."""
    workflow_type = workflow_failed_detail.get("workflow_type", "unknown")
    failure_reason = workflow_failed_detail.get("failure_reason", "Unknown error")
    failure_step = workflow_failed_detail.get("failure_step", "unknown")
    error_details = workflow_failed_detail.get("error_details", {})

    source_module = source.replace("alchemiser.", "") if source else "unknown"

    is_hedge_failure = workflow_type == "hedge_evaluation"
    severity = "MEDIUM" if is_hedge_failure else "CRITICAL"
    priority = "MEDIUM" if is_hedge_failure else "HIGH"

    error_report = f"""
Workflow Failure Report
=======================

Workflow Type: {workflow_type}
Failed Step: {failure_step}
Source Module: {source_module}
Correlation ID: {correlation_id}

Failure Reason:
{failure_reason}

Error Details:
{_format_error_details(error_details)}
"""

    return ErrorNotificationRequested(
        correlation_id=correlation_id,
        causation_id=workflow_failed_detail.get("event_id", correlation_id),
        event_id=f"error-notification-{uuid4()}",
        timestamp=datetime.now(UTC),
        source_module="notifications_v2.lambda_handler",
        source_component="NotificationsLambda",
        error_severity=severity,
        error_priority=priority,
        error_title=f"Workflow Failed: {failure_step}",
        error_report=error_report.strip(),
        error_code=error_details.get("exception_type"),
        workflow_type=workflow_type,
    )


def _format_error_details(error_details: dict[str, Any]) -> str:
    """Format error details dictionary for email display."""
    if not error_details:
        return "No additional details available"
    lines = []
    for key, value in error_details.items():
        lines.append(f"  - {key}: {value}")
    return "\n".join(lines)
