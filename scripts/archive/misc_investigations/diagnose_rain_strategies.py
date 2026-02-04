#!/usr/bin/env python3
"""Business Unit: diagnostic | Status: current.

Investigate Rain strategies signal discrepancies for 2026-01-14.

Discrepancies:
- rains_concise_em: We have EDZ, live signal has XLF
- rains_em_dancer: We have EDZ YANG TLT, live signal has EDZ VBF

Both strategies use RSI for decision branching and `select-bottom 1` with RSI
for choosing from a basket of safe sectors/bonds.

Usage:
    poetry run python scripts/diagnose_rain_strategies.py
"""

from __future__ import annotations

import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd

# Set default bucket before importing modules
os.environ.setdefault("MARKET_DATA_BUCKET", "alchemiser-prod-market-data")

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "layers" / "shared"))
sys.path.insert(0, str(project_root / "functions" / "strategy_worker"))

from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)

# Analysis date from validation CSV
ANALYSIS_DATE = datetime(2026, 1, 14, tzinfo=UTC)


def compute_rsi(prices: pd.Series, window: int = 14) -> pd.Series:
    """Compute RSI using Wilder's smoothing method."""
    if len(prices) < window:
        return pd.Series([50.0] * len(prices), index=prices.index)

    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    alpha = 1.0 / window
    avg_gain = gain.ewm(alpha=alpha, adjust=False).mean()
    avg_loss = loss.ewm(alpha=alpha, adjust=False).mean()

    rs = avg_gain.divide(avg_loss, fill_value=0.0)
    rsi = 100 - (100 / (1 + rs))

    return rsi.fillna(50.0)


def fetch_prices(store: MarketDataStore, symbol: str, include_t0: bool) -> pd.Series | None:
    """Fetch closing prices from S3.

    Args:
        store: MarketDataStore instance
        symbol: Ticker symbol
        include_t0: If True, include ANALYSIS_DATE; if False, exclude it (T-1)

    Returns:
        Series of closing prices indexed by timestamp
    """
    df = store.read_symbol_data(symbol)
    if df is None or df.empty or "timestamp" not in df.columns:
        return None

    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.sort_values("timestamp")

    # Filter based on T-0 or T-1
    if include_t0:
        end_dt = datetime(
            ANALYSIS_DATE.year, ANALYSIS_DATE.month, ANALYSIS_DATE.day, 23, 59, 59, tzinfo=UTC
        )
    else:
        end_dt = ANALYSIS_DATE - timedelta(days=1)
        end_dt = datetime(end_dt.year, end_dt.month, end_dt.day, 23, 59, 59, tzinfo=UTC)

    start_dt = end_dt - timedelta(days=400)
    df = df[(df["timestamp"] >= start_dt) & (df["timestamp"] <= end_dt)]

    if df.empty:
        return None

    return pd.Series(df["close"].values, index=df["timestamp"])


def get_latest_rsi(prices: pd.Series | None, window: int) -> float | None:
    """Compute RSI and return latest value."""
    if prices is None or len(prices) < window:
        return None
    series = compute_rsi(prices, window)
    if len(series) > 0 and not pd.isna(series.iloc[-1]):
        return float(series.iloc[-1])
    return None


