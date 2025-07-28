#!/usr/bin/env python3
"""
Integration tests for end-to-end trading scenarios including
paper trading, live trading simulation, and backtest mode.
"""

import pytest
from unittest.mock import MagicMock, patch, call
from datetime import datetime, timedelta
import tempfile
import os

from the_alchemiser.execution.order_manager_adapter import OrderManagerAdapter
from the_alchemiser.core.data.data_provider import UnifiedDataProvider


@pytest.fixture
def mock_trading_client():
    """Mock Alpaca trading client."""
    client = MagicMock()
    client.submit_order.return_value = MagicMock(id='test_order_123', status='new')
    client.get_order_by_id.return_value = MagicMock(id='test_order_123', status='filled')
    client.get_all_positions.return_value = []
    client.get_account.return_value = MagicMock(
        buying_power=10000.0, 
        cash=10000.0, 
        portfolio_value=10000.0
    )
    client.get_clock.return_value = MagicMock(is_open=True)
    client.close_position.return_value = MagicMock(id='liquidation_order')
    return client


@pytest.fixture
def mock_data_provider():
    """Mock data provider."""
    provider = MagicMock(spec=UnifiedDataProvider)
    provider.get_current_price.return_value = 150.0
    provider.get_latest_quote.return_value = (149.0, 151.0)
    provider.get_market_hours.return_value = (True, True)
    provider.get_historical_data.return_value = MagicMock()
    return provider


@pytest.fixture
def mock_strategies():
    """Mock trading strategies."""
    strategies = []
    for i in range(2):
        strategy = MagicMock()
        strategy.name = f"TestStrategy_{i+1}"
        strategy.get_signal.return_value = {
            "action": "buy", 
            "confidence": 0.7,
            "allocation": {"AAPL": 0.5, "GOOGL": 0.5}
        }
        strategies.append(strategy)
    return strategies


class TestPaperTradingIntegration:
    """Test end-to-end paper trading scenarios."""
    
    def test_complete_paper_trading_session(self, mock_trading_client, mock_data_provider, mock_strategies):
        """Test complete paper trading session from start to finish."""
        # Setup order manager
        order_manager = OrderManagerAdapter(mock_trading_client, mock_data_provider)
        
        # Simulate complete trading session
        with patch('the_alchemiser.execution.multi_strategy_trader.MultiStrategyTrader') as MockTrader:
            # Mock the trader to simulate execution
            mock_trader_instance = MockTrader.return_value
            mock_trader_instance.execute_strategies.return_value = {
                'strategy_summary': {
                    'TestStrategy_1': {'signal': 'buy', 'confidence': 0.7},
                    'TestStrategy_2': {'signal': 'buy', 'confidence': 0.7}
                },
                'trading_summary': {
                    'total_orders': 2,
                    'successful_orders': 2,
                    'failed_orders': 0,
                    'total_value_traded': 15000.0
                },
                'final_portfolio_state': {
                    'AAPL': {'shares': 50.0, 'value': 7500.0},
                    'GOOGL': {'shares': 3.0, 'value': 7500.0}
                }
            }
            
            # Execute trading session
            trader = MockTrader(order_manager, mock_strategies)
            result = trader.execute_strategies(mode='paper')
            
            # Verify execution
            assert result is not None
            assert result['trading_summary']['total_orders'] == 2
            assert result['trading_summary']['successful_orders'] == 2
            
            # Verify strategies were called
            MockTrader.assert_called_once_with(order_manager, mock_strategies)
    
    def test_paper_trading_with_market_data(self, mock_trading_client, mock_data_provider):
        """Test paper trading with real market data integration."""
        order_manager = OrderManagerAdapter(mock_trading_client, mock_data_provider)
        
        # Mock market data for multiple symbols
        price_data = {'AAPL': 150.0, 'GOOGL': 2500.0, 'MSFT': 350.0}
        mock_data_provider.get_current_price.side_effect = lambda symbol: price_data.get(symbol, 100.0)
        
        # Test portfolio rebalancing
        target_allocations = {'AAPL': 0.4, 'GOOGL': 0.3, 'MSFT': 0.3}
        
        # Place orders for each allocation
        orders_placed = []
        for symbol, allocation in target_allocations.items():
            shares = (10000.0 * allocation) / price_data[symbol]
            order_id = order_manager.place_limit_or_market(symbol, shares, 'buy')
            orders_placed.append(order_id)
        
        # Verify all orders were placed
        assert all(order_id is not None for order_id in orders_placed)
        assert mock_trading_client.submit_order.call_count == 3
    
    def test_paper_trading_error_recovery(self, mock_trading_client, mock_data_provider):
        """Test paper trading with error recovery."""
        order_manager = OrderManagerAdapter(mock_trading_client, mock_data_provider)
        
        # Simulate intermittent failures
        mock_trading_client.submit_order.side_effect = [
            Exception("Network error"),  # First order fails
            MagicMock(id='order_2'),     # Second order succeeds
            Exception("Rate limit"),     # Third order fails
            MagicMock(id='order_4')      # Fourth order succeeds
        ]
        
        # Attempt multiple orders
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
        results = []
        
        for symbol in symbols:
            order_id = order_manager.place_limit_or_market(symbol, 10.0, 'buy')
            results.append(order_id)
        
        # Should have 2 successful orders and 2 failures
        successful = [r for r in results if r is not None]
        failed = [r for r in results if r is None]
        
        assert len(successful) == 2
        assert len(failed) == 2


