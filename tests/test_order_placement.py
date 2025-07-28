#!/usr/bin/env python3
"""
Test order placement scenarios including market orders, limit orders, 
partial fills, and failed orders.
"""

import pytest
from unittest.mock import MagicMock, patch
from alpaca.trading.enums import OrderSide
from alpaca.common.exceptions import APIError

from the_alchemiser.execution.order_manager_adapter import OrderManagerAdapter
from the_alchemiser.execution.simple_order_manager import SimpleOrderManager


@pytest.fixture
def mock_trading_client():
    """Mock Alpaca trading client."""
    client = MagicMock()
    client.submit_order.return_value = MagicMock(id='test_order_123')
    client.get_order_by_id.return_value = MagicMock(id='test_order_123', status='filled')
    client.get_all_positions.return_value = []
    client.get_clock.return_value = MagicMock(is_open=True)
    return client


@pytest.fixture
def mock_data_provider():
    """Mock data provider."""
    provider = MagicMock()
    provider.get_current_price.return_value = 100.0
    provider.get_latest_quote.return_value = (99.0, 101.0)
    return provider


@pytest.fixture
def order_manager(mock_trading_client, mock_data_provider):
    """Create OrderManagerAdapter for testing."""
    return OrderManagerAdapter(mock_trading_client, mock_data_provider)


class TestMarketOrders:
    """Test market order scenarios."""
    
    def test_market_buy_order(self, order_manager, mock_trading_client):
        """Test successful market buy order."""
        order_id = order_manager.place_limit_or_market('AAPL', 10.0, OrderSide.BUY)
        
        assert order_id is not None
        mock_trading_client.submit_order.assert_called_once()
        
        # Verify it's a market order (adapter uses market orders)
        call_args = mock_trading_client.submit_order.call_args[0][0]
        assert call_args.symbol == 'AAPL'
        assert call_args.qty == 10.0
        assert call_args.side == OrderSide.BUY
    
    def test_market_sell_order(self, order_manager, mock_trading_client):
        """Test successful market sell order."""
        # Mock having a position
        mock_trading_client.get_all_positions.return_value = [
            MagicMock(symbol='AAPL', qty=20.0)
        ]
        
        order_id = order_manager.place_safe_sell_order('AAPL', 5.0)
        
        assert order_id is not None
        mock_trading_client.submit_order.assert_called_once()
    
    def test_market_order_insufficient_buying_power(self, order_manager, mock_trading_client):
        """Test market order with insufficient buying power."""
        # Mock insufficient buying power error
        error_response = {"code": 40310000, "message": "insufficient buying power"}
        mock_trading_client.submit_order.side_effect = APIError(error_response)
        
        order_id = order_manager.place_limit_or_market('AAPL', 1000.0, OrderSide.BUY)
        
        # Should return None when order fails
        assert order_id is None


class TestPartialFills:
    """Test partial fill scenarios."""
    
    def test_partial_fill_completion(self, order_manager, mock_trading_client):
        """Test order that gets partially filled then completed."""
        # Mock partial fill then completion
        partial_order = MagicMock(id='test_order_123', status='partially_filled')
        completed_order = MagicMock(id='test_order_123', status='filled')
        
        mock_trading_client.get_order_by_id.side_effect = [partial_order, completed_order]
        
        # Test settlement waiting
        sell_orders = [{'order_id': 'test_order_123'}]
        result = order_manager.wait_for_settlement(sell_orders, max_wait_time=2, poll_interval=0.1)
        
        assert result is True
    
    def test_partial_fill_timeout(self, order_manager, mock_trading_client):
        """Test order that remains partially filled until timeout."""
        # Mock order stuck in partial fill
        partial_order = MagicMock(id='test_order_123', status='partially_filled')
        mock_trading_client.get_order_by_id.return_value = partial_order
        
        sell_orders = [{'order_id': 'test_order_123'}]
        result = order_manager.wait_for_settlement(sell_orders, max_wait_time=0.2, poll_interval=0.1)
        
        # Should timeout and return False
        assert result is False


