"""Business Unit: notifications | Status: current.

Notification service for event-driven notifications via SES.

This service consumes notification events and sends templated HTML + plain text emails
via Amazon SES with deduplication and recovery tracking.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer

from the_alchemiser.shared.events.base import BaseEvent
from the_alchemiser.shared.events.schemas import (
    DataLakeNotificationRequested,
    ErrorNotificationRequested,
    SystemNotificationRequested,
    TradingNotificationRequested,
)
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.notifications.dedup import get_dedup_manager
from the_alchemiser.shared.notifications.ses_publisher import send_email
from the_alchemiser.shared.notifications.templates import (
    format_subject,
    render_daily_run_failure_html,
    render_daily_run_failure_text,
    render_daily_run_partial_success_html,
    render_daily_run_partial_success_text,
    render_daily_run_success_html,
    render_daily_run_success_text,
)


class NotificationService:
    """Event-driven notification service using Amazon SES.

    Consumes notification events and sends appropriate emails using SES
    with HTML + plain text templates, deduplication, and recovery tracking.
    """

    def __init__(self, container: ApplicationContainer) -> None:
        """Initialize notification service.

        Args:
            container: Application container for dependency injection

        """
        self.container = container
        self.logger = get_logger(__name__)
        self.event_bus = container.services.event_bus()
        # Track processed events for idempotency (in-memory for Lambda)
        self._processed_events: set[str] = set()

        # Get environment configuration
        self.stage = os.environ.get("APP__STAGE", "dev")
        self.prod_recipients = os.environ.get("NOTIFICATIONS_TO_PROD", "notifications@rwxt.org")
        self.nonprod_recipients = os.environ.get(
            "NOTIFICATIONS_TO_NONPROD", "notifications@rwxt.org"
        )

        # Deduplication manager
        self.dedup_manager = get_dedup_manager()

    def register_handlers(self) -> None:
        """Register event handlers with the event bus."""
        # Subscribe to notification events
        self.event_bus.subscribe("ErrorNotificationRequested", self)
        self.event_bus.subscribe("TradingNotificationRequested", self)
        self.event_bus.subscribe("SystemNotificationRequested", self)

        self.logger.info("Registered notification event handlers")

    def handle_event(self, event: BaseEvent) -> None:
        """Handle notification events with idempotency guard.

        Args:
            event: The notification event to handle

        """
        # Idempotency check - skip if already processed
        if event.event_id in self._processed_events:
            self.logger.debug(
                f"Skipping duplicate event {event.event_type}",
                extra={
                    "event_id": event.event_id,
                    "correlation_id": event.correlation_id,
                    "causation_id": event.causation_id,
                },
            )
            return

        try:
            if isinstance(event, ErrorNotificationRequested):
                self._handle_error_notification(event)
            elif isinstance(event, TradingNotificationRequested):
                self._handle_trading_notification(event)
            elif isinstance(event, SystemNotificationRequested):
                self._handle_system_notification(event)
            elif isinstance(event, DataLakeNotificationRequested):
                self._handle_data_lake_notification(event)
            else:
                self.logger.debug(
                    f"NotificationService ignoring event type: {event.event_type}",
                    extra={
                        "event_id": event.event_id,
                        "correlation_id": event.correlation_id,
                    },
                )

            # Mark as processed after successful handling
            self._processed_events.add(event.event_id)

        except Exception as e:
            # Log errors but don't re-raise - notifications shouldn't break workflows
            self.logger.error(
                f"Notification service failed for {event.event_type}: {e}",
                exc_info=True,
                extra={
                    "event_id": event.event_id,
                    "correlation_id": event.correlation_id,
                    "causation_id": event.causation_id,
                    "error_type": type(e).__name__,
                },
            )

    def can_handle(self, event_type: str) -> bool:
        """Check if service can handle a specific event type.

        Args:
            event_type: The type of event to check

        Returns:
            True if this service can handle the event type

        """
        return event_type in [
            "ErrorNotificationRequested",
            "TradingNotificationRequested",
            "SystemNotificationRequested",
            "DataLakeNotificationRequested",
        ]

    def _log_event_context(self, event: BaseEvent, message: str, level: str = "info") -> None:
        """Log message with event context (correlation_id, causation_id).

        Args:
            event: Event providing context
            message: Log message
            level: Log level (info, error, warning, debug)

        """
        extra = {
            "event_id": event.event_id,
            "correlation_id": event.correlation_id,
            "causation_id": event.causation_id,
        }
        getattr(self.logger, level)(message, extra=extra)

    def _handle_error_notification(self, event: ErrorNotificationRequested) -> None:
        """Handle error notification event.

        Args:
            event: The error notification event

        """
        self._log_event_context(event, f"Processing error notification: {event.error_title}")

        # Extract error details for dedup
        error_details = {
            "exception_type": event.error_code or "Unknown",
            "exception_message": event.error_report,
        }

        # Check if we should send this failure email (dedup)
        component = "Daily Run"  # Default for now; can be extracted from event later
        failed_step = event.error_title  # Use title as failed step
        run_id = event.correlation_id

        should_send = self.dedup_manager.should_send_failure_email(
            component=component,
            env=self.stage,
            failed_step=failed_step,
            error_details=error_details,
            run_id=run_id,
        )

        if not should_send:
            self._log_event_context(
                event,
                "Failure email suppressed by deduplication",
                "info",
            )
            return

        try:
            # Build template context for failure email
            context = {
                "status": "FAILURE",
                "env": self.stage,
                "run_id": event.correlation_id,
                "correlation_id": event.correlation_id,
                "failed_step": failed_step,
                "impact": "Workflow did not complete successfully",
                "exception_type": event.error_code or "Unknown",
                "exception_message": event.error_report[:500],  # Truncate for email
                "stack_trace": event.error_report,
                "retry_attempts": 0,  # Not tracked yet
                "last_attempt_time_utc": event.timestamp.isoformat(),
                "last_successful_run_id": "N/A",
                "last_successful_run_time_utc": "N/A",
                "quick_actions": [
                    "Check CloudWatch Logs for detailed stack trace",
                    "Verify Alpaca API connectivity and credentials",
                    "Check market data freshness in S3",
                    "Review recent code changes",
                ],
                "logs_url": self._build_logs_url(event.correlation_id),
            }

            # Render templates
            html_body = render_daily_run_failure_html(context)
            text_body = render_daily_run_failure_text(context)

            # Build subject
            subject = format_subject(
                component=component,
                status="FAILURE",
                env=self.stage,
                run_id=run_id,
            )

            # Get recipient addresses
            to_addresses = self._get_recipients()

            # Send via SES
            result = send_email(
                to_addresses=to_addresses,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
            )

            if result.get("status") == "sent":
                self._log_event_context(
                    event,
                    f"Error notification sent via SES (message_id={result.get('message_id')})",
                )
            else:
                self._log_event_context(
                    event,
                    f"Failed to send error notification: {result.get('error')}",
                    "error",
                )

        except Exception as e:
            self._log_event_context(
                event,
                f"Failed to send error notification ({type(e).__name__}): {e}",
                "error",
            )

    def _handle_trading_notification(self, event: TradingNotificationRequested) -> None:
        """Handle trading notification event.

        Supports three outcomes: SUCCESS, PARTIAL_SUCCESS (non-fractionable skips only),
        and FAILURE (actual trade failures).

        Args:
            event: The trading notification event

        """
        self._log_event_context(
            event, f"Processing trading notification: success={event.trading_success}"
        )

        # Check for recovery (if this is a success after previous failures)
        if event.trading_success:
            recovery_info = self.dedup_manager.check_recovery(
                component="Daily Run",
                env=self.stage,
                run_id=event.correlation_id,
            )

            if recovery_info:
                self._send_recovery_email(recovery_info, event)

        # Build template context for success/failure email
        execution_data = event.execution_data or {}
        execution_summary = execution_data.get("execution_summary", {})

        # Check if this is a partial success (non-fractionable skips only)
        is_partial_success = execution_data.get("is_partial_success", False)
        non_fractionable_skipped = execution_data.get("non_fractionable_skipped_symbols", [])

        # Extract timing from execution_data (populated by TradeAggregator)
        start_time_utc = execution_data.get("start_time_utc", "")
        end_time_utc = execution_data.get("end_time_utc", "") or datetime.now(UTC).isoformat()

        # Calculate duration if both timestamps available
        duration_seconds = 0
        if start_time_utc and end_time_utc:
            try:
                from dateutil import parser as date_parser

                start_dt = date_parser.isoparse(start_time_utc)
                end_dt = date_parser.isoparse(end_time_utc)
                duration_seconds = int((end_dt - start_dt).total_seconds())
            except Exception as e:
                self.logger.warning(f"Failed to parse timing data: {e}")

        # Extract data freshness from execution_data (propagated from strategy workers)
        data_freshness_raw = execution_data.get("data_freshness", {})
        data_freshness = {
            "latest_timestamp": data_freshness_raw.get("latest_timestamp", "N/A"),
            "age_days": data_freshness_raw.get("age_days", 0),
            "gate_status": data_freshness_raw.get("gate_status", "PASS"),
        }

        # Determine status for template
        if is_partial_success:
            status = "PARTIAL_SUCCESS"
        elif event.trading_success:
            status = "SUCCESS"
        else:
            status = "FAILURE"

        context = {
            "status": status,
            "env": self.stage,
            "mode": event.trading_mode,
            "run_id": event.correlation_id,
            "start_time_utc": start_time_utc or "N/A",
            "end_time_utc": end_time_utc,
            "duration_seconds": duration_seconds,
            "symbols_evaluated": execution_summary.get("symbols_evaluated", 0),
            "eligible_signals_count": execution_summary.get("eligible_signals", 0),
            "blocked_by_risk_count": execution_summary.get("blocked_by_risk", 0),
            "orders_placed": event.orders_placed,
            "orders_filled": event.orders_succeeded,
            "orders_cancelled": 0,  # Not tracked yet
            "orders_rejected": event.orders_placed - event.orders_succeeded,
            # Portfolio snapshot from execution_data (fetched from Alpaca by TradeAggregator)
            "equity": execution_data.get("equity", 0),
            "cash": execution_data.get("cash", 0),
            "gross_exposure": execution_data.get("gross_exposure", 0),
            "net_exposure": execution_data.get("net_exposure", 0),
            "top_positions": execution_data.get("top_positions", []),
            "data_freshness": data_freshness,
            "warnings": [],
            "logs_url": self._build_logs_url(event.correlation_id),
            # Partial success specific
            "non_fractionable_skipped_symbols": non_fractionable_skipped,
        }

        try:
            # Render templates based on status
            if is_partial_success:
                # Partial success: non-fractionable skips only, rest succeeded
                html_body = render_daily_run_partial_success_html(context)
                text_body = render_daily_run_partial_success_text(context)
            elif event.trading_success:
                # Full success
                html_body = render_daily_run_success_html(context)
                text_body = render_daily_run_success_text(context)
            else:
                # Actual failures
                context.update(
                    {
                        "failed_step": "execution",
                        "impact": "Trades did not execute successfully",
                        "exception_type": event.error_code or "TradingFailure",
                        "exception_message": event.error_message or "Trading execution failed",
                        "stack_trace": event.error_message or "",
                        "retry_attempts": 0,
                        "last_attempt_time_utc": datetime.now(UTC).isoformat(),
                        "last_successful_run_id": "N/A",
                        "last_successful_run_time_utc": "N/A",
                        "quick_actions": [
                            "Check Alpaca account status and buying power",
                            "Verify market is open (Mon-Fri 9:30 AM - 4:00 PM ET)",
                            "Check for rejected orders in trade ledger",
                            "Review risk controls and position limits",
                        ],
                    }
                )
                html_body = render_daily_run_failure_html(context)
                text_body = render_daily_run_failure_text(context)

            # Build subject
            subject = format_subject(
                component="Daily Run",
                status=status,
                env=self.stage,
                run_id=event.correlation_id,
            )

            # Get recipient addresses
            to_addresses = self._get_recipients()

            # Send via SES
            result = send_email(
                to_addresses=to_addresses,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
            )

            if result.get("status") == "sent":
                self._log_event_context(
                    event,
                    f"Trading notification sent via SES (message_id={result.get('message_id')}, "
                    f"status={status}, partial_success={is_partial_success})",
                )
            else:
                self._log_event_context(
                    event,
                    f"Failed to send trading notification: {result.get('error')}",
                    "error",
                )

        except Exception as e:
            self._log_event_context(
                event,
                f"Failed to send trading notification ({type(e).__name__}): {e}",
                "error",
            )

    def _send_recovery_email(
        self, recovery_info: dict[str, Any], event: TradingNotificationRequested
    ) -> None:
        """Send RECOVERED email after previous failures cleared.

        Args:
            recovery_info: Recovery information from dedup manager
            event: The successful trading event that triggered recovery

        """
        self.logger.info(
            "Sending RECOVERED notification",
            extra={
                "correlation_id": event.correlation_id,
                "recovered_count": len(recovery_info.get("recovered_keys", [])),
            },
        )

        # Build simple recovery message (can be enhanced with template later)
        recovered_keys = recovery_info.get("recovered_keys", [])
        recovery_details = "\n".join(
            [
                f"• {key['dedup_key']}: {key['repeat_count']} occurrences from {key['first_seen_time']} to {key['last_seen_time']}"
                for key in recovered_keys
            ]
        )

        html_body = f"""
