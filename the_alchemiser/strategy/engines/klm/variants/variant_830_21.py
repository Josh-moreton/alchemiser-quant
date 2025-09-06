"""Business Unit: utilities; Status: current.

KLM Strategy Variant 830/21 - "MonkeyBusiness Simons variant V2".

This variant is similar to other standard variants except:
1. KMLM Switcher uses select-TOP 1 from TECL/SOXL/SVIX (opposite of others)
2. L/S Rotator has "Bond Check" logic using BND moving-average-return
3. Different symbols in the Bond Check paths

This is the V2 (enhanced) version of the MonkeyBusiness Simons approach.
"""

from __future__ import annotations

import pandas as pd

from the_alchemiser.shared.utils.common import ActionType

from ..base_variant import BaseKLMVariant


class KlmVariant83021(BaseKLMVariant):
    """Variant 830/21 - MonkeyBusiness Simons variant V2.

    Key differences:
    - KMLM Switcher: select-TOP 1 from TECL/SOXL/SVIX (highest RSI)
    - Bond Check: BND MA(20) determines KMLM/SPLV vs TLT/LABD/TZA selection
    """

    def __init__(self) -> None:
        super().__init__(
            name="830/21", description="MonkeyBusiness Simons variant V2 - Enhanced with Bond Check"
        )

    def evaluate(
        self,
        indicators: dict[str, dict[str, float]],
        market_data: dict[str, pd.DataFrame] | None = None,
    ) -> tuple[str | dict[str, float], str, str]:
        """Evaluate 830/21 - same as other variants except KMLM Switcher and Bond Check."""
        # Step 1: Primary overbought checks → UVXY
        symbol, reason = self.check_primary_overbought_conditions(indicators)
        if symbol:
            self.log_decision(symbol, ActionType.BUY.value, reason)
            return symbol, ActionType.BUY.value, reason

        # Step 2: Single Popped KMLM logic (same as others)
        return self._evaluate_single_popped_kmlm(indicators)

    def _evaluate_single_popped_kmlm(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[str | dict[str, float], str, str]:
        """Single Popped KMLM logic - identical to other variants."""
        # Check UVXY RSI(21) for strategy branching
        if "UVXY" in indicators:
            uvxy_rsi_21 = indicators["UVXY"]["rsi_21"]

            if uvxy_rsi_21 > 65:
                # UVXY elevated - use BSC strategy
                return self._evaluate_bsc_strategy(indicators)
            # UVXY normal - use Combined Pop Bot
            return self._evaluate_combined_pop_bot(indicators)

        # Fallback if UVXY data unavailable
        return self._evaluate_combined_pop_bot(indicators)

    def _evaluate_bsc_strategy(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[str, str, str]:
        """BSC strategy - identical to other variants."""
        if "SPY" in indicators:
            spy_rsi_21 = indicators["SPY"]["rsi_21"]

            if spy_rsi_21 > 30:
                result = ("VIXM", ActionType.BUY.value, "830/21 BSC: SPY RSI(21) > 30 → VIXM")
            else:
                result = (
                    "SPXL",
                    ActionType.BUY.value,
                    "830/21 BSC: SPY oversold (RSI(21) <= 30) → SPXL",
                )
        else:
            result = ("VIXM", ActionType.BUY.value, "830/21 BSC: Default VIX position")

        self.log_decision(result[0], result[1], result[2])
        return result

    def _evaluate_combined_pop_bot(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[str | dict[str, float], str, str]:
        """Combined Pop Bot - identical to others (NO LABU)."""
        # Priority 1: TQQQ oversold
        if "TQQQ" in indicators and indicators["TQQQ"]["rsi_10"] < 30:
            result = ("TECL", ActionType.BUY.value, "830/21 Pop Bot: TQQQ RSI < 30 → TECL")
            self.log_decision(result[0], result[1], result[2])
            return result

        # Priority 2: SOXL oversold
        if "SOXL" in indicators and indicators["SOXL"]["rsi_10"] < 30:
            result = ("SOXL", ActionType.BUY.value, "830/21 Pop Bot: SOXL RSI < 30 → SOXL")
            self.log_decision(result[0], result[1], result[2])
            return result

        # Priority 3: SPXL oversold
        if "SPXL" in indicators and indicators["SPXL"]["rsi_10"] < 30:
            result = ("SPXL", ActionType.BUY.value, "830/21 Pop Bot: SPXL RSI < 30 → SPXL")
            self.log_decision(result[0], result[1], result[2])
            return result

        # No oversold conditions - proceed to KMLM Switcher
        return self.evaluate_core_kmlm_switcher(indicators)

    def evaluate_core_kmlm_switcher(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[str | dict[str, float], str, str]:
        """Core KMLM switcher for variant 830/21."""
        return self._evaluate_kmlm_switcher_830(indicators)

    def _evaluate_kmlm_switcher_830(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[str | dict[str, float], str, str]:
        """830/21 KMLM Switcher - KEY DIFFERENCE: select-TOP 1 (highest RSI).

        CLJ shows: select-top 1 from TECL/SOXL/SVIX (opposite of other variants)
        """
        if "XLK" in indicators and "KMLM" in indicators:
            xlk_rsi = indicators["XLK"]["rsi_10"]
            kmlm_rsi = indicators["KMLM"]["rsi_10"]

            if xlk_rsi > kmlm_rsi:
                # select-TOP 1 from TECL, SOXL, SVIX (highest RSI)
                candidates = []
                for symbol in ["TECL", "SOXL", "SVIX"]:
                    if symbol in indicators:
                        rsi = indicators[symbol]["rsi_10"]
                        candidates.append((symbol, rsi))

                if candidates:
                    # Select TOP 1 (highest RSI) - opposite of other variants
                    candidates.sort(key=lambda x: x[1], reverse=True)
                    selected = candidates[0]
                    result = (
                        selected[0],
                        ActionType.BUY.value,
                        f"830/21 KMLM Switcher: XLK > KMLM → {selected[0]} (highest RSI: {selected[1]:.1f})",
                    )
                else:
                    result = ("TECL", ActionType.BUY.value, "830/21 KMLM Switcher: TECL fallback")

                self.log_decision(result[0], result[1], result[2])
                return result

        # XLK <= KMLM → Bond Check
        return self._evaluate_bond_check(indicators)

    def _evaluate_bond_check(self, indicators: dict[str, dict[str, float]]) -> tuple[str, str, str]:
        """830/21 Bond Check - UNIQUE: BND moving-average-return determines path.

        CLJ logic:
        - If BND MA(20) > 0: select-bottom 1 from KMLM/SPLV
        - Else: select-top 1 from TLT/LABD/TZA
        """
        # Check BND moving-average-return(20)
        bnd_ma_return = indicators.get("BND", {}).get("moving_average_return_20", 0)

        if bnd_ma_return > 0:
            # Positive bond momentum: select-bottom 1 from KMLM/SPLV
            candidates = []
            for symbol in ["KMLM", "SPLV"]:
                if symbol in indicators:
                    rsi = indicators[symbol]["rsi_10"]
                    candidates.append((symbol, rsi))

            if candidates:
                # Select bottom 1 (lowest RSI)
                candidates.sort(key=lambda x: x[1])
                selected = candidates[0]
                result = (
                    selected[0],
                    ActionType.BUY.value,
                    f"830/21 Bond Check: BND MA(20) {bnd_ma_return:.2f}% > 0 → {selected[0]} (lowest RSI)",
                )
            else:
                result = (
                    "KMLM",
                    ActionType.BUY.value,
                    "830/21 Bond Check: KMLM fallback (positive bonds)",
                )
        else:
            # Negative/zero bond momentum: select-top 1 from TLT/LABD/TZA
            candidates = []
            for symbol in ["TLT", "LABD", "TZA"]:
                if symbol in indicators:
                    rsi = indicators[symbol]["rsi_10"]
                    candidates.append((symbol, rsi))

            if candidates:
                # Select top 1 (highest RSI)
                candidates.sort(key=lambda x: x[1], reverse=True)
                selected = candidates[0]
                result = (
                    selected[0],
                    ActionType.BUY.value,
                    f"830/21 Bond Check: BND MA(20) {bnd_ma_return:.2f}% ≤ 0 → {selected[0]} (highest RSI)",
                )
            else:
                result = (
                    "TLT",
                    ActionType.BUY.value,
                    "830/21 Bond Check: TLT fallback (negative bonds)",
                )

        self.log_decision(result[0], result[1], result[2])
        return result

    def get_required_symbols(self) -> list[str]:
        """830/21 Required symbols - unique Bond Check symbols."""
        # Standard overbought detection
        overbought_symbols = [
            "QQQE",
            "VTV",
            "VOX",
            "TECL",
            "VOOG",
            "VOOV",
            "XLP",
            "TQQQ",
            "XLY",
            "FAS",
            "SPY",
        ]

        # Single Popped KMLM
        single_popped_symbols = ["UVXY"]

        # BSC strategy
        bsc_symbols = ["VIXM", "SPXL"]

        # Combined Pop Bot (no LABU)
        pop_bot_symbols = ["SOXL"]  # TQQQ, SPXL, TECL already included

        # KMLM Switcher - TECL/SOXL/SVIX
        kmlm_switcher_symbols = ["XLK", "KMLM", "SVIX"]

        # Bond Check symbols - UNIQUE to 830/21
        bond_check_symbols = ["BND", "SPLV", "TLT", "LABD", "TZA"]

        return list(
            set(
                overbought_symbols
                + single_popped_symbols
                + bsc_symbols
                + pop_bot_symbols
                + kmlm_switcher_symbols
                + bond_check_symbols
            )
        )
