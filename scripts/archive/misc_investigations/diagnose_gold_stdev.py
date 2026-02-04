#!/usr/bin/env python3
"""Business Unit: debugging | Status: development.

Diagnose Gold strategy signal drift by comparing T-0 vs T-1 stdev-return values.

The Gold strategy's first decision gate is:
    (if (> (stdev-return "GLD" {:window 10}) (stdev-return "GLD" {:window 100}))
      BIL   ; volatility spike → safety
      UGL   ; normal volatility → gold rotation tree

This script compares indicator values using:
- T-0: Wednesday 13 January 2026 as latest bar
- T-1: Tuesday 12 January 2026 as latest bar (excluding Wednesday)

Usage:
    poetry run python scripts/diagnose_gold_stdev.py

"""

from __future__ import annotations

import os
import sys
from datetime import date, datetime
from pathlib import Path

import pandas as pd

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "layers" / "shared"))
sys.path.insert(0, str(PROJECT_ROOT / "functions" / "strategy_worker"))

# Set environment variables for S3 market data access
os.environ.setdefault("MARKET_DATA_BUCKET", "alchemiser-dev-market-data")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")


def calculate_stdev_return(prices: pd.Series, window: int) -> float:
    """Calculate stdev of returns matching our production implementation.

    Args:
        prices: Series of close prices
        window: Rolling window size

    Returns:
        Standard deviation of percentage returns (scaled to %)

    """
    if len(prices) < window + 1:
        return float("nan")
    returns = prices.pct_change() * 100  # Percentage returns
    stdev_series = returns.rolling(window=window, min_periods=window).std()
    return float(stdev_series.iloc[-1])


