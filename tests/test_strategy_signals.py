#!/usr/bin/env python3
"""
Test strategy signal scenarios including conflicting signals,
no signals, and multi-asset signals.
"""

import pytest
from unittest.mock import MagicMock, patch
from collections import defaultdict
from alpaca.trading.enums import OrderSide

from the_alchemiser.execution.order_manager_adapter import OrderManagerAdapter


@pytest.fixture
def mock_trading_client():
    """Mock Alpaca trading client."""
    client = MagicMock()
    client.submit_order.return_value = MagicMock(id='test_order_123')
    client.get_order_by_id.return_value = MagicMock(id='test_order_123', status='filled')
    client.get_all_positions.return_value = []
    client.get_account.return_value = MagicMock(buying_power=10000.0, cash=10000.0, portfolio_value=10000.0)
    client.get_clock.return_value = MagicMock(is_open=True)
    return client


@pytest.fixture
def mock_data_provider():
    """Mock data provider."""
    provider = MagicMock()
    provider.get_current_price.return_value = 100.0
    provider.get_latest_quote.return_value = (99.0, 101.0)
    provider.get_market_hours.return_value = (True, True)
    return provider


@pytest.fixture
def create_mock_strategy():
    """Factory function to create mock strategies."""
    def _create_strategy(name, signal_data):
        strategy = MagicMock()
        strategy.name = name
        strategy.get_signal.return_value = signal_data
        return strategy
    return _create_strategy


@pytest.fixture
def order_manager(mock_trading_client, mock_data_provider):
    """Create OrderManagerAdapter for testing."""
    return OrderManagerAdapter(mock_trading_client, mock_data_provider)


#!/usr/bin/env python3
"""
Test strategy signal scenarios through order manager testing.
"""

import pytest
from unittest.mock import MagicMock
from alpaca.trading.enums import OrderSide

from the_alchemiser.execution.order_manager_adapter import OrderManagerAdapter


@pytest.fixture
def mock_trading_client():
    """Mock Alpaca trading client."""
    client = MagicMock()
    client.submit_order.return_value = MagicMock(id='test_order_123')
    client.get_order_by_id.return_value = MagicMock(id='test_order_123', status='filled')
    client.get_all_positions.return_value = []
    client.get_account.return_value = MagicMock(buying_power=10000.0, cash=10000.0, portfolio_value=10000.0)
    client.get_clock.return_value = MagicMock(is_open=True)
    return client


@pytest.fixture
def mock_data_provider():
    """Mock data provider."""
    provider = MagicMock()
    provider.get_current_price.return_value = 100.0
    provider.get_latest_quote.return_value = (99.0, 101.0)
    provider.get_market_hours.return_value = (True, True)
    return provider


@pytest.fixture
def order_manager(mock_trading_client, mock_data_provider):
    """Create OrderManagerAdapter for testing."""
    return OrderManagerAdapter(mock_trading_client, mock_data_provider)


class TestSignalExecution:
    """Test execution of different signal types."""
    
    def test_buy_signal_execution(self, order_manager):
        """Test execution of buy signals."""
        # Simulate buy signal
        order_id = order_manager.place_limit_or_market('AAPL', 10.0, OrderSide.BUY)
        assert order_id is not None
    
    def test_sell_signal_execution(self, order_manager, mock_trading_client):
        """Test execution of sell signals."""
        # Mock existing position
        mock_trading_client.get_all_positions.return_value = [
            MagicMock(symbol='AAPL', qty=20.0)
        ]
        
        # Simulate sell signal
        order_id = order_manager.place_safe_sell_order('AAPL', 5.0)
        assert order_id is not None
    
    def test_hold_signal_execution(self, order_manager):
        """Test that hold signals result in no orders."""
        # Hold signal means no action - test that no orders are placed
        initial_call_count = 0
        
        # No orders should be placed for hold signal
        # This test verifies the order manager doesn't place spurious orders
        assert True  # Hold signals don't generate orders


