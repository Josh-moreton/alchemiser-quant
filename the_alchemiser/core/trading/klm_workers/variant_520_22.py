"""
KLM Strategy Variant 520/22 - "KMLM (23) - Original"

This variant is similar to 506/38 and 1200/28 except:
- KMLM Switcher uses select-bottom 1 from TECL/SVIX only (no SOXL, no FNGU)
- L/S Rotator uses FTLS/KMLM/SSO/UUP (not SQQQ/TLT like others)
- Everything else is the same: Single Popped KMLM, BSC, Combined Pop Bot (no LABU)

This is the "Original" baseline implementation.
"""

import pandas as pd

from the_alchemiser.core.utils.common import ActionType

from .base_klm_variant import BaseKLMVariant


class KlmVariant52022(BaseKLMVariant):
    """
    Variant 520/22 - "Original" with TECL/SVIX switcher and FTLS/KMLM/SSO/UUP rotator

    Key differences:
    - KMLM Switcher: TECL/SVIX only (no SOXL)
    - L/S Rotator: FTLS/KMLM/SSO/UUP (not SQQQ/TLT)
    """

    def __init__(self) -> None:
        super().__init__(
            name="520/22", description="KMLM (23) - Original baseline with TECL/SVIX switcher"
        )

    def evaluate(
        self,
        indicators: dict[str, dict[str, float]],
        market_data: dict[str, pd.DataFrame] | None = None,
    ) -> tuple[str | dict[str, float], str, str]:
        """
        Evaluate 520/22 - same as 506/38 except KMLM Switcher and L/S Rotator
        """

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
        """
        Single Popped KMLM logic - identical to 506/38
        """

        # Check UVXY RSI(21) for strategy branching
        if "UVXY" in indicators:
            uvxy_rsi_21 = indicators["UVXY"]["rsi_21"]

            if uvxy_rsi_21 > 65:
                # UVXY elevated - use BSC strategy
                return self._evaluate_bsc_strategy(indicators)
            else:
                # UVXY normal - use Combined Pop Bot
                return self._evaluate_combined_pop_bot(indicators)

        # Fallback if UVXY data unavailable
        return self._evaluate_combined_pop_bot(indicators)

    def _evaluate_bsc_strategy(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[str, str, str]:
        """
        BSC strategy - identical to other variants
        """
        if "SPY" in indicators:
            spy_rsi_21 = indicators["SPY"]["rsi_21"]

            if spy_rsi_21 > 30:
                result = ("VIXM", ActionType.BUY.value, "520/22 BSC: SPY RSI(21) > 30 → VIXM")
            else:
                result = (
                    "SPXL",
                    ActionType.BUY.value,
                    "520/22 BSC: SPY oversold (RSI(21) <= 30) → SPXL",
                )
        else:
            result = ("VIXM", ActionType.BUY.value, "520/22 BSC: Default VIX position")

        self.log_decision(result[0], result[1], result[2])
        return result

    def _evaluate_combined_pop_bot(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[str | dict[str, float], str, str]:
        """
        Combined Pop Bot - identical to 506/38 and 1200/28 (NO LABU)
        """

        # Priority 1: TQQQ oversold
        if "TQQQ" in indicators and indicators["TQQQ"]["rsi_10"] < 30:
            result = ("TECL", ActionType.BUY.value, "520/22 Pop Bot: TQQQ RSI < 30 → TECL")
            self.log_decision(result[0], result[1], result[2])
            return result

        # Priority 2: SOXL oversold
        if "SOXL" in indicators and indicators["SOXL"]["rsi_10"] < 30:
            result = ("SOXL", ActionType.BUY.value, "520/22 Pop Bot: SOXL RSI < 30 → SOXL")
            self.log_decision(result[0], result[1], result[2])
            return result

        # Priority 3: SPXL oversold
        if "SPXL" in indicators and indicators["SPXL"]["rsi_10"] < 30:
            result = ("SPXL", ActionType.BUY.value, "520/22 Pop Bot: SPXL RSI < 30 → SPXL")
            self.log_decision(result[0], result[1], result[2])
            return result

        # No oversold conditions - proceed to KMLM Switcher
        return self.evaluate_core_kmlm_switcher(indicators)

    def evaluate_core_kmlm_switcher(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[str | dict[str, float], str, str]:
        """
        Core KMLM switcher for variant 520/22
        """
        return self._evaluate_kmlm_switcher_520(indicators)

    def _evaluate_kmlm_switcher_520(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[str | dict[str, float], str, str]:
        """
        520/22 KMLM Switcher - KEY DIFFERENCE: TECL/SVIX only (no SOXL)

        CLJ shows: select-bottom 1 from [TECL, SVIX] (not TECL/SOXL/SVIX)
        """

        if "XLK" in indicators and "KMLM" in indicators:
            xlk_rsi = indicators["XLK"]["rsi_10"]
            kmlm_rsi = indicators["KMLM"]["rsi_10"]

            if xlk_rsi > kmlm_rsi:
                # select-bottom 1 from TECL, SVIX only
                candidates = []
                for symbol in ["TECL", "SVIX"]:
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
                        f"520/22 KMLM Switcher: XLK > KMLM → {selected[0]} (lowest RSI: {selected[1]:.1f})",
                    )
                else:
                    result = ("TECL", ActionType.BUY.value, "520/22 KMLM Switcher: TECL fallback")

                self.log_decision(result[0], result[1], result[2])
                return result

        # XLK <= KMLM → L/S Rotator
        return self._evaluate_ls_rotator_520(indicators)

    def _evaluate_ls_rotator_520(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[str, str, str]:
        """
        520/22 L/S Rotator - DIFFERENT: uses FTLS/KMLM/SSO/UUP (not SQQQ/TLT)

        CLJ shows: "Long/Short Rotator with FTLS KMLM SSO UUP"
        This is similar to 506/38 but with SSO instead of just UUP/FTLS/KMLM
        """

        # Volatility filter candidates: FTLS, KMLM, SSO, UUP
        rotator_symbols = ["FTLS", "KMLM", "SSO", "UUP"]

        candidates = []
        for symbol in rotator_symbols:
            if symbol in indicators and "stdev_return_6" in indicators[symbol]:
                stdev = indicators[symbol]["stdev_return_6"]
                candidates.append((symbol, stdev))

        if candidates:
            # Select bottom 1 (lowest volatility) - same pattern as 506/38
            candidates.sort(key=lambda x: x[1])
            selected = candidates[0]
            result = (
                selected[0],
                ActionType.BUY.value,
                f"520/22 L/S Rotator: {selected[0]} (lowest volatility: {selected[1]:.3f})",
            )
        else:
            # Fallback to KMLM
            result = ("KMLM", ActionType.BUY.value, "520/22 L/S Rotator: KMLM fallback")

        self.log_decision(result[0], result[1], result[2])
        return result

    def get_required_symbols(self) -> list[str]:
        """
        520/22 Required symbols - "Original" baseline
        """

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

        # KMLM Switcher - TECL/SVIX only (not SOXL, not FNGU)
        kmlm_switcher_symbols = ["XLK", "KMLM", "SVIX"]

        # L/S Rotator - FTLS/KMLM/SSO/UUP (not SQQQ/TLT)
        rotator_symbols = ["FTLS", "SSO", "UUP"]  # KMLM already included

        return list(
            set(
                overbought_symbols
                + single_popped_symbols
                + bsc_symbols
                + pop_bot_symbols
                + kmlm_switcher_symbols
                + rotator_symbols
            )
        )
