#!/usr/bin/env python3
"""Compare RSI values from S3 vs yfinance data."""

import sys
sys.path.insert(0, "functions/strategy_worker")
sys.path.insert(0, "layers/shared")

import pandas as pd
import yfinance as yf
from indicators.indicators import TechnicalIndicators


def main():
    # Load S3 data
    xlp = pd.read_parquet("/tmp/xlp.parquet")
    bond = pd.read_parquet("/tmp/bond.parquet")

    # Calculate RSI from S3 data
    xlp_prices = xlp["close"]
    bond_prices = bond["close"]

    xlp_rsi = TechnicalIndicators.rsi(xlp_prices, window=10)
    bond_rsi = TechnicalIndicators.rsi(bond_prices, window=10)

    print("=== RSI from S3 data (as of 2025-12-31) ===")
    print(f"XLP RSI(10): {xlp_rsi.iloc[-1]:.2f}")
    print(f"BOND RSI(10): {bond_rsi.iloc[-1]:.2f}")

    if xlp_rsi.iloc[-1] < bond_rsi.iloc[-1]:
        print("→ select-bottom 1 picks: XLP (lower RSI)")
    else:
        print("→ select-bottom 1 picks: BOND (lower RSI)")

    # Now fetch yfinance data for comparison
    xlp_yf = yf.Ticker("XLP").history(period="1y")["Close"]
    bond_yf = yf.Ticker("BOND").history(period="1y")["Close"]

    xlp_rsi_yf = TechnicalIndicators.rsi(xlp_yf, window=10)
    bond_rsi_yf = TechnicalIndicators.rsi(bond_yf, window=10)

    print()
    print("=== RSI from yfinance (includes today) ===")
    print(f"Latest date in yfinance: {xlp_yf.index[-1].date()}")
    print(f"XLP RSI(10): {xlp_rsi_yf.iloc[-1]:.2f}")
    print(f"BOND RSI(10): {bond_rsi_yf.iloc[-1]:.2f}")

    if xlp_rsi_yf.iloc[-1] < bond_rsi_yf.iloc[-1]:
        print("→ select-bottom 1 picks: XLP (lower RSI)")
    else:
        print("→ select-bottom 1 picks: BOND (lower RSI)")


if __name__ == "__main__":
    main()
