#!/usr/bin/env python3
"""Business Unit: Scripts | Status: current.

Debug script to investigate blatant_tech divergence.
Traces all decision points to find paths to CORD, NBIS, SOXS.

UPDATED STRATEGY (Jan 2026):
- Branch 1: GDX RSI(7) < 70 -> Metals group; else -> CORD
- Branch 2: CRWV RSI(10) < 80 AND > 30 -> select-bottom 1 [NBIS, APLD, BE]; else -> CORD
- Branch 3: SOXL complex logic -> SOXS path
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

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
from the_alchemiser.shared.value_objects.symbol import Symbol
from indicators.indicators import TechnicalIndicators


def get_prices_for_symbol(adapter: CachedMarketDataAdapter, symbol: str) -> pd.Series:
    """Get price series for a symbol."""
    bars = adapter.get_bars(Symbol(symbol), "1Y", "1D")
    if not bars:
        print(f"      WARNING: No data for {symbol}!")
        return pd.Series(dtype=float)
    return pd.Series([float(b.close) for b in bars])


def safe_rsi(prices: pd.Series, window: int) -> float | None:
    """Calculate RSI safely, returning None if data is insufficient."""
    if len(prices) == 0:
        return None
    rsi = TechnicalIndicators.rsi(prices, window=window)
    if len(rsi) == 0:
        return None
    return float(rsi.iloc[-1])


def print_section(title: str) -> None:
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def print_condition(name: str, value: float, threshold: float, operator: str, result: bool) -> None:
    """Print a condition evaluation."""
    symbol = "✓" if result else "✗"
    print(f"  [{symbol}] {name}: {value:.4f} {operator} {threshold} = {result}")


def main() -> None:
    """Debug blatant_tech divergence by tracing all decision paths."""
    print_section("BLATANT_TECH DIVERGENCE DEBUG (UPDATED STRATEGY)")
    print("\nExpected (Composer): 33% CORD, 33% NBIS, 33% SOXS")
    print("Actual (Our system): 66% CORD, 33% SOXS")
    print("\nThe strategy has 3 equal-weighted branches:")
    print("  Branch 1: GDX RSI(7) logic  -> should give CORD (via else)")
    print("  Branch 2: CRWV RSI(10) logic -> should give NBIS")
    print("  Branch 3: SOXL complex      -> should give SOXS")
    
    # Initialize S3 store for direct reads
    store = MarketDataStore()
    
    # Check what symbols we have in S3
    print_section("S3 DATA CHECK")
    critical_symbols = ["GDX", "CRWV", "NBIS", "APLD", "BE", "CORD", "SOXL"]
    for sym in critical_symbols:
        try:
            df = store.read_symbol_data(sym)
            if df is not None and len(df) > 0:
                print(f"  {sym}: {len(df)} rows, {df.index.min().date()} to {df.index.max().date()}")
            else:
                print(f"  {sym}: NO DATA IN S3!")
        except Exception as e:
            print(f"  {sym}: ERROR - {e}")
    
    # Initialize adapter
    adapter = CachedMarketDataAdapter(append_live_bar=True)
    
    # =========================================================================
    # BRANCH 1: GDX RSI PATH
    # =========================================================================
    print_section("BRANCH 1: GDX RSI PATH")
    print("""
Decision tree:
  if (rsi GDX 7) < 70:
    [Metals Group]
    if (rsi GDX 7) > 40:
      -> select-top 2 by RSI(10) from [CPXR, AGQ, GDXU]  (metal ETFs)
    else:
      -> select-top 1 by RSI(10) from [NBIS, APLD, BE]  (HIGHEST RSI wins)
  else:
    -> CORD
