"""Business Unit: shared | Status: current.

Tests for error reporter module with rate monitoring and aggregation.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from the_alchemiser.shared.errors.error_reporter import (
    ERROR_COUNTS_CLEANUP_WINDOW_SECONDS,
    ERROR_RATE_THRESHOLD_PER_MIN,
    ERROR_RATE_WINDOW_SECONDS,
    SENSITIVE_KEYS,
    EnhancedErrorReporter,
    get_enhanced_error_reporter,
    get_global_error_reporter,
)


class TestEnhancedErrorReporter:
    """Test EnhancedErrorReporter class."""

    def test_create_error_reporter(self):
        """Test creating error reporter."""
        reporter = EnhancedErrorReporter()
        assert reporter is not None
        assert len(reporter.error_counts) == 0
        assert len(reporter.critical_errors) == 0
        assert len(reporter.recent_errors) == 0
        assert reporter.error_rate_window == 300  # 5 minutes

    def test_report_error_with_context_basic(self):
        """Test basic error reporting."""
        reporter = EnhancedErrorReporter()
        error = ValueError("Test error")

        reporter.report_error_with_context(
            error=error,
            context={"module": "test"},
            operation="test_operation",
        )

        assert len(reporter.recent_errors) == 1
        assert reporter.error_counts["ValueError:test_operation"] == 1

    def test_report_error_tracks_error_type(self):
        """Test that error type is tracked."""
        reporter = EnhancedErrorReporter()
        error = RuntimeError("Runtime error")

        reporter.report_error_with_context(
            error=error,
            operation="runtime_test",
        )

        recent = reporter.recent_errors[0]
        assert recent["error_type"] == "RuntimeError"
        assert recent["message"] == "Runtime error"

    def test_report_error_tracks_timestamp(self):
        """Test that timestamp is tracked."""
        reporter = EnhancedErrorReporter()
        error = Exception("Test")

        before = datetime.now(UTC)
        reporter.report_error_with_context(error=error, operation="test")
        after = datetime.now(UTC)

        recent = reporter.recent_errors[0]
        timestamp = datetime.fromisoformat(recent["timestamp"])
        assert before <= timestamp <= after

    def test_report_error_tracks_context(self):
        """Test that context is preserved."""
        reporter = EnhancedErrorReporter()
        error = Exception("Test")
        context = {
            "module": "strategy_v2",
            "correlation_id": "corr-123",
            "symbol": "AAPL",
        }

        reporter.report_error_with_context(
            error=error,
            context=context,
            operation="signal_generation",
        )

        recent = reporter.recent_errors[0]
        assert recent["context"] == context
        assert recent["operation"] == "signal_generation"

    def test_report_error_tracks_critical_flag(self):
        """Test that critical flag is tracked."""
        reporter = EnhancedErrorReporter()
        error = Exception("Critical error")

        reporter.report_error_with_context(
            error=error,
            is_critical=True,
            operation="critical_op",
        )

        recent = reporter.recent_errors[0]
        assert recent["is_critical"] is True

    def test_report_multiple_errors(self):
        """Test reporting multiple errors."""
        reporter = EnhancedErrorReporter()

        for i in range(5):
            error = ValueError(f"Error {i}")
            reporter.report_error_with_context(
                error=error,
                operation=f"operation_{i}",
            )

        assert len(reporter.recent_errors) == 5
        assert len(reporter.error_counts) == 5


class TestEnhancedErrorReporterRateMonitoring:
    """Test rate monitoring functionality."""

    def test_cleanup_old_errors(self):
        """Test that old errors are cleaned up."""
        reporter = EnhancedErrorReporter()

        # Add an old error (more than 5 minutes ago)
        old_timestamp = datetime.now(UTC) - timedelta(minutes=10)
        reporter.recent_errors.append({
            "timestamp": old_timestamp.isoformat(),
            "error_type": "OldError",
            "message": "Old error",
        })

        # Add a recent error
        error = ValueError("Recent error")
        reporter.report_error_with_context(error=error, operation="test")

        # Old error should be cleaned up
        assert len(reporter.recent_errors) == 1
        assert reporter.recent_errors[0]["error_type"] == "ValueError"

    @patch("the_alchemiser.shared.errors.error_reporter.logger")
    def test_check_error_rates_high_rate(self, mock_logger):
        """Test that high error rates trigger warnings."""
        reporter = EnhancedErrorReporter()

        # Add many errors quickly (more than 10 per minute)
        for i in range(60):
            reporter.recent_errors.append({
                "timestamp": datetime.now(UTC).isoformat(),
                "error_type": "TestError",
                "message": f"Error {i}",
            })

        reporter._check_error_rates()

        # Should have logged a warning
        mock_logger.warning.assert_called_once()
        warning_call = mock_logger.warning.call_args[0][0]
        assert "High error rate detected" in warning_call

    @patch("the_alchemiser.shared.errors.error_reporter.logger")
    def test_check_error_rates_normal_rate(self, mock_logger):
        """Test that normal error rates don't trigger warnings."""
        reporter = EnhancedErrorReporter()

        # Add a small number of errors
        for i in range(5):
            reporter.recent_errors.append({
                "timestamp": datetime.now(UTC).isoformat(),
                "error_type": "TestError",
                "message": f"Error {i}",
            })

        reporter._check_error_rates()

        # Should not have logged a warning
        mock_logger.warning.assert_not_called()


