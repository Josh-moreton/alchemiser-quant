import yfinance as yf
import pandas as pd
import numpy as np

# Debug script to understand the data alignment issue
print("Debugging data alignment issue...")

# Fetch data
print("Fetching TQQQ data...")
tqqq = yf.download('TQQQ', start="2020-01-01", progress=False)
print(f"TQQQ shape: {tqqq.shape}")
print(f"TQQQ index type: {type(tqqq.index)}")
print(f"TQQQ columns: {tqqq.columns.tolist()}")
print(f"TQQQ first few dates: {tqqq.index[:5].tolist()}")

print("\nFetching LQQ3.L data...")
lqq3 = yf.download('LQQ3.L', start="2020-01-01", progress=False)
print(f"LQQ3 shape: {lqq3.shape}")
print(f"LQQ3 index type: {type(lqq3.index)}")
print(f"LQQ3 columns: {lqq3.columns.tolist()}")
print(f"LQQ3 first few dates: {lqq3.index[:5].tolist()}")

# Check for any multi-level columns
print(f"\nTQQQ columns levels: {tqqq.columns.nlevels}")
print(f"LQQ3 columns levels: {lqq3.columns.nlevels}")

# Calculate SMA
print("\nCalculating 200-day SMA...")
tqqq['SMA_200'] = tqqq['Close'].rolling(window=200).mean()
print("SMA calculation successful")

# Check for any issues with signal calculation
print("\nGenerating signals...")
tqqq['Signal'] = np.where(tqqq['Close'] > tqqq['SMA_200'], 1, 0)
print("Signal generation successful")

# Check data alignment
print("\nChecking date ranges...")
print(f"TQQQ date range: {tqqq.index.min()} to {tqqq.index.max()}")
print(f"LQQ3 date range: {lqq3.index.min()} to {lqq3.index.max()}")

# Find common dates
common_dates = tqqq.index.intersection(lqq3.index)
print(f"Common dates: {len(common_dates)}")
print(f"First common date: {common_dates.min()}")
print(f"Last common date: {common_dates.max()}")
