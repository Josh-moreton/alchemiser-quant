#!/usr/bin/env python3
"""Business Unit: Data | Status: current.

Investigate price mismatches between S3, yfinance, and Alpaca to determine
if mismatches are due to corporate action adjustments not being applied.
"""

import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Setup imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
import io
from typing import Any

import boto3
import pandas as pd
import requests
import yfinance as yf

# Load .env file
from dotenv import load_dotenv
load_dotenv()

# Alpaca API credentials from environment
ALPACA_KEY = os.getenv("ALPACA__KEY", "")
ALPACA_SECRET = os.getenv("ALPACA__SECRET", "")
ALPACA_DATA_URL = "https://data.alpaca.markets/v2"

DEFAULT_BUCKET = "alchemiser-prod-market-data"

# Symbols with known mismatches from validation
MISMATCH_SYMBOLS = [
    "BAM",    # 7 mismatches
    "BKT",    # 398 mismatches
    "CPXR",   # 7 mismatches
    "FBL",    # 1 mismatch
    "GDXU",   # 4 mismatches
    "ISCB",   # 6 mismatches
    "KMLM",   # 500 mismatches
    "OILD",   # 268 mismatches
    "SAA",    # 2 mismatches
    "SPXT",   # 5 mismatches
    "SQM",    # 482 mismatches
    "SVXY",   # 822 mismatches
    "TMF",    # 1 mismatch
    "UGE",    # 12 mismatches
]


def get_s3_data(symbol: str, bucket: str = DEFAULT_BUCKET) -> pd.DataFrame | None:
    """Fetch data from S3 for a symbol (parquet format)."""
    s3 = boto3.client("s3")
    key = f"{symbol}/daily.parquet"
    
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        df = pd.read_parquet(io.BytesIO(response["Body"].read()))
        
        # Normalize column names to Title case
        df.columns = [c.title() if c.lower() in ["open", "high", "low", "close", "volume"] else c for c in df.columns]
        
        # Handle different possible date column names
        date_col = None
        for col in ["Date", "date", "timestamp", "Timestamp"]:
            if col in df.columns:
                date_col = col
                break
        
        if date_col:
            df[date_col] = pd.to_datetime(df[date_col])
            # Convert to tz-naive, date-only for matching
            if df[date_col].dt.tz is not None:
                df[date_col] = df[date_col].dt.tz_convert(None)
            # Normalize to date only (remove time component)
            df[date_col] = df[date_col].dt.normalize()
            df = df.set_index(date_col).sort_index()
        elif df.index.name in ["Date", "date", "timestamp", "Timestamp"] or isinstance(df.index, pd.DatetimeIndex):
            if df.index.tz is not None:
                df.index = df.index.tz_convert(None)
            df.index = df.index.normalize()
            df = df.sort_index()
        
        return df
    except Exception as e:
        print(f"  ❌ S3 error: {e}")
        return None


def get_yfinance_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame | None:
    """Fetch adjusted data from yfinance."""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start_date, end=end_date, auto_adjust=False)
        if df.empty:
            return None
        # Convert to tz-naive and normalize to date only
        if df.index.tz is not None:
            df.index = df.index.tz_convert(None)
        df.index = df.index.normalize()
        return df
    except Exception as e:
        print(f"  ❌ yfinance error: {e}")
        return None


