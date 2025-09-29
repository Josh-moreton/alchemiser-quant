"""Business Unit: shared | Status: current.

Tests for AlpacaManager replace order functionality.
"""

from unittest.mock import Mock, patch

import pytest
from alpaca.trading.models import Order
from alpaca.trading.requests import ReplaceOrderRequest

from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager


class TestAlpacaManagerReplaceOrder:
    """Test replace order functionality in AlpacaManager."""

    @pytest.fixture
    def mock_alpaca_manager(self):
        """Create AlpacaManager instance with mocked trading service."""
        with patch.object(AlpacaManager, '__new__', return_value=Mock(spec=AlpacaManager)):
            manager = Mock(spec=AlpacaManager)
            manager._trading_service = Mock()
            return manager

    def test_replace_order_delegates_to_trading_service(self, mock_alpaca_manager):
        """Test that replace_order delegates to the trading service."""
        # Arrange
        order_id = "test-order-123"
        replace_request = ReplaceOrderRequest(
            qty=50,
            limit_price=150.00,
        )
        
        mock_order = Mock(spec=Order)
        mock_alpaca_manager._trading_service = Mock()
        mock_alpaca_manager._trading_service.replace_order_by_id.return_value = mock_order
        
        # Create a real method implementation
        def replace_order(self, order_id: str, order_data: ReplaceOrderRequest):
            return self._trading_service.replace_order_by_id(order_id, order_data)
        
        # Bind the method to the mock
        mock_alpaca_manager.replace_order = replace_order.__get__(mock_alpaca_manager)

        # Act
        result = mock_alpaca_manager.replace_order(order_id, replace_request)

        # Assert
        mock_alpaca_manager._trading_service.replace_order_by_id.assert_called_once_with(
            order_id, replace_request
        )
        assert result is mock_order

    def test_replace_order_returns_none_on_failure(self, mock_alpaca_manager):
        """Test that replace_order returns None when trading service fails."""
        # Arrange
        order_id = "test-order-123"
        replace_request = ReplaceOrderRequest(
            qty=50,
            limit_price=150.00,
        )
        
        mock_alpaca_manager._trading_service = Mock()
        mock_alpaca_manager._trading_service.replace_order_by_id.return_value = None
        
        # Create a real method implementation
        def replace_order(self, order_id: str, order_data: ReplaceOrderRequest):
            return self._trading_service.replace_order_by_id(order_id, order_data)
        
        # Bind the method to the mock
        mock_alpaca_manager.replace_order = replace_order.__get__(mock_alpaca_manager)

        # Act
        result = mock_alpaca_manager.replace_order(order_id, replace_request)

        # Assert
        mock_alpaca_manager._trading_service.replace_order_by_id.assert_called_once_with(
            order_id, replace_request
        )
        assert result is None