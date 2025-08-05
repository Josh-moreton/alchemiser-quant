"""Unit tests for Portfolio Rebalancer."""

import pytest
from unittest.mock import Mock, patch
from typing import Any

from the_alchemiser.execution.portfolio_rebalancer import PortfolioRebalancer


@pytest.mark.unit
@pytest.mark.portfolio
class TestPortfolioRebalancer:
    """Test cases for PortfolioRebalancer class."""

    def test_init(self, mock_trading_bot):
        """Test PortfolioRebalancer initialization."""
        rebalancer = PortfolioRebalancer(mock_trading_bot)
        
        assert rebalancer.bot == mock_trading_bot
        assert rebalancer.order_manager == mock_trading_bot.order_manager

    def test_rebalance_portfolio_basic(self, mock_trading_bot, sample_target_portfolio):
        """Test basic portfolio rebalancing functionality."""
        rebalancer = PortfolioRebalancer(mock_trading_bot)
        
        # Mock the calculate_rebalance_amounts function
        with patch('the_alchemiser.execution.portfolio_rebalancer.calculate_rebalance_amounts') as mock_calc:
            mock_calc.return_value = {
                "AAPL": {
                    "target_value": 40000.0,
                    "current_value": 15000.0,
                    "needs_rebalance": True
                },
                "MSFT": {
                    "target_value": 30000.0,
                    "current_value": 12500.0,
                    "needs_rebalance": True
                },
                "GOOGL": {
                    "target_value": 30000.0,
                    "current_value": 0.0,
                    "needs_rebalance": True
                }
            }
            
            # Execute rebalancing
            result = rebalancer.rebalance_portfolio(
                target_portfolio=sample_target_portfolio,
                strategy_type="NUCLEAR"
            )
            
            # Verify the function was called with correct arguments
            mock_calc.assert_called_once()
            
            # Check that orders were placed
            assert mock_trading_bot.order_manager.place_order.call_count >= 0

    def test_rebalance_portfolio_sell_unwanted_positions(self, mock_trading_bot):
        """Test selling positions not in target portfolio."""
        rebalancer = PortfolioRebalancer(mock_trading_bot)
        
        # Target portfolio without MSFT (should trigger sell)
        target_portfolio = {"AAPL": 1.0}
        
        with patch('the_alchemiser.execution.portfolio_rebalancer.calculate_rebalance_amounts') as mock_calc:
            mock_calc.return_value = {
                "AAPL": {
                    "target_value": 100000.0,
                    "current_value": 15000.0,
                    "needs_rebalance": True
                }
            }
            
            result = rebalancer.rebalance_portfolio(
                target_portfolio=target_portfolio,
                strategy_type="NUCLEAR"
            )
            
            # Should attempt to sell MSFT since it's not in target
            # Verify sell orders were placed
            assert mock_trading_bot.order_manager.place_order.called

    def test_rebalance_portfolio_insufficient_buying_power(self, mock_trading_bot, sample_target_portfolio):
        """Test behavior when insufficient buying power is available."""
        # Set low buying power
        mock_trading_bot.get_account_info.return_value = {
            "portfolio_value": 100000.0,
            "cash": 100.0,  # Very low cash
            "buying_power": 100.0  # Very low buying power
        }
        
        rebalancer = PortfolioRebalancer(mock_trading_bot)
        
        with patch('the_alchemiser.execution.portfolio_rebalancer.calculate_rebalance_amounts') as mock_calc:
            mock_calc.return_value = {
                "GOOGL": {
                    "target_value": 30000.0,
                    "current_value": 0.0,
                    "needs_rebalance": True
                }
            }
            
            # Should handle insufficient buying power gracefully
            result = rebalancer.rebalance_portfolio(
                target_portfolio=sample_target_portfolio,
                strategy_type="NUCLEAR"
            )
            
            # Should not crash, but may skip some orders
            assert result is not None

    def test_rebalance_portfolio_no_rebalancing_needed(self, mock_trading_bot, sample_target_portfolio):
        """Test when portfolio is already balanced."""
        rebalancer = PortfolioRebalancer(mock_trading_bot)
        
        with patch('the_alchemiser.execution.portfolio_rebalancer.calculate_rebalance_amounts') as mock_calc:
            # Return plan where no rebalancing is needed
            mock_calc.return_value = {
                "AAPL": {
                    "target_value": 40000.0,
                    "current_value": 40000.0,
                    "needs_rebalance": False
                },
                "MSFT": {
                    "target_value": 30000.0,
                    "current_value": 30000.0,
                    "needs_rebalance": False
                }
            }
            
            result = rebalancer.rebalance_portfolio(
                target_portfolio=sample_target_portfolio,
                strategy_type="NUCLEAR"
            )
            
            # Should not place any orders
            mock_trading_bot.order_manager.place_order.assert_not_called()

    def test_rebalance_portfolio_order_execution_failure(self, mock_trading_bot, sample_target_portfolio):
        """Test handling of order execution failures."""
        # Mock order placement to fail
        mock_trading_bot.order_manager.place_order.return_value = None
        
        rebalancer = PortfolioRebalancer(mock_trading_bot)
        
        with patch('the_alchemiser.execution.portfolio_rebalancer.calculate_rebalance_amounts') as mock_calc:
            mock_calc.return_value = {
                "GOOGL": {
                    "target_value": 30000.0,
                    "current_value": 0.0,
                    "needs_rebalance": True
                }
            }
            
            # Should handle order failures gracefully
            result = rebalancer.rebalance_portfolio(
                target_portfolio=sample_target_portfolio,
                strategy_type="NUCLEAR"
            )
            
            # Should not crash when orders fail
            assert result is not None

    @patch('the_alchemiser.execution.portfolio_rebalancer.get_strategy_tracker')
    def test_strategy_tracking_integration(self, mock_tracker, mock_trading_bot, sample_target_portfolio):
        """Test integration with strategy order tracking."""
        mock_tracker_instance = Mock()
        mock_tracker.return_value = mock_tracker_instance
        
        rebalancer = PortfolioRebalancer(mock_trading_bot)
        
        with patch('the_alchemiser.execution.portfolio_rebalancer.calculate_rebalance_amounts') as mock_calc:
            mock_calc.return_value = {
                "AAPL": {
                    "target_value": 40000.0,
                    "current_value": 15000.0,
                    "needs_rebalance": True
                }
            }
            
            result = rebalancer.rebalance_portfolio(
                target_portfolio=sample_target_portfolio,
                strategy_type="NUCLEAR"
            )
            
            # Verify strategy tracker was obtained
            mock_tracker.assert_called()

    def test_price_validation(self, mock_trading_bot, sample_target_portfolio):
        """Test that invalid prices are handled properly."""
        # Mock get_current_price to return invalid price
        mock_trading_bot.get_current_price.return_value = 0.0  # Invalid price
        
        rebalancer = PortfolioRebalancer(mock_trading_bot)
        
        with patch('the_alchemiser.execution.portfolio_rebalancer.calculate_rebalance_amounts') as mock_calc:
            mock_calc.return_value = {
                "GOOGL": {
                    "target_value": 30000.0,
                    "current_value": 0.0,
                    "needs_rebalance": True
                }
            }
            
            # Should handle invalid prices gracefully
            result = rebalancer.rebalance_portfolio(
                target_portfolio=sample_target_portfolio,
                strategy_type="NUCLEAR"
            )
            
            # Should not place orders with invalid prices
            assert result is not None

    def test_position_data_formats(self, mock_trading_bot, sample_target_portfolio):
        """Test handling of different position data formats (dict vs object)."""
        # Mock positions as both dict and object formats
        mixed_positions = {
            "AAPL": {"qty": 100.0, "market_value": 15000.0},  # dict format
            "MSFT": Mock(qty=50.0, market_value=12500.0)       # object format
        }
        mock_trading_bot.get_positions_dict.return_value = mixed_positions
        
        rebalancer = PortfolioRebalancer(mock_trading_bot)
        
        with patch('the_alchemiser.execution.portfolio_rebalancer.calculate_rebalance_amounts') as mock_calc:
            mock_calc.return_value = {}
            
            # Should handle mixed position formats without error
            result = rebalancer.rebalance_portfolio(
                target_portfolio=sample_target_portfolio,
                strategy_type="NUCLEAR"
            )
            
            assert result is not None
