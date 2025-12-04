"""Business Unit: notifications | Status: current.

Notification service for event-driven notifications via SNS.

This service consumes notification events and publishes to SNS for email delivery.
SNS handles the actual email sending via subscribed email addresses.
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
from the_alchemiser.shared.notifications.sns_publisher import publish_notification


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
            # Build subject with error code if available
            if event.error_code:
                subject = f"[FAILURE][{event.error_priority}][{event.error_code}] Alchemiser Error"
            else:
                subject = f"[FAILURE][{event.error_priority}] Alchemiser Error"

            # Build plain text message for SNS
            message = self._build_error_message(event)

            # Publish to SNS
            success = publish_notification(subject=subject, message=message)

            if success:
                self._log_event_context(event, "Error notification published to SNS")
            else:
                self._log_event_context(event, "Failed to publish error notification", "error")

        except Exception as e:
            self._log_event_context(
                event,
                f"Failed to send error notification ({type(e).__name__}): {e}",
                "error",
            )

    def _handle_trading_notification(self, event: TradingNotificationRequested) -> None:
        """Handle trading notification event.

        Args:
            event: The trading notification event

        """
        self._log_event_context(
            event, f"Sending trading notification: success={event.trading_success}"
        )

        try:
            # Build subject line
            subject = self._build_trading_subject(event)

            # Build plain text message for SNS
            message = self._build_trading_message(event)

            # Publish to SNS
            success = publish_notification(subject=subject, message=message)

            if success:
                self._log_event_context(
                    event,
                    f"Trading notification published to SNS (success={event.trading_success})",
                )
            else:
                self._log_event_context(event, "Failed to publish trading notification", "error")

        except Exception as e:
            self._log_event_context(
                event,
                f"Failed to send trading notification ({type(e).__name__}): {e}",
                "error",
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
            return f"[{status_tag}][{event.error_code}] Alchemiser {event.trading_mode.upper()}"
        return f"[{status_tag}] Alchemiser {event.trading_mode.upper()} Trading"

    def _build_trading_message(self, event: TradingNotificationRequested) -> str:
        """Build plain text message for trading notification.

        Args:
            event: Trading notification event

        Returns:
            Plain text message for SNS

        """
        status = "SUCCESS" if event.trading_success else "FAILURE"
        lines = [
            "THE ALCHEMISER - TRADING REPORT",
            "=" * 40,
            "",
            f"Status: {status}",
            f"Mode: {event.trading_mode.upper()}",
            f"Orders Placed: {event.orders_placed}",
            f"Orders Succeeded: {event.orders_succeeded}",
            f"Total Trade Value: ${event.total_trade_value:,.2f}",
            "",
            f"Correlation ID: {event.correlation_id}",
            f"Timestamp: {event.timestamp}",
        ]

        if not event.trading_success and event.error_message:
            lines.extend(["", "Error Details:", event.error_message])

        return "\n".join(lines)

    def _build_error_message(self, event: ErrorNotificationRequested) -> str:
        """Build plain text message for error notification.

        Args:
            event: Error notification event

        Returns:
            Plain text message for SNS

        """
        lines = [
            "THE ALCHEMISER - ERROR REPORT",
            "=" * 40,
            "",
            f"Severity: {event.error_severity}",
            f"Priority: {event.error_priority}",
            f"Title: {event.error_title}",
            "",
            "Details:",
            "-" * 40,
            event.error_report,
            "-" * 40,
            "",
            f"Correlation ID: {event.correlation_id}",
            f"Timestamp: {event.timestamp}",
        ]

        if event.error_code:
            lines.insert(4, f"Error Code: {event.error_code}")

        return "\n".join(lines)

    def _handle_system_notification(self, event: SystemNotificationRequested) -> None:
        """Handle system notification event.

        Args:
            event: The system notification event

        """
        self._log_event_context(event, f"Sending system notification: {event.notification_type}")

        try:
            # Use text_content for SNS (plain text only)
            message = event.text_content or "System notification (no content provided)"

            success = publish_notification(subject=event.subject, message=message)

            if success:
                self._log_event_context(event, "System notification published to SNS")
            else:
                self._log_event_context(event, "Failed to publish system notification", "error")

        except Exception as e:
            self._log_event_context(
                event,
                f"Failed to send system notification ({type(e).__name__}): {e}",
                "error",
            )
