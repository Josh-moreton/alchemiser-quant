#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Comprehensive test suite for error schema DTOs.

Tests cover validation, immutability, serialization/deserialization,
and edge cases for all error reporting and notification schemas.
"""

import pytest
from pydantic import ValidationError

from the_alchemiser.shared.schemas.errors import (
    ErrorDetailInfo,
    ErrorNotificationData,
    ErrorReportSummary,
    ErrorSummaryData,
)


@pytest.mark.unit
class TestErrorDetailInfo:
    """Test ErrorDetailInfo schema."""

    def test_create_with_all_required_fields(self):
        """Test creating ErrorDetailInfo with all required fields."""
        error = ErrorDetailInfo(
            error_type="ValueError",
            error_message="Invalid input",
            category="trading",
            context="order_execution",
            component="execution_v2",
            timestamp="2025-10-08T12:00:00+00:00",
            traceback="Traceback line 1\nTraceback line 2",
        )

        assert error.error_type == "ValueError"
        assert error.error_message == "Invalid input"
        assert error.category == "trading"
        assert error.context == "order_execution"
        assert error.component == "execution_v2"
        assert error.timestamp == "2025-10-08T12:00:00+00:00"
        assert error.traceback == "Traceback line 1\nTraceback line 2"
        assert error.additional_data == {}
        assert error.suggested_action is None

    def test_create_with_optional_fields(self):
        """Test creating ErrorDetailInfo with optional fields."""
        error = ErrorDetailInfo(
            error_type="OrderExecutionError",
            error_message="Insufficient funds",
            category="trading",
            context="place_order",
            component="execution_v2",
            timestamp="2025-10-08T12:00:00+00:00",
            traceback="Full traceback",
            additional_data={"symbol": "AAPL", "quantity": 10},
            suggested_action="Increase account balance",
        )

        assert error.additional_data == {"symbol": "AAPL", "quantity": 10}
        assert error.suggested_action == "Increase account balance"

    def test_immutability(self):
        """Test that ErrorDetailInfo is frozen."""
        error = ErrorDetailInfo(
            error_type="ValueError",
            error_message="Test",
            category="trading",
            context="test",
            component="test",
            timestamp="2025-10-08T12:00:00+00:00",
            traceback="traceback",
        )

        with pytest.raises(ValidationError, match="Instance is frozen"):
            error.error_type = "TypeError"  # type: ignore

    def test_extra_fields_are_ignored(self):
        """Test that extra fields are silently ignored (not forbidden).

        Note: ConfigDict has strict=True and frozen=True but not extra='forbid',
        so extra fields are ignored rather than raising an error. This is
        documented as a Medium severity finding in the file review.
        """
        error = ErrorDetailInfo(
            error_type="ValueError",
            error_message="Test",
            category="trading",
            context="test",
            component="test",
            timestamp="2025-10-08T12:00:00+00:00",
            traceback="traceback",
            unexpected_field="not_allowed",  # type: ignore
        )
        # Extra field is ignored, model is created successfully
        assert error.error_type == "ValueError"
        assert not hasattr(error, "unexpected_field")

    def test_serialization_to_dict(self):
        """Test model_dump() serialization."""
        error = ErrorDetailInfo(
            error_type="ValueError",
            error_message="Test error",
            category="data",
            context="data_fetch",
            component="market_data",
            timestamp="2025-10-08T12:00:00+00:00",
            traceback="line 1\nline 2",
            additional_data={"source": "alpaca"},
        )

        data = error.model_dump()
        assert data["error_type"] == "ValueError"
        assert data["error_message"] == "Test error"
        assert data["category"] == "data"
        assert data["additional_data"] == {"source": "alpaca"}
        assert data["suggested_action"] is None

    def test_deserialization_from_dict(self):
        """Test model_validate() deserialization."""
        data = {
            "error_type": "ConfigurationError",
            "error_message": "Missing API key",
            "category": "configuration",
            "context": "initialization",
            "component": "config_loader",
            "timestamp": "2025-10-08T12:00:00+00:00",
            "traceback": "config.py line 45",
            "additional_data": {"config_file": ".env"},
            "suggested_action": "Set ALPACA_API_KEY environment variable",
        }

        error = ErrorDetailInfo.model_validate(data)
        assert error.error_type == "ConfigurationError"
        assert error.suggested_action == "Set ALPACA_API_KEY environment variable"

    def test_missing_required_field_raises_error(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError, match="Field required"):
            ErrorDetailInfo(
                error_type="ValueError",
                error_message="Test",
                category="trading",
                # Missing context, component, timestamp, traceback
            )  # type: ignore


@pytest.mark.unit
class TestErrorSummaryData:
    """Test ErrorSummaryData schema."""

    def test_create_with_empty_errors_list(self):
        """Test creating ErrorSummaryData with empty errors list."""
        summary = ErrorSummaryData(count=0, errors=[])

        assert summary.count == 0
        assert summary.errors == []

    def test_create_with_error_details(self):
        """Test creating ErrorSummaryData with error details."""
        error1 = ErrorDetailInfo(
            error_type="ValueError",
            error_message="Error 1",
            category="trading",
            context="test",
            component="test",
            timestamp="2025-10-08T12:00:00+00:00",
            traceback="trace1",
        )
        error2 = ErrorDetailInfo(
            error_type="TypeError",
            error_message="Error 2",
            category="trading",
            context="test",
            component="test",
            timestamp="2025-10-08T12:01:00+00:00",
            traceback="trace2",
        )

        summary = ErrorSummaryData(count=2, errors=[error1, error2])

        assert summary.count == 2
        assert len(summary.errors) == 2
        assert summary.errors[0].error_type == "ValueError"
        assert summary.errors[1].error_type == "TypeError"

    def test_count_validation_non_negative(self):
        """Test that count must be non-negative."""
        with pytest.raises(ValidationError, match="greater than or equal to 0"):
            ErrorSummaryData(count=-1, errors=[])

    def test_immutability(self):
        """Test that ErrorSummaryData is frozen."""
        summary = ErrorSummaryData(count=0, errors=[])

        with pytest.raises(ValidationError, match="Instance is frozen"):
            summary.count = 5  # type: ignore

    def test_serialization_with_nested_errors(self):
        """Test serialization with nested ErrorDetailInfo objects."""
        error = ErrorDetailInfo(
            error_type="ValueError",
            error_message="Nested error",
            category="strategy",
            context="signal_generation",
            component="strategy_v2",
            timestamp="2025-10-08T12:00:00+00:00",
            traceback="strategy.py line 100",
        )
        summary = ErrorSummaryData(count=1, errors=[error])

        data = summary.model_dump()
        assert data["count"] == 1
        assert len(data["errors"]) == 1
        assert data["errors"][0]["error_type"] == "ValueError"

    def test_default_empty_list(self):
        """Test that errors defaults to empty list."""
        summary = ErrorSummaryData(count=0)
        assert summary.errors == []


@pytest.mark.unit
class TestErrorReportSummary:
    """Test ErrorReportSummary schema."""

    def test_create_with_all_none(self):
        """Test creating ErrorReportSummary with all categories None."""
        summary = ErrorReportSummary()

        assert summary.critical is None
        assert summary.trading is None
        assert summary.data is None
        assert summary.strategy is None
        assert summary.configuration is None
        assert summary.notification is None
        assert summary.warning is None

    def test_create_with_some_categories(self):
        """Test creating ErrorReportSummary with some categories populated."""
        critical_summary = ErrorSummaryData(count=1, errors=[])
        trading_summary = ErrorSummaryData(count=2, errors=[])

        summary = ErrorReportSummary(
            critical=critical_summary,
            trading=trading_summary,
        )

        assert summary.critical is not None
        assert summary.critical.count == 1
        assert summary.trading is not None
        assert summary.trading.count == 2
        assert summary.data is None
        assert summary.strategy is None

    def test_create_with_all_categories(self):
        """Test creating ErrorReportSummary with all categories."""
        summary = ErrorReportSummary(
            critical=ErrorSummaryData(count=1),
            trading=ErrorSummaryData(count=2),
            data=ErrorSummaryData(count=3),
            strategy=ErrorSummaryData(count=4),
            configuration=ErrorSummaryData(count=5),
            notification=ErrorSummaryData(count=6),
            warning=ErrorSummaryData(count=7),
        )

        assert summary.critical.count == 1  # type: ignore
        assert summary.trading.count == 2  # type: ignore
        assert summary.data.count == 3  # type: ignore
        assert summary.strategy.count == 4  # type: ignore
        assert summary.configuration.count == 5  # type: ignore
        assert summary.notification.count == 6  # type: ignore
        assert summary.warning.count == 7  # type: ignore

    def test_immutability(self):
        """Test that ErrorReportSummary is frozen."""
        summary = ErrorReportSummary()

        with pytest.raises(ValidationError, match="Instance is frozen"):
            summary.critical = ErrorSummaryData(count=1)  # type: ignore

    def test_serialization(self):
        """Test serialization of ErrorReportSummary."""
        summary = ErrorReportSummary(
            critical=ErrorSummaryData(count=1),
            trading=ErrorSummaryData(count=2),
        )

        data = summary.model_dump()
        assert data["critical"]["count"] == 1
        assert data["trading"]["count"] == 2
        assert data["data"] is None

    def test_deserialization(self):
        """Test deserialization of ErrorReportSummary."""
        data = {
            "critical": {"count": 1, "errors": []},
            "trading": {"count": 2, "errors": []},
            "data": None,
            "strategy": None,
            "configuration": None,
            "notification": None,
            "warning": None,
        }

        summary = ErrorReportSummary.model_validate(data)
        assert summary.critical.count == 1  # type: ignore
        assert summary.trading.count == 2  # type: ignore
        assert summary.data is None


@pytest.mark.unit
class TestErrorNotificationData:
    """Test ErrorNotificationData schema."""

    def test_create_with_all_required_fields(self):
        """Test creating ErrorNotificationData with all required fields."""
        notification = ErrorNotificationData(
            severity="high",
            priority="urgent",
            title="Critical Trading Error",
            error_report="Detailed error report text",
            html_content="<html>Error details</html>",
            success=True,
            email_sent=True,
        )

        assert notification.severity == "high"
        assert notification.priority == "urgent"
        assert notification.title == "Critical Trading Error"
        assert notification.error_report == "Detailed error report text"
        assert notification.html_content == "<html>Error details</html>"
        assert notification.success is True
        assert notification.email_sent is True
        assert notification.correlation_id is None
        assert notification.event_id is None

    def test_create_with_optional_tracing_fields(self):
        """Test creating ErrorNotificationData with event tracing fields."""
        notification = ErrorNotificationData(
            severity="medium",
            priority="normal",
            title="Trading Warning",
            error_report="Warning message",
            html_content="<p>Warning</p>",
            success=True,
            email_sent=False,
            correlation_id="corr-123-456",
            event_id="event-789",
        )

        assert notification.correlation_id == "corr-123-456"
        assert notification.event_id == "event-789"

    def test_immutability(self):
        """Test that ErrorNotificationData is frozen."""
        notification = ErrorNotificationData(
            severity="low",
            priority="normal",
            title="Test",
            error_report="Test report",
            html_content="<p>Test</p>",
            success=True,
            email_sent=False,
        )

        with pytest.raises(ValidationError, match="Instance is frozen"):
            notification.severity = "high"  # type: ignore

    def test_serialization(self):
        """Test model_dump() serialization."""
        notification = ErrorNotificationData(
            severity="critical",
            priority="urgent",
            title="System Failure",
            error_report="Complete system failure",
            html_content="<html><body>Error</body></html>",
            success=False,
            email_sent=False,
            correlation_id="corr-999",
        )

        data = notification.model_dump()
        assert data["severity"] == "critical"
        assert data["priority"] == "urgent"
        assert data["success"] is False
        assert data["correlation_id"] == "corr-999"
        assert data["event_id"] is None

    def test_deserialization(self):
        """Test model_validate() deserialization."""
        data = {
            "severity": "high",
            "priority": "urgent",
            "title": "Error Alert",
            "error_report": "Report text",
            "html_content": "<html>HTML</html>",
            "success": True,
            "email_sent": True,
            "correlation_id": "corr-abc",
            "event_id": "event-xyz",
        }

        notification = ErrorNotificationData.model_validate(data)
        assert notification.severity == "high"
        assert notification.correlation_id == "corr-abc"
        assert notification.event_id == "event-xyz"

    def test_boolean_fields(self):
        """Test boolean field handling."""
        # Test with True values
        notification1 = ErrorNotificationData(
            severity="low",
            priority="normal",
            title="Test",
            error_report="Report",
            html_content="<p>Test</p>",
            success=True,
            email_sent=True,
        )
        assert notification1.success is True
        assert notification1.email_sent is True

        # Test with False values
        notification2 = ErrorNotificationData(
            severity="low",
            priority="normal",
            title="Test",
            error_report="Report",
            html_content="<p>Test</p>",
            success=False,
            email_sent=False,
        )
        assert notification2.success is False
        assert notification2.email_sent is False

    def test_missing_required_field_raises_error(self):
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError, match="Field required"):
            ErrorNotificationData(
                severity="high",
                priority="urgent",
                title="Test",
                # Missing error_report, html_content, success, email_sent
            )  # type: ignore


@pytest.mark.unit
class TestComplexNestedScenarios:
    """Test complex scenarios with nested schemas."""

    def test_full_error_report_workflow(self):
        """Test creating a complete error report with all nested structures."""
        # Create error details
        error1 = ErrorDetailInfo(
            error_type="InsufficientFundsError",
            error_message="Account balance too low",
            category="trading",
            context="order_placement",
            component="execution_v2",
            timestamp="2025-10-08T12:00:00+00:00",
            traceback="execution.py line 150",
            additional_data={"symbol": "AAPL", "required": 1000, "available": 500},
            suggested_action="Deposit more funds",
        )

        error2 = ErrorDetailInfo(
            error_type="MarketDataError",
            error_message="Quote stale",
            category="data",
            context="price_fetch",
            component="market_data",
            timestamp="2025-10-08T12:01:00+00:00",
            traceback="market_data.py line 200",
        )

        # Create summaries
        trading_summary = ErrorSummaryData(count=1, errors=[error1])
        data_summary = ErrorSummaryData(count=1, errors=[error2])

        # Create full report
        report = ErrorReportSummary(
            trading=trading_summary,
            data=data_summary,
        )

        # Verify structure
        assert report.trading is not None
        assert report.trading.count == 1
        assert len(report.trading.errors) == 1
        assert report.trading.errors[0].error_type == "InsufficientFundsError"

        assert report.data is not None
        assert report.data.count == 1
        assert report.data.errors[0].additional_data == {}

        # Test serialization of complete structure
        data = report.model_dump()
        assert data["trading"]["count"] == 1
        assert data["trading"]["errors"][0]["suggested_action"] == "Deposit more funds"
        assert data["data"]["count"] == 1

    def test_empty_report_summary(self):
        """Test creating an empty error report summary."""
        report = ErrorReportSummary()
        data = report.model_dump()

        # All categories should be None
        for category in [
            "critical",
            "trading",
            "data",
            "strategy",
            "configuration",
            "notification",
            "warning",
        ]:
            assert data[category] is None

    def test_serialization_roundtrip(self):
        """Test that serialization and deserialization preserves data."""
        original = ErrorDetailInfo(
            error_type="TestError",
            error_message="Test message",
            category="warning",
            context="test_context",
            component="test_component",
            timestamp="2025-10-08T12:00:00+00:00",
            traceback="test traceback",
            additional_data={"key": "value", "count": 42},
            suggested_action="Test action",
        )

        # Serialize
        data = original.model_dump()

        # Deserialize
        restored = ErrorDetailInfo.model_validate(data)

        # Verify all fields match
        assert restored.error_type == original.error_type
        assert restored.error_message == original.error_message
        assert restored.category == original.category
        assert restored.context == original.context
        assert restored.component == original.component
        assert restored.timestamp == original.timestamp
        assert restored.traceback == original.traceback
        assert restored.additional_data == original.additional_data
        assert restored.suggested_action == original.suggested_action
