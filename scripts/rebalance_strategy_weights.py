#!/usr/bin/env python3
"""Business Unit: scripts | Status: current.

Monthly Strategy Weight Rebalancer.

Reads the latest CSV export from strategy_results/, extracts Calmar ratios,
and recalculates strategy weights using the Calmar-tilt formula:

    w_i = Normalise(w_base × clip((Calmar_i / MedianCalmar)^α, f_min, f_max))

Where:
    - w_base = 1/N (equal weight baseline)
    - α = 0.5 (square-root dampening)
    - f_min = 0.5 (no strategy below 50% of base weight)
    - f_max = 2.0 (no strategy above 2× base weight)
    - MedianCalmar = median Calmar across all strategies

Usage:
    python scripts/rebalance_strategy_weights.py
    python scripts/rebalance_strategy_weights.py --dry-run
    python scripts/rebalance_strategy_weights.py --csv strategy_results/2026-01-13T09-13_export.csv

Reference: GitHub Issue #2975
"""

from __future__ import annotations

import argparse
import json
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from statistics import median

import pandas as pd

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
STRATEGY_RESULTS_DIR = PROJECT_ROOT / "strategy_results"
CONFIG_DIR = (
    PROJECT_ROOT
    / "layers"
    / "shared"
    / "the_alchemiser"
    / "shared"
    / "config"
)
STRATEGY_PROD_JSON = CONFIG_DIR / "strategy.prod.json"

# Calmar-tilt parameters (from issue #2975)
ALPHA = Decimal("0.5")  # Square-root dampening
F_MIN = Decimal("0.5")  # Floor: 50% of base weight
F_MAX = Decimal("2.0")  # Cap: 2× base weight

# CSV strategy name prefix -> filename mapping
CSV_TO_FILENAME: dict[str, str] = {
    "Flextiger-DefAI+eVTO": "defence.clj",
    "Golden Rotation 2x": "gold.clj",
    "Nuclear Energy with": "nuclear.clj",
    "Pals Minor Spell of": "pals_spell.clj",
    "Rain's Concise EM Le": "rains_concise_em.clj",
    "Rain's Unified EM Le": "rains_em_dancer.clj",
    "Simons KMLM FULL BUI": "simons_full_kmlm.clj",
    "(A) Sisyphus V0.1": "sisyphus_lowvol.clj",
    "BT 1Nov16-22Nov22 AR": "tqqq_ftlt_1.clj",
    "2017 BT TQQQ For The": "tqqq_ftlt_2.clj",
    "TQQQ For The Long Te": "tqqq_ftlt.clj",
    "Blatant Tech Rulersh": "blatant_tech.clj",
}


