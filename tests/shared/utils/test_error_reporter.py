"""Business Unit: shared | Status: current.

Tests for utils error_reporter module with security and observability features.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest

from the_alchemiser.shared.errors.exceptions import SecurityError
from the_alchemiser.shared.utils.error_reporter import (
    ErrorReporter,
    get_error_reporter,
    report_error_globally,
)


class TestErrorReporter:
    """Test ErrorReporter class basic functionality."""

    def test_create_error_reporter(self):
        """Test creating error reporter."""
        reporter = ErrorReporter()
        assert reporter is not None
        assert len(reporter.error_counts) == 0
        assert len(reporter.critical_errors) == 0
        assert len(reporter.recent_errors) == 0
        assert reporter.error_rate_window == 300
        assert reporter.error_rate_threshold == 10

    def test_report_error_basic(self):
        """Test basic error reporting."""
        reporter = ErrorReporter()
        error = ValueError("Test error")

        reporter.report_error(
            error=error,
            context={"operation": "test_operation"},
        )

        assert len(reporter.recent_errors) == 1
        assert reporter.error_counts["ValueError:test_operation"] == 1

    def test_report_error_tracks_correlation_id(self):
        """Test that correlation_id is tracked."""
        reporter = ErrorReporter()
        error = ValueError("Test error")
        context = {
            "correlation_id": "corr-123",
            "causation_id": "cause-456",
            "operation": "test_op",
        }

        reporter.report_error(error=error, context=context)

        recent = reporter.recent_errors[0]
        assert recent["correlation_id"] == "corr-123"
        assert recent["causation_id"] == "cause-456"
        assert recent["operation"] == "test_op"

    def test_report_error_redacts_sensitive_data(self):
        """Test that sensitive data is redacted."""
        reporter = ErrorReporter()
        error = ValueError("Test error")
        context = {
            "operation": "login",
            "password": "secret123",
            "api_key": "key-abc-123",
            "username": "testuser",
        }

        reporter.report_error(error=error, context=context)

        recent = reporter.recent_errors[0]
        assert recent["context"]["password"] == "[REDACTED]"
        assert recent["context"]["api_key"] == "[REDACTED]"
        assert recent["context"]["username"] == "testuser"

    def test_report_error_redacts_nested_sensitive_data(self):
        """Test that sensitive data in nested dicts is redacted."""
        reporter = ErrorReporter()
        error = ValueError("Test error")
        context = {
            "operation": "api_call",
            "request": {
                "url": "https://api.example.com",
                "headers": {"authorization": "Bearer token123"},
            },
        }

        reporter.report_error(error=error, context=context)

        recent = reporter.recent_errors[0]
        assert recent["context"]["request"]["headers"]["authorization"] == "[REDACTED]"
        assert recent["context"]["request"]["url"] == "https://api.example.com"

    def test_critical_error_detection(self):
        """Test that critical errors are detected."""
        reporter = ErrorReporter()
        error = SecurityError("Security breach")

        reporter.report_error(error=error, context={"operation": "test"})

        assert len(reporter.critical_errors) == 1
        assert reporter.critical_errors[0]["error_type"] == "SecurityError"

    def test_critical_error_notification(self):
        """Test that critical errors trigger notifications."""
        mock_notification = Mock()
        reporter = ErrorReporter(notification_manager=mock_notification)
        error = SecurityError("Security breach")

        reporter.report_error(error=error, context={"operation": "test"})

        mock_notification.send_critical_alert.assert_called_once()

    def test_time_based_cleanup(self):
        """Test that old errors are cleaned up."""
        reporter = ErrorReporter()

        # Add an old error manually
        old_time = datetime.now(UTC) - timedelta(minutes=10)
        reporter.recent_errors.append(
            {
                "timestamp": old_time.isoformat(),
                "error_type": "OldError",
                "message": "Old",
            }
        )

        # Report a new error (triggers cleanup)
        error = ValueError("New error")
        reporter.report_error(error=error, context={"operation": "test"})

        # Old error should be gone
        assert len(reporter.recent_errors) == 1
        assert reporter.recent_errors[0]["error_type"] == "ValueError"

    def test_critical_errors_cleanup_after_one_hour(self):
        """Test that critical errors are cleaned up after 1 hour."""
        reporter = ErrorReporter()

        # Add an old critical error
        old_time = datetime.now(UTC) - timedelta(hours=2)
        reporter.critical_errors.append(
            {
                "timestamp": old_time.isoformat(),
                "error_type": "OldCritical",
                "message": "Old critical",
            }
        )

        # Report a new error (triggers cleanup)
        error = ValueError("New error")
        reporter.report_error(error=error, context={"operation": "test"})

        # Old critical error should be gone
        assert len(reporter.critical_errors) == 0


class TestErrorReporterRateMonitoring:
    """Test rate monitoring and alerting."""

    def test_high_error_rate_triggers_alert_once(self):
        """Test that high error rates trigger alert only once."""
        mock_notification = Mock()
        reporter = ErrorReporter(notification_manager=mock_notification)

        # Report more than threshold
        for _ in range(11):
            reporter.report_error(ValueError("Test"), context={"operation": "test"})

        # Should alert only once
        assert mock_notification.send_warning_alert.call_count == 1

    def test_alert_resets_when_rate_drops(self):
        """Test that alerts reset when error rate drops below threshold."""
        mock_notification = Mock()
        reporter = ErrorReporter(notification_manager=mock_notification)

        # Report more than threshold
        for _ in range(11):
            reporter.report_error(ValueError("Test"), context={"operation": "test"})

        assert mock_notification.send_warning_alert.call_count == 1

        # Clear errors to drop below threshold
        reporter.error_counts["ValueError:test"] = 5

        # Report one more error to trigger check
        reporter.report_error(ValueError("Test"), context={"operation": "test"})

        # Should still be only 1 alert (no new alert)
        assert mock_notification.send_warning_alert.call_count == 1

        # Now increase again
        for _ in range(10):
            reporter.report_error(ValueError("Test"), context={"operation": "test"})

        # Should alert again (2 total)
        assert mock_notification.send_warning_alert.call_count == 2


class TestErrorReporterSummary:
    """Test error summary functionality."""

    def test_get_error_summary_empty(self):
        """Test error summary with no errors."""
        reporter = ErrorReporter()
        summary = reporter.get_error_summary()

        assert summary["critical_errors"] == 0
        assert summary["last_critical"] is None
        assert summary["recent_errors_count"] == 0
        assert summary["error_rate_per_minute"] == 0.0

    def test_get_error_summary_with_errors(self):
        """Test error summary with errors."""
        reporter = ErrorReporter()

        for _ in range(3):
            reporter.report_error(ValueError("Test"), context={"operation": "op1"})

        summary = reporter.get_error_summary()

        assert summary["recent_errors_count"] == 3
        assert summary["error_counts"]["ValueError:op1"] == 3
        assert summary["error_rate_per_minute"] > 0

    def test_get_error_summary_with_critical(self):
        """Test error summary includes critical errors."""
        reporter = ErrorReporter()

        reporter.report_error(
            SecurityError("Critical"), context={"operation": "security_check"}
        )

        summary = reporter.get_error_summary()

        assert summary["critical_errors"] == 1
        assert summary["last_critical"]["error_type"] == "SecurityError"


class TestErrorReporterFactoryFunctions:
    """Test factory and singleton functions."""

    def test_get_error_reporter_singleton(self):
        """Test that get_error_reporter returns singleton."""
        # Clear the global instance
        import the_alchemiser.shared.utils.error_reporter as reporter_module

        reporter_module._global_error_reporter = None

        reporter1 = get_error_reporter()
        reporter2 = get_error_reporter()

        # Should be the same instance
        assert reporter1 is reporter2

    def test_global_reporter_persists_state(self):
        """Test that global reporter persists state."""
        import the_alchemiser.shared.utils.error_reporter as reporter_module

        reporter_module._global_error_reporter = None

        reporter1 = get_error_reporter()
        reporter1.report_error(ValueError("Test"), context={"operation": "test"})

        reporter2 = get_error_reporter()

        # Should have the error from reporter1
        assert len(reporter2.recent_errors) == 1

    def test_report_error_globally(self):
        """Test the global error reporting function."""
        import the_alchemiser.shared.utils.error_reporter as reporter_module

        reporter_module._global_error_reporter = None

        report_error_globally(
            ValueError("Global error"),
            context={"operation": "global_test", "correlation_id": "corr-123"},
        )

        reporter = get_error_reporter()
        assert len(reporter.recent_errors) == 1
        assert reporter.recent_errors[0]["correlation_id"] == "corr-123"


class TestErrorReporterIntegration:
    """Test integration scenarios."""

    def test_full_workflow_with_observability(self):
        """Test complete error workflow with full observability context."""
        mock_notification = Mock()
        reporter = ErrorReporter(notification_manager=mock_notification)

        # Report error with full context
        error = ValueError("Workflow error")
        context = {
            "module": "execution_v2",
            "correlation_id": "corr-123",
            "causation_id": "cause-456",
            "event_id": "evt-789",
            "operation": "order_execution",
        }

        reporter.report_error(error=error, context=context)

        # Verify all context is preserved
        recent = reporter.recent_errors[0]
        assert recent["correlation_id"] == "corr-123"
        assert recent["causation_id"] == "cause-456"
        assert recent["operation"] == "order_execution"

        # Verify in summary
        summary = reporter.get_error_summary()
        assert summary["recent_errors_count"] == 1
        assert "ValueError:order_execution" in summary["error_counts"]

    def test_exception_with_to_dict_method(self):
        """Test that exceptions with to_dict method get their data included."""
        reporter = ErrorReporter()

        # Create an error with to_dict method
        error = SecurityError("Security issue", context={"ip": "192.168.1.1"})

        reporter.report_error(error=error, context={"operation": "auth"})

        recent = reporter.recent_errors[0]
        # Should have the base context
        assert recent["operation"] == "auth"
        # Should also have data from to_dict
        assert "timestamp" in recent

    def test_clear_errors_for_testing(self):
        """Test that clear_errors works for testing scenarios."""
        reporter = ErrorReporter()

        # Add some errors
        for _ in range(5):
            reporter.report_error(ValueError("Test"), context={"operation": "test"})

        assert len(reporter.recent_errors) == 5

        # Clear
        reporter.clear_errors()

        # Should be empty
        assert len(reporter.recent_errors) == 0
        assert len(reporter.error_counts) == 0
        assert len(reporter.critical_errors) == 0
        assert len(reporter._alerted_errors) == 0
