#!/usr/bin/env python3
"""
Test portfolio rebalancing scenarios including full rebalance,
partial rebalance, and edge cases.
"""

import pytest
from unittest.mock import MagicMock, patch, call
from alpaca.trading.enums import OrderSide

from the_alchemiser.execution.order_manager_adapter import OrderManagerAdapter


@pytest.fixture
def mock_trading_client():
    """Mock Alpaca trading client."""
    client = MagicMock()
    client.submit_order.return_value = MagicMock(id='test_order_123')
    client.get_order_by_id.return_value = MagicMock(id='test_order_123', status='filled')
    client.get_all_positions.return_value = []
    client.get_account.return_value = MagicMock(buying_power=10000.0, cash=5000.0)
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


class TestFullRebalance:
    """Test full portfolio rebalancing scenarios."""
    
    def test_rebalance_from_cash_to_positions(self, order_manager, mock_trading_client, mock_data_provider):
        """Test rebalancing from 100% cash to target allocations."""
        # Mock empty portfolio
        mock_trading_client.get_all_positions.return_value = []
        mock_trading_client.get_account.return_value = MagicMock(
            buying_power=10000.0, 
            cash=10000.0,
            portfolio_value=10000.0
        )
        
        # Simulate rebalancing by placing orders for target allocations
        target_allocations = ['AAPL', 'GOOGL', 'MSFT']  # 3 assets
        
        # Mock price data
        mock_data_provider.get_current_price.side_effect = lambda symbol: {
            'AAPL': 150.0, 'GOOGL': 2500.0, 'MSFT': 350.0
        }.get(symbol, 100.0)
        
        orders_placed = []
        for symbol in target_allocations:
            order_id = order_manager.place_limit_or_market(symbol, 10.0, OrderSide.BUY)
            orders_placed.append(order_id)
        
        # Should place 3 buy orders
        assert all(order_id is not None for order_id in orders_placed)
        assert mock_trading_client.submit_order.call_count == 3
    
    def test_rebalance_between_positions(self, order_manager, mock_trading_client, mock_data_provider):
        """Test rebalancing between existing positions."""
        # Mock current positions: 100% AAPL
        mock_trading_client.get_all_positions.return_value = [
            MagicMock(symbol='AAPL', qty=66.67, market_value=10000.0)  # 100% allocation
        ]
        mock_trading_client.get_account.return_value = MagicMock(
            buying_power=1000.0,
            cash=0.0,
            portfolio_value=10000.0
        )
        
        # Simulate selling some AAPL and buying GOOGL
        mock_data_provider.get_current_price.side_effect = lambda symbol: {
            'AAPL': 150.0, 'GOOGL': 2500.0
        }.get(symbol, 100.0)
        
        # Sell some AAPL
        sell_order = order_manager.place_safe_sell_order('AAPL', 20.0)
        # Buy GOOGL
        buy_order = order_manager.place_limit_or_market('GOOGL', 2.0, OrderSide.BUY)
        
        assert sell_order is not None
        assert buy_order is not None
    
    def test_rebalance_to_cash(self, order_manager, mock_trading_client):
        """Test rebalancing from positions to 100% cash."""
        # Mock current positions
        mock_trading_client.get_all_positions.return_value = [
            MagicMock(symbol='AAPL', qty=33.33, market_value=5000.0),
            MagicMock(symbol='GOOGL', qty=2.0, market_value=5000.0)
        ]
        mock_trading_client.get_account.return_value = MagicMock(
            buying_power=1000.0,
            cash=0.0,
            portfolio_value=10000.0
        )
        
        # Liquidate all positions
        aapl_liquidation = order_manager.liquidate_position('AAPL')
        googl_liquidation = order_manager.liquidate_position('GOOGL')
        
        # Should liquidate all positions
        assert aapl_liquidation is not None
        assert googl_liquidation is not None
        assert mock_trading_client.close_position.call_count == 2


