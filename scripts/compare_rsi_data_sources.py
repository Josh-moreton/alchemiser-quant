#!/usr/bin/env python3
"""Business Unit: Scripts | Status: current.

Compare RSI values across Alpaca, yfinance, and S3 datalake.

This script calculates RSI values for key indicators that trigger the
EDC vs EDZ risk-off decision across multiple strategies. The goal is
to identify which data source produces values that would result in
Composer selecting EDZ (bear) instead of EDC (bull).

Key Decision Logic:
- If RSI(IEI) > RSI(IWM) → EDC (bull)
- If RSI(IEI) <= RSI(IWM) → EDZ (bear)

Composer is selecting EDZ, so we need to find which data source gives:
RSI(IEI) <= RSI(IWM)
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pandas as pd
import yfinance as yf
from alpaca.data.enums import Adjustment
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from dotenv import load_dotenv

# Load environment variables - try multiple locations
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

# Add project root to path for S3 imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore


# ==============================================================================
# RSI Calculation (Wilder's smoothing - matches Composer)
# ==============================================================================
def calculate_rsi(prices: pd.Series, window: int) -> float:
    """Calculate RSI using Wilder's smoothing method.
    
    This matches the calculation used by Composer and TradingView.
    
    Args:
        prices: Series of closing prices (oldest to newest)
        window: RSI lookback period
        
    Returns:
        Latest RSI value (0-100)
    """
    if len(prices) < window + 1:
        return 50.0  # Neutral if insufficient data
    
    delta = prices.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    
    # Wilder's smoothing: alpha = 1/window
    avg_gain = gain.ewm(alpha=1/window, min_periods=window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/window, min_periods=window, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return float(rsi.iloc[-1])


# ==============================================================================
# Data Source Fetchers
# ==============================================================================
def get_alpaca_client() -> StockHistoricalDataClient:
    """Get authenticated Alpaca client."""
    api_key = (
        os.environ.get("ALPACA__KEY")
        or os.environ.get("ALPACA_KEY")
        or os.environ.get("ALPACA_API_KEY")
        or os.environ.get("APCA_API_KEY_ID")
    )
    api_secret = (
        os.environ.get("ALPACA__SECRET")
        or os.environ.get("ALPACA_SECRET")
        or os.environ.get("ALPACA_API_SECRET")
        or os.environ.get("APCA_API_SECRET_KEY")
    )
    
    if not api_key or not api_secret:
        raise RuntimeError("Alpaca credentials not found in environment. Set ALPACA__KEY and ALPACA__SECRET")
    
    return StockHistoricalDataClient(api_key, api_secret)


def fetch_alpaca_data(
    client: StockHistoricalDataClient | None,
    symbol: str,
    end_date: datetime,
    lookback_days: int = 50,
) -> pd.DataFrame:
    """Fetch historical bars from Alpaca with Adjustment.ALL."""
    if client is None:
        return pd.DataFrame()
    
    start_date = end_date - timedelta(days=lookback_days + 10)  # Extra buffer
    
    try:
        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Day,
            start=start_date,
            end=end_date,
            adjustment=Adjustment.ALL,
        )
        
        response = client.get_stock_bars(request)
        
        if symbol not in response:
            return pd.DataFrame()
        
        bars = response[symbol]
        data = []
        for bar in bars:
            data.append({
                "date": bar.timestamp.date(),
                "close": float(bar.close),
            })
        
        df = pd.DataFrame(data)
        df.set_index("date", inplace=True)
        return df
    except Exception as e:
        print(f"    ⚠️ Alpaca error for {symbol}: {e}")
        return pd.DataFrame()


def fetch_yfinance_data(
    symbol: str,
    end_date: datetime,
    lookback_days: int = 50,
) -> pd.DataFrame:
    """Fetch historical bars from yfinance (adjusted)."""
    start_date = end_date - timedelta(days=lookback_days + 10)
    
    ticker = yf.Ticker(symbol)
    df = ticker.history(
        start=start_date.strftime("%Y-%m-%d"),
        end=(end_date + timedelta(days=1)).strftime("%Y-%m-%d"),  # yfinance is exclusive
    )
    
    if df.empty:
        return pd.DataFrame()
    
    # Convert to simple date index
    result = pd.DataFrame({
        "close": df["Close"].values,
    }, index=[d.date() for d in df.index])
    
    return result


def fetch_s3_data(
    store: MarketDataStore,
    symbol: str,
    end_date: datetime,
    lookback_days: int = 50,
) -> pd.DataFrame:
    """Fetch historical bars from S3 datalake."""
    try:
        df = store.read_symbol_data(symbol, use_cache=False)
        
        if df is None or df.empty:
            return pd.DataFrame()
        
        # Ensure we have a date column/index
        if "timestamp" in df.columns:
            df["date"] = pd.to_datetime(df["timestamp"]).dt.date
            df.set_index("date", inplace=True)
        elif "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.date
            df.set_index("date", inplace=True)
        
        # Filter to lookback period
        cutoff_date = (end_date - timedelta(days=lookback_days + 10)).date()
        end_date_only = end_date.date()
        df = df[(df.index >= cutoff_date) & (df.index <= end_date_only)]
        
        # Return just close prices
        return pd.DataFrame({"close": df["close"]}, index=df.index)
        
    except Exception as e:
        print(f"  ⚠️ S3 error for {symbol}: {e}")
        return pd.DataFrame()


# ==============================================================================
# RSI Comparison Logic
# ==============================================================================
@dataclass
class RsiComparison:
    """Comparison of RSI values for EDC/EDZ decision."""
    symbol_a: str
    symbol_b: str
    window_a: int
    window_b: int
    
    alpaca_rsi_a: float
    alpaca_rsi_b: float
    alpaca_decision: str
    
    yfinance_rsi_a: float
    yfinance_rsi_b: float
    yfinance_decision: str
    
    s3_rsi_a: float
    s3_rsi_b: float
    s3_decision: str
    
    expected_decision: str  # What Composer chose (EDZ)


def compare_rsi_pair(
    alpaca_client: StockHistoricalDataClient,
    s3_store: MarketDataStore,
    symbol_a: str,
    symbol_b: str,
    window_a: int,
    window_b: int,
    end_date: datetime,
    lookback_days: int = 50,
) -> RsiComparison:
    """Compare RSI values between two symbols across all data sources."""
    
    print(f"\n  Fetching {symbol_a} (window={window_a}) vs {symbol_b} (window={window_b})...")
    
    # Fetch data from all sources
    alpaca_a = fetch_alpaca_data(alpaca_client, symbol_a, end_date, lookback_days)
    alpaca_b = fetch_alpaca_data(alpaca_client, symbol_b, end_date, lookback_days)
    
    yf_a = fetch_yfinance_data(symbol_a, end_date, lookback_days)
    yf_b = fetch_yfinance_data(symbol_b, end_date, lookback_days)
    
    s3_a = fetch_s3_data(s3_store, symbol_a, end_date, lookback_days)
    s3_b = fetch_s3_data(s3_store, symbol_b, end_date, lookback_days)
    
    # Calculate RSI values
    alpaca_rsi_a = calculate_rsi(alpaca_a["close"], window_a) if not alpaca_a.empty else 50.0
    alpaca_rsi_b = calculate_rsi(alpaca_b["close"], window_b) if not alpaca_b.empty else 50.0
    
    yf_rsi_a = calculate_rsi(yf_a["close"], window_a) if not yf_a.empty else 50.0
    yf_rsi_b = calculate_rsi(yf_b["close"], window_b) if not yf_b.empty else 50.0
    
    s3_rsi_a = calculate_rsi(s3_a["close"], window_a) if not s3_a.empty else 50.0
    s3_rsi_b = calculate_rsi(s3_b["close"], window_b) if not s3_b.empty else 50.0
    
    # Determine decisions: if RSI_A > RSI_B → EDC, else → EDZ
    alpaca_decision = "EDC" if alpaca_rsi_a > alpaca_rsi_b else "EDZ"
    yf_decision = "EDC" if yf_rsi_a > yf_rsi_b else "EDZ"
    s3_decision = "EDC" if s3_rsi_a > s3_rsi_b else "EDZ"
    
    return RsiComparison(
        symbol_a=symbol_a,
        symbol_b=symbol_b,
        window_a=window_a,
        window_b=window_b,
        alpaca_rsi_a=alpaca_rsi_a,
        alpaca_rsi_b=alpaca_rsi_b,
        alpaca_decision=alpaca_decision,
        yfinance_rsi_a=yf_rsi_a,
        yfinance_rsi_b=yf_rsi_b,
        yfinance_decision=yf_decision,
        s3_rsi_a=s3_rsi_a,
        s3_rsi_b=s3_rsi_b,
        s3_decision=s3_decision,
        expected_decision="EDZ",  # Composer chose EDZ
    )


def print_comparison(comp: RsiComparison) -> None:
    """Print formatted comparison results."""
    print(f"\n{'='*80}")
    print(f"COMPARISON: RSI({comp.symbol_a}, {comp.window_a}) vs RSI({comp.symbol_b}, {comp.window_b})")
    print(f"Logic: If {comp.symbol_a} > {comp.symbol_b} → EDC (bull), else → EDZ (bear)")
    print(f"Expected (Composer): {comp.expected_decision}")
    print(f"{'='*80}")
    
    print(f"\n{'Source':<12} {'RSI ' + comp.symbol_a:>12} {'RSI ' + comp.symbol_b:>12} {'Diff':>10} {'Decision':>10} {'Match':>8}")
    print("-" * 80)
    
    # Alpaca
    alpaca_diff = comp.alpaca_rsi_a - comp.alpaca_rsi_b
    alpaca_match = "✅" if comp.alpaca_decision == comp.expected_decision else "❌"
    print(f"{'Alpaca':<12} {comp.alpaca_rsi_a:>12.2f} {comp.alpaca_rsi_b:>12.2f} {alpaca_diff:>10.2f} {comp.alpaca_decision:>10} {alpaca_match:>8}")
    
    # yfinance
    yf_diff = comp.yfinance_rsi_a - comp.yfinance_rsi_b
    yf_match = "✅" if comp.yfinance_decision == comp.expected_decision else "❌"
    print(f"{'yfinance':<12} {comp.yfinance_rsi_a:>12.2f} {comp.yfinance_rsi_b:>12.2f} {yf_diff:>10.2f} {comp.yfinance_decision:>10} {yf_match:>8}")
    
    # S3
    s3_diff = comp.s3_rsi_a - comp.s3_rsi_b
    s3_match = "✅" if comp.s3_decision == comp.expected_decision else "❌"
    print(f"{'S3 Lake':<12} {comp.s3_rsi_a:>12.2f} {comp.s3_rsi_b:>12.2f} {s3_diff:>10.2f} {comp.s3_decision:>10} {s3_match:>8}")


def print_raw_prices(
    alpaca_client: StockHistoricalDataClient | None,
    s3_store: MarketDataStore | None,
    symbol: str,
    end_date: datetime,
    num_days: int = 20,
) -> None:
    """Print raw closing prices from all sources for debugging."""
    print(f"\n{'='*80}")
    print(f"RAW CLOSING PRICES: {symbol} (last {num_days} days)")
    print(f"{'='*80}")
    
    alpaca_df = fetch_alpaca_data(alpaca_client, symbol, end_date, num_days + 10)
    yf_df = fetch_yfinance_data(symbol, end_date, num_days + 10)
    s3_df = fetch_s3_data(s3_store, symbol, end_date, num_days + 10)
    
    print(f"\n{'Date':<12} {'Alpaca':>12} {'yfinance':>12} {'S3':>12} {'A-Y Diff':>10} {'A-S3 Diff':>10}")
    print("-" * 80)
    
    # Get all dates
    all_dates = set()
    if not alpaca_df.empty:
        all_dates.update(alpaca_df.index)
    if not yf_df.empty:
        all_dates.update(yf_df.index)
    if not s3_df.empty:
        all_dates.update(s3_df.index)
    
    for date in sorted(all_dates)[-num_days:]:
        alpaca_close = alpaca_df.loc[date, "close"] if date in alpaca_df.index else None
        yf_close = yf_df.loc[date, "close"] if date in yf_df.index else None
        s3_close = s3_df.loc[date, "close"] if date in s3_df.index else None
        
        a_str = f"{alpaca_close:.4f}" if alpaca_close else "N/A"
        y_str = f"{yf_close:.4f}" if yf_close else "N/A"
        s3_str = f"{s3_close:.4f}" if s3_close else "N/A"
        
        ay_diff = ""
        if alpaca_close and yf_close:
            diff = alpaca_close - yf_close
            ay_diff = f"{diff:+.4f}"
        
        as3_diff = ""
        if alpaca_close and s3_close:
            diff = alpaca_close - s3_close
            as3_diff = f"{diff:+.4f}"
        
        print(f"{date}   {a_str:>12} {y_str:>12} {s3_str:>12} {ay_diff:>10} {as3_diff:>10}")


def main() -> None:
    """Run RSI comparison across all data sources."""
    print("=" * 80)
    print("RSI DATA SOURCE COMPARISON")
    print("Identifying which data source matches Composer's EDZ decision")
    print("=" * 80)
    
    # Initialize data sources
    print("\nInitializing data sources...")
    
    try:
        alpaca_client = get_alpaca_client()
        # Test with a quick call
        print("  ✓ Alpaca client ready")
    except Exception as e:
        print(f"  ⚠️ Alpaca not available: {e}")
        alpaca_client = None
    
    try:
        s3_store = MarketDataStore()
        print("  ✓ S3 store ready")
    except Exception as e:
        print(f"  ⚠️ S3 store not available: {e}")
        s3_store = None
    
    # Use yesterday as the evaluation date (last complete trading day)
    # Adjust this to match when you ran the validation
    end_date = datetime(2026, 1, 6, tzinfo=timezone.utc)  # Jan 6, 2026 (day before validation)
    print(f"\nEvaluation date: {end_date.date()}")
    
    # Key RSI comparisons that trigger EDC vs EDZ
    # Format: (symbol_a, symbol_b, window_a, window_b)
    comparisons = [
        # chicken_rice.clj - "IEI vs IWM"
        ("IEI", "IWM", 10, 15),
        
        # ftl_starburst.clj - "Modified Foreign Rat"  
        ("IEI", "IWM", 11, 16),
        ("IEI", "EEM", 11, 16),
        
        # rains_em_dancer.clj - multiple checks
        ("IEI", "IWM", 10, 12),
        ("IEI", "IWM", 10, 15),
        ("IGIB", "SPY", 10, 10),
        ("IGIB", "EEM", 15, 15),
        
        # sisyphus_lowvol.clj
        ("IEI", "IWM", 10, 15),
        ("IGIB", "EEM", 15, 15),
    ]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_comparisons = []
    for comp in comparisons:
        if comp not in seen:
            seen.add(comp)
            unique_comparisons.append(comp)
    
    print(f"\nRunning {len(unique_comparisons)} unique RSI comparisons...")
    
    results = []
    for symbol_a, symbol_b, window_a, window_b in unique_comparisons:
        result = compare_rsi_pair(
            alpaca_client,
            s3_store,
            symbol_a,
            symbol_b,
            window_a,
            window_b,
            end_date,
        )
        results.append(result)
        print_comparison(result)
    
    # Print raw prices for key symbols
    key_symbols = ["IEI", "IWM", "EEM", "IGIB", "SPY"]
    for symbol in key_symbols:
        print_raw_prices(alpaca_client, s3_store, symbol, end_date)
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    alpaca_matches = sum(1 for r in results if r.alpaca_decision == r.expected_decision)
    yf_matches = sum(1 for r in results if r.yfinance_decision == r.expected_decision)
    s3_matches = sum(1 for r in results if r.s3_decision == r.expected_decision)
    
    total = len(results)
    print(f"\nData source accuracy (matching Composer's EDZ decision):")
    print(f"  Alpaca:   {alpaca_matches}/{total} ({alpaca_matches/total*100:.0f}%)")
    print(f"  yfinance: {yf_matches}/{total} ({yf_matches/total*100:.0f}%)")
    print(f"  S3 Lake:  {s3_matches}/{total} ({s3_matches/total*100:.0f}%)")
    
    # Recommendation
    print("\n" + "-" * 80)
    if yf_matches > alpaca_matches and yf_matches > s3_matches:
        print("📊 RECOMMENDATION: yfinance data produces correct EDZ decisions")
        print("   Consider refreshing S3 datalake with yfinance data for these symbols")
    elif alpaca_matches > yf_matches and alpaca_matches > s3_matches:
        print("📊 RECOMMENDATION: Alpaca data produces correct EDZ decisions")
        print("   Verify S3 datalake is using Alpaca with correct adjustment settings")
    elif s3_matches > alpaca_matches and s3_matches > yf_matches:
        print("📊 RECOMMENDATION: S3 data is correct - check other calculation issues")
    else:
        print("📊 INCONCLUSIVE: All sources produce similar results")
        print("   The issue may be in calculation timing or partial bar handling")
    print("-" * 80)


if __name__ == "__main__":
    main()
