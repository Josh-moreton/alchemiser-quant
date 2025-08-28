"""Business Unit: utilities; Status: current.

KLM Strategy Variant 1200/28 - "KMLM (43)".

This variant is nearly IDENTICAL to 506/38 except:
- KMLM Switcher uses select-bottom 1 from TECL/SOXL/SVIX (instead of FNGU)
- Everything else is the same: Single Popped KMLM, BSC, Combined Pop Bot (no LABU)

Pattern: QQQE → VTV → VOX → TECL → VOOG → VOOV → XLP → TQQQ → XLY → FAS → SPY →
         Single Popped KMLM (UVXY RSI check → BSC or Pop Bot → KMLM Switcher)
"""
from __future__ import annotations


import pandas as pd

from the_alchemiser.utils.common import ActionType

from .base_klm_variant import BaseKLMVariant


class KlmVariant120028(BaseKLMVariant):
    """Variant 1200/28 - Same as 506/38 except KMLM Switcher logic.

    Key difference: KMLM Switcher uses select-bottom 1 from TECL/SOXL/SVIX (not FNGU)
    """

    def __init__(self) -> None:
        super().__init__(
            name="1200/28", description="KMLM (43) - Standard pattern with TECL/SOXL/SVIX switcher"
        )

    def evaluate(
        self,
        indicators: dict[str, dict[str, float]],
        market_data: dict[str, pd.DataFrame] | None = None,
    ) -> tuple[str | dict[str, float], str, str]:
        """Evaluate 1200/28 - same as 506/38 except KMLM Switcher."""
        # Step 1: Primary overbought checks → UVXY
        symbol, reason = self.check_primary_overbought_conditions(indicators)
        if symbol:
            self.log_decision(symbol, ActionType.BUY.value, reason)
            return symbol, ActionType.BUY.value, reason

        # Step 2: Single Popped KMLM logic (same as 506/38)
        return self._evaluate_single_popped_kmlm(indicators)

    def _evaluate_single_popped_kmlm(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[str | dict[str, float], str, str]:
        """Single Popped KMLM logic - identical to 506/38."""
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
        """BSC strategy - identical to 506/38."""
        if "SPY" in indicators:
            spy_rsi_21 = indicators["SPY"]["rsi_21"]

            if spy_rsi_21 > 30:
                result = ("VIXM", ActionType.BUY.value, "1200/28 BSC: SPY RSI(21) > 30 → VIXM")
            else:
                result = (
                    "SPXL",
                    ActionType.BUY.value,
                    "1200/28 BSC: SPY oversold (RSI(21) <= 30) → SPXL",
                )
        else:
            result = ("VIXM", ActionType.BUY.value, "1200/28 BSC: Default VIX position")

        self.log_decision(result[0], result[1], result[2])
        return result

    def _evaluate_combined_pop_bot(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[str | dict[str, float], str, str]:
        """Combined Pop Bot - identical to 506/38 (NO LABU)."""
        # Priority 1: TQQQ oversold
        if "TQQQ" in indicators and indicators["TQQQ"]["rsi_10"] < 30:
            result = ("TECL", ActionType.BUY.value, "1200/28 Pop Bot: TQQQ RSI < 30 → TECL")
            self.log_decision(result[0], result[1], result[2])
            return result

        # Priority 2: SOXL oversold
        if "SOXL" in indicators and indicators["SOXL"]["rsi_10"] < 30:
            result = ("SOXL", ActionType.BUY.value, "1200/28 Pop Bot: SOXL RSI < 30 → SOXL")
            self.log_decision(result[0], result[1], result[2])
            return result

        # Priority 3: SPXL oversold
        if "SPXL" in indicators and indicators["SPXL"]["rsi_10"] < 30:
            result = ("SPXL", ActionType.BUY.value, "1200/28 Pop Bot: SPXL RSI < 30 → SPXL")
            self.log_decision(result[0], result[1], result[2])
            return result

        # No oversold conditions - proceed to KMLM Switcher
        return self.evaluate_core_kmlm_switcher(indicators)

    def evaluate_core_kmlm_switcher(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[str | dict[str, float], str, str]:
        """Core KMLM switcher for variant 1200/28."""
        return self._evaluate_kmlm_switcher_1200(indicators)

    def _evaluate_kmlm_switcher_1200(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[str | dict[str, float], str, str]:
        """1200/28 KMLM Switcher - KEY DIFFERENCE from 506/38.

        Uses select-bottom 1 from TECL/SOXL/SVIX (not FNGU like 506/38)
        """
        if "XLK" in indicators and "KMLM" in indicators:
            xlk_rsi = indicators["XLK"]["rsi_10"]
            kmlm_rsi = indicators["KMLM"]["rsi_10"]

            if xlk_rsi > kmlm_rsi:
                # select-bottom 1 from TECL, SOXL, SVIX
                candidates = []
                for symbol in ["TECL", "SOXL", "SVIX"]:
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
                        f"1200/28 KMLM Switcher: XLK > KMLM → {selected[0]} (lowest RSI: {selected[1]:.1f})",
                    )
                else:
                    result = ("TECL", ActionType.BUY.value, "1200/28 KMLM Switcher: TECL fallback")

                self.log_decision(result[0], result[1], result[2])
                return result

        # XLK <= KMLM → L/S Rotator (need to check CLJ for exact logic)
        return self._evaluate_ls_rotator_1200(indicators)

    def _evaluate_ls_rotator_1200(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[str, str, str]:
        """1200/28 L/S Rotator - need to check if same as others or different
        For now, assume similar to 1280/26 (SQQQ/TLT select-top 1).
        """
        candidates = []
        for symbol in ["SQQQ", "TLT"]:
            if symbol in indicators:
                rsi = indicators[symbol]["rsi_10"]
                candidates.append((symbol, rsi))

        if candidates:
            # Select top 1 (highest RSI) - contrarian strategy
            candidates.sort(key=lambda x: x[1], reverse=True)
            top_candidate = candidates[0]
            result = (
                top_candidate[0],
                ActionType.BUY.value,
                f"1200/28 L/S Rotator: {top_candidate[0]} (highest RSI: {top_candidate[1]:.1f})",
            )
        else:
            result = ("BIL", ActionType.BUY.value, "1200/28 L/S Rotator: BIL fallback")

        self.log_decision(result[0], result[1], result[2])
        return result

    def get_required_symbols(self) -> list[str]:
        """1200/28 Required symbols - same as 506/38 except FNGU → SVIX."""
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

        # KMLM Switcher - TECL/SOXL/SVIX (not FNGU)
        kmlm_switcher_symbols = ["XLK", "KMLM", "SVIX"]

        # L/S Rotator - SQQQ/TLT
        rotator_symbols = ["SQQQ", "TLT"]

        # Fallback
        fallback_symbols = ["BIL"]

        return list(
            set(
                overbought_symbols
                + single_popped_symbols
                + bsc_symbols
                + pop_bot_symbols
                + kmlm_switcher_symbols
                + rotator_symbols
                + fallback_symbols
            )
        )
