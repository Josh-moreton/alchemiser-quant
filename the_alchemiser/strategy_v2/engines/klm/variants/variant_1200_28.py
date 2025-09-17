"""Business Unit: strategy | Status: current.

KLM Strategy Variant 1200/28 - "KMLM (43)".

This variant is nearly IDENTICAL to 506/38 except:
- KMLM Switcher uses select-bottom 1 from TECL/SOXL/SVIX (instead of FNGU)
- Everything else is the same: Single Popped KMLM, BSC, Combined Pop Bot (no LABU)

Pattern: QQQE → VTV → VOX → TECL → VOOG → VOOV → XLP → TQQQ → XLY → FAS → SPY →
         Single Popped KMLM (UVXY RSI check → BSC or Pop Bot → KMLM Switcher)
"""

from __future__ import annotations

import pandas as pd

from the_alchemiser.shared.dto.technical_indicators_dto import TechnicalIndicatorDTO
from the_alchemiser.shared.utils.common import ActionType
from the_alchemiser.shared.value_objects.core_types import KLMDecision

from ..base_variant import BaseKLMVariant


class KlmVariant120028(BaseKLMVariant):
    """Variant 1200/28 - Same as 506/38 except KMLM Switcher logic.

    Key difference: KMLM Switcher uses select-bottom 1 from TECL/SOXL/SVIX (not FNGU)
    """

    def __init__(self) -> None:
        """Initialize 1200/28 variant with name and description."""
        super().__init__(
            name="1200/28",
            description="KMLM (43) - Standard pattern with TECL/SOXL/SVIX switcher",
        )

    def evaluate(
        self,
        indicators: dict[str, TechnicalIndicatorDTO],
        market_data: dict[str, pd.DataFrame] | None = None,
    ) -> KLMDecision:
        """Evaluate 1200/28 - same as 506/38 except KMLM Switcher."""
        # Step 1: Primary overbought checks → UVXY
        overbought_result = self.check_primary_overbought_conditions(indicators)
        if overbought_result:
            self.log_klm_decision(overbought_result)
            return overbought_result

        # Step 2: Single Popped KMLM logic (same as 506/38)
        return self.evaluate_single_popped_kmlm(indicators)

    def evaluate_core_kmlm_switcher(
        self, indicators: dict[str, TechnicalIndicatorDTO]
    ) -> KLMDecision:
        """Core KMLM switcher for variant 1200/28.

        KEY DIFFERENCE from 506/38: Uses select-bottom 1 from TECL/SOXL/SVIX (not FNGU)
        """
        if "XLK" in indicators and "KMLM" in indicators:
            xlk_rsi = indicators["XLK"].rsi_10 or 50
            kmlm_rsi = indicators["KMLM"].rsi_10 or 50

            if xlk_rsi > kmlm_rsi:
                # select-bottom 1 from TECL, SOXL, SVIX
                candidates = []
                for symbol in ["TECL", "SOXL", "SVIX"]:
                    if symbol in indicators:
                        rsi = indicators[symbol].rsi_10 or 50
                        candidates.append((symbol, rsi))

                if candidates:
                    # Select bottom 1 (lowest RSI)
                    bottom_1 = self.apply_select_bottom_filter(candidates, 1)
                    selected_symbol = bottom_1[0][0]
                    selected_rsi = bottom_1[0][1]
                    result = self.create_klm_decision(
                        selected_symbol,
                        ActionType.BUY.value,
                        f"1200/28 KMLM Switcher: {selected_symbol} (lowest RSI: {selected_rsi:.1f})",
                    )
                    self.log_klm_decision(result)
                    return result

        # XLK <= KMLM → L/S Rotator
        return self._evaluate_ls_rotator_1200(indicators)

    def _evaluate_ls_rotator_1200(
        self, indicators: dict[str, dict[str, float]]
    ) -> KLMDecision:
        """1200/28 L/S Rotator - uses SQQQ/TLT select-top 1."""
        candidates = []
        for symbol in ["SQQQ", "TLT"]:
            if symbol in indicators:
                rsi = indicators[symbol].rsi_10 or 50
                candidates.append((symbol, rsi))

        if candidates:
            # Select top 1 (highest RSI) - contrarian strategy
            top_1 = self.apply_select_top_filter(candidates, 1)
            selected_symbol = top_1[0][0]
            selected_rsi = top_1[0][1]
            result = self.create_klm_decision(
                selected_symbol,
                ActionType.BUY.value,
                f"1200/28 L/S Rotator: {selected_symbol} (highest RSI: {selected_rsi:.1f})",
            )
        else:
            # Fallback
            result = self.create_klm_decision(
                "TLT", ActionType.BUY.value, "1200/28 L/S Rotator: TLT fallback"
            )

        self.log_klm_decision(result)
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