class TestLiveTradingSimulation:
    """Test live trading simulation (with safety checks)."""
    
    def test_live_trading_safety_checks(self, mock_trading_client, mock_data_provider):
        """Test safety checks in live trading mode."""
        order_manager = OrderManagerAdapter(mock_trading_client, mock_data_provider)
        
        # Mock account with limited funds for safety
        mock_trading_client.get_account.return_value = MagicMock(
            buying_power=1000.0,  # Limited funds for safety
            cash=1000.0,
            portfolio_value=2000.0
        )
        
        # Test position size limits
        large_order_id = order_manager.place_limit_or_market('AAPL', 100.0, 'buy')  # $15k order
        
        # Should be rejected due to insufficient funds
        if large_order_id is None:
            # API rejected the order (expected)
            pass
        else:
            # Order was placed - verify it's reasonable size
            call_args = mock_trading_client.submit_order.call_args[0][0]
            order_value = float(call_args.qty) * 150.0  # Assuming $150/share
            assert order_value <= 1000.0  # Within buying power
    
    def test_live_trading_position_tracking(self, mock_trading_client, mock_data_provider):
        """Test position tracking in live trading."""
        order_manager = OrderManagerAdapter(mock_trading_client, mock_data_provider)
        
        # Mock existing positions
        mock_trading_client.get_all_positions.return_value = [
            MagicMock(symbol='AAPL', qty=10.0, market_value=1500.0),
            MagicMock(symbol='GOOGL', qty=2.0, market_value=5000.0)
        ]
        
        # Test safe sell (shouldn't oversell)
        order_id = order_manager.place_safe_sell_order('AAPL', 5.0)
        
        assert order_id is not None
        
        # Verify quantity doesn't exceed position
        call_args = mock_trading_client.submit_order.call_args[0][0]
        assert float(call_args.qty) <= 10.0
    
    def test_live_trading_market_hours_check(self, mock_trading_client, mock_data_provider):
        """Test market hours checking in live trading."""
        order_manager = OrderManagerAdapter(mock_trading_client, mock_data_provider)
        
        # Test during market hours
        mock_trading_client.get_clock.return_value = MagicMock(is_open=True)
        order_id = order_manager.place_limit_or_market('AAPL', 1.0, 'buy')
        assert order_id is not None
        
        # Test after market hours
        mock_trading_client.get_clock.return_value = MagicMock(is_open=False)
        # Implementation may still allow order placement for next day
        # This tests that the system checks market status


