"""Business Unit: data_quality_monitor | Status: current.

Tests for data quality monitor Lambda handler.
"""

from __future__ import annotations

from unittest.mock import Mock, patch

from the_alchemiser.data_quality_monitor.lambda_handler import lambda_handler
from the_alchemiser.data_quality_monitor.quality_checker import ValidationResult


class TestLambdaHandler:
    """Test suite for Lambda handler."""

    @patch("the_alchemiser.data_quality_monitor.lambda_handler.DataQualityChecker")
    def test_handler_success_all_symbols_pass(
        self,
        mock_checker_class: Mock,
    ) -> None:
        """Test handler when all symbols pass validation."""
        # Arrange
        mock_checker = Mock()
        mock_checker_class.return_value = mock_checker

        # Mock validation results (all pass)
        mock_checker.validate_all_symbols.return_value = {
            "AAPL": ValidationResult(
                symbol="AAPL",
                passed=True,
                issues=[],
                rows_checked=5,
                external_source="yfinance",
            ),
            "GOOGL": ValidationResult(
                symbol="GOOGL",
                passed=True,
                issues=[],
                rows_checked=5,
                external_source="yfinance",
            ),
        }

        event = {}
        context = Mock()

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 200
        assert response["body"]["status"] == "success"
        assert response["body"]["total_symbols"] == 2
        assert response["body"]["passed"] == 2
        assert response["body"]["issues_found"] == 0

    @patch("the_alchemiser.data_quality_monitor.lambda_handler.DataQualityChecker")
    def test_handler_detects_issues(
        self,
        mock_checker_class: Mock,
    ) -> None:
        """Test handler when some symbols fail validation."""
        # Arrange
        mock_checker = Mock()
        mock_checker_class.return_value = mock_checker

        # Mock validation results (one fails)
        mock_checker.validate_all_symbols.return_value = {
            "AAPL": ValidationResult(
                symbol="AAPL",
                passed=True,
                issues=[],
                rows_checked=5,
                external_source="yfinance",
            ),
            "GOOGL": ValidationResult(
                symbol="GOOGL",
                passed=False,
                issues=["Data is stale", "Missing 1 recent trading day"],
                rows_checked=3,
                external_source="yfinance",
            ),
        }

        event = {}
        context = Mock()

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 200
        assert response["body"]["status"] == "issues_detected"
        assert response["body"]["total_symbols"] == 2
        assert response["body"]["passed"] == 1
        assert response["body"]["failed"] == 1
        assert "GOOGL" in response["body"]["failed_symbols"]
        assert len(response["body"]["issues"]) == 2

    @patch("the_alchemiser.data_quality_monitor.lambda_handler.DataQualityChecker")
    def test_handler_specific_symbols(
        self,
        mock_checker_class: Mock,
    ) -> None:
        """Test handler with specific symbols in event."""
        # Arrange
        mock_checker = Mock()
        mock_checker_class.return_value = mock_checker

        # Mock validation results
        mock_checker.validate_symbols.return_value = {
            "MSFT": ValidationResult(
                symbol="MSFT",
                passed=True,
                issues=[],
                rows_checked=10,
                external_source="yfinance",
            ),
        }

        event = {"symbols": ["MSFT"], "lookback_days": 10}
        context = Mock()

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 200
        mock_checker.validate_symbols.assert_called_once_with(
            symbols=["MSFT"],
            lookback_days=10,
        )

    @patch("the_alchemiser.data_quality_monitor.lambda_handler.DataQualityChecker")
    @patch("the_alchemiser.data_quality_monitor.lambda_handler.publish_to_eventbridge")
    def test_handler_exception_handling(
        self,
        mock_publish: Mock,
        mock_checker_class: Mock,
    ) -> None:
        """Test handler exception handling."""
        # Arrange
        mock_checker = Mock()
        mock_checker_class.return_value = mock_checker

        # Mock exception
        mock_checker.validate_all_symbols.side_effect = Exception("Test error")

        event = {}
        context = Mock()

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["statusCode"] == 500
        assert response["body"]["status"] == "error"
        assert "Test error" in response["body"]["error"]

        # Verify WorkflowFailed event was published
        mock_publish.assert_called_once()
        workflow_failed_event = mock_publish.call_args[0][0]
        assert workflow_failed_event.workflow_type == "data_quality_check"
        assert workflow_failed_event.failure_reason == "Test error"

    @patch("the_alchemiser.data_quality_monitor.lambda_handler.DataQualityChecker")
    def test_handler_includes_correlation_id(
        self,
        mock_checker_class: Mock,
    ) -> None:
        """Test that handler includes correlation ID in response."""
        # Arrange
        mock_checker = Mock()
        mock_checker_class.return_value = mock_checker
        mock_checker.validate_all_symbols.return_value = {}

        event = {"correlation_id": "test-correlation-123"}
        context = Mock()

        # Act
        response = lambda_handler(event, context)

        # Assert
        assert response["body"]["correlation_id"] == "test-correlation-123"
