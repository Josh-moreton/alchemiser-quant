"""Business Unit: shared | Status: current

Comprehensive unit tests for portfolio calculation utilities.

This test suite provides full coverage of portfolio calculation functions including
allocation comparison, portfolio value calculations, and edge case handling.
"""

import pytest
from decimal import Decimal
from unittest.mock import patch

from the_alchemiser.shared.utils.portfolio_calculations import (
    build_allocation_comparison,
)


class TestBuildAllocationComparison:
    """Test allocation comparison building functionality."""

    def test_basic_allocation_comparison(self):
        """Test basic allocation comparison calculation."""
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
        
        # Check target values (50%, 30%, 20% of $100k)
        assert result["target_values"]["AAPL"] == Decimal("50000.00")
        assert result["target_values"]["GOOGL"] == Decimal("30000.00")
        assert result["target_values"]["MSFT"] == Decimal("20000.00")
        
        # Check current values
        assert result["current_values"]["AAPL"] == Decimal("45000.00")
        assert result["current_values"]["GOOGL"] == Decimal("35000.00")
        assert result["current_values"]["MSFT"] == Decimal("20000.00")
        
        # Check deltas (target - current)
        assert result["deltas"]["AAPL"] == Decimal("5000.00")    # Need to buy $5k
        assert result["deltas"]["GOOGL"] == Decimal("-5000.00")  # Need to sell $5k
        assert result["deltas"]["MSFT"] == Decimal("0.00")       # No change needed

    def test_zero_portfolio_value_fallback_to_equity(self):
        """Test fallback to equity when portfolio_value is zero."""
        consolidated_portfolio = {"AAPL": 1.0}
        account_dict = {"portfolio_value": 0.0, "equity": 50000.0}
        positions_dict = {"AAPL": 45000.0}
        
        result = build_allocation_comparison(
            consolidated_portfolio, account_dict, positions_dict
        )
        
        # Should use equity value of $50k
        assert result["target_values"]["AAPL"] == Decimal("50000.00")

    def test_missing_portfolio_value_fallback_to_equity(self):
        """Test fallback to equity when portfolio_value is missing."""
        consolidated_portfolio = {"AAPL": 1.0}
        account_dict = {"equity": 75000.0}  # No portfolio_value key
        positions_dict = {"AAPL": 70000.0}
        
        result = build_allocation_comparison(
            consolidated_portfolio, account_dict, positions_dict
        )
        
        # Should use equity value of $75k
        assert result["target_values"]["AAPL"] == Decimal("75000.00")

    def test_string_portfolio_value_conversion(self):
        """Test conversion of string portfolio values."""
        consolidated_portfolio = {"AAPL": 0.5, "GOOGL": 0.5}
        account_dict = {"portfolio_value": "100000.0"}  # String value
        positions_dict = {"AAPL": 40000.0, "GOOGL": 60000.0}
        
        result = build_allocation_comparison(
            consolidated_portfolio, account_dict, positions_dict
        )
        
        assert result["target_values"]["AAPL"] == Decimal("50000.00")
        assert result["target_values"]["GOOGL"] == Decimal("50000.00")

    def test_missing_both_portfolio_value_and_equity_raises_error(self):
        """Test that missing both values raises ValueError."""
        consolidated_portfolio = {"AAPL": 1.0}
        account_dict = {}  # Missing both portfolio_value and equity
        positions_dict = {"AAPL": 50000.0}
        
        with pytest.raises(ValueError, match="Portfolio value not available"):
            build_allocation_comparison(
                consolidated_portfolio, account_dict, positions_dict
            )

    def test_position_not_in_current_positions(self):
        """Test handling when target position is not in current positions."""
        consolidated_portfolio = {
            "AAPL": 0.6,
            "GOOGL": 0.4,
        }
        account_dict = {"portfolio_value": 100000.0}
        positions_dict = {
            "AAPL": 50000.0,
            # GOOGL missing from current positions
        }
        
        result = build_allocation_comparison(
            consolidated_portfolio, account_dict, positions_dict
        )
        
        # Target values should still be calculated
        assert result["target_values"]["AAPL"] == Decimal("60000.00")
        assert result["target_values"]["GOOGL"] == Decimal("40000.00")
        
        # Current values
        assert result["current_values"]["AAPL"] == Decimal("50000.00")
        assert result["current_values"]["GOOGL"] == Decimal("0.00")  # Should default to 0
        
        # Deltas
        assert result["deltas"]["AAPL"] == Decimal("10000.00")   # Need to buy more
        assert result["deltas"]["GOOGL"] == Decimal("40000.00")  # Need to buy (new position)

    def test_current_position_not_in_target(self):
        """Test handling when current position is not in target allocation."""
        consolidated_portfolio = {
            "AAPL": 1.0,  # Only AAPL in target
        }
        account_dict = {"portfolio_value": 100000.0}
        positions_dict = {
            "AAPL": 80000.0,
            "GOOGL": 20000.0,  # GOOGL not in target allocation
        }
        
        result = build_allocation_comparison(
            consolidated_portfolio, account_dict, positions_dict
        )
        
        # Only AAPL should be in target_values and deltas
        assert "AAPL" in result["target_values"]
        assert "GOOGL" not in result["target_values"]
        assert "GOOGL" not in result["deltas"]
        
        # But GOOGL should be in current_values
        assert result["current_values"]["GOOGL"] == Decimal("20000.00")
        
        assert result["target_values"]["AAPL"] == Decimal("100000.00")
        assert result["deltas"]["AAPL"] == Decimal("20000.00")

    def test_zero_allocation_percentages(self):
        """Test handling of zero allocation percentages."""
        consolidated_portfolio = {
            "AAPL": 0.0,  # 0% allocation
            "GOOGL": 1.0, # 100% allocation
        }
        account_dict = {"portfolio_value": 100000.0}
        positions_dict = {
            "AAPL": 10000.0,  # Currently have some AAPL
            "GOOGL": 90000.0,
        }
        
        result = build_allocation_comparison(
            consolidated_portfolio, account_dict, positions_dict
        )
        
        # Target values
        assert result["target_values"]["AAPL"] == Decimal("0.00")
        assert result["target_values"]["GOOGL"] == Decimal("100000.00")
        
        # Deltas - should sell all AAPL, buy more GOOGL
        assert result["deltas"]["AAPL"] == Decimal("-10000.00")
        assert result["deltas"]["GOOGL"] == Decimal("10000.00")

    def test_fractional_percentages(self):
        """Test handling of fractional allocation percentages."""
        consolidated_portfolio = {
            "AAPL": 0.333333,  # 33.3333%
            "GOOGL": 0.666667, # 66.6667%
        }
        account_dict = {"portfolio_value": 100000.0}
        positions_dict = {
            "AAPL": 33000.0,
            "GOOGL": 67000.0,
        }
        
        result = build_allocation_comparison(
            consolidated_portfolio, account_dict, positions_dict
        )
        
        # Should handle fractional calculations with Decimal precision
        assert result["target_values"]["AAPL"] == Decimal("33333.30")
        assert result["target_values"]["GOOGL"] == Decimal("66666.70")
        
        assert result["deltas"]["AAPL"] == Decimal("333.30")
        assert result["deltas"]["GOOGL"] == Decimal("-333.30")

    def test_large_portfolio_values(self):
        """Test handling of large portfolio values."""
        consolidated_portfolio = {
            "AAPL": 0.5,
            "GOOGL": 0.5,
        }
        account_dict = {"portfolio_value": 10000000.0}  # $10M portfolio
        positions_dict = {
            "AAPL": 4500000.0,
            "GOOGL": 5500000.0,
        }
        
        result = build_allocation_comparison(
            consolidated_portfolio, account_dict, positions_dict
        )
        
        assert result["target_values"]["AAPL"] == Decimal("5000000.00")
        assert result["target_values"]["GOOGL"] == Decimal("5000000.00")
        
        assert result["deltas"]["AAPL"] == Decimal("500000.00")
        assert result["deltas"]["GOOGL"] == Decimal("-500000.00")

    def test_small_portfolio_values(self):
        """Test handling of small portfolio values."""
        consolidated_portfolio = {
            "AAPL": 0.5,
            "GOOGL": 0.5,
        }
        account_dict = {"portfolio_value": 100.0}  # $100 portfolio
        positions_dict = {
            "AAPL": 45.0,
            "GOOGL": 55.0,
        }
        
        result = build_allocation_comparison(
            consolidated_portfolio, account_dict, positions_dict
        )
        
        assert result["target_values"]["AAPL"] == Decimal("50.00")
        assert result["target_values"]["GOOGL"] == Decimal("50.00")
        
        assert result["deltas"]["AAPL"] == Decimal("5.00")
        assert result["deltas"]["GOOGL"] == Decimal("-5.00")

    def test_empty_consolidated_portfolio(self):
        """Test handling of empty consolidated portfolio."""
        consolidated_portfolio = {}
        account_dict = {"portfolio_value": 100000.0}
        positions_dict = {"AAPL": 50000.0}
        
        result = build_allocation_comparison(
            consolidated_portfolio, account_dict, positions_dict
        )
        
        # Should have empty target_values and deltas
        assert result["target_values"] == {}
        assert result["deltas"] == {}
        
        # But should still have current_values
        assert result["current_values"]["AAPL"] == Decimal("50000.00")

    def test_empty_positions_dict(self):
        """Test handling of empty current positions."""
        consolidated_portfolio = {
            "AAPL": 0.5,
            "GOOGL": 0.5,
        }
        account_dict = {"portfolio_value": 100000.0}
        positions_dict = {}
        
        result = build_allocation_comparison(
            consolidated_portfolio, account_dict, positions_dict
        )
        
        # Target values should still be calculated
        assert result["target_values"]["AAPL"] == Decimal("50000.00")
        assert result["target_values"]["GOOGL"] == Decimal("50000.00")
        
        # Current values should be zero
        assert result["current_values"]["AAPL"] == Decimal("0.00")
        assert result["current_values"]["GOOGL"] == Decimal("0.00")
        
        # Deltas should equal target values (need to buy everything)
        assert result["deltas"]["AAPL"] == Decimal("50000.00")
        assert result["deltas"]["GOOGL"] == Decimal("50000.00")

    def test_negative_current_positions(self):
        """Test handling of negative current position values."""
        consolidated_portfolio = {"AAPL": 1.0}
        account_dict = {"portfolio_value": 100000.0}
        positions_dict = {"AAPL": -10000.0}  # Negative position (short?)
        
        result = build_allocation_comparison(
            consolidated_portfolio, account_dict, positions_dict
        )
        
        assert result["target_values"]["AAPL"] == Decimal("100000.00")
        assert result["current_values"]["AAPL"] == Decimal("-10000.00")
        assert result["deltas"]["AAPL"] == Decimal("110000.00")  # Need to buy $110k to get to target