class TestFailedOrders:
    """Test various order failure scenarios."""
    
    def test_insufficient_buying_power_buy(self, order_manager, mock_trading_client):
        """Test buy order with insufficient buying power."""
        error_response = {"code": 40310000, "message": "insufficient buying power"}
        mock_trading_client.submit_order.side_effect = APIError(error_response)
        
        order_id = order_manager.place_limit_or_market('AAPL', 1000.0, OrderSide.BUY)
        
        assert order_id is None
    
    def test_attempt_to_short_sell(self, order_manager, mock_trading_client):
        """Test attempt to sell more than owned (should not short)."""
        # Mock having only 5 shares
        mock_trading_client.get_all_positions.return_value = [
            MagicMock(symbol='AAPL', qty=5.0)
        ]
        
        # Try to sell 10 shares (more than owned)
        order_id = order_manager.place_safe_sell_order('AAPL', 10.0)
        
        # Should still work but cap the quantity
        assert order_id is not None
        
        # Verify the actual quantity was capped
        call_args = mock_trading_client.submit_order.call_args[0][0]
        assert float(call_args.qty) <= 5.0
    
    def test_api_network_error(self, order_manager, mock_trading_client):
        """Test API/network errors."""
        mock_trading_client.submit_order.side_effect = Exception("Network error")
        
        order_id = order_manager.place_limit_or_market('AAPL', 1.0, OrderSide.BUY)
        
        assert order_id is None
    
    def test_symbol_not_tradable(self, order_manager, mock_trading_client):
        """Test trading a symbol that's not available."""
        error_response = {"code": 40410000, "message": "symbol not found"}
        mock_trading_client.submit_order.side_effect = APIError(error_response)
        
        order_id = order_manager.place_limit_or_market('INVALID', 1.0, OrderSide.BUY)
        
        assert order_id is None


class TestPositionLiquidation:
    """Test position liquidation scenarios."""
    
    def test_full_liquidation(self, order_manager, mock_trading_client):
        """Test full position liquidation using API."""
        mock_trading_client.close_position.return_value = MagicMock(id='liquidation_order_123')
        
        order_id = order_manager.liquidate_position('AAPL')
        
        assert order_id is not None
        mock_trading_client.close_position.assert_called_once_with('AAPL')
    
    def test_liquidation_with_zero_position(self, order_manager, mock_trading_client):
        """Test attempt to liquidate when no position exists."""
        mock_trading_client.close_position.side_effect = Exception("No position to close")
        
        order_id = order_manager.liquidate_position('AAPL')
        
        assert order_id is None
    
    def test_liquidation_with_fractional_shares(self, order_manager, mock_trading_client):
        """Test liquidation with fractional shares."""
        mock_trading_client.get_all_positions.return_value = [
            MagicMock(symbol='AAPL', qty=1.5)  # Fractional shares
        ]
        mock_trading_client.close_position.return_value = MagicMock(id='liquidation_order_123')
        
        order_id = order_manager.liquidate_position('AAPL')
        
        assert order_id is not None
    
    def test_safe_sell_triggers_liquidation(self, order_manager, mock_trading_client):
        """Test that selling entire position triggers liquidation API."""
        # Mock having exactly 10 shares
        mock_trading_client.get_all_positions.return_value = [
            MagicMock(symbol='AAPL', qty=10.0)
        ]
        mock_trading_client.close_position.return_value = MagicMock(id='liquidation_order_123')
        
        # Try to sell exactly 10 shares (100% of position)
        order_id = order_manager.place_safe_sell_order('AAPL', 10.0)
        
        assert order_id is not None
        # Should use liquidation API instead of regular sell order
        mock_trading_client.close_position.assert_called_once_with('AAPL')


class TestOrderStatusPolling:
    """Test order status polling and settlement logic."""
    
    def test_order_filled_immediately(self, order_manager, mock_trading_client):
        """Test order that fills immediately."""
        filled_order = MagicMock(id='test_order_123', status='filled')
        mock_trading_client.get_order_by_id.return_value = filled_order
        
        sell_orders = [{'order_id': 'test_order_123'}]
        result = order_manager.wait_for_settlement(sell_orders, max_wait_time=1, poll_interval=0.1)
        
        assert result is True
    
    def test_order_canceled(self, order_manager, mock_trading_client):
        """Test order that gets canceled."""
        canceled_order = MagicMock(id='test_order_123', status='canceled')
        mock_trading_client.get_order_by_id.return_value = canceled_order
        
        sell_orders = [{'order_id': 'test_order_123'}]
        result = order_manager.wait_for_settlement(sell_orders, max_wait_time=1, poll_interval=0.1)
        
        assert result is True  # Canceled is considered settled
    
    def test_order_rejected(self, order_manager, mock_trading_client):
        """Test order that gets rejected."""
        rejected_order = MagicMock(id='test_order_123', status='rejected')
        mock_trading_client.get_order_by_id.return_value = rejected_order
        
        sell_orders = [{'order_id': 'test_order_123'}]
        result = order_manager.wait_for_settlement(sell_orders, max_wait_time=1, poll_interval=0.1)
        
        assert result is True  # Rejected is considered settled
    
    def test_multiple_orders_settlement(self, order_manager, mock_trading_client):
        """Test waiting for multiple orders to settle."""
        def mock_get_order(order_id):
            return MagicMock(id=order_id, status='filled')
        
        mock_trading_client.get_order_by_id.side_effect = mock_get_order
        
        sell_orders = [
            {'order_id': 'order_1'},
            {'order_id': 'order_2'},
            {'order_id': 'order_3'}
        ]
        result = order_manager.wait_for_settlement(sell_orders, max_wait_time=1, poll_interval=0.1)
        
        assert result is True
