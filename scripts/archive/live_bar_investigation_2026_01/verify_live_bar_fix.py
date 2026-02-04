#!/usr/bin/env python3
"""Business Unit: diagnostic | Status: current.

Verify that use_live_bar=True fix resolves signal discrepancies across strategies.

This script checks if T-0 data (with live bar) correctly produces signals
matching the live Composer signals for the 2026-01-14 validation failures.

Usage:
    poetry run python scripts/verify_live_bar_fix.py
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd

# Set default bucket before importing modules
os.environ.setdefault("MARKET_DATA_BUCKET", "alchemiser-prod-market-data")

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "layers" / "shared"))
sys.path.insert(0, str(project_root / "functions" / "strategy_worker"))

from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)

# Analysis date from validation CSV
ANALYSIS_DATE = datetime(2026, 1, 14, tzinfo=UTC)


@dataclass
class ValidationCase:
    """A validation case from the CSV."""

    strategy: str
    our_signal: list[str]
    live_signal: list[str]
    notes: str


# Validation failures from signal_validation_2026-01-14.csv
VALIDATION_CASES = [
    ValidationCase(
        strategy="defence",
        our_signal=["KTOS", "RCAT"],
        live_signal=["KTOS", "SPAI"],
        notes="RSI(7) filter for top 2 selection",
    ),
    ValidationCase(
        strategy="nuclear",
        our_signal=["LEU", "OKLO", "BWXT"],
        live_signal=["LEU", "OKLO", "NLR"],
        notes="moving-average-return(90) ranking for top 3",
    ),
    ValidationCase(
        strategy="simons_full_kmlm",
        our_signal=["SVIX"],
        live_signal=["UVXY"],
        notes="RSI(10) overbought checks trigger UVXY",
    ),
    ValidationCase(
        strategy="tqqq_ftlt_2",
        our_signal=["EDC", "RETL", "TNA"],
        live_signal=["VIXY"],
        notes="RSI(10) overbought checks trigger VIXY",
    ),
]


def compute_rsi(prices: pd.Series, window: int = 14) -> pd.Series:
    """Compute RSI using Wilder's smoothing method."""
    if len(prices) < window:
        return pd.Series([50.0] * len(prices), index=prices.index)

    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    alpha = 1.0 / window
    avg_gain = gain.ewm(alpha=alpha, adjust=False).mean()
    avg_loss = loss.ewm(alpha=alpha, adjust=False).mean()

    rs = avg_gain.divide(avg_loss, fill_value=0.0)
    rsi = 100 - (100 / (1 + rs))

    return rsi.fillna(50.0)


def compute_moving_average_return(prices: pd.Series, window: int = 90) -> pd.Series:
    """Compute rolling average of percentage returns."""
    if len(prices) < window:
        return pd.Series([0.0] * len(prices), index=prices.index)

    returns = prices.pct_change()
    return returns.rolling(window=window).mean() * 100


def fetch_prices(store: MarketDataStore, symbol: str, include_t0: bool) -> pd.Series | None:
    """Fetch closing prices from S3.

    Args:
        store: MarketDataStore instance
        symbol: Ticker symbol
        include_t0: If True, include ANALYSIS_DATE; if False, exclude it (T-1)

    Returns:
        Series of closing prices indexed by timestamp
    """
    df = store.read_symbol_data(symbol)
    if df is None or df.empty or "timestamp" not in df.columns:
        return None

    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.sort_values("timestamp")

    # Filter based on T-0 or T-1
    if include_t0:
        end_dt = datetime(
            ANALYSIS_DATE.year, ANALYSIS_DATE.month, ANALYSIS_DATE.day, 23, 59, 59, tzinfo=UTC
        )
    else:
        end_dt = ANALYSIS_DATE - timedelta(days=1)
        end_dt = datetime(end_dt.year, end_dt.month, end_dt.day, 23, 59, 59, tzinfo=UTC)

    start_dt = end_dt - timedelta(days=400)
    df = df[(df["timestamp"] >= start_dt) & (df["timestamp"] <= end_dt)]

    if df.empty:
        return None

    return pd.Series(df["close"].values, index=df["timestamp"])


def get_latest_value(prices: pd.Series, indicator_func, window: int) -> float | None:
    """Compute indicator and return latest value."""
    if prices is None or len(prices) < window:
        return None
    series = indicator_func(prices, window)
    if len(series) > 0 and not pd.isna(series.iloc[-1]):
        return float(series.iloc[-1])
    return None


