"""Business Unit: strategy | Status: current

KLM Strategy Variant 830/21 - "MonkeyBusiness Simons variant V2".

This variant is similar to other standard variants except:
1. KMLM Switcher uses select-TOP 1 from TECL/SOXL/SVIX (opposite of others)
2. L/S Rotator has "Bond Check" logic using BND moving-average-return
3. Different symbols in the Bond Check paths

This is the V2 (enhanced) version of the MonkeyBusiness Simons approach.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from the_alchemiser.shared.utils.common import ActionType

if TYPE_CHECKING:
    from the_alchemiser.shared.value_objects.core_types import KLMDecision
else:
    # Import for runtime use
    from the_alchemiser.shared.value_objects.core_types import KLMDecision

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
    ) -> KLMDecision:
        """Evaluate 830/21 - same as other variants except KMLM Switcher and Bond Check."""
        # Step 1: Primary overbought checks → UVXY
        overbought_result = self.check_primary_overbought_conditions(indicators)
        if overbought_result:
            self.log_klm_decision(overbought_result)
            return overbought_result

        # Step 2: Single Popped KMLM logic (same as others)
        return self.evaluate_single_popped_kmlm(indicators)

    def evaluate_core_kmlm_switcher(self, indicators: dict[str, dict[str, float]]) -> KLMDecision:
        """Core KMLM switcher for variant 830/21.

        KEY DIFFERENCE: select-TOP 1 (highest RSI).
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
                    # Select top 1 (highest RSI) - opposite of other variants
                    top_1 = self.apply_select_top_filter(candidates, 1)
                    selected_symbol = top_1[0][0]
                    selected_rsi = top_1[0][1]
                    result = self.create_klm_decision(
                        selected_symbol,
                        ActionType.BUY.value,
                        f"830/21 KMLM Switcher: {selected_symbol} (highest RSI: {selected_rsi:.1f})",
                    )
                    self.log_klm_decision(result)
                    return result

        # Fallback to Bond Check logic if XLK <= KMLM or missing data
        return self._evaluate_bond_check(indicators)

    def _evaluate_bond_check(self, indicators: dict[str, dict[str, float]]) -> KLMDecision:
        """830/21 Bond Check - uses BND moving-average-return logic."""
        # Check BND moving average return (window 20)
        if "BND" in indicators and "ma_return_90" in indicators["BND"]:
            bnd_ma_return = indicators["BND"]["ma_return_90"]

            if bnd_ma_return > 0:
                # Positive BND return → KMLM/SPLV path
                return self._evaluate_kmlm_splv_path(indicators)
            # Negative/zero BND return → TLT/LABD/TZA path
            return self._evaluate_tlt_path(indicators)

        # Fallback if BND data unavailable
        return self.create_klm_decision(
            "KMLM", ActionType.BUY.value, "830/21 Bond Check: KMLM fallback"
        )

    def _evaluate_kmlm_splv_path(self, indicators: dict[str, dict[str, float]]) -> KLMDecision:
        """KMLM/SPLV path when BND MA return > 0."""
        # Select between KMLM and SPLV using volatility filter
        candidates = []
        for symbol in ["KMLM", "SPLV"]:
            if symbol in indicators and "stdev_return_6" in indicators[symbol]:
                stdev = indicators[symbol]["stdev_return_6"]
                candidates.append((symbol, stdev))

        if candidates:
            # Select bottom 1 (lowest volatility)
            bottom_1 = self.apply_select_bottom_filter(candidates, 1)
            selected_symbol = bottom_1[0][0]
            selected_stdev = bottom_1[0][1]
            return self.create_klm_decision(
                selected_symbol,
                ActionType.BUY.value,
                f"830/21 KMLM/SPLV: {selected_symbol} (lowest volatility: {selected_stdev:.3f})",
            )
        return self.create_klm_decision(
            "KMLM", ActionType.BUY.value, "830/21 KMLM/SPLV: KMLM fallback"
        )

    def _evaluate_tlt_path(self, indicators: dict[str, dict[str, float]]) -> KLMDecision:
        """TLT/LABD/TZA path when BND MA return <= 0."""
        # Select from TLT, LABD, TZA using volatility filter
        candidates = []
        for symbol in ["TLT", "LABD", "TZA"]:
            if symbol in indicators and "stdev_return_6" in indicators[symbol]:
                stdev = indicators[symbol]["stdev_return_6"]
                candidates.append((symbol, stdev))

        if candidates:
            # Select bottom 1 (lowest volatility)
            bottom_1 = self.apply_select_bottom_filter(candidates, 1)
            selected_symbol = bottom_1[0][0]
            selected_stdev = bottom_1[0][1]
            return self.create_klm_decision(
                selected_symbol,
                ActionType.BUY.value,
                f"830/21 TLT path: {selected_symbol} (lowest volatility: {selected_stdev:.3f})",
            )
        return self.create_klm_decision(
            "TLT", ActionType.BUY.value, "830/21 TLT path: TLT fallback"
        )

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