class TestEnhancedErrorReporterSummary:
    """Test error summary generation."""

    def test_get_error_summary_empty(self):
        """Test error summary with no errors."""
        reporter = EnhancedErrorReporter()
        summary = reporter.get_error_summary()

        assert summary["total_error_types"] == 0
        assert summary["recent_errors_count"] == 0
        assert summary["error_rate_per_minute"] == 0.0
        assert len(summary["most_common_errors"]) == 0

    def test_get_error_summary_with_errors(self):
        """Test error summary with errors."""
        reporter = EnhancedErrorReporter()

        # Add various errors
        for i in range(3):
            reporter.report_error_with_context(
                ValueError("Test error"),
                operation="op1",
            )
        for i in range(2):
            reporter.report_error_with_context(
                RuntimeError("Runtime error"),
                operation="op2",
            )

        summary = reporter.get_error_summary()

        assert summary["total_error_types"] == 2
        assert summary["recent_errors_count"] == 5
        assert summary["error_rate_per_minute"] > 0

    def test_get_error_summary_most_common(self):
        """Test that most common errors are reported."""
        reporter = EnhancedErrorReporter()

        # Add more of one error type
        for i in range(5):
            reporter.report_error_with_context(
                ValueError("Frequent error"),
                operation="frequent_op",
            )
        reporter.report_error_with_context(
            RuntimeError("Rare error"),
            operation="rare_op",
        )

        summary = reporter.get_error_summary()
        most_common = summary["most_common_errors"]

        assert len(most_common) >= 1
        assert most_common[0][0] == "ValueError:frequent_op"
        assert most_common[0][1] == 5

    def test_get_error_summary_limits_common_errors(self):
        """Test that summary limits to top 5 most common errors."""
        reporter = EnhancedErrorReporter()

        # Add many different error types
        for i in range(10):
            reporter.report_error_with_context(
                ValueError(f"Error {i}"),
                operation=f"op_{i}",
            )

        summary = reporter.get_error_summary()
        most_common = summary["most_common_errors"]

        assert len(most_common) <= 5


class TestEnhancedErrorReporterCriticalErrors:
    """Test critical error handling."""

    @patch("the_alchemiser.shared.errors.error_handler.get_error_handler")
    def test_report_critical_error_uses_handler(self, mock_get_handler):
        """Test that critical errors are reported to error handler."""
        mock_handler = Mock()
        mock_get_handler.return_value = mock_handler

        reporter = EnhancedErrorReporter()
        error = Exception("Critical error")

        reporter.report_error_with_context(
            error=error,
            is_critical=True,
            operation="critical_operation",
        )

        # Should have called error handler
        mock_handler.handle_error.assert_called_once()
        call_args = mock_handler.handle_error.call_args
        assert call_args[1]["error"] == error
        assert call_args[1]["context"] == "critical_operation"


class TestErrorReporterFactoryFunctions:
    """Test factory and singleton functions."""

    def test_get_enhanced_error_reporter_creates_new_instance(self):
        """Test that get_enhanced_error_reporter creates new instances."""
        reporter1 = get_enhanced_error_reporter()
        reporter2 = get_enhanced_error_reporter()

        # Should be different instances
        assert reporter1 is not reporter2
        assert isinstance(reporter1, EnhancedErrorReporter)
        assert isinstance(reporter2, EnhancedErrorReporter)

    def test_get_global_error_reporter_singleton(self):
        """Test that get_global_error_reporter returns singleton."""
        # Clear the global instance first
        import the_alchemiser.shared.errors.error_reporter as reporter_module

        reporter_module._global_enhanced_error_reporter = None

        reporter1 = get_global_error_reporter()
        reporter2 = get_global_error_reporter()

        # Should be the same instance
        assert reporter1 is reporter2
        assert isinstance(reporter1, EnhancedErrorReporter)

    def test_global_reporter_persists_state(self):
        """Test that global reporter persists state across calls."""
        # Clear the global instance
        import the_alchemiser.shared.errors.error_reporter as reporter_module

        reporter_module._global_enhanced_error_reporter = None

        reporter1 = get_global_error_reporter()
        reporter1.report_error_with_context(
            ValueError("Test error"),
            operation="test",
        )

        reporter2 = get_global_error_reporter()

        # Should have the error from reporter1
        assert len(reporter2.recent_errors) == 1