def verify_defence(store: MarketDataStore) -> dict:
    """Verify defence strategy: RSI(7) filter for top 2 selection.

    Defence uses filter (rsi {:window 7}) (select-top 2) on these assets:
    AIRO, BBAI, KTOS, ONDS, OSS, RCAT, SPAI, UMAC, ITA, ACHR, EVTL, JOBY
    """
    symbols = ["AIRO", "BBAI", "KTOS", "ONDS", "OSS", "RCAT", "SPAI", "UMAC", "ITA", "ACHR", "EVTL", "JOBY"]

    t0_rsi = {}
    t1_rsi = {}

    for symbol in symbols:
        t0_prices = fetch_prices(store, symbol, include_t0=True)
        t1_prices = fetch_prices(store, symbol, include_t0=False)

        t0_val = get_latest_value(t0_prices, compute_rsi, 7)
        t1_val = get_latest_value(t1_prices, compute_rsi, 7)

        if t0_val is not None:
            t0_rsi[symbol] = t0_val
        if t1_val is not None:
            t1_rsi[symbol] = t1_val

    # Select top 2 by RSI
    t0_top2 = sorted(t0_rsi.items(), key=lambda x: x[1], reverse=True)[:2]
    t1_top2 = sorted(t1_rsi.items(), key=lambda x: x[1], reverse=True)[:2]

    return {
        "strategy": "defence",
        "indicator": "RSI(7) select-top 2",
        "t0_ranking": [(s, round(v, 2)) for s, v in sorted(t0_rsi.items(), key=lambda x: x[1], reverse=True)],
        "t1_ranking": [(s, round(v, 2)) for s, v in sorted(t1_rsi.items(), key=lambda x: x[1], reverse=True)],
        "t0_top2": [s for s, _ in t0_top2],
        "t1_top2": [s for s, _ in t1_top2],
        "live_signal": ["KTOS", "SPAI"],
        "t0_matches_live": set([s for s, _ in t0_top2]) == set(["KTOS", "SPAI"]),
        "t1_matches_live": set([s for s, _ in t1_top2]) == set(["KTOS", "SPAI"]),
    }


def verify_nuclear(store: MarketDataStore) -> dict:
    """Verify nuclear strategy: moving-average-return(90) for top 3 selection."""
    symbols = ["SMR", "BWXT", "LEU", "EXC", "NLR", "OKLO"]

    t0_mar = {}
    t1_mar = {}

    for symbol in symbols:
        t0_prices = fetch_prices(store, symbol, include_t0=True)
        t1_prices = fetch_prices(store, symbol, include_t0=False)

        t0_val = get_latest_value(t0_prices, compute_moving_average_return, 90)
        t1_val = get_latest_value(t1_prices, compute_moving_average_return, 90)

        if t0_val is not None:
            t0_mar[symbol] = t0_val
        if t1_val is not None:
            t1_mar[symbol] = t1_val

    # Select top 3 by moving average return
    t0_top3 = sorted(t0_mar.items(), key=lambda x: x[1], reverse=True)[:3]
    t1_top3 = sorted(t1_mar.items(), key=lambda x: x[1], reverse=True)[:3]

    return {
        "strategy": "nuclear",
        "indicator": "moving-average-return(90) select-top 3",
        "t0_ranking": [(s, round(v, 4)) for s, v in sorted(t0_mar.items(), key=lambda x: x[1], reverse=True)],
        "t1_ranking": [(s, round(v, 4)) for s, v in sorted(t1_mar.items(), key=lambda x: x[1], reverse=True)],
        "t0_top3": [s for s, _ in t0_top3],
        "t1_top3": [s for s, _ in t1_top3],
        "live_signal": ["LEU", "OKLO", "NLR"],
        "t0_matches_live": set([s for s, _ in t0_top3]) == set(["LEU", "OKLO", "NLR"]),
        "t1_matches_live": set([s for s, _ in t1_top3]) == set(["LEU", "OKLO", "NLR"]),
    }


