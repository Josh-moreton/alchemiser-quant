#!/usr/bin/env python3
"""Business Unit: Scripts | Status: current.

Check RSI values for ftl_starburst TECL/TECS and EDC/EDZ decisions.
Compares S3, yfinance data to find discrepancies vs Composer.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Set environment
os.environ.setdefault("MARKET_DATA_BUCKET", "alchemiser-dev-market-data")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "layers" / "shared"))

import pandas as pd
import yfinance as yf

from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore


def calculate_rsi(prices: pd.Series, window: int) -> float:
    """Calculate RSI using Wilder's smoothing method."""
    if len(prices) < window + 1:
        return 50.0
    
    delta = prices.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    
    avg_gain = gain.ewm(alpha=1/window, min_periods=window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/window, min_periods=window, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return float(rsi.iloc[-1])


def fetch_yfinance(symbol: str, end_date: datetime, lookback: int = 50) -> pd.DataFrame:
    """Fetch from yfinance up to end_date."""
    start = end_date - timedelta(days=lookback + 10)
    ticker = yf.Ticker(symbol)
    df = ticker.history(
        start=start.strftime("%Y-%m-%d"),
        end=(end_date + timedelta(days=1)).strftime("%Y-%m-%d"),
    )
    if df.empty:
        return pd.DataFrame()
    return pd.DataFrame({"close": df["Close"].values}, index=[d.date() for d in df.index])


def fetch_s3(store: MarketDataStore, symbol: str, end_date: datetime, lookback: int = 50) -> pd.DataFrame:
    """Fetch from S3 up to end_date."""
    try:
        df = store.read_symbol_data(symbol, use_cache=False)
        if df is None or df.empty:
            return pd.DataFrame()
        
        if "timestamp" in df.columns:
            df["date"] = pd.to_datetime(df["timestamp"]).dt.date
            df.set_index("date", inplace=True)
        
        cutoff = (end_date - timedelta(days=lookback + 10)).date()
        end = end_date.date()
        df = df[(df.index >= cutoff) & (df.index <= end)]
        
        return pd.DataFrame({"close": df["close"]}, index=df.index)
    except Exception as e:
        print(f"  S3 error for {symbol}: {e}")
        return pd.DataFrame()


def compare_decision(
    name: str,
    sym_a: str, sym_b: str,
    win_a: int, win_b: int,
    end_date: datetime,
    s3_store: MarketDataStore,
    expected_bull: str,
    expected_bear: str,
    composer_choice: str,
) -> None:
    """Compare RSI decision across data sources."""
    print(f"\n{'='*70}")
    print(f"{name}")
    print(f"Condition: RSI({sym_a}, {win_a}) > RSI({sym_b}, {win_b})")
    print(f"  True -> {expected_bull} (bull)")
    print(f"  False -> {expected_bear} (bear)")
    print(f"Composer chose: {composer_choice}")
    print(f"{'='*70}")
    
    # yfinance
    yf_a = fetch_yfinance(sym_a, end_date)
    yf_b = fetch_yfinance(sym_b, end_date)
    
    if not yf_a.empty and not yf_b.empty:
        rsi_a = calculate_rsi(yf_a["close"], win_a)
        rsi_b = calculate_rsi(yf_b["close"], win_b)
        decision = expected_bull if rsi_a > rsi_b else expected_bear
        match = "✓" if decision == composer_choice else "✗ MISMATCH"
        print(f"\nyfinance (end: {yf_a.index[-1]}):")
        print(f"  {sym_a} RSI({win_a}) = {rsi_a:.2f}")
        print(f"  {sym_b} RSI({win_b}) = {rsi_b:.2f}")
        print(f"  Decision: {decision} {match}")
    
    # S3
    s3_a = fetch_s3(s3_store, sym_a, end_date)
    s3_b = fetch_s3(s3_store, sym_b, end_date)
    
    if not s3_a.empty and not s3_b.empty:
        rsi_a = calculate_rsi(s3_a["close"], win_a)
        rsi_b = calculate_rsi(s3_b["close"], win_b)
        decision = expected_bull if rsi_a > rsi_b else expected_bear
        match = "✓" if decision == composer_choice else "✗ MISMATCH"
        print(f"\nS3 datalake (end: {s3_a.index[-1]}):")
        print(f"  {sym_a} RSI({win_a}) = {rsi_a:.2f}")
        print(f"  {sym_b} RSI({win_b}) = {rsi_b:.2f}")
        print(f"  Decision: {decision} {match}")


def main() -> None:
    """Run RSI comparison for ftl_starburst decisions."""
    print("="*70)
    print("FTL Starburst Decision Analysis")
    print("Comparing our RSI calculations vs Composer expected outcomes")
    print("="*70)
    
    # Initialize S3 store
    try:
        s3_store = MarketDataStore()
        print("S3 store initialized")
    except Exception as e:
        print(f"S3 store error: {e}")
        return
    
    # Check for Jan 7, 2026 (the date in Composer screenshot)
    end_date = datetime(2026, 1, 7, tzinfo=timezone.utc)
    print(f"\nAnalysis date: {end_date.date()}")
    
    # 1. TECL/TECS decision
    compare_decision(
        name="TECL/TECS Decision (KMLM | Technology)",
        sym_a="XLK", sym_b="KMLM",
        win_a=10, win_b=10,
        end_date=end_date,
        s3_store=s3_store,
        expected_bull="TECL",
        expected_bear="TECS",
        composer_choice="TECL",  # Composer shows TECL
    )
    
    # 2. EDC/EDZ decision (Modified Foreign Rat - when EEM > MA200)
    compare_decision(
        name="EDC/EDZ Decision (Modified Foreign Rat)",
        sym_a="IEI", sym_b="IWM",
        win_a=11, win_b=16,
        end_date=end_date,
        s3_store=s3_store,
        expected_bull="EDC",
        expected_bear="EDZ",
        composer_choice="EDC",  # Composer shows EDC
    )
    
    # Check raw last 5 days of prices
    print(f"\n{'='*70}")
    print("Raw price data (last 5 days)")
    print("="*70)
    
    for sym in ["XLK", "KMLM", "IEI", "IWM"]:
        yf_df = fetch_yfinance(sym, end_date, 20)
        s3_df = fetch_s3(s3_store, sym, end_date, 20)
        
        print(f"\n{sym}:")
        print(f"  {'Date':<12} {'yfinance':>12} {'S3':>12} {'Diff':>10}")
        
        if not yf_df.empty:
            for i in range(-5, 0):
                try:
                    date = yf_df.index[i]
                    yf_close = yf_df["close"].iloc[i]
                    s3_close = s3_df.loc[date, "close"] if date in s3_df.index else None
                    diff = f"{yf_close - s3_close:.4f}" if s3_close else "N/A"
                    s3_str = f"{s3_close:.4f}" if s3_close else "N/A"
                    print(f"  {date}   {yf_close:>12.4f} {s3_str:>12} {diff:>10}")
                except (IndexError, KeyError):
                    pass


if __name__ == "__main__":
    main()