def get_alpaca_data(
    symbol: str, 
    start_date: str, 
    end_date: str,
    adjustment: str = "all",
    feed: str = "iex"
) -> pd.DataFrame | None:
    """Fetch data from Alpaca with specified adjustment type.
    
    adjustment options:
    - "raw": unadjusted data
    - "split": adjusted for splits only
    - "dividend": adjusted for dividends only  
    - "all": adjusted for both splits and dividends
    
    feed options:
    - "iex": Free IEX feed (default)
    - "sip": Paid SIP feed (requires subscription)
    """
    headers = {
        "accept": "application/json",
        "APCA-API-KEY-ID": ALPACA_KEY,
        "APCA-API-SECRET-KEY": ALPACA_SECRET,
    }
    
    # Alpaca has 15-minute delay on data - adjust end time to avoid hitting this limit
    # For daily bars, just use yesterday's date to be safe
    end_dt = datetime.strptime(end_date, "%Y-%m-%d") - timedelta(days=1)
    safe_end_date = end_dt.strftime("%Y-%m-%d")
    
    # Use the multi-symbol endpoint with correct format
    url = f"{ALPACA_DATA_URL}/stocks/bars"
    params = {
        "symbols": symbol,
        "start": start_date,
        "end": safe_end_date,
        "timeframe": "1D",
        "adjustment": adjustment,
        "feed": feed,
        "sort": "asc",
        "limit": 10000,
    }
    
    all_bars = []
    next_page_token = None
    
    try:
        while True:
            if next_page_token:
                params["page_token"] = next_page_token
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Multi-symbol endpoint returns bars nested under symbol name
            bars = data.get("bars", {}).get(symbol, [])
            if bars:
                all_bars.extend(bars)
            
            next_page_token = data.get("next_page_token")
            if not next_page_token:
                break
        
        if not all_bars:
            return None
            
        df = pd.DataFrame(all_bars)
        df["t"] = pd.to_datetime(df["t"])
        # Convert to tz-naive and normalize to date only (same as S3/yfinance)
        if df["t"].dt.tz is not None:
            df["t"] = df["t"].dt.tz_convert(None)
        df["t"] = df["t"].dt.normalize()
        df = df.set_index("t").sort_index()
        # Rename columns to match our convention
        df = df.rename(columns={
            "o": "Open",
            "h": "High", 
            "l": "Low",
            "c": "Close",
            "v": "Volume",
        })
        return df
        
    except Exception as e:
        print(f"  ❌ Alpaca error ({adjustment}): {e}")
        return None


def calculate_pct_diff(val1: float, val2: float) -> float:
    """Calculate percentage difference between two values."""
    if val1 == 0 and val2 == 0:
        return 0.0
    if val1 == 0:
        return float("inf")
    return abs(val1 - val2) / abs(val1) * 100