def verify_simons_kmlm(store: MarketDataStore) -> dict:
    """Verify simons_full_kmlm: RSI(10) overbought checks trigger UVXY.

    The strategy checks RSI(10) > 79 on QQQE, VTV, VOX, TECL, VOOG, VOOV, TQQQ
    and RSI(10) > 75 on XLP, RSI(10) > 80 on XLY, FAS, SPY
    If ANY of these trigger, it selects UVXY instead of equity assets.
    """
    checks = [
        ("QQQE", 10, 79),
        ("VTV", 10, 79),
        ("VOX", 10, 79),
        ("TECL", 10, 79),
        ("VOOG", 10, 79),
        ("VOOV", 10, 79),
        ("XLP", 10, 75),  # Lower threshold
        ("TQQQ", 10, 79),
        ("XLY", 10, 80),
        ("FAS", 10, 80),
        ("SPY", 10, 80),
    ]

    t0_triggers = []
    t1_triggers = []
    details = []

    for symbol, window, threshold in checks:
        t0_prices = fetch_prices(store, symbol, include_t0=True)
        t1_prices = fetch_prices(store, symbol, include_t0=False)

        t0_val = get_latest_value(t0_prices, compute_rsi, window)
        t1_val = get_latest_value(t1_prices, compute_rsi, window)

        t0_trigger = t0_val is not None and t0_val > threshold
        t1_trigger = t1_val is not None and t1_val > threshold

        if t0_trigger:
            t0_triggers.append(symbol)
        if t1_trigger:
            t1_triggers.append(symbol)

        details.append({
            "symbol": symbol,
            "threshold": threshold,
            "t0_rsi": round(t0_val, 2) if t0_val else None,
            "t1_rsi": round(t1_val, 2) if t1_val else None,
            "t0_triggers": t0_trigger,
            "t1_triggers": t1_trigger,
        })

    # If any check triggers, strategy selects UVXY
    t0_selects_uvxy = len(t0_triggers) > 0
    t1_selects_uvxy = len(t1_triggers) > 0

    return {
        "strategy": "simons_full_kmlm",
        "indicator": "RSI(10) overbought checks",
        "details": details,
        "t0_triggers": t0_triggers,
        "t1_triggers": t1_triggers,
        "t0_selects": "UVXY" if t0_selects_uvxy else "equity (SVIX path)",
        "t1_selects": "UVXY" if t1_selects_uvxy else "equity (SVIX path)",
        "live_signal": "UVXY",
        "t0_matches_live": t0_selects_uvxy,
        "t1_matches_live": t1_selects_uvxy,
    }


def verify_tqqq_ftlt_2(store: MarketDataStore) -> dict:
    """Verify tqqq_ftlt_2: RSI(10) overbought checks trigger VIXY/UVXY.

    The strategy checks:
    - SPY RSI(10) > 80 -> UVXY
    - TECL RSI(10) > 79 -> UVXY
    - XLP RSI(10) > 77.5 -> VIXY, > 80 -> UVXY
    - QQQ RSI(10) > 79 -> VIXY, > 81 -> UVXY
    - QQQE RSI(10) > 79 -> VIXY, > 83 -> UVXY
    - VTV RSI(10) > 79 -> VIXY
    - XLY RSI(10) > 80 -> VIXY
    - XLF RSI(10) > 80 -> VIXY
    """
    checks = [
        ("SPY", 10, 80, "UVXY"),
        ("TECL", 10, 79, "UVXY"),
        ("XLP", 10, 77.5, "VIXY"),
        ("XLP", 10, 80, "UVXY"),
        ("QQQ", 10, 79, "VIXY"),
        ("QQQ", 10, 81, "UVXY"),
        ("QQQE", 10, 79, "VIXY"),
        ("QQQE", 10, 83, "UVXY"),
        ("VTV", 10, 79, "VIXY"),
        ("XLY", 10, 80, "VIXY"),
        ("XLF", 10, 80, "VIXY"),
    ]

    t0_triggers = []
    t1_triggers = []
    details = []

    for symbol, window, threshold, vix_product in checks:
        t0_prices = fetch_prices(store, symbol, include_t0=True)
        t1_prices = fetch_prices(store, symbol, include_t0=False)

        t0_val = get_latest_value(t0_prices, compute_rsi, window)
        t1_val = get_latest_value(t1_prices, compute_rsi, window)

        t0_trigger = t0_val is not None and t0_val > threshold
        t1_trigger = t1_val is not None and t1_val > threshold

        if t0_trigger:
            t0_triggers.append((symbol, threshold, vix_product))
        if t1_trigger:
            t1_triggers.append((symbol, threshold, vix_product))

        details.append({
            "symbol": symbol,
            "threshold": threshold,
            "vix_product": vix_product,
            "t0_rsi": round(t0_val, 2) if t0_val else None,
            "t1_rsi": round(t1_val, 2) if t1_val else None,
            "t0_triggers": t0_trigger,
            "t1_triggers": t1_trigger,
        })

    # First trigger in the cascade determines outcome
    t0_selects = None
    for d in details:
        if d["t0_triggers"]:
            t0_selects = d["vix_product"]
            break

    t1_selects = None
    for d in details:
        if d["t1_triggers"]:
            t1_selects = d["vix_product"]
            break

    return {
        "strategy": "tqqq_ftlt_2",
        "indicator": "RSI(10) overbought cascade",
        "details": details,
        "t0_triggers": [(s, t, p) for s, t, p in t0_triggers],
        "t1_triggers": [(s, t, p) for s, t, p in t1_triggers],
        "t0_selects": t0_selects or "equity path",
        "t1_selects": t1_selects or "equity path",
        "live_signal": "VIXY",
        "t0_matches_live": t0_selects == "VIXY",
        "t1_matches_live": t1_selects == "VIXY",
    }


