#!/usr/bin/env python3
"""Business Unit: diagnostics | Status: current.

Diagnostic script to test different cumulative return calculation methods.

This script fetches real market data and computes cumulative return using
different methodologies to identify which one matches Composer's logic.

The KMLM vs BIL decision depends on:
1. cumulative-return("QQQ", 15) > cumulative-return("LQD", 30)
2. rsi("IWM", 5) > rsi("DIA", 10)

Usage:
    poetry run python scripts/diagnose_cumret_methods.py
"""

from __future__ import annotations

import os
import sys
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

# Add project paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "functions", "strategy_worker"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "layers", "shared"))

from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


def cumret_method_1(prices: pd.Series, window: int) -> float:
    """Method 1: Our current implementation.
    
    Formula: ((current_price / price_N_periods_ago) - 1) * 100
    Uses shift(window) which compares to the price WINDOW bars back.
    
    Example with window=3:
    - Day 0: $100
    - Day 1: $102
    - Day 2: $105
    - Day 3: $108 (current)
    
    shift(3) gives us $100 (Day 0), so return = (108/100 - 1) * 100 = 8%
    """
    if len(prices) <= window:
        return float("nan")
    series = ((prices / prices.shift(window)) - 1) * 100
    return float(series.iloc[-1])


def cumret_method_2(prices: pd.Series, window: int) -> float:
    """Method 2: Log returns accumulated.
    
    Uses log returns for more accurate compounding.
    Formula: (exp(sum of log returns over window) - 1) * 100
    """
    import numpy as np
    if len(prices) <= window:
        return float("nan")
    log_returns = np.log(prices / prices.shift(1))
    cumulative_log_return = log_returns.iloc[-window:].sum()
    return float((np.exp(cumulative_log_return) - 1) * 100)


def cumret_method_3(prices: pd.Series, window: int) -> float:
    """Method 3: Rolling pct_change sum (simple returns).
    
    Sums simple percentage changes over window.
    Formula: sum(pct_change) * 100
    
    NOTE: This is mathematically incorrect for compounding but
    some platforms use it.
    """
    if len(prices) <= window:
        return float("nan")
    pct_changes = prices.pct_change()
    return float(pct_changes.iloc[-window:].sum() * 100)


def cumret_method_4(prices: pd.Series, window: int) -> float:
    """Method 4: Compare to price (window-1) periods ago.
    
    Off-by-one variant: shift(window-1) instead of shift(window).
    This would give the return over the LAST N-1 complete days plus today.
    """
    if len(prices) <= window - 1:
        return float("nan")
    series = ((prices / prices.shift(window - 1)) - 1) * 100
    return float(series.iloc[-1])


def cumret_method_5(prices: pd.Series, window: int) -> float:
    """Method 5: Compare to price (window+1) periods ago.
    
    Off-by-one variant in the other direction.
    """
    if len(prices) <= window + 1:
        return float("nan")
    series = ((prices / prices.shift(window + 1)) - 1) * 100
    return float(series.iloc[-1])


def cumret_method_6(prices: pd.Series, window: int) -> float:
    """Method 6: Product of (1 + daily_return) - 1.
    
    Compound return calculation.
    Formula: (product of (1 + r_i) for i in last N periods) - 1) * 100
    """
    if len(prices) <= window:
        return float("nan")
    daily_returns = prices.pct_change()
    compound_factor = (1 + daily_returns.iloc[-window:]).prod()
    return float((compound_factor - 1) * 100)


def cumret_method_7(prices: pd.Series, window: int) -> float:
    """Method 7: Annualized return (probably not, but checking).
    
    Some platforms show annualized figures.
    """
    if len(prices) <= window:
        return float("nan")
    simple_return = (prices.iloc[-1] / prices.iloc[-window - 1]) - 1
    annualized = ((1 + simple_return) ** (252 / window)) - 1
    return float(annualized * 100)


def rsi_wilders(prices: pd.Series, window: int) -> float:
    """Our RSI implementation using Wilder's smoothing."""
    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    alpha = 1.0 / window
    avg_gain = gain.ewm(alpha=alpha, adjust=False).mean()
    avg_loss = loss.ewm(alpha=alpha, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0


def rsi_traditional(prices: pd.Series, window: int) -> float:
    """Traditional RSI using SMA instead of EWM."""
    delta = prices.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=window, min_periods=window).mean()
    avg_loss = loss.rolling(window=window, min_periods=window).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0


