#!/usr/bin/env python3
"""Business Unit: diagnostics | Status: current.

Diagnostic script to analyze the top-level filter ranking in beam_chain.

The strategy structure is:
  weight-equal
    filter (stdev-return {:window 10}) (select-top 8)
      [10 groups]

This means we rank all 10 groups by their stdev-return(10) and select the TOP 8.
If our stdev calculation differs from Composer's, we might include/exclude
different groups.

The groups that produce KMLM and IEF might be in the bottom 2 (excluded)
in Composer but included in our calculation.

Usage:
    poetry run python scripts/diagnose_filter_ranking.py
"""

from __future__ import annotations

import os
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

# Add project paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "functions", "strategy_worker"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "layers", "shared"))

os.environ["MARKET_DATA_BUCKET"] = "alchemiser-dev-market-data"
os.environ.setdefault("AWS_REGION", "ap-southeast-2")
os.environ["LOG_LEVEL"] = "WARNING"

import uuid
from the_alchemiser.shared.data_v2.cached_market_data_adapter import CachedMarketDataAdapter
from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore
from the_alchemiser.shared.schemas.indicator_request import IndicatorRequest
from indicators.indicator_service import IndicatorService


# The 10 groups from beam_chain.clj based on the image
# Each group needs to be evaluated to get a "representative" stdev-return(10)
# But actually, the filter operates on the GROUP as a whole...
# 
# Wait - how does stdev-return work on a GROUP? 
# The filter likely computes stdev-return(10) on the GROUP'S output asset.
# But that requires evaluating the group first to know which asset it selects.
#
# Let's think about this differently - maybe the filter evaluates each group
# to get its selected asset(s), then ranks by stdev-return of those assets.

GROUPS = [
    "Beam Filter: CORP, BTAL 28/6",
    "Beam Filter: GLD, CORP 32/5.6", 
    "Beam Filter: GLD, QQQ 319/54",
    "Beam Filter: AIQ, ICLN, CIBR 64/9",
    "Beam Filter: SOXX, KMLM, HYG 156/21",  # <-- This produces KMLM
    "Beam Filter: TMV, GLD 103/10",
    "Beam Filter: GLD, SOXX, BTAL 124/17.5",
    "Beam Filter: HYG, BTAL 28/9.5",
    "Beam Filter: BITO, IEF 85/23",  # <-- This might produce IEF
    "Beam Filter: XLK, XLP, XLE 75/4.3",
]


def get_stdev_return(indicator_service: IndicatorService, symbol: str, window: int = 10) -> float:
    """Get stdev-return for a symbol."""
    request = IndicatorRequest(
        request_id=str(uuid.uuid4()),
        symbol=symbol,
        indicator_type="stdev_return",
        parameters={"window": window},
        correlation_id="filter-trace",
    )
    result = indicator_service.get_indicator(request)
    return float(result.metadata.get("value", 0.0))


