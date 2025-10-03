"""Business Unit: shared | Status: current.

Tests for error reporter module with rate monitoring and aggregation.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from the_alchemiser.shared.errors.error_reporter import (
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
