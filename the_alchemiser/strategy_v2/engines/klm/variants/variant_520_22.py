"""Business Unit: strategy | Status: current

KLM Strategy Variant 520/22 - "KMLM (23) - Original".

This variant is similar to 506/38 and 1200/28 except:
- KMLM Switcher uses select-bottom 1 from TECL/SVIX only (no SOXL, no FNGU)
- L/S Rotator uses FTLS/KMLM/SSO/UUP (not SQQQ/TLT like others)
- Everything else is the same: Single Popped KMLM, BSC, Combined Pop Bot (no LABU)

This is the "Original" baseline implementation.
"""

from __future__ import annotations

import pandas as pd

from the_alchemiser.shared.utils.common import ActionType
from the_alchemiser.shared.value_objects.core_types import KLMDecision

from ..base_variant import BaseKLMVariant


class KlmVariant52022(BaseKLMVariant):
    """Variant 520/22 - "Original" with TECL/SVIX switcher and FTLS/KMLM/SSO/UUP rotator.

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
    ) -> KLMDecision:
        """Evaluate 520/22 - same as 506/38 except KMLM Switcher and L/S Rotator."""
        # Step 1: Primary overbought checks → UVXY
        overbought_result = self.check_primary_overbought_conditions(indicators)
        if overbought_result:
            self.log_klm_decision(overbought_result)
            return overbought_result

        # Step 2: Single Popped KMLM logic (same as 506/38)
        return self.evaluate_single_popped_kmlm(indicators)

    def evaluate_core_kmlm_switcher(self, indicators: dict[str, dict[str, float]]) -> KLMDecision:
        """Core KMLM switcher for variant 520/22.

        KEY DIFFERENCE: TECL/SVIX only (no SOXL).
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
                    selected_symbol = candidates[0][0]
                    selected_rsi = candidates[0][1]
                    result = self.create_klm_decision(
                        selected_symbol,
                        ActionType.BUY.value,
                        f"520/22 KMLM Switcher: {selected_symbol} (lowest RSI: {selected_rsi:.1f})",
                    )
                    self.log_klm_decision(result)
                    return result

        # Fallback to L/S Rotator if XLK <= KMLM or missing data
        return self._evaluate_long_short_rotator(indicators)

    def _evaluate_long_short_rotator(self, indicators: dict[str, dict[str, float]]) -> KLMDecision:
        """520/22 L/S Rotator - uses FTLS/KMLM/SSO/UUP (like 410/38)."""
        rotator_symbols = ["FTLS", "KMLM", "SSO", "UUP"]

        # Apply volatility filter (stdev-return window 6)
        volatility_candidates = []
        for symbol in rotator_symbols:
            if symbol in indicators and "stdev_return_6" in indicators[symbol]:
                stdev = indicators[symbol]["stdev_return_6"]
                volatility_candidates.append((symbol, stdev))

        if volatility_candidates:
            # Select bottom 1 by volatility (lowest standard deviation)
            bottom_1 = self.apply_select_bottom_filter(volatility_candidates, 1)
            selected_symbol = bottom_1[0][0]
            selected_stdev = bottom_1[0][1]

            result = self.create_klm_decision(
                selected_symbol,
                ActionType.BUY.value,
                f"520/22 L/S Rotator: {selected_symbol} (lowest volatility: {selected_stdev:.3f})",
            )
        else:
            # Fallback to KMLM
            result = self.create_klm_decision(
                "KMLM", ActionType.BUY.value, "520/22 L/S Rotator: KMLM fallback"
            )

        self.log_klm_decision(result)
        return result

    def get_required_symbols(self) -> list[str]:
        """520/22 Required symbols - "Original" baseline."""
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