def main() -> None:
    """Run verification for all validation cases."""
    print("=" * 100)
    print("VERIFICATION: Does use_live_bar=True fix signal discrepancies?")
    print("=" * 100)
    print(f"\n📅 Analysis date: {ANALYSIS_DATE.strftime('%Y-%m-%d')}")
    print("   T-0 = includes analysis date bar (use_live_bar=True)")
    print("   T-1 = excludes analysis date bar (use_live_bar=False)")
    print()

    store = MarketDataStore()
    all_pass = True

    # Verify each strategy
    results = [
        verify_defence(store),
        verify_nuclear(store),
        verify_simons_kmlm(store),
        verify_tqqq_ftlt_2(store),
    ]

    for result in results:
        print("\n" + "=" * 100)
        print(f"📊 Strategy: {result['strategy']}")
        print(f"   Indicator: {result['indicator']}")
        print("-" * 100)

        if "ranking" in result.get("t0_ranking", ""):
            pass  # Skip detailed ranking output

        if "details" in result:
            print("\n   RSI Check Details:")
            for d in result["details"]:
                trigger_mark = "🔥" if d["t0_triggers"] != d["t1_triggers"] else "  "
                print(
                    f"   {trigger_mark} {d['symbol']:6} | "
                    f"threshold > {d['threshold']:5} | "
                    f"T-0: {d['t0_rsi']:7.2f} {'✓' if d['t0_triggers'] else ' '} | "
                    f"T-1: {d['t1_rsi']:7.2f} {'✓' if d['t1_triggers'] else ' '}"
                )

        if "t0_top2" in result:
            print(f"\n   T-0 Top 2: {result['t0_top2']}")
            print(f"   T-1 Top 2: {result['t1_top2']}")
            print(f"   Live:      {result['live_signal']}")

        if "t0_top3" in result:
            print(f"\n   T-0 Top 3: {result['t0_top3']}")
            print(f"   T-1 Top 3: {result['t1_top3']}")
            print(f"   Live:      {result['live_signal']}")

        if "t0_selects" in result:
            print(f"\n   T-0 selects: {result['t0_selects']}")
            print(f"   T-1 selects: {result['t1_selects']}")
            print(f"   Live signal: {result['live_signal']}")

        t0_pass = result["t0_matches_live"]
        t1_pass = result["t1_matches_live"]

        print()
        if t0_pass and not t1_pass:
            print("   ✅ T-0 (use_live_bar=True) MATCHES live signal")
            print("   ❌ T-1 (use_live_bar=False) does NOT match live signal")
            print("   → FIX CONFIRMED: use_live_bar=True resolves this discrepancy")
        elif t0_pass and t1_pass:
            print("   ✅ Both T-0 and T-1 match live signal (no divergence)")
        elif not t0_pass and not t1_pass:
            print("   ❌ Neither T-0 nor T-1 matches live signal")
            print("   → Different root cause - needs further investigation")
            all_pass = False
        else:
            print("   ⚠️ T-1 matches but T-0 doesn't - unexpected!")
            all_pass = False

    # Summary
    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)

    fixed_count = sum(1 for r in results if r["t0_matches_live"] and not r["t1_matches_live"])
    already_ok = sum(1 for r in results if r["t0_matches_live"] and r["t1_matches_live"])
    still_broken = sum(1 for r in results if not r["t0_matches_live"])

    print(f"\n   Strategies fixed by use_live_bar=True: {fixed_count}")
    print(f"   Strategies already matching:           {already_ok}")
    print(f"   Strategies still not matching:         {still_broken}")

    if all_pass:
        print("\n   ✅ ALL strategies now match live signals with use_live_bar=True")
    else:
        print("\n   ⚠️ Some strategies still have discrepancies - further investigation needed")


if __name__ == "__main__":
    main()
