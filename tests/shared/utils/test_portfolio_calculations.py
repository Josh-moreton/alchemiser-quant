"""Business Unit: shared | Status: current

Comprehensive unit tests for portfolio calculation utilities.

This test suite provides full coverage of portfolio calculation functions including
allocation comparison, portfolio value calculations, and edge case handling.
"""

import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock

from the_alchemiser.shared.utils.portfolio_calculations import (
    build_allocation_comparison,
)


class TestBuildAllocationComparison:
    """Test allocation comparison building functionality."""

    def setup_method(self):
        """Set up mock settings for each test."""
        self.mock_settings = MagicMock()
        self.mock_settings.alpaca.cash_reserve_pct = 0.01  # 1% cash reserve
        
    @patch('the_alchemiser.shared.utils.portfolio_calculations.load_settings')
    def test_basic_allocation_comparison(self, mock_load_settings):
        """Test basic allocation comparison calculation."""
        mock_load_settings.return_value = self.mock_settings
        
        consolidated_portfolio = {
            "AAPL": 0.5,  # 50%
            "GOOGL": 0.3,  # 30%
            "MSFT": 0.2,  # 20%
        }
        account_dict = {"portfolio_value": 100000.0}
        positions_dict = {
            "AAPL": 45000.0,   # Currently 45%
            "GOOGL": 35000.0,  # Currently 35%
            "MSFT": 20000.0,   # Currently 20%
        }
        
        result = build_allocation_comparison(
            consolidated_portfolio, account_dict, positions_dict
        )
        
        # Effective portfolio value is $100k * 0.99 = $99k (1% cash reserve)
        # Check target values (50%, 30%, 20% of $99k)
        assert result["target_values"]["AAPL"] == Decimal("49500.0000")
        assert result["target_values"]["GOOGL"] == Decimal("29700.0000")
        assert result["target_values"]["MSFT"] == Decimal("19800.0000")
        
        # Check current values
        assert result["current_values"]["AAPL"] == Decimal("45000.0")
        assert result["current_values"]["GOOGL"] == Decimal("35000.0")
        assert result["current_values"]["MSFT"] == Decimal("20000.0")
        
        # Check deltas (target - current)
        assert result["deltas"]["AAPL"] == Decimal("4500.0000")     # Need to buy
        assert result["deltas"]["GOOGL"] == Decimal("-5300.0000")   # Need to sell
        assert result["deltas"]["MSFT"] == Decimal("-200.0000")     # Need to sell a bit

    @patch('the_alchemiser.shared.utils.portfolio_calculations.load_settings')
    def test_zero_portfolio_value_fallback_to_equity(self, mock_load_settings):
        """Test fallback to equity when portfolio_value is zero."""
        mock_load_settings.return_value = self.mock_settings
        
        consolidated_portfolio = {"AAPL": 1.0}
        account_dict = {"portfolio_value": 0.0, "equity": 50000.0}
        positions_dict = {"AAPL": 45000.0}
        
        result = build_allocation_comparison(
            consolidated_portfolio, account_dict, positions_dict
        )
        
        # Should use equity value of $50k * 0.99 = $49.5k
        assert result["target_values"]["AAPL"] == Decimal("49500.0000")

    @patch('the_alchemiser.shared.utils.portfolio_calculations.load_settings')
    def test_missing_portfolio_value_fallback_to_equity(self, mock_load_settings):
        """Test fallback to equity when portfolio_value is missing."""
        mock_load_settings.return_value = self.mock_settings
        
        consolidated_portfolio = {"AAPL": 1.0}
        account_dict = {"equity": 75000.0}  # No portfolio_value key
        positions_dict = {"AAPL": 70000.0}
        
        result = build_allocation_comparison(
            consolidated_portfolio, account_dict, positions_dict
        )
        
        # Should use equity value of $75k * 0.99 = $74.25k
        assert result["target_values"]["AAPL"] == Decimal("74250.0000")

    @patch('the_alchemiser.shared.utils.portfolio_calculations.load_settings')
    def test_string_portfolio_value_conversion(self, mock_load_settings):
        """Test conversion of string portfolio values."""
        mock_load_settings.return_value = self.mock_settings
        
        consolidated_portfolio = {"AAPL": 0.5, "GOOGL": 0.5}
        account_dict = {"portfolio_value": "100000.0"}  # String value
        positions_dict = {"AAPL": 40000.0, "GOOGL": 60000.0}
        
        result = build_allocation_comparison(
            consolidated_portfolio, account_dict, positions_dict
        )
        
        # $100k * 0.99 * 0.5 = $49.5k each
        assert result["target_values"]["AAPL"] == Decimal("49500.0000")
        assert result["target_values"]["GOOGL"] == Decimal("49500.0000")

    def test_missing_both_portfolio_value_and_equity_raises_error(self):
        """Test that missing both values raises ValueError."""
        consolidated_portfolio = {"AAPL": 1.0}
        account_dict = {}  # Missing both portfolio_value and equity
        positions_dict = {"AAPL": 50000.0}
        
        with pytest.raises(ValueError, match="Portfolio value not available"):
            build_allocation_comparison(
                consolidated_portfolio, account_dict, positions_dict
            )

    @patch('the_alchemiser.shared.utils.portfolio_calculations.load_settings')
    def test_empty_consolidated_portfolio_has_current_deltas(self, mock_load_settings):
        """Test handling of empty consolidated portfolio includes current position deltas."""
        mock_load_settings.return_value = self.mock_settings
        
        consolidated_portfolio = {}
        account_dict = {"portfolio_value": 100000.0}
        positions_dict = {"AAPL": 50000.0}
        
        result = build_allocation_comparison(
            consolidated_portfolio, account_dict, positions_dict
        )
        
        # Should have empty target_values but deltas show current positions need to be sold
        assert result["target_values"] == {}
        assert result["deltas"]["AAPL"] == Decimal("-50000.0")  # Need to sell current position
        
        # But should still have current_values
        assert result["current_values"]["AAPL"] == Decimal("50000.0")