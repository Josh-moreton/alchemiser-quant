#!/usr/bin/env python3
"""
Test cash and buying power scenarios including sufficient cash,
insufficient cash, and zero cash scenarios.
"""

import pytest
from unittest.mock import MagicMock, patch
from alpaca.trading.enums import OrderSide
from alpaca.common.exceptions import APIError

from the_alchemiser.execution.smart_execution import SmartExecution


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
    """Create SmartExecution for testing."""
    return SmartExecution(mock_trading_client, mock_data_provider)


class TestSufficientCash:
    """Test scenarios with sufficient buying power."""
    
    def test_large_cash_position(self, order_manager, mock_trading_client):
        """Test trading with large cash position."""
        # Mock high buying power
        mock_trading_client.get_account.return_value = MagicMock(
            buying_power=50000.0,
            cash=50000.0,
            portfolio_value=50000.0
        )
        
        # Place moderate order
        order_id = order_manager.place_order('AAPL', 100.0, OrderSide.BUY)
        
        assert order_id is not None
        mock_trading_client.submit_order.assert_called_once()
    
    def test_exact_buying_power_usage(self, order_manager, mock_trading_client, mock_data_provider):
        """Test using exactly available buying power."""
        # Mock specific buying power
        mock_trading_client.get_account.return_value = MagicMock(
            buying_power=10000.0,
            cash=10000.0,
            portfolio_value=10000.0
        )
        mock_data_provider.get_current_price.return_value = 100.0
        
        # Try to buy exactly $10,000 worth (100 shares at $100)
        order_id = order_manager.place_order('AAPL', 100.0, OrderSide.BUY)
        
        assert order_id is not None
    
    def test_small_order_large_account(self, order_manager, mock_trading_client):
        """Test small order with large account."""
        mock_trading_client.get_account.return_value = MagicMock(
            buying_power=100000.0,
            cash=100000.0,
            portfolio_value=100000.0
        )
        
        # Small order relative to account size
        order_id = order_manager.place_order('AAPL', 1.0, OrderSide.BUY)
        
        assert order_id is not None
        mock_trading_client.submit_order.assert_called_once()


class TestInsufficientCash:
    """Test scenarios with insufficient buying power."""
    
    def test_insufficient_buying_power_error(self, order_manager, mock_trading_client):
        """Test order rejection due to insufficient buying power."""
        # Mock low buying power
        mock_trading_client.get_account.return_value = MagicMock(
            buying_power=100.0,
            cash=100.0,
            portfolio_value=1000.0
        )
        
        # Mock API error for insufficient buying power
        error_response = {"code": 40310000, "message": "insufficient buying power"}
        mock_trading_client.submit_order.side_effect = APIError(error_response)
        
        # Try to place large order
        order_id = order_manager.place_order('AAPL', 1000.0, OrderSide.BUY)
        
        assert order_id is None
    
    def test_order_larger_than_buying_power(self, order_manager, mock_trading_client, mock_data_provider):
        """Test order size larger than available buying power."""
        mock_trading_client.get_account.return_value = MagicMock(
            buying_power=1000.0,
            cash=1000.0,
            portfolio_value=2000.0
        )
        mock_data_provider.get_current_price.return_value = 500.0
        
        # Try to buy 10 shares at $500 = $5000 (exceeds $1000 buying power)
        error_response = {"code": 40310000, "message": "insufficient buying power"}
        mock_trading_client.submit_order.side_effect = APIError(error_response)
        
        order_id = order_manager.place_order('AAPL', 10.0, OrderSide.BUY)
        
        assert order_id is None
    
    def test_buying_power_consumed_by_pending_orders(self, order_manager, mock_trading_client):
        """Test insufficient buying power due to pending orders."""
        mock_trading_client.get_account.return_value = MagicMock(
            buying_power=500.0,  # Reduced due to pending orders
            cash=2000.0,         # Higher cash but tied up in pending orders
            portfolio_value=5000.0
        )
        
        error_response = {"code": 40310000, "message": "insufficient buying power"}
        mock_trading_client.submit_order.side_effect = APIError(error_response)
        
        order_id = order_manager.place_order('AAPL', 10.0, OrderSide.BUY)
        
        assert order_id is None
    
    def test_margin_call_scenario(self, order_manager, mock_trading_client):
        """Test trading during margin call (negative buying power)."""
        mock_trading_client.get_account.return_value = MagicMock(
            buying_power=-1000.0,  # Negative due to margin call
            cash=0.0,
            portfolio_value=8000.0  # Portfolio declined
        )
        
        error_response = {"code": 40310000, "message": "insufficient buying power"}
        mock_trading_client.submit_order.side_effect = APIError(error_response)
        
        order_id = order_manager.place_order('AAPL', 1.0, OrderSide.BUY)
        
        assert order_id is None


