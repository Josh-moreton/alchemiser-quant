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