class TestEnhancedErrorReporterIntegration:
    """Test integration scenarios for error reporter."""

    def test_error_workflow_with_context_preservation(self):
        """Test complete error reporting workflow with context."""
        reporter = EnhancedErrorReporter()

        # Report error with full context
        error = ValueError("Workflow error")
        context = {
            "module": "execution_v2",
            "correlation_id": "corr-123",
            "causation_id": "cause-456",
            "event_id": "evt-789",
        }

        reporter.report_error_with_context(
            error=error,
            context=context,
            operation="order_execution",
        )

        # Verify all context is preserved
        recent = reporter.recent_errors[0]
        assert recent["context"]["correlation_id"] == "corr-123"
        assert recent["context"]["causation_id"] == "cause-456"
        assert recent["operation"] == "order_execution"

        # Verify in summary
        summary = reporter.get_error_summary()
        assert summary["recent_errors_count"] == 1
        assert "ValueError:order_execution" in summary["error_counts"]

    def test_rate_monitoring_over_time(self):
        """Test rate monitoring with time-based cleanup."""
        reporter = EnhancedErrorReporter()

        # Add errors at different times
        old_time = datetime.now(UTC) - timedelta(minutes=6)
        recent_time = datetime.now(UTC)

        # Add old error directly
        reporter.recent_errors.append({
            "timestamp": old_time.isoformat(),
            "error_type": "OldError",
            "message": "Old",
        })

        # Add recent error through normal flow
        reporter.report_error_with_context(
            ValueError("Recent"),
            operation="test",
        )

        # Only recent error should remain
        assert len(reporter.recent_errors) == 1
        assert reporter.recent_errors[0]["error_type"] == "ValueError"


class TestEnhancedErrorReporterSensitiveDataRedaction:
    """Test sensitive data redaction functionality."""

    def test_redact_sensitive_keys(self):
        """Test that sensitive keys are redacted."""
        reporter = EnhancedErrorReporter()
        error = ValueError("Test error")
        context = {
            "operation": "login",
            "password": "secret123",
            "api_key": "key-abc-123",
            "username": "testuser",
        }

        reporter.report_error_with_context(
            error=error,
            context=context,
            operation="auth",
        )

        recent = reporter.recent_errors[0]
        assert recent["context"]["password"] == "[REDACTED]"
        assert recent["context"]["api_key"] == "[REDACTED]"
        assert recent["context"]["username"] == "testuser"

    def test_redact_nested_sensitive_data(self):
        """Test that nested sensitive data is redacted."""
        reporter = EnhancedErrorReporter()
        error = ValueError("Test error")
        context = {
            "operation": "api_call",
            "request": {
                "url": "https://api.example.com",
                "headers": {"authorization": "Bearer token123"},
            },
        }

        reporter.report_error_with_context(error=error, context=context, operation="api")

        recent = reporter.recent_errors[0]
        assert recent["context"]["request"]["headers"]["authorization"] == "[REDACTED]"
        assert recent["context"]["request"]["url"] == "https://api.example.com"

    def test_all_sensitive_keys_redacted(self):
        """Test that all SENSITIVE_KEYS are redacted."""
        reporter = EnhancedErrorReporter()
        error = ValueError("Test")

        # Create context with all sensitive keys
        context = {key: f"secret-{key}" for key in SENSITIVE_KEYS}
        context["safe_field"] = "safe_value"

        reporter.report_error_with_context(error=error, context=context, operation="test")

        recent = reporter.recent_errors[0]
        # All sensitive keys should be redacted
        for key in SENSITIVE_KEYS:
            assert recent["context"][key] == "[REDACTED]"
        # Safe field should remain
        assert recent["context"]["safe_field"] == "safe_value"


