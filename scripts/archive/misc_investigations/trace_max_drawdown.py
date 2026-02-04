#!/usr/bin/env python3
"""Trace max-drawdown filter decisions for failing strategies.

Business Unit: Scripts | Status: current.

This script traces the max-drawdown filter comparisons to identify
why ftl_starburst_gen2 selects TQQQ when Composer selects NAIL.

The key investigation points:
1. Raw price data alignment
2. Rolling window calculation
3. cummax() peak detection
4. Drawdown formula: (price / peak - 1) * -100
"""

import os
import sys
from datetime import date, datetime, timezone
from decimal import Decimal

import pandas as pd

# Set up paths
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, os.path.join(project_root, "functions", "strategy_worker"))
sys.path.insert(0, os.path.join(project_root, "layers", "shared"))

os.environ["MARKET_DATA_BUCKET"] = "alchemiser-dev-market-data"
os.environ.setdefault("AWS_REGION", "ap-southeast-2")

from the_alchemiser.shared.data_v2.cached_market_data_adapter import CachedMarketDataAdapter
from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore
from the_alchemiser.shared.schemas.indicator_request import IndicatorRequest
from indicators.indicator_service import IndicatorService
from indicators.indicators import TechnicalIndicators


def trace_max_drawdown_comparison(
    symbol_a: str, 
    symbol_b: str, 
    window: int = 12,
    show_raw_data: bool = False,
    use_live_bar: bool = True,
) -> None:
    """Trace max-drawdown comparison between two symbols.
    
    Args:
        symbol_a: First symbol (e.g., "TQQQ")
        symbol_b: Second symbol (e.g., "NAIL")
        window: Lookback window for max-drawdown calculation
        show_raw_data: If True, print raw price and drawdown series
        use_live_bar: If True, append today's partial bar (matches production)
    """
    store = MarketDataStore()
    adapter = CachedMarketDataAdapter(market_data_store=store, append_live_bar=use_live_bar)
    indicator_service = IndicatorService(market_data_service=adapter)
    
    print("=" * 80)
    print(f"MAX-DRAWDOWN FILTER TRACE: {symbol_a} vs {symbol_b}")
    print(f"Window: {window} days | select-bottom 1 (lowest drawdown wins)")
    print(f"Live bar mode: {'ENABLED (matches production)' if use_live_bar else 'DISABLED'}")
    print("=" * 80)
    
    # Fetch raw prices for both symbols
    print("\n1. FETCHING RAW PRICE DATA")
    print("-" * 40)
    
    # Use indicator service's internal method to get consistent data
    request_a = IndicatorRequest(
        request_id="trace-a",
        correlation_id="trace",
        symbol=symbol_a,
        indicator_type="max_drawdown",
        parameters={"window": window},
    )
    request_b = IndicatorRequest(
        request_id="trace-b",
        correlation_id="trace",
        symbol=symbol_b,
        indicator_type="max_drawdown",
        parameters={"window": window},
    )
    
    # Get indicator results
    result_a = indicator_service.get_indicator(request_a)
    result_b = indicator_service.get_indicator(request_b)
    
    mdd_a = float(result_a.metadata["value"])
    mdd_b = float(result_b.metadata["value"])
    
    print(f"\n2. INDICATOR SERVICE RESULTS")
    print("-" * 40)
    print(f"  {symbol_a} max-drawdown({window}) = {mdd_a:.4f}%")
    print(f"  {symbol_b} max-drawdown({window}) = {mdd_b:.4f}%")
    print(f"\n  select-bottom 1 winner: {'%s' % (symbol_a if mdd_a < mdd_b else symbol_b)}")
    print(f"  (lower drawdown = better = wins select-bottom)")
    
    # Now trace the raw calculation
    print(f"\n3. RAW CALCULATION TRACE")
    print("-" * 40)
    
    # Fetch price data directly to trace the computation
    # get_bars returns list[BarModel], convert to DataFrame
    bars_a = adapter.get_bars(symbol_a, period="1M", timeframe="1D")
    bars_b = adapter.get_bars(symbol_b, period="1M", timeframe="1D")
    
    def bars_to_df(bars: list) -> pd.DataFrame:
        """Convert BarModel list to DataFrame."""
        data = []
        for bar in bars:
            data.append({
                "timestamp": bar.timestamp,
                "open": float(bar.open),
                "high": float(bar.high),
                "low": float(bar.low),
                "close": float(bar.close),
                "volume": bar.volume,
            })
        df = pd.DataFrame(data)
        if not df.empty:
            df = df.set_index("timestamp").sort_index()
        return df
    
    prices_a = bars_to_df(bars_a)
    prices_b = bars_to_df(bars_b)
    
    print(f"  {symbol_a}: {len(prices_a)} bars available")
    print(f"  {symbol_b}: {len(prices_b)} bars available")
    
    if prices_a is not None and len(prices_a) > 0:
        closes_a = prices_a["close"]
        print(f"\n  {symbol_a} latest {window + 2} closes:")
        for i, (idx, price) in enumerate(closes_a.tail(window + 2).items()):
            marker = " <-- today" if i == len(closes_a.tail(window + 2)) - 1 else ""
            print(f"    {idx}: ${price:.2f}{marker}")
    
    if prices_b is not None and len(prices_b) > 0:
        closes_b = prices_b["close"]
        print(f"\n  {symbol_b} latest {window + 2} closes:")
        for i, (idx, price) in enumerate(closes_b.tail(window + 2).items()):
            marker = " <-- today" if i == len(closes_b.tail(window + 2)) - 1 else ""
            print(f"    {idx}: ${price:.2f}{marker}")
    
    # Manually compute max-drawdown to trace the logic
    print(f"\n4. STEP-BY-STEP MAX-DRAWDOWN COMPUTATION")
    print("-" * 40)
    
    def trace_mdd_calculation(symbol: str, prices_df: pd.DataFrame, window: int) -> float:
        """Trace max-drawdown calculation step by step."""
        print(f"\n  {symbol}:")
        
        if prices_df.empty:
            print("    No price data available")
            return 0.0
        
        closes = prices_df["close"]
        
        # Get the last window prices
        window_prices = closes.tail(window)
        print(f"    Window prices (last {window}):")
        for idx, price in window_prices.items():
            print(f"      {idx}: ${price:.2f}")
        
        # Compute cummax within window
        cummax = window_prices.cummax()
        print(f"\n    Cumulative max (rolling peak):")
        for idx, peak in cummax.items():
            print(f"      {idx}: ${peak:.2f}")
        
        # Compute drawdown from peak
        drawdown_pct = (window_prices / cummax - 1.0) * 100
        print(f"\n    Drawdown from peak:")
        for idx, dd in drawdown_pct.items():
            print(f"      {idx}: {dd:.2f}%")
        
        # Max drawdown is the most negative (largest decline)
        max_dd = -drawdown_pct.min()
        print(f"\n    Max drawdown = {max_dd:.4f}%")
        return max_dd
    
    if not prices_a.empty and not prices_b.empty:
        traced_mdd_a = trace_mdd_calculation(symbol_a, prices_a, window)
        traced_mdd_b = trace_mdd_calculation(symbol_b, prices_b, window)
        
        print(f"\n5. TRACED RESULTS COMPARISON")
        print("-" * 40)
        print(f"  {symbol_a}: IndicatorService={mdd_a:.4f}%, Traced={traced_mdd_a:.4f}%")
        print(f"  {symbol_b}: IndicatorService={mdd_b:.4f}%, Traced={traced_mdd_b:.4f}%")
        
        if abs(mdd_a - traced_mdd_a) > 0.01 or abs(mdd_b - traced_mdd_b) > 0.01:
            print("\n  ⚠️  DISCREPANCY between IndicatorService and traced calculation!")
            print("     This may indicate different data windows or calculation methods.")
    
    print(f"\n6. FILTER DECISION ANALYSIS")
    print("-" * 40)
    print(f"  select-bottom 1 with max-drawdown:")
    print(f"    - Picks the asset with LOWEST drawdown (least risky)")
    print(f"    - {symbol_a}: {mdd_a:.4f}%")
    print(f"    - {symbol_b}: {mdd_b:.4f}%")
    
    winner = symbol_a if mdd_a < mdd_b else symbol_b
    expected = "NAIL"  # From validation notes
    
    print(f"\n  Our selection: {winner}")
    print(f"  Expected (Composer): {expected}")
    
    if winner != expected:
        print(f"\n  ❌ MISMATCH! We select {winner} but Composer selects {expected}")
        print("\n  Possible causes:")
        print("    1. Different number of bars in lookback window")
        print("    2. Partial bar inclusion/exclusion differences")
        print("    3. Timestamp alignment (UTC vs ET)")
        print("    4. Different close price source (adjusted vs raw)")
    else:
        print(f"\n  ✓ MATCH with Composer")
    
    print("\n" + "=" * 80)