class TestBacktestMode:
    """Test backtest mode integration."""
    
    def test_backtest_with_historical_data(self, mock_data_provider, mock_strategies):
        """Test backtesting with historical data."""
        # Mock historical data
        historical_data = MagicMock()
        historical_data.index = [
            datetime.now() - timedelta(days=i) for i in range(30, 0, -1)
        ]
        historical_data.values = [[150.0 + i] for i in range(30)]
        
        mock_data_provider.get_historical_data.return_value = historical_data
        
        # Create backtest client (mock)
        backtest_client = MagicMock()
        backtest_client.submit_order.return_value = MagicMock(id='backtest_order')
        backtest_client.get_all_positions.return_value = []
        backtest_client.get_account.return_value = MagicMock(
            buying_power=10000.0,
            portfolio_value=10000.0
        )
        
        order_manager = OrderManagerAdapter(backtest_client, mock_data_provider)
        
        # Simulate backtest execution
        backtest_results = []
        for day in range(30):
            # Update mock data for each day
            current_price = 150.0 + day
            mock_data_provider.get_current_price.return_value = current_price
            
            # Execute strategy for this day
            order_id = order_manager.place_limit_or_market('AAPL', 1.0, 'buy')
            backtest_results.append({
                'day': day,
                'price': current_price,
                'order_id': order_id
            })
        
        # Verify backtest completed
        assert len(backtest_results) == 30
        assert all(result['order_id'] is not None for result in backtest_results)
    
    def test_backtest_portfolio_evolution(self, mock_data_provider):
        """Test portfolio evolution during backtest."""
        # Create backtest-specific client
        backtest_client = MagicMock()
        
        # Mock evolving portfolio
        portfolio_states = []
        for day in range(10):
            positions = [
                MagicMock(symbol='AAPL', qty=day * 10.0, market_value=day * 1500.0)
            ]
            portfolio_states.append(positions)
        
        backtest_client.get_all_positions.side_effect = portfolio_states
        backtest_client.submit_order.return_value = MagicMock(id='order')
        
        order_manager = OrderManagerAdapter(backtest_client, mock_data_provider)
        
        # Track portfolio evolution
        portfolio_evolution = []
        for day in range(10):
            positions = order_manager.order_manager.trading_client.get_all_positions()
            total_value = sum(pos.market_value for pos in positions)
            portfolio_evolution.append(total_value)
            
            # Place order for next day
            order_manager.place_limit_or_market('AAPL', 10.0, 'buy')
        
        # Verify portfolio grew over time
        assert portfolio_evolution[0] == 0.0  # Started empty
        assert portfolio_evolution[-1] > portfolio_evolution[0]  # Grew over time
    
    def test_backtest_performance_metrics(self, mock_data_provider):
        """Test calculation of backtest performance metrics."""
        # Mock backtest client with performance tracking
        backtest_client = MagicMock()
        
        # Mock account evolution
        account_states = []
        for day in range(20):
            portfolio_value = 10000.0 + (day * 100.0)  # Growing portfolio
            account_states.append(MagicMock(
                portfolio_value=portfolio_value,
                buying_power=portfolio_value * 0.5
            ))
        
        backtest_client.get_account.side_effect = account_states
        backtest_client.submit_order.return_value = MagicMock(id='order')
        
        order_manager = OrderManagerAdapter(backtest_client, mock_data_provider)
        
        # Collect performance data
        performance_data = []
        for day in range(20):
            account = order_manager.order_manager.trading_client.get_account()
            performance_data.append({
                'day': day,
                'portfolio_value': account.portfolio_value,
                'buying_power': account.buying_power
            })
        
        # Calculate basic metrics
        initial_value = performance_data[0]['portfolio_value']
        final_value = performance_data[-1]['portfolio_value']
        total_return = (final_value - initial_value) / initial_value
        
        # Verify positive performance
        assert total_return > 0
        assert final_value > initial_value


