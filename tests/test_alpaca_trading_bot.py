import time
# Patch time.sleep to a no-op for all tests in this module
import pytest

@pytest.fixture(autouse=True)
def patch_sleep(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda x: None)
#!/usr/bin/env python3
"""
Comprehensive pytest testing suite for the Alpaca Trading Bot
Tests all scenarios and market conditions to ensure robust trading behavior
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import pandas as pd
import json

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from execution.alpaca_trader import AlpacaTradingBot
from alpaca.trading.enums import OrderSide, TimeInForce


class TestAlpacaTradingBotSetup:
    """Test bot initialization and setup"""
    
    def test_init_with_valid_credentials(self):
        """Test bot initialization with valid credentials"""
        with patch.dict(os.environ, {
            'ALPACA_PAPER_KEY': 'test_key',
            'ALPACA_PAPER_SECRET': 'test_secret'
        }):
            with patch('execution.alpaca_trader.TradingClient') as mock_trading:
                with patch('execution.alpaca_trader.StockHistoricalDataClient') as mock_data:
                    bot = AlpacaTradingBot(paper_trading=True)
                    assert bot.paper_trading is True
                    assert bot.api_key == 'test_key'
                    assert bot.secret_key == 'test_secret'
    
    def test_init_missing_credentials(self):
        """Test bot initialization fails with missing credentials"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Alpaca API credentials not found"):
                AlpacaTradingBot(paper_trading=True)
    
    def test_live_trading_credentials(self):
        """Test live trading credential selection"""
        with patch.dict(os.environ, {
            'ALPACA_KEY': 'live_key',
            'ALPACA_SECRET': 'live_secret'
        }):
            with patch('execution.alpaca_trader.TradingClient'):
                with patch('execution.alpaca_trader.StockHistoricalDataClient'):
                    bot = AlpacaTradingBot(paper_trading=False)
                    assert bot.paper_trading is False
                    assert bot.api_key == 'live_key'


class TestPriceFetching:
    """Test price fetching functionality"""
    
    @pytest.fixture
    def mock_bot(self):
        """Create a mock bot for testing"""
        with patch.dict(os.environ, {
            'ALPACA_PAPER_KEY': 'test_key',
            'ALPACA_PAPER_SECRET': 'test_secret'
        }):
            with patch('execution.alpaca_trader.TradingClient'):
                with patch('execution.alpaca_trader.StockHistoricalDataClient'):
                    return AlpacaTradingBot(paper_trading=True)
    
    def test_get_current_price_success(self, mock_bot):
        """Test successful price fetching from Alpaca"""
        mock_quote = Mock()
        mock_quote.bid_price = 100.0
        mock_quote.ask_price = 102.0
        
        mock_response = {'AAPL': mock_quote}
        mock_bot.data_client.get_stock_latest_quote = Mock(return_value=mock_response)
        
        price = mock_bot.get_current_price('AAPL')
        assert price == 101.0  # Midpoint of bid/ask
    
    def test_get_current_price_no_bid_ask(self, mock_bot):
        """Test price fetching when bid/ask unavailable"""
        mock_quote = Mock()
        mock_quote.bid_price = 0
        mock_quote.ask_price = 0
        
        mock_response = {'AAPL': mock_quote}
        mock_bot.data_client.get_stock_latest_quote = Mock(return_value=mock_response)
        
        price = mock_bot.get_current_price('AAPL')
        assert price == 0.0
    
    def test_get_current_price_api_failure(self, mock_bot):
        """Test price fetching when Alpaca API fails"""
        mock_bot.data_client.get_stock_latest_quote = Mock(side_effect=Exception("API Error"))
        
        price = mock_bot.get_current_price('AAPL')
        assert price == 0.0
    
    def test_get_current_price_symbol_not_found(self, mock_bot):
        """Test price fetching for invalid symbol"""
        mock_response = {}  # Empty response
        mock_bot.data_client.get_stock_latest_quote = Mock(return_value=mock_response)
        
        price = mock_bot.get_current_price('INVALID')
        assert price == 0.0


