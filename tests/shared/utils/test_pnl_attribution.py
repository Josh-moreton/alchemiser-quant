#!/usr/bin/env python3
"""Unit tests for P&L attribution utilities.

Tests decomposition of realized P&L to contributing strategies based on their
allocation weights, including edge cases and property-based tests.
"""

from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from the_alchemiser.shared.utils.pnl_attribution import decompose_pnl_to_strategies


class TestDecomposePnlToStrategies:
    """Tests for decompose_pnl_to_strategies function."""

    def test_single_strategy_full_allocation(self):
        """Test single strategy with 100% allocation receives all P&L."""
        contributions = {
            "momentum": {"AAPL": Decimal("1.0")},
        }
        result = decompose_pnl_to_strategies(
            symbol="AAPL",
            total_pnl=Decimal("500.00"),
            strategy_contributions=contributions,
        )
        assert result == {"momentum": Decimal("500.00")}

    def test_two_strategies_equal_split(self):
        """Test two strategies with equal allocation split P&L equally."""
        contributions = {
            "momentum": {"AAPL": Decimal("0.5")},
            "mean_rev": {"AAPL": Decimal("0.5")},
        }
        result = decompose_pnl_to_strategies(
            symbol="AAPL",
            total_pnl=Decimal("100.00"),
            strategy_contributions=contributions,
        )
        assert result == {
            "momentum": Decimal("50.00"),
            "mean_rev": Decimal("50.00"),
        }

    def test_two_strategies_unequal_split(self):
        """Test two strategies with 60/40 allocation split."""
        contributions = {
            "momentum": {"AAPL": Decimal("0.6")},
            "mean_rev": {"AAPL": Decimal("0.4")},
        }
        result = decompose_pnl_to_strategies(
            symbol="AAPL",
            total_pnl=Decimal("500.00"),
            strategy_contributions=contributions,
        )
        assert result["momentum"] == Decimal("300.00")
        assert result["mean_rev"] == Decimal("200.00")

    def test_multiple_strategies_proportional_split(self):
        """Test multiple strategies with varying allocations."""
        contributions = {
            "momentum": {"AAPL": Decimal("0.5")},
            "mean_rev": {"AAPL": Decimal("0.3")},
            "value": {"AAPL": Decimal("0.2")},
        }
        result = decompose_pnl_to_strategies(
            symbol="AAPL",
            total_pnl=Decimal("1000.00"),
            strategy_contributions=contributions,
        )
        assert result["momentum"] == Decimal("500.00")
        assert result["mean_rev"] == Decimal("300.00")
        assert result["value"] == Decimal("200.00")

    def test_negative_pnl_loss_distribution(self):
        """Test negative P&L (losses) are distributed proportionally."""
        contributions = {
            "momentum": {"AAPL": Decimal("0.6")},
            "mean_rev": {"AAPL": Decimal("0.4")},
        }
        result = decompose_pnl_to_strategies(
            symbol="AAPL",
            total_pnl=Decimal("-100.00"),
            strategy_contributions=contributions,
        )
        assert result["momentum"] == Decimal("-60.00")
        assert result["mean_rev"] == Decimal("-40.00")

    def test_zero_pnl(self):
        """Test zero P&L results in zero for all strategies."""
        contributions = {
            "momentum": {"AAPL": Decimal("0.6")},
            "mean_rev": {"AAPL": Decimal("0.4")},
        }
        result = decompose_pnl_to_strategies(
            symbol="AAPL",
            total_pnl=Decimal("0.00"),
            strategy_contributions=contributions,
        )
        assert result["momentum"] == Decimal("0.00")
        assert result["mean_rev"] == Decimal("0.00")

    def test_small_pnl_precision(self):
        """Test small P&L amounts preserve decimal precision."""
        contributions = {
            "momentum": {"AAPL": Decimal("0.6")},
            "mean_rev": {"AAPL": Decimal("0.4")},
        }
        result = decompose_pnl_to_strategies(
            symbol="AAPL",
            total_pnl=Decimal("0.01"),
            strategy_contributions=contributions,
        )
        # 0.01 * 0.6 = 0.006, 0.01 * 0.4 = 0.004
        assert result["momentum"] == Decimal("0.006")
        assert result["mean_rev"] == Decimal("0.004")

    def test_multiple_symbols_single_strategy_per_symbol(self):
        """Test symbol with single contributing strategy."""
        contributions = {
            "momentum": {"AAPL": Decimal("1.0"), "MSFT": Decimal("0.5")},
            "mean_rev": {"MSFT": Decimal("0.5")},
        }
        # AAPL only has momentum
        result_aapl = decompose_pnl_to_strategies(
            symbol="AAPL",
            total_pnl=Decimal("100.00"),
            strategy_contributions=contributions,
        )
        assert result_aapl == {"momentum": Decimal("100.00")}

        # MSFT has both strategies
        result_msft = decompose_pnl_to_strategies(
            symbol="MSFT",
            total_pnl=Decimal("100.00"),
            strategy_contributions=contributions,
        )
        assert result_msft["momentum"] == Decimal("50.00")
        assert result_msft["mean_rev"] == Decimal("50.00")

    def test_symbol_not_in_contributions_raises_error(self):
        """Test error when symbol has no contributions."""
        contributions = {
            "momentum": {"AAPL": Decimal("1.0")},
        }
        with pytest.raises(ValueError, match="has no strategy contributions"):
            decompose_pnl_to_strategies(
                symbol="GOOGL",
                total_pnl=Decimal("100.00"),
                strategy_contributions=contributions,
            )

    def test_zero_total_allocation_raises_error(self):
        """Test error when all allocations are zero."""
        contributions = {
            "momentum": {"AAPL": Decimal("0.0")},
            "mean_rev": {"AAPL": Decimal("0.0")},
        }
        with pytest.raises(ValueError, match="Total allocation.*is zero"):
            decompose_pnl_to_strategies(
                symbol="AAPL",
                total_pnl=Decimal("100.00"),
                strategy_contributions=contributions,
            )

    def test_empty_contributions_dict_raises_error(self):
        """Test error with empty contributions dictionary."""
        contributions: dict[str, dict[str, Decimal]] = {}
        with pytest.raises(ValueError, match="has no strategy contributions"):
            decompose_pnl_to_strategies(
                symbol="AAPL",
                total_pnl=Decimal("100.00"),
                strategy_contributions=contributions,
            )

    def test_partial_allocations_sum_less_than_one(self):
        """Test decomposition works even if allocations don't sum to 1.0."""
        # This can happen in partial portfolios or when tracking specific strategies
        contributions = {
            "momentum": {"AAPL": Decimal("0.3")},
            "mean_rev": {"AAPL": Decimal("0.2")},
        }
        result = decompose_pnl_to_strategies(
            symbol="AAPL",
            total_pnl=Decimal("100.00"),
            strategy_contributions=contributions,
        )
        # Total allocation = 0.5
        # momentum: 0.3 / 0.5 = 0.6 → 60% of P&L
        # mean_rev: 0.2 / 0.5 = 0.4 → 40% of P&L
        assert result["momentum"] == Decimal("60.00")
        assert result["mean_rev"] == Decimal("40.00")

    def test_large_pnl_values(self):
        """Test decomposition with large P&L values."""
        contributions = {
            "momentum": {"AAPL": Decimal("0.6")},
            "mean_rev": {"AAPL": Decimal("0.4")},
        }
        result = decompose_pnl_to_strategies(
            symbol="AAPL",
            total_pnl=Decimal("1000000.00"),
            strategy_contributions=contributions,
        )
        assert result["momentum"] == Decimal("600000.00")
        assert result["mean_rev"] == Decimal("400000.00")

    def test_very_small_allocations(self):
        """Test decomposition with very small allocation weights."""
        contributions = {
            "momentum": {"AAPL": Decimal("0.001")},
            "mean_rev": {"AAPL": Decimal("0.001")},
        }
        result = decompose_pnl_to_strategies(
            symbol="AAPL",
            total_pnl=Decimal("100.00"),
            strategy_contributions=contributions,
        )
        # Each gets 50% of the P&L
        assert result["momentum"] == Decimal("50.00")
        assert result["mean_rev"] == Decimal("50.00")