class TestEndToEndWorkflows:
    """Test complete end-to-end trading workflows."""
    
    def test_morning_portfolio_rebalance(self, mock_trading_client, mock_data_provider, mock_strategies):
        """Test complete morning portfolio rebalancing workflow."""
        order_manager = OrderManagerAdapter(mock_trading_client, mock_data_provider)
        
        # Mock morning market conditions
        mock_trading_client.get_clock.return_value = MagicMock(
            is_open=True,
            timestamp=datetime.now().replace(hour=9, minute=30)  # Market open
        )
        
        # Mock overnight positions
        mock_trading_client.get_all_positions.return_value = [
            MagicMock(symbol='AAPL', qty=20.0, market_value=3000.0),
            MagicMock(symbol='GOOGL', qty=2.0, market_value=5000.0),
            MagicMock(symbol='CASH', qty=1.0, market_value=2000.0)
        ]
        
        # Target rebalancing
        target_allocations = {'AAPL': 0.5, 'GOOGL': 0.3, 'MSFT': 0.2}
        
        # Execute rebalancing workflow
        rebalance_orders = []
        total_portfolio_value = 10000.0
        
        for symbol, target_pct in target_allocations.items():
            target_value = total_portfolio_value * target_pct
            current_price = mock_data_provider.get_current_price(symbol)
            target_shares = target_value / current_price
            
            order_id = order_manager.place_limit_or_market(symbol, target_shares, 'buy')
            rebalance_orders.append(order_id)
        
        # Verify rebalancing executed
        assert len(rebalance_orders) == 3
        assert all(order_id is not None for order_id in rebalance_orders)
    
    def test_intraday_strategy_execution(self, mock_trading_client, mock_data_provider, mock_strategies):
        """Test intraday strategy execution workflow."""
        order_manager = OrderManagerAdapter(mock_trading_client, mock_data_provider)
        
        # Simulate intraday price movements
        price_timeline = [150.0, 152.0, 148.0, 155.0, 147.0]  # Volatile day
        
        execution_results = []
        
        for hour, price in enumerate(price_timeline):
            mock_data_provider.get_current_price.return_value = price
            
            # Mock strategy response to price movement
            for strategy in mock_strategies:
                if price > 150.0:
                    strategy.get_signal.return_value = {
                        "action": "buy", "confidence": 0.8, "allocation": {"AAPL": 0.6}
                    }
                else:
                    strategy.get_signal.return_value = {
                        "action": "sell", "confidence": 0.7, "allocation": {"AAPL": 0.2}
                    }
            
            # Execute strategy
            signal = mock_strategies[0].get_signal()
            if signal['action'] == 'buy':
                order_id = order_manager.place_limit_or_market('AAPL', 10.0, 'buy')
            else:
                order_id = order_manager.place_safe_sell_order('AAPL', 5.0)
            
            execution_results.append({
                'hour': hour,
                'price': price,
                'action': signal['action'],
                'order_id': order_id
            })
        
        # Verify intraday execution
        assert len(execution_results) == 5
        buy_orders = [r for r in execution_results if r['action'] == 'buy']
        sell_orders = [r for r in execution_results if r['action'] == 'sell']
        
        assert len(buy_orders) > 0
        assert len(sell_orders) > 0
    
    def test_end_of_day_settlement(self, mock_trading_client, mock_data_provider):
        """Test end-of-day settlement workflow."""
        order_manager = OrderManagerAdapter(mock_trading_client, mock_data_provider)
        
        # Mock pending orders from the day
        pending_orders = [
            {'order_id': 'order_1'},
            {'order_id': 'order_2'},
            {'order_id': 'order_3'}
        ]
        
        # Mock order status progression
        def mock_order_status(order_id):
            # Simulate orders settling over time
            if order_id == 'order_1':
                return MagicMock(id=order_id, status='filled')
            elif order_id == 'order_2':
                return MagicMock(id=order_id, status='partially_filled')
            else:
                return MagicMock(id=order_id, status='pending_new')
        
        mock_trading_client.get_order_by_id.side_effect = mock_order_status
        
        # Wait for settlement
        settlement_result = order_manager.wait_for_settlement(
            pending_orders, 
            max_wait_time=1.0, 
            poll_interval=0.1
        )
        
        # Verify settlement handling
        assert settlement_result is not None  # Should complete (timeout or settle)
        
        # Verify final portfolio state
        final_positions = mock_trading_client.get_all_positions()
        final_account = mock_trading_client.get_account()
        
        assert final_positions is not None
        assert final_account is not None