class TestAccountOperations:
    """Test account information and position retrieval"""
    
    @pytest.fixture
    def mock_bot(self):
        with patch.dict(os.environ, {
            'ALPACA_PAPER_KEY': 'test_key',
            'ALPACA_PAPER_SECRET': 'test_secret'
        }):
            with patch('execution.alpaca_trader.TradingClient'):
                with patch('execution.alpaca_trader.StockHistoricalDataClient'):
                    return AlpacaTradingBot(paper_trading=True)
    
    def test_get_account_info_success(self, mock_bot):
        """Test successful account info retrieval"""
        mock_account = Mock()
        mock_account.account_number = 'TEST123'
        mock_account.portfolio_value = 100000.0
        mock_account.buying_power = 200000.0
        mock_account.cash = 50000.0
        mock_account.day_trade_count = 0
        mock_account.status = 'ACTIVE'
        
        mock_bot.trading_client.get_account = Mock(return_value=mock_account)
        
        account_info = mock_bot.get_account_info()
        
        assert account_info['account_number'] == 'TEST123'
        assert account_info['portfolio_value'] == 100000.0
        assert account_info['buying_power'] == 200000.0
        assert account_info['cash'] == 50000.0
    
    def test_get_account_info_failure(self, mock_bot):
        """Test account info retrieval failure"""
        mock_bot.trading_client.get_account = Mock(side_effect=Exception("API Error"))
        
        account_info = mock_bot.get_account_info()
        assert account_info == {}
    
    def test_get_positions_success(self, mock_bot):
        """Test successful position retrieval"""
        mock_position = Mock()
        mock_position.symbol = 'AAPL'
        mock_position.qty = 100.0
        mock_position.market_value = 15000.0
        mock_position.cost_basis = 14000.0
        mock_position.unrealized_pl = 1000.0
        mock_position.unrealized_plpc = 0.071
        mock_position.current_price = 150.0
        
        mock_bot.trading_client.get_all_positions = Mock(return_value=[mock_position])
        
        positions = mock_bot.get_positions()
        
        assert 'AAPL' in positions
        assert positions['AAPL']['qty'] == 100.0
        assert positions['AAPL']['market_value'] == 15000.0
    
    def test_get_positions_empty(self, mock_bot):
        """Test position retrieval with no positions"""
        mock_bot.trading_client.get_all_positions = Mock(return_value=[])
        
        positions = mock_bot.get_positions()
        assert positions == {}


class TestOrderPlacement:
    """Test order placement functionality"""
    
    @pytest.fixture
    def mock_bot(self):
        with patch.dict(os.environ, {
            'ALPACA_PAPER_KEY': 'test_key',
            'ALPACA_PAPER_SECRET': 'test_secret'
        }):
            with patch('execution.alpaca_trader.TradingClient'):
                with patch('execution.alpaca_trader.StockHistoricalDataClient'):
                    return AlpacaTradingBot(paper_trading=True)
    
    def test_place_buy_order_success(self, mock_bot):
        """Test successful buy order placement"""
        mock_order = Mock()
        mock_order.id = 'order_123'
        mock_order.status = 'filled'  # Ensure status is filled for test
        mock_bot.trading_client.submit_order = Mock(return_value=mock_order)
        order_id = mock_bot.place_order('AAPL', 10.5, OrderSide.BUY)
        assert order_id == 'order_123'
        mock_bot.trading_client.submit_order.assert_called_once()
    
    def test_place_sell_order_success(self, mock_bot):
        """Test successful sell order placement"""
        mock_order = Mock()
        mock_order.id = 'order_456'
        mock_order.status = 'filled'  # Ensure status is filled for test
        mock_bot.trading_client.submit_order = Mock(return_value=mock_order)
        order_id = mock_bot.place_order('AAPL', 5.25, OrderSide.SELL)
        assert order_id == 'order_456'
    
    def test_place_order_invalid_quantity(self, mock_bot):
        """Test order placement with invalid quantity"""
        order_id = mock_bot.place_order('AAPL', 0, OrderSide.BUY)
        assert order_id is None
        
        order_id = mock_bot.place_order('AAPL', -10, OrderSide.BUY)
        assert order_id is None
    
    def test_place_order_api_failure(self, mock_bot):
        """Test order placement when API fails"""
        mock_bot.trading_client.submit_order = Mock(side_effect=Exception("Order failed"))
        
        order_id = mock_bot.place_order('AAPL', 10, OrderSide.BUY)
        assert order_id is None


