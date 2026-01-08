"""Trace the filter decision at line 8-10 of ftl_starburst.

Business Unit: debugging | Status: development.
"""
import sys
sys.path.insert(0, "/Users/joshmoreton/GitHub/alchemiser-quant/layers/shared")

from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore


def main() -> None:
    """Trace the filter decision."""
    print("=" * 70)
    print("FILTER DECISION: moving-average-return {:window 10} select-bottom 1")
    print("=" * 70)
    print()
    print("The filter at line 8-10 compares TWO groups:")
    print("  1. WYLD Mean Reversion Combo (line 12)")
    print("  2. Walter's Champagne and CocaineStrategies (line 1499)")
    print()
    print("select-bottom 1 picks the group with LOWEST moving-average-return")
    print()
    print("NOTE: The DSL calculates moving-average-return on the GROUP portfolio,")
    print("not individual assets. This is a PORTFOLIO-level metric.")
    print()
    print("Since groups are complex nested structures, we need to understand")
    print("how our DSL evaluator calculates the portfolio's moving-average-return.")
    print()
    print("-" * 70)
    print("KEY INSIGHT:")
    print("-" * 70)
    print()
    print("Composer shows MULTIPLE assets with weights:")
    print("  SOXL 33.3%, TECL 44.5%, EDC 10.9%, COST 4%, GE 3%, LLY 2.4%, NVO 1.7%")
    print()
    print("Our system shows: TECL 100%")
    print()
    print("This means ONE of two things:")
    print("  1. Walter's group was selected (it has XLK vs KMLM → TECL)")
    print("  2. Our filter evaluator is working correctly, but Composer")
    print("     is doing something DIFFERENT with the portfolio structure.")
    print()
    print("-" * 70)
    print("THE REAL QUESTION:")
    print("-" * 70)
    print()
    print("If select-bottom 1 picks ONE group (Walter's), we get TECL.")
    print("But Composer shows SOXL, TECL, EDC, COST, GE, LLY, NVO...")
    print()
    print("SOXL is from the IEI vs IWM RSI check (IEI > IWM → EDC in mean reversion)")
    print("But we also checked XLK vs KMLM → TECL in Walter's group.")
    print()
    print("This suggests Composer might be COMBINING multiple groups,")
    print("not just selecting the bottom 1.")
    print()
    print("Let me check where SOXL appears in the strategy...")


if __name__ == "__main__":
    main()