""")
    
    gdx_prices = get_prices_for_symbol(adapter, "GDX")
    gdx_rsi_7 = TechnicalIndicators.rsi(gdx_prices, window=7).iloc[-1]
    
    print(f"GDX RSI(7) = {gdx_rsi_7:.4f}")
    cond1_lt_70 = gdx_rsi_7 < 70
    print_condition("GDX RSI(7) < 70", gdx_rsi_7, 70, "<", cond1_lt_70)
    
    if cond1_lt_70:
        print("\n  -> Enters Metals Group")
        cond1_gt_40 = gdx_rsi_7 > 40
        print_condition("GDX RSI(7) > 40", gdx_rsi_7, 40, ">", cond1_gt_40)
        
        if cond1_gt_40:
            print("\n  -> Selects TOP 2 by RSI(10) from [CPXR, AGQ, GDXU]")
            for sym in ["CPXR", "AGQ", "GDXU"]:
                try:
                    prices = get_prices_for_symbol(adapter, sym)
                    rsi_10 = TechnicalIndicators.rsi(prices, window=10).iloc[-1]
                    print(f"      {sym} RSI(10) = {rsi_10:.4f}")
                except Exception as e:
                    print(f"      {sym}: ERROR - {e}")
            print("  BRANCH 1 RESULT: Two of [CPXR, AGQ, GDXU] (highest RSI)")
        else:
            print("\n  -> Selects TOP 1 by RSI(10) from [NBIS, APLD, BE] (HIGHEST wins)")
            rsi_values: dict[str, float] = {}
            for sym in ["NBIS", "APLD", "BE"]:
                try:
                    prices = get_prices_for_symbol(adapter, sym)
                    rsi_10 = TechnicalIndicators.rsi(prices, window=10).iloc[-1]
                    rsi_values[sym] = rsi_10
                    print(f"      {sym} RSI(10) = {rsi_10:.4f}")
                except Exception as e:
                    print(f"      {sym}: ERROR - {e}")
            if rsi_values:
                winner = max(rsi_values, key=rsi_values.get)  # type: ignore[arg-type]
                print(f"  BRANCH 1 RESULT: {winner} (highest RSI)")
    else:
        print("\n  -> Takes ELSE branch")
        print("  BRANCH 1 RESULT: CORD")
    
    # =========================================================================
    # BRANCH 2: CRWV RSI PATH (UPDATED - was APLD)
    # =========================================================================
    print_section("BRANCH 2: CRWV RSI PATH")
    print("""
Decision tree:
  if (rsi CRWV 10) < 80:
    if (rsi CRWV 10) > 30:
      -> select-bottom 1 by RSI(10) from [NBIS, APLD, BE]  (LOWEST RSI wins)
    else:
      -> Metals group with CORD + metals
  else:
    -> CORD
""")
    
    crwv_prices = get_prices_for_symbol(adapter, "CRWV")
    crwv_rsi_10 = safe_rsi(crwv_prices, window=10)
    
    if crwv_rsi_10 is None:
        print("  *** ERROR: NO DATA FOR CRWV! ***")
        print("  This is likely causing the divergence!")
        print("  Need to add CRWV to the symbol universe.")
        print("\n  BRANCH 2 RESULT: UNKNOWN (missing data)")
        cond2_lt_80 = False  # Default for later analysis
        cond2_gt_30 = False
    else:
        print(f"CRWV RSI(10) = {crwv_rsi_10:.4f}")
        
        cond2_lt_80 = crwv_rsi_10 < 80
        print_condition("CRWV RSI(10) < 80", crwv_rsi_10, 80, "<", cond2_lt_80)
        
        if cond2_lt_80:
            print("\n  -> Enters inner branch")
            cond2_gt_30 = crwv_rsi_10 > 30
            print_condition("CRWV RSI(10) > 30", crwv_rsi_10, 30, ">", cond2_gt_30)
            
            if cond2_gt_30:
                print("\n  -> Selects BOTTOM 1 by RSI(10) from [NBIS, APLD, BE] (LOWEST wins)")
                print("     NOTE: CORD is NOT in this filter!")
                rsi_values = {}
                for sym in ["NBIS", "APLD", "BE"]:
                    try:
                        prices = get_prices_for_symbol(adapter, sym)
                        rsi_10 = safe_rsi(prices, window=10)
                        if rsi_10 is not None:
                            rsi_values[sym] = rsi_10
                            print(f"      {sym} RSI(10) = {rsi_10:.4f}")
                        else:
                            print(f"      {sym}: NO DATA")
                    except Exception as e:
                        print(f"      {sym}: ERROR - {e}")
                if rsi_values:
                    winner = min(rsi_values, key=rsi_values.get)  # type: ignore[arg-type]
                    print(f"  BRANCH 2 RESULT: {winner} (lowest RSI)")
            else:
                print("\n  -> Takes ELSE branch (CRWV RSI(10) <= 30)")
                print("  -> Goes to Metals group with CORD")
                print("  BRANCH 2 RESULT: CORD + metals (complex)")
        else:
            print("\n  -> Takes ELSE branch (CRWV RSI(10) >= 80)")
            print("  BRANCH 2 RESULT: CORD")
    
    # =========================================================================
    # BRANCH 3: SOXL COMPLEX PATH (unchanged)
    # =========================================================================
    print_section("BRANCH 3: SOXL COMPLEX PATH")
    print("""
