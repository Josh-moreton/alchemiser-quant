"""Business Unit: strategy | Status: current

KLM Strategy Variant 506/38 - "KMLM (13) - Longer BT".

This is the first variant in the Clojure strategy ensemble. It follows the standard
overbought detection pattern followed by "Single Popped KMLM" logic.

Pattern: QQQE → VTV → VOX → TECL → VOOG → VOOV → XLP → TQQQ → XLY → FAS → SPY →
         Single Popped KMLM (UVXY RSI check → BSC or Pop Bot → Core KMLM Switcher)

CORRECTED LOGIC:
- KMLM Switcher: When XLK > KMLM → FNGU (NOT TECL/SOXL/SVIX)
- L/S Rotator: UUP, FTLS, KMLM only (NOT SVXY/VIXM/SVIX)
- This matches CLJ lines 170-195 exactly
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


class KlmVariant50638(BaseKLMVariant):
    """Variant 506/38 - Standard overbought detection with Single Popped KMLM fallback.

    This variant represents the most common pattern in the KLM ensemble:
    1. Primary overbought checks → UVXY
    2. Single Popped KMLM logic (UVXY RSI-based branching)
    3. BSC strategy or Pop Bot + Core KMLM Switcher
    """

    def __init__(self) -> None:
        super().__init__(
            name="506/38", description="KMLM (13) - Longer BT - Standard overbought detection"
        )

    def evaluate(
        self,
        indicators: dict[str, dict[str, float]],
        market_data: dict[str, pd.DataFrame] | None = None,
    ) -> KLMDecision:
        """Evaluate the 506/38 variant strategy.

        Returns:
            KLMDecision with symbol, action, and reasoning

        """
        # Step 1: Primary overbought checks (common across most variants)
        overbought_result = self.check_primary_overbought_conditions(indicators)
        if overbought_result:
            self.log_klm_decision(overbought_result)
            return overbought_result

        # Step 2: Single Popped KMLM logic
        return self.evaluate_single_popped_kmlm(indicators)

    def evaluate_core_kmlm_switcher(
        self, indicators: dict[str, dict[str, float]]
    ) -> KLMDecision:
        """Core KMLM switcher logic - CORRECTED to match CLJ exactly:

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
                result = self.create_klm_decision(
                    "FNGU",
                    ActionType.BUY.value,
                    f"KMLM Switcher: XLK RSI {xlk_rsi:.1f} > KMLM RSI {kmlm_rsi:.1f} → FNGU",
                )
                self.log_klm_decision(result)
                return result

        # Step 2: Long/Short Rotator logic (when XLK <= KMLM or missing data)
        return self._evaluate_long_short_rotator(indicators)

    def _evaluate_long_short_rotator(
        self, indicators: dict[str, dict[str, float]]
    ) -> KLMDecision:
        """Long/Short Rotator - CORRECTED to match CLJ exactly.

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

            result = self.create_klm_decision(
                selected_symbol,
                ActionType.BUY.value,
                f"L/S Rotator: {selected_symbol} (lowest volatility: {selected_stdev:.3f})",
            )

        else:
            # Fallback - CLJ doesn't specify this, but we need something
            # Default to KMLM since it's the most defensive in the list
            result = self.create_klm_decision(
                "KMLM",
                ActionType.BUY.value,
                "L/S Rotator: KMLM fallback (missing volatility data)",
            )

        self.log_klm_decision(result)
        return result

    def get_required_symbols(self) -> list[str]:
        """506/38 Required symbols - CORRECTED to match CLJ exactly.

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
