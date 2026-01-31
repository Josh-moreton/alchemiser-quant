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

# Valid stages
VALID_STAGES = ("dev", "staging", "prod")


def get_config_path(stage: str) -> Path:
    """Get the config file path for the given stage."""
    if stage not in VALID_STAGES:
        raise ValueError(f"Invalid stage '{stage}'. Must be one of: {VALID_STAGES}")
    return CONFIG_DIR / f"strategy.{stage}.json"

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
    "The Holy Grail": "holy_grail.clj",
    "KMLM switcher": "kmlm_switcher.clj",
    "Custom Exposures": "custom_exposures.clj",
    "FTL Starburst": "ftl_starburst.clj",
    "Gold Currency Hedge": "gold_currency.clj",
    "Growth Blend": "growth_blend.clj",
    "V1a What Have I Done": "what_have_i_done.clj",
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


def strip_prefix(filename: str) -> str:
    """Strip 'testing/' prefix from filename if present."""
    if filename.startswith("testing/"):
        return filename[8:]  # len("testing/") == 8
    return filename


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
        print(f"❌ ERROR: Could not match CSV names: {unmatched}")
        print("\nPlease add mappings to CSV_TO_FILENAME in scripts/rebalance_strategy_weights.py")
        print("Available .clj files can be found in layers/shared/the_alchemiser/shared/strategies/")
        sys.exit(1)

    return calmar_by_filename


def calculate_calmar_tilt_weights(
    calmar_ratios: dict[str, Decimal],
    config_files: set[str],
    alpha: Decimal = ALPHA,
    f_min: Decimal = F_MIN,
    f_max: Decimal = F_MAX,
) -> dict[str, Decimal]:
    """Calculate Calmar-tilted weights using the formula from issue #2975.

    Formula:
        w_i = Normalise(w_base × clip((Calmar_i / MedianCalmar)^α, f_min, f_max))

    Strategies in config but missing from CSV get the base weight (1/N),
    and the remaining allocation is distributed among CSV-based strategies.

    IMPORTANT: Only strategies present in BOTH CSV and config are used for
    weight calculation. CSV strategies not in config are ignored (with warning).

    Args:
        calmar_ratios: Dict of filename -> Calmar ratio (from CSV)
        config_files: Set of all strategy filenames from config
        alpha: Dampening exponent (default 0.5 = square root)
        f_min: Minimum multiplier (default 0.5)
        f_max: Maximum multiplier (default 2.0)

    Returns:
        Dict of filename -> normalized weight
    """
    # Total number of strategies (from config, not CSV)
    n_total = len(config_files)
    if n_total == 0:
        raise ValueError("No strategies in config")

    # Filter CSV strategies to only those in config (ignore extras)
    extra_in_csv = set(calmar_ratios.keys()) - config_files
    if extra_in_csv:
        print(f"\n⚠️  Strategies in CSV but not in config (ignored): {extra_in_csv}")

    # Only use CSV strategies that are in config for weight calculation
    calmar_ratios = {k: v for k, v in calmar_ratios.items() if k in config_files}

    # Base weight = 1/N (using total config strategies)
    w_base = Decimal("1") / Decimal(str(n_total))

    # Identify missing strategies (in config but not in CSV)
    csv_files = set(calmar_ratios.keys())
    missing_strategies = config_files - csv_files

    if missing_strategies:
        print(f"\n⚠️  Strategies missing from CSV (will get base weight {float(w_base):.1%}):")
        for s in sorted(missing_strategies):
            print(f"    - {s}")

    # Reserve base weight for missing strategies
    reserved_weight = w_base * Decimal(str(len(missing_strategies)))
    available_weight = Decimal("1") - reserved_weight

    # Calculate median Calmar from CSV strategies
    if not calmar_ratios:
        raise ValueError("No Calmar ratios provided from CSV")

    calmar_values = list(calmar_ratios.values())
    median_calmar = Decimal(str(median([float(c) for c in calmar_values])))

    if median_calmar == 0:
        raise ValueError("Median Calmar ratio is zero, cannot compute weights")

    print(f"\nCalmar-Tilt Calculation:")
    print(f"  N strategies (config): {n_total}")
    print(f"  N strategies (CSV matched): {len(calmar_ratios)}")
    print(f"  N missing from CSV (base weight): {len(missing_strategies)}")
    print(f"  Base weight (1/N): {float(w_base):.4f}")
    print(f"  Reserved for missing: {float(reserved_weight):.4f}")
    print(f"  Available for CSV strategies: {float(available_weight):.4f}")
    print(f"  Median Calmar: {float(median_calmar):.4f}")
    print(f"  Alpha (dampening): {float(alpha)}")
    print(f"  f_min (floor): {float(f_min)}")
    print(f"  f_max (cap): {float(f_max)}")

    # Calculate raw weights with tilt for CSV strategies
    raw_weights: dict[str, Decimal] = {}

    print("\n  Per-strategy calculation (CSV strategies):")
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

    # Normalize CSV strategies to fill the available_weight
    csv_total = sum(raw_weights.values())
    normalized_weights: dict[str, Decimal] = {}

    for filename, raw_w in raw_weights.items():
        # Scale to fit within available_weight
        scaled = (raw_w / csv_total) * available_weight
        normalized_weights[filename] = scaled.quantize(
            Decimal("0.001"), rounding=ROUND_HALF_UP
        )

    # Add missing strategies at base weight
    for filename in missing_strategies:
        normalized_weights[filename] = w_base.quantize(
            Decimal("0.001"), rounding=ROUND_HALF_UP
        )

    # Adjust for rounding errors to ensure exact sum of 1.0
    adjustment = Decimal("1") - sum(normalized_weights.values())
    if adjustment != 0:
        # Add adjustment to largest weight
        largest = max(normalized_weights, key=lambda k: normalized_weights[k])
        normalized_weights[largest] += adjustment

    return normalized_weights


def load_current_config(config_path: Path) -> dict:
    """Load the current strategy config."""
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config: dict, config_path: Path) -> None:
    """Save the strategy config."""
    with config_path.open("w", encoding="utf-8") as f:
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
    parser.add_argument(
        "--stage",
        type=str,
        default="prod",
        choices=VALID_STAGES,
        help="Stage to update: dev, staging, or prod (default: prod)",
    )
    args = parser.parse_args()

    # Get config path for the specified stage
    config_path = get_config_path(args.stage)
    print(f"Target config: {config_path.name}")

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

    # Load current config
    config = load_current_config(config_path)
    old_allocations = config.get("allocations", {})
    config_files = set(config.get("files", []))

    # Calculate new weights (passing config_files so missing strategies get base weight)
    new_weights = calculate_calmar_tilt_weights(
        calmar_ratios,
        config_files=config_files,
        alpha=Decimal(str(args.alpha)),
        f_min=Decimal(str(args.f_min)),
        f_max=Decimal(str(args.f_max)),
    )

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

    if args.dry_run:
        print(f"\n[DRY RUN] No changes made to {config_path.name}")
        return 0

    # Update config
    config["allocations"] = {
        filename: float(new_weights.get(filename, Decimal("0")))
        for filename in config.get("files", [])
    }

    save_config(config, config_path)
    print(f"\n✅ Updated {config_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
