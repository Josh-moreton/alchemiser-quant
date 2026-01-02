#!/usr/bin/env python3
"""Minimal reproducer for weight-equal accumulation issue.

This tests the hypothesis that nested weight-equal operators
incorrectly accumulate weights instead of distributing them.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "functions", "strategy_worker"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "layers", "shared"))

from dotenv import load_dotenv
load_dotenv()

from decimal import Decimal
from engines.dsl.operators.portfolio import weight_equal, collect_weights_from_value
from the_alchemiser.shared.schemas.indicator_request import PortfolioFragment


def test_nested_weight_equal():
    """Test how nested weight-equal behaves."""
    
    # Simulate: (weight-equal [(weight-equal [A, B]) (weight-equal [A, C])])
    # Expected: A=50% (25% + 25%), B=25%, C=25%
    # 
    # If inner weight-equal [A, B] → {A: 50%, B: 50%}
    # And inner weight-equal [A, C] → {A: 50%, C: 50%}
    # Then outer should give each inner 50%:
    #   From first: A=25%, B=25%
    #   From second: A=25%, C=25%
    #   Total: A=50%, B=25%, C=25%
    
    inner1 = PortfolioFragment(
        fragment_id="1",
        source_step="test",
        weights={"A": Decimal("0.5"), "B": Decimal("0.5")}
    )
    
    inner2 = PortfolioFragment(
        fragment_id="2", 
        source_step="test",
        weights={"A": Decimal("0.5"), "C": Decimal("0.5")}
    )
    
    # Simulate what weight_equal would do with these
    all_weights = {}
    for frag in [inner1, inner2]:
        frag_weights = collect_weights_from_value(frag)
        for sym, w in frag_weights.items():
            all_weights[sym] = all_weights.get(sym, Decimal("0")) + w
    
    print("Raw accumulated weights:")
    for sym, w in sorted(all_weights.items()):
        print(f"  {sym}: {w}")
    
    total = sum(all_weights.values())
    print(f"\nTotal before normalization: {total}")
    
    normalized = {sym: w / total for sym, w in all_weights.items()}
    print("\nNormalized weights:")
    for sym, w in sorted(normalized.items()):
        print(f"  {sym}: {float(w)*100:.1f}%")
    
    print("\n" + "=" * 60)
    print("ANALYSIS:")
    print("=" * 60)
    print("Inner1 has A=50%, B=50%")
    print("Inner2 has A=50%, C=50%")
    print("\nActual result: A=50%, B=25%, C=25%")
    print("This IS correct! Each inner contributes equally.")
    print("\nBut the problem is when:")
    print("  - Inner1 = {BIL: 100%}")
    print("  - Inner2 = {BIL: 100%}")
    print("  - Inner3 = {DRV: 100%}")
    print("Accumulation: BIL=2, DRV=1 → BIL=66%, DRV=33%")
    print("When it should be: BIL=33%, BIL=33%, DRV=33% = BIL=66%, DRV=33%")
    print("\nWait... that's actually the same! The algorithm is correct.")
    print("\nThe real issue must be something else...")


def test_many_bil_branches():
    """Test what happens when many branches return BIL."""
    print("\n" + "=" * 60)
    print("Testing many BIL branches")
    print("=" * 60)
    
    # Simulate bento_collection scenario:
    # Many branches return {BIL: 100%}, few return {DRV: 100%} or {LABU: 100%}
    fragments = []
    
    # 88 branches return BIL
    for i in range(88):
        fragments.append(PortfolioFragment(
            fragment_id=str(i),
            source_step="test",
            weights={"BIL": Decimal("1.0")}
        ))
    
    # 11 branches return DRV
    for i in range(11):
        fragments.append(PortfolioFragment(
            fragment_id=f"drv_{i}",
            source_step="test", 
            weights={"DRV": Decimal("1.0")}
        ))
    
    # 15 branches return LABU
    for i in range(15):
        fragments.append(PortfolioFragment(
            fragment_id=f"labu_{i}",
            source_step="test",
            weights={"LABU": Decimal("1.0")}
        ))
    
    all_weights = {}
    for frag in fragments:
        frag_weights = collect_weights_from_value(frag)
        for sym, w in frag_weights.items():
            all_weights[sym] = all_weights.get(sym, Decimal("0")) + w
    
    total = sum(all_weights.values())
    normalized = {sym: w / total for sym, w in all_weights.items()}
    
    print(f"\nIf {len(fragments)} independent branches all get combined:")
    for sym, w in sorted(normalized.items(), key=lambda x: -x[1]):
        print(f"  {sym}: {float(w)*100:.2f}%")
    
    print("\nThis matches the bento_collection output!")
    print("BIL: 88/114 = 77%")
    print("But we got 98.88%... so there's more BIL accumulation happening.")
    

def test_deep_nesting():
    """Test what happens with deep nesting."""
    print("\n" + "=" * 60)
    print("Testing deep nesting effect")
    print("=" * 60)
    
    # Consider this structure:
    # (weight-equal
    #   [(weight-equal [BIL])     ; Level 1: BIL=100%
    #    (weight-equal             
    #      [(weight-equal [BIL])  ; Level 2: BIL=100%
    #       (weight-equal [DRV])] ; Level 2: DRV=100%
    #    )])
    #
    # At Level 2: BIL=50%, DRV=50% (equal weight)
    # At Level 1: We have two children:
    #   - Child 1: BIL=100% 
    #   - Child 2: BIL=50%, DRV=50%
    # Accumulation: BIL=1.0+0.5=1.5, DRV=0.5
    # Normalized: BIL=75%, DRV=25%
    #
    # BUT in Composer, each CHILD of weight-equal should get EQUAL weight.
    # So it should be:
    #   - Child 1 gets 50% → BIL=50%
    #   - Child 2 gets 50% → BIL=25%, DRV=25%
    #   - Result: BIL=75%, DRV=25% (same!)
    #
    # The issue is when we have MANY children at the same level,
    # each with BIL, vs few with DRV.
    
    # Simulate 3 levels with uneven distribution
    # Level 3: 10 x BIL, 1 x DRV  (each returns 100%)
    level3_weights = {}
    for _ in range(10):
        level3_weights["BIL"] = level3_weights.get("BIL", Decimal("0")) + Decimal("1.0")
    level3_weights["DRV"] = Decimal("1.0")
    
    # Normalize level 3
    total3 = sum(level3_weights.values())
    level3_normalized = {k: v/total3 for k, v in level3_weights.items()}
    print(f"Level 3 (10 BIL + 1 DRV): BIL={float(level3_normalized['BIL'])*100:.1f}%, DRV={float(level3_normalized['DRV'])*100:.1f}%")
    
    # Level 2: Another weight-equal with BIL + level3 result
    level2_weights = {}
    level2_weights["BIL"] = Decimal("1.0")  # Direct BIL child
    for k, v in level3_normalized.items():
        level2_weights[k] = level2_weights.get(k, Decimal("0")) + v
    
    total2 = sum(level2_weights.values())
    level2_normalized = {k: v/total2 for k, v in level2_weights.items()}
    print(f"Level 2 (BIL + level3): BIL={float(level2_normalized['BIL'])*100:.1f}%, DRV={float(level2_normalized['DRV'])*100:.1f}%")
    
    # Level 1: Another weight-equal with BIL + level2 result
    level1_weights = {}
    level1_weights["BIL"] = Decimal("1.0")  # Direct BIL child
    for k, v in level2_normalized.items():
        level1_weights[k] = level1_weights.get(k, Decimal("0")) + v
    
    total1 = sum(level1_weights.values())
    level1_normalized = {k: v/total1 for k, v in level1_weights.items()}
    print(f"Level 1 (BIL + level2): BIL={float(level1_normalized['BIL'])*100:.1f}%, DRV={float(level1_normalized['DRV'])*100:.1f}%")
    
    print("\nAs you can see, BIL keeps gaining weight at each level!")
    print("This is because weight-equal adds weights then normalizes.")
    print("\nThe 'correct' behavior would be to give each CHILD equal weight,")
    print("scaling down the child's internal weights proportionally.")


if __name__ == "__main__":
    test_nested_weight_equal()
    test_many_bil_branches()
    test_deep_nesting()
