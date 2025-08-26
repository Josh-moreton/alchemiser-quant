"""Pure evaluation logic for the Nuclear strategy (typed, framework-free).

This module exposes a small, pure function used by the typed Nuclear engine
to decide the recommended symbol, action, and reasoning from precomputed
indicators. It does not perform any IO or import infrastructure code.

Scope note:
- Mirrors key branches from the legacy orchestrator to avoid unexpected HOLDs.
- Adds a bull-market branch (SPY price > SPY 200MA) that recommends the
    NUCLEAR_PORTFOLIO when not otherwise overbought/oversold.
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

    Minimal logic aligned with existing unit tests, plus bull-market parity:
    - If SPY missing: HOLD with explicit reasoning
    - If SPY RSI(10) > 81: UVXY BUY (extreme overbought)
    - If 79 < SPY RSI(10) <= 81: UVXY_BTAL_PORTFOLIO BUY (defensive portfolio)
    - If SPY RSI(10) < 30: TQQQ BUY (oversold bounce)
    - If SPY price > SPY 200MA: NUCLEAR_PORTFOLIO BUY (bull-market rotation)
    - Else: SPY HOLD (neutral)
    """

    def _rsi(sym: str, window: int = 10) -> float | None:
        d = indicators.get(sym)
        if not d:
            return None
        key = f"rsi_{window}"
        try:
            return float(d.get(key)) if key in d else None
        except Exception:
            return None

    def _price(sym: str) -> float | None:
        d = indicators.get(sym)
        try:
            return float(d.get("current_price")) if d and "current_price" in d else None
        except Exception:
            return None

    def _ma(sym: str, window: int) -> float | None:
        d = indicators.get(sym)
        key = f"ma_{window}"
        try:
            return float(d.get(key)) if d and key in d else None
        except Exception:
            return None

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

    # Branch A: SPY overbought path
    if spy_rsi_10 > 79.0:
        if spy_rsi_10 > 81.0:
            return (
                "UVXY",
                "BUY",
                f"SPY extremely overbought: RSI(10) {spy_rsi_10:.1f} > 81 – volatility hedge recommended",
            )
        # Nested checks for other symbols > 81
        for sym in ["IOO", "TQQQ", "VTV", "XLF"]:
            r = _rsi(sym, 10)
            if r is not None and r > 81.0:
                return (
                    "UVXY",
                    "BUY",
                    f"{sym} extremely overbought: RSI(10) {r:.1f} > 81 – hedge with UVXY",
                )
        return (
            "UVXY_BTAL_PORTFOLIO",
            "BUY",
            f"SPY moderately overbought: RSI(10) {spy_rsi_10:.1f} in 79–81 band → UVXY 75% + BTAL 25%",
        )

    # Branch B: Other overbought leaders in order IOO, TQQQ, VTV, XLF
    for leader, cascade in [
        ("IOO", ["TQQQ", "VTV", "XLF"]),
        ("TQQQ", ["VTV", "XLF"]),
        ("VTV", ["XLF"]),
        ("XLF", []),
    ]:
        lr = _rsi(leader, 10)
        if lr is not None and lr > 79.0:
            if lr > 81.0:
                return (
                    "UVXY",
                    "BUY",
                    f"{leader} extremely overbought: RSI(10) {lr:.1f} > 81 – hedge with UVXY",
                )
            for sym in cascade:
                r = _rsi(sym, 10)
                if r is not None and r > 81.0:
                    return (
                        "UVXY",
                        "BUY",
                        f"{sym} extremely overbought: RSI(10) {r:.1f} > 81 – hedge with UVXY",
                    )
            return (
                "UVXY_BTAL_PORTFOLIO",
                "BUY",
                f"{leader} moderately overbought: RSI(10) {lr:.1f} in 79–81 band → UVXY 75% + BTAL 25%",
            )

    # Branch C: VOX overbought special-case
    vox_r = _rsi("VOX", 10)
    if vox_r is not None and vox_r > 79.0:
        xlf_r = _rsi("XLF", 10)
        if xlf_r is not None and xlf_r > 81.0:
            return (
                "UVXY",
                "BUY",
                f"VOX overbought context; XLF RSI(10) {xlf_r:.1f} > 81 – hedge with UVXY",
            )
        return (
            "UVXY_BTAL_PORTFOLIO",
            "BUY",
            f"VOX overbought: RSI(10) {vox_r:.1f} > 79 – UVXY 75% + BTAL 25%",
        )

    # Oversold checks (match legacy order): TQQQ first, then SPY -> UPRO
    tqqq = indicators.get("TQQQ")
    try:
        tqqq_rsi_10 = float(tqqq["rsi_10"]) if tqqq and "rsi_10" in tqqq else None
    except Exception:
        tqqq_rsi_10 = None

    if tqqq_rsi_10 is not None and tqqq_rsi_10 < 30.0:
        return (
            "TQQQ",
            "BUY",
            f"TQQQ oversold: RSI(10) {tqqq_rsi_10:.1f} < 30 – leveraged tech bounce setup",
        )

    if spy_rsi_10 < 30.0:
        return (
            "UPRO",
            "BUY",
            f"SPY oversold: RSI(10) {spy_rsi_10:.1f} < 30 – buy UPRO (3x SPY) for bounce",
        )

    # Bull vs Bear
    spy_price = _price("SPY")
    spy_ma_200 = _ma("SPY", 200)
    if spy_price is not None and spy_ma_200 is not None and spy_price > spy_ma_200:
        return (
            "NUCLEAR_PORTFOLIO",
            "BUY",
            (
                f"Bull market rotation – SPY ${spy_price:.2f} above 200MA ${spy_ma_200:.2f}. "
                "Shift to Nuclear portfolio leaders (e.g., SMR/BWXT/LEU) for upside exposure."
            ),
        )

    # Bear market: construct inverse-volatility portfolio across two selected assets
    return (
        "BEAR_PORTFOLIO",
        "BUY",
        (
            "Bear market defensive allocation – construct two-asset inverse-volatility basket "
            "based on PSQ/TQQQ/QQQ and bond RSIs (TLT/IEF) with 14-day vol weights"
        ),
    )
