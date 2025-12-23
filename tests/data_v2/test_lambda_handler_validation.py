"""Business Unit: data | Status: current.

Integration tests for data Lambda handler validation feature.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

import pytest


class TestDataLambdaHandlerValidation:
    """Tests for data validation in lambda_handler."""

    @pytest.fixture
    def validation_schedule_event(self) -> dict[str, Any]:
        """Create a sample validation schedule EventBridge event."""
        return {
            "version": "0",
            "id": str(uuid4()),
            "detail-type": "Scheduled Event",
            "source": "aws.events",
            "time": "2025-01-01T20:00:00Z",
            "region": "us-east-1",
            "resources": [
                "arn:aws:events:us-east-1:123456789012:rule/DataValidationSchedule"
            ],
            "detail": {},
        }

    @pytest.fixture
    def manual_validation_event(self) -> dict[str, Any]:
        """Create a manual validation trigger event."""
        return {
            "validation_trigger": True,
            "symbols": ["AAPL", "MSFT"],
            "lookback_days": 5,
            "correlation_id": "test-validation-123",
        }

    def test_validation_event_detection_schedule(
        self, validation_schedule_event: dict[str, Any]
    ) -> None:
        """Test that scheduled validation events are correctly detected."""
        from the_alchemiser.data_v2.lambda_handler import _is_validation_event

        # Act
        is_validation = _is_validation_event(validation_schedule_event)

        # Assert
        assert is_validation is True

    def test_validation_event_detection_manual(
        self, manual_validation_event: dict[str, Any]
    ) -> None:
        """Test that manual validation events are correctly detected."""
        from the_alchemiser.data_v2.lambda_handler import _is_validation_event

        # Act
        is_validation = _is_validation_event(manual_validation_event)

        # Assert
        assert is_validation is True

    def test_validation_handler_success(
        self, validation_schedule_event: dict[str, Any]
    ) -> None:
        """Test successful validation run."""
        from the_alchemiser.data_v2.data_quality_validator import ValidationResult

        # Mock the validator and its methods
        mock_validation_result = ValidationResult(
            symbols_checked=10,
            symbols_passed=9,
            symbols_failed=1,
            discrepancies=[],
            validation_date="2025-01-01",
        )

        mock_report_path = Mock()
        mock_report_path.unlink = Mock()

        with (
            patch(
                "the_alchemiser.data_v2.lambda_handler.MarketDataStore"
            ) as mock_store_class,
            patch(
                "the_alchemiser.data_v2.lambda_handler.DataQualityValidator"
            ) as mock_validator_class,
            patch(
                "the_alchemiser.data_v2.lambda_handler.publish_to_eventbridge"
            ) as mock_publish,
        ):
            # Setup mocks
            mock_store = Mock()
            mock_store_class.return_value = mock_store

            mock_validator = Mock()
            mock_validator_class.return_value = mock_validator
            mock_validator.validate_all_symbols.return_value = mock_validation_result
            mock_validator.generate_report_csv.return_value = mock_report_path
            mock_validator.upload_report_to_s3.return_value = (
                "data-quality-reports/2025-01-01_validation_report.csv"
            )

            # Import and call handler
            from the_alchemiser.data_v2.lambda_handler import lambda_handler

            # Act
            response = lambda_handler(validation_schedule_event, None)

            # Assert
            assert response["statusCode"] == 200
            assert response["body"]["status"] == "success"
            assert response["body"]["symbols_checked"] == 10
            assert response["body"]["symbols_passed"] == 9
            assert response["body"]["symbols_failed"] == 1

            # Verify validator was called
            mock_validator.validate_all_symbols.assert_called_once()
            mock_validator.generate_report_csv.assert_called_once_with(
                mock_validation_result
            )
            mock_validator.upload_report_to_s3.assert_called_once()

            # Verify event was published
            mock_publish.assert_called_once()

    def test_validation_handler_manual_invocation(
        self, manual_validation_event: dict[str, Any]
    ) -> None:
        """Test manual validation with specific symbols."""
        from the_alchemiser.data_v2.data_quality_validator import ValidationResult

        mock_validation_result = ValidationResult(
            symbols_checked=2,
            symbols_passed=2,
            symbols_failed=0,
            discrepancies=[],
            validation_date="2025-01-01",
        )

        mock_report_path = Mock()
        mock_report_path.unlink = Mock()

        with (
            patch(
                "the_alchemiser.data_v2.lambda_handler.MarketDataStore"
            ) as mock_store_class,
            patch(
                "the_alchemiser.data_v2.lambda_handler.DataQualityValidator"
            ) as mock_validator_class,
            patch(
                "the_alchemiser.data_v2.lambda_handler.publish_to_eventbridge"
            ) as mock_publish,
        ):
            # Setup mocks
            mock_store = Mock()
            mock_store_class.return_value = mock_store

            mock_validator = Mock()
            mock_validator_class.return_value = mock_validator
            mock_validator.validate_all_symbols.return_value = mock_validation_result
            mock_validator.generate_report_csv.return_value = mock_report_path
            mock_validator.upload_report_to_s3.return_value = (
                "data-quality-reports/2025-01-01_validation_report.csv"
            )

            # Import and call handler
            from the_alchemiser.data_v2.lambda_handler import lambda_handler

            # Act
            response = lambda_handler(manual_validation_event, None)

            # Assert
            assert response["statusCode"] == 200
            assert response["body"]["status"] == "success"

            # Verify validator was called with specific symbols
            mock_validator.validate_all_symbols.assert_called_once_with(
                symbols=["AAPL", "MSFT"], lookback_days=5
            )

    def test_validation_handler_error(
        self, validation_schedule_event: dict[str, Any]
    ) -> None:
        """Test validation handler error handling."""
        with (
            patch(
                "the_alchemiser.data_v2.lambda_handler.MarketDataStore"
            ) as mock_store_class,
            patch(
                "the_alchemiser.data_v2.lambda_handler.publish_to_eventbridge"
            ) as mock_publish,
        ):
            # Setup mock to raise exception
            mock_store_class.side_effect = Exception("S3 connection error")

            # Import and call handler
            from the_alchemiser.data_v2.lambda_handler import lambda_handler

            # Act
            response = lambda_handler(validation_schedule_event, None)

            # Assert
            assert response["statusCode"] == 500
            assert response["body"]["status"] == "error"
            assert "S3 connection error" in response["body"]["error"]

            # Verify failure event was published
            mock_publish.assert_called_once()
            published_event = mock_publish.call_args[0][0]
            assert published_event.event_type == "WorkflowFailed"
            assert published_event.workflow_type == "data_validation"
