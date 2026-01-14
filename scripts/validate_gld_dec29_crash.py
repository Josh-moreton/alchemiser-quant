#!/usr/bin/env python3
"""Business Unit: debugging | Status: development.

Validate the GLD Dec 29 2025 crash across multiple data sources.

The Gold strategy diagnostic showed a -4.35% return on Dec 29, 2025.
This script cross-validates that data point against:
1. Our S3/cached data
2. Alpaca Markets API (live)
3. Yahoo Finance (yfinance)

Usage:
    poetry run python scripts/validate_gld_dec29_crash.py

"""

from __future__ import annotations

import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "layers" / "shared"))
sys.path.insert(0, str(PROJECT_ROOT / "functions" / "strategy_worker"))

# Set environment variables for S3 market data access
os.environ.setdefault("MARKET_DATA_BUCKET", "alchemiser-dev-market-data")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")


def get_s3_data() -> pd.DataFrame:
    """Fetch GLD data from our S3/cached store."""
    from the_alchemiser.shared.data_v2.cached_market_data_adapter import (
        CachedMarketDataAdapter,
    )

    print("\n📦 Fetching from S3/Cache...")
    adapter = CachedMarketDataAdapter()
    bars = adapter.get_bars("GLD", "1Y", "1Day")
    df = pd.DataFrame([{"date": b.timestamp.date(), "close": float(b.close)} for b in bars])
    df = df.drop_duplicates(subset=["date"]).sort_values("date").reset_index(drop=True)
    return df


def get_alpaca_data() -> pd.DataFrame | None:
    """Fetch GLD data from Alpaca Markets API."""
    try:
        from alpaca.data.historical import StockHistoricalDataClient
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame

        api_key = os.environ.get("ALPACA_API_KEY")
        api_secret = os.environ.get("ALPACA_SECRET_KEY")

        if not api_key or not api_secret:
            print("⚠️  Alpaca credentials not found in environment")
            return None

        print("\n🦙 Fetching from Alpaca...")
        client = StockHistoricalDataClient(api_key, api_secret)

        request = StockBarsRequest(
            symbol_or_symbols=["GLD"],
            start=datetime(2025, 12, 20),
            end=datetime(2026, 1, 15),
            timeframe=TimeFrame.Day,
        )
        bars = client.get_stock_bars(request)

        records = []
        for bar in bars["GLD"]:
            records.append({"date": bar.timestamp.date(), "close": float(bar.close)})

        df = pd.DataFrame(records)
        df = df.drop_duplicates(subset=["date"]).sort_values("date").reset_index(drop=True)
        return df

    except ImportError:
        print("⚠️  alpaca-py not installed")
        return None
    except Exception as e:
        print(f"⚠️  Alpaca error: {e}")
        return None


def get_yfinance_data() -> pd.DataFrame | None:
    """Fetch GLD data from Yahoo Finance."""
    try:
        import yfinance as yf

        print("\n📈 Fetching from Yahoo Finance...")
        ticker = yf.Ticker("GLD")
        hist = ticker.history(start="2025-12-20", end="2026-01-15")

        if hist.empty:
            print("⚠️  yfinance returned empty data")
            return None

        df = hist.reset_index()
        df = df.rename(columns={"Date": "date", "Close": "close"})
        df["date"] = pd.to_datetime(df["date"]).dt.date
        df = df[["date", "close"]]
        df = df.drop_duplicates(subset=["date"]).sort_values("date").reset_index(drop=True)
        return df

    except ImportError:
        print("⚠️  yfinance not installed")
        return None
    except Exception as e:
        print(f"⚠️  yfinance error: {e}")
        return None


def calculate_returns(df: pd.DataFrame) -> pd.DataFrame:
    """Add return column to dataframe."""
    df = df.copy()
    df["return_pct"] = df["close"].pct_change() * 100
    return df


