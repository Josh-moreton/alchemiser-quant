#!/usr/bin/env python3
"""Test different max-drawdown calculation methods.

Business Unit: Scripts | Status: current.
"""
import pandas as pd


# NAIL prices (from our data)
nail_data = {
    "2025-12-19": 52.85,
    "2025-12-22": 52.25,
    "2025-12-23": 51.08,
    "2025-12-24": 52.47,
    "2025-12-26": 52.46,
    "2025-12-29": 51.67,
    "2025-12-30": 51.16,
    "2025-12-31": 49.62,
    "2026-01-02": 51.45,
    "2026-01-05": 52.67,
    "2026-01-06": 53.82,
    "2026-01-07": 49.94,
    "2026-01-08": 56.16,
    "2026-01-09": 66.56,
}

# TQQQ prices (from our data)
tqqq_data = {
    "2025-12-19": 53.44,
    "2025-12-22": 54.17,
    "2025-12-23": 54.93,
    "2025-12-24": 55.36,
    "2025-12-26": 55.31,
    "2025-12-29": 54.49,
    "2025-12-30": 54.10,
    "2025-12-31": 52.72,
    "2026-01-02": 52.35,
    "2026-01-05": 53.60,
    "2026-01-06": 55.01,
    "2026-01-07": 55.17,
    "2026-01-08": 54.19,
    "2026-01-09": 55.76,
}

nail_prices = pd.Series(nail_data)
tqqq_prices = pd.Series(tqqq_data)


def calc_max_dd(prices: pd.Series, window: int, method: str = "cummax") -> float:
    """Calculate max drawdown using different methods."""
    window_prices = prices.tail(window)

    if method == "cummax":
        # Our method: cummax within window
        cummax = window_prices.cummax()
        drawdown_pct = (window_prices / cummax - 1.0) * 100
        return float(-drawdown_pct.min())

    elif method == "global_peak":
        # Alternative: peak is max of entire window at start
        peak = window_prices.max()
        drawdown_pct = (window_prices / peak - 1.0) * 100
        return float(-drawdown_pct.min())

    elif method == "first_price":
        # Alternative: calculate from first price (not peak)
        first_price = window_prices.iloc[0]
        drawdown_pct = (window_prices / first_price - 1.0) * 100
        return float(-drawdown_pct.min())

    elif method == "prev_peak":
        # Alternative: peak includes one bar before window
        extended_prices = prices.tail(window + 1)
        peak = extended_prices.iloc[0]
        window_data = extended_prices.iloc[1:]
        peaks = []
        for price in window_data:
            if price > peak:
                peak = price
            peaks.append(peak)
        peaks_series = pd.Series(peaks, index=window_data.index)
        drawdown_pct = (window_data / peaks_series - 1.0) * 100
        return float(-drawdown_pct.min())

    return 0.0


if __name__ == "__main__":
    print("MAX-DRAWDOWN COMPARISON WITH DIFFERENT METHODS")
    print("=" * 70)
    print()

    for window in [10, 11, 12, 13, 14, 15]:
        print(f"Window = {window}:")
        for method in ["cummax", "global_peak", "first_price", "prev_peak"]:
            nail_mdd = calc_max_dd(nail_prices, window, method)
            tqqq_mdd = calc_max_dd(tqqq_prices, window, method)
            winner = "TQQQ" if tqqq_mdd < nail_mdd else "NAIL"
            marker = " <-- NAIL wins!" if winner == "NAIL" else ""
            print(f"  {method:15s}: TQQQ={tqqq_mdd:6.2f}% NAIL={nail_mdd:6.2f}% -> {winner}{marker}")
        print()