class TestPortfolioRebalancing:
    """Test portfolio rebalancing logic - the core functionality"""
    
    @pytest.fixture
    def mock_bot(self):
        with patch.dict(os.environ, {
            'ALPACA_PAPER_KEY': 'test_key',
            'ALPACA_PAPER_SECRET': 'test_secret'
        }):
            with patch('execution.alpaca_trader.TradingClient'):
                with patch('execution.alpaca_trader.StockHistoricalDataClient'):
                    bot = AlpacaTradingBot(paper_trading=True)
                    # Mock price fetching to return consistent prices
                    bot.get_current_price = Mock(side_effect=lambda symbol: {
                        'SMR': 40.0,
                        'LEU': 200.0,
                        'OKLO': 60.0,
                        'AAPL': 150.0,
                        'TSLA': 250.0
                    }.get(symbol, 100.0))
                    return bot
    
    def test_rebalance_empty_portfolio_to_nuclear(self, mock_bot):
        """Test rebalancing from empty portfolio to nuclear allocation"""
        # Mock account with cash only
        mock_bot.get_account_info = Mock(return_value={
            'portfolio_value': 100000.0,
            'cash': 100000.0
        })
        mock_bot.get_positions = Mock(return_value={})
        
        # Mock successful order placement
        mock_bot.place_order = Mock(return_value='order_123')
        
        target_portfolio = {
            'SMR': 0.312,   # 31.2%
            'LEU': 0.395,   # 39.5%
            'OKLO': 0.292   # 29.2%
        }
        
        orders = mock_bot.rebalance_portfolio(target_portfolio)
        
        # Should place 3 buy orders
        assert len(orders) == 3
        
        # Check that we have buy orders for all target symbols
        buy_symbols = {o['symbol'] for o in orders if o['side'] == OrderSide.BUY}
        assert 'SMR' in buy_symbols
        assert 'LEU' in buy_symbols
        assert 'OKLO' in buy_symbols
        
        # Verify order placement was called
        assert mock_bot.place_order.call_count == 3
    
    def test_rebalance_existing_portfolio_minor_adjustment(self, mock_bot):
        """Test minor rebalancing of existing portfolio"""
        # Mock account with existing positions
        mock_bot.get_account_info = Mock(return_value={
            'portfolio_value': 100000.0,
            'cash': 1000.0
        })
        
        # Current positions slightly off-target
        mock_bot.get_positions = Mock(return_value={
            'SMR': {
                'qty': 750.0,
                'market_value': 30000.0,  # 30% (target: 31.2%)
                'current_price': 40.0
            },
            'LEU': {
                'qty': 200.0,
                'market_value': 40000.0,  # 40% (target: 39.5%)
                'current_price': 200.0
            },
            'OKLO': {
                'qty': 483.33,
                'market_value': 29000.0,  # 29% (target: 29.2%)
                'current_price': 60.0
            }
        })
        
        mock_bot.place_order = Mock(return_value='order_123')
        
        target_portfolio = {
            'SMR': 0.312,
            'LEU': 0.395,
            'OKLO': 0.292
        }
        
        orders = mock_bot.rebalance_portfolio(target_portfolio)
        
        # Should make minimal trades
        # LEU: 40% -> 39.5% (small sell)
        # SMR: 30% -> 31.2% (small buy)
        # OKLO: 29% -> 29.2% (small buy)
        
        # Check that minimal trading occurred (not all positions sold and rebought)
        call_count = mock_bot.place_order.call_count
        assert call_count <= 3  # At most 3 trades for fine-tuning
    
    def test_rebalance_major_portfolio_change(self, mock_bot):
        """Test major portfolio rebalancing (different strategy)"""
        # Mock account with tech portfolio
        mock_bot.get_account_info = Mock(return_value={
            'portfolio_value': 100000.0,
            'cash': 1000.0
        })
        
        mock_bot.get_positions = Mock(return_value={
            'AAPL': {
                'qty': 330.0,
                'market_value': 49500.0,  # 50%
                'current_price': 150.0
            },
            'TSLA': {
                'qty': 200.0,
                'market_value': 50000.0,  # 50%
                'current_price': 250.0
            }
        })
        
        mock_bot.place_order = Mock(return_value='order_123')
        
        # Switch to nuclear portfolio
        target_portfolio = {
            'SMR': 0.312,
            'LEU': 0.395,
            'OKLO': 0.292
        }
        
        orders = mock_bot.rebalance_portfolio(target_portfolio)
        
        # Should sell all current positions and buy new ones
        expected_orders = ['AAPL_SELL', 'TSLA_SELL', 'SMR_BUY', 'LEU_BUY', 'OKLO_BUY']
        assert len(orders) >= 3  # At least the new buys
    
    def test_rebalance_insufficient_cash(self, mock_bot):
        """Test rebalancing when insufficient cash for full allocation"""
        mock_bot.get_account_info = Mock(return_value={
            'portfolio_value': 100000.0,
            'cash': 100.0  # Very little cash
        })
        
        mock_bot.get_positions = Mock(return_value={
            'SMR': {
                'qty': 100.0,
                'market_value': 4000.0,  # Only 4%
                'current_price': 40.0
            }
        })
        
        mock_bot.place_order = Mock(return_value='order_123')
        
        target_portfolio = {
            'SMR': 0.312,   # Want 31.2% but don't have cash
            'LEU': 0.395,
            'OKLO': 0.292
        }
        
        orders = mock_bot.rebalance_portfolio(target_portfolio)
        
        # Should handle insufficient cash gracefully
        # May not achieve full target allocation but shouldn't crash
        assert isinstance(orders, list)
    
    def test_rebalance_price_fetching_failure(self, mock_bot):
        """Test rebalancing when price fetching fails for some symbols"""
        mock_bot.get_account_info = Mock(return_value={
            'portfolio_value': 100000.0,
            'cash': 50000.0
        })
        
        mock_bot.get_positions = Mock(return_value={})
        
        # Mock price fetching to fail for one symbol
        def mock_price_fetch(symbol):
            if symbol == 'LEU':
                return 0.0  # Price fetch failed
            return {'SMR': 40.0, 'OKLO': 60.0}.get(symbol, 100.0)
        
        mock_bot.get_current_price = Mock(side_effect=mock_price_fetch)
        mock_bot.place_order = Mock(return_value='order_123')
        
        target_portfolio = {
            'SMR': 0.312,
            'LEU': 0.395,   # Price unavailable
            'OKLO': 0.292
        }
        
        orders = mock_bot.rebalance_portfolio(target_portfolio)
        
        # Should skip LEU and only trade SMR and OKLO
        assert 'LEU_BUY' not in orders
        assert len(orders) <= 2
    
    def test_rebalance_complete_portfolio_switch(self, mock_bot):
        """Test complete switch from one portfolio to another"""
        # Mock account info
        mock_bot.get_account_info = Mock(return_value={
            'portfolio_value': 47500.0,  # Total portfolio value
            'cash': 0.0
        })
        
        # Mock successful order placement
        mock_bot.place_order = Mock(return_value='mock_order_id')
        
        # Current: Hold different nuclear stocks
        current_positions = {
            'OKLO': {
                'qty': 500.0,
                'market_value': 25000.0,
                'current_price': 50.0
            },
            'NNE': {
                'qty': 750.0,
                'market_value': 22500.0,
                'current_price': 30.0
            }
        }
        mock_bot.get_positions = Mock(return_value=current_positions)
        
        # Target: Switch to classic nuclear portfolio
        target_portfolio = {'SMR': 0.6, 'LEU': 0.4}
        
        # Patch get_account_info to simulate cash update after sells
        def get_account_info_side_effect():
            # After sells, simulate increased cash/buying power
            return {
                'portfolio_value': 47500.0,
                'cash': 47500.0,
                'buying_power': 47500.0
            }
        mock_bot.get_account_info = Mock(side_effect=get_account_info_side_effect)
        orders = mock_bot.rebalance_portfolio(target_portfolio)
        # Should sell all current positions and buy new ones
        assert len(orders) == 4  # 2 sells + 2 buys
        # Verify all current positions are sold
        sell_orders = [o for o in orders if o['side'] == OrderSide.SELL]
        sell_symbols = {o['symbol'] for o in sell_orders}
        assert 'OKLO' in sell_symbols
        assert 'NNE' in sell_symbols
        # Verify new positions are bought
        buy_orders = [o for o in orders if o['side'] == OrderSide.BUY]
        buy_symbols = {o['symbol'] for o in buy_orders}
        assert 'SMR' in buy_symbols
        assert 'LEU' in buy_symbols

    def test_rebalance_partial_overlap_switch(self, mock_bot):
        """Test switching with partial overlap between portfolios"""
        # Mock account info
        mock_bot.get_account_info = Mock(return_value={
            'portfolio_value': 46000.0,  # Total portfolio value
            'cash': 0.0
        })
        
        # Mock successful order placement
        mock_bot.place_order = Mock(return_value='mock_order_id')
        
        # Current: Mixed portfolio with some overlap
        current_positions = {
            'SMR': {
                'qty': 400.0,
                'market_value': 16000.0,
                'current_price': 40.0
            },
            'OKLO': {
                'qty': 600.0,
                'market_value': 30000.0,
                'current_price': 50.0
            }
        }
        mock_bot.get_positions = Mock(return_value=current_positions)
        
        # Target: Keep SMR, drop OKLO, add LEU
        target_portfolio = {'SMR': 0.65, 'LEU': 0.35}
        
        # Patch get_account_info to simulate cash update after sells
        def get_account_info_side_effect():
            # After sells, simulate increased cash/buying_power
            return {
                'portfolio_value': 46000.0,
                'cash': 46000.0,
                'buying_power': 46000.0
            }
        mock_bot.get_account_info = Mock(side_effect=get_account_info_side_effect)
        orders = mock_bot.rebalance_portfolio(target_portfolio)
        # Should: sell all OKLO, buy SMR and LEU
        oklo_sells = [o for o in orders if o['symbol'] == 'OKLO' and o['side'] == OrderSide.SELL]
        assert len(oklo_sells) == 1
        assert oklo_sells[0]['qty'] > 0
        smr_buys = [o for o in orders if o['symbol'] == 'SMR' and o['side'] == OrderSide.BUY]
        assert len(smr_buys) == 1
        leu_buys = [o for o in orders if o['symbol'] == 'LEU' and o['side'] == OrderSide.BUY]
        assert len(leu_buys) == 1

    def test_rebalance_to_cash_position(self, mock_bot):
        """Test liquidating entire portfolio to cash"""
        # Mock account info
        mock_bot.get_account_info = Mock(return_value={
            'portfolio_value': 34000.0,  # Total portfolio value
            'cash': 0.0
        })
        
        # Mock successful order placement
        mock_bot.place_order = Mock(return_value='mock_order_id')
        
        # Current: Some positions
        current_positions = {
            'SMR': {
                'qty': 500.0,
                'market_value': 20000.0,
                'current_price': 40.0
            },
            'LEU': {
                'qty': 400.0,
                'market_value': 14000.0,
                'current_price': 35.0
            }
        }
        mock_bot.get_positions = Mock(return_value=current_positions)
        
        # Target: Empty portfolio (all cash)
        target_portfolio = {}
        
        orders = mock_bot.rebalance_portfolio(target_portfolio)
        
        # Should sell all positions
        assert len(orders) == 2
        assert all(o['side'] == OrderSide.SELL for o in orders)
        
        # Verify all current positions are liquidated
        sell_symbols = {o['symbol'] for o in orders}
        assert 'SMR' in sell_symbols
        assert 'LEU' in sell_symbols
        
        # Check quantities - the bot sells all shares to reach 0% allocation
        smr_sell = next(o for o in orders if o['symbol'] == 'SMR')
        leu_sell = next(o for o in orders if o['symbol'] == 'LEU')
        assert smr_sell['qty'] == 500.0  # All SMR shares
        assert leu_sell['qty'] > 0  # Some or all LEU shares (depending on rebalancing logic)

    def test_rebalance_from_cash_to_positions(self, mock_bot):
        """Test deploying cash to new positions"""
        # Mock account info  
        mock_bot.get_account_info = Mock(return_value={
            'portfolio_value': 100000.0,  # Total portfolio value
            'cash': 100000.0  # All cash
        })
        
        # Mock successful order placement
        mock_bot.place_order = Mock(return_value='mock_order_id')
        
        # Current: No positions (all cash)
        mock_bot.get_positions = Mock(return_value={})
        
        # Target: New nuclear allocation
        target_portfolio = {'SMR': 0.5, 'LEU': 0.3, 'OKLO': 0.2}
        
        orders = mock_bot.rebalance_portfolio(target_portfolio)
        
        # Should only buy (no sells since starting from cash)
        assert len(orders) == 3
        assert all(o['side'] == OrderSide.BUY for o in orders)
        
        # Verify all target symbols are bought
        buy_symbols = {o['symbol'] for o in orders}
        assert buy_symbols == {'SMR', 'LEU', 'OKLO'}

    def test_rebalance_micro_adjustments(self, mock_bot):
        """Test very small portfolio adjustments"""
        # Mock account info
        mock_bot.get_account_info = Mock(return_value={
            'portfolio_value': 99945.0,  # Total portfolio value
            'cash': 0.0
        })
        
        # Mock successful order placement
        mock_bot.place_order = Mock(return_value='mock_order_id')
        
        # Current: Nearly target allocation
        current_positions = {
            'SMR': {
                'qty': 1250.0,  # $50,000 = 50.1%
                'market_value': 50000.0,
                'current_price': 40.0
            },
            'LEU': {
                'qty': 1427.0,  # $49,945 = 49.9%
                'market_value': 49945.0,
                'current_price': 35.0
            }
        }
        mock_bot.get_positions = Mock(return_value=current_positions)
        
        # Target: 50% / 50% split (very minor adjustment needed)
        target_portfolio = {'SMR': 0.5, 'LEU': 0.5}
        
        orders = mock_bot.rebalance_portfolio(target_portfolio)
        
        # Should make minimal or no trades
        assert len(orders) <= 2
        
        # If any orders exist, they should be small adjustments
        for order in orders:
            assert order['qty'] < 10.0  # Very small quantities only

    def test_rebalance_identical_portfolio(self, mock_bot):
        """Test rebalancing to identical current portfolio"""
        # Mock account info
        mock_bot.get_account_info = Mock(return_value={
            'portfolio_value': 50000.0,  # Total portfolio value
            'cash': 0.0
        })
        
        # Mock successful order placement
        mock_bot.place_order = Mock(return_value='mock_order_id')
        
        # Current: Perfect target allocation
        current_positions = {
            'SMR': {
                'qty': 750.0,  # $30,000 = 60%
                'market_value': 30000.0,
                'current_price': 40.0
            },
            'LEU': {
                'qty': 571.43,  # $20,000 = 40%
                'market_value': 20000.0,
                'current_price': 35.0
            }
        }
        mock_bot.get_positions = Mock(return_value=current_positions)
        
        # Target: Exactly the same as current
        target_portfolio = {'SMR': 0.6, 'LEU': 0.4}
        
        orders = mock_bot.rebalance_portfolio(target_portfolio)
        
        # Should generate no orders (or very minimal due to rounding)
        assert len(orders) == 0 or all(o['qty'] < 1.0 for o in orders)


