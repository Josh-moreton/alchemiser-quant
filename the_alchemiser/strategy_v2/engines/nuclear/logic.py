"""Business Unit: strategy | Status: current.

Pure evaluation logic for the Nuclear strategy (typed, framework-free).

This module exposes a small, pure function used by the typed Nuclear engine
to decide the recommended symbol, action, and reasoning from precomputed
indicators. It does not perform any IO or import infrastructure code.

Scope note:
- Mirrors key branches from the legacy orchestrator to avoid unexpected HOLDs.
- Adds a bull-market branch (SPY price > SPY 200MA) that recommends the
    NUCLEAR_PORTFOLIO when not otherwise overbought/oversold.
"""

from __future__ import annotations

from the_alchemiser.shared.dto.technical_indicators_dto import TechnicalIndicatorDTO


def evaluate_nuclear_strategy(
    indicators: dict[str, TechnicalIndicatorDTO],
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
        dto = indicators.get(sym)
        if not dto:
            return None
        try:
            return dto.get_rsi_by_period(window)
        except Exception:
            return None

    def _price(sym: str) -> float | None:
        dto = indicators.get(sym)
        try:
            return float(dto.current_price) if dto and dto.current_price else None
        except Exception:
            return None

    def _ma(sym: str, window: int) -> float | None:
        dto = indicators.get(sym)
        if dto is None:
            return None
        try:
            return dto.get_ma_by_period(window)
        except Exception:
            return None

    def _check_extreme_overbought(symbols: list[str]) -> tuple[str, str, str] | None:
        """Check if any symbol is extremely overbought (RSI > 81)."""
        for sym in symbols:
            r = _rsi(sym, 10)
            if r is not None and r > 81.0:
                return (
                    "UVXY",
                    "BUY",
                    f"{sym} extremely overbought: RSI(10) {r:.1f} > 81 - hedge with UVXY",
                )
        return None

    def _evaluate_spy_overbought(spy_rsi: float) -> tuple[str, str, str]:
        """Evaluate SPY overbought conditions."""
        if spy_rsi > 81.0:
            return (
                "UVXY",
                "BUY",
                f"SPY extremely overbought: RSI(10) {spy_rsi:.1f} > 81 - volatility hedge recommended",
            )

        # Check other symbols for extreme overbought
        extreme_result = _check_extreme_overbought(["IOO", "TQQQ", "VTV", "XLF"])
        if extreme_result:
            return extreme_result

        return (
            "UVXY_BTAL_PORTFOLIO",
            "BUY",
            f"SPY moderately overbought: RSI(10) {spy_rsi:.1f} in 79-81 band → UVXY 75% + BTAL 25%",
        )

    def _evaluate_leader_cascade() -> tuple[str, str, str] | None:
        """Evaluate leader cascade for overbought conditions."""
        cascade_configs = [
            ("IOO", ["TQQQ", "VTV", "XLF"]),
            ("TQQQ", ["VTV", "XLF"]),
            ("VTV", ["XLF"]),
            ("XLF", []),
        ]

        for leader, cascade_symbols in cascade_configs:
            lr = _rsi(leader, 10)
            if lr is not None and lr > 79.0:
                if lr > 81.0:
                    return (
                        "UVXY",
                        "BUY",
                        f"{leader} extremely overbought: RSI(10) {lr:.1f} > 81 - hedge with UVXY",
                    )

                # Check cascade symbols for extreme overbought
                extreme_result = _check_extreme_overbought(cascade_symbols)
                if extreme_result:
                    return extreme_result

                return (
                    "UVXY_BTAL_PORTFOLIO",
                    "BUY",
                    f"{leader} moderately overbought: RSI(10) {lr:.1f} in 79-81 band → UVXY 75% + BTAL 25%",
                )
        return None

    def _evaluate_vox_special_case() -> tuple[str, str, str] | None:
        """Evaluate VOX special overbought case."""
        vox_r = _rsi("VOX", 10)
        if vox_r is not None and vox_r > 79.0:
            xlf_r = _rsi("XLF", 10)
            if xlf_r is not None and xlf_r > 81.0:
                return (
                    "UVXY",
                    "BUY",
                    f"VOX overbought context; XLF RSI(10) {xlf_r:.1f} > 81 - hedge with UVXY",
                )
            return (
                "UVXY_BTAL_PORTFOLIO",
                "BUY",
                f"VOX overbought: RSI(10) {vox_r:.1f} > 79 - UVXY 75% + BTAL 25%",
            )
        return None

    def _evaluate_oversold_conditions(spy_rsi: float) -> tuple[str, str, str] | None:
        """Evaluate oversold conditions for TQQQ and SPY."""
        # Check TQQQ oversold first
        tqqq_dto = indicators.get("TQQQ")
        try:
            tqqq_rsi_10 = tqqq_dto.rsi_10 if tqqq_dto else None
        except Exception:
            tqqq_rsi_10 = None

        if tqqq_rsi_10 is not None and tqqq_rsi_10 < 30.0:
            return (
                "TQQQ",
                "BUY",
                f"TQQQ oversold: RSI(10) {tqqq_rsi_10:.1f} < 30 - leveraged tech bounce setup",
            )

        # Check SPY oversold
        if spy_rsi < 30.0:
            return (
                "UPRO",
                "BUY",
                f"SPY oversold: RSI(10) {spy_rsi:.1f} < 30 - buy UPRO (3x SPY) for bounce",
            )
        return None

    def _evaluate_bull_bear_conditions() -> tuple[str, str, str]:
        """Evaluate bull vs bear market conditions."""
        spy_price = _price("SPY")
        spy_ma_200 = _ma("SPY", 200)

        if spy_price is not None and spy_ma_200 is not None and spy_price > spy_ma_200:
            return (
                "NUCLEAR_PORTFOLIO",
                "BUY",
                (
                    f"Bull market rotation - SPY ${spy_price:.2f} above 200MA ${spy_ma_200:.2f}. "
                    "Shift to Nuclear portfolio leaders (e.g., SMR/BWXT/LEU) for upside exposure."
                ),
            )

        # Default to bear market portfolio
        return (
            "BEAR_PORTFOLIO",
            "BUY",
            (
                "Bear market defensive allocation - construct two-asset inverse-volatility basket "
                "based on PSQ/TQQQ/QQQ and bond RSIs (TLT/IEF) with 14-day vol weights"
            ),
        )

    # Main evaluation logic
    spy_dto = indicators.get("SPY")
    if not spy_dto or spy_dto.rsi_10 is None:
        return (
            "SPY",
            "HOLD",
            "Missing SPY data for RSI(10) - missing SPY data prevents evaluation",
        )

    try:
        spy_rsi_10 = spy_dto.rsi_10
    except Exception:
        return (
            "SPY",
            "HOLD",
            "Invalid SPY RSI(10) - missing spy data prevents evaluation",
        )

    # Evaluate conditions in order of priority
    # 1. SPY overbought conditions
    if spy_rsi_10 > 79.0:
        return _evaluate_spy_overbought(spy_rsi_10)

    # 2. Other leader cascade conditions
    leader_result = _evaluate_leader_cascade()
    if leader_result:
        return leader_result

    # 3. VOX special case
    vox_result = _evaluate_vox_special_case()
    if vox_result:
        return vox_result

    # 4. Oversold conditions
    oversold_result = _evaluate_oversold_conditions(spy_rsi_10)
    if oversold_result:
        return oversold_result

    # 5. Bull vs Bear market conditions
    return _evaluate_bull_bear_conditions()