def trace_filter_path(strategy_name: str = "ftl_starburst_gen2") -> None:
    """Trace the decision path leading to the max-drawdown filter."""
    from the_alchemiser.shared.data_v2.cached_market_data_adapter import CachedMarketDataAdapter
    from the_alchemiser.shared.data_v2.market_data_store import MarketDataStore
    from the_alchemiser.shared.schemas.indicator_request import IndicatorRequest
    from indicators.indicator_service import IndicatorService
    
    store = MarketDataStore()
    adapter = CachedMarketDataAdapter(market_data_store=store)
    indicator_service = IndicatorService(market_data_service=adapter)
    
    print("=" * 80)
    print(f"DECISION PATH TRACE: {strategy_name}")
    print("=" * 80)
    
    def get_indicator(symbol: str, indicator_type: str, window: int) -> float:
        """Get indicator value."""
        request = IndicatorRequest(
            request_id="trace",
            correlation_id="trace",
            symbol=symbol,
            indicator_type=indicator_type,
            parameters={"window": window},
        )
        result = indicator_service.get_indicator(request)
        return float(result.metadata["value"])
    
    # Trace the key decision points leading to the TQQQ vs NAIL filter
    # From reading ftl_starburst_gen2.clj:
    # The MAX DD: TQQQ vs NAIL filter is reached via:
    # 1. RSI checks (QQQ, SPY, etc.)
    # 2. Oversold checks (various)
    # 3. SPY RSI(70) < 62 → stdev-return filter path
    # 4. IEF RSI > PSQ RSI → bullish path with max-dd filters
    
    print("\n1. KEY CONDITIONAL CHECKS")
    print("-" * 40)
    
    # Check the conditions that lead to the max-dd filter
    spy_rsi_70 = get_indicator("SPY", "rsi", 70)
    print(f"  SPY RSI(70) = {spy_rsi_70:.2f}")
    print(f"    Condition: SPY RSI(70) > 62? {spy_rsi_70:.2f} > 62 = {spy_rsi_70 > 62}")
    
    if spy_rsi_70 <= 62:
        print("  → Taking stdev-return filter path (not overbought)")
        
        ief_rsi_20 = get_indicator("IEF", "rsi", 20)
        psq_rsi_60 = get_indicator("PSQ", "rsi", 60)
        print(f"\n  IEF RSI(20) = {ief_rsi_20:.2f}")
        print(f"  PSQ RSI(60) = {psq_rsi_60:.2f}")
        print(f"  Condition: IEF RSI > PSQ RSI? {ief_rsi_20:.2f} > {psq_rsi_60:.2f} = {ief_rsi_20 > psq_rsi_60}")
        
        if ief_rsi_20 > psq_rsi_60:
            print("  → Taking BULLISH path (stdev-return select-top filter)")
            print("\n  This path leads to MAX DD filters including TQQQ vs NAIL")
        else:
            print("  → Taking WAM Package path (bearish)")
    else:
        print("  → Taking Overbought path")
    
    print("\n2. OTHER MAX-DD COMPARISONS IN SAME BRANCH")
    print("-" * 40)
    
    # Show all the max-dd comparisons in this branch
    comparisons = [
        ("TQQQ", "UVXY", 11),
        ("TQQQ", "SOXL", 10),
        ("TQQQ", "FNGU", 9),
        ("TQQQ", "UUP", 10),
        ("TQQQ", "VDE", 10),
        ("TQQQ", "SMH", 11),
        ("TQQQ", "AVUV", 12),
        ("TQQQ", "NAIL", 12),
    ]
    
    for sym_a, sym_b, window in comparisons:
        try:
            mdd_a = get_indicator(sym_a, "max_drawdown", window)
            mdd_b = get_indicator(sym_b, "max_drawdown", window)
            winner = sym_a if mdd_a < mdd_b else sym_b
            print(f"  {sym_a} vs {sym_b} (window={window}): {mdd_a:.2f}% vs {mdd_b:.2f}% → {winner}")
        except Exception as e:
            print(f"  {sym_a} vs {sym_b}: Error - {e}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Trace max-drawdown filter decisions")
    parser.add_argument("--symbol-a", default="TQQQ", help="First symbol")
    parser.add_argument("--symbol-b", default="NAIL", help="Second symbol")
    parser.add_argument("--window", type=int, default=12, help="Max-drawdown window")
    parser.add_argument("--trace-path", action="store_true", help="Trace full decision path")
    parser.add_argument("--no-live-bar", action="store_true", help="Disable live bar (test S3 only)")
    
    args = parser.parse_args()
    
    if args.trace_path:
        trace_filter_path()
    
    trace_max_drawdown_comparison(
        args.symbol_a, 
        args.symbol_b, 
        args.window,
        use_live_bar=not args.no_live_bar,
    )
