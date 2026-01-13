#!/usr/bin/env python3
"""Validation script for Calmar-tilted strategy weight calculations.

This script validates that the Calmar-tilt formula produces expected results
and that all components (weights normalization, partial adjustment, etc.) work correctly.
"""

import sys
from decimal import Decimal
from pathlib import Path

# Setup PYTHONPATH for shared layer imports
sys.path.insert(
    0,
    str(Path(__file__).parent.parent / "layers" / "shared"),
)

from the_alchemiser.shared.schemas.strategy_weights import CalmarMetrics
from the_alchemiser.shared.services.strategy_weight_service import StrategyWeightService


def test_calmar_tilt_calculation() -> None:
    """Test Calmar-tilt formula produces expected results."""
    print("\n🧪 Testing Calmar-tilt calculation...")

    # Mock repository (we won't actually save to DynamoDB)
    class MockRepo:
        def __init__(self):
            self.weights = None

        def get_current_weights(self):
            return self.weights

    repo = MockRepo()
    service = StrategyWeightService(repository=repo)

    # Test case: 3 strategies with different Calmar ratios
    base_weights = {
        "strategy_a": Decimal("0.333333"),
        "strategy_b": Decimal("0.333333"),
        "strategy_c": Decimal("0.333334"),
    }

    # Strategy A: High Calmar (1.5) - should get tilted UP
    # Strategy B: Medium Calmar (1.0) - should stay near base
    # Strategy C: Low Calmar (0.5) - should get tilted DOWN
    from datetime import UTC, datetime

    now = datetime.now(UTC)
    calmar_metrics = {
        "strategy_a": CalmarMetrics(
            strategy_name="strategy_a",
            twelve_month_return=Decimal("0.15"),
            twelve_month_max_drawdown=Decimal("0.10"),
            calmar_ratio=Decimal("1.5"),
            months_of_data=12,
            as_of=now,
        ),
        "strategy_b": CalmarMetrics(
            strategy_name="strategy_b",
            twelve_month_return=Decimal("0.10"),
            twelve_month_max_drawdown=Decimal("0.10"),
            calmar_ratio=Decimal("1.0"),
            months_of_data=12,
            as_of=now,
        ),
        "strategy_c": CalmarMetrics(
            strategy_name="strategy_c",
            twelve_month_return=Decimal("0.05"),
            twelve_month_max_drawdown=Decimal("0.10"),
            calmar_ratio=Decimal("0.5"),
            months_of_data=12,
            as_of=now,
        ),
    }

    # Compute target weights
    target_weights = service._compute_target_weights(base_weights, calmar_metrics)

    print(f"Base weights: {base_weights}")
    print(f"Calmar ratios: {[float(m.calmar_ratio) for m in calmar_metrics.values()]}")
    print(f"Target weights: {target_weights}")

    # Validate results
    # Median Calmar = 1.0
    # Strategy A: tilt = (1.5/1.0)^0.5 = 1.225, clamped to [0.5, 2.0] = 1.225
    # Strategy B: tilt = (1.0/1.0)^0.5 = 1.0
    # Strategy C: tilt = (0.5/1.0)^0.5 = 0.707, clamped to [0.5, 2.0] = 0.707

    # After normalization:
    # Total = 0.333*1.225 + 0.333*1.0 + 0.333*0.707 = 0.408 + 0.333 + 0.235 = 0.976
    # A: 0.408/0.976 ≈ 0.418
    # B: 0.333/0.976 ≈ 0.341
    # C: 0.235/0.976 ≈ 0.241

    assert target_weights["strategy_a"] > base_weights["strategy_a"], (
        f"High Calmar strategy should have higher weight than base"
    )
    assert target_weights["strategy_c"] < base_weights["strategy_c"], (
        f"Low Calmar strategy should have lower weight than base"
    )

    # Check sum is 1.0 (within tolerance)
    total = sum(target_weights.values())
    assert abs(float(total) - 1.0) < 0.01, f"Target weights should sum to 1.0, got {total}"

    print(f"✅ Strategy A (high Calmar) weight increased from {float(base_weights['strategy_a']):.4f} to {float(target_weights['strategy_a']):.4f}")
    print(f"✅ Strategy C (low Calmar) weight decreased from {float(base_weights['strategy_c']):.4f} to {float(target_weights['strategy_c']):.4f}")
    print(f"✅ Total weight: {float(total):.4f} (expected 1.0)")


