"""Debug script: Compute UVXY RSI(10) for Feb 6 mismatch analysis."""
from __future__ import annotations

import pandas as pd
import numpy as np


def compute_rsi_ewm(close: pd.Series, window: int = 10) -> pd.Series:
    """RSI via pandas EWM (our engine method)."""
    delta = close.diff()
    gains = delta.clip(lower=0)
    losses = (-delta).clip(lower=0)
    alpha = 1.0 / window
    avg_gain = gains.ewm(alpha=alpha, adjust=False).mean()
    avg_loss = losses.ewm(alpha=alpha, adjust=False).mean()
    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi.fillna(50.0)


def compute_rsi_sma_seeded(close: pd.Series, window: int = 10) -> pd.Series:
    """RSI via SMA-seeded Wilder smoothing (textbook / Composer method)."""
    delta = close.diff()
    gains = delta.clip(lower=0)
    losses = (-delta).clip(lower=0)

    avg_gain_sma = gains.rolling(window=window, min_periods=window).mean()
    avg_loss_sma = losses.rolling(window=window, min_periods=window).mean()

    ag = pd.Series(np.nan, index=close.index, dtype=float)
    al = pd.Series(np.nan, index=close.index, dtype=float)

    first_valid = avg_gain_sma.first_valid_index()
    if first_valid is None:
        return pd.Series(50.0, index=close.index)

    ag.iloc[first_valid] = avg_gain_sma.iloc[first_valid]
    al.iloc[first_valid] = avg_loss_sma.iloc[first_valid]

    for i in range(first_valid + 1, len(close)):
        ag.iloc[i] = (ag.iloc[i - 1] * (window - 1) + gains.iloc[i]) / window
        al.iloc[i] = (al.iloc[i - 1] * (window - 1) + losses.iloc[i]) / window

    rs = ag / al
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi.fillna(50.0)


def main() -> None:
    df = pd.read_parquet("/tmp/uvxy_daily.parquet")
    close = df["close"].astype(float)
    print(f"UVXY: {len(df)} bars, {df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}")

    rsi_ewm = compute_rsi_ewm(close, 10)
    rsi_sma = compute_rsi_sma_seeded(close, 10)

    feb6_mask = df["timestamp"].dt.strftime("%Y-%m-%d") == "2026-02-06"
    feb6_idx = df.index[feb6_mask]
    if len(feb6_idx) == 0:
        print("Feb 6 not found")
        return

    idx = feb6_idx[0]

    print("\n=== UVXY price + RSI(10) context ===")
    print(f"{'Date':>12}  {'Close':>8}  {'Chg':>7}  {'RSI-EWM':>10}  {'RSI-SMA':>10}  {'from40-EWM':>12}  {'from40-SMA':>12}")
    delta = close.diff()
    for i in range(max(0, idx - 7), min(len(df), idx + 1)):
        d = df["timestamp"].iloc[i].strftime("%Y-%m-%d")
        c = close.iloc[i]
        ch = delta.iloc[i] if not np.isnan(delta.iloc[i]) else 0
        r1 = rsi_ewm.iloc[i]
        r2 = rsi_sma.iloc[i]
        m = " <-- MISMATCH" if i == idx else ""
        print(f"{d:>12}  {c:>8.2f}  {ch:>+7.2f}  {r1:>10.4f}  {r2:>10.4f}  {r1-40:>+12.4f}  {r2-40:>+12.4f}{m}")

    print(f"\n=== Summary for Feb 6 ===")
    print(f"  EWM RSI(10):        {rsi_ewm.iloc[idx]:.8f}  -> {'< 40 -> UVIX' if rsi_ewm.iloc[idx] < 40 else '>= 40 -> UVXY'}")
    print(f"  SMA-seeded RSI(10): {rsi_sma.iloc[idx]:.8f}  -> {'< 40 -> UVIX' if rsi_sma.iloc[idx] < 40 else '>= 40 -> UVXY'}")
    print(f"  Composer expects:   < 40 -> UVIX")
    print(f"  Discrepancy:        {abs(rsi_ewm.iloc[idx] - rsi_sma.iloc[idx]):.8f}")

    if rsi_ewm.iloc[idx] >= 40 and rsi_sma.iloc[idx] < 40:
        print("\n  ** SMA-seeded method matches Composer! The RSI seeding method is the root cause. **")
    elif rsi_ewm.iloc[idx] >= 40 and rsi_sma.iloc[idx] >= 40:
        print("\n  ** Both methods agree (>= 40). Divergence likely from data differences, not RSI method. **")


if __name__ == "__main__":
    main()
