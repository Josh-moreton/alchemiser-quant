#!/usr/bin/env python3
"""Business Unit: Scripts | Status: current.

Debug script for rains_concise_em divergence analysis.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project paths
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "layers" / "shared"))
sys.path.insert(0, str(PROJECT_ROOT / "functions" / "strategy_worker"))

import os
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

os.environ.setdefault("MARKET_DATA_BUCKET", "alchemiser-dev-market-data")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

from datetime import datetime, timezone
from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore
from the_alchemiser.shared.data_v2.cached_market_data_adapter import CachedMarketDataAdapter
from the_alchemiser.shared.data_v2.live_bar_provider import LiveBarProvider
from the_alchemiser.shared.value_objects.symbol import Symbol
from indicators.indicators import TechnicalIndicators


def main():
    """Compare IGIB vs DBE RSI values to understand rains_concise_em divergence."""
    symbols = ["IGIB", "DBE", "IEI", "IWM", "MHD", "XLP", "PIM", "BBH", "MMT", "XLU"]

    print("=" * 80)
    print("RAINS_CONCISE_EM - Key Decision Point RSI Analysis")
    print("=" * 80)
    print("\nExpected (Composer): EDZ XLF")
    print("Actual (Our system): EDZ only")
    print("\nKey decision: IGIB RSI(10) > DBE RSI(10)")
    print("  If TRUE  -> EDZ + Leveraged Sectors (with XLF in filter)")
    print("  If FALSE -> EDZ only")
    print("=" * 80)

    # Get data with live bar
    print("\n--- Loading market data ---")
    adapter = CachedMarketDataAdapter(append_live_bar=True)

    # Calculate RSI for all key symbols
    import pandas as pd

    results = {}
    for symbol in symbols:
        bars = adapter.get_bars(Symbol(symbol), "1Y", "1D")
        prices = pd.Series([float(b.close) for b in bars])
        rsi_10 = TechnicalIndicators.rsi(prices, window=10)
        rsi_15 = TechnicalIndicators.rsi(prices, window=15)
        results[symbol] = {
            "rsi_10": rsi_10.iloc[-1] if len(rsi_10) > 0 else None,
            "rsi_15": rsi_15.iloc[-1] if len(rsi_15) > 0 else None,
            "last_close": float(bars[-1].close) if bars else None,
            "bar_count": len(bars),
        }
        print(f"  {symbol}: RSI(10)={results[symbol]['rsi_10']:.2f}, RSI(15)={results[symbol]['rsi_15']:.2f}")

    # Key comparisons
    print("\n--- Key Decision Point Comparisons (with live bar) ---")
    comparisons = [
        ("IGIB", "DBE", 10, 10),  # Key divergence point
        ("IEI", "IWM", 10, 15),   # IWM uses window 15 in DSL
        ("MHD", "XLP", 10, 10),
        ("PIM", "BBH", 10, 10),
        ("MMT", "XLU", 10, 10),
    ]

    for left, right, left_window, right_window in comparisons:
        left_key = f"rsi_{left_window}"
        right_key = f"rsi_{right_window}"
        left_val = results[left][left_key]
        right_val = results[right][right_key]
        result = left_val > right_val
        diff = left_val - right_val
        print(f"  {left} RSI({left_window}) > {right} RSI({right_window}): {left_val:.2f} > {right_val:.2f} = {result} (diff: {diff:+.2f})")

    # Now check without live bar (T-1)
    print("\n--- Without Live Bar (T-1 close) ---")
    adapter_t1 = CachedMarketDataAdapter(append_live_bar=False)

    results_t1 = {}
    for symbol in ["IGIB", "DBE"]:
        bars = adapter_t1.get_bars(Symbol(symbol), "1Y", "1D")
        prices = pd.Series([float(b.close) for b in bars])
        rsi_10 = TechnicalIndicators.rsi(prices, window=10)
        results_t1[symbol] = rsi_10.iloc[-1] if len(rsi_10) > 0 else None
        print(f"  {symbol}: RSI(10)={results_t1[symbol]:.2f}")

    print("\n" + "=" * 80)
    print("KEY FINDING: IGIB vs DBE Comparison")
    print("=" * 80)
    igib_live = results["IGIB"]["rsi_10"]
    dbe_live = results["DBE"]["rsi_10"]
    igib_t1 = results_t1["IGIB"]
    dbe_t1 = results_t1["DBE"]

    print(f"  IGIB RSI(10) with live bar:    {igib_live:.4f}")
    print(f"  IGIB RSI(10) without live bar: {igib_t1:.4f}")
    print(f"  DBE RSI(10) with live bar:     {dbe_live:.4f}")
    print(f"  DBE RSI(10) without live bar:  {dbe_t1:.4f}")
    print()
    print(f"  With live bar:    IGIB > DBE = {igib_live > dbe_live} ({igib_live:.2f} vs {dbe_live:.2f})")
    print(f"  Without live bar: IGIB > DBE = {igib_t1 > dbe_t1} ({igib_t1:.2f} vs {dbe_t1:.2f})")
    print()
    print("  If IGIB > DBE = TRUE  → EDZ + XLF (via Leveraged Sectors filter)")
    print("  If IGIB > DBE = FALSE → EDZ only")

    # Analysis
    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    if igib_live <= dbe_live:
        print(f"\n>>> IGIB RSI(10) = {igib_live:.2f} <= DBE RSI(10) = {dbe_live:.2f}")
        print(">>> This means condition (IGIB > DBE) is FALSE")
        print(">>> So we take ELSE branch -> EDZ only")
        print(">>> But Composer shows EDZ + XLF, meaning their IGIB > DBE")
        print("\nPossible causes:")
        print("  1. Data difference (S3 vs Composer source)")
        print("  2. Live bar timing (our price vs Composer's price)")
        print("  3. RSI calculation difference (Wilder vs SMA-based)")
    else:
        print(f"\n>>> IGIB RSI(10) = {igib_live:.2f} > DBE RSI(10) = {dbe_live:.2f}")
        print(">>> This means condition is TRUE")
        print(">>> So we should enter Leveraged Sectors group with XLF")
        print(">>> Something else is causing the divergence")


if __name__ == "__main__":
    main()
