"""Business Unit: strategy | Status: current.

Original KLM strategy - exact match to CLJ implementation.
"""

from typing import Any

import pandas as pd

from the_alchemiser.shared.dto.technical_indicators_dto import TechnicalIndicatorDTO
from the_alchemiser.shared.utils.common import ActionType
from the_alchemiser.shared.value_objects.core_types import KLMDecision
from the_alchemiser.strategy_v2.engines.klm.base_variant import BaseKLMVariant


class KlmVariantOriginal(BaseKLMVariant):
    """Original KLM variant - exact match to 'Simons KMLM switcher (single pops)'.

    This is the EXACT implementation of the original CLJ strategy:
    - Simons KMLM switcher (single pops)| BT 4/13/22 = A.R. 466% / D.D. 22% V2
    - Specific RSI thresholds per symbol (not uniform)
    - Nested if-else structure preserved in logic flow
    - Original KMLM Switcher with select-bottom 2 and select-top 1
    """

    def __init__(self) -> None:
        """Initialize Original KLM variant."""
        super().__init__(
            name="Original_CLJ",
            description="Simons KMLM switcher (single pops) | BT 4/13/22 = A.R. 466% / D.D. 22% V2"
        )

    def get_overbought_config(self) -> dict[str, Any]:
        """Get overbought detection configuration with EXACT thresholds from CLJ.

        Note: Different thresholds for XLP (75), XLY (80), FAS (80), SPY (80).
        """
        return {
            "symbols": [
                ("QQQE", 79),
                ("VTV", 79),
                ("VOX", 79),
                ("TECL", 79),
                ("VOOG", 79),
                ("VOOV", 79),
                ("XLP", 75),  # Different threshold: 75 not 79
                ("TQQQ", 79),
                ("XLY", 80),  # Different threshold: 80 not 79
                ("FAS", 80),  # Different threshold: 80 not 79
                ("SPY", 80),  # Different threshold: 80 not 79
            ],
            "hedge_symbol": "UVXY",
            "rsi_window": 10,
        }

    def get_combined_pop_config(self) -> dict[str, Any]:
        """Get Combined Pop Bot configuration with EXACT thresholds from CLJ.

        Note: LABU has different threshold (25) vs others (30).
        """
        return {
            "pops": [
                {"symbol": "TQQQ", "target": "TECL", "threshold": 30},
                {"symbol": "SOXL", "target": "SOXL", "threshold": 30},
                {"symbol": "SPXL", "target": "SPXL", "threshold": 30},
                {
                    "symbol": "LABU",
                    "target": "LABU",
                    "threshold": 25,
                },  # Different threshold: 25 not 30
            ],
            "rsi_window": 10,
        }

    def get_kmlm_switcher_config(self) -> dict[str, Any]:
        """KMLM Switcher - exact CLJ implementation.

        When XLK RSI > KMLM RSI:
        - Select bottom 2 from [TECL, SOXL, SVIX]
        Otherwise (L/S Rotator):
        - Select top 1 from [SQQQ, TLT]
        """
        return {
            "compare_symbols": ("XLK", "KMLM"),
            "tech_symbols": ["TECL", "SOXL", "SVIX"],
            "ls_symbols": ["SQQQ", "TLT"],
            "rsi_window": 10,
            "selection": {
                "tech": ("bottom", 2),  # select-bottom 2
                "ls": ("top", 1),  # select-top 1
            },
        }

    def get_variant_name(self) -> str:
        """Return variant name."""
        return "Original_CLJ"

    def get_description(self) -> str:
        """Return variant description."""
        return (
            "Simons KMLM switcher (single pops) | BT 4/13/22 = A.R. 466% / D.D. 22% V2"
        )

    def has_single_popped_kmlm(self) -> bool:
        """Original strategy does NOT have Single Popped KMLM logic."""
        return False

    def has_bond_check(self) -> bool:
        """Original strategy does NOT have Bond Check logic."""
        return False

    def get_scale_in_config(self) -> dict[str, Any] | None:
        """Original strategy does NOT have scale-in logic."""
        return None

    def evaluate(
        self,
        indicators: dict[str, TechnicalIndicatorDTO],
        market_data: dict[str, pd.DataFrame] | None = None,
    ) -> KLMDecision:
        """Evaluate Original KLM strategy - EXACT match to CLJ specification.

        Implements the exact nested if-else structure from 'klm original.clj':
        1. UVXY guard-rail path (11-step overbought detection)
        2. Combined Pop Bot (oversold rotations including LABU)
        3. KMLM switcher (XLK vs KMLM comparison)

        Args:
            indicators: Dictionary of calculated technical indicators (RSI window=10)
            market_data: Raw market data (optional, not used in original CLJ)

        Returns:
            KLMDecision with exact asset selection and reasoning

        """
        # Step 1: UVXY Guard-rail Path (11-step overbought detection)
        # This matches the exact sequence from CLJ with proper thresholds
        overbought_result = self.check_primary_overbought_conditions(indicators)
        if overbought_result is not None:
            return overbought_result

        # Step 2: Combined Pop Bot (exact CLJ sequence including LABU)
        pop_bot_result = self._evaluate_original_combined_pop_bot(indicators)
        if pop_bot_result is not None:
            return pop_bot_result

        # Step 3: KMLM Switcher (XLK vs KMLM RSI comparison)
        return self._evaluate_original_kmlm_switcher(indicators)

    def _evaluate_original_combined_pop_bot(
        self, indicators: dict[str, TechnicalIndicatorDTO]
    ) -> KLMDecision | None:
        """Original Combined Pop Bot with EXACT CLJ sequence including LABU.

        CLJ sequence:
        1. TQQQ RSI(10) < 30 → TECL
        2. SOXL RSI(10) < 30 → SOXL
        3. SPXL RSI(10) < 30 → SPXL
        4. LABU RSI(10) < 25 → LABU (different threshold!)
        5. If none, proceed to KMLM switcher

        """
        # Priority 1: TQQQ oversold check
        if "TQQQ" in indicators:
            tqqq_rsi = indicators["TQQQ"].rsi_10 or 50
            if tqqq_rsi < 30:
                return self.create_klm_decision(
                    "TECL",
                    ActionType.BUY.value,
                    f"Pop Bot: TQQQ RSI(10) {tqqq_rsi:.1f} < 30 → TECL",
                )

        # Priority 2: SOXL oversold check
        if "SOXL" in indicators:
            soxl_rsi = indicators["SOXL"].rsi_10 or 50
            if soxl_rsi < 30:
                return self.create_klm_decision(
                    "SOXL",
                    ActionType.BUY.value,
                    f"Pop Bot: SOXL RSI(10) {soxl_rsi:.1f} < 30 → SOXL",
                )

        # Priority 3: SPXL oversold check
        if "SPXL" in indicators:
            spxl_rsi = indicators["SPXL"].rsi_10 or 50
            if spxl_rsi < 30:
                return self.create_klm_decision(
                    "SPXL",
                    ActionType.BUY.value,
                    f"Pop Bot: SPXL RSI(10) {spxl_rsi:.1f} < 30 → SPXL",
                )

        # Priority 4: LABU oversold check (ORIGINAL CLJ has threshold 25, not 30!)
        if "LABU" in indicators:
            labu_rsi = indicators["LABU"].rsi_10 or 50
            if labu_rsi < 25:
                return self.create_klm_decision(
                    "LABU",
                    ActionType.BUY.value,
                    f"Pop Bot: LABU RSI(10) {labu_rsi:.1f} < 25 → LABU",
                )

        # No oversold conditions met - proceed to KMLM switcher
        return None

    def _evaluate_original_kmlm_switcher(
        self, indicators: dict[str, TechnicalIndicatorDTO]
    ) -> KLMDecision:
        """Original KMLM Switcher - exact CLJ implementation.

        Logic from CLJ:
        - Compare RSI(XLK) vs RSI(KMLM) (both window 10)
        - If XLK RSI > KMLM RSI:
          - filter by RSI, select-bottom 2 from [TECL, SOXL, SVIX]
          - weight-equal across selected two
        - Else (L/S Rotator):
          - filter by RSI, select-top 1 from [SQQQ, TLT]
          - 100% weight to selected one

        """
        # Get RSI values for comparison
        xlk_rsi = indicators["XLK"].rsi_10 if "XLK" in indicators else 50
        kmlm_rsi = indicators["KMLM"].rsi_10 if "KMLM" in indicators else 50

        if xlk_rsi > kmlm_rsi:
            # Tech branch: select-bottom 2 from [TECL, SOXL, SVIX]
            tech_symbols = ["TECL", "SOXL", "SVIX"]
            selected_symbols = self._filter_and_select_by_rsi(
                tech_symbols, indicators, "bottom", 2
            )

            if selected_symbols:
                # weight-equal across selected symbols
                equal_weight = 1.0 / len(selected_symbols)
                allocation = dict.fromkeys(selected_symbols, equal_weight)
                reasoning = (
                    f"KMLM Switcher: XLK RSI({xlk_rsi:.1f}) > KMLM RSI({kmlm_rsi:.1f}) "
                    f"→ Tech branch, selected {selected_symbols}"
                )
                return self.create_klm_decision(allocation, ActionType.BUY.value, reasoning)
            # Fallback if no tech symbols available
            return self.create_klm_decision(
                "TECL",
                ActionType.BUY.value,
                f"KMLM Switcher: XLK RSI({xlk_rsi:.1f}) > KMLM RSI({kmlm_rsi:.1f}) → TECL (fallback)",
            )
        # L/S Rotator: select-top 1 from [SQQQ, TLT]
        ls_symbols = ["SQQQ", "TLT"]
        selected_symbols = self._filter_and_select_by_rsi(
            ls_symbols, indicators, "top", 1
        )

        if selected_symbols:
            # 100% weight to selected symbol
            selected_symbol = selected_symbols[0]
            reasoning = (
                f"KMLM Switcher: XLK RSI({xlk_rsi:.1f}) ≤ KMLM RSI({kmlm_rsi:.1f}) "
                f"→ L/S Rotator, selected {selected_symbol}"
            )
            return self.create_klm_decision(selected_symbol, ActionType.BUY.value, reasoning)
        # Fallback if no L/S symbols available
        return self.create_klm_decision(
            "TLT",
            ActionType.BUY.value,
            f"KMLM Switcher: XLK RSI({xlk_rsi:.1f}) ≤ KMLM RSI({kmlm_rsi:.1f}) → TLT (fallback)",
        )

    def _filter_and_select_by_rsi(
        self,
        candidates: list[str],
        indicators: dict[str, TechnicalIndicatorDTO],
        selection_type: str,
        count: int,
    ) -> list[str]:
        """Filter candidates by RSI and select top/bottom N.

        Implements the exact filter/select logic from CLJ:
        - filter by RSI (window 10) - only include symbols with valid RSI
        - select-bottom N or select-top N based on RSI values
        - Deterministic tie-breaking using symbol name (alphabetical)

        Args:
            candidates: List of symbol strings to consider
            indicators: Dictionary of technical indicators
            selection_type: "top" or "bottom"
            count: Number of symbols to select

        Returns:
            List of selected symbols (up to count)

        """
        # Filter to only symbols with valid RSI data
        valid_candidates = []
        for symbol in candidates:
            if symbol in indicators:
                rsi_value = indicators[symbol].rsi_10
                if rsi_value is not None and 0 <= rsi_value <= 100:
                    valid_candidates.append((symbol, rsi_value))

        if not valid_candidates:
            return []

        # Sort by RSI value, then by symbol name for deterministic tie-breaking
        if selection_type == "bottom":
            # Sort ascending (lowest RSI first), then alphabetically
            sorted_candidates = sorted(valid_candidates, key=lambda x: (x[1], x[0]))
        else:  # "top"
            # Sort descending (highest RSI first), then alphabetically
            sorted_candidates = sorted(valid_candidates, key=lambda x: (-x[1], x[0]))

        # Select top N
        selected = sorted_candidates[:count]
        return [symbol for symbol, _ in selected]

    def evaluate_core_kmlm_switcher(
        self, indicators: dict[str, TechnicalIndicatorDTO]
    ) -> KLMDecision:
        """Core KMLM switcher implementation for base class compatibility."""
        return self._evaluate_original_kmlm_switcher(indicators)
