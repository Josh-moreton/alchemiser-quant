#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Compare RSI values with and without live bar injection.

This script demonstrates the impact of live bar injection on RSI-based
decisions (EDC vs EDZ). It compares RSI calculations using:

1. S3 cached data through Jan 5 (Friday close)
2. S3 cached data through Jan 6 (Monday close)  
3. S3 cached data + today's live bar (intraday)

The goal is to identify whether live bar injection causes the IEI vs IWM
RSI comparison to flip from EDZ (correct per Composer) to EDC (incorrect).

Usage:
    MARKET_DATA_BUCKET=alchemiser-dev-market-data poetry run python scripts/compare_rsi_with_live_bar.py
"""

from __future__ import annotations

import os
import sys
from datetime import UTC, datetime, timedelta, date
from decimal import Decimal

import pandas as pd

# Add layers to path for shared imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "layers", "shared"))

# Suppress noisy logging
import logging
logging.getLogger("alpaca").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


def calculate_rsi(prices: pd.Series, window: int) -> float:
    """Calculate RSI using Wilder's smoothing method.
    
    This matches Composer/TradingView's RSI implementation.
    """
    if len(prices) < window + 1:
        return 50.0  # Neutral fallback
    
    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    alpha = 1.0 / window
    avg_gain = gain.ewm(alpha=alpha, adjust=False).mean()
    avg_loss = loss.ewm(alpha=alpha, adjust=False).mean()
    
    rs = avg_gain.divide(avg_loss, fill_value=0.0)
    rsi = 100 - (100 / (1 + rs))
    
    return float(rsi.fillna(50.0).iloc[-1])


def get_s3_data_through_date(
    store: "MarketDataStore",
    symbol: str,
    cutoff_date: date,
) -> pd.DataFrame:
    """Get S3 data filtered through a specific date."""
    df = store.read_symbol_data(symbol)
    if df is None or df.empty:
        return pd.DataFrame()
    
    if "timestamp" in df.columns:
        df = df.set_index("timestamp")
    
    df.index = pd.to_datetime(df.index)
    if df.index.tz is None:
        df.index = df.index.tz_localize(UTC)
    
    cutoff_datetime = pd.Timestamp(cutoff_date, tz=UTC)
    df = df[df.index.normalize() <= cutoff_datetime]
    
    return df.sort_index()


def main() -> None:
    """Run RSI comparison with different data cutoffs."""
    from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore
    from the_alchemiser.shared.data_v2.live_bar_provider import LiveBarProvider
    
    print("=" * 80)
    print("RSI COMPARISON: LIVE BAR IMPACT ANALYSIS")
    print("=" * 80)
    print()
    
    # Initialize data sources
    store = MarketDataStore()
    live_provider = LiveBarProvider()
    
    # Define dates
    jan_5 = date(2026, 1, 5)  # Friday
    jan_6 = date(2026, 1, 6)  # Monday
    today = datetime.now(UTC).date()
    
    print(f"Jan 5 (Friday):  {jan_5}")
    print(f"Jan 6 (Monday):  {jan_6}")
    print(f"Today:           {today}")
    print()
    
    # RSI comparisons to test (from affected strategies)
    comparisons = [
        ("IEI", "IWM", 10, 15, "chicken_rice, sisyphus_lowvol"),
        ("IEI", "IWM", 11, 16, "ftl_starburst"),
        ("IEI", "EEM", 11, 16, "ftl_starburst (alt)"),
        ("IEI", "IWM", 10, 12, "rains_em_dancer"),
    ]
    
    # First, show raw closing prices for key symbols
    symbols = ["IEI", "IWM", "EEM"]
    
    print("=" * 80)
    print("RAW CLOSING PRICES")
    print("=" * 80)
    
    for symbol in symbols:
        df_full = get_s3_data_through_date(store, symbol, today)
        if df_full.empty:
            print(f"\n{symbol}: No data available")
            continue
        
        print(f"\n{symbol} - Last 10 closes from S3:")
        print("-" * 40)
        for ts, row in df_full.tail(10).iterrows():
            print(f"  {ts.date()}:  ${row['close']:.2f}")
        
        # Try to get live bar
        live_bar = live_provider.get_todays_bar(symbol)
        if live_bar:
            print(f"  {today} (LIVE): ${float(live_bar.close):.2f}  ← intraday")
    
    print()
    print("=" * 80)
    print("RSI COMPARISONS BY DATE CUTOFF")
    print("Logic: If RSI(Symbol1) > RSI(Symbol2) → EDC, else → EDZ")
    print("Expected (Composer): EDZ for all comparisons")
    print("=" * 80)
    
    # Run each comparison
    for sym_a, sym_b, window_a, window_b, strategies in comparisons:
        print()
        print(f"\n{'='*80}")
        print(f"RSI({sym_a}, {window_a}) vs RSI({sym_b}, {window_b})")
        print(f"Used by: {strategies}")
        print("=" * 80)
        
        # Get data for each date cutoff
        results = []
        
        for cutoff_date, label in [
            (jan_5, "Jan 5 (Fri)"),
            (jan_6, "Jan 6 (Mon)"),
        ]:
            df_a = get_s3_data_through_date(store, sym_a, cutoff_date)
            df_b = get_s3_data_through_date(store, sym_b, cutoff_date)
            
            if df_a.empty or df_b.empty:
                print(f"  {label}: No data")
                continue
            
            # Calculate RSI
            rsi_a = calculate_rsi(df_a["close"], window_a)
            rsi_b = calculate_rsi(df_b["close"], window_b)
            
            decision = "EDC" if rsi_a > rsi_b else "EDZ"
            match = "✅" if decision == "EDZ" else "❌ WRONG"
            
            results.append({
                "label": label,
                "rsi_a": rsi_a,
                "rsi_b": rsi_b,
                "decision": decision,
                "match": match,
            })
        
        # Now with live bar
        df_a_base = get_s3_data_through_date(store, sym_a, jan_6)
        df_b_base = get_s3_data_through_date(store, sym_b, jan_6)
        
        live_a = live_provider.get_todays_bar(sym_a)
        live_b = live_provider.get_todays_bar(sym_b)
        
        if not df_a_base.empty and not df_b_base.empty and live_a and live_b:
            # Append live bars
            closes_a = df_a_base["close"].tolist() + [float(live_a.close)]
            closes_b = df_b_base["close"].tolist() + [float(live_b.close)]
            
            rsi_a = calculate_rsi(pd.Series(closes_a), window_a)
            rsi_b = calculate_rsi(pd.Series(closes_b), window_b)
            
            decision = "EDC" if rsi_a > rsi_b else "EDZ"
            match = "✅" if decision == "EDZ" else "❌ WRONG"
            
            results.append({
                "label": f"Jan 6 + Live ({today})",
                "rsi_a": rsi_a,
                "rsi_b": rsi_b,
                "decision": decision,
                "match": match,
            })
        
        # Print results table
        print()
        print(f"{'Data Cutoff':<25} {'RSI '+sym_a:>10} {'RSI '+sym_b:>10} {'Diff':>8} {'Decision':>10} {'Match':>10}")
        print("-" * 80)
        
        for r in results:
            diff = r["rsi_a"] - r["rsi_b"]
            print(
                f"{r['label']:<25} {r['rsi_a']:>10.2f} {r['rsi_b']:>10.2f} "
                f"{diff:>+8.2f} {r['decision']:>10} {r['match']:>10}"
            )
    
    # Summary
    print()
    print("=" * 80)
    print("ANALYSIS")
    print("=" * 80)
    print()
    print("If Jan 5/Jan 6 show EDZ (correct) but 'Jan 6 + Live' shows EDC (wrong),")
    print("then LIVE BAR INJECTION is causing the discrepancy.")
    print()
    print("If all dates show EDZ, the issue may be in:")
    print("  - How the strategy ran at a different time (intraday prices were different)")
    print("  - S3 data was stale when the strategy ran")
    print("  - Different calculation logic in the actual indicator service")
    print()


if __name__ == "__main__":
    main()
