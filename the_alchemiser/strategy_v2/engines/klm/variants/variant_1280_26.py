"""Business Unit: strategy | Status: current

KLM Strategy Variant 1280/26 - "KMLM (50)".

COMPLETELY DIFFERENT from 506/38! This variant:
1. Uses standard overbought detection → UVXY
2. Goes directly to Combined Pop Bot (NO Single Popped KMLM logic)
3. Combined Pop Bot includes LABU with RSI < 25 threshold
4. KMLM Switcher uses select-bottom 2 from TECL/SOXL/SVIX (NOT FNGU)
5. L/S Rotator uses SQQQ/TLT with select-top 1 (NOT UUP/FTLS/KMLM)

This is a fundamentally different architecture from other variants.
"""

from __future__ import annotations

import pandas as pd

from the_alchemiser.shared.utils.common import ActionType
from the_alchemiser.shared.value_objects.core_types import KLMDecision

from ..base_variant import BaseKLMVariant


class KlmVariant128026(BaseKLMVariant):
    """Variant 1280/26 - COMPLETELY different from 506/38.

    Key differences:
    - NO Single Popped KMLM logic (goes directly from overbought to Combined Pop Bot)
    - Combined Pop Bot includes LABU (RSI < 25)
    - KMLM Switcher uses select-bottom 2 from TECL/SOXL/SVIX
    - L/S Rotator uses SQQQ/TLT with select-top 1
    """

    def __init__(self) -> None:
        super().__init__(
            name="1280/26", description="KMLM (50) - Direct to Combined Pop Bot variant"
        )

    def evaluate(
        self,
        indicators: dict[str, dict[str, float]],
        market_data: dict[str, pd.DataFrame] | None = None,
    ) -> KLMDecision:
        """Evaluate 1280/26 - completely different flow from 506/38.

        Flow: Overbought Detection → Combined Pop Bot → KMLM Switcher
        (NO Single Popped KMLM logic)
        """
        # Step 1: Standard overbought checks → UVXY
        overbought_result = self.check_primary_overbought_conditions(indicators)
        if overbought_result:
            self.log_klm_decision(overbought_result)
            return overbought_result

        # Step 2: Combined Pop Bot (includes LABU!)
        return self._evaluate_combined_pop_bot_with_labu(indicators)

    def _evaluate_combined_pop_bot_with_labu(
        self, indicators: dict[str, dict[str, float]]
    ) -> KLMDecision:
        """Combined Pop Bot for 1280/26 - includes LABU with RSI < 25.

        Order: TQQQ < 30 → SOXL < 30 → SPXL < 30 → LABU < 25 → KMLM Switcher
        """
        # Priority 1: TQQQ oversold
        if "TQQQ" in indicators and indicators["TQQQ"]["rsi_10"] < 30:
            result = self.create_klm_decision(
                "TECL", ActionType.BUY.value, "1280/26 Pop Bot: TQQQ RSI < 30 → TECL"
            )
            self.log_klm_decision(result)
            return result

        # Priority 2: SOXL oversold
        if "SOXL" in indicators and indicators["SOXL"]["rsi_10"] < 30:
            result = self.create_klm_decision(
                "SOXL", ActionType.BUY.value, "1280/26 Pop Bot: SOXL RSI < 30 → SOXL"
            )
            self.log_klm_decision(result)
            return result

        # Priority 3: SPXL oversold
        if "SPXL" in indicators and indicators["SPXL"]["rsi_10"] < 30:
            result = self.create_klm_decision(
                "SPXL", ActionType.BUY.value, "1280/26 Pop Bot: SPXL RSI < 30 → SPXL"
            )
            self.log_klm_decision(result)
            return result

        # Priority 4: LABU oversold (KEY DIFFERENCE - this variant includes LABU)
        if "LABU" in indicators and indicators["LABU"]["rsi_10"] < 25:
            result = self.create_klm_decision(
                "LABU", ActionType.BUY.value, "1280/26 Pop Bot: LABU RSI < 25 → LABU"
            )
            self.log_klm_decision(result)
            return result

        # No oversold conditions - proceed to KMLM Switcher
        return self.evaluate_core_kmlm_switcher(indicators)

    def evaluate_core_kmlm_switcher(self, indicators: dict[str, dict[str, float]]) -> KLMDecision:
        """Core KMLM switcher for variant 1280/26.

        select-bottom 2 from TECL/SOXL/SVIX (NOT FNGU) creates equal-weight allocation.
        CLJ lines 331-350: When XLK > KMLM → select-bottom 2 from [TECL, SOXL, SVIX]
        """
        if "XLK" in indicators and "KMLM" in indicators:
            xlk_rsi = indicators["XLK"]["rsi_10"]
            kmlm_rsi = indicators["KMLM"]["rsi_10"]

            if xlk_rsi > kmlm_rsi:
                # select-bottom 2 from TECL, SOXL, SVIX
                candidates = []
                for symbol in ["TECL", "SOXL", "SVIX"]:
                    if symbol in indicators:
                        rsi = indicators[symbol]["rsi_10"]
                        candidates.append((symbol, rsi))

                if len(candidates) >= 2:
                    # Select bottom 2 (lowest RSI values)
                    bottom_2 = self.apply_select_bottom_filter(candidates, 2)
                    # Create equal weight allocation (50/50)
                    allocation = {symbol: 0.5 for symbol, _ in bottom_2}
                    selected_symbols = [symbol for symbol, _ in bottom_2]
                    result = self.create_klm_decision(
                        allocation,
                        ActionType.BUY.value,
                        f"1280/26 KMLM Switcher: {', '.join(selected_symbols)} (bottom 2 RSI)",
                    )
                    self.log_klm_decision(result)
                    return result
                if candidates:
                    # Only one candidate available, use it
                    selected_symbol = candidates[0][0]
                    result = self.create_klm_decision(
                        selected_symbol,
                        ActionType.BUY.value,
                        f"1280/26 KMLM Switcher: {selected_symbol} (only candidate)",
                    )
                    self.log_klm_decision(result)
                    return result

        # XLK <= KMLM → L/S Rotator
        return self._evaluate_ls_rotator_1280(indicators)

    def _evaluate_ls_rotator_1280(self, indicators: dict[str, dict[str, float]]) -> KLMDecision:
        """1280/26 L/S Rotator - uses SQQQ/TLT select-top 1."""
        candidates = []
        for symbol in ["SQQQ", "TLT"]:
            if symbol in indicators:
                rsi = indicators[symbol]["rsi_10"]
                candidates.append((symbol, rsi))

        if candidates:
            # Select top 1 (highest RSI) - contrarian strategy
            top_1 = self.apply_select_top_filter(candidates, 1)
            selected_symbol = top_1[0][0]
            selected_rsi = top_1[0][1]
            result = self.create_klm_decision(
                selected_symbol,
                ActionType.BUY.value,
                f"1280/26 L/S Rotator: {selected_symbol} (highest RSI: {selected_rsi:.1f})",
            )
        else:
            # Fallback
            result = self.create_klm_decision(
                "TLT", ActionType.BUY.value, "1280/26 L/S Rotator: TLT fallback"
            )

        self.log_klm_decision(result)
        return result

    def get_required_symbols(self) -> list[str]:
        """1280/26 Required symbols - completely different from 506/38."""
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
            "UVXY",
        ]

        # Combined Pop Bot with LABU
        pop_bot_symbols = ["SOXL", "SPXL", "LABU"]

        # KMLM Switcher - TECL/SOXL/SVIX (NOT FNGU)
        kmlm_switcher_symbols = ["XLK", "KMLM", "SVIX"]  # TECL, SOXL already included

        # L/S Rotator - SQQQ/TLT (NOT UUP/FTLS/KMLM)
        rotator_symbols = ["SQQQ", "TLT"]

        # Defensive fallback
        fallback_symbols = ["BIL"]

        return list(
            set(
                overbought_symbols
                + pop_bot_symbols
                + kmlm_switcher_symbols
                + rotator_symbols
                + fallback_symbols
            )
        )
