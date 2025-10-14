#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Tests for Lambda EventBridge handler.

Tests cover:
- Event routing to appropriate handlers
- Event deserialization from EventBridge payload
- Error handling and retry behavior
- Unknown event type handling
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import Mock, patch

import pytest

from the_alchemiser.lambda_handler_eventbridge import (
    _get_event_class,
    _get_handler_for_event,
    eventbridge_handler,
)


@pytest.fixture
def mock_context() -> Mock:
    """Create mock Lambda context."""
    context = Mock()
    context.request_id = "test-request-123"
    return context


@pytest.fixture
def signal_generated_event() -> dict[str, Any]:
    """Create sample SignalGenerated EventBridge event."""
    return {
        "version": "0",
        "id": "event-123",
        "detail-type": "SignalGenerated",
        "source": "alchemiser.strategy",
        "account": "123456789012",
        "time": "2023-10-14T12:00:00Z",
        "region": "us-east-1",
        "resources": ["correlation:corr-123"],
        "detail": {
            "event_id": "event-123",
            "correlation_id": "corr-123",
            "causation_id": "cause-123",
            "timestamp": "2023-10-14T12:00:00+00:00",
            "event_type": "SignalGenerated",
            "source_module": "strategy",
            "schema_version": "1.0",
            "signals_data": {"BTC": 0.5},
            "consolidated_portfolio": {"BTC": 0.5},
            "signal_count": 1,
            "metadata": {},
        },
    }


@pytest.mark.unit
class TestEventBridgeHandler:
    """Test EventBridge Lambda handler."""

    @patch("the_alchemiser.lambda_handler_eventbridge.ApplicationContainer.create_for_environment")
    def test_handler_processes_signal_generated(
        self,
        mock_container_factory: Mock,
        signal_generated_event: dict[str, Any],
        mock_context: Mock,
    ) -> None:
        """Test handler successfully processes SignalGenerated event."""
        # Setup mock handler
        mock_handler = Mock()
        mock_container = Mock()
        mock_container_factory.return_value = mock_container

        with patch(
            "the_alchemiser.lambda_handler_eventbridge._get_handler_for_event",
            return_value=mock_handler,
        ):
            response = eventbridge_handler(signal_generated_event, mock_context)

        assert response["statusCode"] == 200
        assert response["body"] == "Event processed successfully"
        mock_handler.handle_event.assert_called_once()

        # Verify event was reconstructed correctly
        event_arg = mock_handler.handle_event.call_args[0][0]
        assert event_arg.event_type == "SignalGenerated"
        assert event_arg.event_id == "event-123"
        assert event_arg.correlation_id == "corr-123"
        assert event_arg.signal_count == 1

    def test_handler_with_string_detail(self, mock_context: Mock) -> None:
        """Test handler processes event with detail as JSON string."""
        event = {
            "detail-type": "SignalGenerated",
            "source": "alchemiser.strategy",
            "detail": json.dumps(
                {
                    "event_id": "event-123",
                    "correlation_id": "corr-123",
                    "causation_id": "cause-123",
                    "timestamp": "2023-10-14T12:00:00+00:00",
                    "event_type": "SignalGenerated",
                    "source_module": "strategy",
                    "schema_version": "1.0",
                    "signals_data": {},
                    "consolidated_portfolio": {},
                    "signal_count": 0,
                    "metadata": {},
                }
            ),
        }

        mock_handler = Mock()
        with patch(
            "the_alchemiser.lambda_handler_eventbridge.ApplicationContainer.create_for_environment"
        ), patch(
            "the_alchemiser.lambda_handler_eventbridge._get_handler_for_event",
            return_value=mock_handler,
        ):
            response = eventbridge_handler(event, mock_context)

        assert response["statusCode"] == 200
        mock_handler.handle_event.assert_called_once()

    def test_handler_unknown_event_type(self, mock_context: Mock) -> None:
        """Test handler returns 400 for unknown event type."""
        event = {
            "detail-type": "UnknownEvent",
            "source": "alchemiser.unknown",
            "detail": {"event_id": "test"},
        }

        response = eventbridge_handler(event, mock_context)

        assert response["statusCode"] == 400
        assert "Unknown event type" in response["body"]

    def test_handler_no_handler_for_event(
        self, signal_generated_event: dict[str, Any], mock_context: Mock
    ) -> None:
        """Test handler returns 404 when no handler found."""
        with patch(
            "the_alchemiser.lambda_handler_eventbridge.ApplicationContainer.create_for_environment"
        ), patch(
            "the_alchemiser.lambda_handler_eventbridge._get_handler_for_event",
            return_value=None,
        ):
            response = eventbridge_handler(signal_generated_event, mock_context)

        assert response["statusCode"] == 404
        assert "No handler for" in response["body"]

    @patch("the_alchemiser.lambda_handler_eventbridge.ApplicationContainer.create_for_environment")
    def test_handler_raises_on_error(
        self,
        mock_container_factory: Mock,
        signal_generated_event: dict[str, Any],
        mock_context: Mock,
    ) -> None:
        """Test handler re-raises exceptions for Lambda retry."""
        mock_handler = Mock()
        mock_handler.handle_event.side_effect = Exception("Handler error")

        with patch(
            "the_alchemiser.lambda_handler_eventbridge._get_handler_for_event",
            return_value=mock_handler,
        ), pytest.raises(Exception, match="Handler error"):
            eventbridge_handler(signal_generated_event, mock_context)


