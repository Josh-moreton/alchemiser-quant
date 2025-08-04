#!/usr/bin/env python3
"""
Test market conditions scenarios for the quantitative trading system.
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, time
from alpaca.trading.enums import OrderSide

from the_alchemiser.execution.smart_execution import SmartExecution, is_market_open
from the_alchemiser.execution.alpaca_client import AlpacaClient


@pytest.fixture
def mock_trading_client():
    """Mock Alpaca trading client."""
    client = MagicMock()
    client.submit_order.return_value = MagicMock(id='test_order_123')
    client.get_order_by_id.return_value = MagicMock(id='test_order_123', status='filled')
    client.get_all_positions.return_value = []
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


class TestMarketOpen:
    """Test behavior when market is open."""
    
    def test_market_open_detection(self, mock_trading_client):
        """Test market open detection."""
        # Mock market open
        mock_trading_client.get_clock.return_value = MagicMock(is_open=True)
        assert is_market_open(mock_trading_client) is True
        
        # Mock market closed
        mock_trading_client.get_clock.return_value = MagicMock(is_open=False)
        assert is_market_open(mock_trading_client) is False
    
    def test_orders_placed_when_market_open(self, order_manager, mock_trading_client):
        """Test that orders are placed when market is open."""
        mock_trading_client.get_clock.return_value = MagicMock(is_open=True)
        
        order_id = order_manager.place_order('AAPL', 1.0, OrderSide.BUY)
        
        assert order_id is not None
        mock_trading_client.submit_order.assert_called_once()


class TestMarketClosed:
    """Test behavior when market is closed."""
    
    def test_market_closed_detection(self, mock_trading_client):
        """Test market closed detection."""
        mock_trading_client.get_clock.return_value = MagicMock(is_open=False)
        assert is_market_open(mock_trading_client) is False
    
    def test_orders_handled_when_market_closed_ignore_hours(self, mock_trading_client, mock_data_provider):
        """Test orders with ignore_market_hours=True when market closed."""
        mock_trading_client.get_clock.return_value = MagicMock(is_open=False)
        
        order_manager = SmartExecution(
            mock_trading_client, mock_data_provider, ignore_market_hours=True
        )
        
        order_id = order_manager.place_order('AAPL', 1.0, OrderSide.BUY)
        
        assert order_id is not None
        mock_trading_client.submit_order.assert_called_once()


class TestHighVolatility:
    """Test behavior during high volatility conditions."""
    
    def test_wide_bid_ask_spread(self, order_manager, mock_data_provider):
        """Test handling of wide bid/ask spreads."""
        # Simulate wide spread (5% spread)
        mock_data_provider.get_latest_quote.return_value = (95.0, 105.0)
        mock_data_provider.get_current_price.return_value = 100.0
        
        order_id = order_manager.place_order('VOLATILE_STOCK', 1.0, OrderSide.BUY)
        
        assert order_id is not None
    
    def test_rapid_price_changes(self, order_manager, mock_data_provider):
        """Test handling of rapid price changes."""
        # Simulate price changes between calls
        prices = [100.0, 105.0, 95.0, 102.0]
        mock_data_provider.get_current_price.side_effect = prices
        
        for i in range(len(prices)):
            order_id = order_manager.place_order('VOLATILE_STOCK', 1.0, OrderSide.BUY)
            assert order_id is not None


class TestLowLiquidity:
    """Test behavior with low liquidity assets."""
    
    def test_thinly_traded_asset(self, order_manager, mock_data_provider):
        """Test trading thinly traded assets."""
        # Simulate large spread for illiquid asset
        mock_data_provider.get_latest_quote.return_value = (90.0, 110.0)
        mock_data_provider.get_current_price.return_value = 100.0
        
        order_id = order_manager.place_order('ILLIQUID_STOCK', 0.1, OrderSide.BUY)
        
        assert order_id is not None
    
    def test_large_spread_handling(self, order_manager, mock_data_provider):
        """Test handling of very large spreads."""
        # Mock existing position for sell order
        order_manager.simple_order_manager.trading_client.get_all_positions.return_value = [
            MagicMock(symbol='WIDE_SPREAD_STOCK', qty=10.0, market_value=1000.0)
        ]
        
        # 20% spread
        mock_data_provider.get_latest_quote.return_value = (80.0, 120.0)
        mock_data_provider.get_current_price.return_value = 100.0
        
        order_id = order_manager.place_order('WIDE_SPREAD_STOCK', 1.0, OrderSide.SELL)
        
        assert order_id is not None


class TestAPIErrors:
    """Test handling of API errors and exceptions."""
    
    def test_api_exception_handling(self, mock_trading_client, mock_data_provider):
        """Test graceful handling of API exceptions."""
        mock_trading_client.get_clock.side_effect = Exception("API Error")
        
        # Should return False when API call fails
        result = is_market_open(mock_trading_client)
        assert result is False
    
    def test_order_submission_failure(self, order_manager, mock_trading_client):
        """Test handling of order submission failures."""
        mock_trading_client.submit_order.side_effect = Exception("Order submission failed")
        
        order_id = order_manager.place_order('AAPL', 1.0, OrderSide.BUY)
        
        # Should return None when order fails
        assert order_id is None
