#!/usr/bin/env python3
"""Compare RSI calculations between our system and yfinance.

Business Unit: Scripts | Status: current.

This script compares RSI values for key symbols to identify calculation differences.
"""

import os
import sys
from datetime import date, timedelta

import pandas as pd
import yfinance as yf

# Set up paths
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, os.path.join(project_root, "functions", "strategy_worker"))
sys.path.insert(0, os.path.join(project_root, "layers", "shared"))

os.environ["MARKET_DATA_BUCKET"] = "alchemiser-dev-market-data"
os.environ.setdefault("AWS_REGION", "ap-southeast-2")


def compute_rsi_wilder(prices: pd.Series, window: int) -> float:
    """Compute RSI using Wilder's smoothing (our method)."""
    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    alpha = 1.0 / window
    avg_gain = gain.ewm(alpha=alpha, adjust=False).mean()
    avg_loss = loss.ewm(alpha=alpha, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]


def compute_rsi_sma(prices: pd.Series, window: int) -> float:
    """Compute RSI using SMA (simpler method, sometimes used)."""
    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=window).mean()
    avg_loss = loss.rolling(window=window).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi.iloc[-1]


def get_s3_prices(symbol: str) -> pd.Series:
    """Get prices from S3."""
    from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore
    
    store = MarketDataStore()
    df = store.read_symbol_data(symbol)
    if df is None:
        raise ValueError(f"No data for {symbol}")
    
    # Ensure sorted by date
    if 'timestamp' in df.columns:
        df = df.sort_values('timestamp')
    
    return pd.Series(df['close'].values)


def get_yfinance_prices(symbol: str, days: int = 300) -> pd.Series:
    """Get prices from yfinance."""
    end = date.today()
    start = end - timedelta(days=days)
    
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start, end=end)
    
    return df['Close']


def main() -> None:
    """Compare RSI calculations."""
    print("=" * 80)
    print("RSI Calculation Comparison: S3 vs yfinance")
    print("=" * 80)
    
    # Key symbols and windows from ftl_starburst decision tree
    comparisons = [
        ("XLK", 10),   # Tech momentum check
        ("KMLM", 10),  # vs XLK
        ("IEI", 11),   # EM bull/bear check
        ("IWM", 16),   # vs IEI
        ("IEF", 20),   # Overcompensating frontrunner
        ("PSQ", 60),   # vs IEF
        ("AGG", 15),   # WAM Core check
        ("QQQ", 15),   # vs AGG
        ("VIXM", 14),  # Volatility check
    ]
    
    print(f"\n{'Symbol':<8} {'Window':<8} {'S3 Wilder':<12} {'YF Wilder':<12} {'S3 SMA':<12} {'YF SMA':<12}")
    print("-" * 80)
    
    for symbol, window in comparisons:
        try:
            # Get prices from both sources
            s3_prices = get_s3_prices(symbol)
            yf_prices = get_yfinance_prices(symbol)
            
            # Compute RSI using both methods on both data sources
            s3_wilder = compute_rsi_wilder(s3_prices, window)
            yf_wilder = compute_rsi_wilder(yf_prices, window)
            s3_sma = compute_rsi_sma(s3_prices, window)
            yf_sma = compute_rsi_sma(yf_prices, window)
            
            print(f"{symbol:<8} {window:<8} {s3_wilder:<12.4f} {yf_wilder:<12.4f} {s3_sma:<12.4f} {yf_sma:<12.4f}")
        except Exception as e:
            print(f"{symbol:<8} {window:<8} ERROR: {e}")
    
    print("\n" + "=" * 80)
    print("Key Decision Points from ftl_starburst:")
    print("=" * 80)
    
    # Get prices for key comparisons
    xlk_s3 = get_s3_prices("XLK")
    kmlm_s3 = get_s3_prices("KMLM")
    xlk_yf = get_yfinance_prices("XLK")
    kmlm_yf = get_yfinance_prices("KMLM")
    
    xlk_rsi_s3 = compute_rsi_wilder(xlk_s3, 10)
    kmlm_rsi_s3 = compute_rsi_wilder(kmlm_s3, 10)
    xlk_rsi_yf = compute_rsi_wilder(xlk_yf, 10)
    kmlm_rsi_yf = compute_rsi_wilder(kmlm_yf, 10)
    
    print(f"\n1. XLK vs KMLM (TECL/TECS decision):")
    print(f"   S3:       XLK RSI(10)={xlk_rsi_s3:.4f}  vs  KMLM RSI(10)={kmlm_rsi_s3:.4f}")
    print(f"            XLK > KMLM ? {xlk_rsi_s3 > kmlm_rsi_s3} → {'TECL' if xlk_rsi_s3 > kmlm_rsi_s3 else 'TECS'}")
    print(f"   yfinance: XLK RSI(10)={xlk_rsi_yf:.4f}  vs  KMLM RSI(10)={kmlm_rsi_yf:.4f}")
    print(f"            XLK > KMLM ? {xlk_rsi_yf > kmlm_rsi_yf} → {'TECL' if xlk_rsi_yf > kmlm_rsi_yf else 'TECS'}")
    
    iei_s3 = get_s3_prices("IEI")
    iwm_s3 = get_s3_prices("IWM")
    iei_yf = get_yfinance_prices("IEI")
    iwm_yf = get_yfinance_prices("IWM")
    
    iei_rsi_s3 = compute_rsi_wilder(iei_s3, 11)
    iwm_rsi_s3 = compute_rsi_wilder(iwm_s3, 16)
    iei_rsi_yf = compute_rsi_wilder(iei_yf, 11)
    iwm_rsi_yf = compute_rsi_wilder(iwm_yf, 16)
    
    print(f"\n2. IEI vs IWM (EDC/EDZ decision):")
    print(f"   S3:       IEI RSI(11)={iei_rsi_s3:.4f}  vs  IWM RSI(16)={iwm_rsi_s3:.4f}")
    print(f"            IEI > IWM ? {iei_rsi_s3 > iwm_rsi_s3} → {'EDC' if iei_rsi_s3 > iwm_rsi_s3 else 'EDZ'}")
    print(f"   yfinance: IEI RSI(11)={iei_rsi_yf:.4f}  vs  IWM RSI(16)={iwm_rsi_yf:.4f}")
    print(f"            IEI > IWM ? {iei_rsi_yf > iwm_rsi_yf} → {'EDC' if iei_rsi_yf > iwm_rsi_yf else 'EDZ'}")
    
    # Check data freshness
    print("\n" + "=" * 80)
    print("Data Freshness Check:")
    print("=" * 80)
    
    from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore
    store = MarketDataStore()
    
    for symbol in ["XLK", "KMLM", "IEI", "IWM"]:
        s3_df = store.read_symbol_data(symbol)
        if s3_df is not None and 'timestamp' in s3_df.columns:
            last_date = pd.to_datetime(s3_df['timestamp']).max()
            print(f"  {symbol}: S3 last date = {last_date.date()}, rows = {len(s3_df)}")


if __name__ == "__main__":
    main()
