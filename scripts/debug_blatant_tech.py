#!/usr/bin/env python3
"""Business Unit: Scripts | Status: current.

Debug script to investigate blatant_tech divergence.
Checks key decision points for GDX RSI(7) condition.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project paths
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "layers" / "shared"))
sys.path.insert(0, str(PROJECT_ROOT / "functions" / "strategy_worker"))

import os
os.environ.setdefault("MARKET_DATA_BUCKET", "alchemiser-dev-market-data")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

import pandas as pd
from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore
from the_alchemiser.shared.data_v2.cached_market_data_adapter import CachedMarketDataAdapter
from the_alchemiser.shared.data_v2.live_bar_provider import LiveBarProvider
from the_alchemiser.shared.value_objects.symbol import Symbol
from indicators.indicators import TechnicalIndicators


def main():
    print("=" * 70)
    print("BLATANT_TECH DIVERGENCE DEBUG")
    print("=" * 70)
    print("\nExpected (Composer): CORD NBIS SOX")
    print("Actual (Our system): CORD SOXS")
    print("\nKey decision: (< (rsi 'GDX' {:window 7}) 70)")
    print("  If TRUE  -> enters Metals group -> can select NBIS")
    print("  If FALSE -> else branch -> just CORD")
    print("=" * 70)
    
    # Check S3 historical data
    print("\n--- S3 Historical Data (no live bar) ---")
    store = MarketDataStore()
    gdx_df = store.read_symbol_data("GDX")
    print(f"GDX rows in S3: {len(gdx_df)}")
    print(f"GDX last 5 dates and closes:")
    print(gdx_df[["close"]].tail())
    
    # Calculate RSI(7) without live bar
    prices_s3 = gdx_df["close"]
    rsi_7_s3 = TechnicalIndicators.rsi(prices_s3, window=7)
    print(f"\nGDX RSI(7) from S3 = {rsi_7_s3.iloc[-1]:.4f}")
    print(f"Condition: rsi(GDX, 7) < 70 = {rsi_7_s3.iloc[-1] < 70}")
    
    # Check with live bar
    print("\n--- With Live Bar from Alpaca ---")
    adapter = CachedMarketDataAdapter(append_live_bar=True)
    bars = adapter.get_bars(Symbol("GDX"), "1Y", "1D")
    print(f"Total bars with live: {len(bars)}")
    print(f"Last 5 bars:")
    for bar in bars[-5:]:
        print(f"  {bar.timestamp.date()}: close={bar.close}")
    
    # Check if last bar is live
    if bars:
        last_bar = bars[-1]
        print(f"\nLast bar is_incomplete: {getattr(last_bar, 'is_incomplete', 'N/A')}")
    
    # Calculate RSI with live bar
    prices_live = pd.Series([float(b.close) for b in bars])
    rsi_7_live = TechnicalIndicators.rsi(prices_live, window=7)
    print(f"\nGDX RSI(7) with live bar = {rsi_7_live.iloc[-1]:.4f}")
    print(f"Condition: rsi(GDX, 7) < 70 = {rsi_7_live.iloc[-1] < 70}")
    
    # Check T-1 (yesterday only)
    print("\n--- T-1 Comparison (no today) ---")
    if len(bars) > 1:
        prices_t1 = pd.Series([float(b.close) for b in bars[:-1]])
        rsi_7_t1 = TechnicalIndicators.rsi(prices_t1, window=7)
        print(f"GDX RSI(7) T-1 = {rsi_7_t1.iloc[-1]:.4f}")
        print(f"Condition T-1: rsi(GDX, 7) < 70 = {rsi_7_t1.iloc[-1] < 70}")
    
    # Key insight
    print("\n" + "=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    rsi_val = rsi_7_live.iloc[-1]
    if rsi_val >= 70:
        print(f"\n>>> GDX RSI(7) = {rsi_val:.2f} >= 70")
        print(">>> This means condition (< rsi 70) is FALSE")
        print(">>> So we take ELSE branch -> CORD only")
        print(">>> But Composer shows NBIS, meaning their RSI < 70")
        print("\nPossible causes:")
        print("  1. Data difference (S3 vs Composer source)")
        print("  2. Live bar timing (our price vs Composer's price)")
        print("  3. RSI calculation difference")
    else:
        print(f"\n>>> GDX RSI(7) = {rsi_val:.2f} < 70")
        print(">>> This means condition is TRUE")
        print(">>> So we should enter Metals group")
        print(">>> Something else is causing the divergence")


if __name__ == "__main__":
    main()
