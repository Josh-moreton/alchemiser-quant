"""Business Unit: shared | Status: current

Comprehensive unit tests for portfolio calculation utilities.

This test suite provides full coverage of portfolio calculation functions including
allocation comparison, portfolio value calculations, and edge case handling.
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from the_alchemiser.shared.errors.exceptions import ConfigurationError
from the_alchemiser.shared.utils.portfolio_calculations import (
    build_allocation_comparison,
)


class TestBuildAllocationComparison:
    """Test allocation comparison building functionality."""

    def setup_method(self):
        """Set up mock settings for each test."""
        self.mock_settings = MagicMock()
        self.mock_settings.alpaca.cash_reserve_pct = 0.01  # 1% cash reserve

    @patch("the_alchemiser.shared.utils.portfolio_calculations.load_settings")
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
            "AAPL": 45000.0,  # Currently 45%
            "GOOGL": 35000.0,  # Currently 35%
            "MSFT": 20000.0,  # Currently 20%
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
        assert result["deltas"]["AAPL"] == Decimal("4500.0000")  # Need to buy
        assert result["deltas"]["GOOGL"] == Decimal("-5300.0000")  # Need to sell
        assert result["deltas"]["MSFT"] == Decimal("-200.0000")  # Need to sell a bit

    @patch("the_alchemiser.shared.utils.portfolio_calculations.load_settings")
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

    @patch("the_alchemiser.shared.utils.portfolio_calculations.load_settings")
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

    @patch("the_alchemiser.shared.utils.portfolio_calculations.load_settings")
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
        """Test that missing both values raises ConfigurationError."""
        consolidated_portfolio = {"AAPL": 1.0}
        account_dict = {}  # Missing both portfolio_value and equity
        positions_dict = {"AAPL": 50000.0}

        with pytest.raises(ConfigurationError, match="Portfolio value not available"):
            build_allocation_comparison(
                consolidated_portfolio, account_dict, positions_dict
            )

    @patch("the_alchemiser.shared.utils.portfolio_calculations.load_settings")
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
        assert result["deltas"]["AAPL"] == Decimal(
            "-50000.0"
        )  # Need to sell current position

        # But should still have current_values
        assert result["current_values"]["AAPL"] == Decimal("50000.0")


class TestPropertyBasedAllocationComparison:
    """Property-based tests using Hypothesis for mathematical properties."""

    def setup_method(self):
        """Set up mock settings for each test."""
        self.mock_settings = MagicMock()
        self.mock_settings.alpaca.cash_reserve_pct = 0.01  # 1% cash reserve

    @given(
        portfolio_value=st.floats(min_value=1000.0, max_value=10_000_000.0),
        allocation=st.floats(min_value=0.0, max_value=1.0),
    )
    @patch("the_alchemiser.shared.utils.portfolio_calculations.load_settings")
    def test_target_value_proportional_to_portfolio_value(
        self, mock_load_settings, portfolio_value: float, allocation: float
    ):
        """Test that target values scale proportionally with portfolio value."""
        mock_load_settings.return_value = self.mock_settings

        consolidated_portfolio = {"AAPL": allocation}
        account_dict = {"portfolio_value": portfolio_value}
        positions_dict = {}

        result = build_allocation_comparison(
            consolidated_portfolio, account_dict, positions_dict
        )

        # Expected: target_value = portfolio_value * 0.99 * allocation
        expected = (
            Decimal(str(portfolio_value)) * Decimal("0.99") * Decimal(str(allocation))
        )
        actual = result["target_values"]["AAPL"]

        # Use tolerance for float->Decimal conversion
        # Float precision can introduce errors up to ~1e-14 relative error,
        # which for values near $1000 can be ~0.02 absolute error
        tolerance = max(Decimal("0.02"), abs(expected) * Decimal("0.0001"))
        assert abs(actual - expected) <= tolerance

    @given(
        portfolio_value=st.floats(min_value=1000.0, max_value=1_000_000.0),
        num_symbols=st.integers(min_value=1, max_value=10),
    )
    @patch("the_alchemiser.shared.utils.portfolio_calculations.load_settings")
    def test_deltas_sum_property(
        self, mock_load_settings, portfolio_value: float, num_symbols: int
    ):
        """Test that sum of deltas equals effective portfolio value when starting from empty."""
        mock_load_settings.return_value = self.mock_settings

        # Create equal-weight portfolio
        weight = 1.0 / num_symbols
        symbols = [f"SYM{i}" for i in range(num_symbols)]
        consolidated_portfolio = dict.fromkeys(symbols, weight)

        account_dict = {"portfolio_value": portfolio_value}
        positions_dict = {}  # Start with empty portfolio

        result = build_allocation_comparison(
            consolidated_portfolio, account_dict, positions_dict
        )

        # Sum of all deltas should equal effective portfolio value (99% of total)
        total_deltas = sum(result["deltas"].values())
        expected_total = Decimal(str(portfolio_value)) * Decimal("0.99")

        # Allow small tolerance for rounding
        tolerance = Decimal("0.10")
        assert abs(total_deltas - expected_total) <= tolerance

    @given(
        portfolio_value=st.floats(min_value=1000.0, max_value=1_000_000.0),
        symbol=st.text(
            min_size=1, max_size=5, alphabet=st.characters(whitelist_categories=("Lu",))
        ),
        current_value=st.floats(min_value=0.0, max_value=100_000.0),
    )
    @patch("the_alchemiser.shared.utils.portfolio_calculations.load_settings")
    def test_delta_calculation_consistency(
        self,
        mock_load_settings,
        portfolio_value: float,
        symbol: str,
        current_value: float,
    ):
        """Test that delta = target - current for all cases."""
        mock_load_settings.return_value = self.mock_settings
        assume(symbol)  # Ensure symbol is not empty

        target_allocation = 0.5  # 50%
        consolidated_portfolio = {symbol: target_allocation}
        account_dict = {"portfolio_value": portfolio_value}
        positions_dict = {symbol: current_value}

        result = build_allocation_comparison(
            consolidated_portfolio, account_dict, positions_dict
        )

        # Verify delta = target - current
        target = result["target_values"][symbol]
        current = result["current_values"][symbol]
        delta = result["deltas"][symbol]

        # Must be exact for Decimal arithmetic
        assert delta == target - current

    @given(
        portfolio_value=st.floats(min_value=1000.0, max_value=1_000_000.0),
    )
    @patch("the_alchemiser.shared.utils.portfolio_calculations.load_settings")
    def test_all_symbols_included_in_output(
        self, mock_load_settings, portfolio_value: float
    ):
        """Test that all symbols from both inputs appear in deltas."""
        mock_load_settings.return_value = self.mock_settings

        consolidated_portfolio = {"AAPL": 0.5, "GOOGL": 0.5}
        account_dict = {"portfolio_value": portfolio_value}
        positions_dict = {"MSFT": 10000.0, "AAPL": 20000.0}  # MSFT not in target

        result = build_allocation_comparison(
            consolidated_portfolio, account_dict, positions_dict
        )

        # All unique symbols should appear in deltas
        all_symbols = {"AAPL", "GOOGL", "MSFT"}
        assert set(result["deltas"].keys()) == all_symbols

        # Symbols only in positions should have negative deltas (need to sell)
        assert result["deltas"]["MSFT"] < Decimal("0")

        # Symbols only in targets should have positive deltas (need to buy)
        assert result["deltas"]["GOOGL"] > Decimal("0")