class TestDecomposePnlPropertyBased:
    """Property-based tests for P&L decomposition using Hypothesis."""

    @given(
        st.decimals(
            min_value=Decimal("-10000"),
            max_value=Decimal("10000"),
            places=2,
        ),
        st.lists(
            st.decimals(
                min_value=Decimal("0.01"),
                max_value=Decimal("1.0"),
                places=2,
            ),
            min_size=1,
            max_size=10,
        ),
    )
    def test_sum_of_decomposed_pnl_equals_total(
        self, total_pnl: Decimal, allocations: list[Decimal]
    ):
        """Property: Sum of decomposed P&L must equal total P&L."""
        # Create contributions from allocations
        contributions = {f"strategy_{i}": {"AAPL": alloc} for i, alloc in enumerate(allocations)}

        result = decompose_pnl_to_strategies(
            symbol="AAPL",
            total_pnl=total_pnl,
            strategy_contributions=contributions,
        )

        # Sum of all strategy P&L should equal total P&L
        decomposed_sum = sum(result.values())

        # Use small tolerance for floating point comparison
        tolerance = Decimal("0.01")
        diff = abs(decomposed_sum - total_pnl)
        assert diff <= tolerance, f"Sum {decomposed_sum} != total {total_pnl}, diff={diff}"

    @given(
        st.lists(
            st.decimals(
                min_value=Decimal("0.01"),
                max_value=Decimal("1.0"),
                places=3,
            ),
            min_size=2,
            max_size=5,
        )
    )
    def test_proportional_decomposition_maintains_ratios(self, allocations: list[Decimal]):
        """Property: Decomposed P&L maintains allocation ratios."""
        # Skip if all allocations are the same (no ratio to test)
        if len(set(allocations)) == 1:
            return

        contributions = {f"strategy_{i}": {"AAPL": alloc} for i, alloc in enumerate(allocations)}

        total_pnl = Decimal("1000.00")
        result = decompose_pnl_to_strategies(
            symbol="AAPL",
            total_pnl=total_pnl,
            strategy_contributions=contributions,
        )

        # Check that ratios are preserved
        total_allocation = sum(allocations)
        for i, alloc in enumerate(allocations):
            strategy_id = f"strategy_{i}"
            expected_proportion = alloc / total_allocation
            actual_pnl = result[strategy_id]
            expected_pnl = total_pnl * expected_proportion

            # Allow small tolerance for decimal arithmetic
            tolerance = Decimal("0.01")
            diff = abs(actual_pnl - expected_pnl)
            assert diff <= tolerance, (
                f"Strategy {strategy_id}: expected {expected_pnl}, got {actual_pnl}, diff={diff}"
            )

    @given(
        st.decimals(
            min_value=Decimal("0.01"),
            max_value=Decimal("10000"),
            places=2,
        )
    )
    def test_single_strategy_receives_all_pnl(self, total_pnl: Decimal):
        """Property: Single strategy with 100% allocation gets all P&L."""
        contributions = {
            "only_strategy": {"AAPL": Decimal("1.0")},
        }
        result = decompose_pnl_to_strategies(
            symbol="AAPL",
            total_pnl=total_pnl,
            strategy_contributions=contributions,
        )
        assert result["only_strategy"] == total_pnl

    @given(
        st.decimals(
            min_value=Decimal("-10000"),
            max_value=Decimal("-0.01"),
            places=2,
        ),
        st.lists(
            st.decimals(
                min_value=Decimal("0.01"),
                max_value=Decimal("1.0"),
                places=2,
            ),
            min_size=1,
            max_size=5,
        ),
    )
    def test_negative_pnl_decomposition_sum(self, total_pnl: Decimal, allocations: list[Decimal]):
        """Property: Negative P&L decomposition sums correctly."""
        contributions = {f"strategy_{i}": {"AAPL": alloc} for i, alloc in enumerate(allocations)}

        result = decompose_pnl_to_strategies(
            symbol="AAPL",
            total_pnl=total_pnl,
            strategy_contributions=contributions,
        )

        # All individual P&L values should be negative
        for strategy_pnl in result.values():
            assert strategy_pnl <= 0, f"Expected negative P&L, got {strategy_pnl}"

        # Sum should equal total (negative)
        decomposed_sum = sum(result.values())
        tolerance = Decimal("0.01")
        diff = abs(decomposed_sum - total_pnl)
        assert diff <= tolerance


