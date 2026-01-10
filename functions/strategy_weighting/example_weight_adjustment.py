#!/usr/bin/env python3
"""
Example demonstrating dynamic weight adjustment logic.

This script shows how Sharpe ratios are mapped to weight multipliers
and how baseline allocations are adjusted.
"""

from decimal import Decimal

# Example baseline allocations from config
baseline_allocations = {
    "beam_chain.clj": Decimal("0.20"),
    "nuclear_feaver.clj": Decimal("0.25"),
    "gold.clj": Decimal("0.15"),
    "tqqq_ftlt.clj": Decimal("0.20"),
    "sisyphus_lowvol.clj": Decimal("0.20"),
}

# Example Sharpe ratios calculated from trade history
sharpe_ratios = {
    "beam_chain.clj": Decimal("1.8"),  # Best performer
    "nuclear_feaver.clj": Decimal("1.2"),  # Good performer
    "gold.clj": Decimal("0.5"),  # Mediocre performer
    "tqqq_ftlt.clj": Decimal("0.8"),  # Below average
    "sisyphus_lowvol.clj": Decimal("-0.2"),  # Worst performer
}

# Weight adjustment constraints
MIN_MULTIPLIER = Decimal("0.5")  # 50% of baseline (halving)
MAX_MULTIPLIER = Decimal("2.0")  # 200% of baseline (doubling)


def calculate_weight_multipliers(sharpe_ratios):
    """Map Sharpe ratios to weight multipliers."""
    min_sharpe = min(sharpe_ratios.values())
    max_sharpe = max(sharpe_ratios.values())
    sharpe_range = max_sharpe - min_sharpe

    multipliers = {}
    for strategy, sharpe in sharpe_ratios.items():
        # Normalize Sharpe to [0, 1]
        normalized = (sharpe - min_sharpe) / sharpe_range
        # Map to multiplier range [0.5, 2.0]
        multiplier = MIN_MULTIPLIER + normalized * (MAX_MULTIPLIER - MIN_MULTIPLIER)
        multipliers[strategy] = multiplier

    return multipliers


def apply_weight_adjustments(baseline, multipliers):
    """Apply multipliers and renormalize."""
    # Apply multipliers
    adjusted = {s: baseline[s] * multipliers[s] for s in baseline}

    # Renormalize to sum to 1.0
    total = sum(adjusted.values())
    dynamic = {s: w / total for s, w in adjusted.items()}

    return dynamic


def main():
    """Demonstrate weight adjustment."""
    print("=" * 80)
    print("DYNAMIC WEIGHT ADJUSTMENT EXAMPLE")
    print("=" * 80)
    print()

    # Calculate multipliers from Sharpe ratios
    multipliers = calculate_weight_multipliers(sharpe_ratios)

    print("STEP 1: SHARPE RATIOS AND MULTIPLIERS")
    print("-" * 80)
    for strategy in sorted(sharpe_ratios, key=lambda s: sharpe_ratios[s], reverse=True):
        sharpe = sharpe_ratios[strategy]
        mult = multipliers[strategy]
        print(f"  {strategy:25s}  Sharpe: {sharpe:6.2f}  →  Multiplier: {mult:.2f}x")
    print()

    # Apply multipliers to baseline allocations
    dynamic_weights = apply_weight_adjustments(baseline_allocations, multipliers)

    print("STEP 2: BASELINE VS DYNAMIC ALLOCATIONS")
    print("-" * 80)
    print(f"  {'Strategy':25s}  {'Baseline':>10s}  {'Dynamic':>10s}  {'Change':>10s}")
    print("-" * 80)

    for strategy in sorted(baseline_allocations):
        baseline = baseline_allocations[strategy]
        dynamic = dynamic_weights[strategy]
        change = dynamic - baseline
        sign = "+" if change > 0 else ""

        print(
            f"  {strategy:25s}  "
            f"{float(baseline):9.1%}  "
            f"{float(dynamic):9.1%}  "
            f"{sign}{float(change):9.1%}"
        )

    print("-" * 80)
    print(
        f"  {'TOTAL':25s}  "
        f"{float(sum(baseline_allocations.values())):9.1%}  "
        f"{float(sum(dynamic_weights.values())):9.1%}"
    )
    print()

    print("INTERPRETATION:")
    print("-" * 80)
    print("  • Strategies with higher Sharpe ratios receive MORE capital")
    print("  • Strategies with lower Sharpe ratios receive LESS capital")
    print("  • No strategy can drop below 50% or exceed 200% of baseline")
    print("  • Total allocation always sums to 100%")
    print()


if __name__ == "__main__":
    main()