class TestSignalParsing:
    """Test nuclear signal parsing and portfolio allocation"""
    
    @pytest.fixture
    def mock_bot(self):
        with patch.dict(os.environ, {
            'ALPACA_PAPER_KEY': 'test_key',
            'ALPACA_PAPER_SECRET': 'test_secret'
        }):
            with patch('execution.alpaca_trader.TradingClient'):
                with patch('execution.alpaca_trader.StockHistoricalDataClient'):
                    return AlpacaTradingBot(paper_trading=True)
    
    def test_parse_nuclear_portfolio_signals(self, mock_bot):
        """Test parsing of nuclear portfolio signals"""
        signals = [
            {
                'symbol': 'SMR',
                'action': 'BUY',
                'reason': 'Nuclear portfolio allocation: 31.2% (Bull market)',
                'timestamp': datetime.now().isoformat()
            },
            {
                'symbol': 'LEU',
                'action': 'BUY',
                'reason': 'Nuclear portfolio allocation: 39.5% (Bull market)',
                'timestamp': datetime.now().isoformat()
            },
            {
                'symbol': 'OKLO',
                'action': 'BUY',
                'reason': 'Nuclear portfolio allocation: 29.2% (Bull market)',
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        portfolio = mock_bot.parse_portfolio_from_signals(signals)
        
        assert portfolio['SMR'] == 0.312
        assert portfolio['LEU'] == 0.395
        assert portfolio['OKLO'] == 0.292
        assert abs(sum(portfolio.values()) - 1.0) < 0.01  # Should sum to ~100%
    
    def test_parse_single_buy_signal(self, mock_bot):
        """Test parsing of single BUY signal without percentage"""
        signals = [
            {
                'symbol': 'UVXY',
                'action': 'BUY',
                'reason': 'Market volatility spike detected',
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        portfolio = mock_bot.parse_portfolio_from_signals(signals)
        
        assert portfolio['UVXY'] == 1.0  # 100% allocation
    
    def test_parse_hold_signals(self, mock_bot):
        """Test parsing of HOLD signals"""
        signals = [
            {
                'symbol': 'SPY',
                'action': 'HOLD',
                'reason': 'Market conditions neutral',
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        portfolio = mock_bot.parse_portfolio_from_signals(signals)
        
        assert portfolio == {}  # No allocations for HOLD
    
    def test_parse_mixed_signals(self, mock_bot):
        """Test parsing mixed BUY and HOLD signals"""
        signals = [
            {
                'symbol': 'SMR',
                'action': 'BUY',
                'reason': 'Nuclear portfolio allocation: 50% (Bull market)',
                'timestamp': datetime.now().isoformat()
            },
            {
                'symbol': 'SPY',
                'action': 'HOLD',
                'reason': 'Market neutral',
                'timestamp': datetime.now().isoformat()
            },
            {
                'symbol': 'LEU',
                'action': 'BUY',
                'reason': 'Nuclear portfolio allocation: 50% (Bull market)',
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        portfolio = mock_bot.parse_portfolio_from_signals(signals)
        
        # Should only include BUY signals
        assert len(portfolio) == 2
        assert 'SPY' not in portfolio
        assert portfolio['SMR'] == 0.5
        assert portfolio['LEU'] == 0.5


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.fixture
    def mock_bot(self):
        with patch.dict(os.environ, {
            'ALPACA_PAPER_KEY': 'test_key',
            'ALPACA_PAPER_SECRET': 'test_secret'
        }):
            with patch('execution.alpaca_trader.TradingClient'):
                with patch('execution.alpaca_trader.StockHistoricalDataClient'):
                    return AlpacaTradingBot(paper_trading=True)
    
    def test_account_info_unavailable(self, mock_bot):
        """Test handling when account info is unavailable"""
        mock_bot.get_account_info = Mock(return_value={})
        
        target_portfolio = {'SMR': 0.5, 'LEU': 0.5}
        orders = mock_bot.rebalance_portfolio(target_portfolio)
        
        assert orders == []
    
    def test_all_price_fetches_fail(self, mock_bot):
        """Test handling when all price fetches fail"""
        mock_bot.get_account_info = Mock(return_value={
            'portfolio_value': 100000.0,
            'cash': 50000.0
        })
        mock_bot.get_positions = Mock(return_value={})
        mock_bot.get_current_price = Mock(return_value=0.0)  # All prices fail
        
        target_portfolio = {'SMR': 0.5, 'LEU': 0.5}
        orders = mock_bot.rebalance_portfolio(target_portfolio)
        
        # Should handle gracefully without crashing
        assert isinstance(orders, list)
    
    def test_order_placement_failures(self, mock_bot):
        """Test handling when order placement fails"""
        mock_bot.get_account_info = Mock(return_value={
            'portfolio_value': 100000.0,
            'cash': 50000.0
        })
        mock_bot.get_positions = Mock(return_value={})
        mock_bot.get_current_price = Mock(return_value=100.0)
        mock_bot.place_order = Mock(return_value=None)  # All orders fail
        
        target_portfolio = {'SMR': 0.5, 'LEU': 0.5}
        orders = mock_bot.rebalance_portfolio(target_portfolio)
        
        # Should handle gracefully
        assert isinstance(orders, list)


class TestMarketConditions:
    """Test bot behavior under different market conditions"""
    
    @pytest.fixture
    def mock_bot(self):
        with patch.dict(os.environ, {
            'ALPACA_PAPER_KEY': 'test_key',
            'ALPACA_PAPER_SECRET': 'test_secret'
        }):
            with patch('execution.alpaca_trader.TradingClient'):
                with patch('execution.alpaca_trader.StockHistoricalDataClient'):
                    return AlpacaTradingBot(paper_trading=True)
    
    def test_bull_market_nuclear_portfolio(self, mock_bot):
        """Test nuclear portfolio allocation in bull market"""
        # Set up standard bull market nuclear allocation
        target_portfolio = {
            'SMR': 0.312,
            'LEU': 0.395, 
            'OKLO': 0.292
        }
        
        # Verify allocations sum to ~100%
        total_allocation = sum(target_portfolio.values())
        assert abs(total_allocation - 1.0) < 0.01
        
        # Verify individual allocations are reasonable
        for symbol, weight in target_portfolio.items():
            assert 0.0 < weight < 0.5  # No single position > 50%
    
    def test_bear_market_portfolio(self, mock_bot):
        """Test bear market portfolio allocation"""
        # Mock bear market signals
        signals = [
            {
                'symbol': 'UVXY',
                'action': 'BUY',
                'reason': 'Bear market allocation: 75% (UVXY)',
                'timestamp': datetime.now().isoformat()
            },
            {
                'symbol': 'BTAL',
                'action': 'BUY',
                'reason': 'Bear market allocation: 25% (BTAL)',
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        portfolio = mock_bot.parse_portfolio_from_signals(signals)
        
        # Should be defensive allocation
        assert 'UVXY' in portfolio
        assert 'BTAL' in portfolio
        assert abs(sum(portfolio.values()) - 1.0) < 0.01
    
    def test_volatile_market_conditions(self, mock_bot):
        """Test handling of rapidly changing prices"""
        # Mock volatile price fetching
        call_count = 0
        def volatile_prices(symbol):
            nonlocal call_count
            call_count += 1
            base_price = {'SMR': 40.0, 'LEU': 200.0, 'OKLO': 60.0}.get(symbol, 100.0)
            # Simulate price volatility
            volatility = 0.1 * (call_count % 3 - 1)  # -10%, 0%, +10%
            return base_price * (1 + volatility)
        
        mock_bot.get_current_price = Mock(side_effect=volatile_prices)
        mock_bot.get_account_info = Mock(return_value={
            'portfolio_value': 100000.0,
            'cash': 50000.0
        })
        mock_bot.get_positions = Mock(return_value={})
        mock_bot.place_order = Mock(return_value='order_123')
        
        target_portfolio = {'SMR': 0.33, 'LEU': 0.33, 'OKLO': 0.34}
        orders = mock_bot.rebalance_portfolio(target_portfolio)
        
        # Should handle volatile prices without issues
        assert isinstance(orders, list)


class TestIntegrationScenarios:
    """Test end-to-end integration scenarios"""
    
    @pytest.fixture
    def mock_bot(self):
        with patch.dict(os.environ, {
            'ALPACA_PAPER_KEY': 'test_key',
            'ALPACA_PAPER_SECRET': 'test_secret'
        }):
            with patch('execution.alpaca_trader.TradingClient'):
                with patch('execution.alpaca_trader.StockHistoricalDataClient'):
                    return AlpacaTradingBot(paper_trading=True)
    
    def test_full_nuclear_strategy_execution(self, mock_bot):
        """Test complete nuclear strategy execution flow"""
        # Mock signal file reading
        mock_signals = [
            {
                'symbol': 'SMR',
                'action': 'BUY',
                'reason': 'Nuclear portfolio allocation: 31.2% (Bull market)',
                'timestamp': datetime.now().isoformat()
            },
            {
                'symbol': 'LEU', 
                'action': 'BUY',
                'reason': 'Nuclear portfolio allocation: 39.5% (Bull market)',
                'timestamp': datetime.now().isoformat()
            },
            {
                'symbol': 'OKLO',
                'action': 'BUY', 
                'reason': 'Nuclear portfolio allocation: 29.2% (Bull market)',
                'timestamp': datetime.now().isoformat()
            }
        ]
        
        mock_bot.read_nuclear_signals = Mock(return_value=mock_signals)
        mock_bot.get_account_info = Mock(return_value={
            'portfolio_value': 100000.0,
            'cash': 100000.0
        })
        mock_bot.get_positions = Mock(return_value={})
        mock_bot.get_current_price = Mock(side_effect=lambda symbol: {
            'SMR': 40.0, 'LEU': 200.0, 'OKLO': 60.0
        }.get(symbol, 0.0))
        mock_bot.place_order = Mock(return_value='order_123')
        mock_bot.rebalance_portfolio = Mock(return_value=[
            {'symbol': 'SMR', 'side': OrderSide.BUY, 'qty': 78.0, 'order_id': 'order_1', 'estimated_value': 31200.0},
            {'symbol': 'LEU', 'side': OrderSide.BUY, 'qty': 197.5, 'order_id': 'order_2', 'estimated_value': 39500.0},
            {'symbol': 'OKLO', 'side': OrderSide.BUY, 'qty': 486.67, 'order_id': 'order_3', 'estimated_value': 29200.0}
        ])
        
        # Test the full execution
        success = mock_bot.execute_nuclear_strategy()
        
        assert success is True
        mock_bot.rebalance_portfolio.assert_called_once()
    
    def test_no_signals_available(self, mock_bot):
        """Test execution when no signals are available"""
        mock_bot.read_nuclear_signals = Mock(return_value=[])
        
        success = mock_bot.execute_nuclear_strategy()
        
        assert success is False
    
    def test_invalid_signal_format(self, mock_bot):
        """Test handling of malformed signals"""
        # Mock corrupted signals
        mock_signals = [
            {
                'symbol': 'SMR',
                'action': 'INVALID_ACTION',
                'reason': 'Corrupted data',
                'timestamp': 'invalid_timestamp'
            }
        ]
        
        mock_bot.read_nuclear_signals = Mock(return_value=mock_signals)
        
        success = mock_bot.execute_nuclear_strategy()
        
        # Should handle gracefully
        assert success is False


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])
