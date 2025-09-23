#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Strategy logic validation tests for DSL engine.

Tests that validate actual strategy decision-making logic and ensure
different market conditions produce the expected portfolio allocations.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.utils.test_harness import DslTestHarness


@pytest.mark.strategy
class TestStrategyLogicExecution:
    """Test actual strategy logic execution and decision paths."""

    def test_nuclear_strategy_rsi_conditions(self, repository_root: Path) -> None:
        """Test Nuclear strategy responds to different RSI values."""
        harness = DslTestHarness(str(repository_root), seed=42)

        # Test high RSI condition (> 79) - should trigger UVXY defensive allocation
        harness.mock_market_data.set_rsi("SPY", 85)
        result = harness.evaluate_strategy("Nuclear.clj")

        assert result.success, "Nuclear strategy should evaluate successfully"
        assert result.allocation_result is not None, "Should produce allocation"
        assert (
            "UVXY" in result.allocation_result.target_weights
        ), "High RSI should trigger UVXY"

        # Test normal RSI condition - should trigger different allocation
        harness.reset_state()
        harness.mock_market_data.set_rsi("SPY", 50)
        result2 = harness.evaluate_strategy("Nuclear.clj")

        assert result2.success, "Nuclear strategy should evaluate successfully"
        assert result2.allocation_result is not None, "Should produce allocation"
        assert (
            result.allocation_result.target_weights
            != result2.allocation_result.target_weights
        ), "Different RSI values should produce different allocations"

    @pytest.mark.parametrize(
        "rsi_value,expected_behavior",
        [
            (85, "defensive"),  # High RSI should trigger defensive UVXY
            (
                50,
                "mixed",
            ),  # Mid RSI should trigger mixed behavior (could be nuclear or bear logic)
            (25, "aggressive"),  # Low RSI should trigger aggressive allocation
        ],
    )
    def test_nuclear_rsi_boundaries(
        self, repository_root: Path, rsi_value: float, expected_behavior: str
    ) -> None:
        """Test Nuclear strategy at RSI boundary conditions."""
        harness = DslTestHarness(str(repository_root), seed=42)

        # Set RSI for all symbols that Nuclear strategy checks
        symbols_to_set = ["SPY", "IOO", "TQQQ", "VTV", "XLF", "VOX", "PSQ"]
        for symbol in symbols_to_set:
            harness.mock_market_data.set_rsi(symbol, rsi_value)

        result = harness.evaluate_strategy("Nuclear.clj")

        assert (
            result.success
        ), f"Nuclear should evaluate successfully with RSI {rsi_value}"
        assert result.allocation_result is not None, "Should produce allocation"

        allocations = result.allocation_result.target_weights

        if expected_behavior == "defensive":
            assert (
                "UVXY" in allocations
            ), f"High RSI {rsi_value} should allocate to UVXY, got {dict(allocations)}"
            # Check that UVXY has significant allocation
            assert (
                allocations["UVXY"] > 0.5
            ), f"UVXY should have significant allocation, got {allocations['UVXY']}"
        elif expected_behavior == "mixed":
            # Should allocate to any valid strategy assets (nuclear, bear, etc.)
            # Nuclear strategy is complex with many possible allocations
            valid_stocks = {
                "SMR",
                "BWXT",
                "LEU",
                "EXC",
                "NLR",
                "OKLO",
                "SQQQ",
                "TQQQ",
                "UPRO",
                "QQQ",
                "PSQ",
            }
            allocated_stocks = set(allocations.keys())
            assert allocated_stocks.intersection(
                valid_stocks
            ), f"Mixed RSI {rsi_value} should allocate to valid strategy assets, got {dict(allocations)}"
        elif expected_behavior == "aggressive":
            aggressive_stocks = {"UPRO", "TECL", "TQQQ"}
            allocated_stocks = set(allocations.keys())
            assert allocated_stocks.intersection(
                aggressive_stocks
            ), f"Low RSI {rsi_value} should allocate to aggressive stocks, got {dict(allocations)}"
            # Verify significant allocation to aggressive stock
            for symbol in allocated_stocks:
                if symbol in aggressive_stocks:
                    assert (
                        allocations[symbol] > 0.5
                    ), f"Aggressive allocation should be significant, got {allocations[symbol]}"

    def test_tecl_strategy_weight_allocations(self, repository_root: Path) -> None:
        """Test TECL strategy produces correct weight allocations."""
        harness = DslTestHarness(str(repository_root), seed=42)

        # Mock conditions for defensive UVXY+BIL allocation
        harness.mock_market_data.set_rsi("TQQQ", 85)
        harness.mock_market_data.set_rsi("XLK", 85)
        result = harness.evaluate_strategy("TECL.clj")

        assert result.success, "TECL strategy should evaluate successfully"
        assert result.allocation_result is not None, "Should produce allocation"

        allocations = result.allocation_result.target_weights

        # Should have defensive allocation when RSI is high
        assert (
            "UVXY" in allocations or "BIL" in allocations
        ), f"High RSI should trigger defensive allocation, got {dict(allocations)}"

        # Test aggressive allocation with low RSI
        harness.reset_state()
        harness.mock_market_data.set_rsi("TQQQ", 25)
        harness.mock_market_data.set_rsi("XLK", 25)
        result2 = harness.evaluate_strategy("TECL.clj")

        assert result2.success, "TECL strategy should evaluate successfully"
        assert result2.allocation_result is not None, "Should produce allocation"

        allocations2 = result2.allocation_result.target_weights

        # Should have aggressive allocation when RSI is low
        assert (
            "TECL" in allocations2
        ), f"Low RSI should trigger TECL allocation, got {dict(allocations2)}"

        # Verify different conditions produce different allocations
        assert (
            allocations != allocations2
        ), "Different market conditions should produce different allocations"

    def test_klm_strategy_decision_logic(self, repository_root: Path) -> None:
        """Test KLM strategy decision tree logic."""
        harness = DslTestHarness(str(repository_root), seed=42)

        # Test with high RSI across multiple symbols (should trigger UVXY)
        symbols_to_test = ["QQQE", "VTV", "VOX", "TECL"]
        for symbol in symbols_to_test:
            harness.mock_market_data.set_rsi(symbol, 85)

        result = harness.evaluate_strategy("KLM.clj")

        assert result.success, "KLM strategy should evaluate successfully"
        assert result.allocation_result is not None, "Should produce allocation"

        allocations = result.allocation_result.target_weights

        # KLM should trigger defensive allocation with high RSI
        assert (
            "UVXY" in allocations
        ), f"High RSI should trigger UVXY allocation, got {dict(allocations)}"

    def test_strategy_allocation_weights_sum_to_one(
        self, repository_root: Path
    ) -> None:
        """Test that all strategy allocations sum to 1.0."""
        harness = DslTestHarness(str(repository_root), seed=42)

        strategies_to_test = ["Nuclear.clj", "TECL.clj", "KLM.clj", "Grail.clj"]

        for strategy_file in strategies_to_test:
            harness.reset_state()
            result = harness.evaluate_strategy(strategy_file)

            assert result.success, f"{strategy_file} should evaluate successfully"
            assert (
                result.allocation_result is not None
            ), f"{strategy_file} should produce allocation"

            total_weight = sum(result.allocation_result.target_weights.values())
            assert (
                abs(float(total_weight) - 1.0) < 0.001
            ), f"{strategy_file} allocations must sum to 1.0, got {total_weight}"

    def test_strategy_no_negative_allocations(self, repository_root: Path) -> None:
        """Test that strategies never produce negative allocations."""
        harness = DslTestHarness(str(repository_root), seed=42)

        strategies_to_test = ["Nuclear.clj", "TECL.clj", "KLM.clj", "Grail.clj"]

        for strategy_file in strategies_to_test:
            harness.reset_state()

            # Test with extreme high RSI
            harness.mock_market_data.set_rsi("SPY", 95)
            harness.mock_market_data.set_rsi("TQQQ", 95)
            harness.mock_market_data.set_rsi("QQQ", 95)

            result = harness.evaluate_strategy(strategy_file)

            if result.success and result.allocation_result:
                for symbol, weight in result.allocation_result.target_weights.items():
                    assert (
                        weight >= 0
                    ), f"{strategy_file} produced negative allocation: {symbol}={weight}"

    def test_defensive_vs_aggressive_allocations(self, repository_root: Path) -> None:
        """Test that strategies show defensive vs aggressive behavior."""
        harness = DslTestHarness(str(repository_root), seed=42)

        # Define defensive and aggressive symbols based on strategy patterns
        defensive_symbols = {"UVXY", "BIL", "BSV", "PSQ", "SQQQ"}
        aggressive_symbols = {"TECL", "TQQQ", "UPRO", "EXC", "NLR", "BWXT"}

        strategies_to_test = ["Nuclear.clj", "TECL.clj"]

        for strategy_file in strategies_to_test:
            # Test defensive conditions (high RSI)
            harness.reset_state()
            harness.mock_market_data.set_rsi("SPY", 90)
            harness.mock_market_data.set_rsi("TQQQ", 90)
            harness.mock_market_data.set_rsi("QQQ", 90)

            defensive_result = harness.evaluate_strategy(strategy_file)

            # Test aggressive conditions (low RSI)
            harness.reset_state()
            harness.mock_market_data.set_rsi("SPY", 20)
            harness.mock_market_data.set_rsi("TQQQ", 20)
            harness.mock_market_data.set_rsi("QQQ", 20)

            aggressive_result = harness.evaluate_strategy(strategy_file)

            if defensive_result.success and aggressive_result.success:
                if (
                    defensive_result.allocation_result
                    and aggressive_result.allocation_result
                ):
                    def_allocs = set(
                        defensive_result.allocation_result.target_weights.keys()
                    )
                    agg_allocs = set(
                        aggressive_result.allocation_result.target_weights.keys()
                    )

                    # Check if allocations change between defensive and aggressive conditions
                    assert (
                        def_allocs != agg_allocs
                        or defensive_result.allocation_result.target_weights
                        != aggressive_result.allocation_result.target_weights
                    ), f"{strategy_file} should show different behavior in defensive vs aggressive conditions"