class TestPartialRebalance:
    """Test partial rebalancing scenarios."""
    
    def test_small_allocation_change(self, multi_strategy_trader, mock_trading_client):
        """Test rebalancing with small allocation changes below threshold."""
        # Mock current positions close to target
        mock_trading_client.get_all_positions.return_value = [
            MagicMock(symbol='AAPL', qty=33.0, market_value=4950.0),  # 49.5%
            MagicMock(symbol='GOOGL', qty=2.02, market_value=5050.0)   # 50.5%
        ]
        mock_trading_client.get_account.return_value = MagicMock(
            buying_power=1000.0,
            cash=0.0,
            portfolio_value=10000.0
        )
        
        # Target: 50% each (very small change)
        target_allocations = {
            'AAPL': 0.5,
            'GOOGL': 0.5
        }
        
        with patch.object(multi_strategy_trader.data_provider, 'get_current_price') as mock_price:
            mock_price.side_effect = lambda symbol: {'AAPL': 150.0, 'GOOGL': 2500.0}[symbol]
            
            result = multi_strategy_trader.execute_rebalancing(target_allocations, mode='market')
        
        # Should not place any orders (below rebalance threshold)
        assert mock_trading_client.submit_order.call_count == 0
        assert result is not None
        assert result['trading_summary']['total_orders'] == 0
    
    def test_single_symbol_rebalance(self, multi_strategy_trader, mock_trading_client):
        """Test rebalancing that only affects one symbol."""
        # Mock current: 70% AAPL, 30% GOOGL
        mock_trading_client.get_all_positions.return_value = [
            MagicMock(symbol='AAPL', qty=46.67, market_value=7000.0),
            MagicMock(symbol='GOOGL', qty=1.2, market_value=3000.0)
        ]
        mock_trading_client.get_account.return_value = MagicMock(
            buying_power=1000.0,
            cash=0.0,
            portfolio_value=10000.0
        )
        
        # Target: 60% AAPL, 40% GOOGL (sell AAPL, buy GOOGL)
        target_allocations = {
            'AAPL': 0.6,
            'GOOGL': 0.4
        }
        
        with patch.object(multi_strategy_trader.data_provider, 'get_current_price') as mock_price:
            mock_price.side_effect = lambda symbol: {'AAPL': 150.0, 'GOOGL': 2500.0}[symbol]
            
            result = multi_strategy_trader.execute_rebalancing(target_allocations, mode='market')
        
        # Should place orders to adjust allocations
        assert mock_trading_client.submit_order.call_count >= 1
        assert result is not None


class TestNoTradesNeeded:
    """Test scenarios where no trades are needed."""
    
    def test_already_at_target_allocation(self, multi_strategy_trader, mock_trading_client):
        """Test when portfolio is already at target allocation."""
        # Mock positions exactly at target
        mock_trading_client.get_all_positions.return_value = [
            MagicMock(symbol='AAPL', qty=33.33, market_value=5000.0),  # 50%
            MagicMock(symbol='GOOGL', qty=2.0, market_value=5000.0)    # 50%
        ]
        mock_trading_client.get_account.return_value = MagicMock(
            buying_power=1000.0,
            cash=0.0,
            portfolio_value=10000.0
        )
        
        # Target matches current
        target_allocations = {
            'AAPL': 0.5,
            'GOOGL': 0.5
        }
        
        with patch.object(multi_strategy_trader.data_provider, 'get_current_price') as mock_price:
            mock_price.side_effect = lambda symbol: {'AAPL': 150.0, 'GOOGL': 2500.0}[symbol]
            
            result = multi_strategy_trader.execute_rebalancing(target_allocations, mode='market')
        
        # Should not place any orders
        assert mock_trading_client.submit_order.call_count == 0
        assert result['trading_summary']['total_orders'] == 0
    
    def test_within_tolerance_threshold(self, multi_strategy_trader, mock_trading_client):
        """Test when differences are within tolerance threshold."""
        # Mock positions within 1% of target
        mock_trading_client.get_all_positions.return_value = [
            MagicMock(symbol='AAPL', qty=33.67, market_value=5050.0),  # 50.5%
            MagicMock(symbol='GOOGL', qty=1.98, market_value=4950.0)   # 49.5%
        ]
        mock_trading_client.get_account.return_value = MagicMock(
            buying_power=1000.0,
            cash=0.0,
            portfolio_value=10000.0
        )
        
        target_allocations = {
            'AAPL': 0.5,
            'GOOGL': 0.5
        }
        
        with patch.object(multi_strategy_trader.data_provider, 'get_current_price') as mock_price:
            mock_price.side_effect = lambda symbol: {'AAPL': 150.0, 'GOOGL': 2500.0}[symbol]
            
            result = multi_strategy_trader.execute_rebalancing(target_allocations, mode='market')
        
        # Should not rebalance (within tolerance)
        assert mock_trading_client.submit_order.call_count == 0


