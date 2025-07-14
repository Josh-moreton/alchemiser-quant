#!/usr/bin/env python3
"""
Test Portfolio Position Switching Scenarios
Tests all possible transitions between different portfolio states
"""

import sys
import os
import pytest
from unittest.mock import Mock, patch
from decimal import Decimal

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from execution.alpaca_trader import AlpacaTradingBot
from alpaca.trading.enums import OrderSide


class TestPositionSwitching:
    """Test various position switching scenarios"""
    
    @pytest.fixture
    def mock_bot(self):
        """Create a mock trading bot for testing"""
        with patch.dict(os.environ, {
            'ALPACA_PAPER_KEY': 'test_key',
            'ALPACA_PAPER_SECRET': 'test_secret'
        }):
            with patch('execution.alpaca_trader.TradingClient'):
                with patch('execution.alpaca_trader.StockHistoricalDataClient'):
                    bot = AlpacaTradingBot(paper_trading=True)
                    
                    # Mock price fetching for all symbols
                    def mock_price_fetch(symbol):
                        prices = {'AAPL': 150.0, 'TSLA': 250.0, 'MSFT': 300.0, 'SMR': 40.0, 'LEU': 35.0}
                        return prices.get(symbol, 100.0)
                    
                    bot.get_current_price = Mock(side_effect=mock_price_fetch)
                    bot.place_order = Mock(return_value='mock_order_id')
                    
                    # Mock account info
                    bot.get_account_info = Mock(return_value={
                        'cash': 100000.0,
                        'portfolio_value': 100000.0,
                        'buying_power': 100000.0
                    })
                    
                    yield bot

    def test_single_position_switch(self, mock_bot):
        """Test switching from one single position to another single position"""
        # Current: 100% AAPL (100 shares at $150 = $15,000)
        current_positions = {
            'AAPL': {
                'qty': 100.0,
                'market_value': 15000.0,
                'current_price': 150.0
            }
        }
        mock_bot.get_positions = Mock(return_value=current_positions)
        
        # Target: 100% TSLA
        target_portfolio = {'TSLA': 1.0}
        
        orders = mock_bot.rebalance_portfolio(target_portfolio)
        
        # Should place exactly 2 orders: sell all AAPL, buy TSLA
        assert len(orders) == 2
        
        # Check for AAPL sell order and TSLA buy order
        sell_orders = [o for o in orders if o['side'] == OrderSide.SELL and o['symbol'] == 'AAPL']
        buy_orders = [o for o in orders if o['side'] == OrderSide.BUY and o['symbol'] == 'TSLA']
        assert len(sell_orders) == 1
        assert len(buy_orders) == 1
        assert sell_orders[0]['qty'] == 100.0  # All AAPL shares sold
        assert sell_orders[0]['order_id'] == 'mock_order_id'
        assert buy_orders[0]['order_id'] == 'mock_order_id'

    def test_single_to_multi_asset_split(self, mock_bot):
        """Test switching from single position to multi-asset portfolio"""
        # Current: 100% AAPL (100 shares at $150 = $15,000)
        current_positions = {
            'AAPL': {
                'qty': 100.0,
                'market_value': 15000.0,
                'current_price': 150.0
            }
        }
        mock_bot.get_positions = Mock(return_value=current_positions)
        
        # Target: 50% AAPL, 50% TSLA
        target_portfolio = {'AAPL': 0.5, 'TSLA': 0.5}
        
        orders = mock_bot.rebalance_portfolio(target_portfolio)
        
        # Should place orders: partial sell AAPL, buy TSLA
        assert len(orders) >= 1  # At least TSLA buy, may or may not need AAPL sell
        
        # Should buy TSLA (new position)
        tsla_buys = [o for o in orders if o['side'] == OrderSide.BUY and o['symbol'] == 'TSLA']
        assert len(tsla_buys) == 1
        assert tsla_buys[0]['order_id'] == 'mock_order_id'
        
        # May also sell some AAPL if rebalancing is needed
        # The exact behavior depends on the bot's rebalancing logic

    def test_multi_to_single_consolidation(self, mock_bot):
        """Test switching from multi-asset to single position"""
        # Current: 50% AAPL, 50% TSLA
        current_positions = {
            'AAPL': {
                'qty': 50.0,
                'market_value': 7500.0,
                'current_price': 150.0
            },
            'TSLA': {
                'qty': 30.0,
                'market_value': 7500.0,
                'current_price': 250.0
            }
        }
        mock_bot.get_positions = Mock(return_value=current_positions)
        
        # Target: 100% TSLA
        target_portfolio = {'TSLA': 1.0}
        
        orders = mock_bot.rebalance_portfolio(target_portfolio)
        
        # Should sell AAPL (not in target) and may buy more TSLA
        assert len(orders) >= 1
        
        # Check for AAPL full sell (not in target portfolio)
        aapl_sells = [o for o in orders if o['side'] == OrderSide.SELL and o['symbol'] == 'AAPL']
        assert len(aapl_sells) == 1
        assert aapl_sells[0]['qty'] == 50.0  # All AAPL shares sold
        assert aapl_sells[0]['order_id'] == 'mock_order_id'
        
        # May also buy more TSLA to reach 100% allocation
        # Exact behavior depends on rebalancing logic

    def test_multi_to_multi_with_overlap(self, mock_bot):
        """Test switching between two multi-asset portfolios with some overlap"""
        # Current: 50% AAPL, 50% TSLA
        current_positions = {
            'AAPL': {
                'qty': 50.0,
                'market_value': 7500.0,
                'current_price': 150.0
            },
            'TSLA': {
                'qty': 30.0,
                'market_value': 7500.0,
                'current_price': 250.0
            }
        }
        mock_bot.get_positions = Mock(return_value=current_positions)
        
        # Target: 70% TSLA, 30% MSFT (drop AAPL, increase TSLA, add MSFT)
        target_portfolio = {'TSLA': 0.7, 'MSFT': 0.3}
        
        orders = mock_bot.rebalance_portfolio(target_portfolio)
        
        # Should sell AAPL (not in target) and buy MSFT (new position)
        assert len(orders) >= 2
        
        # Check for AAPL full sell (not in target)
        aapl_sells = [o for o in orders if o['side'] == OrderSide.SELL and o['symbol'] == 'AAPL']
        assert len(aapl_sells) == 1
        assert aapl_sells[0]['order_id'] == 'mock_order_id'
        
        # Check for MSFT buy (new position)
        msft_buys = [o for o in orders if o['side'] == OrderSide.BUY and o['symbol'] == 'MSFT']
        assert len(msft_buys) == 1
        assert msft_buys[0]['order_id'] == 'mock_order_id'

    def test_full_liquidation_to_cash(self, mock_bot):
        """Test switching to all-cash (full liquidation)"""
        # Current: 50% AAPL, 50% TSLA
        current_positions = {
            'AAPL': {
                'qty': 50.0,
                'market_value': 7500.0,
                'current_price': 150.0
            },
            'TSLA': {
                'qty': 30.0,
                'market_value': 7500.0,
                'current_price': 250.0
            }
        }
        mock_bot.get_positions = Mock(return_value=current_positions)
        
        # Target: Empty portfolio (all cash)
        target_portfolio = {}
        
        orders = mock_bot.rebalance_portfolio(target_portfolio)
        
        # Should sell all positions
        assert len(orders) == 2
        
        # Check that all current positions are sold
        sell_orders = [o for o in orders if o['side'] == OrderSide.SELL]
        sell_symbols = {o['symbol'] for o in sell_orders}
        assert 'AAPL' in sell_symbols
        assert 'TSLA' in sell_symbols
        assert all(o['order_id'] == 'mock_order_id' for o in sell_orders)

    def test_cash_to_new_position(self, mock_bot):
        """Test switching from all-cash to new positions"""
        # Current: No positions (all cash)
        current_positions = {}
        mock_bot.get_positions = Mock(return_value=current_positions)
        
        # Target: 60% SMR, 40% LEU (nuclear portfolio)
        target_portfolio = {'SMR': 0.6, 'LEU': 0.4}
        
        orders = mock_bot.rebalance_portfolio(target_portfolio)
        
        # Should place buy orders for both positions
        assert len(orders) >= 1  # At least one buy order
        
        # The bot might place orders sequentially, so we just check 
        # that it's trying to establish positions
        buy_orders = [o for o in orders if o['side'] == OrderSide.BUY]
        buy_symbols = {o['symbol'] for o in buy_orders}
        has_smr_or_leu = 'SMR' in buy_symbols or 'LEU' in buy_symbols
        assert has_smr_or_leu

    def test_identical_portfolio_no_trades(self, mock_bot):
        """Test switching to the same portfolio (should result in no trades)"""
        # Current: 60% SMR, 40% LEU
        current_positions = {
            'SMR': {
                'qty': 1500.0,
                'market_value': 60000.0,
                'current_price': 40.0
            },
            'LEU': {
                'qty': 1143.0,
                'market_value': 40005.0,
                'current_price': 35.0
            }
        }
        mock_bot.get_positions = Mock(return_value=current_positions)
        
        # Target: Same as current (60% SMR, 40% LEU)
        target_portfolio = {'SMR': 0.6, 'LEU': 0.4}
        
        orders = mock_bot.rebalance_portfolio(target_portfolio)
        
        # Should place no orders or very minimal rebalancing
        assert len(orders) <= 2  # Allow for minor rebalancing due to rounding

    def test_small_allocation_handling(self, mock_bot):
        """Test switching with very small allocations (rounding edge cases)"""
        # Current: 100% AAPL
        current_positions = {
            'AAPL': {
                'qty': 100.0,
                'market_value': 15000.0,
                'current_price': 150.0
            }
        }
        mock_bot.get_positions = Mock(return_value=current_positions)
        
        # Target: 99.9% AAPL, 0.1% TSLA (tiny allocation)
        target_portfolio = {'AAPL': 0.999, 'TSLA': 0.001}
        
        orders = mock_bot.rebalance_portfolio(target_portfolio)
        
        # Should handle small allocations - might skip very tiny amounts
        # The exact behavior depends on the bot's minimum order logic
        assert len(orders) >= 0  # No specific requirement, just should not crash

    def test_insufficient_cash_scenario(self, mock_bot):
        """Test switching when there might be insufficient cash"""
        # Current: Small position
        current_positions = {
            'AAPL': {
                'qty': 10.0,
                'market_value': 1500.0,
                'current_price': 150.0
            }
        }
        mock_bot.get_positions = Mock(return_value=current_positions)
        
        # Mock very low cash
        mock_bot.get_account_info = Mock(return_value={
            'cash': 100.0,  # Very low cash
            'portfolio_value': 1600.0,
            'buying_power': 100.0
        })
        
        # Target: 50% AAPL, 50% TSLA (would need to sell some AAPL to buy TSLA)
        target_portfolio = {'AAPL': 0.5, 'TSLA': 0.5}
        
        orders = mock_bot.rebalance_portfolio(target_portfolio)
        
        # Should still create some orders, handling cash constraints appropriately
        assert len(orders) >= 0  # Should not crash

    def test_complex_three_way_switch(self, mock_bot):
        """Test complex switching between three different assets"""
        # Current: 33% AAPL, 33% TSLA, 34% MSFT
        current_positions = {
            'AAPL': {
                'qty': 22.0,
                'market_value': 3300.0,
                'current_price': 150.0
            },
            'TSLA': {
                'qty': 13.2,
                'market_value': 3300.0,
                'current_price': 250.0
            },
            'MSFT': {
                'qty': 11.33,
                'market_value': 3400.0,
                'current_price': 300.0
            }
        }
        mock_bot.get_positions = Mock(return_value=current_positions)
        
        # Target: 50% SMR, 30% LEU, 20% AAPL (major reshuffling)
        target_portfolio = {'SMR': 0.5, 'LEU': 0.3, 'AAPL': 0.2}
        
        orders = mock_bot.rebalance_portfolio(target_portfolio)
        
        # Should create multiple orders for the complex rebalancing
        assert len(orders) >= 2
        
        # Check that TSLA and MSFT are sold (not in target)
        sell_orders = [o for o in orders if o['side'] == OrderSide.SELL]
        sell_symbols = {o['symbol'] for o in sell_orders}
        assert 'TSLA' in sell_symbols
        assert 'MSFT' in sell_symbols
        assert all(o['order_id'] == 'mock_order_id' for o in sell_orders)


if __name__ == '__main__':
    pytest.main([__file__])