<!DOCTYPE html>
<html>
<body style="font-family: sans-serif; padding: 20px;">
    <h2 style="color: #17a2b8;">✅ System Recovered</h2>
    <p>Previous failures have been resolved in run <strong>{event.correlation_id}</strong>.</p>
    <h3>Recovered Failures:</h3>
    <ul>
        {"".join([f"<li>{key['dedup_key']}: {key['repeat_count']} occurrences</li>" for key in recovered_keys])}
    </ul>
    <p>The system is now operating normally.</p>
</body>
</html>
"""

        text_body = f"""
SYSTEM RECOVERED
================

Previous failures have been resolved in run {event.correlation_id}.

Recovered Failures:
{recovery_details}

The system is now operating normally.
"""

        subject = format_subject(
            component="Daily Run",
            status="RECOVERED",
            env=self.stage,
            run_id=event.correlation_id,
        )

        try:
            result = send_email(
                to_addresses=self._get_recipients(),
                subject=subject,
                html_body=html_body,
                text_body=text_body,
            )

            if result.get("status") == "sent":
                self.logger.info(
                    f"Recovery notification sent (message_id={result.get('message_id')})",
                    extra={"correlation_id": event.correlation_id},
                )
        except Exception as e:
            self.logger.error(
                f"Failed to send recovery notification: {e}",
                extra={"correlation_id": event.correlation_id},
            )

    def _handle_system_notification(self, event: SystemNotificationRequested) -> None:
        """Handle system notification event.

        Args:
            event: The system notification event

        """
        self._log_event_context(event, f"Processing system notification: {event.notification_type}")

        try:
            # Use text_content for plain text body
            text_body = event.text_content or "System notification (no content provided)"

            # Create simple HTML wrapper for text content
            html_body = f"""