def test_partial_adjustment() -> None:
    """Test partial adjustment smoothing."""
    print("\n🧪 Testing partial adjustment...")

    class MockRepo:
        def __init__(self):
            self.weights = None

        def get_current_weights(self):
            return self.weights

    repo = MockRepo()
    service = StrategyWeightService(repository=repo)

    current_realized = {
        "strategy_a": Decimal("0.30"),
        "strategy_b": Decimal("0.40"),
        "strategy_c": Decimal("0.30"),
    }

    target = {
        "strategy_a": Decimal("0.50"),  # Should move up
        "strategy_b": Decimal("0.30"),  # Should move down
        "strategy_c": Decimal("0.20"),  # Should move down
    }

    lambda_value = Decimal("0.1")

    # Apply partial adjustment
    realized = service._apply_partial_adjustment(current_realized, target, lambda_value)

    print(f"Current: {current_realized}")
    print(f"Target: {target}")
    print(f"Lambda: {float(lambda_value)}")
    print(f"Realized: {realized}")

    # Expected:
    # A: 0.30 + 0.1 * (0.50 - 0.30) = 0.30 + 0.02 = 0.32
    # B: 0.40 + 0.1 * (0.30 - 0.40) = 0.40 - 0.01 = 0.39
    # C: 0.30 + 0.1 * (0.20 - 0.30) = 0.30 - 0.01 = 0.29
    # After normalization to sum=1.0

    # Validate direction of movement
    assert realized["strategy_a"] > current_realized["strategy_a"], (
        f"Strategy A should move toward target (up)"
    )
    assert realized["strategy_b"] < current_realized["strategy_b"], (
        f"Strategy B should move toward target (down)"
    )
    assert realized["strategy_c"] < current_realized["strategy_c"], (
        f"Strategy C should move toward target (down)"
    )

    # Validate realized is closer to target than current
    distance_before = abs(float(current_realized["strategy_a"] - target["strategy_a"]))
    distance_after = abs(float(realized["strategy_a"] - target["strategy_a"]))
    assert distance_after < distance_before, (
        f"Realized weight should be closer to target than current"
    )

    # Check sum is 1.0 (within tolerance)
    total = sum(realized.values())
    assert abs(float(total) - 1.0) < 0.01, f"Realized weights should sum to 1.0, got {total}"

    print(f"✅ Strategy A moved from {float(current_realized['strategy_a']):.4f} toward {float(target['strategy_a']):.4f} to {float(realized['strategy_a']):.4f}")
    print(f"✅ Total weight: {float(total):.4f} (expected 1.0)")


def test_caps_and_floors() -> None:
    """Test that tilt factors are capped at [0.5, 2.0]."""
    print("\n🧪 Testing caps and floors...")

    class MockRepo:
        def __init__(self):
            self.weights = None

        def get_current_weights(self):
            return self.weights

    repo = MockRepo()
    service = StrategyWeightService(repository=repo)

    from datetime import UTC, datetime

    now = datetime.now(UTC)

    # Test extreme Calmar ratios
    base_weights = {
        "strategy_extreme_high": Decimal("0.5"),
        "strategy_extreme_low": Decimal("0.5"),
    }

    calmar_metrics = {
        "strategy_extreme_high": CalmarMetrics(
            strategy_name="strategy_extreme_high",
            twelve_month_return=Decimal("1.0"),  # 100% return
            twelve_month_max_drawdown=Decimal("0.1"),  # 10% drawdown
            calmar_ratio=Decimal("10.0"),  # Very high Calmar
            months_of_data=12,
            as_of=now,
        ),
        "strategy_extreme_low": CalmarMetrics(
            strategy_name="strategy_extreme_low",
            twelve_month_return=Decimal("0.01"),  # 1% return
            twelve_month_max_drawdown=Decimal("0.2"),  # 20% drawdown
            calmar_ratio=Decimal("0.05"),  # Very low Calmar
            months_of_data=12,
            as_of=now,
        ),
    }

    target_weights = service._compute_target_weights(base_weights, calmar_metrics)

    print(f"Base weights: {base_weights}")
    print(f"Calmar ratios: {[float(m.calmar_ratio) for m in calmar_metrics.values()]}")
    print(f"Target weights: {target_weights}")

    # With extreme Calmar ratios, tilt should be capped
    # Max tilt of 2.0 means max weight = 0.5 * 2.0 / (normalized sum)
    # Min tilt of 0.5 means min weight = 0.5 * 0.5 / (normalized sum)

    # After normalization with tilt [2.0, 0.5]:
    # high: 0.5 * 2.0 = 1.0
    # low: 0.5 * 0.5 = 0.25
    # Total = 1.25
    # Normalized: high = 1.0/1.25 = 0.8, low = 0.25/1.25 = 0.2

    assert target_weights["strategy_extreme_high"] <= Decimal("0.81"), (
        f"High Calmar strategy should be capped"
    )
    assert target_weights["strategy_extreme_low"] >= Decimal("0.19"), (
        f"Low Calmar strategy should have floor"
    )

    print(f"✅ Extreme high Calmar capped at {float(target_weights['strategy_extreme_high']):.4f} (max theoretical: 0.80)")
    print(f"✅ Extreme low Calmar floored at {float(target_weights['strategy_extreme_low']):.4f} (min theoretical: 0.20)")


def main() -> None:
    """Run all validation tests."""
    print("=" * 70)
    print("🔬 Calmar-Tilted Strategy Weight Validation")
    print("=" * 70)

    try:
        test_calmar_tilt_calculation()
        test_partial_adjustment()
        test_caps_and_floors()

        print("\n" + "=" * 70)
        print("✅ All validation tests passed!")
        print("=" * 70)

    except AssertionError as e:
        print(f"\n❌ Validation failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
