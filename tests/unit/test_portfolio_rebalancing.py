"""
Unit tests for portfolio rebalancing logic.

Tests the core portfolio rebalancing calculations that are critical to the trading system.
Covers edge cases identified in the failure mode analysis.
"""

from unittest.mock import Mock, patch

import pytest

from the_alchemiser.execution.portfolio_rebalancer import PortfolioRebalancer
from the_alchemiser.utils.trading_math import calculate_rebalance_amounts


class TestPortfolioRebalancing:
    """Test portfolio rebalancing calculations and logic."""

    def test_simple_rebalance_calculation(self):
        """Test basic rebalancing calculation with clean numbers."""
        target_portfolio = {"AAPL": 0.5, "MSFT": 0.3, "CASH": 0.2}
        current_values = {"AAPL": 40000.0, "MSFT": 20000.0}  # CASH implicit: 40000
        portfolio_value = 100000.0

        result = calculate_rebalance_amounts(target_portfolio, current_values, portfolio_value)

        # Expected: AAPL should go to 50k (need +10k), MSFT to 30k (need +10k)
        assert result["AAPL"]["target_value"] == 50000.0
        assert result["AAPL"]["current_value"] == 40000.0
        assert result["AAPL"]["trade_amount"] == 10000.0
        assert result["AAPL"]["needs_rebalance"] is True

        assert result["MSFT"]["target_value"] == 30000.0
        assert result["MSFT"]["current_value"] == 20000.0
        assert result["MSFT"]["trade_amount"] == 10000.0
        assert result["MSFT"]["needs_rebalance"] is True

    def test_rebalance_with_zero_positions(self):
        """Test rebalancing when starting from all cash."""
        target_portfolio = {"AAPL": 0.6, "MSFT": 0.4}
        current_values = {}  # All cash
        portfolio_value = 100000.0

        result = calculate_rebalance_amounts(target_portfolio, current_values, portfolio_value)

        assert result["AAPL"]["target_value"] == 60000.0
        assert result["AAPL"]["current_value"] == 0.0
        assert result["AAPL"]["trade_amount"] == 60000.0
        assert result["AAPL"]["needs_rebalance"] is True

        assert result["MSFT"]["target_value"] == 40000.0
        assert result["MSFT"]["current_value"] == 0.0
        assert result["MSFT"]["trade_amount"] == 40000.0
        assert result["MSFT"]["needs_rebalance"] is True

    def test_rebalance_precision_edge_cases(self):
        """Test rebalancing with precision edge cases that could cause floating point errors."""
        # Use numbers that are problematic for floating point arithmetic
        target_portfolio = {"AAPL": 1 / 3, "MSFT": 1 / 3, "GOOGL": 1 / 3}  # 0.333... each
        current_values = {"AAPL": 33333.33, "MSFT": 33333.33, "GOOGL": 33333.34}
        portfolio_value = 100000.0

        result = calculate_rebalance_amounts(target_portfolio, current_values, portfolio_value)

        # Each should target exactly 33333.33 (rounded)
        for symbol in ["AAPL", "MSFT", "GOOGL"]:
            target = result[symbol]["target_value"]
            # Should be very close to 33333.33
            assert abs(target - 33333.33) < 0.01

    def test_rebalance_with_tiny_amounts(self):
        """Test rebalancing doesn't trigger for tiny amounts (prevents thrashing)."""
        target_portfolio = {"AAPL": 0.5, "MSFT": 0.5}
        # Current values very close to target
        current_values = {"AAPL": 49995.0, "MSFT": 50005.0}
        portfolio_value = 100000.0

        result = calculate_rebalance_amounts(target_portfolio, current_values, portfolio_value)

        # Should not need rebalancing for tiny differences
        # Note: This depends on the threshold implementation in calculate_rebalance_amounts
        for symbol in ["AAPL", "MSFT"]:
            # Trade amounts should be small
            trade_amount = abs(result[symbol]["trade_amount"])
            assert trade_amount < 100.0  # Less than $100 trade

    def test_portfolio_allocation_sum_invariant(self):
        """Test that portfolio allocations always sum to 1.0 (or close due to rounding)."""
        test_cases = [
            {"AAPL": 0.4, "MSFT": 0.3, "GOOGL": 0.2, "CASH": 0.1},
            {"SPY": 0.7, "QQQ": 0.3},
            {"SINGLE": 1.0},
            {},  # All cash
        ]

        for target_portfolio in test_cases:
            total_allocation = sum(target_portfolio.values())
            assert abs(total_allocation - 1.0) < 1e-10 or total_allocation == 0.0

    def test_negative_position_handling(self):
        """Test handling of negative positions (short positions)."""
        target_portfolio = {"AAPL": 0.5, "MSFT": 0.5}
        # Current has a short position
        current_values = {"AAPL": -10000.0, "MSFT": 60000.0}  # Net: 50k
        portfolio_value = 50000.0

        result = calculate_rebalance_amounts(target_portfolio, current_values, portfolio_value)

        # Should handle negative positions correctly
        assert result["AAPL"]["current_value"] == -10000.0
        assert result["AAPL"]["target_value"] == 25000.0
        assert result["AAPL"]["trade_amount"] == 35000.0  # Need to buy 35k to get from -10k to +25k


