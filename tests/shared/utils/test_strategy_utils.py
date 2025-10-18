#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Comprehensive tests for strategy_utils module.

Tests cover:
- Type correctness (returns dict[StrategyType, float])
- Numerical integrity (allocations sum to 1.0)
- Immutability and idempotency
- Contract validation
"""

from __future__ import annotations

import math

import pytest

from the_alchemiser.shared.types.strategy_types import StrategyType
from the_alchemiser.shared.utils.strategy_utils import get_strategy_allocations


class TestGetStrategyAllocations:
    """Test suite for get_strategy_allocations function."""

    @pytest.mark.unit
    def test_returns_dict_with_strategy_type_keys(self) -> None:
        """Verify function returns dict with StrategyType enum keys."""
        allocations = get_strategy_allocations()

        assert isinstance(allocations, dict), "Should return a dictionary"
        assert len(allocations) > 0, "Should return non-empty dictionary"

        # All keys must be StrategyType enum values
        for key in allocations:
            assert isinstance(key, StrategyType), f"Key {key} must be StrategyType enum"

    @pytest.mark.unit
    def test_returns_float_values(self) -> None:
        """Verify all allocation values are floats."""
        allocations = get_strategy_allocations()

        for strategy, allocation in allocations.items():
            assert isinstance(allocation, float), (
                f"Allocation for {strategy} must be float, got {type(allocation)}"
            )

    @pytest.mark.unit
    def test_allocations_sum_to_one(self) -> None:
        """Verify allocations sum to 1.0 within tolerance.

        Critical for portfolio allocation - must sum to 100% of capital.
        Uses math.isclose for float comparison per coding guidelines.
        """
        allocations = get_strategy_allocations()
        total = sum(allocations.values())

        assert math.isclose(total, 1.0, abs_tol=1e-9), f"Allocations must sum to 1.0, got {total}"

    @pytest.mark.unit
    def test_all_allocations_non_negative(self) -> None:
        """Verify all allocations are non-negative.

        Negative allocations would be invalid for position sizing.
        """
        allocations = get_strategy_allocations()

        for strategy, allocation in allocations.items():
            assert allocation >= 0.0, (
                f"Allocation for {strategy} must be non-negative, got {allocation}"
            )

    @pytest.mark.unit
    def test_all_allocations_at_most_one(self) -> None:
        """Verify no single allocation exceeds 1.0.

        Single strategy cannot use more than 100% of capital.
        """
        allocations = get_strategy_allocations()

        for strategy, allocation in allocations.items():
            assert allocation <= 1.0, f"Allocation for {strategy} must be <= 1.0, got {allocation}"

    @pytest.mark.unit
    def test_idempotency(self) -> None:
        """Verify function returns same result on repeated calls.

        Deterministic behavior required for trading system stability.
        """
        first_call = get_strategy_allocations()
        second_call = get_strategy_allocations()

        assert first_call == second_call, "Function must be idempotent"
        # Verify it's not the same object reference (immutability)
        assert first_call is not second_call, "Should return new dict on each call"

    @pytest.mark.unit
    def test_current_implementation_returns_dsl_only(self) -> None:
        """Test current DSL-focused implementation.

        This test documents the current behavior during DSL migration phase.
        Should be updated when other strategies are enabled.
        """
        allocations = get_strategy_allocations()

        # Current implementation only returns DSL
        assert StrategyType.DSL in allocations, "DSL strategy must be present"
        assert allocations[StrategyType.DSL] == 1.0, "DSL should have 100% allocation"
        assert len(allocations) == 1, "Current implementation only returns DSL"

    @pytest.mark.unit
    def test_no_invalid_strategy_types(self) -> None:
        """Verify only valid StrategyType enum values are returned."""
        allocations = get_strategy_allocations()
        valid_strategies = {
            StrategyType.NUCLEAR,
            StrategyType.TECL,
            StrategyType.KLM,
            StrategyType.DSL,
        }

        for strategy in allocations:
            assert strategy in valid_strategies, f"Strategy {strategy} is not a valid StrategyType"

    @pytest.mark.unit
    def test_docstring_example_consistency(self) -> None:
        """Verify docstring example matches actual behavior."""
        allocations = get_strategy_allocations()

        # Docstring claims: allocations[StrategyType.DSL] -> 1.0
        assert StrategyType.DSL in allocations, "Docstring example references DSL - must exist"
        assert allocations[StrategyType.DSL] == 1.0, (
            "Docstring example shows DSL=1.0, must match implementation"
        )

    @pytest.mark.unit
    def test_return_type_annotation_correctness(self) -> None:
        """Verify return type matches annotation dict[StrategyType, float]."""
        allocations = get_strategy_allocations()

        # Type annotation claims dict[StrategyType, float]
        assert isinstance(allocations, dict)

        for key, value in allocations.items():
            assert isinstance(key, StrategyType), f"Key {key} must be StrategyType"
            assert isinstance(value, float), f"Value {value} must be float"
