"""Business Unit: scripts | Status: current."""

from __future__ import annotations

import pandas as pd
import numpy as np


def rsi_wilder(prices: np.ndarray, window: int) -> float:
    """Calculate Wilder's RSI using EWM smoothing."""
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)
    alpha = 1.0 / window
    avg_gain = float(gains[0])
    avg_loss = float(losses[0])
    for i in range(1, len(gains)):
        avg_gain = alpha * float(gains[i]) + (1 - alpha) * avg_gain
        avg_loss = alpha * float(losses[i]) + (1 - alpha) * avg_loss
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - 100.0 / (1.0 + rs)


def rsi_sma_seeded(prices: np.ndarray, window: int) -> float:
    """Calculate Wilder's RSI seeded with SMA of first N periods."""
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)
    if len(gains) < window:
        return 50.0
    avg_gain = float(np.mean(gains[:window]))
    avg_loss = float(np.mean(losses[:window]))
    for i in range(window, len(gains)):
        avg_gain = (avg_gain * (window - 1) + float(gains[i])) / window
        avg_loss = (avg_loss * (window - 1) + float(losses[i])) / window
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100.0 - 100.0 / (1.0 + rs)


def rsi_sma_only(prices: np.ndarray, window: int) -> float:
    """Calculate RSI using only SMA over last N periods (no smoothing)."""
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)
    recent_gains = gains[-window:]
    recent_losses = losses[-window:]
    avg_g = float(np.mean(recent_gains))
    avg_l = float(np.mean(recent_losses))
    if avg_l == 0:
        return 100.0
    rs = avg_g / avg_l
    return 100.0 - 100.0 / (1.0 + rs)


def main() -> None:
    df = pd.read_parquet("/tmp/uvxy_data.parquet")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)

    mask = df["timestamp"] <= "2026-02-07"
    data = df[mask].copy()
    closes = data["close"].values
    total_bars = len(closes)
    window = 10

    print(f"Total UVXY bars up to Feb 6: {total_bars}")
    print(f"RSI window: {window}")
    print(f"Threshold: 40 (below = UVIX, above = UVXY)")
    print()

    print("=" * 70)
    print("WILDER RSI (EWM alpha=1/n) with different lookback lengths:")
    print("=" * 70)
    lookbacks = [15, 20, 30, 50, 100, 200, 500, 1000, total_bars]
    for lb in lookbacks:
        if lb > total_bars:
            lb = total_bars
        prices_slice = closes[-lb:]
        rsi_val = rsi_wilder(prices_slice, window)
        marker = "<-- BELOW 40 (UVIX)" if rsi_val < 40 else ""
        print(f"  Lookback={lb:>5} bars:  RSI(10)={rsi_val:>7.2f}  {marker}")

    print()
    print("=" * 70)
    print("SMA-SEEDED WILDER RSI with different lookback lengths:")
    print("=" * 70)
    for lb in lookbacks:
        if lb > total_bars:
            lb = total_bars
        prices_slice = closes[-lb:]
        rsi_val = rsi_sma_seeded(prices_slice, window)
        marker = "<-- BELOW 40 (UVIX)" if rsi_val < 40 else ""
        print(f"  Lookback={lb:>5} bars:  RSI(10)={rsi_val:>7.2f}  {marker}")

    print()
    print("=" * 70)
    print("PURE SMA RSI (no smoothing, just last N bars average):")
    print("=" * 70)
    for lb in [10, 14, 20, 30]:
        if lb + 1 > total_bars:
            continue
        prices_slice = closes[-(lb + 1) :]
        rsi_val = rsi_sma_only(prices_slice, lb)
        marker = "<-- BELOW 40 (UVIX)" if rsi_val < 40 else ""
        print(f"  SMA bars={lb:>3}:  RSI={rsi_val:>7.2f}  {marker}")

    print()
    print("=" * 70)
    print("UVXY close prices (last 15 bars):")
    print("=" * 70)
    recent = data.tail(15)
    for _, r in recent.iterrows():
        ts = r["timestamp"]
        ts_str = ts.strftime("%Y-%m-%d") if hasattr(ts, "strftime") else str(ts)
        print(f"  {ts_str}  close={r['close']:>10.2f}")

    # Compute what the close prices would need to be for RSI < 40
    print()
    print("=" * 70)
    print("SENSITIVITY: How much would Feb 6 close need to drop for RSI < 40?")
    print("=" * 70)
    for test_close in [37.30, 35.0, 33.0, 31.0, 29.0, 27.0, 25.0]:
        test_prices = closes.copy()
        test_prices[-1] = test_close
        rsi_val = rsi_wilder(test_prices, window)
        marker = "<-- BELOW 40" if rsi_val < 40 else ""
        print(f"  Close={test_close:>7.2f}:  RSI(10)={rsi_val:>7.2f}  {marker}")


if __name__ == "__main__":
    main()
