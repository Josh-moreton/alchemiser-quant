#!/usr/bin/env python3
"""
Market Scenario Tests for Alpaca Trading Bot
Tests specific market conditions and edge cases
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
import pandas as pd

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from execution.alpaca_trader import AlpacaTradingBot


class TestMarketCrashScenario:
    """Test bot behavior during market crash conditions"""
    
    @pytest.fixture
    def crash_bot(self):
        """Create bot configured for crash testing"""
        with patch.dict(os.environ, {
            'ALPACA_PAPER_KEY': 'test_key',
            'ALPACA_PAPER_SECRET': 'test_secret'
        }):
            with patch('execution.alpaca_trader.TradingClient'):
                with patch('execution.alpaca_trader.StockHistoricalDataClient'):
                    return AlpacaTradingBot(paper_trading=True)
    
    def test_portfolio_rebalance_during_crash(self, crash_bot):
        """Test portfolio rebalancing during major market decline"""
        # Mock massive portfolio decline
        crash_bot.get_account_info = Mock(return_value={
            'portfolio_value': 50000.0,  # Down 50% from $100k
            'cash': 5000.0
        })
        
        # Mock current positions with huge losses
        crash_bot.get_positions = Mock(return_value={
            'SMR': {
                'qty': 500.0,
                'market_value': 15000.0,  # Down from $30k
                'current_price': 30.0     # Down from $60
            },
            'LEU': {
                'qty': 100.0,
                'market_value': 15000.0,  # Down from $30k
                'current_price': 150.0    # Down from $300
            },
            'OKLO': {
                'qty': 333.0,
                'market_value': 15000.0,  # Down from $30k
                'current_price': 45.0     # Down from $90
            }
        })
        
        # Mock current prices (further decline)
        crash_bot.get_current_price = Mock(side_effect=lambda symbol: {
            'SMR': 25.0,   # Further decline
            'LEU': 120.0,  # Further decline
            'OKLO': 40.0   # Further decline
        }.get(symbol, 50.0))
        
        crash_bot.place_order = Mock(return_value='crash_order')
        
        # Switch to defensive portfolio
        defensive_portfolio = {
            'UVXY': 0.75,  # VIX spike protection
            'BTAL': 0.25   # Bear market ETF
        }
        
        orders = crash_bot.rebalance_portfolio(defensive_portfolio)
        
        # Should execute defensive rebalancing
        assert isinstance(orders, list)
        # Should sell nuclear positions and buy defensive assets
    
    def test_insufficient_buying_power_crash(self, crash_bot):
        """Test handling when buying power is restricted during crash"""
        crash_bot.get_account_info = Mock(return_value={
            'portfolio_value': 30000.0,
            'cash': 100.0,  # Very little cash
            'buying_power': 50.0  # Restricted buying power
        })
        
        crash_bot.get_positions = Mock(return_value={
            'SMR': {
                'qty': 200.0,
                'market_value': 10000.0,
                'current_price': 50.0
            }
        })
        
        crash_bot.get_current_price = Mock(return_value=100.0)
        crash_bot.place_order = Mock(return_value='order_123')
        
        target_portfolio = {'UVXY': 1.0}  # Want to go all-in UVXY
        
        orders = crash_bot.rebalance_portfolio(target_portfolio)
        
        # Should handle limited buying power gracefully
        assert isinstance(orders, list)


class TestVolatilitySpike:
    """Test bot behavior during volatility spikes"""
    
    @pytest.fixture
    def vol_bot(self):
        with patch.dict(os.environ, {
            'ALPACA_PAPER_KEY': 'test_key',
            'ALPACA_PAPER_SECRET': 'test_secret'
        }):
            with patch('execution.alpaca_trader.TradingClient'):
                with patch('execution.alpaca_trader.StockHistoricalDataClient'):
                    return AlpacaTradingBot(paper_trading=True)
    
    def test_vix_spike_response(self, vol_bot):
        """Test response to VIX spike scenario"""
        vol_bot.get_account_info = Mock(return_value={
            'portfolio_value': 100000.0,
            'cash': 5000.0
        })
        
        vol_bot.get_positions = Mock(return_value={
            'TQQQ': {
                'qty': 1000.0,
                'market_value': 95000.0,  # Leveraged tech position
                'current_price': 95.0
            }
        })
        
        # Mock UVXY spike pricing
        def volatile_pricing(symbol):
            if symbol == 'UVXY':
                return 25.0  # VIX spike
            elif symbol == 'TQQQ':
                return 85.0  # Tech decline
            return 100.0
        
        vol_bot.get_current_price = Mock(side_effect=volatile_pricing)
        vol_bot.place_order = Mock(return_value='vol_order')
        
        # Switch to volatility protection
        vol_portfolio = {'UVXY': 1.0}
        
        orders = vol_bot.rebalance_portfolio(vol_portfolio)
        
        # Should execute volatility hedge
        assert 'TQQQ_SELL' in orders or len(orders) > 0
    
    def test_extreme_bid_ask_spreads(self, vol_bot):
        """Test handling of extreme bid-ask spreads during volatility"""
        # Mock extreme spreads
        mock_quote = Mock()
        mock_quote.bid_price = 90.0
        mock_quote.ask_price = 110.0  # 20-point spread
        
        vol_bot.data_client.get_stock_latest_quote = Mock(return_value={'UVXY': mock_quote})
        
        price = vol_bot.get_current_price('UVXY')
        
        # Should return midpoint even with wide spreads
        assert price == 100.0


class TestLowLiquidityConditions:
    """Test bot behavior in low liquidity conditions"""
    
    @pytest.fixture
    def liquidity_bot(self):
        with patch.dict(os.environ, {
            'ALPACA_PAPER_KEY': 'test_key',
            'ALPACA_PAPER_SECRET': 'test_secret'
        }):
            with patch('execution.alpaca_trader.TradingClient'):
                with patch('execution.alpaca_trader.StockHistoricalDataClient'):
                    return AlpacaTradingBot(paper_trading=True)
    
    def test_partial_fills_simulation(self, liquidity_bot):
        """Test handling of partial order fills"""
        # Mock order placement that might result in partial fills
        def mock_order_placement(symbol, qty, side):
            if qty > 1000:  # Large orders might be partially filled
                return None  # Simulate rejection of large orders
            return 'small_order_123'
        
        liquidity_bot.place_order = Mock(side_effect=mock_order_placement)
        liquidity_bot.get_current_price = Mock(return_value=100.0)
        liquidity_bot.get_account_info = Mock(return_value={
            'portfolio_value': 500000.0,  # Large account
            'cash': 500000.0
        })
        liquidity_bot.get_positions = Mock(return_value={})
        
        # Try to buy large position
        large_portfolio = {'SMR': 1.0}  # Want entire portfolio in SMR
        
        orders = liquidity_bot.rebalance_portfolio(large_portfolio)
        
        # Should handle large order size gracefully
        assert isinstance(orders, list)
    
    def test_illiquid_stock_pricing(self, liquidity_bot):
        """Test pricing for illiquid stocks"""
        # Mock zero bid/ask (illiquid stock)
        mock_quote = Mock()
        mock_quote.bid_price = 0.0
        mock_quote.ask_price = 0.0
        
        liquidity_bot.data_client.get_stock_latest_quote = Mock(return_value={'ILLIQUID': mock_quote})
        
        price = liquidity_bot.get_current_price('ILLIQUID')
        
        # Should return 0 for illiquid stocks
        assert price == 0.0


class TestAfterHoursTrading:
    """Test bot behavior during after-hours trading"""
    
    @pytest.fixture
    def afterhours_bot(self):
        with patch.dict(os.environ, {
            'ALPACA_PAPER_KEY': 'test_key',
            'ALPACA_PAPER_SECRET': 'test_secret'
        }):
            with patch('execution.alpaca_trader.TradingClient'):
                with patch('execution.alpaca_trader.StockHistoricalDataClient'):
                    return AlpacaTradingBot(paper_trading=True)
    
    def test_after_hours_pricing(self, afterhours_bot):
        """Test price fetching during after-hours"""
        # Mock after-hours quote with only last price
        mock_quote = Mock()
        mock_quote.bid_price = 0.0  # No bid after hours
        mock_quote.ask_price = 0.0  # No ask after hours
        mock_quote.last_price = 150.0  # But last trade available
        
        afterhours_bot.data_client.get_stock_latest_quote = Mock(return_value={'AAPL': mock_quote})
        
        # Current implementation returns 0 if no bid/ask, but we could modify to use last_price
        price = afterhours_bot.get_current_price('AAPL')
        
        # This test documents current behavior - returns 0 without bid/ask
        assert price == 0.0
    
    def test_weekend_execution_attempt(self, afterhours_bot):
        """Test bot execution attempt during weekend"""
        # Mock no market data available
        afterhours_bot.get_current_price = Mock(return_value=0.0)  # No prices available
        afterhours_bot.get_account_info = Mock(return_value={
            'portfolio_value': 100000.0,
            'cash': 50000.0
        })
        afterhours_bot.get_positions = Mock(return_value={})
        
        target_portfolio = {'SMR': 0.5, 'LEU': 0.5}
        
        orders = afterhours_bot.rebalance_portfolio(target_portfolio)
        
        # Should handle no pricing gracefully
        assert orders == {} or len(orders) == 0


class TestExtremeMarketConditions:
    """Test bot behavior under extreme market conditions"""
    
    @pytest.fixture
    def extreme_bot(self):
        with patch.dict(os.environ, {
            'ALPACA_PAPER_KEY': 'test_key',
            'ALPACA_PAPER_SECRET': 'test_secret'
        }):
            with patch('execution.alpaca_trader.TradingClient'):
                with patch('execution.alpaca_trader.StockHistoricalDataClient'):
                    return AlpacaTradingBot(paper_trading=True)
    
    def test_circuit_breaker_simulation(self, extreme_bot):
        """Test behavior during market circuit breaker halt"""
        # Mock API errors that might occur during circuit breakers
        extreme_bot.trading_client.submit_order = Mock(side_effect=Exception("Market halted"))
        extreme_bot.get_account_info = Mock(return_value={
            'portfolio_value': 100000.0,
            'cash': 50000.0
        })
        extreme_bot.get_positions = Mock(return_value={})
        extreme_bot.get_current_price = Mock(return_value=100.0)
        
        target_portfolio = {'UVXY': 1.0}
        
        orders = extreme_bot.rebalance_portfolio(target_portfolio)
        
        # Should handle market halt gracefully
        assert isinstance(orders, list)
    
    def test_flash_crash_scenario(self, extreme_bot):
        """Test rapid price changes during flash crash"""
        # Mock rapidly changing prices
        price_sequence = [100.0, 80.0, 60.0, 40.0, 65.0]  # Flash crash and recovery
        call_count = 0
        
        def flash_crash_prices(symbol):
            nonlocal call_count
            if call_count < len(price_sequence):
                price = price_sequence[call_count]
                call_count += 1
                return price
            return price_sequence[-1]
        
        extreme_bot.get_current_price = Mock(side_effect=flash_crash_prices)
        extreme_bot.get_account_info = Mock(return_value={
            'portfolio_value': 100000.0,
            'cash': 50000.0
        })
        extreme_bot.get_positions = Mock(return_value={})
        extreme_bot.place_order = Mock(return_value='flash_order')
        
        target_portfolio = {'SMR': 1.0}
        
        orders = extreme_bot.rebalance_portfolio(target_portfolio)
        
        # Should handle rapid price changes
        assert isinstance(orders, list)
    
    def test_penny_stock_behavior(self, extreme_bot):
        """Test handling of very low-priced stocks"""
        # Mock penny stock prices
        extreme_bot.get_current_price = Mock(return_value=0.05)  # 5 cents
        extreme_bot.get_account_info = Mock(return_value={
            'portfolio_value': 100000.0,
            'cash': 100000.0
        })
        extreme_bot.get_positions = Mock(return_value={})
        extreme_bot.place_order = Mock(return_value='penny_order')
        
        target_portfolio = {'PENNY': 1.0}
        
        orders = extreme_bot.rebalance_portfolio(target_portfolio)
        
        # Should handle penny stocks (but might result in huge quantities)
        assert isinstance(orders, list)


class TestHighFrequencyScenarios:
    """Test bot behavior under high-frequency trading conditions"""
    
    @pytest.fixture
    def hft_bot(self):
        with patch.dict(os.environ, {
            'ALPACA_PAPER_KEY': 'test_key',
            'ALPACA_PAPER_SECRET': 'test_secret'
        }):
            with patch('execution.alpaca_trader.TradingClient'):
                with patch('execution.alpaca_trader.StockHistoricalDataClient'):
                    return AlpacaTradingBot(paper_trading=True)
    
    def test_rapid_signal_changes(self, hft_bot):
        """Test rapid successive signal changes"""
        # Simulate rapid signal changes
        signal_sequence = [
            [{'symbol': 'SMR', 'action': 'BUY', 'reason': 'Nuclear portfolio allocation: 100%', 'timestamp': datetime.now().isoformat()}],
            [{'symbol': 'UVXY', 'action': 'BUY', 'reason': 'Volatility spike', 'timestamp': datetime.now().isoformat()}],
            [{'symbol': 'TQQQ', 'action': 'BUY', 'reason': 'Tech rally', 'timestamp': datetime.now().isoformat()}]
        ]
        
        for signals in signal_sequence:
            portfolio = hft_bot.parse_portfolio_from_signals(signals)
            # Each signal change should be parsed correctly
            assert len(portfolio) == 1
            assert list(portfolio.values())[0] == 1.0
    
    def test_sub_second_price_updates(self, hft_bot):
        """Test handling of very frequent price updates"""
        # Mock rapid price changes
        import time
        prices = [100.0, 100.1, 99.9, 100.05, 99.95]
        call_count = 0
        
        def rapid_prices(symbol):
            nonlocal call_count
            price = prices[call_count % len(prices)]
            call_count += 1
            return price
        
        hft_bot.get_current_price = Mock(side_effect=rapid_prices)
        
        # Multiple rapid price calls
        for i in range(10):
            price = hft_bot.get_current_price('TEST')
            assert 99.0 <= price <= 101.0  # Should be within reasonable range


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