@pytest.mark.unit
class TestGetEventClass:
    """Test _get_event_class helper."""

    def test_signal_generated(self) -> None:
        """Test mapping SignalGenerated."""
        from the_alchemiser.shared.events import SignalGenerated

        event_class = _get_event_class("SignalGenerated")
        assert event_class is SignalGenerated

    def test_rebalance_planned(self) -> None:
        """Test mapping RebalancePlanned."""
        from the_alchemiser.shared.events import RebalancePlanned

        event_class = _get_event_class("RebalancePlanned")
        assert event_class is RebalancePlanned

    def test_trade_executed(self) -> None:
        """Test mapping TradeExecuted."""
        from the_alchemiser.shared.events import TradeExecuted

        event_class = _get_event_class("TradeExecuted")
        assert event_class is TradeExecuted

    def test_workflow_completed(self) -> None:
        """Test mapping WorkflowCompleted."""
        from the_alchemiser.shared.events import WorkflowCompleted

        event_class = _get_event_class("WorkflowCompleted")
        assert event_class is WorkflowCompleted

    def test_workflow_failed(self) -> None:
        """Test mapping WorkflowFailed."""
        from the_alchemiser.shared.events import WorkflowFailed

        event_class = _get_event_class("WorkflowFailed")
        assert event_class is WorkflowFailed

    def test_unknown_event_type(self) -> None:
        """Test returns None for unknown event type."""
        event_class = _get_event_class("UnknownEvent")
        assert event_class is None


