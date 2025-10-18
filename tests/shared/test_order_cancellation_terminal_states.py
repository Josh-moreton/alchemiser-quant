"""Business Unit: shared | Status: current.

Test order cancellation result handling for terminal states.

This test validates that cancel_order properly detects when an order
is already in a terminal state and returns appropriate results to prevent
duplicate order placement.
"""

from unittest.mock import Mock

import pytest

from the_alchemiser.shared.schemas.operations import OrderCancellationResult
from the_alchemiser.shared.services.alpaca_trading_service import AlpacaTradingService


class TestOrderCancellationTerminalStates:
    """Test order cancellation handling for terminal states."""

    @pytest.fixture
    def mock_trading_client(self):
        """Create a mock trading client."""
        return Mock()

    @pytest.fixture
    def mock_websocket_manager(self):
        """Create a mock websocket manager."""
        return Mock()

    @pytest.fixture
    def trading_service(self, mock_trading_client, mock_websocket_manager):
        """Create trading service with mocked dependencies."""
        return AlpacaTradingService(
            trading_client=mock_trading_client,
            websocket_manager=mock_websocket_manager,
            paper_trading=True,
        )

    def test_cancel_order_success(self, trading_service, mock_trading_client):
        """Test successful order cancellation."""
        order_id = "test-order-123"
        mock_trading_client.cancel_order_by_id.return_value = None

        result = trading_service.cancel_order(order_id)

        assert isinstance(result, OrderCancellationResult)
        assert result.success is True
        assert result.error is None
        assert result.order_id == order_id
        mock_trading_client.cancel_order_by_id.assert_called_once_with(order_id)

    def test_cancel_order_already_filled(self, trading_service, mock_trading_client):
        """Test cancellation when order is already filled."""
        order_id = "test-order-123"
        # Simulate the error from the issue
        error = Exception('{"code":42210000,"message":"order is already in \\"filled\\" state"}')
        mock_trading_client.cancel_order_by_id.side_effect = error

        result = trading_service.cancel_order(order_id)

        assert isinstance(result, OrderCancellationResult)
        assert result.success is True  # Success because order is complete
        assert result.error == "already_filled"
        assert result.order_id == order_id

    def test_cancel_order_already_cancelled(self, trading_service, mock_trading_client):
        """Test cancellation when order is already cancelled."""
        order_id = "test-order-123"
        error = Exception('order is already in "canceled" state')
        mock_trading_client.cancel_order_by_id.side_effect = error

        result = trading_service.cancel_order(order_id)

        assert isinstance(result, OrderCancellationResult)
        assert result.success is True
        assert result.error == "already_cancelled"
        assert result.order_id == order_id

    def test_cancel_order_already_rejected(self, trading_service, mock_trading_client):
        """Test cancellation when order is already rejected."""
        order_id = "test-order-123"
        error = Exception('order is already in "rejected" state')
        mock_trading_client.cancel_order_by_id.side_effect = error

        result = trading_service.cancel_order(order_id)

        assert isinstance(result, OrderCancellationResult)
        assert result.success is True
        assert result.error == "already_rejected"
        assert result.order_id == order_id

    def test_cancel_order_genuine_failure(self, trading_service, mock_trading_client):
        """Test cancellation with genuine failure (not terminal state)."""
        order_id = "test-order-123"
        error = Exception("Insufficient permissions")
        mock_trading_client.cancel_order_by_id.side_effect = error

        result = trading_service.cancel_order(order_id)

        assert isinstance(result, OrderCancellationResult)
        assert result.success is False
        assert result.error == "Insufficient permissions"
        assert result.order_id == order_id

    def test_cancel_order_network_error(self, trading_service, mock_trading_client):
        """Test cancellation with network error."""
        order_id = "test-order-123"
        error = Exception("Connection timeout")
        mock_trading_client.cancel_order_by_id.side_effect = error

        result = trading_service.cancel_order(order_id)

        assert isinstance(result, OrderCancellationResult)
        assert result.success is False
        assert "Connection timeout" in result.error
        assert result.order_id == order_id
