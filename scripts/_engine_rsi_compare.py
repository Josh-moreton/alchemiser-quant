"""Business Unit: scripts | Status: current."""

from __future__ import annotations

import numpy as np
import pandas as pd


def rsi_engine_style(data: pd.Series, window: int) -> pd.Series:
    """Replicate the exact RSI calculation from indicators.py."""
    delta = data.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    alpha = 1.0 / window
    avg_gain = gain.ewm(alpha=alpha, adjust=False).mean()
    avg_loss = loss.ewm(alpha=alpha, adjust=False).mean()
    rs = avg_gain.divide(avg_loss, fill_value=0.0)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50.0)


def rsi_manual(prices: np.ndarray, window: int) -> float:
    """Manual Wilder RSI (from analysis scripts)."""
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


def main() -> None:
    # ---- XLP ----
    df = pd.read_parquet("/tmp/xlp_data.parquet")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    mask = df["timestamp"] <= "2026-02-07"
    data = df[mask].copy()

    closes_series = data["close"]
    closes_array = data["close"].values

    print("=" * 70)
    print("XLP RSI(10) - Engine vs Manual comparison")
    print("=" * 70)

    # Engine-style (pandas ewm)
    rsi_series = rsi_engine_style(closes_series, 10)
    engine_val = float(rsi_series.iloc[-1])

    # Manual-style (numpy loop)
    manual_val = rsi_manual(closes_array, 10)

    print(f"Total bars:     {len(closes_array)}")
    print(f"Last close:     {closes_array[-1]:.2f} ({data['timestamp'].iloc[-1]})")
    print()
    print(f"Engine RSI(10): {engine_val:.6f}")
    print(f"Manual RSI(10): {manual_val:.6f}")
    print(f"Difference:     {abs(engine_val - manual_val):.10f}")
    print()
    print(f"Threshold:      85.0")
    print(f"Engine > 85:    {engine_val > 85}")
    print(f"Manual > 85:    {manual_val > 85}")

    # Check last 5 RSI values to see trend
    print()
    print("Last 5 RSI(10) values (engine):")
    for i in range(-5, 0):
        ts = data["timestamp"].iloc[i]
        ts_str = ts.strftime("%Y-%m-%d") if hasattr(ts, "strftime") else str(ts)
        print(f"  {ts_str}: RSI={float(rsi_series.iloc[i]):.4f}  close={closes_array[i]:.2f}")

    # ---- UVXY ----
    print()
    print("=" * 70)
    print("UVXY RSI(10) - Engine vs Manual comparison")
    print("=" * 70)

    df2 = pd.read_parquet("/tmp/uvxy_data.parquet")
    df2["timestamp"] = pd.to_datetime(df2["timestamp"])
    df2 = df2.sort_values("timestamp").reset_index(drop=True)
    mask2 = df2["timestamp"] <= "2026-02-07"
    data2 = df2[mask2].copy()

    closes_series2 = data2["close"]
    closes_array2 = data2["close"].values

    rsi_series2 = rsi_engine_style(closes_series2, 10)
    engine_val2 = float(rsi_series2.iloc[-1])
    manual_val2 = rsi_manual(closes_array2, 10)

    print(f"Total bars:     {len(closes_array2)}")
    print(f"Last close:     {closes_array2[-1]:.2f}")
    print()
    print(f"Engine RSI(10): {engine_val2:.6f}")
    print(f"Manual RSI(10): {manual_val2:.6f}")
    print(f"Threshold:      40.0")
    print(f"Engine < 40:    {engine_val2 < 40}")
    print(f"Manual < 40:    {manual_val2 < 40}")

    # ---- UVXY RSI(21) ----
    print()
    print("=" * 70)
    print("UVXY RSI(21) - First gate check")
    print("=" * 70)
    rsi21_series = rsi_engine_style(closes_series2, 21)
    engine_val21 = float(rsi21_series.iloc[-1])
    print(f"Engine RSI(21): {engine_val21:.6f}")
    print(f"Threshold:      65.0")
    print(f"Engine > 65:    {engine_val21 > 65}")


if __name__ == "__main__":
    main()
