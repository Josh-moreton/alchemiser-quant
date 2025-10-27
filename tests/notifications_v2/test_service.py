"""Business Unit: notifications | Status: current.

Tests for NotificationService event-driven email handling.

Covers service behaviors including:
- Event registration and routing
- Error notification handling
- Trading notification handling (success and failure)
- System notification handling
- Missing/partial data scenarios
- Error conditions and logging

Tests are deterministic and hermetic - no network calls.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import Mock, patch

import pytest

from the_alchemiser.notifications_v2.service import NotificationService
from the_alchemiser.shared.events.base import BaseEvent
from the_alchemiser.shared.events.schemas import (
    ErrorNotificationRequested,
    SystemNotificationRequested,
    TradingNotificationRequested,
)


class TestNotificationServiceInit:
    """Test NotificationService initialization and registration."""

    @pytest.fixture
    def mock_container(self) -> Mock:
        """Create a mock ApplicationContainer."""
        container = Mock()
        mock_event_bus = Mock()
        container.services.event_bus.return_value = mock_event_bus
        return container

    def test_service_initialization(self, mock_container: Mock) -> None:
        """Test service initializes with container and logger."""
        service = NotificationService(mock_container)

        assert service.container is mock_container
        assert service.logger is not None
        assert service.event_bus is not None

    def test_register_handlers(self, mock_container: Mock) -> None:
        """Test event handlers are registered with event bus."""
        service = NotificationService(mock_container)
        mock_event_bus = mock_container.services.event_bus.return_value

        service.register_handlers()

        # Verify all three event types are subscribed
        assert mock_event_bus.subscribe.call_count == 3
        call_args = [call.args for call in mock_event_bus.subscribe.call_args_list]

        assert ("ErrorNotificationRequested", service) in call_args
        assert ("TradingNotificationRequested", service) in call_args
        assert ("SystemNotificationRequested", service) in call_args

    def test_can_handle_supported_events(self, mock_container: Mock) -> None:
        """Test can_handle returns True for supported event types."""
        service = NotificationService(mock_container)

        assert service.can_handle("ErrorNotificationRequested") is True
        assert service.can_handle("TradingNotificationRequested") is True
        assert service.can_handle("SystemNotificationRequested") is True

    def test_can_handle_unsupported_events(self, mock_container: Mock) -> None:
        """Test can_handle returns False for unsupported event types."""
        service = NotificationService(mock_container)

        assert service.can_handle("UnknownEvent") is False
        assert service.can_handle("SignalGenerated") is False
        assert service.can_handle("RebalancePlanned") is False


class TestErrorNotificationHandling:
    """Test error notification handling behaviors."""

    @pytest.fixture
    def mock_container(self) -> Mock:
        """Create a mock ApplicationContainer."""
        container = Mock()
        mock_event_bus = Mock()
        container.services.event_bus.return_value = mock_event_bus
        return container

    @pytest.fixture
    def error_event(self) -> ErrorNotificationRequested:
        """Create a sample error notification event."""
        return ErrorNotificationRequested(
            event_id=f"event-{uuid.uuid4()}",
            correlation_id=f"corr-{uuid.uuid4()}",
            causation_id=f"cause-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="test_service",
            error_severity="CRITICAL",
            error_priority="URGENT",
            error_title="Trading System Failure",
            error_report="Critical error in execution module: Order placement failed",
            error_code="EXEC-001",
            recipient_override=None,
        )

    @patch("the_alchemiser.notifications_v2.service.send_email_notification")
    def test_handle_error_notification_success(
        self,
        mock_send_email: Mock,
        mock_container: Mock,
        error_event: ErrorNotificationRequested,
    ) -> None:
        """Test successful error notification handling."""
        mock_send_email.return_value = True
        service = NotificationService(mock_container)

        service.handle_event(error_event)

        # Verify email was sent with correct parameters
        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args

        assert "FAILURE" in call_args.kwargs["subject"]
        assert "URGENT" in call_args.kwargs["subject"]
        assert "EXEC-001" in call_args.kwargs["subject"]
        assert "CRITICAL" in call_args.kwargs["subject"]
        assert call_args.kwargs["text_content"] == error_event.error_report
        assert call_args.kwargs["recipient_email"] is None

    @patch("the_alchemiser.notifications_v2.service.send_email_notification")
    def test_handle_error_notification_without_code(
        self,
        mock_send_email: Mock,
        mock_container: Mock,
    ) -> None:
        """Test error notification without error code."""
        mock_send_email.return_value = True
        service = NotificationService(mock_container)

        event = ErrorNotificationRequested(
            event_id=f"event-{uuid.uuid4()}",
            correlation_id=f"corr-{uuid.uuid4()}",
            causation_id=f"cause-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="test_service",
            error_severity="HIGH",
            error_priority="HIGH",
            error_title="Data Validation Error",
            error_report="Invalid data format detected",
            error_code=None,  # No error code
        )

        service.handle_event(event)

        # Verify email was sent without error code in subject
        mock_send_email.assert_called_once()
        subject = mock_send_email.call_args.kwargs["subject"]
        assert "[FAILURE][HIGH]" in subject
        assert "EXEC-001" not in subject

    @patch("the_alchemiser.notifications_v2.service.send_email_notification")
    def test_handle_error_notification_with_recipient_override(
        self,
        mock_send_email: Mock,
        mock_container: Mock,
    ) -> None:
        """Test error notification with recipient override."""
        mock_send_email.return_value = True
        service = NotificationService(mock_container)

        # Create event with recipient override directly
        error_event = ErrorNotificationRequested(
            event_id=f"event-{uuid.uuid4()}",
            correlation_id=f"corr-{uuid.uuid4()}",
            causation_id=f"cause-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="test_service",
            error_severity="CRITICAL",
            error_priority="URGENT",
            error_title="Trading System Failure",
            error_report="Critical error in execution module: Order placement failed",
            error_code="EXEC-001",
            recipient_override="custom@example.com",
        )

        service.handle_event(error_event)

        # Verify recipient override is used
        call_args = mock_send_email.call_args
        assert call_args.kwargs["recipient_email"] == "custom@example.com"

    @patch("the_alchemiser.notifications_v2.service.send_email_notification")
    def test_handle_error_notification_email_failure(
        self,
        mock_send_email: Mock,
        mock_container: Mock,
        error_event: ErrorNotificationRequested,
    ) -> None:
        """Test error notification when email sending fails."""
        mock_send_email.return_value = False
        service = NotificationService(mock_container)

        # Should not raise exception
        service.handle_event(error_event)

        # Email should still be attempted
        mock_send_email.assert_called_once()

    @patch("the_alchemiser.notifications_v2.service.send_email_notification")
    def test_handle_error_notification_exception(
        self,
        mock_send_email: Mock,
        mock_container: Mock,
        error_event: ErrorNotificationRequested,
    ) -> None:
        """Test error notification when exception occurs during sending."""
        mock_send_email.side_effect = Exception("SMTP connection failed")
        service = NotificationService(mock_container)

        # Should not raise exception - error should be logged
        service.handle_event(error_event)

        mock_send_email.assert_called_once()


class TestTradingNotificationHandling:
    """Test trading notification handling behaviors."""

    @pytest.fixture
    def mock_container(self) -> Mock:
        """Create a mock ApplicationContainer."""
        container = Mock()
        mock_event_bus = Mock()
        container.services.event_bus.return_value = mock_event_bus
        return container

    @pytest.fixture
    def successful_trading_event(self) -> TradingNotificationRequested:
        """Create a successful trading notification event."""
        return TradingNotificationRequested(
            event_id=f"event-{uuid.uuid4()}",
            correlation_id=f"corr-{uuid.uuid4()}",
            causation_id=f"cause-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="test_service",
            trading_success=True,
            trading_mode="PAPER",
            orders_placed=5,
            orders_succeeded=5,
            total_trade_value=10000.50,
            execution_data={
                "symbols_traded": ["AAPL", "GOOGL", "MSFT"],
                "total_notional": 10000.50,
            },
            error_message=None,
            error_code=None,
        )

    @pytest.fixture
    def failed_trading_event(self) -> TradingNotificationRequested:
        """Create a failed trading notification event."""
        return TradingNotificationRequested(
            event_id=f"event-{uuid.uuid4()}",
            correlation_id=f"corr-{uuid.uuid4()}",
            causation_id=f"cause-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="test_service",
            trading_success=False,
            trading_mode="LIVE",
            orders_placed=5,
            orders_succeeded=2,
            total_trade_value=3000.00,
            execution_data={
                "failed_symbols": ["TSLA", "NVDA", "AMD"],
            },
            error_message="Failed to execute 3 orders due to insufficient buying power",
            error_code="EXEC-002",
        )

    @patch("the_alchemiser.notifications_v2.service.send_email_notification")
    @patch("the_alchemiser.notifications_v2.service.EmailTemplates")
    def test_handle_successful_trading_notification(
        self,
        mock_templates: Mock,
        mock_send_email: Mock,
        mock_container: Mock,
        successful_trading_event: TradingNotificationRequested,
    ) -> None:
        """Test successful trading notification handling."""
        mock_templates.simple_trading_notification.return_value = (
            "<html>Success Report</html>"
        )
        mock_send_email.return_value = True
        service = NotificationService(mock_container)

        service.handle_event(successful_trading_event)

        # Verify simplified template was used
        mock_templates.simple_trading_notification.assert_called_once()
        call_args = mock_templates.simple_trading_notification.call_args
        assert call_args.kwargs["success"] is True
        assert call_args.kwargs["mode"] == "PAPER"
        assert call_args.kwargs["orders_count"] == 5

        # Verify email was sent with success status
        mock_send_email.assert_called_once()
        subject = mock_send_email.call_args.kwargs["subject"]
        assert "[SUCCESS]" in subject
        assert "PAPER" in subject

    @patch("the_alchemiser.notifications_v2.service.send_email_notification")
    @patch("the_alchemiser.notifications_v2.service.EmailTemplates")
    def test_handle_successful_trading_with_template_fallback(
        self,
        mock_templates: Mock,
        mock_send_email: Mock,
        mock_container: Mock,
        successful_trading_event: TradingNotificationRequested,
    ) -> None:
        """Test successful trading with fallback to basic template on error."""
        # With simplified template, no fallback is needed
        # The simplified template is simple enough that it shouldn't fail
        mock_templates.simple_trading_notification.return_value = (
            "<html>Simple Success Report</html>"
        )
        mock_send_email.return_value = True
        service = NotificationService(mock_container)

        service.handle_event(successful_trading_event)

        # Verify simplified template was used
        mock_templates.simple_trading_notification.assert_called_once()

        # Verify email was sent
        mock_send_email.assert_called_once()
        html_content = mock_send_email.call_args.kwargs["html_content"]
        assert "Simple Success Report" in html_content

    @patch("the_alchemiser.notifications_v2.service.send_email_notification")
    @patch("the_alchemiser.notifications_v2.service.EmailTemplates")
    def test_handle_failed_trading_notification(
        self,
        mock_templates: Mock,
        mock_send_email: Mock,
        mock_container: Mock,
        failed_trading_event: TradingNotificationRequested,
    ) -> None:
        """Test failed trading notification handling."""
        mock_templates.simple_trading_notification.return_value = "<html>Failure Report</html>"
        mock_send_email.return_value = True
        service = NotificationService(mock_container)

        service.handle_event(failed_trading_event)

        # Verify simplified template was used
        mock_templates.simple_trading_notification.assert_called_once()
        call_args = mock_templates.simple_trading_notification.call_args
        
        # Check template parameters
        assert call_args.kwargs["success"] is False
        assert call_args.kwargs["mode"] == "LIVE"
        assert call_args.kwargs["orders_count"] == 5

        # Verify email was sent with failure status
        mock_send_email.assert_called_once()
        subject = mock_send_email.call_args.kwargs["subject"]
        assert "[FAILURE]" in subject
        assert "EXEC-002" in subject
        assert "LIVE" in subject

    @patch("the_alchemiser.notifications_v2.service.send_email_notification")
    @patch("the_alchemiser.notifications_v2.service.EmailTemplates")
    def test_handle_failed_trading_without_error_code(
        self,
        mock_templates: Mock,
        mock_send_email: Mock,
        mock_container: Mock,
    ) -> None:
        """Test failed trading notification without error code."""
        mock_templates.simple_trading_notification.return_value = "<html>Failure Report</html>"
        mock_send_email.return_value = True
        service = NotificationService(mock_container)

        event = TradingNotificationRequested(
            event_id=f"event-{uuid.uuid4()}",
            correlation_id=f"corr-{uuid.uuid4()}",
            causation_id=f"cause-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="test_service",
            trading_success=False,
            trading_mode="PAPER",
            orders_placed=3,
            orders_succeeded=1,
            total_trade_value=500.00,
            execution_data={},
            error_message="Unknown error",
            error_code=None,  # No error code
        )

        service.handle_event(event)

        # Verify subject doesn't include error code
        subject = mock_send_email.call_args.kwargs["subject"]
        assert "[FAILURE]" in subject
        assert "EXEC-" not in subject

    @patch("the_alchemiser.notifications_v2.service.send_email_notification")
    @patch("the_alchemiser.notifications_v2.service.EmailTemplates")
    def test_handle_failed_trading_without_error_message(
        self,
        mock_templates: Mock,
        mock_send_email: Mock,
        mock_container: Mock,
    ) -> None:
        """Test failed trading notification handles missing error message."""
        mock_templates.simple_trading_notification.return_value = "<html>Failure Report</html>"
        mock_send_email.return_value = True
        service = NotificationService(mock_container)

        event = TradingNotificationRequested(
            event_id=f"event-{uuid.uuid4()}",
            correlation_id=f"corr-{uuid.uuid4()}",
            causation_id=f"cause-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="test_service",
            trading_success=False,
            trading_mode="PAPER",
            orders_placed=1,
            orders_succeeded=0,
            total_trade_value=0.0,
            execution_data={},
            error_message=None,  # No error message
            error_code=None,
        )

        service.handle_event(event)

        # Verify simplified template was called (no error message processing needed)
        mock_templates.simple_trading_notification.assert_called_once()

    @patch("the_alchemiser.notifications_v2.service.send_email_notification")
    def test_trading_notification_email_send_failure(
        self,
        mock_send_email: Mock,
        mock_container: Mock,
        successful_trading_event: TradingNotificationRequested,
    ) -> None:
        """Test trading notification when email sending fails."""
        mock_send_email.return_value = False
        service = NotificationService(mock_container)

        # Should not raise exception
        service.handle_event(successful_trading_event)

        mock_send_email.assert_called_once()


class TestSystemNotificationHandling:
    """Test system notification handling behaviors."""

    @pytest.fixture
    def mock_container(self) -> Mock:
        """Create a mock ApplicationContainer."""
        container = Mock()
        mock_event_bus = Mock()
        container.services.event_bus.return_value = mock_event_bus
        return container

    @pytest.fixture
    def system_event(self) -> SystemNotificationRequested:
        """Create a system notification event."""
        return SystemNotificationRequested(
            event_id=f"event-{uuid.uuid4()}",
            correlation_id=f"corr-{uuid.uuid4()}",
            causation_id=f"cause-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="test_service",
            notification_type="INFO",
            subject="System Health Check",
            html_content="<html><body>System is operational</body></html>",
            text_content="System is operational",
        )

    @patch("the_alchemiser.notifications_v2.service.send_email_notification")
    def test_handle_system_notification_success(
        self,
        mock_send_email: Mock,
        mock_container: Mock,
        system_event: SystemNotificationRequested,
    ) -> None:
        """Test successful system notification handling."""
        mock_send_email.return_value = True
        service = NotificationService(mock_container)

        service.handle_event(system_event)

        # Verify email was sent with provided content
        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args

        assert call_args.kwargs["subject"] == "System Health Check"
        assert call_args.kwargs["html_content"] == system_event.html_content
        assert call_args.kwargs["text_content"] == system_event.text_content
        assert call_args.kwargs["recipient_email"] is None

    @patch("the_alchemiser.notifications_v2.service.send_email_notification")
    def test_handle_system_notification_with_recipient_override(
        self,
        mock_send_email: Mock,
        mock_container: Mock,
    ) -> None:
        """Test system notification with recipient override."""
        mock_send_email.return_value = True
        service = NotificationService(mock_container)

        # Create event with recipient override directly
        system_event = SystemNotificationRequested(
            event_id=f"event-{uuid.uuid4()}",
            correlation_id=f"corr-{uuid.uuid4()}",
            causation_id=f"cause-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="test_service",
            notification_type="INFO",
            subject="System Health Check",
            html_content="<html><body>System is operational</body></html>",
            text_content="System is operational",
            recipient_override="admin@example.com",
        )

        service.handle_event(system_event)

        call_args = mock_send_email.call_args
        assert call_args.kwargs["recipient_email"] == "admin@example.com"

    @patch("the_alchemiser.notifications_v2.service.send_email_notification")
    def test_handle_system_notification_without_text_content(
        self,
        mock_send_email: Mock,
        mock_container: Mock,
    ) -> None:
        """Test system notification handles missing text content."""
        mock_send_email.return_value = True
        service = NotificationService(mock_container)

        event = SystemNotificationRequested(
            event_id=f"event-{uuid.uuid4()}",
            correlation_id=f"corr-{uuid.uuid4()}",
            causation_id=f"cause-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="test_service",
            notification_type="WARNING",
            subject="System Warning",
            html_content="<html><body>Warning message</body></html>",
            text_content=None,  # No text content
        )

        service.handle_event(event)

        call_args = mock_send_email.call_args
        assert call_args.kwargs["text_content"] is None

    @patch("the_alchemiser.notifications_v2.service.send_email_notification")
    def test_handle_system_notification_email_failure(
        self,
        mock_send_email: Mock,
        mock_container: Mock,
        system_event: SystemNotificationRequested,
    ) -> None:
        """Test system notification when email sending fails."""
        mock_send_email.return_value = False
        service = NotificationService(mock_container)

        # Should not raise exception
        service.handle_event(system_event)

        mock_send_email.assert_called_once()

    @patch("the_alchemiser.notifications_v2.service.send_email_notification")
    def test_handle_system_notification_exception(
        self,
        mock_send_email: Mock,
        mock_container: Mock,
        system_event: SystemNotificationRequested,
    ) -> None:
        """Test system notification when exception occurs."""
        mock_send_email.side_effect = Exception("Network timeout")
        service = NotificationService(mock_container)

        # Should not raise exception - error should be logged
        service.handle_event(system_event)

        mock_send_email.assert_called_once()


class TestEventRoutingAndErrorHandling:
    """Test event routing and general error handling."""

    @pytest.fixture
    def mock_container(self) -> Mock:
        """Create a mock ApplicationContainer."""
        container = Mock()
        mock_event_bus = Mock()
        container.services.event_bus.return_value = mock_event_bus
        return container

    def test_handle_unsupported_event_type(self, mock_container: Mock) -> None:
        """Test handling of unsupported event types."""
        service = NotificationService(mock_container)

        # Create a generic event that's not a notification event
        class UnsupportedEvent(BaseEvent):
            event_type: str = "UnsupportedEvent"

        event = UnsupportedEvent(
            event_id=f"event-{uuid.uuid4()}",
            correlation_id=f"corr-{uuid.uuid4()}",
            causation_id=f"cause-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="test_service",
        )

        # Should not raise exception - just ignore
        service.handle_event(event)

    @patch("the_alchemiser.notifications_v2.service.send_email_notification")
    def test_handle_event_exception_logged(
        self,
        mock_send_email: Mock,
        mock_container: Mock,
    ) -> None:
        """Test that exceptions during event handling are logged with context."""
        mock_send_email.side_effect = Exception("Catastrophic failure")
        service = NotificationService(mock_container)

        event = ErrorNotificationRequested(
            event_id=f"event-{uuid.uuid4()}",
            correlation_id="corr-test-123",
            causation_id=f"cause-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="test_service",
            error_severity="HIGH",
            error_priority="HIGH",
            error_title="Test Error",
            error_report="Test error report",
        )

        # Should not raise exception
        service.handle_event(event)


class TestLoggingBehavior:
    """Test structured logging behavior (JSON format via shared.logging)."""

    @pytest.fixture
    def mock_container(self) -> Mock:
        """Create a mock ApplicationContainer."""
        container = Mock()
        mock_event_bus = Mock()
        container.services.event_bus.return_value = mock_event_bus
        return container

    @patch("the_alchemiser.notifications_v2.service.send_email_notification")
    def test_logging_on_successful_error_notification(
        self,
        mock_send_email: Mock,
        mock_container: Mock,
    ) -> None:
        """Test that successful operations are logged."""
        mock_send_email.return_value = True
        service = NotificationService(mock_container)

        event = ErrorNotificationRequested(
            event_id=f"event-{uuid.uuid4()}",
            correlation_id=f"corr-{uuid.uuid4()}",
            causation_id=f"cause-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="test_service",
            error_severity="HIGH",
            error_priority="HIGH",
            error_title="Test Error",
            error_report="Test error report",
        )

        # Mock the logger to capture calls
        with patch.object(service.logger, "info") as mock_logger_info:
            service.handle_event(event)

            # Verify logging occurred
            assert mock_logger_info.call_count >= 2
            # First log: sending notification
            # Second log: email sent successfully

    @patch("the_alchemiser.notifications_v2.service.send_email_notification")
    def test_logging_on_email_send_failure(
        self,
        mock_send_email: Mock,
        mock_container: Mock,
    ) -> None:
        """Test that email send failures are logged as errors."""
        mock_send_email.return_value = False
        service = NotificationService(mock_container)

        event = SystemNotificationRequested(
            event_id=f"event-{uuid.uuid4()}",
            correlation_id=f"corr-{uuid.uuid4()}",
            causation_id=f"cause-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="test_service",
            notification_type="INFO",
            subject="Test",
            html_content="<html>Test</html>",
        )

        with patch.object(service.logger, "error") as mock_logger_error:
            service.handle_event(event)

            # Verify error was logged
            mock_logger_error.assert_called_once()
            assert "Failed to send system notification email" in str(mock_logger_error.call_args)

    @patch("the_alchemiser.notifications_v2.service.send_email_notification")
    def test_logging_includes_correlation_id_on_error(
        self,
        mock_send_email: Mock,
        mock_container: Mock,
    ) -> None:
        """Test that error logs include correlation_id for traceability."""
        mock_send_email.side_effect = Exception("Test exception")
        service = NotificationService(mock_container)

        correlation_id = f"corr-test-{uuid.uuid4()}"
        event_id = f"event-test-{uuid.uuid4()}"

        event = ErrorNotificationRequested(
            event_id=event_id,
            correlation_id=correlation_id,
            causation_id=f"cause-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="test_service",
            error_severity="HIGH",
            error_priority="HIGH",
            error_title="Test Error",
            error_report="Test error report",
        )

        with patch.object(service.logger, "error") as mock_logger_error:
            service.handle_event(event)

            # Verify error log includes extra context
            assert mock_logger_error.call_count > 0
            # Check that extra parameter with event_id and correlation_id was passed
            for call in mock_logger_error.call_args_list:
                if "extra" in call.kwargs:
                    extra = call.kwargs["extra"]
                    assert extra["event_id"] == event_id
                    assert extra["correlation_id"] == correlation_id
                    break


class TestMissingAndPartialData:
    """Test handling of missing and partial data scenarios."""

    @pytest.fixture
    def mock_container(self) -> Mock:
        """Create a mock ApplicationContainer."""
        container = Mock()
        mock_event_bus = Mock()
        container.services.event_bus.return_value = mock_event_bus
        return container

    @patch("the_alchemiser.notifications_v2.service.send_email_notification")
    @patch("the_alchemiser.notifications_v2.service.EmailTemplates")
    def test_trading_notification_with_empty_execution_data(
        self,
        mock_templates: Mock,
        mock_send_email: Mock,
        mock_container: Mock,
    ) -> None:
        """Test trading notification with empty execution data dictionary."""
        mock_templates.simple_trading_notification.return_value = "<html>Report</html>"
        mock_send_email.return_value = True
        service = NotificationService(mock_container)

        event = TradingNotificationRequested(
            event_id=f"event-{uuid.uuid4()}",
            correlation_id=f"corr-{uuid.uuid4()}",
            causation_id=f"cause-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="test_service",
            trading_success=False,
            trading_mode="PAPER",
            orders_placed=0,
            orders_succeeded=0,
            total_trade_value=0.0,
            execution_data={},  # Empty execution data
            error_message="No orders executed",
        )

        # Should handle gracefully with simplified template
        service.handle_event(event)

        mock_send_email.assert_called_once()
        # Verify simplified template was called
        mock_templates.simple_trading_notification.assert_called_once()

    @patch("the_alchemiser.notifications_v2.service.send_email_notification")
    @patch("the_alchemiser.notifications_v2.service.EmailTemplates")
    def test_successful_trading_with_minimal_execution_data(
        self,
        mock_templates: Mock,
        mock_send_email: Mock,
        mock_container: Mock,
    ) -> None:
        """Test successful trading notification with minimal execution data."""
        mock_templates.simple_trading_notification.return_value = (
            "<html>Success</html>"
        )
        mock_send_email.return_value = True
        service = NotificationService(mock_container)

        event = TradingNotificationRequested(
            event_id=f"event-{uuid.uuid4()}",
            correlation_id=f"corr-{uuid.uuid4()}",
            causation_id=f"cause-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="test_service",
            trading_success=True,
            trading_mode="PAPER",
            orders_placed=1,
            orders_succeeded=1,
            total_trade_value=100.0,
            execution_data={},  # Minimal data
        )

        # Should handle gracefully with simplified template
        service.handle_event(event)

        mock_send_email.assert_called_once()
        # Verify simplified template was called with correct parameters
        mock_templates.simple_trading_notification.assert_called_once()
        call_args = mock_templates.simple_trading_notification.call_args
        assert call_args.kwargs["success"] is True
        assert call_args.kwargs["orders_count"] == 1

    @patch("the_alchemiser.notifications_v2.service.send_email_notification")
    def test_error_notification_with_minimal_fields(
        self,
        mock_send_email: Mock,
        mock_container: Mock,
    ) -> None:
        """Test error notification with only required fields."""
        mock_send_email.return_value = True
        service = NotificationService(mock_container)

        # Create event with minimal required fields
        event = ErrorNotificationRequested(
            event_id=f"event-{uuid.uuid4()}",
            correlation_id=f"corr-{uuid.uuid4()}",
            causation_id=f"cause-{uuid.uuid4()}",
            timestamp=datetime.now(UTC),
            source_module="test_service",
            error_severity="MEDIUM",
            error_priority="MEDIUM",
            error_title="Minimal Error",
            error_report="Basic error report",
        )

        service.handle_event(event)

        # Should work without optional fields
        mock_send_email.assert_called_once()
        subject = mock_send_email.call_args.kwargs["subject"]
        assert "MEDIUM" in subject