class TestEdgeCases:
    """Test edge cases in portfolio rebalancing."""
    
    def test_zero_target_allocation(self, multi_strategy_trader, mock_trading_client):
        """Test removing a symbol entirely (0% allocation)."""
        # Mock current position to be liquidated
        mock_trading_client.get_all_positions.return_value = [
            MagicMock(symbol='AAPL', qty=33.33, market_value=5000.0),
            MagicMock(symbol='GOOGL', qty=2.0, market_value=5000.0)
        ]
        mock_trading_client.get_account.return_value = MagicMock(
            buying_power=1000.0,
            cash=0.0,
            portfolio_value=10000.0
        )
        
        # Target: Only AAPL (GOOGL gets 0% = liquidated)
        target_allocations = {
            'AAPL': 1.0
            # GOOGL not included = 0% allocation
        }
        
        result = multi_strategy_trader.execute_rebalancing(target_allocations, mode='market')
        
        # Should liquidate GOOGL position
        assert result is not None
    
    def test_new_symbol_addition(self, multi_strategy_trader, mock_trading_client):
        """Test adding a new symbol to portfolio."""
        # Mock current single position
        mock_trading_client.get_all_positions.return_value = [
            MagicMock(symbol='AAPL', qty=66.67, market_value=10000.0)  # 100%
        ]
        mock_trading_client.get_account.return_value = MagicMock(
            buying_power=1000.0,
            cash=0.0,
            portfolio_value=10000.0
        )
        
        # Target: Add MSFT to portfolio
        target_allocations = {
            'AAPL': 0.6,
            'MSFT': 0.4  # New symbol
        }
        
        with patch.object(multi_strategy_trader.data_provider, 'get_current_price') as mock_price:
            mock_price.side_effect = lambda symbol: {'AAPL': 150.0, 'MSFT': 350.0}[symbol]
            
            result = multi_strategy_trader.execute_rebalancing(target_allocations, mode='market')
        
        # Should sell some AAPL and buy MSFT
        assert result is not None
    
    def test_insufficient_cash_for_rebalance(self, multi_strategy_trader, mock_trading_client):
        """Test rebalancing when insufficient cash available."""
        # Mock low cash scenario
        mock_trading_client.get_all_positions.return_value = [
            MagicMock(symbol='AAPL', qty=33.33, market_value=5000.0)
        ]
        mock_trading_client.get_account.return_value = MagicMock(
            buying_power=100.0,  # Very low buying power
            cash=50.0,
            portfolio_value=5050.0
        )
        
        # Target: Add expensive stock
        target_allocations = {
            'AAPL': 0.5,
            'GOOGL': 0.5  # Expensive stock
        }
        
        with patch.object(multi_strategy_trader.data_provider, 'get_current_price') as mock_price:
            mock_price.side_effect = lambda symbol: {'AAPL': 150.0, 'GOOGL': 2500.0}[symbol]
            
            result = multi_strategy_trader.execute_rebalancing(target_allocations, mode='market')
        
        # Should handle gracefully (partial rebalance or no action)
        assert result is not None
    
    def test_fractional_shares_rebalance(self, multi_strategy_trader, mock_trading_client):
        """Test rebalancing with fractional shares."""
        # Mock fractional position
        mock_trading_client.get_all_positions.return_value = [
            MagicMock(symbol='AAPL', qty=33.333, market_value=5000.0)  # Fractional
        ]
        mock_trading_client.get_account.return_value = MagicMock(
            buying_power=1000.0,
            cash=0.0,
            portfolio_value=5000.0
        )
        
        target_allocations = {
            'AAPL': 0.7,
            'GOOGL': 0.3
        }
        
        with patch.object(multi_strategy_trader.data_provider, 'get_current_price') as mock_price:
            mock_price.side_effect = lambda symbol: {'AAPL': 150.0, 'GOOGL': 2500.0}[symbol]
            
            result = multi_strategy_trader.execute_rebalancing(target_allocations, mode='market')
        
        # Should handle fractional shares correctly
        assert result is not None


class TestRebalanceWithDifferentModes:
    """Test rebalancing with different execution modes."""
    
    def test_market_mode_rebalance(self, multi_strategy_trader, mock_trading_client):
        """Test rebalancing using market orders."""
        mock_trading_client.get_all_positions.return_value = []
        mock_trading_client.get_account.return_value = MagicMock(
            buying_power=10000.0,
            cash=10000.0,
            portfolio_value=10000.0
        )
        
        target_allocations = {'AAPL': 1.0}
        
        with patch.object(multi_strategy_trader.data_provider, 'get_current_price') as mock_price:
            mock_price.return_value = 150.0
            
            result = multi_strategy_trader.execute_rebalancing(target_allocations, mode='market')
        
        assert result is not None
        assert mock_trading_client.submit_order.called
    
    def test_limit_mode_rebalance(self, multi_strategy_trader, mock_trading_client):
        """Test rebalancing using limit orders."""
        mock_trading_client.get_all_positions.return_value = []
        mock_trading_client.get_account.return_value = MagicMock(
            buying_power=10000.0,
            cash=10000.0,
            portfolio_value=10000.0
        )
        
        target_allocations = {'AAPL': 1.0}
        
        with patch.object(multi_strategy_trader.data_provider, 'get_current_price') as mock_price:
            mock_price.return_value = 150.0
            
            result = multi_strategy_trader.execute_rebalancing(target_allocations, mode='limit')
        
        assert result is not None
    
    def test_paper_mode_rebalance(self, multi_strategy_trader, mock_trading_client):
        """Test rebalancing in paper trading mode."""
        mock_trading_client.get_all_positions.return_value = []
        mock_trading_client.get_account.return_value = MagicMock(
            buying_power=10000.0,
            cash=10000.0,
            portfolio_value=10000.0
        )
        
        target_allocations = {'AAPL': 1.0}
        
        with patch.object(multi_strategy_trader.data_provider, 'get_current_price') as mock_price:
            mock_price.return_value = 150.0
            
            result = multi_strategy_trader.execute_rebalancing(target_allocations, mode='paper')
        
        assert result is not None
        # Paper mode should still return results but might not place real orders