def investigate_symbol(symbol: str, lookback_days: int = 30) -> dict[str, Any]:
    """Investigate price mismatches for a single symbol."""
    print(f"\n{'='*70}")
    print(f" Investigating {symbol}")
    print(f"{'='*70}")
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=lookback_days)
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")
    
    # Fetch from all sources
    print(f"\n📦 Fetching S3 data...")
    s3_df = get_s3_data(symbol)
    
    print(f"📈 Fetching yfinance data (with Adj Close)...")
    yf_df = get_yfinance_data(symbol, start_str, end_str)
    
    print(f"🦙 Fetching Alpaca data (adjustment=raw)...")
    alpaca_raw_df = get_alpaca_data(symbol, start_str, end_str, adjustment="raw")
    
    print(f"🦙 Fetching Alpaca data (adjustment=all)...")
    alpaca_adj_df = get_alpaca_data(symbol, start_str, end_str, adjustment="all")
    
    # Check what we got
    results = {
        "symbol": symbol,
        "has_s3": s3_df is not None and not s3_df.empty,
        "has_yf": yf_df is not None and not yf_df.empty,
        "has_alpaca_raw": alpaca_raw_df is not None and not alpaca_raw_df.empty,
        "has_alpaca_adj": alpaca_adj_df is not None and not alpaca_adj_df.empty,
    }
    
    if not all([results["has_s3"], results["has_yf"]]):
        print(f"  ⚠️  Missing data - cannot compare")
        return results
    
    # Filter S3 to the lookback period
    s3_df = s3_df[s3_df.index >= start_date]
    
    # Find common dates
    common_dates = s3_df.index.intersection(yf_df.index)
    if len(common_dates) == 0:
        print(f"  ⚠️  No overlapping dates")
        return results
    
    print(f"\n📊 Comparing {len(common_dates)} overlapping days...")
    
    # Build comparison table
    comparison_data = []
    
    for date in sorted(common_dates)[-10:]:  # Last 10 days
        row = {
            "Date": date.strftime("%Y-%m-%d"),
            "S3_Close": s3_df.loc[date, "Close"] if "Close" in s3_df.columns else None,
            "YF_Close": yf_df.loc[date, "Close"] if "Close" in yf_df.columns else None,
            "YF_AdjClose": yf_df.loc[date, "Adj Close"] if "Adj Close" in yf_df.columns else None,
        }
        
        if alpaca_raw_df is not None and date in alpaca_raw_df.index:
            row["Alpaca_Raw"] = alpaca_raw_df.loc[date, "Close"]
        else:
            row["Alpaca_Raw"] = None
            
        if alpaca_adj_df is not None and date in alpaca_adj_df.index:
            row["Alpaca_Adj"] = alpaca_adj_df.loc[date, "Close"]
        else:
            row["Alpaca_Adj"] = None
            
        comparison_data.append(row)
    
    # Print comparison table
    print(f"\n📋 Last 10 days comparison:")
    print("-" * 100)
    print(f"{'Date':<12} {'S3_Close':>12} {'YF_Close':>12} {'YF_AdjClose':>12} {'Alpaca_Raw':>12} {'Alpaca_Adj':>12}")
    print("-" * 100)
    
    for row in comparison_data:
        s3_close = f"{row['S3_Close']:.4f}" if row['S3_Close'] else "N/A"
        yf_close = f"{row['YF_Close']:.4f}" if row['YF_Close'] else "N/A"
        yf_adj = f"{row['YF_AdjClose']:.4f}" if row['YF_AdjClose'] else "N/A"
        alp_raw = f"{row['Alpaca_Raw']:.4f}" if row['Alpaca_Raw'] else "N/A"
        alp_adj = f"{row['Alpaca_Adj']:.4f}" if row['Alpaca_Adj'] else "N/A"
        print(f"{row['Date']:<12} {s3_close:>12} {yf_close:>12} {yf_adj:>12} {alp_raw:>12} {alp_adj:>12}")
    
    # Analyze mismatches
    print(f"\n🔍 Mismatch Analysis:")
    
    # Check S3 vs YF Adj Close
    s3_vs_yf_adj_mismatches = 0
    s3_vs_yf_close_mismatches = 0
    s3_vs_alpaca_raw_mismatches = 0
    s3_vs_alpaca_adj_mismatches = 0
    
    tolerance_pct = 2.0  # 2% tolerance
    
    for date in common_dates:
        s3_close = s3_df.loc[date, "Close"]
        yf_close = yf_df.loc[date, "Close"]
        yf_adj = yf_df.loc[date, "Adj Close"]
        
        if calculate_pct_diff(s3_close, yf_adj) > tolerance_pct:
            s3_vs_yf_adj_mismatches += 1
            
        if calculate_pct_diff(s3_close, yf_close) > tolerance_pct:
            s3_vs_yf_close_mismatches += 1
            
        if alpaca_raw_df is not None and date in alpaca_raw_df.index:
            if calculate_pct_diff(s3_close, alpaca_raw_df.loc[date, "Close"]) > tolerance_pct:
                s3_vs_alpaca_raw_mismatches += 1
                
        if alpaca_adj_df is not None and date in alpaca_adj_df.index:
            if calculate_pct_diff(s3_close, alpaca_adj_df.loc[date, "Close"]) > tolerance_pct:
                s3_vs_alpaca_adj_mismatches += 1
    
    print(f"  S3 vs YF Adj Close:    {s3_vs_yf_adj_mismatches}/{len(common_dates)} mismatches")
    print(f"  S3 vs YF Close:        {s3_vs_yf_close_mismatches}/{len(common_dates)} mismatches")
    
    if alpaca_raw_df is not None:
        print(f"  S3 vs Alpaca Raw:      {s3_vs_alpaca_raw_mismatches}/{len(common_dates)} mismatches")
    if alpaca_adj_df is not None:
        print(f"  S3 vs Alpaca Adjusted: {s3_vs_alpaca_adj_mismatches}/{len(common_dates)} mismatches")
    
    # Show sample mismatches from earliest dates
    if s3_vs_yf_adj_mismatches > 0:
        print(f"\n📋 Sample mismatches (earliest dates with >2% diff):")
        print("-" * 100)
        print(f"{'Date':<12} {'S3_Close':>12} {'YF_Close':>12} {'YF_AdjClose':>12} {'Alpaca_Adj':>12} {'S3vsYF%':>10}")
        print("-" * 100)
        mismatch_samples = 0
        for date in sorted(common_dates):
            s3_close = s3_df.loc[date, "Close"]
            yf_close = yf_df.loc[date, "Close"]
            yf_adj = yf_df.loc[date, "Adj Close"]
            diff_pct = calculate_pct_diff(s3_close, yf_adj)
            
            if diff_pct > tolerance_pct:
                alp_val = alpaca_adj_df.loc[date, "Close"] if alpaca_adj_df is not None and date in alpaca_adj_df.index else None
                alp_str = f"{alp_val:.4f}" if alp_val else "N/A"
                print(f"{date.strftime('%Y-%m-%d'):<12} {s3_close:>12.4f} {yf_close:>12.4f} {yf_adj:>12.4f} {alp_str:>12} {diff_pct:>9.2f}%")
                mismatch_samples += 1
                if mismatch_samples >= 5:
                    break
    
    # Check if YF Close == YF Adj Close (no adjustments applied)
    yf_close_vs_adj_diff = 0
    for date in common_dates:
        if calculate_pct_diff(yf_df.loc[date, "Close"], yf_df.loc[date, "Adj Close"]) > 0.01:
            yf_close_vs_adj_diff += 1
    
    print(f"\n  YF Close != YF Adj Close on {yf_close_vs_adj_diff}/{len(common_dates)} days")
    
    if yf_close_vs_adj_diff > 0:
        print(f"  ⚠️  This symbol has had adjustments (dividends/splits)!")
        
        # Check if S3 matches unadjusted or adjusted
        if s3_vs_yf_close_mismatches < s3_vs_yf_adj_mismatches:
            print(f"  💡 S3 appears to have UNADJUSTED data (matches YF Close better)")
            results["diagnosis"] = "S3 has unadjusted data"
        else:
            print(f"  💡 S3 appears to have ADJUSTED data (matches YF Adj Close better)")
            results["diagnosis"] = "S3 has adjusted data"
    else:
        print(f"  ℹ️  No adjustments detected in yfinance data for this period")
        results["diagnosis"] = "No adjustments in period"
    
    results["s3_vs_yf_adj_mismatches"] = s3_vs_yf_adj_mismatches
    results["s3_vs_yf_close_mismatches"] = s3_vs_yf_close_mismatches
    results["total_compared"] = len(common_dates)
    
    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Investigate price mismatches between S3, yfinance, and Alpaca"
    )
    parser.add_argument(
        "--symbols",
        type=str,
        default=",".join(MISMATCH_SYMBOLS[:3]),  # Default to first 3 for quick test
        help="Comma-separated list of symbols to investigate",
    )
    parser.add_argument(
        "--all-mismatches",
        action="store_true",
        help="Investigate all known mismatch symbols",
    )
    parser.add_argument(
        "--lookback",
        type=int,
        default=60,
        help="Number of days to look back (default: 60)",
    )
    
    args = parser.parse_args()
    
    if args.all_mismatches:
        symbols = MISMATCH_SYMBOLS
    else:
        symbols = [s.strip().upper() for s in args.symbols.split(",")]
    
    print("=" * 70)
    print(" Price Mismatch Investigation")
    print("=" * 70)
    print(f"Symbols to investigate: {symbols}")
    print(f"Lookback period: {args.lookback} days")
    
    all_results = []
    
    for symbol in symbols:
        result = investigate_symbol(symbol, args.lookback)
        all_results.append(result)
    
    # Summary
    print("\n" + "=" * 70)
    print(" INVESTIGATION SUMMARY")
    print("=" * 70)
    
    unadjusted_count = 0
    adjusted_count = 0
    other_count = 0
    
    for r in all_results:
        diag = r.get("diagnosis", "unknown")
        if "unadjusted" in diag.lower():
            unadjusted_count += 1
        elif "adjusted" in diag.lower():
            adjusted_count += 1
        else:
            other_count += 1
        
        print(f"  {r['symbol']}: {diag}")
    
    print(f"\n📊 Diagnosis breakdown:")
    print(f"  - S3 has unadjusted data: {unadjusted_count}")
    print(f"  - S3 has adjusted data: {adjusted_count}")
    print(f"  - Other/unknown: {other_count}")
    
    if unadjusted_count > adjusted_count:
        print(f"\n💡 CONCLUSION: S3 data appears to NOT be adjusted for corporate actions.")
        print(f"   The validation script compares S3 Close against yfinance Adj Close,")
        print(f"   which will fail for any symbol that has had dividends or splits.")
        print(f"\n   RECOMMENDATION: Either:")
        print(f"   1. Re-download data with adjustments applied, OR")
        print(f"   2. Update validation to compare S3 Close vs YF Close (unadjusted)")


if __name__ == "__main__":
    main()