def main() -> None:
    """Cross-validate GLD Dec 29 crash across data sources."""
    print("=" * 70)
    print("GLD DEC 29 2025 CRASH VALIDATION")
    print("Checking if -4.35% return is consistent across data sources")
    print("=" * 70)

    target_date = date(2025, 12, 29)
    date_range = (date(2025, 12, 22), date(2026, 1, 6))

    # Collect data from all sources
    sources: dict[str, pd.DataFrame | None] = {}

    sources["S3/Cache"] = get_s3_data()
    sources["Alpaca"] = get_alpaca_data()
    sources["Yahoo Finance"] = get_yfinance_data()

    # Filter to date range and calculate returns
    for name, df in sources.items():
        if df is not None:
            mask = (df["date"] >= date_range[0]) & (df["date"] <= date_range[1])
            sources[name] = calculate_returns(df[mask].reset_index(drop=True))

    # Display comparison
    print("\n" + "=" * 70)
    print("DATA COMPARISON (Dec 22 - Jan 6)")
    print("=" * 70)

    # Build comparison table
    all_dates = set()
    for df in sources.values():
        if df is not None:
            all_dates.update(df["date"].tolist())

    all_dates = sorted(all_dates)

    print(f"\n{'Date':<12}", end="")
    for name in sources:
        if sources[name] is not None:
            print(f"{name + ' Close':>18} {name + ' Ret%':>12}", end="")
    print()
    print("-" * 100)

    for d in all_dates:
        row = f"{d!s:<12}"
        for name, df in sources.items():
            if df is not None:
                match = df[df["date"] == d]
                if len(match) > 0:
                    close = match.iloc[0]["close"]
                    ret = match.iloc[0]["return_pct"]
                    ret_str = f"{ret:+.2f}%" if pd.notna(ret) else "N/A"
                    row += f"{close:>18.2f} {ret_str:>12}"
                else:
                    row += f"{'N/A':>18} {'N/A':>12}"
        print(row)

    # Specific focus on Dec 29
    print("\n" + "=" * 70)
    print(f"FOCUS: {target_date} (The Crash Day)")
    print("=" * 70)

    dec29_data = {}
    for name, df in sources.items():
        if df is not None:
            match = df[df["date"] == target_date]
            if len(match) > 0:
                dec29_data[name] = {
                    "close": match.iloc[0]["close"],
                    "return": match.iloc[0]["return_pct"],
                }

    if not dec29_data:
        print(f"\n❌ No data found for {target_date} in any source!")
        return

    print(f"\n{'Source':<20} {'Close Price':>15} {'Return':>12}")
    print("-" * 50)
    for name, data in dec29_data.items():
        ret_str = f"{data['return']:+.2f}%" if pd.notna(data["return"]) else "N/A"
        print(f"{name:<20} ${data['close']:>14.2f} {ret_str:>12}")

    # Validation
    print("\n" + "=" * 70)
    print("VALIDATION RESULT")
    print("=" * 70)

    returns = [d["return"] for d in dec29_data.values() if pd.notna(d.get("return"))]

    if len(returns) < 2:
        print("\n⚠️  Not enough data sources to cross-validate")
        return

    # Check if all returns are within tolerance
    tolerance = 0.1  # 0.1% tolerance for differences
    min_ret, max_ret = min(returns), max(returns)
    spread = max_ret - min_ret

    print(f"\nReturns across sources: {[f'{r:.2f}%' for r in returns]}")
    print(f"Min: {min_ret:.2f}%, Max: {max_ret:.2f}%, Spread: {spread:.2f}%")

    if spread <= tolerance:
        print(f"\n✅ DATA VALIDATED: All sources agree within {tolerance}% tolerance")
        print(f"   The {returns[0]:.2f}% crash on Dec 29 is REAL")
    else:
        print(f"\n⚠️  DATA DISCREPANCY: Spread of {spread:.2f}% exceeds {tolerance}% tolerance")
        print("   Investigate which source has incorrect data")

    # Also check Dec 26 (previous trading day) to understand the context
    print("\n" + "-" * 70)
    print("CONTEXT: Dec 26 → Dec 29 Price Movement")
    print("-" * 70)

    dec26_date = date(2025, 12, 26)
    for name, df in sources.items():
        if df is not None:
            dec26 = df[df["date"] == dec26_date]
            dec29 = df[df["date"] == target_date]
            if len(dec26) > 0 and len(dec29) > 0:
                p26 = dec26.iloc[0]["close"]
                p29 = dec29.iloc[0]["close"]
                change = ((p29 / p26) - 1) * 100
                print(f"{name}: ${p26:.2f} → ${p29:.2f} = {change:+.2f}%")


if __name__ == "__main__":
    main()