<!DOCTYPE html>
<html>
<body style="font-family: sans-serif; padding: 20px;">
    <h2>System Notification</h2>
    <pre style="background-color: #f8f9fa; padding: 15px; border-radius: 4px;">{text_body}</pre>
</body>
</html>
"""

            result = send_email(
                to_addresses=self._get_recipients(),
                subject=event.subject,
                html_body=html_body,
                text_body=text_body,
            )

            if result.get("status") == "sent":
                self._log_event_context(
                    event,
                    f"System notification sent via SES (message_id={result.get('message_id')})",
                )
            else:
                self._log_event_context(
                    event,
                    f"Failed to send system notification: {result.get('error')}",
                    "error",
                )

        except Exception as e:
            self._log_event_context(
                event,
                f"Failed to send system notification ({type(e).__name__}): {e}",
                "error",
            )

    def _handle_data_lake_notification(self, event: DataLakeNotificationRequested) -> None:
        """Handle data lake notification event.

        Sends notification about market data refresh results.

        Args:
            event: The data lake notification event

        """
        context = event.data_lake_context
        self._log_event_context(
            event,
            f"Processing data lake notification: status={event.status}, "
            f"updated={context.get('symbols_updated_count', 0)}, "
            f"failed={context.get('symbols_failed_count', 0)}",
        )

        try:
            total_symbols = context.get("total_symbols", 0)
            updated_count = context.get("symbols_updated_count", 0)
            failed_count = context.get("symbols_failed_count", 0)
            duration_seconds = context.get("duration_seconds", 0)
            failed_symbols = context.get("failed_symbols", [])

            # Format duration
            if duration_seconds >= 60:
                duration_str = f"{duration_seconds // 60}m {duration_seconds % 60}s"
            else:
                duration_str = f"{duration_seconds}s"

            # Determine status emoji and color
            if event.status == "SUCCESS":
                status_emoji = "✅"
                status_color = "#28a745"
            elif event.status == "SUCCESS_WITH_WARNINGS":
                status_emoji = "⚠️"
                status_color = "#ffc107"
            else:
                status_emoji = "❌"
                status_color = "#dc3545"

            # Build failed symbols list (if any)
            failed_list_html = ""
            failed_list_text = ""
            if failed_symbols:
                failed_list_html = (
                    "<h4>Failed Symbols:</h4><ul>"
                    + "".join([f"<li>{sym}</li>" for sym in failed_symbols[:20]])
                    + ("</ul><p><em>...and more</em></p>" if len(failed_symbols) > 20 else "</ul>")
                )
                failed_list_text = (
                    "\nFailed Symbols:\n"
                    + "\n".join([f"  - {sym}" for sym in failed_symbols[:20]])
                    + ("\n  ...and more" if len(failed_symbols) > 20 else "")
                )

            html_body = f"""
