"""Business Unit: notifications | Status: current.

Notification service for event-driven email handling.

This service consumes notification events and sends appropriate emails using
the existing email infrastructure from shared.notifications.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

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
    build_error_email_html,
)
from the_alchemiser.shared.notifications.templates.multi_strategy import (
    MultiStrategyReportBuilder,
)


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

    def register_handlers(self) -> None:
        """Register event handlers with the event bus."""
        # Subscribe to notification events
        self.event_bus.subscribe("ErrorNotificationRequested", self)
        self.event_bus.subscribe("TradingNotificationRequested", self)
        self.event_bus.subscribe("SystemNotificationRequested", self)

        self.logger.info("Registered notification event handlers")

    def handle_event(self, event: BaseEvent) -> None:
        """Handle notification events.

        Args:
            event: The notification event to handle

        """
        try:
            if isinstance(event, ErrorNotificationRequested):
                self._handle_error_notification(event)
            elif isinstance(event, TradingNotificationRequested):
                self._handle_trading_notification(event)
            elif isinstance(event, SystemNotificationRequested):
                self._handle_system_notification(event)
            else:
                self.logger.debug(f"NotificationService ignoring event type: {event.event_type}")

        except Exception as e:
            self.logger.error(
                f"Notification service failed to handle event {event.event_type}: {e}",
                extra={
                    "event_id": event.event_id,
                    "correlation_id": event.correlation_id,
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

    def _handle_error_notification(self, event: ErrorNotificationRequested) -> None:
        """Handle error notification event.

        Args:
            event: The error notification event

        """
        self.logger.info(f"Sending error notification: {event.error_title}")

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
                self.logger.info("Error notification email sent successfully")
            else:
                self.logger.error("Failed to send error notification email")

        except Exception as e:
            self.logger.error(f"Failed to send error notification: {e}")

    def _handle_trading_notification(self, event: TradingNotificationRequested) -> None:
        """Handle trading notification event.

        Args:
            event: The trading notification event

        """
        self.logger.info(f"Sending trading notification: success={event.trading_success}")

        try:
            if event.trading_success:
                # Use enhanced successful trading run template
                try:
                    # Create a result adapter for the enhanced template
                    class EventResultAdapter:
                        def __init__(self, event_data: TradingNotificationRequested) -> None:
                            self.success = True
                            self.orders_executed: list[
                                Any
                            ] = []  # Event data doesn't have detailed order info
                            self.strategy_signals: dict[
                                str, Any
                            ] = {}  # Event data doesn't have signal details
                            self.correlation_id = event_data.correlation_id
                            # Add execution data for template access
                            self._execution_data = event_data.execution_data

                        def __getattr__(self, name: str) -> object:
                            # Allow template to access any field from execution_data
                            return self._execution_data.get(name, None)

                    result_adapter = EventResultAdapter(event)
                    html_content = MultiStrategyReportBuilder.build_multi_strategy_report_neutral(
                        result_adapter,
                        event.trading_mode,
                    )
                except Exception as template_error:
                    # Fallback to basic template if enhanced template fails
                    self.logger.warning(f"Enhanced template failed, using basic: {template_error}")
                    html_content = f"""
                    <h2>Trading Execution Report - {event.trading_mode.upper()}</h2>
                    <p><strong>Status:</strong> Success</p>
                    <p><strong>Orders Placed:</strong> {event.orders_placed}</p>
                    <p><strong>Orders Succeeded:</strong> {event.orders_succeeded}</p>
                    <p><strong>Total Trade Value:</strong> ${event.total_trade_value:,.2f}</p>
                    <p><strong>Correlation ID:</strong> {event.correlation_id}</p>
                    <p><strong>Timestamp:</strong> {event.timestamp}</p>
                    """
            else:
                # Use error template for failed trading
                error_message = event.error_message or "Unknown trading error"
                html_content = build_error_email_html(
                    "Trading Execution Failed",
                    f"Trading workflow failed: {error_message}",
                )

            # Build subject
            status_tag = "SUCCESS" if event.trading_success else "FAILURE"
            if not event.trading_success and event.error_code:
                subject = f"[{status_tag}][{event.error_code}] The Alchemiser - {event.trading_mode.upper()} Trading Report"
            else:
                subject = (
                    f"[{status_tag}] The Alchemiser - {event.trading_mode.upper()} Trading Report"
                )

            # Send notification
            success = send_email_notification(
                subject=subject,
                html_content=html_content,
                text_content=f"Trading execution completed. Success: {event.trading_success}",
                recipient_email=event.recipient_override,
            )

            if success:
                self.logger.info(
                    f"Trading notification sent successfully (success={event.trading_success})"
                )
            else:
                self.logger.error("Failed to send trading notification email")

        except Exception as e:
            self.logger.error(f"Failed to send trading notification: {e}")

    def _handle_system_notification(self, event: SystemNotificationRequested) -> None:
        """Handle system notification event.

        Args:
            event: The system notification event

        """
        self.logger.info(f"Sending system notification: {event.notification_type}")

        try:
            # Send notification with provided content
            success = send_email_notification(
                subject=event.subject,
                html_content=event.html_content,
                text_content=event.text_content,
                recipient_email=event.recipient_override,
            )

            if success:
                self.logger.info("System notification email sent successfully")
            else:
                self.logger.error("Failed to send system notification email")

        except Exception as e:
            self.logger.error(f"Failed to send system notification: {e}")
