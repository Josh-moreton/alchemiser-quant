"""Business Unit: utilities; Status: current.

KLM Strategy Variant 1280/26 - "KMLM (50)".

COMPLETELY DIFFERENT from 506/38! This variant:
1. Uses standard overbought detection → UVXY
2. Goes directly to Combined Pop Bot (NO Single Popped KMLM logic)
3. Combined Pop Bot includes LABU with RSI < 25 threshold
4. KMLM Switcher uses select-bottom 2 from TECL/SOXL/SVIX (NOT FNGU)
5. L/S Rotator uses SQQQ/TLT with select-top 1 (NOT UUP/FTLS/KMLM)

This is a fundamentally different architecture from other variants.
"""

import pandas as pd

from the_alchemiser.domain.types import KLMDecision  # TODO: Phase 9 - Added for gradual migration
from the_alchemiser.utils.common import ActionType

from .base_klm_variant import BaseKLMVariant


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
    ) -> (
        tuple[str | dict[str, float], str, str] | KLMDecision
    ):  # TODO: Phase 9 - Gradual migration to KLMDecision
        """Evaluate 1280/26 - completely different flow from 506/38.

        Flow: Overbought Detection → Combined Pop Bot → KMLM Switcher
        (NO Single Popped KMLM logic)
        """
        # Step 1: Standard overbought checks → UVXY
        symbol, reason = self.check_primary_overbought_conditions(indicators)
        if symbol:
            self.log_decision(symbol, ActionType.BUY.value, reason)
            return symbol, ActionType.BUY.value, reason

        # Step 2: Combined Pop Bot (includes LABU!)
        return self._evaluate_combined_pop_bot_with_labu(indicators)

    def _evaluate_combined_pop_bot_with_labu(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[str | dict[str, float], str, str]:
        """Combined Pop Bot for 1280/26 - includes LABU with RSI < 25.

        Order: TQQQ < 30 → SOXL < 30 → SPXL < 30 → LABU < 25 → KMLM Switcher
        """
        # Priority 1: TQQQ oversold
        if "TQQQ" in indicators and indicators["TQQQ"]["rsi_10"] < 30:
            result = ("TECL", ActionType.BUY.value, "1280/26 Pop Bot: TQQQ RSI < 30 → TECL")
            self.log_decision(result[0], result[1], result[2])
            return result

        # Priority 2: SOXL oversold
        if "SOXL" in indicators and indicators["SOXL"]["rsi_10"] < 30:
            result = ("SOXL", ActionType.BUY.value, "1280/26 Pop Bot: SOXL RSI < 30 → SOXL")
            self.log_decision(result[0], result[1], result[2])
            return result

        # Priority 3: SPXL oversold
        if "SPXL" in indicators and indicators["SPXL"]["rsi_10"] < 30:
            result = ("SPXL", ActionType.BUY.value, "1280/26 Pop Bot: SPXL RSI < 30 → SPXL")
            self.log_decision(result[0], result[1], result[2])
            return result

        # Priority 4: LABU oversold (KEY DIFFERENCE - this variant includes LABU)
        if "LABU" in indicators and indicators["LABU"]["rsi_10"] < 25:
            result = ("LABU", ActionType.BUY.value, "1280/26 Pop Bot: LABU RSI < 25 → LABU")
            self.log_decision(result[0], result[1], result[2])
            return result

        # No oversold conditions - proceed to KMLM Switcher
        return self.evaluate_core_kmlm_switcher(indicators)

    def evaluate_core_kmlm_switcher(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[str | dict[str, float], str, str]:
        """Core KMLM switcher for variant 1280/26."""
        return self._evaluate_kmlm_switcher_1280(indicators)

    def _evaluate_kmlm_switcher_1280(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[str | dict[str, float], str, str]:
        """1280/26 KMLM Switcher - select-bottom 2 from TECL/SOXL/SVIX (NOT FNGU).

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
                    # Select bottom 2 (lowest RSI)
                    candidates.sort(key=lambda x: x[1])
                    bottom_2 = candidates[:2]
                    allocation = {symbol: 0.5 for symbol, _ in bottom_2}
                    symbols = [s[0] for s in bottom_2]
                    result = (
                        allocation,
                        ActionType.BUY.value,
                        f"1280/26 KMLM Switcher: XLK > KMLM → Bottom 2: {symbols}",
                    )
                elif candidates:
                    # Only 1 available
                    result = (  # TODO: Phase 9 - Remove type ignore after converting to KLMDecision
                        candidates[0][0],
                        ActionType.BUY.value,
                        f"1280/26 KMLM Switcher: XLK > KMLM → {candidates[0][0]} (only option)",
                    )  # type: ignore[assignment]
                else:
                    # Fallback
                    result = (  # TODO: Phase 9 - Remove type ignore after converting to KLMDecision
                        "TECL",
                        ActionType.BUY.value,
                        "1280/26 KMLM Switcher: XLK > KMLM → TECL fallback",
                    )  # type: ignore[assignment]

                self.log_decision(result[0], result[1], result[2])
                return result

        # XLK <= KMLM or missing data → L/S Rotator
        return self._evaluate_ls_rotator_1280(indicators)

    def _evaluate_ls_rotator_1280(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[str, str, str]:
        """1280/26 L/S Rotator - COMPLETELY different from other variants.

        CLJ shows: select-top 1 from SQQQ, TLT (not volatility filtering!)
        This selects the HIGHEST RSI (most overbought for contrarian play)
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
                f"1280/26 L/S Rotator: {top_candidate[0]} (highest RSI: {top_candidate[1]:.1f})",
            )
        else:
            # Fallback
            result = ("BIL", ActionType.BUY.value, "1280/26 L/S Rotator: BIL fallback")

        self.log_decision(result[0], result[1], result[2])
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