class TestStrategyContributionsSumValidation:
    """Tests validating that strategy contributions sum correctly."""

    def test_contributions_sum_equals_target_allocation(self):
        """Test that strategy contributions for a symbol sum to expected value."""
        contributions = {
            "momentum": {"AAPL": Decimal("0.6"), "MSFT": Decimal("0.3")},
            "mean_rev": {"AAPL": Decimal("0.4"), "MSFT": Decimal("0.2")},
        }

        # Validate AAPL contributions sum to 1.0
        aapl_total = sum(
            allocations["AAPL"] for allocations in contributions.values() if "AAPL" in allocations
        )
        assert aapl_total == Decimal("1.0")

        # Validate MSFT contributions sum to 0.5
        msft_total = sum(
            allocations["MSFT"] for allocations in contributions.values() if "MSFT" in allocations
        )
        assert msft_total == Decimal("0.5")

    @given(
        st.lists(
            st.decimals(
                min_value=Decimal("0.01"),
                max_value=Decimal("0.5"),
                places=2,
            ),
            min_size=2,
            max_size=10,
        )
    )
    def test_property_contributions_consistency(self, allocations: list[Decimal]):
        """Property: Total allocation equals sum of individual contributions."""
        contributions = {f"strategy_{i}": {"AAPL": alloc} for i, alloc in enumerate(allocations)}

        # Calculate total allocation
        total_allocation = sum(
            allocations["AAPL"] for allocations in contributions.values() if "AAPL" in allocations
        )

        # Decompose some P&L
        result = decompose_pnl_to_strategies(
            symbol="AAPL",
            total_pnl=Decimal("100.00"),
            strategy_contributions=contributions,
        )

        # Each strategy's proportion should be allocation / total_allocation
        for i, alloc in enumerate(allocations):
            strategy_id = f"strategy_{i}"
            expected_proportion = alloc / total_allocation
            actual_proportion = result[strategy_id] / Decimal("100.00")

            tolerance = Decimal("0.001")
            diff = abs(actual_proportion - expected_proportion)
            assert diff <= tolerance