def fetch_prices(symbol: str, days: int = 120) -> pd.Series | None:
    """Fetch historical prices from Alpaca."""
    try:
        from alpaca.data.historical import StockHistoricalDataClient
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame
        from alpaca.data.enums import Adjustment
        
        # Use correct env var names with fallbacks
        api_key = (
            os.environ.get("ALPACA__KEY")
            or os.environ.get("ALPACA_KEY")
            or os.environ.get("APCA_API_KEY_ID")
        )
        api_secret = (
            os.environ.get("ALPACA__SECRET")
            or os.environ.get("ALPACA_SECRET")
            or os.environ.get("APCA_API_SECRET_KEY")
        )
        
        if not api_key or not api_secret:
            print(f"ERROR: Alpaca credentials not found. Set ALPACA__KEY and ALPACA__SECRET")
            print(f"  Found ALPACA__KEY: {bool(api_key)}")
            print(f"  Found ALPACA__SECRET: {bool(api_secret)}")
            return None
        
        client = StockHistoricalDataClient(api_key, api_secret)
        
        # Alpaca SIP data requires 15+ minute delay - query up to 20 minutes ago
        end = datetime.now(UTC) - timedelta(minutes=20)
        start = end - timedelta(days=days * 2)  # Extra buffer for weekends/holidays
        
        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Day,
            start=start,
            end=end,
            adjustment=Adjustment.ALL,  # Use adjusted prices like Composer
        )
        
        bars = client.get_stock_bars(request)
        
        if symbol not in bars.data:
            print(f"No data for {symbol}")
            return None
        
        closes = [float(bar.close) for bar in bars.data[symbol]]
        return pd.Series(closes[-days:])  # Return last N days
        
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None


