#!/usr/bin/env python3
"""Business Unit: diagnostic | Status: current.

Diagnostic script to compare RSI and cumulative return indicators
computed with T-0 (live bar) vs T-1 (previous close) data.

This script investigates signal divergence between our calculations and
Composer's live signals by:
1. Fetching close prices from S3 historical data
2. Fetching close prices from Alpaca historical API
3. Computing RSI and cumulative return using both T-0 and T-1 approaches
4. Comparing values against strategy thresholds to determine which triggers

Usage:
    poetry run python scripts/diagnose_t0_vs_t1_indicators.py --date 2026-01-14
    poetry run python scripts/diagnose_t0_vs_t1_indicators.py --date 2026-01-14 --verbose
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pandas as pd

# Set default bucket before importing modules that need it
os.environ.setdefault("MARKET_DATA_BUCKET", "alchemiser-prod-market-data")

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "layers" / "shared"))
sys.path.insert(0, str(project_root / "functions" / "strategy_worker"))

from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)

# ============================================================================
# Configuration: RSI thresholds extracted from strategy DSL files
# ============================================================================

# defence.clj: Uses RSI(7) filter for top 2 selection, no explicit threshold
# nuclear.clj: RSI(10) thresholds trigger UVXY
# simons_full_kmlm.clj: RSI(10) thresholds trigger UVXY
# tqqq_ftlt_2.clj: RSI(10) thresholds trigger UVXY/VIXY

RSI_THRESHOLDS: dict[str, list[tuple[str, int, float, str]]] = {
    # Strategy: [(symbol, window, threshold, direction)]
    # direction: ">" means RSI > threshold triggers risk-off
    "simons_full_kmlm": [
        ("QQQE", 10, 79, ">"),  # RSI > 79 -> UVXY
        ("VTV", 10, 79, ">"),
        ("VOX", 10, 79, ">"),
        ("TECL", 10, 79, ">"),
        ("VOOG", 10, 79, ">"),
        ("VOOV", 10, 79, ">"),
        ("XLP", 10, 75, ">"),  # Lower threshold for XLP
        ("TQQQ", 10, 79, ">"),
        ("XLY", 10, 80, ">"),
        ("FAS", 10, 80, ">"),
        ("SPY", 10, 80, ">"),
        ("UVXY", 21, 65, ">"),  # Volatility regime check
    ],
    "tqqq_ftlt_2": [
        ("SPY", 10, 80, ">"),
        ("TECL", 10, 79, ">"),
        ("XLP", 10, 77.5, ">"),  # -> VIXY
        ("XLP", 10, 80, ">"),  # -> UVXY
        ("QQQ", 10, 79, ">"),  # -> VIXY
        ("QQQ", 10, 81, ">"),  # -> UVXY
        ("QQQE", 10, 79, ">"),  # -> VIXY
        ("QQQE", 10, 83, ">"),  # -> UVXY
        ("VTV", 10, 79, ">"),
        ("XLY", 10, 80, ">"),
        ("XLF", 10, 80, ">"),
    ],
    "nuclear": [
        ("SPY", 10, 79, ">"),
        ("SPY", 10, 81, ">"),
        ("IOO", 10, 79, ">"),
        ("IOO", 10, 81, ">"),
        ("TQQQ", 10, 79, ">"),
        ("TQQQ", 10, 81, ">"),
        ("VTV", 10, 79, ">"),
        ("VTV", 10, 81, ">"),
        ("XLF", 10, 79, ">"),
        ("XLF", 10, 81, ">"),
        ("VOX", 10, 79, ">"),
    ],
}

# Cumulative return thresholds for nuclear.clj
# Uses moving-average-return window 90 for nuclear portfolio ranking
CUMULATIVE_RETURN_SYMBOLS = {
    "nuclear": [
        ("SMR", 90),
        ("BWXT", 90),
        ("LEU", 90),
        ("EXC", 90),
        ("NLR", 90),
        ("OKLO", 90),
    ],
}


@dataclass
class IndicatorResult:
    """Result of indicator computation."""

    symbol: str
    indicator_type: str
    window: int
    t0_value: float | None  # With today's bar
    t1_value: float | None  # Without today's bar (yesterday's close)
    threshold: float
    direction: str
    t0_triggers: bool
    t1_triggers: bool


def compute_rsi(prices: pd.Series, window: int = 14) -> pd.Series:
    """Compute RSI using Wilder's smoothing method.

    This matches the implementation in indicators.py.
    """
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
    """Compute rolling average of percentage returns.

    This matches the implementation in indicators.py.
    """
    if len(prices) < window:
        return pd.Series([0.0] * len(prices), index=prices.index)

    returns = prices.pct_change()
    return returns.rolling(window=window).mean() * 100


def fetch_s3_prices(
    store: MarketDataStore, symbol: str, end_date: datetime, lookback_days: int = 400
) -> pd.Series | None:
    """Fetch closing prices from S3 Parquet storage.

    Args:
        store: MarketDataStore instance
        symbol: Ticker symbol
        end_date: The 'current' date for analysis (T-0)
        lookback_days: Days of history to fetch

    Returns:
        Series of closing prices indexed by timestamp, or None if not found
    """
    df = store.read_symbol_data(symbol)
    if df is None or df.empty:
        return None

    if "timestamp" not in df.columns:
        return None

    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    df = df.sort_values("timestamp")

    # Filter to lookback period ending at end_date
    end_dt = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59, tzinfo=UTC)
    start_dt = end_dt - timedelta(days=lookback_days)

    df = df[(df["timestamp"] >= start_dt) & (df["timestamp"] <= end_dt)]

    if df.empty:
        return None

    return pd.Series(df["close"].values, index=df["timestamp"])


def fetch_alpaca_prices(
    symbol: str, end_date: datetime, lookback_days: int = 400
) -> pd.Series | None:
    """Fetch closing prices from Alpaca historical API.

    Args:
        symbol: Ticker symbol
        end_date: The 'current' date for analysis (T-0)
        lookback_days: Days of history to fetch

    Returns:
        Series of closing prices indexed by timestamp, or None if not found
    """
    try:
        from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
        from the_alchemiser.shared.services.market_data_service import MarketDataService

        api_key = os.environ.get("ALPACA__KEY", "")
        secret_key = os.environ.get("ALPACA__SECRET", "")

        if not api_key or not secret_key:
            logger.warning("Alpaca credentials not found in environment")
            return None

        alpaca = AlpacaManager(api_key=api_key, secret_key=secret_key, paper=True)
        market_data = MarketDataService(alpaca)

        # Calculate date range
        start_date = end_date - timedelta(days=lookback_days)

        bars = market_data.get_historical_bars(
            symbol=symbol,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            timeframe="1Day",
        )

        if not bars:
            return None

        # Convert to Series
        timestamps = []
        closes = []

        for bar in bars:
            ts = bar.get("timestamp")
            if isinstance(ts, str):
                if ts.endswith("Z"):
                    ts = ts[:-1] + "+00:00"
                ts = datetime.fromisoformat(ts)
            timestamps.append(ts)
            closes.append(float(bar["close"]))

        return pd.Series(closes, index=timestamps)

    except Exception as e:
        logger.warning(f"Failed to fetch Alpaca data for {symbol}: {e}")
        return None


def analyze_indicator(
    prices: pd.Series,
    symbol: str,
    indicator_type: str,
    window: int,
    threshold: float,
    direction: str,
    analysis_date: datetime,
    verbose: bool = False,
) -> IndicatorResult | None:
    """Analyze an indicator with T-0 vs T-1 data.

    Args:
        prices: Full price series including analysis_date
        symbol: Ticker symbol
        indicator_type: 'rsi' or 'cumulative_return'
        window: Indicator window period
        threshold: Trigger threshold
        direction: '>' or '<'
        analysis_date: The T-0 date
        verbose: Whether to print detailed output

    Returns:
        IndicatorResult or None if insufficient data
    """
    if prices is None or len(prices) < window + 10:
        return None

    # Find the analysis date bar
    analysis_dt = datetime(
        analysis_date.year, analysis_date.month, analysis_date.day, tzinfo=UTC
    )

    # Get T-0 prices (includes analysis_date)
    t0_prices = prices[prices.index.date <= analysis_dt.date()]

    # Get T-1 prices (excludes analysis_date)
    t1_prices = prices[prices.index.date < analysis_dt.date()]

    if len(t0_prices) < window or len(t1_prices) < window:
        return None

    # Compute indicator values
    if indicator_type == "rsi":
        t0_series = compute_rsi(t0_prices, window)
        t1_series = compute_rsi(t1_prices, window)
    elif indicator_type == "moving_average_return":
        t0_series = compute_moving_average_return(t0_prices, window)
        t1_series = compute_moving_average_return(t1_prices, window)
    else:
        return None

    t0_value = float(t0_series.iloc[-1]) if len(t0_series) > 0 else None
    t1_value = float(t1_series.iloc[-1]) if len(t1_series) > 0 else None

    # Determine if threshold is triggered
    if direction == ">":
        t0_triggers = t0_value > threshold if t0_value is not None else False
        t1_triggers = t1_value > threshold if t1_value is not None else False
    else:
        t0_triggers = t0_value < threshold if t0_value is not None else False
        t1_triggers = t1_value < threshold if t1_value is not None else False

    if verbose:
        trigger_diff = "*** DIVERGENCE ***" if t0_triggers != t1_triggers else ""
        print(
            f"  {symbol:6} | {indicator_type:8} | window={window:2} | "
            f"T-0: {t0_value:7.2f} | T-1: {t1_value:7.2f} | "
            f"threshold {direction} {threshold:5.1f} | "
            f"T-0 triggers: {t0_triggers} | T-1 triggers: {t1_triggers} {trigger_diff}"
        )

    return IndicatorResult(
        symbol=symbol,
        indicator_type=indicator_type,
        window=window,
        t0_value=t0_value,
        t1_value=t1_value,
        threshold=threshold,
        direction=direction,
        t0_triggers=t0_triggers,
        t1_triggers=t1_triggers,
    )


def run_diagnosis(
    analysis_date: datetime,
    data_source: str = "s3",
    verbose: bool = False,
) -> list[IndicatorResult]:
    """Run full diagnosis for all strategies.

    Args:
        analysis_date: The date to analyze (T-0)
        data_source: 's3' or 'alpaca'
        verbose: Print detailed output

    Returns:
        List of IndicatorResult objects
    """
    results: list[IndicatorResult] = []

    # Initialize data source
    if data_source == "s3":
        store = MarketDataStore()
        fetch_func = lambda sym: fetch_s3_prices(store, sym, analysis_date)
        print(f"\n📦 Using S3 data source (bucket: {store.bucket_name})")
    else:
        fetch_func = lambda sym: fetch_alpaca_prices(sym, analysis_date)
        print("\n🦙 Using Alpaca historical API")

    print(f"📅 Analysis date (T-0): {analysis_date.strftime('%Y-%m-%d')}")
    print(f"📅 T-1 (previous close): {(analysis_date - timedelta(days=1)).strftime('%Y-%m-%d')}")
    print("=" * 100)

    # Collect all unique symbols
    all_symbols: set[str] = set()
    for strategy, thresholds in RSI_THRESHOLDS.items():
        for symbol, window, threshold, direction in thresholds:
            all_symbols.add(symbol)

    for strategy, cum_ret_symbols in CUMULATIVE_RETURN_SYMBOLS.items():
        for symbol, window in cum_ret_symbols:
            all_symbols.add(symbol)

    # Fetch prices for all symbols
    print(f"\n🔄 Fetching prices for {len(all_symbols)} symbols...")
    price_cache: dict[str, pd.Series | None] = {}
    for symbol in sorted(all_symbols):
        prices = fetch_func(symbol)
        price_cache[symbol] = prices
        status = f"✓ {len(prices)} bars" if prices is not None else "✗ no data"
        if verbose:
            print(f"  {symbol}: {status}")

    # Analyze RSI thresholds per strategy
    print("\n" + "=" * 100)
    print("RSI ANALYSIS")
    print("=" * 100)

    for strategy, thresholds in RSI_THRESHOLDS.items():
        print(f"\n📊 Strategy: {strategy}")
        print("-" * 90)

        for symbol, window, threshold, direction in thresholds:
            prices = price_cache.get(symbol)
            if prices is None:
                if verbose:
                    print(f"  {symbol:6} | SKIPPED - no data")
                continue

            result = analyze_indicator(
                prices=prices,
                symbol=symbol,
                indicator_type="rsi",
                window=window,
                threshold=threshold,
                direction=direction,
                analysis_date=analysis_date,
                verbose=verbose,
            )

            if result:
                results.append(result)

    # Analyze cumulative return for nuclear strategy
    print("\n" + "=" * 100)
    print("MOVING AVERAGE RETURN ANALYSIS (nuclear strategy ranking)")
    print("=" * 100)

    for strategy, symbols in CUMULATIVE_RETURN_SYMBOLS.items():
        print(f"\n📊 Strategy: {strategy}")
        print("-" * 90)

        symbol_returns: list[tuple[str, float | None, float | None]] = []

        for symbol, window in symbols:
            prices = price_cache.get(symbol)
            if prices is None:
                if verbose:
                    print(f"  {symbol:6} | SKIPPED - no data")
                continue

            # No explicit threshold for ranking - just compute values
            result = analyze_indicator(
                prices=prices,
                symbol=symbol,
                indicator_type="moving_average_return",
                window=window,
                threshold=0,  # Not used for ranking
                direction=">",
                analysis_date=analysis_date,
                verbose=verbose,
            )

            if result:
                symbol_returns.append((symbol, result.t0_value, result.t1_value))

        # Show top 3 ranking difference
        if symbol_returns:
            print("\n  Ranking by moving-average-return(90):")
            t0_ranked = sorted(
                [(s, v) for s, v, _ in symbol_returns if v is not None],
                key=lambda x: x[1],
                reverse=True,
            )
            t1_ranked = sorted(
                [(s, v) for s, _, v in symbol_returns if v is not None],
                key=lambda x: x[1],
                reverse=True,
            )

            print(f"\n  T-0 Top 3: {[s for s, _ in t0_ranked[:3]]}")
            print(f"  T-1 Top 3: {[s for s, _ in t1_ranked[:3]]}")

            t0_set = set(s for s, _ in t0_ranked[:3])
            t1_set = set(s for s, _ in t1_ranked[:3])
            if t0_set != t1_set:
                print("  *** RANKING DIVERGENCE DETECTED ***")

    # Summary
    print("\n" + "=" * 100)
    print("SUMMARY: Divergences (T-0 vs T-1 trigger different outcomes)")
    print("=" * 100)

    divergences = [r for r in results if r.t0_triggers != r.t1_triggers]
    if divergences:
        for d in divergences:
            print(
                f"  {d.symbol:6} | {d.indicator_type}({d.window}) | "
                f"T-0={d.t0_value:.2f} -> {d.t0_triggers} | "
                f"T-1={d.t1_value:.2f} -> {d.t1_triggers} | "
                f"threshold {d.direction} {d.threshold}"
            )
        print(f"\n  Total divergences: {len(divergences)}")
    else:
        print("  No divergences found with current thresholds.")

    return results


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Diagnose T-0 vs T-1 indicator divergence for signal validation"
    )
    parser.add_argument(
        "--date",
        type=str,
        required=True,
        help="Analysis date in YYYY-MM-DD format (T-0)",
    )
    parser.add_argument(
        "--source",
        type=str,
        choices=["s3", "alpaca"],
        default="s3",
        help="Data source: 's3' (default) or 'alpaca'",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print detailed output for each indicator",
    )

    args = parser.parse_args()

    # Parse date
    try:
        analysis_date = datetime.strptime(args.date, "%Y-%m-%d")
        analysis_date = analysis_date.replace(tzinfo=UTC)
    except ValueError:
        print(f"Error: Invalid date format '{args.date}'. Use YYYY-MM-DD.")
        sys.exit(1)

    print("=" * 100)
    print("T-0 vs T-1 INDICATOR DIAGNOSIS")
    print("=" * 100)
    print("\nThis script compares indicator values computed with:")
    print("  • T-0: Including the analysis date's bar (live bar approach)")
    print("  • T-1: Excluding the analysis date's bar (previous close approach)")
    print("\nOur current production config uses T-1 for RSI (use_live_bar=False).")
    print("Composer's live signals use T-0 data.")
    print("Divergences occur when T-0 triggers a threshold but T-1 does not (or vice versa).")

    run_diagnosis(
        analysis_date=analysis_date,
        data_source=args.source,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
