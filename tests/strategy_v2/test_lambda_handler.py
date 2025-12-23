"""Business Unit: strategy_v2 | Status: current.

Integration tests for strategy Lambda handler.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import Mock, patch

import pytest

from the_alchemiser.shared.errors.exceptions import DataProviderError
from the_alchemiser.strategy_v2.lambda_handler import lambda_handler


class TestLambdaHandler:
    """Test suite for strategy Lambda handler."""

    @pytest.fixture
    def mock_event(self) -> dict:
        """Create a mock Lambda event."""
        return {
            "session_id": "test-session-123",
            "correlation_id": "test-correlation-456",
            "dsl_file": "test-strategy.clj",
            "allocation": "100.00",
            "strategy_number": 1,
            "total_strategies": 1,
        }

    def test_handler_returns_400_on_missing_required_fields(self) -> None:
        """Test that handler returns 400 when required fields are missing."""
        event = {"session_id": "test-session"}
        result = lambda_handler(event, None)

        assert result["statusCode"] == 400
        assert "error" in result["body"]
        assert "required fields" in result["body"]["error"].lower()

    def test_handler_publishes_workflow_failed_on_data_provider_error(
        self, mock_event: dict
    ) -> None:
        """Test that handler publishes WorkflowFailed event on DataProviderError."""
        with patch(
            "the_alchemiser.strategy_v2.lambda_handler.DataValidationService"
        ) as mock_validation_service_class:
            mock_service_instance = Mock()
            mock_service_instance.validate_and_refresh_if_needed.side_effect = (
                DataProviderError("Stale data detected and refresh failed")
            )
            mock_validation_service_class.return_value = mock_service_instance

            with patch(
                "the_alchemiser.strategy_v2.lambda_handler.publish_to_eventbridge"
            ) as mock_publish:
                result = lambda_handler(mock_event, None)

                # Verify error response
                assert result["statusCode"] == 500
                assert result["body"]["error_type"] == "DataValidationError"
                assert "Stale data detected and refresh failed" in result["body"]["error"]

                # Verify WorkflowFailed event was published
                mock_publish.assert_called_once()
                published_event = mock_publish.call_args[0][0]
                assert published_event.workflow_type == "signal_generation"
                assert published_event.failure_step == "data_validation"
                assert "Stale data detected and refresh failed" in published_event.failure_reason

    def test_handler_publishes_workflow_failed_on_dsl_file_not_found(
        self, mock_event: dict
    ) -> None:
        """Test that handler publishes WorkflowFailed event when DSL file not found."""
        with patch(
            "the_alchemiser.strategy_v2.lambda_handler.DataValidationService"
        ) as mock_validation_service_class:
            mock_service_instance = Mock()
            mock_service_instance.validate_and_refresh_if_needed.side_effect = (
                FileNotFoundError("DSL file not found")
            )
            mock_validation_service_class.return_value = mock_service_instance

            with patch(
                "the_alchemiser.strategy_v2.lambda_handler.publish_to_eventbridge"
            ) as mock_publish:
                result = lambda_handler(mock_event, None)

                # Verify error response with ConfigurationError type
                assert result["statusCode"] == 500
                assert result["body"]["error_type"] == "ConfigurationError"
                assert "not found" in result["body"]["error"]

                # Verify WorkflowFailed event was published
                mock_publish.assert_called_once()
                published_event = mock_publish.call_args[0][0]
                assert published_event.failure_step == "dsl_configuration"
                assert "not found" in published_event.failure_reason

    def test_handler_handles_generic_exception_during_validation(
        self, mock_event: dict
    ) -> None:
        """Test that handler publishes WorkflowFailed on generic exception."""
        with patch(
            "the_alchemiser.strategy_v2.lambda_handler.DataValidationService"
        ) as mock_validation_service_class:
            mock_service_instance = Mock()
            mock_service_instance.validate_and_refresh_if_needed.side_effect = (
                RuntimeError("Unexpected error")
            )
            mock_validation_service_class.return_value = mock_service_instance

            with patch(
                "the_alchemiser.strategy_v2.lambda_handler.publish_to_eventbridge"
            ) as mock_publish:
                result = lambda_handler(mock_event, None)

                # Verify error response
                assert result["statusCode"] == 500
                assert "error" in result["body"]

                # Verify WorkflowFailed event was published with signal_generation step
                mock_publish.assert_called_once()
                published_event = mock_publish.call_args[0][0]
                assert published_event.failure_step == "signal_generation"

    def test_handler_continues_to_signal_generation_after_validation(
        self, mock_event: dict
    ) -> None:
        """Test that handler proceeds to signal generation after successful validation."""
        with patch(
            "the_alchemiser.strategy_v2.lambda_handler.DataValidationService"
        ) as mock_validation_service_class, patch(
            "the_alchemiser.strategy_v2.lambda_handler.ApplicationContainer"
        ) as mock_container_class, patch(
            "the_alchemiser.strategy_v2.lambda_handler.SingleFileSignalHandler"
        ) as mock_handler_class, patch(
            "the_alchemiser.strategy_v2.lambda_handler.publish_to_eventbridge"
        ) as mock_publish:
            # Setup validation service (success)
            mock_service_instance = Mock()
            mock_validation_service_class.return_value = mock_service_instance

            # Setup signal handler
            mock_signal_handler = Mock()
            mock_signal_handler.generate_signals.return_value = {
                "signals_data": {"AAPL": "BUY 10"},
                "consolidated_portfolio": {"AAPL": 10},
                "signal_count": 1,
            }
            mock_handler_class.return_value = mock_signal_handler

            result = lambda_handler(mock_event, None)

            # Verify validation was called
            mock_service_instance.validate_and_refresh_if_needed.assert_called_once()

            # Verify signal generation was attempted
            mock_signal_handler.generate_signals.assert_called_once()

            # Verify result is success
            assert result["statusCode"] == 200
            assert result["body"]["signal_count"] == 1
