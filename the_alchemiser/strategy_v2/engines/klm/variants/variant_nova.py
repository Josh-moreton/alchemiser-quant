"""Business Unit: strategy | Status: current

KLM Strategy Variant Nova - "Nerfed 2900/8 (373) - Nova - Short BT".

This variant is DIFFERENT from others in several key ways:
1. Uses UVIX instead of UVXY in Single Popped KMLM check
2. KMLM Switcher uses RSI(11) and select-top 1 from individual stocks
3. Individual stock selection: FNGO, TSLA, MSFT, AAPL, NVDA, GOOGL, AMZN
4. Optimized for short-term trading analysis

This is the "Nova" experimental variant with individual stock selection.
"""

from __future__ import annotations

import pandas as pd

from the_alchemiser.shared.utils.common import ActionType
from the_alchemiser.shared.value_objects.core_types import KLMDecision

from ..base_variant import BaseKLMVariant


class KLMVariantNova(BaseKLMVariant):
    """Variant Nova - Individual stock selection with UVIX check.

    Key differences:
    - Single Popped KMLM uses UVIX (not UVXY)
    - KMLM Switcher uses RSI(11) and select-top 1 from individual stocks
    - Stock selection: FNGO, TSLA, MSFT, AAPL, NVDA, GOOGL, AMZN
    """

    def __init__(self) -> None:
        super().__init__(
            name="Nova", description="Nerfed 2900/8 (373) - Nova - Short BT with individual stocks"
        )

    def evaluate(
        self,
        indicators: dict[str, dict[str, float]],
        market_data: dict[str, pd.DataFrame] | None = None,
    ) -> KLMDecision:
        """Evaluate Nova - same as others except UVIX check and individual stock selection."""
        # Step 1: Primary overbought checks → UVXY (same as others)
        overbought_result = self.check_primary_overbought_conditions(indicators)
        if overbought_result:
            self.log_klm_decision(overbought_result)
            return overbought_result

        # Step 2: Single Popped KMLM logic (DIFFERENT: uses UVIX)
        return self._evaluate_single_popped_kmlm_nova(indicators)

    def _evaluate_single_popped_kmlm_nova(
        self, indicators: dict[str, dict[str, float]]
    ) -> KLMDecision:
        """Nova Single Popped KMLM - DIFFERENT: uses UVIX instead of UVXY."""
        # Check UVIX RSI(21) for strategy branching (not UVXY!)
        if "UVIX" in indicators:
            uvix_rsi_21 = indicators["UVIX"]["rsi_21"]

            if uvix_rsi_21 > 65:
                # UVIX elevated - use BSC strategy
                return self.evaluate_bsc_strategy(indicators)
            # UVIX normal - use Combined Pop Bot
            return self.evaluate_combined_pop_bot(indicators)

        # Fallback if UVIX data unavailable
        return self.evaluate_combined_pop_bot(indicators)

    def evaluate_core_kmlm_switcher(self, indicators: dict[str, dict[str, float]]) -> KLMDecision:
        """Core KMLM switcher for variant Nova.

        COMPLETELY DIFFERENT: Individual stocks with RSI(11).
        CLJ shows: RSI(11) select-top 1 from FNGO/TSLA/MSFT/AAPL/NVDA/GOOGL/AMZN
        """
        if "XLK" in indicators and "KMLM" in indicators:
            xlk_rsi = indicators["XLK"]["rsi_10"]
            kmlm_rsi = indicators["KMLM"]["rsi_10"]

            if xlk_rsi > kmlm_rsi:
                # Individual stock selection with RSI(11) and select-top 1
                stock_symbols = ["FNGO", "TSLA", "MSFT", "AAPL", "NVDA", "GOOGL", "AMZN"]
                candidates = []

                for symbol in stock_symbols:
                    if symbol in indicators and "rsi_11" in indicators[symbol]:
                        rsi_11 = indicators[symbol]["rsi_11"]
                        candidates.append((symbol, rsi_11))

                if candidates:
                    # Select TOP 1 (highest RSI(11))
                    top_1 = self.apply_select_top_filter(candidates, 1)
                    selected_symbol = top_1[0][0]
                    selected_rsi = top_1[0][1]
                    result = self.create_klm_decision(
                        selected_symbol,
                        ActionType.BUY.value,
                        f"Nova KMLM Switcher: {selected_symbol} (highest RSI(11): {selected_rsi:.1f})",
                    )
                    self.log_klm_decision(result)
                    return result
                # Fallback to FNGO if no RSI(11) data
                result = self.create_klm_decision(
                    "FNGO", ActionType.BUY.value, "Nova KMLM Switcher: FNGO fallback"
                )
                self.log_klm_decision(result)
                return result

        # XLK <= KMLM → L/S Rotator (same as 520/22)
        return self._evaluate_ls_rotator_nova(indicators)

    def _evaluate_ls_rotator_nova(self, indicators: dict[str, dict[str, float]]) -> KLMDecision:
        """Nova L/S Rotator - same as 520/22 (FTLS/KMLM/SSO/UUP)."""
        # Volatility filter candidates: FTLS, KMLM, SSO, UUP
        rotator_symbols = ["FTLS", "KMLM", "SSO", "UUP"]

        candidates = []
        for symbol in rotator_symbols:
            if symbol in indicators and "stdev_return_6" in indicators[symbol]:
                stdev = indicators[symbol]["stdev_return_6"]
                candidates.append((symbol, stdev))

        if candidates:
            # Select bottom 1 (lowest volatility)
            bottom_1 = self.apply_select_bottom_filter(candidates, 1)
            selected_symbol = bottom_1[0][0]
            selected_stdev = bottom_1[0][1]
            result = self.create_klm_decision(
                selected_symbol,
                ActionType.BUY.value,
                f"Nova L/S Rotator: {selected_symbol} (lowest volatility: {selected_stdev:.3f})",
            )
        else:
            # Fallback to KMLM
            result = self.create_klm_decision(
                "KMLM", ActionType.BUY.value, "Nova L/S Rotator: KMLM fallback"
            )

        self.log_klm_decision(result)
        return result

    def get_required_symbols(self) -> list[str]:
        """Nova Required symbols - includes individual stocks and UVIX."""
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

        # Single Popped KMLM - UVIX instead of UVXY
        single_popped_symbols = ["UVIX"]

        # BSC strategy
        bsc_symbols = ["VIXM", "SPXL"]

        # Combined Pop Bot (no LABU)
        pop_bot_symbols = ["SOXL"]  # TQQQ, SPXL, TECL already included

        # KMLM Switcher - XLK/KMLM for comparison
        kmlm_switcher_symbols = ["XLK", "KMLM"]

        # Individual stocks for Nova selection
        individual_stocks = ["FNGO", "TSLA", "MSFT", "AAPL", "NVDA", "GOOGL", "AMZN"]

        # L/S Rotator - FTLS/KMLM/SSO/UUP
        rotator_symbols = ["FTLS", "SSO", "UUP"]  # KMLM already included

        return list(
            set(
                overbought_symbols
                + single_popped_symbols
                + bsc_symbols
                + pop_bot_symbols
                + kmlm_switcher_symbols
                + individual_stocks
                + rotator_symbols
            )
        )
