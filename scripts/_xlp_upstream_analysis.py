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


def main() -> None:
    # Load XLP data
    df = pd.read_parquet("/tmp/xlp_data.parquet")
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp").reset_index(drop=True)
    mask = df["timestamp"] <= "2026-02-07"
    data = df[mask].copy()
    closes = data["close"].values

    print("=" * 70)
    print("XLP RSI(10) Analysis - Key upstream condition for UVIX routing")
    print("=" * 70)
    print()

    rsi_val = rsi_wilder(closes, 10)
    distance_85 = rsi_val - 85.0
    print(f"XLP RSI(10) on Feb 6:  {rsi_val:.4f}")
    print(f"Distance from 85:      {distance_85:+.4f}")
    print(f"XLP > 85 evaluates to: {'TRUE -> direct UVIX' if rsi_val > 85 else 'FALSE -> check UVXY RSI'}")
    print()

    # Show how close XLP RSI is to 85
    print("SENSITIVITY: What if XLP closes differed slightly?")
    actual_close = closes[-1]
    for delta in [0, 0.5, 1.0, 1.5, 2.0, 3.0]:
        test = closes.copy()
        test[-1] = actual_close + delta
        rsi_val = rsi_wilder(test, 10)
        marker = "<-- ABOVE 85 (UVIX)" if rsi_val > 85 else ""
        print(f"  Close={test[-1]:.2f} (+{delta:.1f}):  RSI(10)={rsi_val:.4f}  {marker}")
    print()

    # Also check XLP RSI(10) > 77 (decides whether this code path is reached)
    rsi77 = rsi_wilder(closes, 10)
    print(f"XLP RSI(10) > 77:      {'TRUE (enters Scale-In group)' if rsi77 > 77 else 'FALSE'}")
    print()

    # Show last 15 XLP closes
    recent = data.tail(15)
    print("XLP close prices (last 15 bars):")
    for _, r in recent.iterrows():
        ts = r["timestamp"]
        ts_str = ts.strftime("%Y-%m-%d") if hasattr(ts, "strftime") else str(ts)
        print(f"  {ts_str}  close={r['close']:>8.2f}")

    # Now check SVXY max-drawdown (the OTHER UVIX path)
    print()
    print("=" * 70)
    print("SVXY max-drawdown(5) Analysis - Alternative UVIX routing")
    print("=" * 70)
    df2 = pd.read_parquet("/tmp/svxy_data.parquet")
    df2["timestamp"] = pd.to_datetime(df2["timestamp"])
    df2 = df2.sort_values("timestamp").reset_index(drop=True)
    mask2 = df2["timestamp"] <= "2026-02-07"
    data2 = df2[mask2].copy()
    if len(data2) >= 6:
        last5_closes = data2.tail(6)["close"].values
        peak = last5_closes[:-1].max()
        current = last5_closes[-1]
        drawdown = ((peak - current) / peak) * 100
        print(f"SVXY last 6 closes: {last5_closes}")
        print(f"Peak (5-day window): {peak:.2f}")
        print(f"Current:             {current:.2f}")
        print(f"Max drawdown(5):     {drawdown:.2f}%")
        print(f"Threshold:           15%")
        print(f"Result:              {'> 15 -> UVIX path' if drawdown > 15 else '<= 15 -> UVXY path'}")

    # What about FAS, IOO, SPY, QQQ RSI? Are any near their thresholds?
    print()
    print("=" * 70)
    print("All upstream conditions (any near their threshold?)")
    print("=" * 70)
    for symbol, threshold, op in [
        ("FAS", 79.5, ">"),
        ("IOO", 80.0, ">"),
        ("SPY", 80.0, ">"),
        ("QQQ", 79.0, ">"),
        ("XLP", 77.0, ">"),
        ("XLP", 85.0, ">"),
    ]:
        try:
            path = f"/tmp/{symbol.lower()}_data.parquet"
            dfs = pd.read_parquet(path)
            dfs["timestamp"] = pd.to_datetime(dfs["timestamp"])
            dfs = dfs.sort_values("timestamp").reset_index(drop=True)
            ms = dfs["timestamp"] <= "2026-02-07"
            cs = dfs[ms]["close"].values
            rsi_val = rsi_wilder(cs, 10)
            distance = rsi_val - threshold
            result = rsi_val > threshold if op == ">" else rsi_val < threshold
            marker = "***NEAR***" if abs(distance) < 3 else ""
            print(f"  {symbol} RSI(10) {op} {threshold}: actual={rsi_val:.2f}, dist={distance:+.2f} -> {result}  {marker}")
        except FileNotFoundError:
            print(f"  {symbol}: data not available locally, skipping")


if __name__ == "__main__":
    main()
