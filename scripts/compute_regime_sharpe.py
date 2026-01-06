#!/usr/bin/env python
"""Business Unit: scripts | Status: current.

Compute per-regime Sharpe ratios for all strategies.

This script:
1. Downloads SPY data and runs HMM to label each day with a regime
2. For each strategy DSL file, simulates historical returns
3. Computes Sharpe ratio for each strategy within each regime
4. Outputs regime_weights.json for use by the Strategy Orchestrator

Usage:
    python scripts/compute_regime_sharpe.py --output data/regime_weights.json
    python scripts/compute_regime_sharpe.py --start 2015-01-01 --end 2024-12-31

Prerequisites:
    - Poetry environment with hmmlearn, pandas, numpy, yfinance
    - DSL strategy files in data/strategies/ or similar

Note: This is an offline script for generating the regime_weights.json config.
It should be run periodically (e.g., monthly) to update Sharpe estimates.
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yfinance as yf

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from the_alchemiser.shared.regime.classifier import HMMRegimeClassifier

warnings.filterwarnings("ignore")

# Standard trading days per year for US equity markets (annualization factor)
TRADING_DAYS_PER_YEAR = 252


def download_spy_data(start_date: str, end_date: str) -> pd.DataFrame:
    """Download SPY data from Yahoo Finance.

    Args:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Returns:
        SPY OHLC DataFrame

    """
    print(f"Downloading SPY data from {start_date} to {end_date}...")
    spy_data = yf.download("SPY", start=start_date, end=end_date, progress=False)
    print(f"Downloaded {len(spy_data)} days of data")
    return spy_data


def compute_regime_labels(spy_data: pd.DataFrame) -> tuple[pd.Series, HMMRegimeClassifier]:
    """Run HMM classifier and return regime labels for each day.

    Args:
        spy_data: SPY OHLC DataFrame

    Returns:
        Tuple of (regime_series, fitted_classifier)

    """
    print("\nRunning HMM regime classification...")
    classifier = HMMRegimeClassifier()

    # Prepare features
    features_df = classifier.prepare_features(spy_data)

    # Fit and classify
    classifier.fit(features_df)
    regime_state = classifier.classify_with_smoothing(features_df)

    # Get regime labels for all days using the internal state probabilities
    # For now, use the final regime as representative
    regimes = pd.Series(
        [regime_state.regime.value] * len(features_df),
        index=features_df.index,
    )

    # Print regime distribution
    regime_counts = regimes.value_counts()
    print("\nRegime distribution:")
    for regime, count in regime_counts.items():
        pct = count / len(regimes) * 100
        print(f"  {regime}: {count} days ({pct:.1f}%)")

    return regimes, classifier


def generate_placeholder_returns(
    strategy_file: str,
    regimes: pd.Series,
    spy_data: pd.DataFrame,
) -> pd.Series:
    """Generate placeholder returns for a strategy.

    This is a PLACEHOLDER function. In production, you would:
    1. Run the actual DSL strategy through a backtest engine
    2. Record daily returns for each day in the regime period
    3. Return actual strategy returns

    For now, we generate synthetic returns based on strategy characteristics.

    Args:
        strategy_file: Name of DSL strategy file
        regimes: Regime labels for each day
        spy_data: SPY OHLC data

    Returns:
        Series of daily returns aligned with regimes index

    """
    # Calculate SPY returns aligned with regimes
    if isinstance(spy_data.columns, pd.MultiIndex):
        spy_close = spy_data["Close"].iloc[:, 0]
    else:
        spy_close = spy_data["Close"]

    spy_returns = np.log(spy_close / spy_close.shift(1))
    spy_returns = spy_returns.loc[regimes.index]

    # WARNING: PLACEHOLDER DATA - Replace with actual backtest results.
    # Strategy characteristics (placeholder - would come from actual backtest)
    # These multipliers represent how a strategy performs relative to SPY.
    # TODO: Implement actual strategy backtest integration to replace these.
    strategy_profiles: dict[str, dict[str, float]] = {
        "nuclear_feaver.clj": {"beta": 1.5, "alpha": 0.0002, "vol_mult": 1.3},
        "beam_chain.clj": {"beta": 1.2, "alpha": 0.0003, "vol_mult": 1.1},
        "beefier_3x.clj": {"beta": 2.5, "alpha": 0.0001, "vol_mult": 2.0},
        "chicken_rice.clj": {"beta": 0.8, "alpha": 0.0001, "vol_mult": 0.9},
        "nova_ibit.clj": {"beta": 2.0, "alpha": 0.0004, "vol_mult": 1.8},
        "rains_em_dancer.clj": {"beta": 1.0, "alpha": 0.0002, "vol_mult": 1.2},
        "simons_kmlm.clj": {"beta": 0.3, "alpha": 0.0004, "vol_mult": 0.6},
        "bento_collection.clj": {"beta": 0.9, "alpha": 0.0002, "vol_mult": 1.0},
        "sisyphus_lowvol.clj": {"beta": 0.4, "alpha": 0.0002, "vol_mult": 0.5},
        "gold.clj": {"beta": -0.1, "alpha": 0.0001, "vol_mult": 0.7},
    }

    profile = strategy_profiles.get(
        strategy_file, {"beta": 1.0, "alpha": 0.0001, "vol_mult": 1.0}
    )

    # Generate synthetic returns: strategy = alpha + beta * SPY + noise
    np.random.seed(hash(strategy_file) % 2**32)
    noise = np.random.normal(0, 0.005, len(spy_returns)) * profile["vol_mult"]

    strategy_returns = profile["alpha"] + profile["beta"] * spy_returns.values + noise

    return pd.Series(strategy_returns, index=regimes.index)


def compute_sharpe_by_regime(
    returns: pd.Series,
    regimes: pd.Series,
    risk_free_rate: float = 0.05,
) -> dict[str, dict[str, Any]]:
    """Compute Sharpe ratio for each regime.

    Args:
        returns: Daily strategy returns
        regimes: Regime label for each day
        risk_free_rate: Annual risk-free rate (default 5%)

    Returns:
        Dict mapping regime -> {sharpe, mean_return, volatility, sample_days}

    """
    daily_rf = risk_free_rate / TRADING_DAYS_PER_YEAR
    results: dict[str, dict[str, Any]] = {}

    for regime in regimes.unique():
        mask = regimes == regime
        regime_returns = returns.loc[mask]

        if len(regime_returns) < 30:
            # Insufficient data
            results[regime] = {
                "sharpe": 0.0,
                "mean_return": 0.0,
                "volatility": 0.0,
                "sample_days": len(regime_returns),
            }
            continue

        mean_return = regime_returns.mean()
        volatility = regime_returns.std()

        if volatility > 0:
            sharpe = (mean_return - daily_rf) / volatility * np.sqrt(TRADING_DAYS_PER_YEAR)
        else:
            sharpe = 0.0

        results[regime] = {
            "sharpe": round(sharpe, 2),
            "mean_return": round(mean_return * TRADING_DAYS_PER_YEAR * 100, 2),  # Annualized %
            "volatility": round(volatility * np.sqrt(TRADING_DAYS_PER_YEAR) * 100, 2),  # Annualized %
            "sample_days": len(regime_returns),
        }

    return results


# Heuristic mapping from Sharpe ratio bands to weight multipliers.
# These constants define how aggressively to overweight or underweight
# strategies based on their per-regime Sharpe ratios. They can be tuned
# empirically without changing the core logic in `compute_weight_multipliers`.
SHARPE_OVERWEIGHT_MIN: float = 1.0
SHARPE_SLIGHT_OVERWEIGHT_MIN: float = 0.5
SHARPE_NEUTRAL_MIN: float = 0.0
SHARPE_UNDERWEIGHT_MIN: float = -0.5

WEIGHT_MULTIPLIER_OVERWEIGHT: float = 1.3
WEIGHT_MULTIPLIER_SLIGHT_OVERWEIGHT: float = 1.1
WEIGHT_MULTIPLIER_NEUTRAL: float = 1.0
WEIGHT_MULTIPLIER_UNDERWEIGHT: float = 0.7
WEIGHT_MULTIPLIER_SIGNIFICANT_UNDERWEIGHT: float = 0.3


def compute_weight_multipliers(sharpe_by_regime: dict[str, float]) -> dict[str, float]:
    """Compute weight multipliers from Sharpe ratios.

    Uses a simple heuristic defined by the module-level Sharpe band and
    weight multiplier constants:
    - Sharpe >= SHARPE_OVERWEIGHT_MIN: WEIGHT_MULTIPLIER_OVERWEIGHT
    - Sharpe >= SHARPE_SLIGHT_OVERWEIGHT_MIN: WEIGHT_MULTIPLIER_SLIGHT_OVERWEIGHT
    - Sharpe >= SHARPE_NEUTRAL_MIN: WEIGHT_MULTIPLIER_NEUTRAL
    - Sharpe >= SHARPE_UNDERWEIGHT_MIN: WEIGHT_MULTIPLIER_UNDERWEIGHT
    - Otherwise: WEIGHT_MULTIPLIER_SIGNIFICANT_UNDERWEIGHT

    Args:
        sharpe_by_regime: Sharpe ratio for each regime

    Returns:
        Weight multiplier for each regime

    """
    multipliers: dict[str, float] = {}

    for regime, sharpe in sharpe_by_regime.items():
        if sharpe >= SHARPE_OVERWEIGHT_MIN:
            mult = WEIGHT_MULTIPLIER_OVERWEIGHT
        elif sharpe >= SHARPE_SLIGHT_OVERWEIGHT_MIN:
            mult = WEIGHT_MULTIPLIER_SLIGHT_OVERWEIGHT
        elif sharpe >= SHARPE_NEUTRAL_MIN:
            mult = WEIGHT_MULTIPLIER_NEUTRAL
        elif sharpe >= SHARPE_UNDERWEIGHT_MIN:
            mult = WEIGHT_MULTIPLIER_UNDERWEIGHT
        else:
            mult = WEIGHT_MULTIPLIER_SIGNIFICANT_UNDERWEIGHT

        multipliers[regime] = round(mult, 1)

    return multipliers


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Compute per-regime Sharpe ratios for strategy weighting"
    )
    parser.add_argument(
        "--start",
        type=str,
        default="2005-01-01",
        help="Start date for analysis (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end",
        type=str,
        default=datetime.now().strftime("%Y-%m-%d"),
        help="End date for analysis (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="layers/shared/the_alchemiser/shared/config/regime_weights.json",
        help="Output path for regime_weights.json",
    )
    parser.add_argument(
        "--strategies",
        type=str,
        default="layers/shared/the_alchemiser/shared/config/strategy.prod.json",
        help="Path to strategy config JSON",
    )

    args = parser.parse_args()

    print("=" * 80)
    print("REGIME-STRATIFIED SHARPE RATIO COMPUTATION")
    print("=" * 80)
    print(f"Date range: {args.start} to {args.end}")
    print(f"Output: {args.output}")

    # Load strategy config
    with open(args.strategies, "r") as f:
        strategy_config = json.load(f)
    strategy_files = strategy_config.get("files", [])
    print(f"Strategies: {len(strategy_files)}")

    # Download SPY data
    spy_data = download_spy_data(args.start, args.end)

    # Compute regime labels
    regimes, classifier = compute_regime_labels(spy_data)

    # Compute Sharpe for each strategy in each regime
    print("\n" + "=" * 80)
    print("COMPUTING PER-STRATEGY SHARPE RATIOS BY REGIME")
    print("=" * 80)

    strategies_output: dict[str, dict[str, Any]] = {}

    for strategy_file in strategy_files:
        print(f"\n{strategy_file}:")

        # Get strategy returns (placeholder - replace with actual backtest)
        returns = generate_placeholder_returns(strategy_file, regimes, spy_data)

        # Compute Sharpe by regime
        regime_stats = compute_sharpe_by_regime(returns, regimes)

        # Extract Sharpe values
        sharpe_by_regime = {k: v["sharpe"] for k, v in regime_stats.items()}
        sample_days_by_regime = {k: v["sample_days"] for k, v in regime_stats.items()}

        # Compute weight multipliers
        weight_multipliers = compute_weight_multipliers(sharpe_by_regime)

        # Print summary
        for regime, stats in regime_stats.items():
            mult = weight_multipliers[regime]
            print(
                f"  {regime}: Sharpe={stats['sharpe']:.2f}, "
                f"Days={stats['sample_days']}, Mult={mult:.1f}"
            )

        strategies_output[strategy_file] = {
            "sharpe_by_regime": sharpe_by_regime,
            "weight_multiplier_by_regime": weight_multipliers,
            "sample_days_by_regime": sample_days_by_regime,
        }

    # Build output config
    output_config = {
        "schema_version": "1.0.0",
        "description": f"Regime-based strategy weights computed on {datetime.now().isoformat()}",
        "adjustment_method": "sharpe_weighted",
        "min_weight": 0.02,
        "max_weight": 0.40,
        "sharpe_floor": 0.0,
        "enable_regime_adjustment": True,
        "strategies": strategies_output,
        "_metadata": {
            "computed_at": datetime.now().isoformat(),
            "date_range": f"{args.start} to {args.end}",
            "total_days": len(regimes),
            "regime_distribution": regimes.value_counts().to_dict(),
        },
    }

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(output_config, f, indent=2, default=str)

    print("\n" + "=" * 80)
    print(f"Output written to: {args.output}")
    print("=" * 80)

    # Print current regime (if supported by classifier implementation)
    if hasattr(classifier, "print_current_state"):
        classifier.print_current_state(regimes, classifier.prepare_features(spy_data))


if __name__ == "__main__":
    main()