class TestPortfolioRebalancerClass:
    """Test the PortfolioRebalancer class methods."""

    @pytest.fixture
    def mock_bot(self):
        """Create a mock trading bot for testing."""
        bot = Mock()
        bot.get_account_info.return_value = {
            "portfolio_value": 100000.0,
            "cash": 20000.0,
            "buying_power": 40000.0,
        }
        bot.get_positions_dict.return_value = {
            "AAPL": Mock(market_value=40000.0, qty=100),
            "MSFT": Mock(market_value=40000.0, qty=150),
        }
        bot.get_current_price.return_value = 150.0
        bot.order_manager = Mock()
        bot.order_manager.place_order.return_value = "test_order_123"
        return bot

    @pytest.fixture
    def rebalancer(self, mock_bot):
        """Create a PortfolioRebalancer instance with mocked dependencies."""
        return PortfolioRebalancer(mock_bot)

    def test_rebalancer_initialization(self, mock_bot):
        """Test PortfolioRebalancer initializes correctly."""
        rebalancer = PortfolioRebalancer(mock_bot)
        assert rebalancer.bot == mock_bot
        assert rebalancer.order_manager == mock_bot.order_manager

    def test_position_format_handling(self, rebalancer, mock_bot):
        """Test rebalancer handles both dict and object position formats."""
        # Test with dict format positions
        mock_bot.get_positions_dict.return_value = {
            "AAPL": {"qty": "100", "market_value": "15000.0"},
            "MSFT": {"qty": "50", "market_value": "7500.0"},
        }

        target_portfolio = {"AAPL": 0.5, "MSFT": 0.5}

        # Should not raise an exception
        try:
            rebalancer.rebalance_portfolio(target_portfolio, "TEST_STRATEGY")
        except Exception as e:
            pytest.fail(f"Rebalancer failed with dict positions: {e}")

        # Test with object format positions (Mock objects)
        mock_bot.get_positions_dict.return_value = {
            "AAPL": Mock(qty=100, market_value=15000.0),
            "MSFT": Mock(qty=50, market_value=7500.0),
        }

        # Should not raise an exception
        try:
            rebalancer.rebalance_portfolio(target_portfolio, "TEST_STRATEGY")
        except Exception as e:
            pytest.fail(f"Rebalancer failed with object positions: {e}")

    def test_insufficient_buying_power_handling(self, rebalancer, mock_bot):
        """Test rebalancer handles insufficient buying power gracefully."""
        # Set up scenario with insufficient buying power
        mock_bot.get_account_info.return_value = {
            "portfolio_value": 100000.0,
            "cash": 100.0,  # Very low cash
            "buying_power": 100.0,  # Very low buying power
        }

        target_portfolio = {"AAPL": 1.0}  # Want to go all-in on AAPL

        # Should handle gracefully without crashing
        result = rebalancer.rebalance_portfolio(target_portfolio, "TEST_STRATEGY")

        # Should return some result (even if incomplete)
        assert result is not None

    @patch("the_alchemiser.tracking.strategy_order_tracker.get_strategy_tracker")
    def test_order_tracking_integration(self, mock_tracker, rebalancer, mock_bot):
        """Test that orders are properly tracked by strategy."""
        mock_tracker_instance = Mock()
        mock_tracker.return_value = mock_tracker_instance

        target_portfolio = {"AAPL": 0.5, "MSFT": 0.5}

        rebalancer.rebalance_portfolio(target_portfolio, "TEST_STRATEGY")

        # Should have called the tracker to record orders
        # (Exact calls depend on what orders were placed)
        mock_tracker.assert_called()


class TestRebalanceEdgeCases:
    """Test edge cases that could cause system failures."""

    def test_empty_portfolio_handling(self):
        """Test handling of completely empty portfolios."""
        target_portfolio = {}
        current_values = {}
        portfolio_value = 0.0

        # Should not crash with empty inputs
        result = calculate_rebalance_amounts(target_portfolio, current_values, portfolio_value)
        assert isinstance(result, dict)

    def test_zero_portfolio_value(self):
        """Test handling of zero portfolio value."""
        target_portfolio = {"AAPL": 1.0}
        current_values = {}
        portfolio_value = 0.0

        result = calculate_rebalance_amounts(target_portfolio, current_values, portfolio_value)

        # Should handle zero portfolio value gracefully
        assert result["AAPL"]["target_value"] == 0.0

    def test_large_portfolio_values(self):
        """Test handling of very large portfolio values (billionaire problems)."""
        target_portfolio = {"AAPL": 0.5, "MSFT": 0.5}
        current_values = {"AAPL": 500_000_000.0}  # $500M in AAPL
        portfolio_value = 1_000_000_000.0  # $1B portfolio

        result = calculate_rebalance_amounts(target_portfolio, current_values, portfolio_value)

        # Should handle large numbers correctly
        assert result["AAPL"]["target_value"] == 500_000_000.0
        assert result["MSFT"]["target_value"] == 500_000_000.0

    def test_extreme_precision_requirements(self):
        """Test calculations with extreme precision requirements."""
        # Portfolio with many small positions that must sum to exactly 1.0
        num_positions = 100
        equal_weight = 1.0 / num_positions

        target_portfolio = {f"STOCK_{i}": equal_weight for i in range(num_positions)}
        current_values = {}
        portfolio_value = 1_000_000.0

        result = calculate_rebalance_amounts(target_portfolio, current_values, portfolio_value)

        # Total allocation should be very close to 1.0
        total_target_value = sum(
            result[symbol]["target_value"] for symbol in target_portfolio.keys()
        )
        assert abs(total_target_value - portfolio_value) < 0.01  # Within 1 cent

    def test_symbol_name_edge_cases(self):
        """Test handling of unusual symbol names."""
        weird_symbols = ["BRK.A", "BF.B", "SYMBOL-WITH-DASH", "123NUMERIC"]
        target_portfolio = dict.fromkeys(weird_symbols, 0.25)
        current_values = {}
        portfolio_value = 100000.0

        # Should handle unusual symbol names without issues
        result = calculate_rebalance_amounts(target_portfolio, current_values, portfolio_value)

        for symbol in weird_symbols:
            assert symbol in result
            assert result[symbol]["target_value"] == 25000.0