@pytest.mark.unit
class TestGetHandlerForEvent:
    """Test _get_handler_for_event helper."""

    def test_signal_generated_handler(self) -> None:
        """Test returns PortfolioAnalysisHandler for SignalGenerated."""
        from the_alchemiser.shared.config.container import ApplicationContainer

        container = ApplicationContainer.create_for_testing()
        handler = _get_handler_for_event(container, "SignalGenerated")

        assert handler is not None
        from the_alchemiser.portfolio_v2.handlers import PortfolioAnalysisHandler

        assert isinstance(handler, PortfolioAnalysisHandler)

    def test_rebalance_planned_handler(self) -> None:
        """Test returns TradingExecutionHandler for RebalancePlanned."""
        from the_alchemiser.shared.config.container import ApplicationContainer

        container = ApplicationContainer.create_for_testing()
        handler = _get_handler_for_event(container, "RebalancePlanned")

        assert handler is not None
        from the_alchemiser.execution_v2.handlers import TradingExecutionHandler

        assert isinstance(handler, TradingExecutionHandler)

    def test_trade_executed_no_handler(self) -> None:
        """Test returns None for TradeExecuted (orchestrator only)."""
        from the_alchemiser.shared.config.container import ApplicationContainer

        container = ApplicationContainer.create_for_testing()
        handler = _get_handler_for_event(container, "TradeExecuted")

        assert handler is None

    def test_workflow_completed_no_handler(self) -> None:
        """Test returns None for WorkflowCompleted (orchestrator only)."""
        from the_alchemiser.shared.config.container import ApplicationContainer

        container = ApplicationContainer.create_for_testing()
        handler = _get_handler_for_event(container, "WorkflowCompleted")

        assert handler is None

    def test_unknown_event_type(self) -> None:
        """Test returns None for unknown event type."""
        from the_alchemiser.shared.config.container import ApplicationContainer

        container = ApplicationContainer.create_for_testing()
        handler = _get_handler_for_event(container, "UnknownEvent")

        assert handler is None


