"""
Pure evaluation logic for the Nuclear strategy (typed, framework-free).

This module exposes a small, pure function used by the typed Nuclear engine
to decide the recommended symbol, action, and reasoning from precomputed
indicators. It does not perform any IO or import infrastructure code.
"""

from __future__ import annotations

from typing import Any


def evaluate_nuclear_strategy(
    indicators: dict[str, Any], market_data: dict[str, Any] | None = None
) -> tuple[str, str, str]:
    """Evaluate the Nuclear strategy from indicators only.

    Contract:
    - Returns (symbol, action, reasoning)
    - Must be deterministic and side-effect free

    Minimal logic aligned with existing unit tests:
    - If SPY missing: HOLD with explicit reasoning
    - If SPY RSI(10) > 81: UVXY BUY (extreme overbought)
    - If 79 < SPY RSI(10) <= 81: UVXY_BTAL_PORTFOLIO BUY (defensive portfolio)
    - If SPY RSI(10) < 30: TQQQ BUY (oversold bounce)
    - Else: SPY HOLD (neutral)
    """

    spy = indicators.get("SPY")
    if not spy or "rsi_10" not in spy:
        return (
            "SPY",
            "HOLD",
            "Missing SPY data for RSI(10) – missing SPY data prevents evaluation",
        )

    try:
        spy_rsi_10 = float(spy["rsi_10"])
    except Exception:
        return (
            "SPY",
            "HOLD",
            "Invalid SPY RSI(10) – missing spy data prevents evaluation",
        )

    # Extreme overbought
    if spy_rsi_10 > 81.0:
        return (
            "UVXY",
            "BUY",
            "SPY extremely overbought (RSI > 81) – volatility hedge recommended",
        )

    # Moderate overbought – defensive portfolio
    if spy_rsi_10 > 79.0:
        return (
            "UVXY_BTAL_PORTFOLIO",
            "BUY",
            "SPY overbought (79-81), UVXY 75% + BTAL 25% allocation",
        )

    # Oversold bounce
    if spy_rsi_10 < 30.0:
        return (
            "TQQQ",
            "BUY",
            "SPY oversold (RSI < 30) – mean-reversion bounce opportunity",
        )

    # Neutral
    return ("SPY", "HOLD", "Neutral market conditions – no strong signal")