@pytest.mark.strategy
class TestStrategyScenarioMatrix:
    """Test strategies under comprehensive market scenario matrix."""

    @pytest.mark.parametrize(
        "strategy_file", ["Nuclear.clj", "TECL.clj", "KLM.clj", "Grail.clj"]
    )
    @pytest.mark.parametrize(
        "scenario_type,rsi_range",
        [
            ("oversold", (15, 25)),  # Very low RSI - should trigger aggressive
            ("normal", (45, 55)),  # Normal RSI - balanced behavior
            ("overbought", (75, 85)),  # High RSI - should trigger defensive
        ],
    )
    def test_strategy_scenario_matrix(
        self,
        strategy_file: str,
        scenario_type: str,
        rsi_range: tuple[int, int],
        repository_root: Path,
    ) -> None:
        """Test each strategy under each market scenario produces valid outcomes."""
        harness = DslTestHarness(str(repository_root), seed=42)

        # Set RSI values in the specified range
        rsi_value = (rsi_range[0] + rsi_range[1]) / 2  # Use midpoint
        harness.mock_market_data.set_rsi("SPY", rsi_value)
        harness.mock_market_data.set_rsi("TQQQ", rsi_value)
        harness.mock_market_data.set_rsi("QQQ", rsi_value)

        # Evaluate strategy
        result = harness.evaluate_strategy(strategy_file)

        # Verify strategy responds to market conditions
        assert result.success, f"{strategy_file} failed under {scenario_type} scenario"
        assert (
            result.allocation_result is not None
        ), f"{strategy_file} should produce allocation under {scenario_type} scenario"

        # Verify allocation validity
        total_weight = sum(result.allocation_result.target_weights.values())
        assert (
            abs(float(total_weight) - 1.0) < 0.001
        ), f"{strategy_file} allocation weights should sum to 1.0 under {scenario_type}"

        # Store results for comparison across scenarios
        allocations = dict(result.allocation_result.target_weights)
        assert len(allocations) > 0, f"{strategy_file} should have non-empty allocation"

    def test_cross_scenario_allocation_differences(self, repository_root: Path) -> None:
        """Test that strategies produce different allocations across scenarios."""
        harness = DslTestHarness(str(repository_root), seed=42)

        strategies = ["Nuclear.clj", "TECL.clj"]
        scenarios = [("oversold", 20), ("normal", 50), ("overbought", 80)]

        for strategy_file in strategies:
            scenario_results = {}

            for scenario_name, rsi_value in scenarios:
                harness.reset_state()
                harness.mock_market_data.set_rsi("SPY", rsi_value)
                harness.mock_market_data.set_rsi("TQQQ", rsi_value)

                result = harness.evaluate_strategy(strategy_file)

                if result.success and result.allocation_result:
                    scenario_results[scenario_name] = (
                        result.allocation_result.target_weights
                    )

            # Verify we have results for all scenarios
            assert (
                len(scenario_results) == 3
            ), f"{strategy_file} should succeed in all scenarios"

            # Verify at least some scenarios produce different allocations
            allocations_list = list(scenario_results.values())
            all_same = all(
                allocations_list[0] == alloc for alloc in allocations_list[1:]
            )

            assert (
                not all_same
            ), f"{strategy_file} should produce different allocations across scenarios"