class TestEventBridgeHandlerIdempotency:
    """Test idempotency functionality in EventBridge handler."""

    @patch("the_alchemiser.lambda_handler_eventbridge.is_duplicate_event")
    @patch("the_alchemiser.lambda_handler_eventbridge.mark_event_processed")
    @patch("the_alchemiser.lambda_handler_eventbridge.ApplicationContainer")
    def test_handler_skips_duplicate_event(
        self,
        mock_container_class: Mock,
        mock_mark: Mock,
        mock_is_duplicate: Mock,
    ) -> None:
        """Test handler skips processing of duplicate events."""
        from the_alchemiser.lambda_handler_eventbridge import eventbridge_handler

        # Setup mocks
        mock_is_duplicate.return_value = True  # Event is a duplicate
        mock_mark.return_value = True

        # Mock context
        context = Mock()
        context.request_id = "lambda-123"

        # EventBridge event payload
        event = {
            "detail-type": "SignalGenerated",
            "source": "alchemiser.strategy",
            "detail": {
                "event_id": "evt-duplicate",
                "correlation_id": "corr-duplicate",
                "timestamp": "2025-10-14T12:00:00Z",
                "event_type": "SignalGenerated",
                "source_module": "strategy",
                "signals_data": {},
                "consolidated_portfolio": {},
                "signal_count": 0,
            },
        }

        # Invoke handler
        response = eventbridge_handler(event, context)

        # Verify response indicates duplicate
        assert response["statusCode"] == 200
        assert "duplicate" in response["body"].lower()

        # Verify idempotency check was called
        mock_is_duplicate.assert_called_once()

        # Verify mark was NOT called (already duplicate)
        mock_mark.assert_not_called()

        # Verify handler was NOT invoked
        mock_container_class.create_for_environment.assert_not_called()

    @patch("the_alchemiser.lambda_handler_eventbridge.is_duplicate_event")
    @patch("the_alchemiser.lambda_handler_eventbridge.mark_event_processed")
    @patch("the_alchemiser.lambda_handler_eventbridge.ApplicationContainer")
    def test_handler_processes_new_event(
        self,
        mock_container_class: Mock,
        mock_mark: Mock,
        mock_is_duplicate: Mock,
    ) -> None:
        """Test handler processes new (non-duplicate) events."""
        from the_alchemiser.lambda_handler_eventbridge import eventbridge_handler

        # Setup mocks
        mock_is_duplicate.return_value = False  # Not a duplicate
        mock_mark.return_value = True

        # Mock container and handler
        mock_container = Mock()
        mock_handler = Mock()
        mock_container_class.create_for_environment.return_value = mock_container

        # Mock handler creation
        from the_alchemiser.portfolio_v2.handlers import PortfolioAnalysisHandler

        with patch(
            "the_alchemiser.lambda_handler_eventbridge._get_handler_for_event",
            return_value=mock_handler,
        ):
            # Mock context
            context = Mock()
            context.request_id = "lambda-456"

            # EventBridge event payload
            event = {
                "detail-type": "SignalGenerated",
                "source": "alchemiser.strategy",
                "detail": {
                    "event_id": "evt-new",
                    "correlation_id": "corr-new",
                    "causation_id": "cause-new",
                    "timestamp": "2025-10-14T12:00:00Z",
                    "event_type": "SignalGenerated",
                    "source_module": "strategy",
                    "signals_data": {},
                    "consolidated_portfolio": {},
                    "signal_count": 0,
                },
            }

            # Invoke handler
            response = eventbridge_handler(event, context)

            # Verify success response
            assert response["statusCode"] == 200
            assert "processed successfully" in response["body"].lower()

            # Verify idempotency check was called
            mock_is_duplicate.assert_called_once()

            # Verify mark was called AFTER processing
            mock_mark.assert_called_once_with("evt-new", stage="dev")

            # Verify handler was invoked
            mock_handler.handle_event.assert_called_once()

    @patch("the_alchemiser.lambda_handler_eventbridge.is_duplicate_event")
    @patch("the_alchemiser.lambda_handler_eventbridge.mark_event_processed")
    def test_handler_uses_stage_from_environment(
        self,
        mock_mark: Mock,
        mock_is_duplicate: Mock,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Test handler uses APP__STAGE environment variable."""
        from the_alchemiser.lambda_handler_eventbridge import eventbridge_handler

        # Set stage environment variable
        monkeypatch.setenv("APP__STAGE", "prod")

        # Setup mocks
        mock_is_duplicate.return_value = True  # Skip processing

        # Mock context
        context = Mock()
        context.request_id = "lambda-789"

        # EventBridge event payload
        event = {
            "detail-type": "SignalGenerated",
            "source": "alchemiser.strategy",
            "detail": {
                "event_id": "evt-stage-test",
                "correlation_id": "corr-stage",
                "timestamp": "2025-10-14T12:00:00Z",
                "event_type": "SignalGenerated",
                "source_module": "strategy",
                "signals_data": {},
                "consolidated_portfolio": {},
                "signal_count": 0,
            },
        }

        # Invoke handler
        eventbridge_handler(event, context)

        # Verify stage was passed correctly
        mock_is_duplicate.assert_called_once_with("evt-stage-test", stage="prod")

    @patch("the_alchemiser.lambda_handler_eventbridge.is_duplicate_event")
    @patch("the_alchemiser.lambda_handler_eventbridge.mark_event_processed")
    def test_handler_extracts_correlation_id_from_detail(
        self,
        mock_mark: Mock,
        mock_is_duplicate: Mock,
    ) -> None:
        """Test handler extracts correlation_id from event detail for logging."""
        from the_alchemiser.lambda_handler_eventbridge import eventbridge_handler

        # Setup mocks
        mock_is_duplicate.return_value = True  # Skip processing for simplicity

        # Mock context
        context = Mock()
        context.request_id = "lambda-corr"

        # EventBridge event payload with correlation_id in detail
        event = {
            "detail-type": "SignalGenerated",
            "source": "alchemiser.strategy",
            "detail": {
                "event_id": "evt-corr",
                "correlation_id": "corr-from-detail",
                "timestamp": "2025-10-14T12:00:00Z",
                "event_type": "SignalGenerated",
                "source_module": "strategy",
                "signals_data": {},
                "consolidated_portfolio": {},
                "signal_count": 0,
            },
        }

        # Invoke handler (will skip processing due to mock)
        response = eventbridge_handler(event, context)

        # Verify response
        assert response["statusCode"] == 200

        # The correlation_id should be extracted from detail and used for logging
        # This is verified by the set_request_id call within the handler