class TestZeroCash:
    """Test scenarios with zero or minimal cash."""
    
    def test_zero_cash_balance(self, order_manager, mock_trading_client):
        """Test trading with zero cash (only positions)."""
        mock_trading_client.get_account.return_value = MagicMock(
            buying_power=0.0,
            cash=0.0,
            portfolio_value=10000.0  # All in positions
        )
        mock_trading_client.get_all_positions.return_value = [
            MagicMock(symbol='AAPL', qty=100.0, market_value=10000.0)
        ]
        
        error_response = {"code": 40310000, "message": "insufficient buying power"}
        mock_trading_client.submit_order.side_effect = APIError(error_response)
        
        # Try to buy more (should fail)
        order_id = order_manager.place_order('GOOGL', 1.0, OrderSide.BUY)
        
        assert order_id is None
    
    def test_can_still_sell_with_zero_cash(self, order_manager, mock_trading_client):
        """Test that selling is still possible with zero cash."""
        mock_trading_client.get_account.return_value = MagicMock(
            buying_power=0.0,
            cash=0.0,
            portfolio_value=10000.0
        )
        mock_trading_client.get_all_positions.return_value = [
            MagicMock(symbol='AAPL', qty=100.0, market_value=10000.0)
        ]
        
        # Selling should work even with zero cash
        order_id = order_manager.place_safe_sell_order('AAPL', 10.0)
        
        assert order_id is not None
        mock_trading_client.submit_order.assert_called_once()
    
    def test_minimal_cash_small_order(self, order_manager, mock_trading_client, mock_data_provider):
        """Test small order with minimal cash."""
        mock_trading_client.get_account.return_value = MagicMock(
            buying_power=10.0,  # Very small amount
            cash=10.0,
            portfolio_value=1000.0
        )
        mock_data_provider.get_current_price.return_value = 5.0  # Cheap stock
        
        # Buy small amount that fits in buying power
        order_id = order_manager.place_order('CHEAP', 1.0, OrderSide.BUY)
        
        assert order_id is not None
    
    def test_zero_cash_liquidation_scenario(self, order_manager, mock_trading_client):
        """Test liquidation when cash is zero."""
        mock_trading_client.get_account.return_value = MagicMock(
            buying_power=0.0,
            cash=0.0,
            portfolio_value=5000.0
        )
        mock_trading_client.get_all_positions.return_value = [
            MagicMock(symbol='AAPL', qty=50.0, market_value=5000.0)
        ]
        mock_trading_client.close_position.return_value = MagicMock(id='liquidation_order')
        
        # Liquidation should work regardless of cash position
        order_id = order_manager.liquidate_position('AAPL')
        
        assert order_id is not None
        mock_trading_client.close_position.assert_called_once_with('AAPL')


class TestBuyingPowerCalculations:
    """Test various buying power calculation scenarios."""
    
    def test_buying_power_vs_cash_difference(self, order_manager, mock_trading_client):
        """Test when buying power differs from cash due to margin."""
        mock_trading_client.get_account.return_value = MagicMock(
            buying_power=20000.0,  # 2x leverage
            cash=10000.0,
            portfolio_value=10000.0
        )
        
        # Should be able to use full buying power
        order_id = order_manager.place_order('AAPL', 150.0, OrderSide.BUY)  # $15k order
        
        assert order_id is not None
    
    def test_day_trading_buying_power(self, order_manager, mock_trading_client):
        """Test day trading buying power scenarios."""
        # Pattern day trader with 4x intraday buying power
        mock_trading_client.get_account.return_value = MagicMock(
            buying_power=40000.0,  # 4x for day trading
            cash=10000.0,
            portfolio_value=10000.0,
            day_trading_buying_power=40000.0
        )
        
        # Large intraday order
        order_id = order_manager.place_order('AAPL', 300.0, OrderSide.BUY)  # $30k order
        
        assert order_id is not None
    
    def test_overnight_buying_power_reduction(self, order_manager, mock_trading_client):
        """Test reduced buying power for overnight positions."""
        # End of day: buying power reduced to 2x for overnight
        mock_trading_client.get_account.return_value = MagicMock(
            buying_power=20000.0,  # 2x for overnight
            cash=10000.0,
            portfolio_value=10000.0
        )
        
        order_id = order_manager.place_order('AAPL', 150.0, OrderSide.BUY)
        
        assert order_id is not None


class TestCashManagementEdgeCases:
    """Test edge cases in cash management."""
    
    def test_negative_cash_positive_buying_power(self, order_manager, mock_trading_client):
        """Test scenario with negative cash but positive buying power."""
        # Can happen with margin accounts
        mock_trading_client.get_account.return_value = MagicMock(
            buying_power=5000.0,   # Positive buying power
            cash=-1000.0,          # Negative cash (margin loan)
            portfolio_value=15000.0
        )
        
        # Should still be able to trade with positive buying power
        order_id = order_manager.place_order('AAPL', 30.0, OrderSide.BUY)
        
        assert order_id is not None
    
    def test_settled_vs_unsettled_cash(self, order_manager, mock_trading_client):
        """Test trading with unsettled cash restrictions."""
        mock_trading_client.get_account.return_value = MagicMock(
            buying_power=1000.0,   # Limited by unsettled cash
            cash=5000.0,           # Higher cash but unsettled
            portfolio_value=10000.0
        )
        
        # Order within settled cash limits should work
        order_id = order_manager.place_order('AAPL', 8.0, OrderSide.BUY)  # $800 order
        
        assert order_id is not None
        
        # Order exceeding settled cash should fail
        error_response = {"code": 40310000, "message": "insufficient buying power"}
        mock_trading_client.submit_order.side_effect = APIError(error_response)
        
        order_id_large = order_manager.place_order('AAPL', 50.0, OrderSide.BUY)  # $5000 order
        
        assert order_id_large is None
    
    def test_currency_conversion_impact(self, order_manager, mock_trading_client):
        """Test cash calculations with currency conversion."""
        # Simulate international account with currency conversion
        mock_trading_client.get_account.return_value = MagicMock(
            buying_power=8000.0,   # USD equivalent after conversion
            cash=10000.0,          # Local currency converted
            portfolio_value=20000.0
        )
        
        order_id = order_manager.place_order('AAPL', 60.0, OrderSide.BUY)
        
        assert order_id is not None
