"""Business Unit: shared | Status: current.

Tests for AlpacaTradingService replace order functionality.
"""

from unittest.mock import Mock, patch
from uuid import UUID

import pytest
from alpaca.trading.models import Order
from alpaca.trading.requests import ReplaceOrderRequest

from the_alchemiser.shared.services.alpaca_trading_service import AlpacaTradingService


class TestAlpacaTradingServiceReplaceOrder:
    """Test replace order functionality in AlpacaTradingService."""

    @pytest.fixture
    def mock_trading_client(self):
        """Create mock trading client."""
        return Mock()

    @pytest.fixture
    def mock_websocket_manager(self):
        """Create mock websocket manager."""
        return Mock()

    @pytest.fixture
    def alpaca_service(self, mock_trading_client, mock_websocket_manager):
        """Create AlpacaTradingService instance with mocks."""
        return AlpacaTradingService(
            trading_client=mock_trading_client,
            websocket_manager=mock_websocket_manager,
            paper_trading=True,
        )

    def test_replace_order_by_id_success(self, alpaca_service, mock_trading_client):
        """Test successful order replacement."""
        # Arrange
        order_id = "test-order-123"
        replace_request = ReplaceOrderRequest(
            qty=50,
            limit_price=150.00,
        )
        
        mock_order = Mock(spec=Order)
        mock_order.id = UUID("12345678-1234-5678-9123-123456789012")
        mock_order.symbol = "AAPL"
        mock_order.qty = 50
        mock_order.limit_price = 150.00
        
        mock_trading_client.replace_order_by_id.return_value = mock_order

        # Act
        result = alpaca_service.replace_order_by_id(order_id, replace_request)

        # Assert
        mock_trading_client.replace_order_by_id.assert_called_once_with(order_id, replace_request)
        assert result is mock_order

    def test_replace_order_by_id_failure(self, alpaca_service, mock_trading_client):
        """Test order replacement failure."""
        # Arrange
        order_id = "test-order-123"
        replace_request = ReplaceOrderRequest(
            qty=50,
            limit_price=150.00,
        )
        
        mock_trading_client.replace_order_by_id.side_effect = Exception("API Error")

        # Act
        result = alpaca_service.replace_order_by_id(order_id, replace_request)

        # Assert
        mock_trading_client.replace_order_by_id.assert_called_once_with(order_id, replace_request)
        assert result is None

    def test_replace_order_by_id_with_dict_response(self, alpaca_service, mock_trading_client):
        """Test order replacement returning dict response."""
        # Arrange
        order_id = "test-order-123"
        replace_request = ReplaceOrderRequest(
            qty=50,
            limit_price=150.00,
        )
        
        dict_response = {
            "id": "12345678-1234-5678-9123-123456789012",
            "symbol": "AAPL",
            "qty": 50,
            "limit_price": 150.00,
            "status": "accepted"
        }
        
        mock_trading_client.replace_order_by_id.return_value = dict_response

        # Act
        result = alpaca_service.replace_order_by_id(order_id, replace_request)

        # Assert
        mock_trading_client.replace_order_by_id.assert_called_once_with(order_id, replace_request)
        assert result == dict_response

    @patch('the_alchemiser.shared.services.alpaca_trading_service.logger')
    def test_replace_order_by_id_logs_success(self, mock_logger, alpaca_service, mock_trading_client):
        """Test that successful replacement is logged."""
        # Arrange
        order_id = "test-order-123"
        replace_request = ReplaceOrderRequest(
            qty=50,
            limit_price=150.00,
        )
        
        mock_order = Mock(spec=Order)
        mock_trading_client.replace_order_by_id.return_value = mock_order

        # Act
        alpaca_service.replace_order_by_id(order_id, replace_request)

        # Assert
        mock_logger.info.assert_called_once()
        log_call_args = mock_logger.info.call_args[0][0]
        assert "Replaced order test-order-123" in log_call_args

    @patch('the_alchemiser.shared.services.alpaca_trading_service.logger')
    def test_replace_order_by_id_logs_failure(self, mock_logger, alpaca_service, mock_trading_client):
        """Test that failed replacement is logged."""
        # Arrange
        order_id = "test-order-123"
        replace_request = ReplaceOrderRequest(
            qty=50,
            limit_price=150.00,
        )
        
        mock_trading_client.replace_order_by_id.side_effect = Exception("API Error")

        # Act
        alpaca_service.replace_order_by_id(order_id, replace_request)

        # Assert
        mock_logger.error.assert_called_once()
        log_call_args = mock_logger.error.call_args[0][0]
        assert "Failed to replace order test-order-123" in log_call_args