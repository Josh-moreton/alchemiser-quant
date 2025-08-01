#!/usr/bin/env python3
"""
Unit Tests for TradingEngine

Tests individual methods and components of the TradingEngine class
in isolation using mocks to ensure each method works correctly.
"""

import pytest
import logging
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from typing import Dict, List

from the_alchemiser.execution.trading_engine import TradingEngine, MultiStrategyExecutionResult
from the_alchemiser.core.trading.strategy_manager import StrategyType
from alpaca.trading.enums import OrderSide


class TestTradingEngineUnit:
    """Unit tests for TradingEngine class methods"""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration"""
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
            }
        }

    @pytest.fixture
    @patch('the_alchemiser.execution.trading_engine.UnifiedDataProvider')
    @patch('the_alchemiser.execution.trading_engine.SmartExecution')
    @patch('the_alchemiser.execution.trading_engine.PortfolioRebalancer')
    @patch('the_alchemiser.execution.trading_engine.MultiStrategyManager')
    def trading_engine(self, mock_strategy_manager, mock_rebalancer, 
                      mock_smart_execution, mock_data_provider, mock_config):
        """Create a TradingEngine instance with mocked dependencies"""
        with patch('the_alchemiser.core.config.get_config', return_value=mock_config):
            engine = TradingEngine(paper_trading=True)
            
            # Set up mock returns
            engine.data_provider = mock_data_provider.return_value
            engine.order_manager = mock_smart_execution.return_value
            engine.portfolio_rebalancer = mock_rebalancer.return_value
            engine.strategy_manager = mock_strategy_manager.return_value
            
            return engine

    def test_init_paper_trading(self, mock_config):
        """Test TradingEngine initialization in paper trading mode"""
        with patch('the_alchemiser.core.config.get_config', return_value=mock_config), \
             patch('the_alchemiser.execution.trading_engine.UnifiedDataProvider') as mock_dp, \
             patch('the_alchemiser.execution.trading_engine.SmartExecution') as mock_se, \
             patch('the_alchemiser.execution.trading_engine.PortfolioRebalancer') as mock_pr, \
             patch('the_alchemiser.execution.trading_engine.MultiStrategyManager') as mock_sm:
            
            engine = TradingEngine(paper_trading=True)
            
            assert engine.paper_trading is True
            assert engine.ignore_market_hours is False
            assert engine.config == mock_config
            
            # Verify dependencies were initialized
            mock_dp.assert_called_once()
            mock_se.assert_called_once()
            mock_pr.assert_called_once()
            mock_sm.assert_called_once()

    def test_init_live_trading(self, mock_config):
        """Test TradingEngine initialization in live trading mode"""
        with patch('the_alchemiser.core.config.get_config', return_value=mock_config), \
             patch('the_alchemiser.execution.trading_engine.UnifiedDataProvider') as mock_dp, \
             patch('the_alchemiser.execution.trading_engine.SmartExecution') as mock_se, \
             patch('the_alchemiser.execution.trading_engine.PortfolioRebalancer') as mock_pr, \
             patch('the_alchemiser.execution.trading_engine.MultiStrategyManager') as mock_sm:
            
            engine = TradingEngine(paper_trading=False)
            
            assert engine.paper_trading is False
            mock_dp.assert_called_once_with(paper_trading=False, config=mock_config)

    def test_init_with_custom_allocations(self, mock_config):
        """Test TradingEngine initialization with custom strategy allocations"""
        custom_allocations = {
            StrategyType.NUCLEAR: 0.7,
            StrategyType.TECL: 0.3
        }
        
        with patch('the_alchemiser.core.config.get_config', return_value=mock_config), \
             patch('the_alchemiser.execution.trading_engine.UnifiedDataProvider'), \
             patch('the_alchemiser.execution.trading_engine.SmartExecution'), \
             patch('the_alchemiser.execution.trading_engine.PortfolioRebalancer'), \
             patch('the_alchemiser.execution.trading_engine.MultiStrategyManager') as mock_sm:
            
            engine = TradingEngine(
                paper_trading=True, 
                strategy_allocations=custom_allocations
            )
            
            mock_sm.assert_called_once_with(custom_allocations, config=mock_config)

    def test_get_account_info_success(self, trading_engine):
        """Test successful account info retrieval"""
        mock_account_data = {
            'account_number': 'TEST123',
            'portfolio_value': 100000.0,
            'equity': 95000.0,
            'cash': 5000.0,
            'buying_power': 200000.0
        }
        
        with patch('the_alchemiser.utils.account_utils.extract_comprehensive_account_data', 
                   return_value=mock_account_data) as mock_extract:
            
            result = trading_engine.get_account_info()
            
            assert result == mock_account_data
            mock_extract.assert_called_once_with(trading_engine.data_provider)

    def test_get_account_info_failure(self, trading_engine):
        """Test account info retrieval failure"""
        with patch('the_alchemiser.utils.account_utils.extract_comprehensive_account_data', 
                   return_value={}) as mock_extract:
            
            result = trading_engine.get_account_info()
            
            assert result == {}
            mock_extract.assert_called_once_with(trading_engine.data_provider)

    def test_get_positions_success(self, trading_engine):
        """Test successful position retrieval"""
        mock_positions = [
            {'symbol': 'SPY', 'qty': '10', 'market_value': '4500.0'},
            {'symbol': 'QQQ', 'qty': '5', 'market_value': '2000.0'}
        ]
        
        trading_engine.data_provider.get_positions.return_value = mock_positions
        
        result = trading_engine.get_positions()
        
        expected = {
            'SPY': {'symbol': 'SPY', 'qty': '10', 'market_value': '4500.0'},
            'QQQ': {'symbol': 'QQQ', 'qty': '5', 'market_value': '2000.0'}
        }
        assert result == expected

    def test_get_positions_empty(self, trading_engine):
        """Test position retrieval when no positions exist"""
        trading_engine.data_provider.get_positions.return_value = []
        
        result = trading_engine.get_positions()
        
        assert result == {}

    def test_get_positions_with_objects(self, trading_engine):
        """Test position retrieval with position objects instead of dicts"""
        mock_position = Mock()
        mock_position.symbol = 'AAPL'
        
        trading_engine.data_provider.get_positions.return_value = [mock_position]
        
        result = trading_engine.get_positions()
        
        assert 'AAPL' in result
        assert result['AAPL'] == mock_position

    def test_get_current_price_success(self, trading_engine):
        """Test successful current price retrieval"""
        trading_engine.data_provider.get_current_price.return_value = 450.75
        
        result = trading_engine.get_current_price('SPY')
        
        assert result == 450.75
        trading_engine.data_provider.get_current_price.assert_called_once_with('SPY')

    def test_get_current_price_failure(self, trading_engine):
        """Test current price retrieval failure"""
        trading_engine.data_provider.get_current_price.return_value = None
        
        result = trading_engine.get_current_price('INVALID')
        
        assert result == 0.0

    def test_get_current_prices_success(self, trading_engine):
        """Test successful multiple price retrieval"""
        def mock_get_price(symbol):
            prices = {'SPY': 450.75, 'QQQ': 380.25, 'AAPL': 175.50}
            return prices.get(symbol)
        
        trading_engine.data_provider.get_current_price.side_effect = mock_get_price
        
        result = trading_engine.get_current_prices(['SPY', 'QQQ', 'AAPL'])
        
        expected = {'SPY': 450.75, 'QQQ': 380.25, 'AAPL': 175.50}
        assert result == expected

    def test_get_current_prices_with_failures(self, trading_engine):
        """Test multiple price retrieval with some failures"""
        def mock_get_price(symbol):
            if symbol == 'INVALID':
                return None
            return 100.0
        
        trading_engine.data_provider.get_current_price.side_effect = mock_get_price
        
        result = trading_engine.get_current_prices(['SPY', 'INVALID', 'QQQ'])
        
        expected = {'SPY': 100.0, 'QQQ': 100.0}
        assert result == expected

    def test_place_order_success(self, trading_engine):
        """Test successful order placement"""
        trading_engine.order_manager.place_order.return_value = 'order_123'
        
        result = trading_engine.place_order('SPY', 10, OrderSide.BUY)
        
        assert result == 'order_123'
        trading_engine.order_manager.place_order.assert_called_once_with(
            'SPY', 10, OrderSide.BUY, 3, 30, 2.0, None
        )

    def test_place_order_failure(self, trading_engine):
        """Test order placement failure"""
        trading_engine.order_manager.place_order.return_value = None
        
        result = trading_engine.place_order('SPY', 10, OrderSide.BUY)
        
        assert result is None

    def test_rebalance_portfolio_success(self, trading_engine):
        """Test successful portfolio rebalancing"""
        target_portfolio = {'SPY': 0.6, 'QQQ': 0.4}
        mock_orders = [
            {'symbol': 'SPY', 'side': 'BUY', 'qty': 5, 'order_id': 'order_1'},
            {'symbol': 'QQQ', 'side': 'SELL', 'qty': 2, 'order_id': 'order_2'}
        ]
        
        trading_engine.portfolio_rebalancer.rebalance_portfolio.return_value = mock_orders
        
        result = trading_engine.rebalance_portfolio(target_portfolio)
        
        assert result == mock_orders
        trading_engine.portfolio_rebalancer.rebalance_portfolio.assert_called_once_with(
            target_portfolio, None
        )

    def test_execute_rebalancing_compatibility(self, trading_engine):
        """Test execute_rebalancing method for backwards compatibility"""
        target_allocations = {'SPY': 0.7, 'BIL': 0.3}
        mock_orders = [{'symbol': 'SPY', 'side': 'BUY', 'qty': 3}]
        
        trading_engine.portfolio_rebalancer.rebalance_portfolio.return_value = mock_orders
        
        result = trading_engine.execute_rebalancing(target_allocations)
        
        expected = {
            'trading_summary': {
                'total_orders': 1,
                'orders_executed': mock_orders
            },
            'orders': mock_orders
        }
        assert result == expected

    def test_wait_for_settlement_success(self, trading_engine):
        """Test successful order settlement waiting"""
        sell_orders = [{'order_id': 'order_1'}, {'order_id': 'order_2'}]
        trading_engine.order_manager.wait_for_settlement.return_value = True
        
        result = trading_engine.wait_for_settlement(sell_orders)
        
        assert result is True
        trading_engine.order_manager.wait_for_settlement.assert_called_once_with(
            sell_orders, 60, 2.0
        )

    def test_wait_for_settlement_timeout(self, trading_engine):
        """Test order settlement timeout"""
        sell_orders = [{'order_id': 'order_1'}]
        trading_engine.order_manager.wait_for_settlement.return_value = False
        
        result = trading_engine.wait_for_settlement(sell_orders, max_wait_time=30)
        
        assert result is False
        trading_engine.order_manager.wait_for_settlement.assert_called_once_with(
            sell_orders, 30, 2.0
        )

    def test_get_multi_strategy_performance_report_success(self, trading_engine):
        """Test successful performance report generation"""
        mock_positions = {'SPY': {'qty': 10}}
        mock_performance = {'nuclear': {'returns': 0.15}, 'tecl': {'returns': 0.08}}
        
        trading_engine.data_provider.get_positions.return_value = [
            {'symbol': 'SPY', 'qty': 10}
        ]
        trading_engine.strategy_manager.strategy_allocations = {
            StrategyType.NUCLEAR: 0.6,
            StrategyType.TECL: 0.4
        }
        trading_engine.strategy_manager.get_strategy_performance_summary.return_value = mock_performance
        
        result = trading_engine.get_multi_strategy_performance_report()
        
        assert 'timestamp' in result
        assert 'strategy_allocations' in result
        assert 'current_positions' in result
        assert 'performance_summary' in result
        assert result['performance_summary'] == mock_performance

    def test_get_multi_strategy_performance_report_error(self, trading_engine):
        """Test performance report generation with error"""
        trading_engine.data_provider.get_positions.side_effect = Exception("Network error")
        
        result = trading_engine.get_multi_strategy_performance_report()
        
        assert 'error' in result
        assert 'Network error' in result['error']

    @patch('the_alchemiser.utils.account_utils.calculate_portfolio_values')
    @patch('the_alchemiser.utils.account_utils.extract_current_position_values')
    @patch('the_alchemiser.utils.trading_math.calculate_allocation_discrepancy')
    def test_build_portfolio_state_data(self, mock_calc_discrepancy, mock_extract_values, 
                                       mock_calc_values, trading_engine):
        """Test portfolio state data building"""
        target_portfolio = {'SPY': 0.6, 'BIL': 0.4}
        account_info = {'portfolio_value': 100000}
        current_positions = {'SPY': {'market_value': 60000}}
        
        mock_calc_values.return_value = {'SPY': 60000, 'BIL': 40000}
        mock_extract_values.return_value = {'SPY': 58000}
        mock_calc_discrepancy.return_value = (0.58, 0.02)
        
        result = trading_engine._build_portfolio_state_data(
            target_portfolio, account_info, current_positions
        )
        
        assert 'allocations' in result
        assert 'SPY' in result['allocations']
        assert 'BIL' in result['allocations']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
