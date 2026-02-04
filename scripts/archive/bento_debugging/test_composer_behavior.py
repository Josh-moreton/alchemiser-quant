#!/usr/bin/env python3
"""Test Composer-style atomic group behavior in weight operators.

This verifies that weight operators treat PortfolioFragments as atomic units
(like Composer.trade) rather than extracting and re-weighting individual symbols.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "functions", "strategy_worker"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "layers", "shared"))

from decimal import Decimal
from engines.dsl.operators.portfolio import (
    _flatten_to_weight_dicts,
    _normalize_fragment_weights,
)
from the_alchemiser.shared.schemas.indicator_request import PortfolioFragment


def test_flatten_treats_fragments_as_atomic():
    """Test that _flatten_to_weight_dicts treats each PortfolioFragment as 1 child."""
    print("=" * 60)
    print("Test 1: _flatten_to_weight_dicts treats PortfolioFragments as atomic")
    print("=" * 60)
    
    # Two PortfolioFragments should count as 2 children, not extract symbols
    frag1 = PortfolioFragment(
        fragment_id="1",
        source_step="test",
        weights={"A": Decimal("0.6"), "B": Decimal("0.4")}
    )
    frag2 = PortfolioFragment(
        fragment_id="2",
        source_step="test",
        weights={"C": Decimal("0.5"), "D": Decimal("0.5")}
    )

    result = _flatten_to_weight_dicts([frag1, frag2])
    
    print(f"  Number of children: {len(result)} (expected: 2)")
    assert len(result) == 2, f"Expected 2 children, got {len(result)}"
    
    print(f"  Child 1: {result[0]}")
    print(f"  Child 2: {result[1]}")
    
    # Verify internal weights are preserved
    assert result[0] == {"A": Decimal("0.6"), "B": Decimal("0.4")}
    assert result[1] == {"C": Decimal("0.5"), "D": Decimal("0.5")}
    
    print("  PASSED!")


def test_flatten_mixed_list():
    """Test mixed list with PortfolioFragment and bare symbol."""
    print()
    print("=" * 60)
    print("Test 2: Mixed list (PortfolioFragment + bare symbol)")
    print("=" * 60)
    
    frag = PortfolioFragment(
        fragment_id="3",
        source_step="test",
        weights={"X": Decimal("0.7"), "Y": Decimal("0.3")}
    )
    
    result = _flatten_to_weight_dicts([frag, "Z"])
    
    print(f"  Number of children: {len(result)} (expected: 2)")
    assert len(result) == 2, f"Expected 2 children, got {len(result)}"
    
    print(f"  Child 1: {result[0]}")
    print(f"  Child 2: {result[1]}")
    
    assert result[0] == {"X": Decimal("0.7"), "Y": Decimal("0.3")}
    assert result[1] == {"Z": Decimal("1.0")}
    
    print("  PASSED!")


def test_flatten_nested_list():
    """Test nested list [[PortfolioFragment]]."""
    print()
    print("=" * 60)
    print("Test 3: Nested [[PortfolioFragment]]")
    print("=" * 60)
    
    frag = PortfolioFragment(
        fragment_id="4",
        source_step="test",
        weights={"P": Decimal("1.0")}
    )
    
    result = _flatten_to_weight_dicts([[frag]])
    
    print(f"  Number of children: {len(result)} (expected: 1)")
    assert len(result) == 1, f"Expected 1 child, got {len(result)}"
    
    print(f"  Child 1: {result[0]}")
    assert result[0] == {"P": Decimal("1.0")}
    
    print("  PASSED!")


def test_normalize_fragment_weights_grouped():
    """Test _normalize_fragment_weights treats groups as atomic units."""
    print()
    print("=" * 60)
    print("Test 4: _normalize_fragment_weights with grouped mode")
    print("=" * 60)
    
    # Two groups in a list - each should get 50%
    frag1 = PortfolioFragment(
        fragment_id="1",
        source_step="test",
        weights={"A": Decimal("1.0")}  # 100% A
    )
    frag2 = PortfolioFragment(
        fragment_id="2",
        source_step="test",
        weights={"B": Decimal("0.6"), "C": Decimal("0.4")}  # 60% B, 40% C
    )
    
    # Mock context (not used for non-list values)
    class MockContext:
        pass
    
    result = _normalize_fragment_weights([frag1, frag2], MockContext())
    
    print(f"  Result: {result}")
    
    # Expected: Each group gets 50%
    # Group1 (A=100%) * 50% = A=50%
    # Group2 (B=60%, C=40%) * 50% = B=30%, C=20%
    expected = {
        "A": Decimal("0.5"),
        "B": Decimal("0.3"),
        "C": Decimal("0.2"),
    }
    
    print(f"  Expected: {expected}")
    
    for sym in expected:
        assert abs(result.get(sym, Decimal("0")) - expected[sym]) < Decimal("0.001"), \
            f"Mismatch for {sym}: got {result.get(sym)}, expected {expected[sym]}"
    
    print("  PASSED!")


def test_weight_equal_scenario():
    """Simulate the weight-equal scenario from Composer discussion."""
    print()
    print("=" * 60)
    print("Test 5: weight-equal with filter output (Composer scenario)")
    print("=" * 60)
    
    # Scenario: (weight-inverse-volatility 90 (filter ... (select-top 3) [assets]))
    # Filter returns equal-weighted 3 assets as a PortfolioFragment
    # Parent weight function should receive this as 1 group
    
    filter_result = PortfolioFragment(
        fragment_id="filter-output",
        source_step="filter",
        weights={
            "SMR": Decimal("0.333333"),
            "BWXT": Decimal("0.333333"),
            "LEU": Decimal("0.333334"),
        }
    )
    
    # If wrapped in weight-equal with another group:
    # (weight-equal [(filter-result) (asset "BIL")])
    other_asset = "BIL"
    
    result = _flatten_to_weight_dicts([filter_result, other_asset])
    
    print(f"  Number of children: {len(result)} (expected: 2)")
    assert len(result) == 2, f"Expected 2 children, got {len(result)}"
    
    print(f"  Child 1 (filter result): {result[0]}")
    print(f"  Child 2 (BIL): {result[1]}")
    
    # Filter result is 1 group with 3 assets
    assert len(result[0]) == 3
    # BIL is 1 group with 1 asset
    assert len(result[1]) == 1
    
    print("  PASSED!")
    print()
    print("COMPOSER BEHAVIOR: The filter's 3 assets are treated as 1 child,")
    print("not extracted as 3 separate children. This matches Composer.trade!")


if __name__ == "__main__":
    test_flatten_treats_fragments_as_atomic()
    test_flatten_mixed_list()
    test_flatten_nested_list()
    test_normalize_fragment_weights_grouped()
    test_weight_equal_scenario()
    
    print()
    print("=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)
