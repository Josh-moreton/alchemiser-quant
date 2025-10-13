"""Business Unit: notifications | Status: current.

Notification service for event-driven email handling.

This service consumes notification events and sends appropriate emails using
the existing email infrastructure from shared.notifications.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer

from the_alchemiser.shared.events.base import BaseEvent
from the_alchemiser.shared.events.schemas import (
    ErrorNotificationRequested,
    SystemNotificationRequested,
    TradingNotificationRequested,
)
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.notifications.client import send_email_notification
from the_alchemiser.shared.notifications.templates import (
    EmailTemplates,
)
from the_alchemiser.shared.notifications.templates.multi_strategy import (
    MultiStrategyReportBuilder,
)


class _ExecutionResultAdapter:
    """Adapter to convert TradingNotificationRequested event to template-compatible result.

    This adapter provides a stable interface for email template generation
    without using dynamic attribute access or Any types.
    """

    def __init__(self, event: TradingNotificationRequested) -> None:
        """Initialize adapter with event data.

        Args:
            event: Trading notification event to adapt

        """
        self.success = True
        self.orders_executed: list[dict[str, object]] = []
        self.strategy_signals: dict[str, dict[str, object]] = {}
        self.correlation_id = event.correlation_id
        self._execution_data = event.execution_data

    def get_execution_data(self, key: str) -> object:
        """Get execution data by key.

        Args:
            key: Data key to retrieve

        Returns:
            Value from execution data or None if not found

        """
        return self._execution_data.get(key, None) if self._execution_data else None


class NotificationService:
    """Event-driven notification service.

    Consumes notification events and sends appropriate emails using existing
    email infrastructure. Designed to be deployable as independent Lambda.
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
            # Don't mark as processed on failure to allow retry
            # Log error but don't re-raise (silent failure for notification service)
            self.logger.error(
                f"Notification service failed to handle event {event.event_type}: {e}",
                extra={
                    "event_id": event.event_id,
                    "correlation_id": event.correlation_id,
                    "causation_id": event.causation_id,
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
        self._log_event_context(event, f"Sending error notification: {event.error_title}")

        try:
            # Build HTML email content using existing templates
            html_content = EmailTemplates.build_error_report(
                title=f"{event.error_severity} Alert - Trading System Errors",
                error_message=event.error_report,
            )

            # Build subject with error code if available
            if event.error_code:
                subject = f"[FAILURE][{event.error_priority}][{event.error_code}] The Alchemiser - {event.error_severity} Error Report"
            else:
                subject = f"[FAILURE][{event.error_priority}] The Alchemiser - {event.error_severity} Error Report"

            # Send notification
            success = send_email_notification(
                subject=subject,
                html_content=html_content,
                text_content=event.error_report,
                recipient_email=event.recipient_override,
            )

            if success:
                self._log_event_context(event, "Error notification email sent successfully")
            else:
                self._log_event_context(event, "Failed to send error notification email", "error")

        except Exception as e:
            self._log_event_context(event, f"Failed to send error notification: {e}", "error")

    def _handle_trading_notification(self, event: TradingNotificationRequested) -> None:
        """Handle trading notification event.

        Args:
            event: The trading notification event

        """
        self._log_event_context(
            event, f"Sending trading notification: success={event.trading_success}"
        )

        try:
            # Build email content based on success/failure
            if event.trading_success:
                html_content = self._build_success_trading_email(event)
            else:
                html_content = self._build_failure_trading_email(event)

            # Build subject line
            subject = self._build_trading_subject(event)

            # Send notification
            success = send_email_notification(
                subject=subject,
                html_content=html_content,
                text_content=f"Trading execution completed. Success: {event.trading_success}",
                recipient_email=event.recipient_override,
            )

            if success:
                self._log_event_context(
                    event,
                    f"Trading notification sent successfully (success={event.trading_success})",
                )
            else:
                self._log_event_context(event, "Failed to send trading notification email", "error")

        except Exception as e:
            self._log_event_context(event, f"Failed to send trading notification: {e}", "error")

    def _build_success_trading_email(self, event: TradingNotificationRequested) -> str:
        """Build HTML content for successful trading notification.

        Args:
            event: Trading notification event

        Returns:
            HTML content for email

        """
        try:
            # Create adapter for template
            result_adapter = _ExecutionResultAdapter(event)
            return MultiStrategyReportBuilder.build_multi_strategy_report_neutral(
                result_adapter,
                event.trading_mode,
            )
        except Exception as template_error:
            # Fallback to basic template if enhanced template fails
            self.logger.warning(
                f"Enhanced template failed, using basic: {template_error}",
                extra={
                    "event_id": event.event_id,
                    "correlation_id": event.correlation_id,
                },
            )
            return self._build_basic_trading_email(event)

    def _build_basic_trading_email(self, event: TradingNotificationRequested) -> str:
        """Build basic HTML fallback for trading notification.

        Args:
            event: Trading notification event

        Returns:
            Basic HTML content

        """
        return f"""
        <h2>Trading Execution Report - {event.trading_mode.upper()}</h2>
        <p><strong>Status:</strong> Success</p>
        <p><strong>Orders Placed:</strong> {event.orders_placed}</p>
        <p><strong>Orders Succeeded:</strong> {event.orders_succeeded}</p>
        <p><strong>Total Trade Value:</strong> ${event.total_trade_value:,.2f}</p>
        <p><strong>Correlation ID:</strong> {event.correlation_id}</p>
        <p><strong>Timestamp:</strong> {event.timestamp}</p>
        """

    def _build_failure_trading_email(self, event: TradingNotificationRequested) -> str:
        """Build HTML content for failed trading notification.

        Args:
            event: Trading notification event

        Returns:
            HTML content for email

        """
        error_message = event.error_message or "Unknown trading error"

        # Build context information for the failure email
        context: dict[str, object] = {
            "Orders Placed": event.orders_placed,
            "Orders Succeeded": event.orders_succeeded,
            "Correlation ID": event.correlation_id,
        }

        # Add failed symbols if available in execution data
        if event.execution_data and event.execution_data.get("failed_symbols"):
            context["Failed Symbols"] = ", ".join(event.execution_data["failed_symbols"])

        return EmailTemplates.failed_trading_run(
            error_details=error_message,
            mode=event.trading_mode,
            context=context,
        )

    def _build_trading_subject(self, event: TradingNotificationRequested) -> str:
        """Build email subject for trading notification.

        Args:
            event: Trading notification event

        Returns:
            Email subject line

        """
        status_tag = "SUCCESS" if event.trading_success else "FAILURE"
        if not event.trading_success and event.error_code:
            return f"[{status_tag}][{event.error_code}] The Alchemiser - {event.trading_mode.upper()} Trading Report"
        return f"[{status_tag}] The Alchemiser - {event.trading_mode.upper()} Trading Report"

    def _handle_system_notification(self, event: SystemNotificationRequested) -> None:
        """Handle system notification event.

        Args:
            event: The system notification event

        """
        self._log_event_context(event, f"Sending system notification: {event.notification_type}")

        try:
            # Send notification with provided content
            success = send_email_notification(
                subject=event.subject,
                html_content=event.html_content,
                text_content=event.text_content,
                recipient_email=event.recipient_override,
            )

            if success:
                self._log_event_context(event, "System notification email sent successfully")
            else:
                self._log_event_context(event, "Failed to send system notification email", "error")

        except Exception as e:
            self._log_event_context(event, f"Failed to send system notification: {e}", "error")