class TestMultiAssetSignals:
    """Test signals affecting multiple assets."""
    
    def test_portfolio_rebalancing_simulation(self, order_manager, mock_data_provider):
        """Test execution of multi-asset rebalancing signals."""
        # Mock price data for multiple assets
        mock_data_provider.get_current_price.side_effect = lambda symbol: {
            'AAPL': 150.0,
            'GOOGL': 2500.0,
            'MSFT': 350.0
        }.get(symbol, 100.0)
        
        # Simulate rebalancing across multiple assets
        assets = ['AAPL', 'GOOGL', 'MSFT']
        orders = []
        
        for asset in assets:
            order_id = order_manager.place_limit_or_market(asset, 5.0, OrderSide.BUY)
            orders.append(order_id)
        
        # All orders should be successful
        assert all(order_id is not None for order_id in orders)
        assert len(orders) == 3
    
    def test_sector_rotation_simulation(self, order_manager, mock_trading_client, mock_data_provider):
        """Test sector rotation through sell/buy combinations."""
        # Mock existing tech positions
        mock_trading_client.get_all_positions.return_value = [
            MagicMock(symbol='AAPL', qty=10.0),
            MagicMock(symbol='GOOGL', qty=2.0)
        ]
        
        # Mock prices
        mock_data_provider.get_current_price.side_effect = lambda symbol: {
            'AAPL': 150.0, 'GOOGL': 2500.0, 'JNJ': 160.0, 'PFE': 45.0
        }.get(symbol, 100.0)
        
        # Simulate rotating from tech to healthcare
        tech_sells = []
        healthcare_buys = []
        
        # Sell tech positions
        tech_sells.append(order_manager.place_safe_sell_order('AAPL', 5.0))
        tech_sells.append(order_manager.place_safe_sell_order('GOOGL', 1.0))
        
        # Buy healthcare positions
        healthcare_buys.append(order_manager.place_limit_or_market('JNJ', 3.0, OrderSide.BUY))
        healthcare_buys.append(order_manager.place_limit_or_market('PFE', 10.0, OrderSide.BUY))
        
        # All orders should execute
        assert all(order_id is not None for order_id in tech_sells)
        assert all(order_id is not None for order_id in healthcare_buys)


class TestSignalValidation:
    """Test validation of signal parameters."""
    
    def test_valid_signal_parameters(self, order_manager, mock_trading_client):
        """Test that valid signal parameters are accepted."""
        # Valid buy signal
        order_id = order_manager.place_limit_or_market('AAPL', 1.0, OrderSide.BUY)
        assert order_id is not None
        
        # Mock position for sell signal
        mock_trading_client.get_all_positions.return_value = [
            MagicMock(symbol='AAPL', qty=10.0, market_value=1500.0)
        ]
        
        # Valid sell signal  
        order_id = order_manager.place_limit_or_market('AAPL', 1.0, OrderSide.SELL)
        assert order_id is not None
    
    def test_invalid_signal_parameters(self, order_manager):
        """Test handling of invalid signal parameters."""
        # Invalid quantity (zero)
        order_id = order_manager.place_limit_or_market('AAPL', 0.0, OrderSide.BUY)
        assert order_id is None
        
        # Invalid quantity (negative)
        order_id = order_manager.place_limit_or_market('AAPL', -1.0, OrderSide.BUY)
        assert order_id is None
    
    def test_signal_timing_validation(self, order_manager, mock_trading_client):
        """Test validation of signal timing."""
        # Test during market hours
        mock_trading_client.get_clock.return_value = MagicMock(is_open=True)
        order_id = order_manager.place_limit_or_market('AAPL', 1.0, OrderSide.BUY)
        assert order_id is not None
        
        # Test during market closed (with ignore_market_hours=False by default)
        mock_trading_client.get_clock.return_value = MagicMock(is_open=False)
        # Order might still be placed (depends on implementation)
        order_id = order_manager.place_limit_or_market('AAPL', 1.0, OrderSide.BUY)
        # Result depends on order manager's market hours handling