class TestEnhancedErrorReporterCorrelationTracking:
    """Test correlation ID and causation ID tracking."""

    def test_extract_correlation_id(self):
        """Test that correlation_id is extracted to top level."""
        reporter = EnhancedErrorReporter()
        error = ValueError("Test error")
        context = {
            "correlation_id": "req-abc-123",
            "module": "execution_v2",
        }

        reporter.report_error_with_context(
            error=error,
            context=context,
            operation="order_processing",
        )

        recent = reporter.recent_errors[0]
        assert recent["correlation_id"] == "req-abc-123"
        assert recent["context"]["correlation_id"] == "req-abc-123"

    def test_extract_causation_id(self):
        """Test that causation_id is extracted to top level."""
        reporter = EnhancedErrorReporter()
        error = ValueError("Test error")
        context = {
            "correlation_id": "req-abc-123",
            "causation_id": "evt-xyz-456",
        }

        reporter.report_error_with_context(
            error=error,
            context=context,
            operation="event_processing",
        )

        recent = reporter.recent_errors[0]
        assert recent["correlation_id"] == "req-abc-123"
        assert recent["causation_id"] == "evt-xyz-456"

    def test_missing_correlation_ids(self):
        """Test handling when correlation IDs are missing."""
        reporter = EnhancedErrorReporter()
        error = ValueError("Test error")
        context = {"module": "test"}

        reporter.report_error_with_context(
            error=error,
            context=context,
            operation="test_op",
        )

        recent = reporter.recent_errors[0]
        assert recent["correlation_id"] is None
        assert recent["causation_id"] is None

    @patch("the_alchemiser.shared.errors.error_reporter.logger")
    def test_correlation_ids_in_warning_log(self, mock_logger):
        """Test that correlation IDs are included in high rate warnings."""
        reporter = EnhancedErrorReporter()

        # Add many errors with correlation IDs
        for i in range(60):
            reporter.report_error_with_context(
                ValueError(f"Error {i}"),
                context={"correlation_id": f"req-{i}"},
                operation="test",
            )

        # Should have logged warning with correlation IDs
        mock_logger.warning.assert_called()
        warning_call = mock_logger.warning.call_args
        assert "High error rate detected" in warning_call[0][0]
        assert "recent_correlation_ids" in warning_call[1]["extra"]


class TestEnhancedErrorReporterErrorCountsCleanup:
    """Test error_counts cleanup to prevent memory leak."""

    def test_error_counts_timestamp_tracking(self):
        """Test that error counts track timestamps."""
        reporter = EnhancedErrorReporter()
        error = ValueError("Test")

        reporter.report_error_with_context(error=error, operation="test")

        assert "ValueError:test" in reporter.error_counts
        assert "ValueError:test" in reporter.error_counts_timestamps
        assert reporter.error_counts_timestamps["ValueError:test"] > 0

    def test_cleanup_old_error_counts(self):
        """Test that old error counts are cleaned up."""
        reporter = EnhancedErrorReporter()

        # Add an old error count
        old_time = datetime.now(UTC).timestamp() - ERROR_COUNTS_CLEANUP_WINDOW_SECONDS - 100
        reporter.error_counts["OldError:test"] = 5
        reporter.error_counts_timestamps["OldError:test"] = old_time

        # Add a recent error
        reporter.report_error_with_context(ValueError("Recent"), operation="test")

        # Old count should be cleaned up
        assert "OldError:test" not in reporter.error_counts
        assert "OldError:test" not in reporter.error_counts_timestamps
        assert "ValueError:test" in reporter.error_counts

    def test_error_counts_summary_reflects_cleanup(self):
        """Test that summary reflects cleaned up counts."""
        reporter = EnhancedErrorReporter()

        # Add old error count
        old_time = datetime.now(UTC).timestamp() - ERROR_COUNTS_CLEANUP_WINDOW_SECONDS - 100
        reporter.error_counts["OldError:old"] = 10
        reporter.error_counts_timestamps["OldError:old"] = old_time

        # Add recent errors
        for i in range(3):
            reporter.report_error_with_context(ValueError(f"Error {i}"), operation="recent")

        summary = reporter.get_error_summary()
        assert "OldError:old" not in summary["error_counts"]
        assert "ValueError:recent" in summary["error_counts"]