def main() -> None:
    """Run the T-0 vs T-1 diagnostic for Gold strategy."""
    from the_alchemiser.shared.data_v2.cached_market_data_adapter import (
        CachedMarketDataAdapter,
    )

    print("=" * 70)
    print("GOLD STRATEGY SIGNAL DRIFT DIAGNOSTIC")
    print("Comparing stdev-return with T-0 (Jan 13) vs T-1 (Jan 12)")
    print("=" * 70)

    adapter = CachedMarketDataAdapter()

    # Fetch GLD data (need enough for 100-day window + buffer)
    bars = adapter.get_bars("GLD", "1Y", "1Day")
    df = pd.DataFrame([{"date": b.timestamp.date(), "close": float(b.close)} for b in bars])
    df = df.drop_duplicates(subset=["date"]).sort_values("date").reset_index(drop=True)

    print(f"\nGLD data: {len(df)} bars from {df['date'].iloc[0]} to {df['date'].iloc[-1]}")

    # Find the indices for our target dates
    # Note: Jan 13 2026 is a Monday, Jan 12 is a Sunday (no trading)
    # Adjusting to use most recent trading days available
    # Using T-0 = latest available, T-1 = one trading day before
    latest_date = df["date"].iloc[-1]
    print(f"\nLatest available date: {latest_date}")

    # Use dynamic dates based on available data
    t0_date = latest_date  # Most recent (should be Jan 13 or close)
    # Find previous trading day
    t0_idx_val = df[df["date"] == t0_date].index[0]
    t1_date = df.loc[t0_idx_val - 1, "date"] if t0_idx_val > 0 else None

    if t1_date is None:
        print("❌ ERROR: Not enough data for T-1")
        return

    print(f"Using T-0: {t0_date} (latest)")
    print(f"Using T-1: {t1_date} (previous trading day)")

    t0_idx = df[df["date"] == t0_date].index
    t1_idx = df[df["date"] == t1_date].index

    if len(t0_idx) == 0:
        print(f"\n❌ ERROR: No data for T-0 date {t0_date}")
        print("Available dates around that time:")
        mask = (df["date"] >= date(2026, 1, 8)) & (df["date"] <= date(2026, 1, 15))
        print(df[mask][["date", "close"]].to_string(index=False))
        return

    if len(t1_idx) == 0:
        print(f"\n❌ ERROR: No data for T-1 date {t1_date}")
        return

    t0_idx = t0_idx[0]
    t1_idx = t1_idx[0]

    print(f"\nT-0 (Wed Jan 13): index {t0_idx}, close = ${df.loc[t0_idx, 'close']:.2f}")
    print(f"T-1 (Tue Jan 12): index {t1_idx}, close = ${df.loc[t1_idx, 'close']:.2f}")

    # Calculate stdev-return with T-0 as latest bar
    prices_t0 = df.loc[: t0_idx, "close"]
    stdev_10_t0 = calculate_stdev_return(prices_t0, 10)
    stdev_100_t0 = calculate_stdev_return(prices_t0, 100)

    # Calculate stdev-return with T-1 as latest bar
    prices_t1 = df.loc[: t1_idx, "close"]
    stdev_10_t1 = calculate_stdev_return(prices_t1, 10)
    stdev_100_t1 = calculate_stdev_return(prices_t1, 100)

    print("\n" + "-" * 70)
    print("STDEV-RETURN COMPARISON")
    print("-" * 70)

    print(f"\n{'Metric':<30} {'T-0 (Jan 13)':<20} {'T-1 (Jan 12)':<20}")
    print("-" * 70)
    print(f"{'stdev-return(GLD, 10)':<30} {stdev_10_t0:<20.6f} {stdev_10_t1:<20.6f}")
    print(f"{'stdev-return(GLD, 100)':<30} {stdev_100_t0:<20.6f} {stdev_100_t1:<20.6f}")

    # Decision analysis
    print("\n" + "-" * 70)
    print("DECISION GATE ANALYSIS")
    print("-" * 70)
    print("\nCondition: stdev_10 > stdev_100 → BIL (risk-off)")
    print("           stdev_10 ≤ stdev_100 → UGL (gold rotation)")

    diff_t0 = stdev_10_t0 - stdev_100_t0
    diff_t1 = stdev_10_t1 - stdev_100_t1

    decision_t0 = "BIL" if stdev_10_t0 > stdev_100_t0 else "UGL"
    decision_t1 = "BIL" if stdev_10_t1 > stdev_100_t1 else "UGL"

    print(f"\nT-0 (Jan 13): stdev_10 - stdev_100 = {diff_t0:+.6f} → {decision_t0}")
    print(f"T-1 (Jan 12): stdev_10 - stdev_100 = {diff_t1:+.6f} → {decision_t1}")

    # Highlight the drift
    print("\n" + "=" * 70)
    if decision_t0 != decision_t1:
        print(f"⚠️  SIGNAL FLIP DETECTED: T-1 → {decision_t1}, T-0 → {decision_t0}")
        print("\nThis confirms the T-0/T-1 timing difference causes signal drift!")
    else:
        print(f"✅ No signal flip: Both T-0 and T-1 → {decision_t0}")
        print("\nThe drift is NOT caused by T-0/T-1 timing difference alone.")
    print("=" * 70)

    # Show the return values around the boundary
    print("\n" + "-" * 70)
    print("DAILY RETURNS (last 15 days)")
    print("-" * 70)

    returns = df["close"].pct_change() * 100
    df["return_pct"] = returns

    start_idx = max(0, t0_idx - 14)
    recent = df.loc[start_idx : t0_idx, ["date", "close", "return_pct"]]
    print(recent.to_string(index=False))

    # Show rolling stdev evolution
    print("\n" + "-" * 70)
    print("STDEV-10 EVOLUTION (last 10 days)")
    print("-" * 70)

    stdev_10_series = returns.rolling(window=10, min_periods=10).std()
    stdev_100_series = returns.rolling(window=100, min_periods=100).std()

    df["stdev_10"] = stdev_10_series
    df["stdev_100"] = stdev_100_series
    df["decision"] = df.apply(
        lambda r: "BIL" if r["stdev_10"] > r["stdev_100"] else "UGL"
        if pd.notna(r["stdev_10"]) and pd.notna(r["stdev_100"])
        else "N/A",
        axis=1,
    )

    start_idx = max(0, t0_idx - 9)
    evolution = df.loc[start_idx : t0_idx, ["date", "stdev_10", "stdev_100", "decision"]]
    print(evolution.to_string(index=False))

    # Additional context: show what's rolling out of the 10-day window
    print("\n" + "-" * 70)
    print("WINDOW BOUNDARY ANALYSIS")
    print("-" * 70)
    print("\nWhat's ENTERING the 10-day window when moving from T-1 to T-0:")
    entering_date = df.loc[t0_idx, "date"]
    entering_return = df.loc[t0_idx, "return_pct"]
    print(f"  + Jan 13: return = {entering_return:+.4f}%")

    print("\nWhat's EXITING the 10-day window when moving from T-1 to T-0:")
    # The bar that exits is 10 days before T-1's oldest bar in window
    exiting_idx = t1_idx - 9  # First bar in T-1's 10-day window
    if exiting_idx >= 0:
        exiting_date = df.loc[exiting_idx, "date"]
        exiting_return = df.loc[exiting_idx, "return_pct"]
        print(f"  - {exiting_date}: return = {exiting_return:+.4f}%")

    # Impact assessment
    print("\n" + "-" * 70)
    print("IMPACT ASSESSMENT")
    print("-" * 70)
    print(f"\nΔ stdev_10 = {stdev_10_t0 - stdev_10_t1:+.6f}")
    print(f"Δ stdev_100 = {stdev_100_t0 - stdev_100_t1:+.6f}")

    margin_t0 = abs(stdev_10_t0 - stdev_100_t0)
    margin_t1 = abs(stdev_10_t1 - stdev_100_t1)
    print(f"\nDecision margin T-0: |{diff_t0:.6f}| = {margin_t0:.6f}")
    print(f"Decision margin T-1: |{diff_t1:.6f}| = {margin_t1:.6f}")

    if margin_t0 < 0.1 or margin_t1 < 0.1:
        print("\n⚠️  VERY CLOSE DECISION: margin < 0.1%")
        print("   Small data differences or timing can flip the signal!")


if __name__ == "__main__":
    main()
