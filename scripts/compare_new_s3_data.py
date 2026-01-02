#!/usr/bin/env python3
"""Compare new S3 data against yfinance to verify adjustment is correct."""

import pandas as pd
import yfinance as yf
from dotenv import load_dotenv

load_dotenv()

# Read new S3 data and set timestamp as index
s3_bond = pd.read_parquet('/tmp/BOND_bars_new.parquet')
s3_bond['date'] = pd.to_datetime(s3_bond['timestamp']).dt.date
s3_bond.set_index('date', inplace=True)

s3_xlp = pd.read_parquet('/tmp/XLP_bars_new.parquet')
s3_xlp['date'] = pd.to_datetime(s3_xlp['timestamp']).dt.date
s3_xlp.set_index('date', inplace=True)

# Get yfinance data for comparison
yf_bond = yf.Ticker('BOND').history(start='2024-12-01', end='2025-01-02')
yf_bond.index = yf_bond.index.date
yf_xlp = yf.Ticker('XLP').history(start='2024-12-01', end='2025-01-02')
yf_xlp.index = yf_xlp.index.date

print("=" * 70)
print("BOND: New S3 Data vs yfinance (adjusted)")
print("=" * 70)
print(f"{'Date':<12} {'S3 Close':>12} {'yfinance':>12} {'Diff':>10} {'Pct':>8}")
print("-" * 70)

for i in range(-10, 0):
    date = s3_bond.index[i]
    s3_close = s3_bond.iloc[i]['close']
    if date in yf_bond.index:
        yf_close = yf_bond.loc[date, 'Close']
        diff = s3_close - yf_close
        pct = (diff / yf_close) * 100
        flag = " ***" if abs(pct) > 0.1 else " OK"
        print(f"{date}   {s3_close:>12.4f} {yf_close:>12.4f} {diff:>10.4f} {pct:>7.2f}%{flag}")

print()
print("=" * 70)
print("XLP: New S3 Data vs yfinance (adjusted)")
print("=" * 70)
print(f"{'Date':<12} {'S3 Close':>12} {'yfinance':>12} {'Diff':>10} {'Pct':>8}")
print("-" * 70)

for i in range(-10, 0):
    date = s3_xlp.index[i]
    s3_close = s3_xlp.iloc[i]['close']
    if date in yf_xlp.index:
        yf_close = yf_xlp.loc[date, 'Close']
        diff = s3_close - yf_close
        pct = (diff / yf_close) * 100
        flag = " ***" if abs(pct) > 0.1 else " OK"
        print(f"{date}   {s3_close:>12.4f} {yf_close:>12.4f} {diff:>10.4f} {pct:>7.2f}%{flag}")

# Now check RSI comparison
print()
print("=" * 70)
print("RSI(10) Comparison - Should now match!")  
print("=" * 70)

def calc_rsi(series, window=10):
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1/window, min_periods=window, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/window, min_periods=window, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

s3_bond_rsi = calc_rsi(s3_bond['close']).iloc[-1]
s3_xlp_rsi = calc_rsi(s3_xlp['close']).iloc[-1]

yf_bond_rsi = calc_rsi(yf_bond['Close']).iloc[-1]
yf_xlp_rsi = calc_rsi(yf_xlp['Close']).iloc[-1]

print(f"\nS3 Data RSI(10) as of {s3_bond.index[-1]}:")
print(f"  BOND: {s3_bond_rsi:.2f}")
print(f"  XLP:  {s3_xlp_rsi:.2f}")
print(f"  -> select-bottom 1 picks: {'BOND' if s3_bond_rsi < s3_xlp_rsi else 'XLP'}")

print(f"\nyfinance RSI(10):")
print(f"  BOND: {yf_bond_rsi:.2f}")
print(f"  XLP:  {yf_xlp_rsi:.2f}")
print(f"  -> select-bottom 1 picks: {'BOND' if yf_bond_rsi < yf_xlp_rsi else 'XLP'}")

if (s3_bond_rsi < s3_xlp_rsi) == (yf_bond_rsi < yf_xlp_rsi):
    print("\n✅ RSI rankings MATCH - chicken_rice should now select correctly!")
else:
    print("\n❌ RSI rankings still differ - need to investigate further")
