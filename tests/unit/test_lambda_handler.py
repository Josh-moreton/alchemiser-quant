#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Unit tests for lambda_handler.py AWS Lambda entry point.

Tests cover:
- Lambda handler invocation with various events
- Event parsing for trade and P&L modes
- Trading mode determination (paper/live)
- Error handling and response structure
- Error notification flows
"""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from the_alchemiser.lambda_handler import (
    _build_error_response,
    _build_response_message,
    _determine_trading_mode,
    _extract_correlation_id,
    _has_correlation_id,
    lambda_handler,
    parse_event_mode,
)
from the_alchemiser.shared.errors.exceptions import (
    DataProviderError,
    StrategyExecutionError,
    TradingClientError,
)
from the_alchemiser.shared.schemas import LambdaEvent


class TestEventParsing:
    """Test event parsing functionality."""

    def test_parse_empty_event(self) -> None:
        """Test parsing empty event defaults to trade."""
        command_args = parse_event_mode({})
        assert command_args == ["trade"]

    def test_parse_none_event(self) -> None:
        """Test parsing None event defaults to trade."""
        event = LambdaEvent()
        command_args = parse_event_mode(event)
        assert command_args == ["trade"]

    def test_parse_trade_event(self) -> None:
        """Test parsing explicit trade event."""
        event = {"mode": "trade"}
        command_args = parse_event_mode(event)
        assert command_args == ["trade"]

    def test_parse_paper_trading_event(self) -> None:
        """Test parsing paper trading event."""
        event = {"mode": "trade", "trading_mode": "paper"}
        command_args = parse_event_mode(event)
        assert command_args == ["trade"]

    def test_parse_live_trading_event(self) -> None:
        """Test parsing live trading event."""
        event = {"mode": "trade", "trading_mode": "live"}
        command_args = parse_event_mode(event)
        assert command_args == ["trade"]

    def test_parse_pnl_weekly_event(self) -> None:
        """Test parsing P&L weekly analysis event."""
        event = {"action": "pnl_analysis", "pnl_type": "weekly"}
        command_args = parse_event_mode(event)
        assert command_args == ["pnl", "--weekly"]

    def test_parse_pnl_monthly_event(self) -> None:
        """Test parsing P&L monthly analysis event."""
        event = {"action": "pnl_analysis", "pnl_type": "monthly"}
        command_args = parse_event_mode(event)
        assert command_args == ["pnl", "--monthly"]

    def test_parse_pnl_with_period_event(self) -> None:
        """Test parsing P&L with specific period."""
        event = {"action": "pnl_analysis", "pnl_period": "3M"}
        command_args = parse_event_mode(event)
        assert command_args == ["pnl", "--period", "3M"]

    def test_parse_pnl_with_periods_count(self) -> None:
        """Test parsing P&L with periods count."""
        event = {"action": "pnl_analysis", "pnl_type": "weekly", "pnl_periods": 3}
        command_args = parse_event_mode(event)
        assert command_args == ["pnl", "--weekly", "--periods", "3"]

    def test_parse_pnl_with_detailed_flag(self) -> None:
        """Test parsing P&L with detailed flag."""
        event = {"action": "pnl_analysis", "pnl_type": "monthly", "pnl_detailed": True}
        command_args = parse_event_mode(event)
        assert command_args == ["pnl", "--monthly", "--detailed"]

    def test_parse_pnl_ignores_periods_1(self) -> None:
        """Test parsing P&L ignores periods when value is 1."""
        event = {"action": "pnl_analysis", "pnl_type": "weekly", "pnl_periods": 1}
        command_args = parse_event_mode(event)
        assert command_args == ["pnl", "--weekly"]

    def test_parse_monthly_summary_raises_error(self) -> None:
        """Test parsing monthly_summary action raises error."""
        event = {"action": "monthly_summary"}
        with pytest.raises(ValueError, match="Unsupported action 'monthly_summary'"):
            parse_event_mode(event)

    def test_parse_lambda_event_object(self) -> None:
        """Test parsing with LambdaEvent object."""
        event = LambdaEvent(mode="trade", trading_mode="paper")
        command_args = parse_event_mode(event)
        assert command_args == ["trade"]


class TestTradingModeDetection:
    """Test trading mode detection from endpoint."""

    @patch("the_alchemiser.lambda_handler.get_alpaca_keys")
    def test_determine_paper_trading_mode(self, mock_get_alpaca_keys: Mock) -> None:
        """Test determining paper trading mode from endpoint."""
        mock_get_alpaca_keys.return_value = (
            "test_key",
            "test_secret",
            "https://paper-api.alpaca.markets",
        )
        mode = _determine_trading_mode("trade")
        assert mode == "paper"

    @patch("the_alchemiser.lambda_handler.get_alpaca_keys")
    def test_determine_live_trading_mode(self, mock_get_alpaca_keys: Mock) -> None:
        """Test determining live trading mode from endpoint."""
        mock_get_alpaca_keys.return_value = (
            "test_key",
            "test_secret",
            "https://api.alpaca.markets",
        )
        mode = _determine_trading_mode("trade")
        assert mode == "live"

    @patch("the_alchemiser.lambda_handler.get_alpaca_keys")
    def test_determine_mode_for_non_trade(self, mock_get_alpaca_keys: Mock) -> None:
        """Test determining mode for non-trade commands."""
        mode = _determine_trading_mode("pnl")
        assert mode == "n/a"
        mock_get_alpaca_keys.assert_not_called()

    @patch("the_alchemiser.lambda_handler.get_alpaca_keys")
    def test_determine_mode_with_none_endpoint(self, mock_get_alpaca_keys: Mock) -> None:
        """Test determining mode when endpoint is None."""
        mock_get_alpaca_keys.return_value = ("test_key", "test_secret", None)
        mode = _determine_trading_mode("trade")
        assert mode == "live"

    @patch("the_alchemiser.lambda_handler.get_alpaca_keys")
    def test_determine_mode_case_insensitive(self, mock_get_alpaca_keys: Mock) -> None:
        """Test determining mode is case insensitive."""
        mock_get_alpaca_keys.return_value = (
            "test_key",
            "test_secret",
            "https://PAPER-api.alpaca.markets",
        )
        mode = _determine_trading_mode("trade")
        assert mode == "paper"


class TestResponseMessage:
    """Test response message building."""

    def test_build_success_message_paper(self) -> None:
        """Test building success message for paper trading."""
        message = _build_response_message("paper", result=True)
        assert message == "Paper trading completed successfully"

    def test_build_success_message_live(self) -> None:
        """Test building success message for live trading."""
        message = _build_response_message("live", result=True)
        assert message == "Live trading completed successfully"

    def test_build_failure_message_paper(self) -> None:
        """Test building failure message for paper trading."""
        message = _build_response_message("paper", result=False)
        assert message == "Paper trading failed"

    def test_build_failure_message_live(self) -> None:
        """Test building failure message for live trading."""
        message = _build_response_message("live", result=False)
        assert message == "Live trading failed"

    def test_build_message_na_mode(self) -> None:
        """Test building message for n/a mode."""
        message = _build_response_message("n/a", result=True)
        assert message == "N/A trading completed successfully"


class TestHelperFunctions:
    """Test helper functions for complexity reduction."""

    def test_extract_correlation_id_from_dict_event(self) -> None:
        """Test extracting correlation ID from dict event."""
        event = {"correlation_id": "test-correlation-123"}
        correlation_id = _extract_correlation_id(event)
        assert correlation_id == "test-correlation-123"

    def test_extract_correlation_id_from_lambda_event(self) -> None:
        """Test extracting correlation ID from LambdaEvent object."""
        event = LambdaEvent(correlation_id="test-correlation-456")
        correlation_id = _extract_correlation_id(event)
        assert correlation_id == "test-correlation-456"

    def test_extract_correlation_id_generates_new_id(self) -> None:
        """Test generating new correlation ID when event has none."""
        event = {"mode": "trade"}
        correlation_id = _extract_correlation_id(event)
        assert correlation_id is not None
        assert len(correlation_id) > 0

    def test_extract_correlation_id_from_none_event(self) -> None:
        """Test generating correlation ID when event is None."""
        correlation_id = _extract_correlation_id(None)
        assert correlation_id is not None
        assert len(correlation_id) > 0

    def test_has_correlation_id_dict_with_id(self) -> None:
        """Test checking correlation ID in dict event."""
        event = {"correlation_id": "test-123"}
        assert _has_correlation_id(event) is True

    def test_has_correlation_id_dict_without_id(self) -> None:
        """Test checking correlation ID in dict event without ID."""
        event = {"mode": "trade"}
        assert _has_correlation_id(event) is False

    def test_has_correlation_id_lambda_event_with_id(self) -> None:
        """Test checking correlation ID in LambdaEvent object."""
        event = LambdaEvent(correlation_id="test-456")
        assert _has_correlation_id(event) is True

    def test_has_correlation_id_lambda_event_without_id(self) -> None:
        """Test checking correlation ID in LambdaEvent object without ID."""
        event = LambdaEvent()
        assert _has_correlation_id(event) is False

    def test_has_correlation_id_none_event(self) -> None:
        """Test checking correlation ID when event is None."""
        assert _has_correlation_id(None) is False

    def test_build_error_response_with_all_fields(self) -> None:
        """Test building error response with all fields."""
        response = _build_error_response(
            mode="trade",
            trading_mode="paper",
            error_message="Test error occurred",
            request_id="req-123",
        )
        assert response["status"] == "failed"
        assert response["mode"] == "trade"
        assert response["trading_mode"] == "paper"
        assert response["message"] == "Test error occurred"
        assert response["request_id"] == "req-123"

    def test_build_error_response_with_unknown_mode(self) -> None:
        """Test building error response with unknown mode."""
        response = _build_error_response(
            mode="unknown",
            trading_mode="unknown",
            error_message="Critical error",
            request_id="req-456",
        )
        assert response["status"] == "failed"
        assert response["mode"] == "unknown"
        assert response["trading_mode"] == "unknown"
        assert response["message"] == "Critical error"
        assert response["request_id"] == "req-456"


class TestLambdaHandler:
    """Test main Lambda handler function."""

    @patch("the_alchemiser.lambda_handler.main")
    @patch("the_alchemiser.lambda_handler.get_alpaca_keys")
    @patch("the_alchemiser.lambda_handler.generate_request_id")
    @patch("the_alchemiser.lambda_handler.set_request_id")
    def test_lambda_handler_success(
        self,
        mock_set_request_id: Mock,
        mock_generate_request_id: Mock,
        mock_get_alpaca_keys: Mock,
        mock_main: Mock,
    ) -> None:
        """Test successful Lambda handler execution."""
        mock_generate_request_id.return_value = "test-correlation-id"
        mock_get_alpaca_keys.return_value = (
            "key",
            "secret",
            "https://paper-api.alpaca.markets",
        )
        mock_result = Mock()
        mock_result.success = True
        mock_main.return_value = mock_result

        context = Mock()
        context.aws_request_id = "test-request-id"
        event = {"mode": "trade"}

        response = lambda_handler(event, context)

        assert response["status"] == "success"
        assert response["mode"] == "trade"
        assert response["trading_mode"] == "paper"
        assert "successfully" in response["message"]
        assert response["request_id"] == "test-request-id"
        mock_main.assert_called_once_with(["trade"])

    @patch("the_alchemiser.lambda_handler.main")
    @patch("the_alchemiser.lambda_handler.get_alpaca_keys")
    @patch("the_alchemiser.lambda_handler.generate_request_id")
    @patch("the_alchemiser.lambda_handler.set_request_id")
    def test_lambda_handler_failure(
        self,
        mock_set_request_id: Mock,
        mock_generate_request_id: Mock,
        mock_get_alpaca_keys: Mock,
        mock_main: Mock,
    ) -> None:
        """Test Lambda handler with failed execution."""
        mock_generate_request_id.return_value = "test-correlation-id"
        mock_get_alpaca_keys.return_value = (
            "key",
            "secret",
            "https://paper-api.alpaca.markets",
        )
        mock_result = Mock()
        mock_result.success = False
        mock_main.return_value = mock_result

        context = Mock()
        context.aws_request_id = "test-request-id"
        event = {"mode": "trade"}

        response = lambda_handler(event, context)

        assert response["status"] == "failed"
        assert response["mode"] == "trade"
        assert response["trading_mode"] == "paper"
        assert "failed" in response["message"]

    @patch("the_alchemiser.lambda_handler.main")
    @patch("the_alchemiser.lambda_handler.get_alpaca_keys")
    @patch("the_alchemiser.lambda_handler.generate_request_id")
    @patch("the_alchemiser.lambda_handler.set_request_id")
    def test_lambda_handler_with_empty_event(
        self,
        mock_set_request_id: Mock,
        mock_generate_request_id: Mock,
        mock_get_alpaca_keys: Mock,
        mock_main: Mock,
    ) -> None:
        """Test Lambda handler with empty event."""
        mock_generate_request_id.return_value = "test-correlation-id"
        mock_get_alpaca_keys.return_value = (
            "key",
            "secret",
            "https://paper-api.alpaca.markets",
        )
        mock_result = Mock()
        mock_result.success = True
        mock_main.return_value = mock_result

        context = Mock()
        context.aws_request_id = "test-request-id"

        response = lambda_handler(None, context)

        assert response["status"] == "success"
        assert response["mode"] == "trade"
        mock_main.assert_called_once_with(["trade"])

    @patch("the_alchemiser.lambda_handler.main")
    @patch("the_alchemiser.lambda_handler.get_alpaca_keys")
    @patch("the_alchemiser.lambda_handler.generate_request_id")
    @patch("the_alchemiser.lambda_handler.set_request_id")
    def test_lambda_handler_with_none_context(
        self,
        mock_set_request_id: Mock,
        mock_generate_request_id: Mock,
        mock_get_alpaca_keys: Mock,
        mock_main: Mock,
    ) -> None:
        """Test Lambda handler with None context."""
        mock_generate_request_id.return_value = "test-correlation-id"
        mock_get_alpaca_keys.return_value = (
            "key",
            "secret",
            "https://paper-api.alpaca.markets",
        )
        mock_result = Mock()
        mock_result.success = True
        mock_main.return_value = mock_result

        event = {"mode": "trade"}

        response = lambda_handler(event, None)

        assert response["status"] == "success"
        assert response["request_id"] == "local"

    @patch("the_alchemiser.lambda_handler.main")
    @patch("the_alchemiser.lambda_handler.get_alpaca_keys")
    @patch("the_alchemiser.lambda_handler.generate_request_id")
    @patch("the_alchemiser.lambda_handler.set_request_id")
    def test_lambda_handler_with_boolean_result(
        self,
        mock_set_request_id: Mock,
        mock_generate_request_id: Mock,
        mock_get_alpaca_keys: Mock,
        mock_main: Mock,
    ) -> None:
        """Test Lambda handler with boolean result (e.g., from pnl command)."""
        mock_generate_request_id.return_value = "test-correlation-id"
        mock_get_alpaca_keys.return_value = (
            "key",
            "secret",
            "https://paper-api.alpaca.markets",
        )
        mock_main.return_value = True

        context = Mock()
        context.aws_request_id = "test-request-id"
        event = {"action": "pnl_analysis", "pnl_type": "weekly"}

        response = lambda_handler(event, context)

        assert response["status"] == "success"
        mock_main.assert_called_once_with(["pnl", "--weekly"])

    @patch("the_alchemiser.lambda_handler._handle_trading_error")
    @patch("the_alchemiser.lambda_handler.get_alpaca_keys")
    @patch("the_alchemiser.lambda_handler.generate_request_id")
    @patch("the_alchemiser.lambda_handler.set_request_id")
    def test_lambda_handler_data_provider_error(
        self,
        mock_set_request_id: Mock,
        mock_generate_request_id: Mock,
        mock_get_alpaca_keys: Mock,
        mock_handle_error: Mock,
    ) -> None:
        """Test Lambda handler with DataProviderError."""
        mock_generate_request_id.return_value = "test-correlation-id"
        mock_get_alpaca_keys.side_effect = DataProviderError("Test data error")

        context = Mock()
        context.aws_request_id = "test-request-id"
        event = {"mode": "trade"}

        response = lambda_handler(event, context)

        assert response["status"] == "failed"
        # The mode is captured before get_alpaca_keys is called
        assert response["mode"] == "trade"
        assert response["trading_mode"] == "unknown"
        assert "DataProviderError" in response["message"]
        mock_handle_error.assert_called_once()

    @patch("the_alchemiser.lambda_handler._handle_trading_error")
    @patch("the_alchemiser.lambda_handler.main")
    @patch("the_alchemiser.lambda_handler.get_alpaca_keys")
    @patch("the_alchemiser.lambda_handler.generate_request_id")
    @patch("the_alchemiser.lambda_handler.set_request_id")
    def test_lambda_handler_strategy_execution_error(
        self,
        mock_set_request_id: Mock,
        mock_generate_request_id: Mock,
        mock_get_alpaca_keys: Mock,
        mock_main: Mock,
        mock_handle_error: Mock,
    ) -> None:
        """Test Lambda handler with StrategyExecutionError."""
        mock_generate_request_id.return_value = "test-correlation-id"
        mock_get_alpaca_keys.return_value = (
            "key",
            "secret",
            "https://paper-api.alpaca.markets",
        )
        mock_main.side_effect = StrategyExecutionError("Test strategy error")

        context = Mock()
        context.aws_request_id = "test-request-id"
        event = {"mode": "trade"}

        response = lambda_handler(event, context)

        assert response["status"] == "failed"
        assert "StrategyExecutionError" in response["message"]
        mock_handle_error.assert_called_once()

    @patch("the_alchemiser.lambda_handler._handle_trading_error")
    @patch("the_alchemiser.lambda_handler.main")
    @patch("the_alchemiser.lambda_handler.get_alpaca_keys")
    @patch("the_alchemiser.lambda_handler.generate_request_id")
    @patch("the_alchemiser.lambda_handler.set_request_id")
    def test_lambda_handler_trading_client_error(
        self,
        mock_set_request_id: Mock,
        mock_generate_request_id: Mock,
        mock_get_alpaca_keys: Mock,
        mock_main: Mock,
        mock_handle_error: Mock,
    ) -> None:
        """Test Lambda handler with TradingClientError."""
        mock_generate_request_id.return_value = "test-correlation-id"
        mock_get_alpaca_keys.return_value = (
            "key",
            "secret",
            "https://paper-api.alpaca.markets",
        )
        mock_main.side_effect = TradingClientError("Test client error")

        context = Mock()
        context.aws_request_id = "test-request-id"
        event = {"mode": "trade"}

        response = lambda_handler(event, context)

        assert response["status"] == "failed"
        assert "TradingClientError" in response["message"]

    @patch("the_alchemiser.lambda_handler._handle_critical_error")
    @patch("the_alchemiser.lambda_handler.main")
    @patch("the_alchemiser.lambda_handler.get_alpaca_keys")
    @patch("the_alchemiser.lambda_handler.generate_request_id")
    @patch("the_alchemiser.lambda_handler.set_request_id")
    def test_lambda_handler_import_error(
        self,
        mock_set_request_id: Mock,
        mock_generate_request_id: Mock,
        mock_get_alpaca_keys: Mock,
        mock_main: Mock,
        mock_handle_error: Mock,
    ) -> None:
        """Test Lambda handler with ImportError."""
        mock_generate_request_id.return_value = "test-correlation-id"
        mock_get_alpaca_keys.return_value = (
            "key",
            "secret",
            "https://paper-api.alpaca.markets",
        )
        mock_main.side_effect = ImportError("Test import error")

        context = Mock()
        context.aws_request_id = "test-request-id"
        event = {"mode": "trade"}

        response = lambda_handler(event, context)

        assert response["status"] == "failed"
        assert response["mode"] == "unknown"
        assert response["trading_mode"] == "unknown"
        assert "critical error" in response["message"]
        mock_handle_error.assert_called_once()

    @patch("the_alchemiser.lambda_handler._handle_critical_error")
    @patch("the_alchemiser.lambda_handler.main")
    @patch("the_alchemiser.lambda_handler.get_alpaca_keys")
    @patch("the_alchemiser.lambda_handler.generate_request_id")
    @patch("the_alchemiser.lambda_handler.set_request_id")
    def test_lambda_handler_value_error(
        self,
        mock_set_request_id: Mock,
        mock_generate_request_id: Mock,
        mock_get_alpaca_keys: Mock,
        mock_main: Mock,
        mock_handle_error: Mock,
    ) -> None:
        """Test Lambda handler with ValueError."""
        mock_generate_request_id.return_value = "test-correlation-id"
        mock_get_alpaca_keys.return_value = (
            "key",
            "secret",
            "https://paper-api.alpaca.markets",
        )
        mock_main.side_effect = ValueError("Test value error")

        context = Mock()
        context.aws_request_id = "test-request-id"
        event = {"mode": "trade"}

        response = lambda_handler(event, context)

        assert response["status"] == "failed"
        assert "critical error" in response["message"]

    @patch("the_alchemiser.lambda_handler._handle_critical_error")
    @patch("the_alchemiser.lambda_handler.main")
    @patch("the_alchemiser.lambda_handler.get_alpaca_keys")
    @patch("the_alchemiser.lambda_handler.generate_request_id")
    @patch("the_alchemiser.lambda_handler.set_request_id")
    def test_lambda_handler_os_error(
        self,
        mock_set_request_id: Mock,
        mock_generate_request_id: Mock,
        mock_get_alpaca_keys: Mock,
        mock_main: Mock,
        mock_handle_error: Mock,
    ) -> None:
        """Test Lambda handler with OSError."""
        mock_generate_request_id.return_value = "test-correlation-id"
        mock_get_alpaca_keys.return_value = (
            "key",
            "secret",
            "https://paper-api.alpaca.markets",
        )
        mock_main.side_effect = OSError("Test OS error")

        context = Mock()
        context.aws_request_id = "test-request-id"
        event = {"mode": "trade"}

        response = lambda_handler(event, context)

        assert response["status"] == "failed"
        assert "critical error" in response["message"]


class TestErrorHandling:
    """Test error handling functions."""

    @patch("the_alchemiser.lambda_handler.handle_trading_error")
    @patch("the_alchemiser.lambda_handler.send_error_notification_if_needed")
    @patch("the_alchemiser.shared.config.container.ApplicationContainer")
    def test_handle_error_with_notification(
        self,
        mock_container_cls: Mock,
        mock_send_notification: Mock,
        mock_handle_trading_error: Mock,
    ) -> None:
        """Test _handle_error function with notification."""
        from the_alchemiser.lambda_handler import _handle_error

        mock_container = Mock()
        mock_event_bus = Mock()
        mock_container.services.event_bus.return_value = mock_event_bus
        mock_container_cls.return_value = mock_container

        error = ValueError("Test error")
        event = {"mode": "trade"}
        request_id = "test-request-id"

        _handle_error(error, event, request_id)

        mock_handle_trading_error.assert_called_once()
        mock_send_notification.assert_called_once_with(mock_event_bus)

    @patch("the_alchemiser.lambda_handler.handle_trading_error")
    def test_handle_error_notification_failure(self, mock_handle_trading_error: Mock) -> None:
        """Test _handle_error when notification setup fails."""
        from the_alchemiser.lambda_handler import _handle_error

        with patch(
            "the_alchemiser.shared.config.container.ApplicationContainer",
            side_effect=ImportError("Container error"),
        ):
            error = ValueError("Test error")
            event = {"mode": "trade"}
            request_id = "test-request-id"

            # Should not raise, just log warning
            _handle_error(error, event, request_id)

            mock_handle_trading_error.assert_called_once()
