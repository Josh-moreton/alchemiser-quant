#!/usr/bin/env python3
"""
Debug where the strategy engine gets its data vs direct S3 queries.
"""

import pandas as pd
from datetime import datetime, timedelta
import pytz
import yfinance as yf

# Initialize S3 access
from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore

store = MarketDataStore()

def wilder_rsi(prices: pd.Series, window: int = 14) -> float:
    """Wilder's RSI using exponential smoothing."""
    delta = prices.diff()
    gains = delta.clip(lower=0)
    losses = (-delta).clip(lower=0)
    
    alpha = 1.0 / window
    avg_gain = gains.ewm(alpha=alpha, min_periods=window, adjust=False).mean()
    avg_loss = losses.ewm(alpha=alpha, min_periods=window, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1])


print("=" * 70)
print("CHECKING S3 DATA FRESHNESS")
print("=" * 70)

for symbol in ["XLK", "KMLM", "IWM", "IEI"]:
    df = store.read_symbol_data(symbol)
    if df is not None and len(df) > 0:
        # Get last 5 rows
        last_rows = df.tail(5)
        print(f"\n{symbol} - Last 5 rows from S3:")
        print(last_rows[["close"]].to_string())
        
        # Latest date is in index
        latest = df.index.max()
        print(f"Latest date in S3: {latest}")
    else:
        print(f"\n{symbol}: NO DATA or empty")

print("\n" + "=" * 70)
print("COMPARING AGAINST CURRENT DATE")
print("=" * 70)

ny_tz = pytz.timezone("America/New_York")
now = datetime.now(ny_tz)
print(f"Current time (NY): {now}")

# Now get fresh yfinance data for comparison
print("\n" + "=" * 70)
print("FRESH YFINANCE DATA")
print("=" * 70)

for symbol in ["XLK", "KMLM"]:
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="10d")
    print(f"\n{symbol} - Last 5 rows from yfinance:")
    print(hist.tail(5)[["Close"]].to_string())
    print(f"Latest date: {hist.index.max()}")

print("\n" + "=" * 70)
print("RSI COMPARISON WITH MATCHING DATE RANGES")
print("=" * 70)

for symbol in ["XLK", "KMLM"]:
    # Get S3 data
    s3_df = store.read_symbol_data(symbol)
    s3_latest = s3_df.index.max()
    
    # Get yfinance data
    ticker = yf.Ticker(symbol)
    yf_hist = ticker.history(period="60d")
    yf_latest = yf_hist.index.max()
    
    print(f"\n{symbol}:")
    print(f"  S3 latest date: {s3_latest}")
    print(f"  YF latest date: {yf_latest}")
    
    # Calculate RSI from each using ALL data
    s3_rsi = wilder_rsi(s3_df["close"], 10)
    yf_rsi = wilder_rsi(yf_hist["Close"], 10)
    
    print(f"  S3 RSI(10) [up to {s3_latest.date()}]: {s3_rsi:.2f}")
    print(f"  YF RSI(10) [up to {yf_latest.date()}]: {yf_rsi:.2f}")
    
    # Check if cutting off YF at S3's latest date gives same RSI
    s3_latest_naive = s3_latest.tz_localize(None) if s3_latest.tzinfo is None else s3_latest.tz_convert(None)
    yf_hist_trimmed = yf_hist[yf_hist.index.tz_localize(None) <= s3_latest_naive]
    if len(yf_hist_trimmed) >= 10:
        yf_trimmed_rsi = wilder_rsi(yf_hist_trimmed["Close"], 10)
        print(f"  YF RSI(10) trimmed to S3 date range: {yf_trimmed_rsi:.2f}")
    
    # Show the price difference for the last common date
    print(f"\n  Price comparison on {s3_latest.date()}:")
    s3_price = float(s3_df.loc[s3_latest, "close"])
    
    # Find matching date in yfinance
    yf_on_date = yf_hist[yf_hist.index.date == s3_latest.date()]
    if len(yf_on_date) > 0:
        yf_price = float(yf_on_date["Close"].iloc[0])
        print(f"    S3: {s3_price:.4f}")
        print(f"    YF: {yf_price:.4f}")
        print(f"    Diff: {s3_price - yf_price:.4f}")
    else:
        print(f"    S3: {s3_price:.4f}")
        print(f"    YF: No data for this date")

print("\n" + "=" * 70)
print("KEY QUESTION: WHY DOES STRATEGY TRACE SHOW DIFFERENT RSI?")
print("=" * 70)
print("""
Strategy trace showed:
  XLK RSI(10) = 59.26
  KMLM RSI(10) = 77.57

But our direct S3 query shows:
  XLK RSI(10) ~ 58.68
  KMLM RSI(10) ~ 57.58

The strategy engine must be:
1. Using different data (cached adapter with live bar?)
2. Using different RSI calculation
3. Reading from a different data source entirely
""")