Decision tree (simplified - showing path to SOXS):
  if (max-drawdown SOXL 60) >= 50:
    [Complex TQQQ analysis...]
  else:
    if (rsi SOXL 32) <= 62.1995:
      if (stdev-return SOXL 105) <= 4.9226:
        -> SOXL
      else:
        if (rsi SOXL 30) >= 57.49:
          if (stdev-return SOXL 30) >= 5.4135:
            -> SOXS  <-- This is likely our path
          else:
            -> select-top 2 cumret(21) [SOXL, SPXL, TQQQ]
        else:
          [more branches...]
    else:
      if (rsi SOXL 32) >= 50:
        -> SOXS  <-- Alternative path to SOXS
      else:
        -> select-top 3...
""")
    
    soxl_prices = get_prices_for_symbol(adapter, "SOXL")
    soxl_mdd_60 = TechnicalIndicators.max_drawdown(soxl_prices, window=60).iloc[-1]
    soxl_rsi_32 = TechnicalIndicators.rsi(soxl_prices, window=32).iloc[-1]
    soxl_rsi_30 = TechnicalIndicators.rsi(soxl_prices, window=30).iloc[-1]
    soxl_stdev_105 = TechnicalIndicators.stdev_return(soxl_prices, window=105).iloc[-1]
    soxl_stdev_30 = TechnicalIndicators.stdev_return(soxl_prices, window=30).iloc[-1]
    
    print(f"SOXL max-drawdown(60) = {soxl_mdd_60:.4f}")
    print(f"SOXL RSI(32) = {soxl_rsi_32:.4f}")
    print(f"SOXL RSI(30) = {soxl_rsi_30:.4f}")
    print(f"SOXL stdev-return(105) = {soxl_stdev_105:.4f}")
    print(f"SOXL stdev-return(30) = {soxl_stdev_30:.4f}")
    
    cond3_mdd_gte_50 = soxl_mdd_60 >= 50
    print_condition("SOXL max-drawdown(60) >= 50", soxl_mdd_60, 50, ">=", cond3_mdd_gte_50)
    
    if not cond3_mdd_gte_50:
        print("\n  -> Takes lower branch (drawdown < 50)")
        cond3_rsi_lte_62 = soxl_rsi_32 <= 62.1995
        print_condition("SOXL RSI(32) <= 62.1995", soxl_rsi_32, 62.1995, "<=", cond3_rsi_lte_62)
        
        if cond3_rsi_lte_62:
            cond3_stdev_lte_49 = soxl_stdev_105 <= 4.9226
            print_condition("SOXL stdev-return(105) <= 4.9226", soxl_stdev_105, 4.9226, "<=", cond3_stdev_lte_49)
            
            if not cond3_stdev_lte_49:
                cond3_rsi30_gte_57 = soxl_rsi_30 >= 57.49
                print_condition("SOXL RSI(30) >= 57.49", soxl_rsi_30, 57.49, ">=", cond3_rsi30_gte_57)
                
                if cond3_rsi30_gte_57:
                    cond3_stdev30_gte_54 = soxl_stdev_30 >= 5.4135
                    print_condition("SOXL stdev-return(30) >= 5.4135", soxl_stdev_30, 5.4135, ">=", cond3_stdev30_gte_54)
                    
                    if cond3_stdev30_gte_54:
                        print("  BRANCH 3 RESULT: SOXS ✓")
                    else:
                        print("  BRANCH 3 RESULT: select-top 2 from [SOXL, SPXL, TQQQ]")
                else:
                    print("  -> RSI(30) < 57.49, checking cumulative return path...")
                    soxl_cumret_32 = TechnicalIndicators.cumulative_return(soxl_prices, window=32).iloc[-1]
                    print(f"  SOXL cumulative-return(32) = {soxl_cumret_32:.4f}")
                    if soxl_cumret_32 <= -12:
                        print("  BRANCH 3 RESULT: SOXL")
                    else:
                        soxl_mdd_250 = TechnicalIndicators.max_drawdown(soxl_prices, window=250).iloc[-1]
                        print(f"  SOXL max-drawdown(250) = {soxl_mdd_250:.4f}")
                        if soxl_mdd_250 <= 71:
                            print("  BRANCH 3 RESULT: SOXS")
                        else:
                            print("  BRANCH 3 RESULT: SOXL")
            else:
                print("  BRANCH 3 RESULT: SOXL")
        else:
            cond3_rsi32_gte_50 = soxl_rsi_32 >= 50
            print_condition("SOXL RSI(32) >= 50", soxl_rsi_32, 50, ">=", cond3_rsi32_gte_50)
            if cond3_rsi32_gte_50:
                print("  BRANCH 3 RESULT: SOXS ✓")
            else:
                print("  BRANCH 3 RESULT: select-top 3...")
    else:
        print("  -> Takes upper branch (drawdown >= 50)")
        print("  [Complex TQQQ analysis - skipped for brevity]")
    
    # =========================================================================
    # T-1 ANALYSIS (What would values be without today's live bar?)
    # =========================================================================
    print_section("T-1 ANALYSIS (Without Today's Live Bar)")
    print("Checking if yesterday's data would give different results...")
    
    # Re-fetch without live bar
    adapter_no_live = CachedMarketDataAdapter(append_live_bar=False)
    
    gdx_prices_t1 = get_prices_for_symbol(adapter_no_live, "GDX")
    crwv_prices_t1 = get_prices_for_symbol(adapter_no_live, "CRWV")
    
    gdx_rsi_7_t1 = safe_rsi(gdx_prices_t1, window=7)
    crwv_rsi_10_t1 = safe_rsi(crwv_prices_t1, window=10)
    
    print(f"\nT-1 Values (S3 historical only, no live bar):")
    if gdx_rsi_7_t1 is not None:
        print(f"  GDX  RSI(7):   {gdx_rsi_7_t1:.4f}  (vs live: {gdx_rsi_7:.4f}, diff: {gdx_rsi_7 - gdx_rsi_7_t1:+.4f})")
    else:
        print(f"  GDX  RSI(7):   NO DATA")
    if crwv_rsi_10_t1 is not None and crwv_rsi_10 is not None:
        print(f"  CRWV RSI(10):  {crwv_rsi_10_t1:.4f}  (vs live: {crwv_rsi_10:.4f}, diff: {crwv_rsi_10 - crwv_rsi_10_t1:+.4f})")
    else:
        print(f"  CRWV RSI(10):  NO DATA (symbol missing from universe!)")
    
    # =========================================================================
    # RSI(10) FILTER ANALYSIS FOR BRANCH 2
    # =========================================================================
    print_section("RSI(10) FILTER ANALYSIS FOR BRANCH 2")
    print("For paths that select-bottom 1 by RSI(10) from [NBIS, APLD, BE]:")
    print("(Lower RSI = more oversold = selected)")
    print("NOTE: CORD is NOT in this list!")
    
    rsi_10_live: dict[str, float] = {}
    rsi_10_t1: dict[str, float] = {}
    
    for sym in ["NBIS", "APLD", "BE"]:
        try:
            prices_live = get_prices_for_symbol(adapter, sym)
            prices_t1 = get_prices_for_symbol(adapter_no_live, sym)
            
            rsi_live = safe_rsi(prices_live, window=10)
            rsi_t1 = safe_rsi(prices_t1, window=10)
            
            if rsi_live is not None:
                rsi_10_live[sym] = rsi_live
            if rsi_t1 is not None:
                rsi_10_t1[sym] = rsi_t1
            
            print(f"\n  {sym}:")
            if rsi_live is not None:
                print(f"    RSI(10) with live bar: {rsi_live:.4f}")
            else:
                print(f"    RSI(10) with live bar: NO DATA")
            if rsi_t1 is not None:
                print(f"    RSI(10) T-1 only:      {rsi_t1:.4f}")
            else:
                print(f"    RSI(10) T-1 only:      NO DATA")
            if rsi_live is not None and rsi_t1 is not None:
                print(f"    Difference:            {rsi_live - rsi_t1:+.4f}")
        except Exception as e:
            print(f"\n  {sym}: ERROR - {e}")
    
    print("\nRanking by RSI(10) - LOWEST wins (select-bottom 1):")
    if rsi_10_live:
        sorted_live = sorted(rsi_10_live.items(), key=lambda x: x[1])
        sorted_t1 = sorted(rsi_10_t1.items(), key=lambda x: x[1])
        print(f"  With live bar: {' < '.join(f'{s}({v:.2f})' for s, v in sorted_live)}")
        print(f"  T-1 only:      {' < '.join(f'{s}({v:.2f})' for s, v in sorted_t1)}")
        print(f"\n  Winner with live bar: {sorted_live[0][0]}")
        print(f"  Winner T-1:           {sorted_t1[0][0]}")
    
    # =========================================================================
    # DIAGNOSIS
    # =========================================================================
    print_section("DIAGNOSIS")
    
    print("\nTo get expected output [CORD, NBIS, SOXS]:")
    print("-" * 60)
    
    print("\n1. BRANCH 1 should output CORD:")
    print(f"   Current: GDX RSI(7) = {gdx_rsi_7:.4f}")
    if gdx_rsi_7 >= 70:
        print("   ✓ GDX RSI(7) >= 70, so ELSE branch -> CORD")
    else:
        print(f"   ✗ GDX RSI(7) < 70, enters Metals group")
        if gdx_rsi_7 > 40:
            print("   ✗ And GDX RSI(7) > 40, so selects metal ETFs, not CORD")
            print("   FIX NEEDED: GDX RSI needs to be >= 70")
        else:
            print("   ✗ GDX RSI(7) <= 40, selects from [NBIS, APLD, BE], not CORD")
            print("   FIX NEEDED: GDX RSI needs to be >= 70")
    
    print("\n2. BRANCH 2 should output NBIS:")
    if crwv_rsi_10 is None:
        print("   *** CRWV DATA MISSING ***")
        print("   Cannot evaluate branch - need to add CRWV to symbol universe!")
        print("   This is likely causing the strategy to fail or default to CORD")
    else:
        print(f"   Current: CRWV RSI(10) = {crwv_rsi_10:.4f}")
        
        if crwv_rsi_10 >= 80:
            print("   ✗ CRWV RSI(10) >= 80, takes ELSE -> CORD instead of NBIS")
            print("   FIX NEEDED: CRWV RSI(10) needs to be < 80")
        elif crwv_rsi_10 <= 30:
            print("   ✗ CRWV RSI(10) <= 30, takes Metals branch with CORD")
            print("   FIX NEEDED: CRWV RSI(10) needs to be > 30")
        else:
            print("   ✓ Conditions met to enter filter (30 < RSI < 80)")
            if rsi_10_live:
                sorted_rsi = sorted(rsi_10_live.items(), key=lambda x: x[1])
                winner = sorted_rsi[0][0]
                if winner == "NBIS":
                    print(f"   ✓ NBIS has lowest RSI(10) = {rsi_10_live['NBIS']:.4f}, so NBIS selected")
                else:
                    print(f"   ✗ {winner} has lowest RSI(10) = {sorted_rsi[0][1]:.4f}")
                    print(f"   ✗ NBIS RSI(10) = {rsi_10_live.get('NBIS', 0):.4f}")
                    print(f"   FIX NEEDED: NBIS needs lower RSI(10) than {winner}")
    
    print("\n3. BRANCH 3 should output SOXS:")
    print("   [Already traced above]")
    
    # =========================================================================
    # SENSITIVITY ANALYSIS
    # =========================================================================
    print_section("SENSITIVITY ANALYSIS")
    print("What price changes would flip the decisions?")
    
    # For Branch 1
    print("\nBranch 1 - GDX RSI(7):")
    print(f"  Current: {gdx_rsi_7:.4f}")
    print(f"  Threshold: 70")
    print(f"  Margin: {70 - gdx_rsi_7:.4f} (positive = room before taking metals path)")
    
    # For Branch 2
    print("\nBranch 2 - CRWV RSI(10):")
    print(f"  Current: {crwv_rsi_10:.4f}")
    print(f"  Upper threshold: 80 (must be below)")
    print(f"  Lower threshold: 30 (must be above)")
    print(f"  Upper margin: {80 - crwv_rsi_10:.4f} (positive = room before CORD)")
    print(f"  Lower margin: {crwv_rsi_10 - 30:.4f} (positive = room before metals branch)")


if __name__ == "__main__":
    main()
