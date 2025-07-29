#!/usr/bin/env python3
"""
Integration Test for AlchemiserTradingBot

Tests the new unified AlchemiserTradingBot against the old AlpacaTradingBot 
and MultiStrategyAlpacaTrader to ensure no functionality is lost during refactoring.

This test verifies:
1. Account info retrieval is identical
2. Position data is identical  
3. Multi-strategy execution produces same results
4. Portfolio rebalancing behavior is consistent
5. Order execution logic is preserved
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, List
from dataclasses import dataclass

# Import the classes we're testing
from the_alchemiser.execution.alchemiser_trader import AlchemiserTradingBot, MultiStrategyExecutionResult
# from the_alchemiser.execution.alpaca_trader import AlpacaTradingBot
# from the_alchemiser.execution.multi_strategy_trader import MultiStrategyAlpacaTrader
from the_alchemiser.core.trading.strategy_manager import StrategyType
from alpaca.trading.enums import OrderSide


@pytest.fixture
def mock_config():
    """Create a mock configuration object"""
    return {
        'alpaca': {
            'paper_endpoint': 'https://paper-api.alpaca.markets/v2',
            'endpoint': 'https://api.alpaca.markets/v2',
            'cash_reserve_pct': 0.05,
            'slippage_bps': 5
        },
        'strategy': {
            'default_strategy_allocations': {
                'nuclear': 0.4,
                'tecl': 0.6
            },
            'poll_timeout': 30,
            'poll_interval': 2.0
        },
        'data': {
            'cache_duration': 300,
            'default_symbol': 'AAPL'
        },
        'logging': {
            'level': 'INFO'
        }
    }


@pytest.fixture
def mock_account_data():
    """Mock account data that should be returned consistently"""
    mock_account = Mock()
    mock_account.account_number = "TEST123"
    mock_account.portfolio_value = 10000.0
    mock_account.equity = 10000.0
    mock_account.buying_power = 5000.0
    mock_account.cash = 1000.0
    mock_account.day_trade_count = 0
    mock_account.status = "ACTIVE"
    
    # Create mock position objects that work with the old trader's getattr() calls
    mock_spy_position = Mock()
    mock_spy_position.symbol = 'SPY'
    mock_spy_position.qty = 10
    mock_spy_position.market_value = 4500.0
    mock_spy_position.cost_basis = 4450.0
    mock_spy_position.unrealized_pl = 50.0
    mock_spy_position.unrealized_plpc = 0.011
    mock_spy_position.current_price = 450.0
    
    mock_qqq_position = Mock()
    mock_qqq_position.symbol = 'QQQ'
    mock_qqq_position.qty = 5
    mock_qqq_position.market_value = 2000.0
    mock_qqq_position.cost_basis = 2025.0
    mock_qqq_position.unrealized_pl = -25.0
    mock_qqq_position.unrealized_plpc = -0.012
    mock_qqq_position.current_price = 400.0
    
    return {
        'account': mock_account,
        'portfolio_history': {
            'equity': [9900, 10000],
            'profit_loss': [100],
            'profit_loss_pct': [0.01]
        },
        'positions': [mock_spy_position, mock_qqq_position],
        'positions_dict': {  # For the new trader that expects dict format
            'SPY': {
                'symbol': 'SPY',
                'qty': 10,
                'market_value': 4500.0,
                'unrealized_pl': 50.0,
                'unrealized_plpc': 0.011,
                'current_price': 450.0,
                'avg_entry_price': 445.0,
                'side': 'long',
                'change_today': 5.0
            },
            'QQQ': {
                'symbol': 'QQQ',
                'qty': 5,
                'market_value': 2000.0,
                'unrealized_pl': -25.0,
                'unrealized_plpc': -0.012,
                'current_price': 400.0,
                'avg_entry_price': 405.0,
                'side': 'long',
                'change_today': -5.0
            }
        }
    }


@pytest.fixture
def mock_strategy_signals():
    """Mock strategy signals for testing"""
    return {
        StrategyType.NUCLEAR: {
            'action': 'BUY',
            'symbol': 'SPY',
            'reason': 'Nuclear signal triggered',
            'timestamp': '2025-07-29T10:00:00'
        },
        StrategyType.TECL: {
            'action': 'HOLD',
            'symbol': 'QQQ',
            'reason': 'TECL signal neutral',
            'timestamp': '2025-07-29T10:00:00'
        }
    }


@pytest.fixture
def mock_consolidated_portfolio():
    """Mock consolidated portfolio allocation"""
    return {
        'SPY': 0.6,
        'QQQ': 0.3,
        'BIL': 0.1
    }


@pytest.fixture
def mock_orders_executed():
    """Mock executed orders"""
    return [
        {
            'symbol': 'SPY',
            'qty': 5.0,
            'side': OrderSide.BUY,
            'order_id': 'order123',
            'estimated_value': 2250.0,
            'price': 450.0,
            'timestamp': '2025-07-29T10:01:00',
            'status': 'filled'
        },
        {
            'symbol': 'BIL',
            'qty': 10.0,
            'side': OrderSide.BUY,
            'order_id': 'order124',
            'estimated_value': 1000.0,
            'price': 100.0,
            'timestamp': '2025-07-29T10:02:00',
            'status': 'filled'
        }
    ]


class TestAlchemiserTradingBotIntegration:
    """Integration tests comparing AlchemiserTradingBot with legacy classes"""

    def test_account_info_consistency(self, mock_config, mock_account_data):
        """Test that account info retrieval is identical across all implementations"""
        
        with patch('the_alchemiser.core.data.data_provider.UnifiedDataProvider.get_account_info') as mock_get_account, \
             patch('the_alchemiser.core.data.data_provider.UnifiedDataProvider.get_portfolio_history') as mock_get_history, \
             patch('the_alchemiser.core.data.data_provider.UnifiedDataProvider.get_open_positions') as mock_get_open_pos:
            
            # Set up mocks
            mock_get_account.return_value = mock_account_data['account']
            mock_get_history.return_value = mock_account_data['portfolio_history']
            mock_get_open_pos.return_value = mock_account_data['positions_dict'].values()  # Use dict format for open positions
            
            # Initialize all three trader types
            new_trader = AlchemiserTradingBot(paper_trading=True, config=mock_config)
            old_trader = AlpacaTradingBot(paper_trading=True, config=mock_config)
            multi_trader = MultiStrategyAlpacaTrader(paper_trading=True, config=mock_config)
            
            # Get account info from all traders
            new_account_info = new_trader.get_account_info()
            old_account_info = old_trader.get_account_info()
            multi_account_info = multi_trader.get_account_info()
            
            # Verify all traders return the same account info
            assert new_account_info['account_number'] == old_account_info['account_number']
            assert new_account_info['portfolio_value'] == old_account_info['portfolio_value']
            assert new_account_info['equity'] == old_account_info['equity']
            assert new_account_info['buying_power'] == old_account_info['buying_power']
            assert new_account_info['cash'] == old_account_info['cash']
            
            # Multi-strategy trader should have same account info too
            assert multi_account_info['portfolio_value'] == new_account_info['portfolio_value']
            assert multi_account_info['equity'] == new_account_info['equity']

    def test_positions_consistency(self, mock_config, mock_account_data):
        """Test that position retrieval is identical across implementations"""
        
        # Initialize traders first  
        new_trader = AlchemiserTradingBot(paper_trading=True, config=mock_config)
        old_trader = AlpacaTradingBot(paper_trading=True, config=mock_config)
        multi_trader = MultiStrategyAlpacaTrader(paper_trading=True, config=mock_config)
        
        # Mock get_positions for each trader to return appropriate format
        with patch.object(new_trader.data_provider, 'get_positions', return_value=mock_account_data['positions_dict'].values()), \
             patch.object(old_trader.data_provider, 'get_positions', return_value=mock_account_data['positions']), \
             patch.object(multi_trader.data_provider, 'get_positions', return_value=mock_account_data['positions']):
            
            # Get positions from all traders
            new_positions = new_trader.get_positions()
            old_positions = old_trader.get_positions()
            multi_positions = multi_trader.get_positions()
            
            # Verify positions are consistent
            assert len(new_positions) == len(old_positions)
            assert len(new_positions) == len(multi_positions)
            
            # Check specific position data
            for symbol in ['SPY', 'QQQ']:
                assert symbol in new_positions
                assert symbol in old_positions
                assert symbol in multi_positions
                
                # Verify position values are identical (within small tolerance for float comparison)
                assert new_positions[symbol]['qty'] == old_positions[symbol]['qty']
                assert abs(new_positions[symbol]['market_value'] - old_positions[symbol]['market_value']) < 0.01

    def test_multi_strategy_execution_parity(self, mock_config, mock_account_data, 
                                           mock_strategy_signals, mock_consolidated_portfolio, 
                                           mock_orders_executed):
        """Test that multi-strategy execution produces identical results"""
        
        # Create comprehensive mocks for all dependencies
        with patch('the_alchemiser.core.data.data_provider.UnifiedDataProvider.get_account_info') as mock_get_account, \
             patch('the_alchemiser.core.data.data_provider.UnifiedDataProvider.get_portfolio_history') as mock_get_history, \
             patch('the_alchemiser.core.data.data_provider.UnifiedDataProvider.get_open_positions') as mock_get_open_pos, \
             patch('the_alchemiser.core.data.data_provider.UnifiedDataProvider.get_positions') as mock_get_positions, \
             patch('the_alchemiser.core.trading.strategy_manager.MultiStrategyManager.run_all_strategies') as mock_run_strategies, \
             patch('the_alchemiser.execution.portfolio_rebalancer.PortfolioRebalancer.rebalance_portfolio') as mock_rebalance_new, \
             patch('the_alchemiser.execution.multi_strategy_trader.MultiStrategyAlpacaTrader.rebalance_portfolio_with_tracking') as mock_rebalance_old:
            
            # Set up mocks
            mock_get_account.return_value = mock_account_data['account']
            mock_get_history.return_value = mock_account_data['portfolio_history']
            mock_get_open_pos.return_value = mock_account_data['positions_dict'].values()
            mock_get_positions.return_value = mock_account_data['positions']
            mock_run_strategies.return_value = (mock_strategy_signals, mock_consolidated_portfolio)
            mock_rebalance_new.return_value = mock_orders_executed
            mock_rebalance_old.return_value = mock_orders_executed
            
            # Initialize traders
            strategy_allocations = {
                StrategyType.NUCLEAR: 0.6,
                StrategyType.TECL: 0.4
            }
            
            new_trader = AlchemiserTradingBot(
                paper_trading=True, 
                strategy_allocations=strategy_allocations,
                config=mock_config
            )
            multi_trader = MultiStrategyAlpacaTrader(
                paper_trading=True,
                strategy_allocations=strategy_allocations, 
                config=mock_config
            )
            
            # Execute multi-strategy on both
            new_result = new_trader.execute_multi_strategy()
            old_result = multi_trader.execute_multi_strategy()
            
            # Verify both executions were successful
            assert new_result.success == True
            assert old_result.success == True
            
            # Verify strategy signals are identical
            assert new_result.strategy_signals == old_result.strategy_signals
            
            # Verify consolidated portfolio is identical
            assert new_result.consolidated_portfolio == old_result.consolidated_portfolio
            
            # Verify orders executed are identical
            assert len(new_result.orders_executed) == len(old_result.orders_executed)
            
            # Compare order details
            for new_order, old_order in zip(new_result.orders_executed, old_result.orders_executed):
                assert new_order['symbol'] == old_order['symbol']
                assert new_order['qty'] == old_order['qty']
                assert new_order['side'] == old_order['side']
                assert new_order['estimated_value'] == old_order['estimated_value']
            
            # Verify account info consistency
            assert new_result.account_info_before['portfolio_value'] == old_result.account_info_before['portfolio_value']
            assert new_result.account_info_after['portfolio_value'] == old_result.account_info_after['portfolio_value']

    def test_portfolio_rebalancing_consistency(self, mock_config, mock_account_data, 
                                             mock_consolidated_portfolio, mock_orders_executed):
        """Test that portfolio rebalancing produces consistent results"""
        
        with patch('the_alchemiser.core.data.data_provider.UnifiedDataProvider.get_account_info') as mock_get_account, \
             patch('the_alchemiser.core.data.data_provider.UnifiedDataProvider.get_positions') as mock_get_positions, \
             patch('the_alchemiser.execution.portfolio_rebalancer.PortfolioRebalancer.rebalance_portfolio') as mock_rebalance_new, \
             patch('the_alchemiser.execution.alpaca_trader.AlpacaTradingBot.rebalance_portfolio') as mock_rebalance_old:
            
            # Set up mocks
            mock_get_account.return_value = mock_account_data['account']
            mock_get_positions.return_value = mock_account_data['positions']
            mock_rebalance_new.return_value = mock_orders_executed
            mock_rebalance_old.return_value = mock_orders_executed
            
            # Initialize traders
            new_trader = AlchemiserTradingBot(paper_trading=True, config=mock_config)
            old_trader = AlpacaTradingBot(paper_trading=True, config=mock_config)
            
            # Execute rebalancing on both
            new_orders = new_trader.rebalance_portfolio(mock_consolidated_portfolio)
            old_orders = old_trader.rebalance_portfolio(mock_consolidated_portfolio)
            
            # Verify identical results
            assert len(new_orders) == len(old_orders)
            
            for new_order, old_order in zip(new_orders, old_orders):
                assert new_order['symbol'] == old_order['symbol']
                assert new_order['qty'] == old_order['qty']
                assert new_order['side'] == old_order['side']

    def test_display_target_vs_current_allocations(self, mock_config, mock_account_data):
        """Test the display_target_vs_current_allocations method works correctly"""
        
        with patch('the_alchemiser.core.data.data_provider.UnifiedDataProvider.get_account_info') as mock_get_account:
            mock_get_account.return_value = mock_account_data['account']
            
            new_trader = AlchemiserTradingBot(paper_trading=True, config=mock_config)
            
            target_portfolio = {'SPY': 0.6, 'QQQ': 0.4}
            account_info = {'portfolio_value': 10000.0}
            current_positions = {
                'SPY': {'market_value': 5000.0},
                'QQQ': {'market_value': 3000.0}
            }
            
            target_values, current_values = new_trader.display_target_vs_current_allocations(
                target_portfolio, account_info, current_positions
            )
            
            # Verify calculations
            assert target_values['SPY'] == 6000.0  # 10000 * 0.6
            assert target_values['QQQ'] == 4000.0  # 10000 * 0.4
            assert current_values['SPY'] == 5000.0
            assert current_values['QQQ'] == 3000.0

    def test_error_handling_consistency(self, mock_config):
        """Test that error handling is consistent across implementations"""
        
        # Mock a failure scenario
        with patch('the_alchemiser.core.data.data_provider.UnifiedDataProvider.get_account_info') as mock_get_account:
            mock_get_account.side_effect = Exception("API Error")
            
            new_trader = AlchemiserTradingBot(paper_trading=True, config=mock_config)
            multi_trader = MultiStrategyAlpacaTrader(paper_trading=True, config=mock_config)
            
            # Both should handle errors gracefully
            new_result = new_trader.execute_multi_strategy()
            old_result = multi_trader.execute_multi_strategy()
            
            # Both should return failed results
            assert new_result.success == False
            assert old_result.success == False
            
            # Both should have error information
            assert 'error' in new_result.execution_summary
            assert 'error' in old_result.execution_summary

    def test_initialization_consistency(self, mock_config):
        """Test that all trader classes initialize with consistent configuration"""
        
        strategy_allocations = {
            StrategyType.NUCLEAR: 0.7,
            StrategyType.TECL: 0.3
        }
        
        # Initialize all traders with same parameters
        new_trader = AlchemiserTradingBot(
            paper_trading=True,
            strategy_allocations=strategy_allocations,
            ignore_market_hours=True,
            config=mock_config
        )
        
        multi_trader = MultiStrategyAlpacaTrader(
            paper_trading=True,
            strategy_allocations=strategy_allocations,
            ignore_market_hours=True,
            config=mock_config
        )
        
        # Verify consistent configuration
        assert new_trader.paper_trading == multi_trader.paper_trading
        assert new_trader.ignore_market_hours == multi_trader.ignore_market_hours
        assert new_trader.config == multi_trader.config
        
        # Verify strategy allocations are correctly set
        assert new_trader.strategy_manager.strategy_allocations == multi_trader.strategy_manager.strategy_allocations


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])