<!DOCTYPE html>
<html>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; padding: 20px; max-width: 600px;">
    <h2 style="color: {status_color};">{status_emoji} Data Lake Refresh {event.status}</h2>

    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
        <tr style="background-color: #f8f9fa;">
            <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>Environment</strong></td>
            <td style="padding: 10px; border: 1px solid #dee2e6;">{self.stage}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>Total Symbols</strong></td>
            <td style="padding: 10px; border: 1px solid #dee2e6;">{total_symbols}</td>
        </tr>
        <tr style="background-color: #f8f9fa;">
            <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>Updated</strong></td>
            <td style="padding: 10px; border: 1px solid #dee2e6; color: #28a745;">{updated_count}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>Failed</strong></td>
            <td style="padding: 10px; border: 1px solid #dee2e6; color: {'#dc3545' if failed_count > 0 else '#28a745'};">{failed_count}</td>
        </tr>
        <tr style="background-color: #f8f9fa;">
            <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>Duration</strong></td>
            <td style="padding: 10px; border: 1px solid #dee2e6;">{duration_str}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>Correlation ID</strong></td>
            <td style="padding: 10px; border: 1px solid #dee2e6; font-family: monospace; font-size: 12px;">{event.correlation_id}</td>
        </tr>
    </table>

    {failed_list_html}

    <p style="color: #6c757d; font-size: 12px; margin-top: 30px;">
        This notification was sent by The Alchemiser data refresh service.
    </p>
