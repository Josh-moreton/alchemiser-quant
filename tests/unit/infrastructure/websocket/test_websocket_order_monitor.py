#!/usr/bin/env python3
"""
Unit tests for WebSocket order monitor DTO migration.

Tests both current dict[str, str] behavior and new WebSocketResultDTO behavior.
"""

from unittest.mock import Mock, patch

import pytest

from the_alchemiser.infrastructure.websocket.websocket_order_monitor import OrderCompletionMonitor
from the_alchemiser.interfaces.schemas.execution import WebSocketResult


@pytest.fixture
def mock_trading_client():
    """Mock trading client for testing."""
    client = Mock()
    client._api_key = "test_api_key"
    client._secret_key = "test_secret_key"
    client._sandbox = True
    return client


@pytest.fixture
def monitor(mock_trading_client):
    """Create OrderCompletionMonitor instance for testing."""
    return OrderCompletionMonitor(
        trading_client=mock_trading_client,
        api_key="test_api_key",
        secret_key="test_secret_key"
    )


class TestOrderCompletionMonitorDTO:
    """Test WebSocketResultDTO migration for OrderCompletionMonitor."""

    def test_wait_for_order_completion_success_returns_websocket_result(self, monitor, mock_trading_client):
        """Test successful order completion returns WebSocketResult DTO."""
        # Mock order already completed
        mock_order = Mock()
        mock_order.status = "filled"
        mock_order.id = "order_123"
        mock_trading_client.get_order_by_id.return_value = mock_order

        # Mock config
        with patch('the_alchemiser.infrastructure.config.load_settings') as mock_config:
            mock_settings = Mock()
            mock_settings.alpaca.enable_websocket_orders = True
            mock_config.return_value = mock_settings

            result = monitor.wait_for_order_completion(["order_123"], max_wait_seconds=30)

            # Should return WebSocketResult format
            assert isinstance(result, dict)
            assert "status" in result
            assert "message" in result
            assert "orders_completed" in result
            assert result["status"] == "completed"
            assert "order_123" in result["orders_completed"]

    def test_wait_for_order_completion_timeout_returns_websocket_result(self, monitor, mock_trading_client):
        """Test timeout scenario returns WebSocketResult DTO."""
        # Mock order not completed yet
        mock_order = Mock()
        mock_order.status = "pending"
        mock_order.id = "order_123"
        mock_trading_client.get_order_by_id.return_value = mock_order

        # Mock config
        with patch('the_alchemiser.infrastructure.config.load_settings') as mock_config:
            mock_settings = Mock()
            mock_settings.alpaca.enable_websocket_orders = True
            mock_config.return_value = mock_settings

            # Mock WebSocket connection creation to avoid actual connection
            with patch('alpaca.trading.stream.TradingStream') as mock_stream:
                mock_stream_instance = Mock()
                mock_stream.return_value = mock_stream_instance

                result = monitor.wait_for_order_completion(["order_123"], max_wait_seconds=1)

                # Should return WebSocketResult format
                assert isinstance(result, dict)
                assert "status" in result
                assert "message" in result
                assert "orders_completed" in result
                assert result["status"] in ["timeout", "completed"]  # May complete or timeout

    def test_wait_for_order_completion_error_returns_websocket_result(self, monitor, mock_trading_client):
        """Test error scenario returns WebSocketResult DTO."""
        # Mock config
        with patch('the_alchemiser.infrastructure.config.load_settings') as mock_config:
            mock_settings = Mock()
            mock_settings.alpaca.enable_websocket_orders = False  # Disabled
            mock_config.return_value = mock_settings

            # Should raise ValueError when WebSocket disabled
            with pytest.raises(ValueError, match="WebSocket order monitoring is disabled"):
                monitor.wait_for_order_completion(["order_123"], max_wait_seconds=30)

    def test_empty_order_list_returns_empty_websocket_result(self, monitor):
        """Test empty order list returns empty WebSocketResult."""
        result = monitor.wait_for_order_completion([], max_wait_seconds=30)

        # Should return WebSocketResult DTO format
        assert isinstance(result, dict)
        assert "status" in result
        assert "message" in result
        assert "orders_completed" in result
        assert result["status"] == "completed"
        assert result["orders_completed"] == []

    def test_missing_api_keys_raises_error(self, mock_trading_client):
        """Test missing API keys raises appropriate error."""
        monitor = OrderCompletionMonitor(trading_client=mock_trading_client, api_key=None, secret_key=None)
        mock_trading_client._api_key = None
        mock_trading_client._secret_key = None

        with pytest.raises(ValueError, match="API keys are required"):
            monitor.wait_for_order_completion(["order_123"], max_wait_seconds=30)


class TestOrderCompletionMonitorAdditionalScenarios:
    """Additional test scenarios for WebSocketResultDTO behavior."""

    def test_websocket_connection_error_scenario(self, monitor, mock_trading_client):
        """Test that WebSocket connection errors are properly handled."""
        # Mock config
        with patch('the_alchemiser.infrastructure.config.load_settings') as mock_config:
            mock_settings = Mock()
            mock_settings.alpaca.enable_websocket_orders = True
            mock_config.return_value = mock_settings

            # Mock order status check
            mock_order = Mock()
            mock_order.status = "pending"
            mock_trading_client.get_order_by_id.return_value = mock_order

            # Mock WebSocket to raise exception
            with patch('alpaca.trading.stream.TradingStream') as mock_stream:
                mock_stream.side_effect = Exception("Connection failed")

                # Should raise RuntimeError when WebSocket creation fails
                with pytest.raises(RuntimeError, match="Failed to create WebSocket connection"):
                    monitor.wait_for_order_completion(["order_123"], max_wait_seconds=30)


class TestWebSocketResultDTOStructure:
    """Test WebSocketResult DTO structure compliance."""

    def test_websocket_result_structure(self):
        """Test WebSocketResult DTO has correct structure."""
        # This tests the TypedDict structure
        result: WebSocketResult = {
            "status": "completed",
            "message": "All orders completed successfully",
            "orders_completed": ["order_123", "order_456"]
        }

        assert result["status"] in ["completed", "timeout", "error"]
        assert isinstance(result["message"], str)
        assert isinstance(result["orders_completed"], list)
        assert all(isinstance(order_id, str) for order_id in result["orders_completed"])

    def test_websocket_result_timeout_structure(self):
        """Test WebSocketResult DTO for timeout scenario."""
        result: WebSocketResult = {
            "status": "timeout",
            "message": "Order monitoring timed out after 30 seconds",
            "orders_completed": ["order_123"]  # Partially completed
        }

        assert result["status"] == "timeout"
        assert "timed out" in result["message"].lower()
        assert isinstance(result["orders_completed"], list)

    def test_websocket_result_error_structure(self):
        """Test WebSocketResult DTO for error scenario."""
        result: WebSocketResult = {
            "status": "error",
            "message": "WebSocket connection failed: Connection error",
            "orders_completed": []  # No orders completed due to error
        }

        assert result["status"] == "error"
        assert "error" in result["message"].lower()
        assert isinstance(result["orders_completed"], list)
