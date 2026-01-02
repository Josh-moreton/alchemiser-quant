#!/usr/bin/env python3
"""Business Unit: Scripts | Status: current.

Debug script to check indicator values for specific symbols.
Helps diagnose why filter conditions might be evaluating differently than Composer.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "functions" / "strategy_worker"))
sys.path.insert(0, str(PROJECT_ROOT / "layers" / "shared"))

import pandas as pd
import yfinance as yf

from indicators.indicators import TechnicalIndicators
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


def get_price_data(symbol: str, period: str = "1y") -> pd.Series | None:
    """Fetch price data from yfinance."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        if hist.empty:
            return None
        return hist["Close"]
    except Exception as e:
        print(f"  {symbol}: Error fetching data - {e}")
        return None


def get_indicator_values(symbols: list[str], indicator: str, window: int) -> dict[str, float | None]:
    """Get indicator values for a list of symbols."""
    results = {}
    
    for symbol in symbols:
        prices = get_price_data(symbol)
        if prices is None or len(prices) == 0:
            print(f"  {symbol}: No data available")
            results[symbol] = None
            continue
            
        try:
            # Calculate indicator
            if indicator == "rsi":
                values = TechnicalIndicators.rsi(prices, window=window)
            elif indicator == "cumulative_return":
                values = TechnicalIndicators.cumulative_return(prices, window=window)
            elif indicator == "moving_average":
                values = TechnicalIndicators.moving_average(prices, window=window)
            else:
                print(f"  Unknown indicator: {indicator}")
                continue
            
            latest = float(values.iloc[-1]) if len(values) > 0 and not pd.isna(values.iloc[-1]) else None
            results[symbol] = latest
            
        except Exception as e:
            print(f"  {symbol}: Error calculating {indicator} - {e}")
            results[symbol] = None
    
    return results


def main():
    """Main entry point."""
    print("\n" + "=" * 70)
    print("Indicator Value Debugger")
    print("=" * 70)
    
    # Check the XLP vs BOND RSI comparison (from chicken_rice.clj filter)
    print("\n--- XLP vs BOND RSI(10) comparison ---")
    print("(Used in chicken_rice.clj filter - select-bottom 1 picks LOWER RSI)")
    print()
    
    rsi_values = get_indicator_values(["XLP", "BOND"], "rsi", 10)
    for sym, val in sorted(rsi_values.items(), key=lambda x: x[1] if x[1] else 999):
        if val is not None:
            print(f"  {sym}: RSI(10) = {val:.2f}")
        else:
            print(f"  {sym}: RSI(10) = N/A")
    
    if rsi_values.get("XLP") and rsi_values.get("BOND"):
        xlp_rsi = rsi_values["XLP"]
        bond_rsi = rsi_values["BOND"]
        winner = "XLP" if xlp_rsi < bond_rsi else "BOND"
        print(f"\n  → select-bottom 1 would pick: {winner} (lower RSI)")
        print(f"  → Difference: {abs(xlp_rsi - bond_rsi):.2f}")
    
    # Check a few other key indicators from the strategy
    print("\n--- Other key RSI values from chicken_rice conditions ---")
    
    # SPY RSI 70 comparison
    spy_rsi_70 = get_indicator_values(["SPY"], "rsi", 70)
    if spy_rsi_70.get("SPY"):
        print(f"  SPY RSI(70) = {spy_rsi_70['SPY']:.2f} (threshold: 60)")
        print(f"    → Condition (> RSI 60) = {spy_rsi_70['SPY'] > 60}")
    
    # SPY RSI 10 check
    spy_rsi_10 = get_indicator_values(["SPY"], "rsi", 10)
    if spy_rsi_10.get("SPY"):
        print(f"  SPY RSI(10) = {spy_rsi_10['SPY']:.2f} (thresholds: <30 oversold, >80 overbought)")
    
    # QQQ cumulative return
    print("\n--- QQQ cumulative return checks ---")
    qqq_cum_5 = get_indicator_values(["QQQ"], "cumulative_return", 5)
    if qqq_cum_5.get("QQQ"):
        print(f"  QQQ Cumulative Return(5) = {qqq_cum_5['QQQ']:.2f}% (threshold: <-5)")
        print(f"    → Condition (< -5) = {qqq_cum_5['QQQ'] < -5}")
    
    print("\n" + "=" * 70)
    print("Compare these values against what Composer shows!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