</body>
</html>
"""

            text_body = f"""
DATA LAKE REFRESH {event.status}
{'=' * 40}

Environment: {self.stage}
Total Symbols: {total_symbols}
Updated: {updated_count}
Failed: {failed_count}
Duration: {duration_str}
Correlation ID: {event.correlation_id}
{failed_list_text}
"""

            subject = f"[{self.stage.upper()}] {status_emoji} Data Lake Refresh {event.status}"

            result = send_email(
                to_addresses=self._get_recipients(),
                subject=subject,
                html_body=html_body,
                text_body=text_body,
            )

            if result.get("status") == "sent":
                self._log_event_context(
                    event,
                    f"Data lake notification sent via SES (message_id={result.get('message_id')})",
                )
            else:
                self._log_event_context(
                    event,
                    f"Failed to send data lake notification: {result.get('error')}",
                    "error",
                )

        except Exception as e:
            self._log_event_context(
                event,
                f"Failed to send data lake notification ({type(e).__name__}): {e}",
                "error",
            )

    def _get_recipients(self) -> list[str]:
        """Get recipient email addresses based on environment.

        Returns:
            List of recipient email addresses

        """
        if self.stage == "prod":
            return [addr.strip() for addr in self.prod_recipients.split(",")]
        return [addr.strip() for addr in self.nonprod_recipients.split(",")]

    def _build_logs_url(self, correlation_id: str) -> str:
        """Build CloudWatch Logs Insights URL filtered by correlation ID.

        Args:
            correlation_id: Correlation ID for filtering

        Returns:
            CloudWatch Logs URL

        """
        region = os.environ.get("AWS_REGION", "us-east-1")
        # TODO: Implement complete URL builder with correlation_id filter, proper timestamp range,
        # and URL encoding for production use. Current placeholder URL doesn't include query parameters.
        return (
            f"https://console.aws.amazon.com/cloudwatch/home?region={region}#logsV2:logs-insights"
        )