class TestEnhancedErrorReporterCriticalErrorsTracking:
    """Test critical errors tracking."""

    @patch("the_alchemiser.shared.errors.error_handler.get_error_handler")
    def test_critical_errors_list_populated(self, mock_get_handler):
        """Test that critical errors are added to critical_errors list."""
        mock_handler = Mock()
        mock_get_handler.return_value = mock_handler

        reporter = EnhancedErrorReporter()
        error = Exception("Critical error")

        reporter.report_error_with_context(
            error=error,
            is_critical=True,
            operation="critical_op",
        )

        # Should have added to critical_errors list
        assert len(reporter.critical_errors) == 1
        assert reporter.critical_errors[0]["is_critical"] is True
        assert reporter.critical_errors[0]["operation"] == "critical_op"

    def test_critical_errors_in_summary(self):
        """Test that critical errors count appears in summary."""
        reporter = EnhancedErrorReporter()

        # Add mix of critical and non-critical errors
        reporter.report_error_with_context(
            ValueError("Normal error"),
            operation="normal",
        )

        # Manually add critical error to list (without triggering handler)
        reporter.critical_errors.append({
            "timestamp": datetime.now(UTC).isoformat(),
            "is_critical": True,
        })

        summary = reporter.get_error_summary()
        assert summary["critical_errors_count"] == 1

    def test_critical_errors_cleanup(self):
        """Test that old critical errors are cleaned up."""
        reporter = EnhancedErrorReporter()

        # Add old critical error
        old_time = datetime.now(UTC) - timedelta(hours=2)
        reporter.critical_errors.append({
            "timestamp": old_time.isoformat(),
            "is_critical": True,
        })

        # Add recent error (triggers cleanup)
        reporter.report_error_with_context(ValueError("Test"), operation="test")

        # Old critical error should be removed
        assert len(reporter.critical_errors) == 0


class TestEnhancedErrorReporterAlertDeduplication:
    """Test alert deduplication functionality."""

    @patch("the_alchemiser.shared.errors.error_reporter.logger")
    def test_alert_deduplication(self, mock_logger):
        """Test that alerts are deduplicated."""
        reporter = EnhancedErrorReporter()

        # Add many errors to trigger rate warning
        for i in range(60):
            reporter.report_error_with_context(ValueError(f"Error {i}"), operation="test")

        # Should have logged warning once
        assert mock_logger.warning.call_count == 1

    @patch("the_alchemiser.shared.errors.error_reporter.logger")
    def test_alert_cooldown(self, mock_logger):
        """Test that alerts respect cooldown period."""
        reporter = EnhancedErrorReporter()

        # Trigger first alert
        for i in range(60):
            reporter.report_error_with_context(ValueError(f"Error {i}"), operation="test")

        first_call_count = mock_logger.warning.call_count

        # Add more errors immediately
        for i in range(20):
            reporter.report_error_with_context(ValueError(f"More {i}"), operation="test")

        # Should not have logged additional warning (cooldown active)
        assert mock_logger.warning.call_count == first_call_count

    @patch("the_alchemiser.shared.errors.error_reporter.logger")
    def test_structured_logging_in_alert(self, mock_logger):
        """Test that alerts use structured logging with extras."""
        reporter = EnhancedErrorReporter()

        # Add many errors
        for i in range(60):
            reporter.report_error_with_context(ValueError(f"Error {i}"), operation="test")

        # Verify structured logging
        warning_call = mock_logger.warning.call_args
        assert "extra" in warning_call[1]
        extras = warning_call[1]["extra"]
        assert "error_rate_per_minute" in extras
        assert "threshold" in extras
        assert "recent_errors_count" in extras
        assert extras["threshold"] == ERROR_RATE_THRESHOLD_PER_MIN


class TestEnhancedErrorReporterTimestampParsing:
    """Test timestamp parsing error handling."""

    def test_malformed_timestamp_handling(self):
        """Test that malformed timestamps don't crash cleanup."""
        reporter = EnhancedErrorReporter()

        # Add error with malformed timestamp
        reporter.recent_errors.append({
            "timestamp": "not-a-timestamp",
            "error_type": "TestError",
        })

        # Should not crash when cleaning up
        reporter.report_error_with_context(ValueError("Test"), operation="test")

        # Should still have the recent error
        assert len(reporter.recent_errors) >= 1

    def test_missing_timestamp_handling(self):
        """Test that missing timestamps don't crash cleanup."""
        reporter = EnhancedErrorReporter()

        # Add error without timestamp
        reporter.recent_errors.append({
            "error_type": "TestError",
        })

        # Should not crash
        reporter.report_error_with_context(ValueError("Test"), operation="test")


class TestEnhancedErrorReporterConstants:
    """Test that constants are properly defined and used."""

    def test_constants_defined(self):
        """Test that all expected constants are defined."""
        assert ERROR_RATE_WINDOW_SECONDS == 300
        assert ERROR_RATE_THRESHOLD_PER_MIN == 10
        assert ERROR_COUNTS_CLEANUP_WINDOW_SECONDS == 3600
        assert SENSITIVE_KEYS is not None
        assert len(SENSITIVE_KEYS) > 0

    def test_error_rate_window_used(self):
        """Test that ERROR_RATE_WINDOW_SECONDS is used in initialization."""
        reporter = EnhancedErrorReporter()
        assert reporter.error_rate_window == ERROR_RATE_WINDOW_SECONDS