def find_latest_csv(results_dir: Path) -> Path:
    """Find the most recent CSV file in the strategy_results directory."""
    csv_files = list(results_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {results_dir}")
    # Sort by filename (timestamp format ensures chronological order)
    return sorted(csv_files, key=lambda p: p.name)[-1]


def match_csv_name_to_filename(csv_name: str) -> str | None:
    """Match a CSV strategy name to its corresponding .clj filename."""
    for prefix, filename in CSV_TO_FILENAME.items():
        if csv_name.startswith(prefix):
            return filename
    return None


def load_calmar_ratios(csv_path: Path) -> dict[str, Decimal]:
    """Load Calmar ratios from CSV and map to filenames.

    Returns:
        Dict mapping filename -> Calmar ratio (using absolute value for negatives)
    """
    df = pd.read_csv(csv_path, index_col=0)

    calmar_by_filename: dict[str, Decimal] = {}
    unmatched: list[str] = []

    for csv_name in df.index:
        # Skip the "Mean" row
        if csv_name == "Mean":
            continue

        filename = match_csv_name_to_filename(csv_name)
        if filename is None:
            unmatched.append(csv_name)
            continue

        calmar_value = df.loc[csv_name, "Calmar Ratio"]
        # Use absolute value for negative Calmar ratios
        calmar_by_filename[filename] = Decimal(str(abs(calmar_value)))

    if unmatched:
        print(f"Warning: Could not match CSV names: {unmatched}")

    return calmar_by_filename


def calculate_calmar_tilt_weights(
    calmar_ratios: dict[str, Decimal],
    alpha: Decimal = ALPHA,
    f_min: Decimal = F_MIN,
    f_max: Decimal = F_MAX,
) -> dict[str, Decimal]:
    """Calculate Calmar-tilted weights using the formula from issue #2975.

    Formula:
        w_i = Normalise(w_base × clip((Calmar_i / MedianCalmar)^α, f_min, f_max))

    Args:
        calmar_ratios: Dict of filename -> Calmar ratio
        alpha: Dampening exponent (default 0.5 = square root)
        f_min: Minimum multiplier (default 0.5)
        f_max: Maximum multiplier (default 2.0)

    Returns:
        Dict of filename -> normalized weight
    """
    n = len(calmar_ratios)
    if n == 0:
        raise ValueError("No Calmar ratios provided")

    # Base weight = 1/N
    w_base = Decimal("1") / Decimal(str(n))

    # Calculate median Calmar
    calmar_values = list(calmar_ratios.values())
    median_calmar = Decimal(str(median([float(c) for c in calmar_values])))

    if median_calmar == 0:
        raise ValueError("Median Calmar ratio is zero, cannot compute weights")

    print(f"\nCalmar-Tilt Calculation:")
    print(f"  N strategies: {n}")
    print(f"  Base weight (1/N): {float(w_base):.4f}")
    print(f"  Median Calmar: {float(median_calmar):.4f}")
    print(f"  Alpha (dampening): {float(alpha)}")
    print(f"  f_min (floor): {float(f_min)}")
    print(f"  f_max (cap): {float(f_max)}")

    # Calculate raw weights with tilt
    raw_weights: dict[str, Decimal] = {}

    print("\n  Per-strategy calculation:")
    for filename, calmar in sorted(calmar_ratios.items()):
        # Ratio to median
        ratio = calmar / median_calmar

        # Apply alpha (square root dampening)
        # For Decimal, we use float conversion for the power operation
        dampened = Decimal(str(float(ratio) ** float(alpha)))

        # Clip to [f_min, f_max]
        clipped = max(f_min, min(f_max, dampened))

        # Multiply by base weight
        raw_weight = w_base * clipped
        raw_weights[filename] = raw_weight

        print(
            f"    {filename:25s}: Calmar={float(calmar):8.2f}, "
            f"ratio={float(ratio):6.2f}, dampened={float(dampened):5.2f}, "
            f"clipped={float(clipped):4.2f}, raw_w={float(raw_weight):.4f}"
        )

    # Normalize to sum to 1
    total = sum(raw_weights.values())
    normalized_weights = {
        filename: (w / total).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
        for filename, w in raw_weights.items()
    }

    # Adjust for rounding errors to ensure exact sum of 1.0
    adjustment = Decimal("1") - sum(normalized_weights.values())
    if adjustment != 0:
        # Add adjustment to largest weight
        largest = max(normalized_weights, key=lambda k: normalized_weights[k])
        normalized_weights[largest] += adjustment

    return normalized_weights


def load_current_config() -> dict:
    """Load the current strategy.prod.json config."""
    with STRATEGY_PROD_JSON.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config: dict) -> None:
    """Save the strategy.prod.json config."""
    with STRATEGY_PROD_JSON.open("w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
        f.write("\n")  # Trailing newline


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Recalculate strategy weights using Calmar-tilt formula"
    )
    parser.add_argument(
        "--csv",
        type=Path,
        help="Path to CSV file (default: latest in strategy_results/)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show calculated weights without updating config",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.5,
        help="Dampening exponent (default: 0.5)",
    )
    parser.add_argument(
        "--f-min",
        type=float,
        default=0.5,
        help="Minimum multiplier floor (default: 0.5)",
    )
    parser.add_argument(
        "--f-max",
        type=float,
        default=2.0,
        help="Maximum multiplier cap (default: 2.0)",
    )
    args = parser.parse_args()

    # Find CSV file
    if args.csv:
        csv_path = args.csv
        if not csv_path.is_absolute():
            csv_path = PROJECT_ROOT / csv_path
    else:
        csv_path = find_latest_csv(STRATEGY_RESULTS_DIR)

    print(f"Reading CSV: {csv_path}")

    # Load Calmar ratios
    calmar_ratios = load_calmar_ratios(csv_path)
    print(f"\nLoaded {len(calmar_ratios)} strategy Calmar ratios:")
    for filename, calmar in sorted(calmar_ratios.items()):
        print(f"  {filename:25s}: {float(calmar):10.2f}")

    # Calculate new weights
    new_weights = calculate_calmar_tilt_weights(
        calmar_ratios,
        alpha=Decimal(str(args.alpha)),
        f_min=Decimal(str(args.f_min)),
        f_max=Decimal(str(args.f_max)),
    )

    # Load current config
    config = load_current_config()
    old_allocations = config.get("allocations", {})

    # Display comparison
    print("\n" + "=" * 70)
    print("WEIGHT COMPARISON (Old → New)")
    print("=" * 70)
    total_old = Decimal("0")
    total_new = Decimal("0")

    for filename in sorted(config.get("files", [])):
        old_w = Decimal(str(old_allocations.get(filename, 0)))
        new_w = new_weights.get(filename, Decimal("0"))
        change = new_w - old_w
        change_pct = (
            (change / old_w * 100) if old_w != 0 else Decimal("0")
        )

        total_old += old_w
        total_new += new_w

        arrow = "→"
        if change > Decimal("0.005"):
            arrow = "↑"
        elif change < Decimal("-0.005"):
            arrow = "↓"

        print(
            f"  {filename:25s}: {float(old_w):6.1%} {arrow} {float(new_w):6.1%} "
            f"({float(change):+.1%}, {float(change_pct):+.0f}%)"
        )

    print("-" * 70)
    print(f"  {'TOTAL':25s}: {float(total_old):6.1%} → {float(total_new):6.1%}")

    # Check for missing strategies
    config_files = set(config.get("files", []))
    weight_files = set(new_weights.keys())
    missing_in_csv = config_files - weight_files
    extra_in_csv = weight_files - config_files

    if missing_in_csv:
        print(f"\n⚠️  Strategies in config but not in CSV: {missing_in_csv}")
    if extra_in_csv:
        print(f"\n⚠️  Strategies in CSV but not in config: {extra_in_csv}")

    if args.dry_run:
        print("\n[DRY RUN] No changes made to strategy.prod.json")
        return 0

    # Update config
    config["allocations"] = {
        filename: float(new_weights.get(filename, Decimal("0")))
        for filename in config.get("files", [])
    }

    save_config(config)
    print(f"\n✅ Updated {STRATEGY_PROD_JSON}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
