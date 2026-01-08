#!/usr/bin/env python3
"""Business Unit: Scripts | Status: current.

Debug script to compare RSI values for ftl_starburst key decision points.
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


def main() -> None:
    """Compare RSI values for ftl_starburst decisions."""
    print("=" * 70)
    print("FTL Starburst RSI Decision Debug")
    print("=" * 70)
    
    # Fetch data for key symbols
    symbols_config = {
        # TECL/TECS decision
        "XLK": {"window": 10, "group": "TECL/TECS"},
        "KMLM": {"window": 10, "group": "TECL/TECS"},
        # EDC/EDZ decision
        "IEI": {"window": 11, "group": "EDC/EDZ"},
        "IWM": {"window": 16, "group": "EDC/EDZ"},
        "EEM": {"window": 16, "group": "EDC/EDZ"},
    }
    
    results: dict[str, dict] = {}
    
    for sym, config in symbols_config.items():
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period="1y")
            if hist.empty:
                print(f"{sym}: No data")
                continue
            
            prices = hist["Close"]
            window = config["window"]
            
            # Our RSI calculation
            our_rsi = TechnicalIndicators.rsi(prices, window=window)
            rsi_val = float(our_rsi.iloc[-1])
            
            # Get last few days of RSI to see trend
            last_5_rsi = our_rsi.tail(5).tolist()
            
            results[sym] = {
                "rsi": rsi_val,
                "window": window,
                "group": config["group"],
                "last_date": hist.index[-1].strftime("%Y-%m-%d"),
                "last_price": float(prices.iloc[-1]),
                "last_5_rsi": last_5_rsi,
            }
            
            print(f"\n{sym} RSI({window}) = {rsi_val:.2f}")
            print(f"  Last price: ${results[sym]['last_price']:.2f} (as of {results[sym]['last_date']})")
            print(f"  Last 5 RSI: {[f'{r:.1f}' for r in last_5_rsi]}")
            
        except Exception as e:
            print(f"{sym}: Error - {e}")
    
    # Analyze decisions
    print("\n" + "=" * 70)
    print("DECISION ANALYSIS")
    print("=" * 70)
    
    # TECL/TECS decision: (> (rsi "XLK" {:window 10}) (rsi "KMLM" {:window 10}))
    if "XLK" in results and "KMLM" in results:
        xlk_rsi = results["XLK"]["rsi"]
        kmlm_rsi = results["KMLM"]["rsi"]
        decision = xlk_rsi > kmlm_rsi
        selected = "TECL (bull)" if decision else "TECS (bear)"
        
        print(f"\n1. TECL/TECS Decision:")
        print(f"   Condition: RSI(XLK, 10) > RSI(KMLM, 10)")
        print(f"   Values: {xlk_rsi:.2f} > {kmlm_rsi:.2f} = {decision}")
        print(f"   -> Selected: {selected}")
        print(f"   EXPECTED (Composer): TECL (bull)")
        print(f"   MATCH: {'YES ✓' if selected.startswith('TECL') else 'NO ✗ <-- BUG'}")
    
    # EDC/EDZ decision: First check EEM price vs MA(200), then RSI comparison
    if "IEI" in results and "IWM" in results:
        iei_rsi = results["IEI"]["rsi"]
        iwm_rsi = results["IWM"]["rsi"]
        decision = iei_rsi > iwm_rsi
        selected = "EDC (bull)" if decision else "EDZ (bear)"
        
        print(f"\n2. EDC/EDZ Decision (when EEM > MA200):")
        print(f"   Condition: RSI(IEI, 11) > RSI(IWM, 16)")
        print(f"   Values: {iei_rsi:.2f} > {iwm_rsi:.2f} = {decision}")
        print(f"   -> Selected: {selected}")
        print(f"   EXPECTED (Composer): EDC (bull)")
        print(f"   MATCH: {'YES ✓' if selected.startswith('EDC') else 'NO ✗ <-- BUG'}")
    
    # Check EEM price vs 200 SMA
    if "EEM" in results:
        print(f"\n3. EEM Price vs 200-day SMA:")
        try:
            ticker = yf.Ticker("EEM")
            hist = ticker.history(period="1y")
            prices = hist["Close"]
            current_price = float(prices.iloc[-1])
            ma_200 = TechnicalIndicators.moving_average(prices, window=200)
            ma_200_val = float(ma_200.iloc[-1])
            above_ma = current_price > ma_200_val
            
            print(f"   Current Price: ${current_price:.2f}")
            print(f"   200-day SMA: ${ma_200_val:.2f}")
            print(f"   Price > MA200: {above_ma}")
            print(f"   -> Takes {'BULLISH' if above_ma else 'BEARISH'} branch")
        except Exception as e:
            print(f"   Error: {e}")
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("""
If RSI values don't match Composer, check:
1. Data source difference (S3 cache vs live yfinance)
2. RSI calculation method (Wilder's vs SMA-based)
3. Partial bar handling (including today's bar or not)
4. Data freshness (cache may have older data)

Key trace from strategy run showed:
- XLK RSI(10) = 59.26, KMLM RSI(10) = 77.57 -> False -> TECS
- IEI RSI(11) = 57.60, IWM RSI(16) = 60.56 -> False -> EDZ
""")


if __name__ == "__main__":
    main()