def diagnose_rains_concise_em(store: MarketDataStore) -> dict:
    """Diagnose rains_concise_em: We have EDZ, live signal has XLF.
    
    The strategy uses (filter (rsi {:window 10}) (select-bottom 1) on:
    TMF, CURE, DRN, ROM, VBF, EVN, BKT, PMM, XLF
    
    It also uses (filter (rsi {:window 6}) (select-bottom 1) on same assets.
    
    To get XLF in live, XLF must be the bottom RSI among these assets.
    """
    # Assets in the "Leveraged Sectors or Bonds" filter
    sector_assets = ["TMF", "CURE", "DRN", "ROM", "VBF", "EVN", "BKT", "PMM", "XLF"]
    
    t0_rsi_10 = {}
    t1_rsi_10 = {}
    t0_rsi_6 = {}
    t1_rsi_6 = {}
    
    for symbol in sector_assets:
        t0_prices = fetch_prices(store, symbol, include_t0=True)
        t1_prices = fetch_prices(store, symbol, include_t0=False)
        
        t0_rsi_10[symbol] = get_latest_rsi(t0_prices, 10)
        t1_rsi_10[symbol] = get_latest_rsi(t1_prices, 10)
        t0_rsi_6[symbol] = get_latest_rsi(t0_prices, 6)
        t1_rsi_6[symbol] = get_latest_rsi(t1_prices, 6)
    
    # Filter out None values and find bottom 1
    t0_rsi_10_valid = {k: v for k, v in t0_rsi_10.items() if v is not None}
    t1_rsi_10_valid = {k: v for k, v in t1_rsi_10.items() if v is not None}
    t0_rsi_6_valid = {k: v for k, v in t0_rsi_6.items() if v is not None}
    t1_rsi_6_valid = {k: v for k, v in t1_rsi_6.items() if v is not None}
    
    # Select bottom 1 (lowest RSI)
    t0_bottom_10 = min(t0_rsi_10_valid.items(), key=lambda x: x[1]) if t0_rsi_10_valid else (None, None)
    t1_bottom_10 = min(t1_rsi_10_valid.items(), key=lambda x: x[1]) if t1_rsi_10_valid else (None, None)
    t0_bottom_6 = min(t0_rsi_6_valid.items(), key=lambda x: x[1]) if t0_rsi_6_valid else (None, None)
    t1_bottom_6 = min(t1_rsi_6_valid.items(), key=lambda x: x[1]) if t1_rsi_6_valid else (None, None)
    
    return {
        "strategy": "rains_concise_em",
        "our_signal": "EDZ",
        "live_signal": "XLF",
        "rsi_10_ranking_t0": sorted(t0_rsi_10_valid.items(), key=lambda x: x[1]),
        "rsi_10_ranking_t1": sorted(t1_rsi_10_valid.items(), key=lambda x: x[1]),
        "rsi_6_ranking_t0": sorted(t0_rsi_6_valid.items(), key=lambda x: x[1]),
        "rsi_6_ranking_t1": sorted(t1_rsi_6_valid.items(), key=lambda x: x[1]),
        "t0_bottom_rsi10": t0_bottom_10,
        "t1_bottom_rsi10": t1_bottom_10,
        "t0_bottom_rsi6": t0_bottom_6,
        "t1_bottom_rsi6": t1_bottom_6,
    }


def diagnose_rains_em_dancer(store: MarketDataStore) -> dict:
    """Diagnose rains_em_dancer: We have EDZ YANG TLT, live signal has EDZ VBF.
    
    The 75% portion uses (filter (rsi {:window 10}) (select-bottom 1) on:
    BSV, TLT, LQD, VBF, XLP, UGE (Safe Sectors or Bonds)
    
    The 25% "dancer" portion uses cumulative-return ranking.
    
    Key difference: TLT in our signal vs VBF in live signal.
    """
    # Assets in the "Safe Sectors or Bonds" filter
    safe_assets = ["BSV", "TLT", "LQD", "VBF", "XLP", "UGE"]
    
    t0_rsi_10 = {}
    t1_rsi_10 = {}
    
    for symbol in safe_assets:
        t0_prices = fetch_prices(store, symbol, include_t0=True)
        t1_prices = fetch_prices(store, symbol, include_t0=False)
        
        t0_rsi_10[symbol] = get_latest_rsi(t0_prices, 10)
        t1_rsi_10[symbol] = get_latest_rsi(t1_prices, 10)
    
    # Filter out None values and find bottom 1
    t0_rsi_valid = {k: v for k, v in t0_rsi_10.items() if v is not None}
    t1_rsi_valid = {k: v for k, v in t1_rsi_10.items() if v is not None}
    
    # Select bottom 1 (lowest RSI)
    t0_bottom = min(t0_rsi_valid.items(), key=lambda x: x[1]) if t0_rsi_valid else (None, None)
    t1_bottom = min(t1_rsi_valid.items(), key=lambda x: x[1]) if t1_rsi_valid else (None, None)
    
    return {
        "strategy": "rains_em_dancer",
        "our_signal": "EDZ YANG TLT",
        "live_signal": "EDZ VBF",
        "key_difference": "TLT vs VBF in safe sectors selection",
        "rsi_10_ranking_t0": sorted(t0_rsi_valid.items(), key=lambda x: x[1]),
        "rsi_10_ranking_t1": sorted(t1_rsi_valid.items(), key=lambda x: x[1]),
        "t0_bottom": t0_bottom,
        "t1_bottom": t1_bottom,
    }


