"""Business Unit: notifications | Status: current.

Unit tests for notifications Lambda handler.

Tests the event unwrapping and routing logic to ensure EventBridge events
are correctly parsed and dispatched to the appropriate handlers.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest


class TestLambdaHandlerEventParsing:
    """Tests for EventBridge event parsing in lambda_handler."""

    @pytest.fixture
    def trade_executed_event(self) -> dict[str, Any]:
        """Create a sample TradeExecuted EventBridge event."""
        return {
            "version": "0",
            "id": str(uuid4()),
            "detail-type": "TradeExecuted",
            "source": "alchemiser.execution",
            "time": "2025-01-01T00:00:00Z",
            "region": "us-east-1",
            "detail": {
                "correlation_id": "test-correlation-id",
                "event_id": "test-event-id",
                "orders_placed": 3,
                "orders_succeeded": 3,
                "orders_executed": [
                    {"symbol": "AAPL", "qty": 10, "filled_value": 1500.00}
                ],
                "execution_summary": {
                    "total_trade_value": 1500.00,
                },
            },
        }

    @pytest.fixture
    def workflow_failed_event(self) -> dict[str, Any]:
        """Create a sample WorkflowFailed EventBridge event."""
        return {
            "version": "0",
            "id": str(uuid4()),
            "detail-type": "WorkflowFailed",
            "source": "alchemiser.execution",
            "time": "2025-01-01T00:00:00Z",
            "region": "us-east-1",
            "detail": {
                "correlation_id": "test-correlation-id",
                "event_id": "test-event-id",
                "workflow_type": "rebalance",
                "failure_reason": "API timeout",
                "failure_step": "order_submission",
                "error_details": {
                    "exception_type": "TimeoutError",
                },
            },
        }

    @pytest.fixture
    def unknown_event(self) -> dict[str, Any]:
        """Create an unknown event type for testing ignore logic."""
        return {
            "version": "0",
            "id": str(uuid4()),
            "detail-type": "SomeOtherEvent",
            "source": "alchemiser.other",
            "time": "2025-01-01T00:00:00Z",
            "region": "us-east-1",
            "detail": {
                "correlation_id": "test-correlation-id",
            },
        }

    @patch("the_alchemiser.notifications_v2.lambda_handler._handle_trade_executed")
    def test_routes_trade_executed_event(
        self, mock_handler: MagicMock, trade_executed_event: dict[str, Any]
    ) -> None:
        """Test that TradeExecuted events are routed to the correct handler."""
        from the_alchemiser.notifications_v2.lambda_handler import lambda_handler

        mock_handler.return_value = {"statusCode": 200, "body": "OK"}

        result = lambda_handler(trade_executed_event, None)

        mock_handler.assert_called_once()
        # Verify the detail was correctly extracted
        call_args = mock_handler.call_args
        detail = call_args[0][0]
        assert detail["correlation_id"] == "test-correlation-id"
        assert result["statusCode"] == 200

    @patch("the_alchemiser.notifications_v2.lambda_handler._handle_workflow_failed")
    def test_routes_workflow_failed_event(
        self, mock_handler: MagicMock, workflow_failed_event: dict[str, Any]
    ) -> None:
        """Test that WorkflowFailed events are routed to the correct handler."""
        from the_alchemiser.notifications_v2.lambda_handler import lambda_handler

        mock_handler.return_value = {"statusCode": 200, "body": "OK"}

        result = lambda_handler(workflow_failed_event, None)

        mock_handler.assert_called_once()
        # Verify the detail was correctly extracted
        call_args = mock_handler.call_args
        detail = call_args[0][0]
        correlation_id = call_args[0][1]
        source = call_args[0][2]
        assert detail["correlation_id"] == "test-correlation-id"
        assert correlation_id == "test-correlation-id"
        assert source == "alchemiser.execution"
        assert result["statusCode"] == 200

    def test_ignores_unknown_event_type(self, unknown_event: dict[str, Any]) -> None:
        """Test that unknown event types are ignored gracefully."""
        from the_alchemiser.notifications_v2.lambda_handler import lambda_handler

        result = lambda_handler(unknown_event, None)

        assert result["statusCode"] == 200
        assert "Ignored event type" in result["body"]
        assert "SomeOtherEvent" in result["body"]

    def test_extracts_detail_type_from_envelope(
        self, trade_executed_event: dict[str, Any]
    ) -> None:
        """Test that detail-type is extracted from the EventBridge envelope.

        This is a regression test for the bug where unwrap_eventbridge_event
        was returning only the detail, causing detail-type to be empty.
        """
        from the_alchemiser.notifications_v2.lambda_handler import lambda_handler

        with patch(
            "the_alchemiser.notifications_v2.lambda_handler._handle_trade_executed"
        ) as mock_handler:
            mock_handler.return_value = {"statusCode": 200, "body": "OK"}

            # The handler should correctly extract detail-type from the envelope
            # and route to _handle_trade_executed
            lambda_handler(trade_executed_event, None)

            # If this is called, detail-type was correctly extracted
            assert mock_handler.called, (
                "Handler not called - detail-type extraction failed"
            )

    def test_extracts_source_for_workflow_failed(
        self, workflow_failed_event: dict[str, Any]
    ) -> None:
        """Test that source is correctly passed to WorkflowFailed handler."""
        from the_alchemiser.notifications_v2.lambda_handler import lambda_handler

        with patch(
            "the_alchemiser.notifications_v2.lambda_handler._handle_workflow_failed"
        ) as mock_handler:
            mock_handler.return_value = {"statusCode": 200, "body": "OK"}

            lambda_handler(workflow_failed_event, None)

            # Verify source was passed to handler
            call_args = mock_handler.call_args
            source = call_args[0][2]
            assert source == "alchemiser.execution"


class TestLambdaHandlerErrorHandling:
    """Tests for error handling in lambda_handler."""

    def test_handles_exception_gracefully(self) -> None:
        """Test that exceptions don't propagate and return 500."""
        from the_alchemiser.notifications_v2.lambda_handler import lambda_handler

        # Malformed event that will cause an error
        malformed_event = {
            "version": "0",
            "id": str(uuid4()),
            "detail-type": "TradeExecuted",
            "source": "alchemiser.execution",
            "detail": {
                # Missing required fields for TradingNotificationRequested
            },
        }

        with patch(
            "the_alchemiser.notifications_v2.lambda_handler._handle_trade_executed"
        ) as mock_handler:
            mock_handler.side_effect = Exception("Test error")

            result = lambda_handler(malformed_event, None)

            # Should return 500 but not raise
            assert result["statusCode"] == 500
            assert "Test error" in result["body"]
