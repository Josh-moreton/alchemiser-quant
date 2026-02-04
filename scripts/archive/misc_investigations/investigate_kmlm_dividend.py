#!/usr/bin/env python3
"""Business Unit: Scripts | Status: current.

Investigate KMLM dividend adjustment issue.

Compares adjusted vs unadjusted prices from multiple sources to identify
if our S3 datalake has stale/unadjusted data causing incorrect RSI.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

os.environ.setdefault("MARKET_DATA_BUCKET", "alchemiser-dev-market-data")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "layers" / "shared"))

import pandas as pd
import yfinance as yf

from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore


def get_yfinance_adjusted(symbol: str, days: int = 60) -> pd.DataFrame:
    """Get adjusted close prices from yfinance."""
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period=f"{days}d")
    if hist.empty:
        return pd.DataFrame()
    
    df = pd.DataFrame({
        "date": [d.date() for d in hist.index],
        "close_adj": hist["Close"].values,
        "open": hist["Open"].values,
        "high": hist["High"].values,
        "low": hist["Low"].values,
        "volume": hist["Volume"].values,
    })
    df.set_index("date", inplace=True)
    return df


def get_yfinance_unadjusted(symbol: str, days: int = 60) -> pd.DataFrame:
    """Get unadjusted close prices from yfinance using auto_adjust=False."""
    ticker = yf.Ticker(symbol)
    # auto_adjust=False returns unadjusted OHLC with separate 'Adj Close' column
    hist = ticker.history(period=f"{days}d", auto_adjust=False)
    if hist.empty:
        return pd.DataFrame()
    
    df = pd.DataFrame({
        "date": [d.date() for d in hist.index],
        "close_unadj": hist["Close"].values,
        "adj_close": hist["Adj Close"].values,
    })
    df.set_index("date", inplace=True)
    return df


def get_s3_prices(store: MarketDataStore, symbol: str, days: int = 60) -> pd.DataFrame:
    """Get prices from S3 datalake."""
    try:
        df = store.read_symbol_data(symbol, use_cache=False)
        if df is None or df.empty:
            return pd.DataFrame()
        
        if "timestamp" in df.columns:
            df["date"] = pd.to_datetime(df["timestamp"]).dt.date
            df.set_index("date", inplace=True)
        
        # Filter to recent days
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).date()
        df = df[df.index >= cutoff]
        
        return pd.DataFrame({
            "close_s3": df["close"],
            "open_s3": df["open"],
        }, index=df.index)
    except Exception as e:
        print(f"S3 error: {e}")
        return pd.DataFrame()


def check_dividends(symbol: str) -> None:
    """Check recent dividends for a symbol."""
    print(f"\n{'='*70}")
    print(f"DIVIDEND HISTORY: {symbol}")
    print("="*70)
    
    ticker = yf.Ticker(symbol)
    divs = ticker.dividends
    
    if divs.empty:
        print("No dividend history found")
        return
    
    # Show last 10 dividends
    print("\nRecent dividends:")
    print(f"{'Date':<15} {'Amount':>10}")
    print("-" * 25)
    
    for date, amount in divs.tail(10).items():
        print(f"{date.strftime('%Y-%m-%d'):<15} ${amount:>9.4f}")
    
    # Check for dividends in last 30 days
    recent_cutoff = pd.Timestamp.now(tz="America/New_York") - timedelta(days=30)
    recent_divs = divs[divs.index >= recent_cutoff]
    
    if not recent_divs.empty:
        print(f"\n⚠️  RECENT DIVIDEND DETECTED in last 30 days!")
        for date, amount in recent_divs.items():
            print(f"   {date.strftime('%Y-%m-%d')}: ${amount:.4f}")
    else:
        print("\n✓ No dividends in last 30 days")


def compare_prices(symbol: str, s3_store: MarketDataStore) -> None:
    """Compare prices across sources to detect adjustment issues."""
    print(f"\n{'='*70}")
    print(f"PRICE COMPARISON: {symbol}")
    print("="*70)
    
    # Get data from all sources
    yf_adj = get_yfinance_adjusted(symbol, 30)
    yf_unadj = get_yfinance_unadjusted(symbol, 30)
    s3_prices = get_s3_prices(s3_store, symbol, 30)
    
    if yf_adj.empty or yf_unadj.empty:
        print("Failed to get yfinance data")
        return
    
    # Merge dataframes
    merged = yf_adj[["close_adj"]].join(yf_unadj[["close_unadj", "adj_close"]], how="outer")
    if not s3_prices.empty:
        merged = merged.join(s3_prices[["close_s3"]], how="outer")
    else:
        merged["close_s3"] = None
    
    print(f"\n{'Date':<12} {'YF Adj':>10} {'YF Unadj':>10} {'YF AdjClose':>12} {'S3':>10} {'S3 vs YF Adj':>12}")
    print("-" * 70)
    
    adjustment_issues = []
    
    for date in sorted(merged.index)[-20:]:  # Last 20 days
        row = merged.loc[date]
        yf_a = row.get("close_adj")
        yf_u = row.get("close_unadj")
        yf_ac = row.get("adj_close")
        s3 = row.get("close_s3")
        
        yf_a_str = f"{yf_a:.4f}" if pd.notna(yf_a) else "N/A"
        yf_u_str = f"{yf_u:.4f}" if pd.notna(yf_u) else "N/A"
        yf_ac_str = f"{yf_ac:.4f}" if pd.notna(yf_ac) else "N/A"
        s3_str = f"{s3:.4f}" if pd.notna(s3) else "N/A"
        
        # Compare S3 to yfinance adjusted
        diff_str = ""
        if pd.notna(s3) and pd.notna(yf_a):
            diff = s3 - yf_a
            diff_str = f"{diff:+.4f}"
            if abs(diff) > 0.01:  # More than 1 cent difference
                diff_str += " ⚠️"
                adjustment_issues.append((date, diff, s3, yf_a))
        
        print(f"{date}   {yf_a_str:>10} {yf_u_str:>10} {yf_ac_str:>12} {s3_str:>10} {diff_str:>12}")
    
    # Summary
    print("\n" + "-" * 70)
    if adjustment_issues:
        print(f"\n⚠️  ADJUSTMENT ISSUES DETECTED: {len(adjustment_issues)} days with price differences")
        print("\nDays with S3 != YF Adjusted:")
        for date, diff, s3_val, yf_val in adjustment_issues:
            print(f"  {date}: S3={s3_val:.4f}, YF Adj={yf_val:.4f}, Diff={diff:+.4f}")
        
        # Check if S3 matches unadjusted prices
        print("\nChecking if S3 matches UNADJUSTED prices (dividend not applied):")
        for date in [d for d, _, _, _ in adjustment_issues[:5]]:
            if date in merged.index:
                row = merged.loc[date]
                s3_val = row.get("close_s3")
                unadj_val = row.get("close_unadj")
                if pd.notna(s3_val) and pd.notna(unadj_val):
                    match = "✓ MATCH" if abs(s3_val - unadj_val) < 0.01 else "✗ NO MATCH"
                    print(f"  {date}: S3={s3_val:.4f}, Unadjusted={unadj_val:.4f} -> {match}")
    else:
        print("\n✓ S3 prices match yfinance adjusted prices")


def calculate_rsi_comparison(symbol: str, s3_store: MarketDataStore, window: int = 10) -> None:
    """Calculate RSI using different price sources to show impact."""
    print(f"\n{'='*70}")
    print(f"RSI CALCULATION COMPARISON: {symbol} (window={window})")
    print("="*70)
    
    def calc_rsi(prices: pd.Series, w: int) -> float:
        if len(prices) < w + 1:
            return 50.0
        delta = prices.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)
        avg_gain = gain.ewm(alpha=1/w, min_periods=w, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/w, min_periods=w, adjust=False).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1])
    
    # Get prices
    yf_adj = get_yfinance_adjusted(symbol, 60)
    yf_unadj = get_yfinance_unadjusted(symbol, 60)
    s3_prices = get_s3_prices(s3_store, symbol, 60)
    
    if not yf_adj.empty:
        rsi_adj = calc_rsi(yf_adj["close_adj"], window)
        print(f"\nRSI using yfinance ADJUSTED prices:   {rsi_adj:.2f}")
    
    if not yf_unadj.empty:
        rsi_unadj = calc_rsi(yf_unadj["close_unadj"], window)
        print(f"RSI using yfinance UNADJUSTED prices: {rsi_unadj:.2f}")
    
    if not s3_prices.empty:
        rsi_s3 = calc_rsi(s3_prices["close_s3"], window)
        print(f"RSI using S3 datalake prices:         {rsi_s3:.2f}")
    
    # Show the difference
    if not yf_adj.empty and not yf_unadj.empty:
        diff = rsi_unadj - rsi_adj
        print(f"\nRSI difference (unadjusted - adjusted): {diff:+.2f}")
        if abs(diff) > 5:
            print("⚠️  SIGNIFICANT RSI DIFFERENCE due to dividend adjustment!")


def main() -> None:
    """Run dividend adjustment investigation."""
    print("="*70)
    print("KMLM DIVIDEND ADJUSTMENT INVESTIGATION")
    print("Checking if S3 datalake has unadjusted prices causing RSI errors")
    print("="*70)
    
    # Initialize S3 store
    try:
        s3_store = MarketDataStore()
        print("S3 store initialized")
    except Exception as e:
        print(f"S3 error: {e}")
        return
    
    # Check KMLM dividends
    check_dividends("KMLM")
    
    # Compare prices
    compare_prices("KMLM", s3_store)
    
    # Calculate RSI impact
    calculate_rsi_comparison("KMLM", s3_store, window=10)
    
    # Also check XLK for comparison (it shouldn't have issues)
    print("\n\n" + "="*70)
    print("CONTROL CHECK: XLK (should not have dividend issues)")
    print("="*70)
    check_dividends("XLK")
    compare_prices("XLK", s3_store)
    calculate_rsi_comparison("XLK", s3_store, window=10)
    
    # Summary
    print("\n\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print("""
If KMLM shows:
1. Recent dividend in the last 30 days
2. S3 prices matching UNADJUSTED yfinance prices  
3. Significant RSI difference between adjusted/unadjusted

Then the bug is: Our data refresh is storing UNADJUSTED prices,
causing RSI calculations to be wrong after dividends.

FIX: Re-run data refresh with adjustment=ALL or use yfinance 
with auto_adjust=True (default) to get properly adjusted prices.
""")


if __name__ == "__main__":
    main()