def diagnose_decision_path(store: MarketDataStore) -> dict:
    """Diagnose the RSI comparison decision path in rains_concise_em.
    
    The strategy has many RSI comparisons that determine if we reach
    the sector selection or go to EDZ directly. Key comparisons include:
    
    Entry checks:
    - (< (rsi "EEM" {:window 14}) 30) -> EDC
    - (> (rsi "EEM" {:window 10}) 80) -> EDZ
    - (> (current-price "SHV") (moving-average-price "SHV" {:window 50}))
    - (> (current-price "EEM") (moving-average-price "EEM" {:window 200}))
    
    Then many RSI-vs-RSI comparisons like:
    - (> (rsi "MMT" {:window 10}) (rsi "XLU" {:window 10}))
    - (> (rsi "PIM" {:window 10}) (rsi "BBH" {:window 10}))
    - etc.
    """
    # Key decision symbols
    decision_symbols = [
        ("EEM", 14), ("EEM", 10),
        ("MMT", 10), ("XLU", 10),
        ("PIM", 10), ("BBH", 10),
        ("MHD", 10), ("XLP", 10),
        ("IEI", 10), ("IWM", 15),
        ("IGIB", 10), ("DBE", 10),
        ("IEF", 10), ("DIA", 10),
    ]
    
    results = {}
    
    for symbol, window in decision_symbols:
        t0_prices = fetch_prices(store, symbol, include_t0=True)
        t1_prices = fetch_prices(store, symbol, include_t0=False)
        
        t0_rsi = get_latest_rsi(t0_prices, window)
        t1_rsi = get_latest_rsi(t1_prices, window)
        
        key = f"{symbol}_RSI{window}"
        results[key] = {
            "t0": round(t0_rsi, 2) if t0_rsi else None,
            "t1": round(t1_rsi, 2) if t1_rsi else None,
            "diff": round(t0_rsi - t1_rsi, 2) if t0_rsi and t1_rsi else None,
        }
    
    # Check MA price conditions
    for symbol, window in [("SHV", 50), ("EEM", 200)]:
        t0_prices = fetch_prices(store, symbol, include_t0=True)
        t1_prices = fetch_prices(store, symbol, include_t0=False)
        
        if t0_prices is not None and len(t0_prices) >= window:
            t0_current = float(t0_prices.iloc[-1])
            t0_ma = float(t0_prices.rolling(window).mean().iloc[-1])
            t0_above = t0_current > t0_ma
        else:
            t0_current, t0_ma, t0_above = None, None, None
            
        if t1_prices is not None and len(t1_prices) >= window:
            t1_current = float(t1_prices.iloc[-1])
            t1_ma = float(t1_prices.rolling(window).mean().iloc[-1])
            t1_above = t1_current > t1_ma
        else:
            t1_current, t1_ma, t1_above = None, None, None
        
        key = f"{symbol}_price>MA{window}"
        results[key] = {
            "t0": {"current": round(t0_current, 2) if t0_current else None, 
                   "ma": round(t0_ma, 2) if t0_ma else None,
                   "above": t0_above},
            "t1": {"current": round(t1_current, 2) if t1_current else None,
                   "ma": round(t1_ma, 2) if t1_ma else None,
                   "above": t1_above},
        }
    
    return results