def main() -> None:
    """Run diagnostic tests for cumulative return methods."""
    print("=" * 80)
    print("CUMULATIVE RETURN METHOD DIAGNOSTIC")
    print("=" * 80)
    print()
    
    # Symbols needed for the KMLM/BIL decision path
    symbols = {
        "QQQ": 15,   # cumulative-return("QQQ", 15)
        "LQD": 30,   # cumulative-return("LQD", 30)
        "IWM": 5,    # rsi("IWM", 5)
        "DIA": 10,   # rsi("DIA", 10)
    }
    
    prices_cache: dict[str, pd.Series] = {}
    
    print("Fetching market data...")
    for symbol in symbols:
        prices = fetch_prices(symbol, days=120)
        if prices is not None:
            prices_cache[symbol] = prices
            print(f"  {symbol}: {len(prices)} bars, latest close: ${prices.iloc[-1]:.2f}")
        else:
            print(f"  {symbol}: FAILED TO FETCH")
    
    print()
    
    if "QQQ" not in prices_cache or "LQD" not in prices_cache:
        print("ERROR: Cannot proceed without QQQ and LQD data")
        return
    
    # Test cumulative return methods
    print("=" * 80)
    print("CUMULATIVE RETURN METHODS")
    print("=" * 80)
    
    methods = [
        ("Method 1: shift(window)", cumret_method_1),
        ("Method 2: Log returns", cumret_method_2),
        ("Method 3: Sum pct_change", cumret_method_3),
        ("Method 4: shift(window-1)", cumret_method_4),
        ("Method 5: shift(window+1)", cumret_method_5),
        ("Method 6: Compound product", cumret_method_6),
        ("Method 7: Annualized", cumret_method_7),
    ]
    
    print()
    print("QQQ (window=15) vs LQD (window=30):")
    print("-" * 80)
    print(f"{'Method':<30} {'QQQ(15)':<12} {'LQD(30)':<12} {'QQQ > LQD?':<12} {'→ Path'}")
    print("-" * 80)
    
    qqq = prices_cache["QQQ"]
    lqd = prices_cache["LQD"]
    
    for name, method in methods:
        qqq_val = method(qqq, 15)
        lqd_val = method(lqd, 30)
        comparison = qqq_val > lqd_val
        path = "→ Continue" if comparison else "→ BIL"
        cmp_str = "TRUE" if comparison else "FALSE"
        print(f"{name:<30} {qqq_val:>10.4f}% {lqd_val:>10.4f}% {cmp_str:<12} {path}")
    
    print()
    
    # Test RSI for the second condition
    if "IWM" in prices_cache and "DIA" in prices_cache:
        print("=" * 80)
        print("RSI COMPARISON (if first condition passes)")
        print("=" * 80)
        print()
        
        iwm = prices_cache["IWM"]
        dia = prices_cache["DIA"]
        
        iwm_rsi_wilders = rsi_wilders(iwm, 5)
        dia_rsi_wilders = rsi_wilders(dia, 10)
        iwm_rsi_trad = rsi_traditional(iwm, 5)
        dia_rsi_trad = rsi_traditional(dia, 10)
        
        print(f"IWM RSI(5) vs DIA RSI(10):")
        print(f"  Wilder's method: IWM={iwm_rsi_wilders:.4f}, DIA={dia_rsi_wilders:.4f}")
        print(f"    IWM > DIA? {iwm_rsi_wilders > dia_rsi_wilders} → {'KMLM' if iwm_rsi_wilders > dia_rsi_wilders else 'BIL'}")
        print()
        print(f"  Traditional SMA: IWM={iwm_rsi_trad:.4f}, DIA={dia_rsi_trad:.4f}")
        print(f"    IWM > DIA? {iwm_rsi_trad > dia_rsi_trad} → {'KMLM' if iwm_rsi_trad > dia_rsi_trad else 'BIL'}")
    
    print()
    print("=" * 80)
    print("REFERENCE PRICE ANALYSIS")
    print("=" * 80)
    print()
    
    # Show what prices are being compared for each method
    for symbol, window in [("QQQ", 15), ("LQD", 30)]:
        if symbol in prices_cache:
            p = prices_cache[symbol]
            print(f"{symbol} (window={window}):")
            print(f"  Current price (today):           ${p.iloc[-1]:.2f}")
            print(f"  Price {window} days ago (shift):    ${p.iloc[-window-1]:.2f}")
            print(f"  Price {window-1} days ago (shift-1): ${p.iloc[-window]:.2f}")
            print(f"  Price {window+1} days ago (shift+1): ${p.iloc[-window-2]:.2f}")
            our_cumret = (p.iloc[-1] / p.iloc[-window-1] - 1) * 100
            print(f"  Our cumret: ({p.iloc[-1]:.2f} / {p.iloc[-window-1]:.2f} - 1) * 100 = {our_cumret:.4f}%")
            print()
    
    print()
    print("=" * 80)
    print("MOVING AVERAGE RETURN METHODS (LEVEL 1 is the divergence point!)")
    print("=" * 80)
    print()
    print("Testing: moving-average-return(HYG, 90) > moving-average-return(XLF, 60)")
    print()
    
    # Fetch HYG and XLF first
    if "HYG" not in prices_cache:
        hyg_prices = fetch_prices("HYG", days=120)
        if hyg_prices is not None:
            prices_cache["HYG"] = hyg_prices
    if "XLF" not in prices_cache:
        xlf_prices = fetch_prices("XLF", days=120)
        if xlf_prices is not None:
            prices_cache["XLF"] = xlf_prices
    
    def mar_method_1(prices: pd.Series, window: int) -> float:
        """Our current: mean of pct_change over window * 100."""
        if len(prices) <= window:
            return float("nan")
        returns = prices.pct_change()
        return float(returns.iloc[-window:].mean() * 100)
    
    def mar_method_2(prices: pd.Series, window: int) -> float:
        """Annualized: mean daily return * 252."""
        if len(prices) <= window:
            return float("nan")
        returns = prices.pct_change()
        daily_mean = returns.iloc[-window:].mean()
        return float(daily_mean * 252 * 100)
    
    def mar_method_3(prices: pd.Series, window: int) -> float:
        """Cumulative over window, then annualized."""
        if len(prices) <= window:
            return float("nan")
        total_return = (prices.iloc[-1] / prices.iloc[-window - 1]) - 1
        # Convert to daily equivalent
        daily_return = (1 + total_return) ** (1 / window) - 1
        return float(daily_return * 100)
    
    def mar_method_4(prices: pd.Series, window: int) -> float:
        """Rolling mean of log returns."""
        import numpy as np
        if len(prices) <= window:
            return float("nan")
        log_returns = np.log(prices / prices.shift(1))
        return float(log_returns.iloc[-window:].mean() * 100)
    
    def mar_method_5(prices: pd.Series, window: int) -> float:
        """SMA of price change (not percent change)."""
        if len(prices) <= window:
            return float("nan")
        price_changes = prices.diff()
        return float(price_changes.iloc[-window:].mean())
    
    def mar_method_6(prices: pd.Series, window: int) -> float:
        """Cumulative return / window (average return per period)."""
        if len(prices) <= window:
            return float("nan")
        total_return = (prices.iloc[-1] / prices.iloc[-window - 1]) - 1
        return float((total_return / window) * 100)
    
    mar_methods = [
        ("Method 1: mean(pct_change) * 100 (our impl)", mar_method_1),
        ("Method 2: Annualized (mean * 252)", mar_method_2),
        ("Method 3: Cumulative->daily equiv", mar_method_3),
        ("Method 4: mean(log returns) * 100", mar_method_4),
        ("Method 5: mean(price diff) - not %", mar_method_5),
        ("Method 6: cumret / window", mar_method_6),
    ]
    
    print(f"{'Method':<45} {'HYG(90)':<15} {'XLF(60)':<15} {'HYG > XLF?'}")
    print("-" * 90)
    
    for name, method in mar_methods:
        hyg_val = method(prices_cache["HYG"], 90)
        xlf_val = method(prices_cache["XLF"], 60)
        comparison = hyg_val > xlf_val
        cmp_str = "TRUE" if comparison else "FALSE"
        print(f"{name:<45} {hyg_val:>12.6f}% {xlf_val:>12.6f}% {cmp_str}")
    
    print()
    print("=" * 80)
    print("FULL DECISION TREE TRACE: 'Beam Filter: SOXX, KMLM, HYG 156/21'")
    print("=" * 80)
    print()
    
    # Fetch additional symbols needed for the full tree
    extra_symbols = ["HYG", "XLF", "LQD", "EFA"]
    for sym in extra_symbols:
        if sym not in prices_cache:
            p = fetch_prices(sym, days=120)
            if p is not None:
                prices_cache[sym] = p
                print(f"  Fetched {sym}: {len(p)} bars, latest: ${p.iloc[-1]:.2f}")
    
    print()
    
    # LEVEL 1: moving-average-return HYG 90 > moving-average-return XLF 60
    hyg = prices_cache.get("HYG")
    xlf = fetch_prices("XLF", days=120)
    if xlf is not None:
        prices_cache["XLF"] = xlf
    
    def mar(prices: pd.Series, window: int) -> float:
        """Moving average return."""
        if len(prices) <= window:
            return float("nan")
        returns = prices.pct_change()
        return float(returns.iloc[-window:].mean() * 100)
    
    hyg_mar_90 = mar(prices_cache["HYG"], 90) if "HYG" in prices_cache else float("nan")
    xlf_mar_60 = mar(prices_cache["XLF"], 60) if "XLF" in prices_cache else float("nan")
    
    print(f"LEVEL 1: moving-average-return(HYG, 90) > moving-average-return(XLF, 60)")
    print(f"  HYG MAR(90) = {hyg_mar_90:.6f}%")
    print(f"  XLF MAR(60) = {xlf_mar_60:.6f}%")
    level1_result = hyg_mar_90 > xlf_mar_60
    print(f"  {hyg_mar_90:.6f} > {xlf_mar_60:.6f} ? {level1_result}")
    branch = "TRUE branch" if level1_result else "FALSE branch"
    print(f"  → Taking {branch}")
    print()
    
    # LEVEL 2 (in TRUE branch): cumulative-return LQD 90 > cumulative-return EFA 75
    if level1_result:
        lqd_90 = cumret_method_1(prices_cache["LQD"], 90) if "LQD" in prices_cache else float("nan")
        efa = fetch_prices("EFA", days=120)
        if efa is not None:
            prices_cache["EFA"] = efa
        efa_75 = cumret_method_1(prices_cache["EFA"], 75) if "EFA" in prices_cache else float("nan")
        
        print(f"LEVEL 2: cumulative-return(LQD, 90) > cumulative-return(EFA, 75)")
        print(f"  LQD cumret(90) = {lqd_90:.4f}%")
        print(f"  EFA cumret(75) = {efa_75:.4f}%")
        level2_result = lqd_90 > efa_75
        print(f"  {lqd_90:.4f} > {efa_75:.4f} ? {level2_result}")
        
        if level2_result:
            print("  → SOXL selected!")
        else:
            print("  → Continue to Level 3...")
            print()
            
            # LEVEL 3: stdev-return LQD 20 > stdev-return HYG 30
            def stdev_return(prices: pd.Series, window: int) -> float:
                if len(prices) <= window:
                    return float("nan")
                returns = prices.pct_change()
                return float(returns.iloc[-window:].std() * 100)
            
            lqd_std_20 = stdev_return(prices_cache["LQD"], 20)
            hyg_std_30 = stdev_return(prices_cache["HYG"], 30)
            
            print(f"LEVEL 3: stdev-return(LQD, 20) > stdev-return(HYG, 30)")
            print(f"  LQD stdev(20) = {lqd_std_20:.6f}%")
            print(f"  HYG stdev(30) = {hyg_std_30:.6f}%")
            level3_result = lqd_std_20 > hyg_std_30
            print(f"  {lqd_std_20:.6f} > {hyg_std_30:.6f} ? {level3_result}")
            print()
            
            # LEVEL 4: cumulative-return HYG 90 > cumulative-return QQQ 15
            hyg_cumret_90 = cumret_method_1(prices_cache["HYG"], 90)
            qqq_cumret_15 = cumret_method_1(prices_cache["QQQ"], 15)
            
            print(f"LEVEL 4: cumulative-return(HYG, 90) > cumulative-return(QQQ, 15)")
            print(f"  HYG cumret(90) = {hyg_cumret_90:.4f}%")
            print(f"  QQQ cumret(15) = {qqq_cumret_15:.4f}%")
            level4_result = hyg_cumret_90 > qqq_cumret_15
            print(f"  {hyg_cumret_90:.4f} > {qqq_cumret_15:.4f} ? {level4_result}")
            
            if level4_result:
                print("  → HYG selected!")
            else:
                print("  → Continue to Level 5...")
                print()
                
                # LEVEL 5: cumulative-return QQQ 15 > cumulative-return LQD 30
                lqd_cumret_30 = cumret_method_1(prices_cache["LQD"], 30)
                
                print(f"LEVEL 5: cumulative-return(QQQ, 15) > cumulative-return(LQD, 30)")
                print(f"  QQQ cumret(15) = {qqq_cumret_15:.4f}%")
                print(f"  LQD cumret(30) = {lqd_cumret_30:.4f}%")
                level5_result = qqq_cumret_15 > lqd_cumret_30
                print(f"  {qqq_cumret_15:.4f} > {lqd_cumret_30:.4f} ? {level5_result}")
                
                if not level5_result:
                    print("  → BIL selected!")
                else:
                    print("  → Continue to Level 6...")
                    print()
                    
                    # LEVEL 6: rsi IWM 5 > rsi DIA 10
                    iwm_rsi = rsi_wilders(prices_cache["IWM"], 5)
                    dia_rsi = rsi_wilders(prices_cache["DIA"], 10)
                    
                    print(f"LEVEL 6: rsi(IWM, 5) > rsi(DIA, 10)")
                    print(f"  IWM rsi(5) = {iwm_rsi:.4f}")
                    print(f"  DIA rsi(10) = {dia_rsi:.4f}")
                    level6_result = iwm_rsi > dia_rsi
                    print(f"  {iwm_rsi:.4f} > {dia_rsi:.4f} ? {level6_result}")
                    
                    if level6_result:
                        print("  → KMLM selected!")
                    else:
                        print("  → BIL selected!")
    else:
        # FALSE branch at level 1 - different path
        print()
        
        def stdev_return(prices: pd.Series, window: int) -> float:
            if len(prices) <= window:
                return float("nan")
            returns = prices.pct_change()
            return float(returns.iloc[-window:].std() * 100)
        
        lqd_std_20 = stdev_return(prices_cache["LQD"], 20)
        hyg_std_30 = stdev_return(prices_cache["HYG"], 30)
        
        print(f"LEVEL 2 (FALSE path): stdev-return(LQD, 20) > stdev-return(HYG, 30)")
        print(f"  LQD stdev(20) = {lqd_std_20:.6f}%")
        print(f"  HYG stdev(30) = {hyg_std_30:.6f}%")
        level2_false_result = lqd_std_20 > hyg_std_30
        print(f"  {lqd_std_20:.6f} > {hyg_std_30:.6f} ? {level2_false_result}")
        print()
        
        if level2_false_result:
            # stdev LQD > stdev HYG: check cumret HYG 90 > cumret QQQ 15
            hyg_cumret_90 = cumret_method_1(prices_cache["HYG"], 90)
            qqq_cumret_15 = cumret_method_1(prices_cache["QQQ"], 15)
            
            print(f"LEVEL 3 (stdev TRUE): cumulative-return(HYG, 90) > cumulative-return(QQQ, 15)")
            print(f"  HYG cumret(90) = {hyg_cumret_90:.4f}%")
            print(f"  QQQ cumret(15) = {qqq_cumret_15:.4f}%")
            level3_result = hyg_cumret_90 > qqq_cumret_15
            print(f"  {hyg_cumret_90:.4f} > {qqq_cumret_15:.4f} ? {level3_result}")
            
            if level3_result:
                print("  → HYG selected!")
            else:
                print("  → Continue to Level 4...")
                print()
                
                # LEVEL 4: cumulative-return QQQ 15 > cumulative-return LQD 30
                lqd_cumret_30 = cumret_method_1(prices_cache["LQD"], 30)
                
                print(f"LEVEL 4: cumulative-return(QQQ, 15) > cumulative-return(LQD, 30)")
                print(f"  QQQ cumret(15) = {qqq_cumret_15:.4f}%")
                print(f"  LQD cumret(30) = {lqd_cumret_30:.4f}%")
                level4_result = qqq_cumret_15 > lqd_cumret_30
                print(f"  {qqq_cumret_15:.4f} > {lqd_cumret_30:.4f} ? {level4_result}")
                
                if not level4_result:
                    print("  → BIL selected!")
                else:
                    print("  → Continue to Level 5...")
                    print()
                    
                    # LEVEL 5: rsi IWM 5 > rsi DIA 10
                    iwm_rsi = rsi_wilders(prices_cache["IWM"], 5)
                    dia_rsi = rsi_wilders(prices_cache["DIA"], 10)
                    
                    print(f"LEVEL 5: rsi(IWM, 5) > rsi(DIA, 10)")
                    print(f"  IWM rsi(5) = {iwm_rsi:.4f}")
                    print(f"  DIA rsi(10) = {dia_rsi:.4f}")
                    level5_result = iwm_rsi > dia_rsi
                    print(f"  {iwm_rsi:.4f} > {dia_rsi:.4f} ? {level5_result}")
                    
                    if level5_result:
                        print("  → KMLM selected!")
                    else:
                        print("  → BIL selected!")
        else:
            # stdev LQD <= stdev HYG: different path
            qqq_cumret_15 = cumret_method_1(prices_cache["QQQ"], 15)
            lqd_cumret_30 = cumret_method_1(prices_cache["LQD"], 30)
            
            print(f"LEVEL 3 (stdev FALSE): cumulative-return(QQQ, 15) > cumulative-return(LQD, 30)")
            print(f"  QQQ cumret(15) = {qqq_cumret_15:.4f}%")
            print(f"  LQD cumret(30) = {lqd_cumret_30:.4f}%")
            level3_result = qqq_cumret_15 > lqd_cumret_30
            print(f"  {qqq_cumret_15:.4f} > {lqd_cumret_30:.4f} ? {level3_result}")
            
            if not level3_result:
                print("  → BIL selected!")
            else:
                print("  → Continue to Level 4...")
                print()
                
                iwm_rsi = rsi_wilders(prices_cache["IWM"], 5)
                dia_rsi = rsi_wilders(prices_cache["DIA"], 10)
                
                print(f"LEVEL 4: rsi(IWM, 5) > rsi(DIA, 10)")
                print(f"  IWM rsi(5) = {iwm_rsi:.4f}")
                print(f"  DIA rsi(10) = {dia_rsi:.4f}")
                level4_result = iwm_rsi > dia_rsi
                print(f"  {iwm_rsi:.4f} > {dia_rsi:.4f} ? {level4_result}")
                
                if level4_result:
                    print("  → KMLM selected!")
                else:
                    print("  → BIL selected!")


if __name__ == "__main__":
    main()