def main() -> None:
    """Analyze filter ranking."""
    print("=" * 80)
    print("FILTER RANKING DIAGNOSTIC: select-top 8 by stdev-return(10)")
    print("=" * 80)
    print()
    
    # Initialize services
    store = MarketDataStore()
    adapter = CachedMarketDataAdapter(market_data_store=store)
    indicator_service = IndicatorService(market_data_service=adapter)
    
    # First, let's understand what assets each group COULD produce
    # Based on group names, the primary assets are:
    GROUP_PRIMARY_ASSETS = {
        "Beam Filter: CORP, BTAL 28/6": ["CORP", "BTAL", "BIL"],
        "Beam Filter: GLD, CORP 32/5.6": ["GLD", "CORP", "BIL"],
        "Beam Filter: GLD, QQQ 319/54": ["GLD", "GDXU", "TQQQ", "BIL"],
        "Beam Filter: AIQ, ICLN, CIBR 64/9": ["AIQ", "ICLN", "CIBR", "BIL"],
        "Beam Filter: SOXX, KMLM, HYG 156/21": ["SOXL", "KMLM", "HYG", "BIL"],
        "Beam Filter: TMV, GLD 103/10": ["TMV", "GLD", "BIL"],
        "Beam Filter: GLD, SOXX, BTAL 124/17.5": ["UGL", "BTAL", "BIL"],
        "Beam Filter: HYG, BTAL 28/9.5": ["HYG", "BTAL", "BIL"],
        "Beam Filter: BITO, IEF 85/23": ["BITO", "IEF", "BIL"],
        "Beam Filter: XLK, XLP, XLE 75/4.3": ["XLK", "XLP", "XLE", "BIL"],
    }
    
    print("STEP 1: Understanding how filter works on groups")
    print("-" * 80)
    print("""
The filter '(stdev-return {:window 10}) (select-top 8)' needs to rank 10 groups.

QUESTION: What does stdev-return(10) mean for a GROUP?

Option A: The filter evaluates each group first, gets the selected asset,
          then computes stdev-return(10) of that asset to rank.
          
Option B: The filter uses some aggregate of all possible assets in the group.

Option C: The filter uses a "representative" asset (first listed? most common?).

Let's compute stdev-return(10) for each group's potential assets and see patterns.
""")
    
    print()
    print("STEP 2: Computing stdev-return(10) for all relevant assets")
    print("-" * 80)
    
    # Collect all unique assets
    all_assets = set()
    for assets in GROUP_PRIMARY_ASSETS.values():
        all_assets.update(assets)
    
    asset_stdev: dict[str, float] = {}
    for asset in sorted(all_assets):
        try:
            stdev = get_stdev_return(indicator_service, asset, 10)
            asset_stdev[asset] = stdev
            print(f"  {asset:<8}: stdev-return(10) = {stdev:.6f}%")
        except Exception as e:
            print(f"  {asset:<8}: ERROR - {e}")
            asset_stdev[asset] = 0.0
    
    print()
    print("STEP 3: Ranking groups by different interpretations")
    print("=" * 80)
    
    # Interpretation 1: Use first asset in group name
    print("\n[Interpretation 1] Rank by FIRST asset mentioned in group name:")
    print("-" * 80)
    
    first_asset_ranking = []
    for group in GROUPS:
        # Extract first asset from group name
        parts = group.replace("Beam Filter: ", "").split(",")[0].strip()
        first_asset = parts.split()[0] if parts else "BIL"
        stdev = asset_stdev.get(first_asset, 0.0)
        first_asset_ranking.append((group, first_asset, stdev))
    
    first_asset_ranking.sort(key=lambda x: x[2], reverse=True)  # TOP = highest
    
    for i, (group, asset, stdev) in enumerate(first_asset_ranking, 1):
        included = "✓ INCLUDED" if i <= 8 else "✗ EXCLUDED"
        kmlm_marker = " <-- KMLM GROUP" if "KMLM" in group else ""
        ief_marker = " <-- IEF GROUP" if "IEF" in group else ""
        print(f"  {i:2}. [{stdev:8.6f}%] {group:<45} ({asset}){kmlm_marker}{ief_marker} {included}")
    
    print()
    
    # Interpretation 2: Use maximum stdev of group's assets
    print("\n[Interpretation 2] Rank by MAX stdev of group's assets:")
    print("-" * 80)
    
    max_stdev_ranking = []
    for group in GROUPS:
        assets = GROUP_PRIMARY_ASSETS.get(group, ["BIL"])
        max_stdev = max(asset_stdev.get(a, 0.0) for a in assets)
        max_asset = max(assets, key=lambda a: asset_stdev.get(a, 0.0))
        max_stdev_ranking.append((group, max_asset, max_stdev))
    
    max_stdev_ranking.sort(key=lambda x: x[2], reverse=True)
    
    for i, (group, asset, stdev) in enumerate(max_stdev_ranking, 1):
        included = "✓ INCLUDED" if i <= 8 else "✗ EXCLUDED"
        kmlm_marker = " <-- KMLM GROUP" if "KMLM" in group else ""
        ief_marker = " <-- IEF GROUP" if "IEF" in group else ""
        print(f"  {i:2}. [{stdev:8.6f}%] {group:<45} ({asset}){kmlm_marker}{ief_marker} {included}")
    
    print()
    
    # Interpretation 3: Use minimum stdev (most stable = top?)
    print("\n[Interpretation 3] Rank by MIN stdev of group's assets (inverse - lowest stdev = top):")
    print("-" * 80)
    
    min_stdev_ranking = []
    for group in GROUPS:
        assets = GROUP_PRIMARY_ASSETS.get(group, ["BIL"])
        min_stdev = min(asset_stdev.get(a, 0.0) for a in assets)
        min_asset = min(assets, key=lambda a: asset_stdev.get(a, 0.0))
        min_stdev_ranking.append((group, min_asset, min_stdev))
    
    # For "select-top" with low stdev meaning stable, TOP might mean lowest stdev
    min_stdev_ranking.sort(key=lambda x: x[2], reverse=True)  # Still highest first for "top"
    
    for i, (group, asset, stdev) in enumerate(min_stdev_ranking, 1):
        included = "✓ INCLUDED" if i <= 8 else "✗ EXCLUDED"
        kmlm_marker = " <-- KMLM GROUP" if "KMLM" in group else ""
        ief_marker = " <-- IEF GROUP" if "IEF" in group else ""
        print(f"  {i:2}. [{stdev:8.6f}%] {group:<45} ({asset}){kmlm_marker}{ief_marker} {included}")
    
    print()
    print("=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    print("""
If Composer's select-top 8 excludes the "SOXX, KMLM, HYG" group and/or 
the "BITO, IEF" group, but our calculation includes them, that would 
explain why we get KMLM/IEF allocations but Composer gets 25% BIL instead.

The key question: which interpretation does Composer use for ranking groups?

Also note: 'select-top 8' with 10 groups means 2 groups are EXCLUDED.
If our stdev calculation is slightly different, the ranking order changes.
""")
    
    # Let's also check what we actually output
    print()
    print("=" * 80)
    print("STEP 4: Check actual outputs for problematic groups")
    print("=" * 80)
    print()
    
    # For KMLM group, what asset gets selected?
    print("Evaluating 'Beam Filter: SOXX, KMLM, HYG 156/21' group decision...")
    
    def get_indicator(symbol: str, ind_type: str, window: int) -> float:
        request = IndicatorRequest(
            request_id=str(uuid.uuid4()),
            symbol=symbol,
            indicator_type=ind_type,
            parameters={"window": window},
            correlation_id="trace",
        )
        result = indicator_service.get_indicator(request)
        return float(result.metadata.get("value", 0.0))
    
    # Trace the KMLM group decision
    hyg_mar_90 = get_indicator("HYG", "moving_average_return", 90)
    xlf_mar_60 = get_indicator("XLF", "moving_average_return", 60)
    print(f"  L1: HYG MAR(90)={hyg_mar_90:.6f}% vs XLF MAR(60)={xlf_mar_60:.6f}%")
    print(f"      HYG > XLF? {hyg_mar_90 > xlf_mar_60} → {'TRUE branch' if hyg_mar_90 > xlf_mar_60 else 'FALSE branch'}")
    
    # Continue down the selected branch
    lqd_stdev_20 = get_indicator("LQD", "stdev_return", 20)
    hyg_stdev_30 = get_indicator("HYG", "stdev_return", 30)
    print(f"  L2: LQD stdev(20)={lqd_stdev_20:.6f}% vs HYG stdev(30)={hyg_stdev_30:.6f}%")
    print(f"      LQD > HYG? {lqd_stdev_20 > hyg_stdev_30} → {'TRUE' if lqd_stdev_20 > hyg_stdev_30 else 'FALSE'}")
    
    qqq_cum_15 = get_indicator("QQQ", "cumulative_return", 15)
    lqd_cum_30 = get_indicator("LQD", "cumulative_return", 30)
    print(f"  L3: QQQ cumret(15)={qqq_cum_15:.4f}% vs LQD cumret(30)={lqd_cum_30:.4f}%")
    print(f"      QQQ > LQD? {qqq_cum_15 > lqd_cum_30} → {'TRUE → Continue to RSI' if qqq_cum_15 > lqd_cum_30 else 'FALSE → BIL'}")
    
    if qqq_cum_15 > lqd_cum_30:
        iwm_rsi_5 = get_indicator("IWM", "rsi", 5)
        dia_rsi_10 = get_indicator("DIA", "rsi", 10)
        print(f"  L4: IWM RSI(5)={iwm_rsi_5:.4f} vs DIA RSI(10)={dia_rsi_10:.4f}")
        print(f"      IWM > DIA? {iwm_rsi_5 > dia_rsi_10} → {'TRUE → KMLM' if iwm_rsi_5 > dia_rsi_10 else 'FALSE → BIL'}")
        
        selected = "KMLM" if iwm_rsi_5 > dia_rsi_10 else "BIL"
    else:
        selected = "BIL"
    
    print()
    print(f"  → This group selects: {selected}")
    print(f"  → stdev-return(10) of {selected}: {asset_stdev.get(selected, 0.0):.6f}%")
    
    print()
    print("If this group gets EXCLUDED by the filter, we wouldn't see KMLM in output.")
    print("If INCLUDED, the group contributes 1/8 = 12.5% to weight-equal.")


if __name__ == "__main__":
    main()