def main() -> None:
    """Run diagnosis for Rain strategies."""
    print("=" * 100)
    print("DIAGNOSIS: Rain Strategies Signal Discrepancies")
    print("=" * 100)
    print(f"\n📅 Analysis date: {ANALYSIS_DATE.strftime('%Y-%m-%d')}")
    print("   T-0 = includes analysis date bar (use_live_bar=True)")
    print("   T-1 = excludes analysis date bar (use_live_bar=False)")
    print()

    store = MarketDataStore()
    
    # Diagnose rains_concise_em
    print("\n" + "=" * 100)
    print("📊 Strategy: rains_concise_em")
    print("   Discrepancy: We have EDZ, live signal has XLF")
    print("-" * 100)
    
    result_concise = diagnose_rains_concise_em(store)
    
    print("\n   Asset Selection: (filter (rsi {:window 10}) (select-bottom 1))")
    print("   Assets: TMF, CURE, DRN, ROM, VBF, EVN, BKT, PMM, XLF")
    print()
    print("   RSI(10) Rankings (lowest first = selected):")
    print("   T-0 (use_live_bar=True):")
    for i, (sym, rsi) in enumerate(result_concise["rsi_10_ranking_t0"][:5], 1):
        mark = "👈 SELECTED" if i == 1 else ""
        print(f"      {i}. {sym:6} RSI={rsi:6.2f} {mark}")
    print("   T-1 (use_live_bar=False):")
    for i, (sym, rsi) in enumerate(result_concise["rsi_10_ranking_t1"][:5], 1):
        mark = "👈 SELECTED" if i == 1 else ""
        print(f"      {i}. {sym:6} RSI={rsi:6.2f} {mark}")
    
    print()
    print("   RSI(6) Rankings (lowest first = selected):")
    print("   T-0 (use_live_bar=True):")
    for i, (sym, rsi) in enumerate(result_concise["rsi_6_ranking_t0"][:5], 1):
        mark = "👈 SELECTED" if i == 1 else ""
        print(f"      {i}. {sym:6} RSI={rsi:6.2f} {mark}")
    print("   T-1 (use_live_bar=False):")
    for i, (sym, rsi) in enumerate(result_concise["rsi_6_ranking_t1"][:5], 1):
        mark = "👈 SELECTED" if i == 1 else ""
        print(f"      {i}. {sym:6} RSI={rsi:6.2f} {mark}")
    
    # Check if T-0 matches live
    t0_win10 = result_concise["t0_bottom_rsi10"][0] if result_concise["t0_bottom_rsi10"][0] else ""
    t1_win10 = result_concise["t1_bottom_rsi10"][0] if result_concise["t1_bottom_rsi10"][0] else ""
    
    print()
    print(f"   Summary (RSI window 10):")
    print(f"      T-0 selects: {t0_win10}")
    print(f"      T-1 selects: {t1_win10}")
    print(f"      Live signal: XLF")
    
    if t0_win10 == "XLF":
        print("   ✅ T-0 (use_live_bar=True) MATCHES live signal")
    else:
        print(f"   ❌ T-0 does NOT match live signal (got {t0_win10}, expected XLF)")
        print("   → This may be a different issue (not just live bar timing)")
    
    # Diagnose rains_em_dancer
    print("\n" + "=" * 100)
    print("📊 Strategy: rains_em_dancer")
    print("   Discrepancy: We have EDZ YANG TLT, live signal has EDZ VBF")
    print("   Key difference: TLT vs VBF in safe sectors selection")
    print("-" * 100)
    
    result_dancer = diagnose_rains_em_dancer(store)
    
    print("\n   Safe Sectors Selection: (filter (rsi {:window 10}) (select-bottom 1))")
    print("   Assets: BSV, TLT, LQD, VBF, XLP, UGE")
    print()
    print("   RSI(10) Rankings (lowest first = selected):")
    print("   T-0 (use_live_bar=True):")
    for i, (sym, rsi) in enumerate(result_dancer["rsi_10_ranking_t0"], 1):
        mark = "👈 SELECTED" if i == 1 else ""
        print(f"      {i}. {sym:6} RSI={rsi:6.2f} {mark}")
    print("   T-1 (use_live_bar=False):")
    for i, (sym, rsi) in enumerate(result_dancer["rsi_10_ranking_t1"], 1):
        mark = "👈 SELECTED" if i == 1 else ""
        print(f"      {i}. {sym:6} RSI={rsi:6.2f} {mark}")
    
    t0_bottom = result_dancer["t0_bottom"][0] if result_dancer["t0_bottom"][0] else ""
    t1_bottom = result_dancer["t1_bottom"][0] if result_dancer["t1_bottom"][0] else ""
    
    print()
    print(f"   Summary:")
    print(f"      T-0 selects: {t0_bottom}")
    print(f"      T-1 selects: {t1_bottom}")
    print(f"      Live signal: VBF")
    
    if t0_bottom == "VBF":
        print("   ✅ T-0 (use_live_bar=True) MATCHES live signal")
    else:
        print(f"   ❌ T-0 does NOT match live signal (got {t0_bottom}, expected VBF)")
        print("   → This may be a different issue (not just live bar timing)")
    
    # Check decision path
    print("\n" + "=" * 100)
    print("📊 Decision Path Analysis")
    print("   Checking if the path to sector selection vs EDZ differs between T-0 and T-1")
    print("-" * 100)
    
    path_results = diagnose_decision_path(store)
    
    print("\n   RSI Comparisons (values that differ significantly may cause path divergence):")
    for key, vals in path_results.items():
        if "RSI" in key:
            t0_val = vals["t0"]
            t1_val = vals["t1"]
            diff = vals["diff"]
            if diff is not None and abs(diff) > 3:
                print(f"   🔥 {key:20} T-0={t0_val:6.2f}  T-1={t1_val:6.2f}  Δ={diff:+6.2f}")
            else:
                print(f"      {key:20} T-0={t0_val:6.2f}  T-1={t1_val:6.2f}  Δ={diff:+6.2f}")
    
    print("\n   Price vs MA Checks:")
    for key, vals in path_results.items():
        if "price>MA" in key:
            t0_above = vals["t0"]["above"] if vals["t0"]["above"] is not None else "?"
            t1_above = vals["t1"]["above"] if vals["t1"]["above"] is not None else "?"
            t0_curr = vals["t0"]["current"]
            t0_ma = vals["t0"]["ma"]
            t1_curr = vals["t1"]["current"]
            t1_ma = vals["t1"]["ma"]
            
            if t0_above != t1_above:
                print(f"   🔥 {key:20} T-0: {t0_curr}/{t0_ma} ({t0_above})  T-1: {t1_curr}/{t1_ma} ({t1_above})")
            else:
                print(f"      {key:20} T-0: {t0_curr}/{t0_ma} ({t0_above})  T-1: {t1_curr}/{t1_ma} ({t1_above})")
    
    # Summary
    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)
    
    live_bar_fixes = []
    other_issues = []
    
    if t0_win10 == "XLF":
        live_bar_fixes.append("rains_concise_em: XLF selection via RSI(10)")
    else:
        other_issues.append(f"rains_concise_em: T-0 got {t0_win10}, expected XLF - investigate further")
    
    if t0_bottom == "VBF":
        live_bar_fixes.append("rains_em_dancer: VBF selection via RSI(10)")
    else:
        other_issues.append(f"rains_em_dancer: T-0 got {t0_bottom}, expected VBF - investigate further")
    
    if live_bar_fixes:
        print("\n   ✅ Strategies fixed by use_live_bar=True:")
        for fix in live_bar_fixes:
            print(f"      - {fix}")
    
    if other_issues:
        print("\n   ⚠️ Strategies with different issues:")
        for issue in other_issues:
            print(f"      - {issue}")


if __name__ == "__main__":
    main()
