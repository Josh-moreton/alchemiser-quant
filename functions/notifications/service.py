"""Business Unit: notifications | Status: current.

Notification service for event-driven notifications via SES.

This service consumes notification events and sends templated HTML + plain text emails
via Amazon SES.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from urllib.parse import quote

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer

from the_alchemiser.shared.events.base import BaseEvent
from the_alchemiser.shared.events.schemas import (
    DataLakeNotificationRequested,
    ErrorNotificationRequested,
    ScheduleNotificationRequested,
    SystemNotificationRequested,
    TradingNotificationRequested,
)
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.notifications.ses_publisher import send_email
from the_alchemiser.shared.notifications.templates import (
    format_subject,
    render_daily_run_failure_html,
    render_daily_run_failure_text,
    render_daily_run_partial_success_html,
    render_daily_run_partial_success_text,
    render_daily_run_success_html,
    render_daily_run_success_text,
    render_html_footer,
    render_html_header,
    render_schedule_created_html,
    render_schedule_created_text,
    render_text_footer,
    render_text_header,
)


class NotificationService:
    """Event-driven notification service using Amazon SES.

    Consumes notification events and sends appropriate emails using SES
    with HTML + plain text templates.
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
        # Single notification email - set per-environment via CI/CD
        self.notification_email = os.environ.get("NOTIFICATION_EMAIL", "notifications@rwxt.org")

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
            elif isinstance(event, ScheduleNotificationRequested):
                self._handle_schedule_notification(event)
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
            "ScheduleNotificationRequested",
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

        component = "your daily rebalance summary"
        failed_step = event.error_title
        run_id = event.correlation_id

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

        # Extract P&L metrics from execution_data (fetched by TradeAggregator)
        pnl_metrics_raw = execution_data.get("pnl_metrics", {})
        monthly_pnl = pnl_metrics_raw.get("monthly_pnl", {})
        yearly_pnl = pnl_metrics_raw.get("yearly_pnl", {})

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
            # P&L metrics (from Alpaca via TradeAggregator)
            "monthly_pnl": monthly_pnl,
            "yearly_pnl": yearly_pnl,
            "warnings": [],
            "logs_url": self._build_logs_url(event.correlation_id),
            # Partial success specific
            "non_fractionable_skipped_symbols": non_fractionable_skipped,
            # Strategy evaluation metadata
            "strategies_evaluated": execution_data.get("strategies_evaluated", 0),
            # Rebalance plan summary for display
            "rebalance_plan_summary": execution_data.get("rebalance_plan_summary", []),
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
                component="your daily rebalance summary",
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

            # Determine status for display
            if event.status == "SUCCESS":
                display_status = "SUCCESS"
                status_color = "#28a745"
            elif event.status == "SUCCESS_WITH_WARNINGS":
                display_status = "SUCCESS_WITH_WARNINGS"
                status_color = "#ffc107"
            else:
                display_status = "FAILURE"
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

            # Build HTML body with header and footer
            header = render_html_header("Data Lake Refresh", display_status)
            footer = render_html_footer()

            html_content = f"""
    <h3 style="color: #333; margin: 20px 0 15px 0; font-size: 16px;">Refresh Results</h3>

    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
        <tr style="background-color: #f8f9fa;">
            <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>Total Symbols</strong></td>
            <td style="padding: 10px; border: 1px solid #dee2e6;">{total_symbols}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>Updated</strong></td>
            <td style="padding: 10px; border: 1px solid #dee2e6; color: #28a745;">{updated_count}</td>
        </tr>
        <tr style="background-color: #f8f9fa;">
            <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>Failed</strong></td>
            <td style="padding: 10px; border: 1px solid #dee2e6; color: {"#dc3545" if failed_count > 0 else "#28a745"};">{failed_count}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>Duration</strong></td>
            <td style="padding: 10px; border: 1px solid #dee2e6;">{duration_str}</td>
        </tr>
        <tr style="background-color: #f8f9fa;">
            <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>Data Source</strong></td>
            <td style="padding: 10px; border: 1px solid #dee2e6;">{context.get("data_source", "alpaca_api")}</td>
        </tr>
        <tr>
            <td style="padding: 10px; border: 1px solid #dee2e6;"><strong>Correlation ID</strong></td>
            <td style="padding: 10px; border: 1px solid #dee2e6; font-family: monospace; font-size: 12px;">{event.correlation_id}</td>
        </tr>
    </table>

    {failed_list_html}
"""

            html_body = header + html_content + footer

            # Build plain text body with header and footer
            text_header = render_text_header("Data Lake Refresh", display_status)
            text_footer = render_text_footer()

            text_content = f"""
Refresh Results
{"=" * 50}

Total Symbols: {total_symbols}
Updated: {updated_count}
Failed: {failed_count}
Duration: {duration_str}
Data Source: {context.get("data_source", "alpaca_api")}
Correlation ID: {event.correlation_id}
{failed_list_text}
"""

            text_body = text_header + text_content + text_footer

            subject = format_subject(
                "Data Lake Refresh", event.status, self.stage, event.correlation_id[:6]
            )

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

    def _handle_schedule_notification(self, event: ScheduleNotificationRequested) -> None:
        """Handle schedule notification event.

        Sends notification about schedule creation, early close, or holiday skip.

        Args:
            event: The schedule notification event

        """
        context = event.schedule_context
        status = context.get("status", "scheduled")
        self._log_event_context(
            event,
            f"Processing schedule notification: status={status}, "
            f"date={context.get('date', 'unknown')}, "
            f"is_early_close={context.get('is_early_close', False)}",
        )

        try:
            # Add environment to context if not already present
            context["env"] = context.get("env", self.stage)

            # Render templates
            html_body = render_schedule_created_html(context)
            text_body = render_schedule_created_text(context)

            # Determine subject based on status
            if status == "skipped_holiday":
                component = "schedule skip"
                display_status = "MARKET CLOSED"
            elif status == "early_close":
                component = "schedule set"
                display_status = "EARLY CLOSE"
            else:
                component = "schedule set"
                display_status = "SCHEDULED"

            subject = format_subject(
                component=component,
                status=display_status,
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
                    f"Schedule notification sent via SES (message_id={result.get('message_id')}, "
                    f"status={status})",
                )
            else:
                self._log_event_context(
                    event,
                    f"Failed to send schedule notification: {result.get('error')}",
                    "error",
                )

        except Exception as e:
            self._log_event_context(
                event,
                f"Failed to send schedule notification ({type(e).__name__}): {e}",
                "error",
            )

    def _get_recipients(self) -> list[str]:
        """Get recipient email addresses.

        Returns:
            List of recipient email addresses (from NOTIFICATION_EMAIL env var)

        """
        return [addr.strip() for addr in self.notification_email.split(",")]

    def _build_logs_url(self, correlation_id: str) -> str:
        """Build CloudWatch Logs Insights URL filtered by correlation ID.

        Args:
            correlation_id: Correlation ID for filtering

        Returns:
            CloudWatch Logs URL with query parameters for filtering

        """
        region = os.environ.get("AWS_REGION", "us-east-1")
        stack_name = os.environ.get("STACK_NAME", f"alchemiser-{self.stage}")

        # Prefer configuration via LAMBDA_LOG_SUFFIXES to avoid tight coupling to template.yaml.
        # Fallback to the current default list to preserve existing behaviour.
        configured_suffixes = os.environ.get("LAMBDA_LOG_SUFFIXES", "")
        if configured_suffixes.strip():
            lambda_suffixes = [
                suffix.strip() for suffix in configured_suffixes.split(",") if suffix.strip()
            ]
        else:
            lambda_suffixes = [
                "strategy-orchestrator",
                "strategy-worker",
                "signal-aggregator",
                "portfolio",
                "execution",
                "trade-aggregator",
                "notifications",
            ]
        log_groups = [f"/aws/lambda/{stack_name}-{suffix}" for suffix in lambda_suffixes]

        # Build the Logs Insights query to filter by correlation_id
        query = f'fields @timestamp, @message | filter @message like "{correlation_id}" | sort @timestamp desc | limit 200'

        # URL-encode the query for the CloudWatch console
        encoded_query = quote(query, safe="")

        # Build source log groups parameter (CloudWatch uses ~'loggroup' format)
        source_groups = "~".join([f"'{lg}'" for lg in log_groups])

        # CloudWatch Logs Insights URL format uses a special encoding:
        # The hash fragment contains query details with ~ as field separator
        # Time range: last 3 hours (relative) to capture full workflow execution
        return (
            f"https://{region}.console.aws.amazon.com/cloudwatch/home?region={region}"
            f"#logsV2:logs-insights$3FqueryDetail$3D~("
            f"end~0"  # 0 = now (relative time)
            f"~start~-10800"  # -10800 = 3 hours ago in seconds
            f"~timeType~'RELATIVE'"
            f"~unit~'seconds'"
            f"~editorString~{encoded_query}"
            f"~source~({source_groups})"
            f")"
        )
