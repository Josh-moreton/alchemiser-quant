#!/usr/bin/env python3
"""Debug script to compare S3 and yfinance data formats."""

import tempfile
import warnings
from pathlib import Path

import boto3
import pandas as pd
import yfinance as yf

warnings.filterwarnings("ignore")

# Get S3 data
s3 = boto3.client("s3")
response = s3.get_object(Bucket="alchemiser-shared-market-data", Key="AAPL/daily.parquet")
with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
    tmp.write(response["Body"].read())
    s3_df = pd.read_parquet(tmp.name)
    Path(tmp.name).unlink()

# Get yfinance data (just recent period to match)
yf_df = yf.download("AAPL", start="2024-11-01", end="2024-11-15", progress=False, auto_adjust=False)
yf_df.columns = yf_df.columns.get_level_values(0)

print("S3 data sample:")
print(s3_df[["timestamp", "close", "volume"]].head(5))
print()
print("yfinance data sample:")
print(yf_df[["Close", "Adj Close", "Volume"]].head(5))
print()

# Compare one date
s3_row = s3_df.iloc[0]
s3_date = pd.to_datetime(s3_row["timestamp"]).strftime("%Y-%m-%d")
print(f"S3 date: {s3_date}, close: {s3_row['close']}, volume: {int(s3_row['volume'])}")

yf_dates = yf_df.index.strftime("%Y-%m-%d").tolist()
if s3_date in yf_dates:
    yf_row = yf_df.loc[yf_df.index.strftime("%Y-%m-%d") == s3_date].iloc[0]
    print(
        f"yf date: {s3_date}, close: {yf_row['Close']}, adj_close: {yf_row['Adj Close']}, volume: {int(yf_row['Volume'])}"
    )
    print()
    diff_close = abs(s3_row["close"] - yf_row["Close"])
    diff_adj = abs(s3_row["close"] - yf_row["Adj Close"])
    print(f"Difference: close={diff_close:.4f}, adj_close={diff_adj:.4f}")
    print(f"Volume diff: {abs(int(s3_row['volume']) - int(yf_row['Volume']))}")
