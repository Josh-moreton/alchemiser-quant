#!/usr/bin/env python3
"""Test Alpaca Adjustment.ALL vs yfinance adjusted prices.

Business Unit: Scripts | Status: current.

This script compares data fetched directly from Alpaca with Adjustment.ALL
against yfinance adjusted prices to identify any discrepancies.
"""

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import Adjustment
from datetime import datetime
import os
import yfinance as yf
import pandas as pd
from dotenv import load_dotenv

load_dotenv()


def get_alpaca_client() -> StockHistoricalDataClient:
    """Get authenticated Alpaca client."""
    api_key = os.environ.get("ALPACA_KEY") or os.environ.get("ALPACA_API_KEY") or os.environ.get("APCA_API_KEY_ID")
    api_secret = os.environ.get("ALPACA_SECRET") or os.environ.get("ALPACA_API_SECRET") or os.environ.get("APCA_API_SECRET_KEY")

    if not api_key or not api_secret:
        raise RuntimeError("Alpaca credentials not found in environment")

    return StockHistoricalDataClient(api_key, api_secret)


def fetch_alpaca_bars(client: StockHistoricalDataClient, symbol: str, start: datetime, end: datetime) -> pd.DataFrame:
    """Fetch bars from Alpaca with Adjustment.ALL."""
    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Day,
        start=start,
        end=end,
        adjustment=Adjustment.ALL,
    )

    response = client.get_stock_bars(request)
    bars = response[symbol]

    data = []
    for bar in bars:
        data.append({
            "date": bar.timestamp.date(),
            "open": float(bar.open),
            "high": float(bar.high),
            "low": float(bar.low),
            "close": float(bar.close),
            "volume": int(bar.volume),
        })

    df = pd.DataFrame(data)
    df.set_index("date", inplace=True)
    return df


def fetch_yfinance_bars(symbol: str, start: str, end: str) -> pd.DataFrame:
    """Fetch adjusted bars from yfinance."""
    ticker = yf.Ticker(symbol)
    df = ticker.history(start=start, end=end)
    df.index = df.index.date
    return df


def compare_data_sources(symbol: str, start: datetime, end: datetime) -> None:
    """Compare Alpaca Adjustment.ALL with yfinance adjusted prices."""
    print(f"\n{'=' * 60}")
    print(f"Comparing {symbol}: Alpaca (Adjustment.ALL) vs yfinance (adjusted)")
    print("=" * 60)

    client = get_alpaca_client()

    # Fetch from both sources
    alpaca_df = fetch_alpaca_bars(client, symbol, start, end)
    yf_df = fetch_yfinance_bars(symbol, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))

    print(f"\n{'Date':<12} {'Alpaca Close':>14} {'yfinance Close':>14} {'Difference':>12} {'Pct Diff':>10}")
    print("-" * 64)

    # Compare last 15 trading days
    for date in alpaca_df.index[-15:]:
        alpaca_close = alpaca_df.loc[date, "close"]
        if date in yf_df.index:
            yf_close = yf_df.loc[date, "Close"]
            diff = alpaca_close - yf_close
            pct_diff = (diff / yf_close) * 100 if yf_close != 0 else 0
            flag = " ***" if abs(pct_diff) > 0.1 else ""
            print(f"{date}   {alpaca_close:>14.4f} {yf_close:>14.4f} {diff:>12.4f} {pct_diff:>9.2f}%{flag}")
        else:
            print(f"{date}   {alpaca_close:>14.4f} {'N/A':>14} {'N/A':>12}")


def main() -> None:
    """Run the comparison for dividend-paying ETFs."""
    start = datetime(2024, 12, 1)
    end = datetime(2025, 1, 2)

    # Test BOND (known to have dividend on 2024-12-31)
    compare_data_sources("BOND", start, end)

    # Test XLP for comparison
    compare_data_sources("XLP", start, end)

    # Also test a non-dividend stock for sanity check
    compare_data_sources("SPY", start, end)

    print("\n" + "=" * 60)
    print("*** = Difference > 0.1% (potential adjustment issue)")
    print("=" * 60)


if __name__ == "__main__":
    main()
