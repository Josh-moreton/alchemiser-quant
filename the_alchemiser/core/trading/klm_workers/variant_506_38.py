"""
KLM Strategy Variant 506/38 - "KMLM (13) - Longer BT"

This is the first variant in the Clojure strategy ensemble. It follows the standard
overbought detection pattern followed by "Single Popped KMLM" logic.

Pattern: QQQE → VTV → VOX → TECL → VOOG → VOOV → XLP → TQQQ → XLY → FAS → SPY →
         Single Popped KMLM (UVXY RSI check → BSC or Pop Bot → Core KMLM Switcher)

CORRECTED LOGIC:
- KMLM Switcher: When XLK > KMLM → FNGU (NOT TECL/SOXL/SVIX)
- L/S Rotator: UUP, FTLS, KMLM only (NOT SVXY/VIXM/SVIX)
- This matches CLJ lines 170-195 exactly
"""

import pandas as pd

from the_alchemiser.core.utils.common import ActionType

from .base_klm_variant import BaseKLMVariant


class KlmVariant50638(BaseKLMVariant):
    """
    Variant 506/38 - Standard overbought detection with Single Popped KMLM fallback

    This variant represents the most common pattern in the KLM ensemble:
    1. Primary overbought checks → UVXY
    2. Single Popped KMLM logic (UVXY RSI-based branching)
    3. BSC strategy or Pop Bot + Core KMLM Switcher
    """

    def __init__(self):
        super().__init__(
            name="506/38", description="KMLM (13) - Longer BT - Standard overbought detection"
        )

    def evaluate(
        self,
        indicators: dict[str, dict[str, float]],
        market_data: dict[str, pd.DataFrame] | None = None,
    ) -> tuple[str | dict[str, float], str, str]:
        """
        Evaluate the 506/38 variant strategy.

        Returns:
            Tuple of (symbol_or_allocation, action, reason)
        """

        # Step 1: Primary overbought checks (common across most variants)
        symbol, reason = self.check_primary_overbought_conditions(indicators)
        if symbol:
            self.log_decision(symbol, ActionType.BUY.value, reason)
            return symbol, ActionType.BUY.value, reason

        # Step 2: Single Popped KMLM logic
        return self._evaluate_single_popped_kmlm(indicators)

    def _evaluate_single_popped_kmlm(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[str | dict[str, float], str, str]:
        """
        Single Popped KMLM logic from Clojure:
        Checks UVXY RSI to decide between BSC strategy or Combined Pop Bot
        """

        # Check UVXY RSI(21) for strategy branching
        if "UVXY" in indicators:
            uvxy_rsi_21 = indicators["UVXY"]["rsi_21"]

            if uvxy_rsi_21 > 65:
                # UVXY elevated - use BSC (Bond/Stock/Commodity) strategy
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
        BSC (Bond/Stock/Commodity) strategy when UVXY RSI > 65

        Logic from Clojure:
        - If SPY RSI(21) > 30: VIXM (moderate VIX position)
        - Else: SPXL (leveraged long position)
        """
        if "SPY" in indicators:
            spy_rsi_21 = indicators["SPY"]["rsi_21"]

            if spy_rsi_21 > 30:
                result = (
                    "VIXM",
                    ActionType.BUY.value,
                    "BSC: SPY RSI(21) > 30, moderate VIX position",
                )
            else:
                result = (
                    "SPXL",
                    ActionType.BUY.value,
                    "BSC: SPY oversold (RSI(21) <= 30), leveraged long position",
                )
        else:
            # Fallback
            result = ("VIXM", ActionType.BUY.value, "BSC: Default VIX position (no SPY data)")

        self.log_decision(result[0], result[1], result[2])
        return result

    def _evaluate_combined_pop_bot(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[str | dict[str, float], str, str]:
        """
        Combined Pop Bot strategy for oversold conditions and sector rotation

        Logic from Clojure:
        1. Check for oversold conditions (TQQQ, SOXL, SPXL, LABU)
        2. If none oversold, proceed to Core KMLM Switcher
        """

        # Priority 1: TQQQ oversold check
        if "TQQQ" in indicators and indicators["TQQQ"]["rsi_10"] < 30:
            result = (
                "TECL",
                ActionType.BUY.value,
                "Pop Bot: TQQQ oversold (RSI < 30), tech dip buy",
            )
            self.log_decision(result[0], result[1], result[2])
            return result

        # Priority 2: SOXL oversold check
        if "SOXL" in indicators and indicators["SOXL"]["rsi_10"] < 30:
            result = (
                "SOXL",
                ActionType.BUY.value,
                "Pop Bot: SOXL oversold (RSI < 30), semiconductor dip buy",
            )
            self.log_decision(result[0], result[1], result[2])
            return result

        # Priority 3: SPXL oversold check
        if "SPXL" in indicators and indicators["SPXL"]["rsi_10"] < 30:
            result = (
                "SPXL",
                ActionType.BUY.value,
                "Pop Bot: SPXL oversold (RSI < 30), S&P dip buy",
            )
            self.log_decision(result[0], result[1], result[2])
            return result

        # Priority 4: LABU oversold check (biotech with different threshold)
        if "LABU" in indicators and indicators["LABU"]["rsi_10"] < 25:
            result = (
                "LABU",
                ActionType.BUY.value,
                "Pop Bot: LABU oversold (RSI < 25), biotech dip buy",
            )
            self.log_decision(result[0], result[1], result[2])
            return result

        # No oversold conditions - proceed to Core KMLM Switcher
        return self.evaluate_core_kmlm_switcher(indicators)

    def evaluate_core_kmlm_switcher(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[str | dict[str, float], str, str]:
        """
        Core KMLM switcher logic - CORRECTED to match CLJ exactly:

        From CLJ lines 170-182: When XLK > KMLM, select FNGU with RSI filter (select-bottom 1)
        This was completely wrong before - it should be FNGU, not TECL/SOXL/SVIX!
        """

        # Step 1: XLK vs KMLM comparison for FNGU selection
        if "XLK" in indicators and "KMLM" in indicators:
            xlk_rsi = indicators["XLK"]["rsi_10"]
            kmlm_rsi = indicators["KMLM"]["rsi_10"]

            if xlk_rsi > kmlm_rsi:
                # CLJ: filter (rsi {:window 10}) (select-bottom 1) [(asset "FNGU")]
                # This means select FNGU (since it's the only candidate with select-bottom 1)
                result = (
                    "FNGU",
                    ActionType.BUY.value,
                    f"KMLM Switcher: XLK RSI {xlk_rsi:.1f} > KMLM RSI {kmlm_rsi:.1f} → FNGU",
                )
                self.log_decision(result[0], result[1], result[2])
                return result

        # Step 2: Long/Short Rotator logic (when XLK <= KMLM or missing data)
        return self._evaluate_long_short_rotator(indicators)

    def _evaluate_long_short_rotator(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[str | dict[str, float], str, str]:
        """
        Long/Short Rotator - CORRECTED to match CLJ exactly

        From CLJ lines 184-195: "Long/Short Rotator with FTLS KMLM SSO UUP"
        filter (stdev-return {:window 6}) (select-bottom 1) [UUP, FTLS, KMLM]

        This was wrong before - should only use UUP, FTLS, KMLM (not SVXY, VIXM, SVIX)
        """

        # CLJ specifies: UUP, FTLS, KMLM with stdev-return filter (select-bottom 1)
        rotator_symbols = ["UUP", "FTLS", "KMLM"]

        # Apply volatility filter (stdev-return window 6)
        volatility_candidates = []
        for symbol in rotator_symbols:
            if symbol in indicators and "stdev_return_6" in indicators[symbol]:
                stdev = indicators[symbol]["stdev_return_6"]
                volatility_candidates.append((symbol, stdev))

        if volatility_candidates:
            # Select bottom 1 by volatility (lowest standard deviation) - exact CLJ logic
            bottom_1 = self.apply_select_bottom_filter(volatility_candidates, 1)
            selected_symbol = bottom_1[0][0]
            selected_stdev = bottom_1[0][1]

            result = (
                selected_symbol,
                ActionType.BUY.value,
                f"L/S Rotator: {selected_symbol} (lowest volatility: {selected_stdev:.3f})",
            )

        else:
            # Fallback - CLJ doesn't specify this, but we need something
            # Default to KMLM since it's the most defensive in the list
            result = (
                "KMLM",
                ActionType.BUY.value,
                "L/S Rotator: KMLM fallback (missing volatility data)",
            )

        self.log_decision(result[0], result[1], result[2])
        return result

    def get_required_symbols(self) -> list[str]:
        """
        506/38 Required symbols - CORRECTED to match CLJ exactly

        Primary overbought: QQQE, VTV, VOX, TECL, VOOG, VOOV, XLP, TQQQ, XLY, FAS, SPY
        Single Popped KMLM: UVXY, SPY (RSI 21)
        BSC Strategy: VIXM, SPXL
        Combined Pop Bot: TQQQ, SOXL, SPXL, TECL
        KMLM Switcher: XLK, KMLM, FNGU (CORRECTED!)
        L/S Rotator: UUP, FTLS, KMLM (CORRECTED!)
        """

        # Primary overbought detection symbols
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

        # Single Popped KMLM symbols
        single_popped_symbols = ["UVXY"]

        # BSC strategy symbols
        bsc_symbols = ["VIXM", "SPXL"]

        # Combined Pop Bot symbols
        pop_bot_symbols = ["SOXL"]  # TQQQ, SPXL, TECL already in other lists

        # KMLM Switcher symbols - CORRECTED
        kmlm_switcher_symbols = ["XLK", "KMLM", "FNGU"]

        # Long/Short Rotator symbols - CORRECTED
        rotator_symbols = ["UUP", "FTLS"]  # KMLM already in kmlm_switcher_symbols

        # Combine all unique symbols
        all_symbols = (
            overbought_symbols
            + single_popped_symbols
            + bsc_symbols
            + pop_bot_symbols
            + kmlm_switcher_symbols
            + rotator_symbols
        )

        return list(set(all_symbols))
