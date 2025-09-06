"""Business Unit: utilities; Status: current.

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
    ) -> tuple[str | dict[str, float], str, str]:
        """Evaluate Nova - same as others except UVIX check and individual stock selection."""
        # Step 1: Primary overbought checks → UVXY (same as others)
        symbol, reason = self.check_primary_overbought_conditions(indicators)
        if symbol:
            self.log_decision(symbol, ActionType.BUY.value, reason)
            return symbol, ActionType.BUY.value, reason

        # Step 2: Single Popped KMLM logic (DIFFERENT: uses UVIX)
        return self._evaluate_single_popped_kmlm_nova(indicators)

    def _evaluate_single_popped_kmlm_nova(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[str | dict[str, float], str, str]:
        """Nova Single Popped KMLM - DIFFERENT: uses UVIX instead of UVXY."""
        # Check UVIX RSI(21) for strategy branching (not UVXY!)
        if "UVIX" in indicators:
            uvix_rsi_21 = indicators["UVIX"]["rsi_21"]

            if uvix_rsi_21 > 65:
                # UVIX elevated - use BSC strategy
                return self._evaluate_bsc_strategy(indicators)
            # UVIX normal - use Combined Pop Bot
            return self._evaluate_combined_pop_bot(indicators)

        # Fallback if UVIX data unavailable
        return self._evaluate_combined_pop_bot(indicators)

    def _evaluate_bsc_strategy(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[str, str, str]:
        """BSC strategy - identical to other variants."""
        if "SPY" in indicators:
            spy_rsi_21 = indicators["SPY"]["rsi_21"]

            if spy_rsi_21 > 30:
                result = ("VIXM", ActionType.BUY.value, "Nova BSC: SPY RSI(21) > 30 → VIXM")
            else:
                result = (
                    "SPXL",
                    ActionType.BUY.value,
                    "Nova BSC: SPY oversold (RSI(21) <= 30) → SPXL",
                )
        else:
            result = ("VIXM", ActionType.BUY.value, "Nova BSC: Default VIX position")

        self.log_decision(result[0], result[1], result[2])
        return result

    def _evaluate_combined_pop_bot(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[str | dict[str, float], str, str]:
        """Combined Pop Bot - identical to others (NO LABU)."""
        # Priority 1: TQQQ oversold
        if "TQQQ" in indicators and indicators["TQQQ"]["rsi_10"] < 30:
            result = ("TECL", ActionType.BUY.value, "Nova Pop Bot: TQQQ RSI < 30 → TECL")
            self.log_decision(result[0], result[1], result[2])
            return result

        # Priority 2: SOXL oversold
        if "SOXL" in indicators and indicators["SOXL"]["rsi_10"] < 30:
            result = ("SOXL", ActionType.BUY.value, "Nova Pop Bot: SOXL RSI < 30 → SOXL")
            self.log_decision(result[0], result[1], result[2])
            return result

        # Priority 3: SPXL oversold
        if "SPXL" in indicators and indicators["SPXL"]["rsi_10"] < 30:
            result = ("SPXL", ActionType.BUY.value, "Nova Pop Bot: SPXL RSI < 30 → SPXL")
            self.log_decision(result[0], result[1], result[2])
            return result

        # No oversold conditions - proceed to KMLM Switcher
        return self.evaluate_core_kmlm_switcher(indicators)

    def evaluate_core_kmlm_switcher(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[str | dict[str, float], str, str]:
        """Core KMLM switcher for variant Nova."""
        return self._evaluate_kmlm_switcher_nova(indicators)

    def _evaluate_kmlm_switcher_nova(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[str | dict[str, float], str, str]:
        """Nova KMLM Switcher - COMPLETELY DIFFERENT: Individual stocks with RSI(11).

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
                    candidates.sort(key=lambda x: x[1], reverse=True)
                    selected = candidates[0]
                    result = (
                        selected[0],
                        ActionType.BUY.value,
                        f"Nova KMLM Switcher: XLK > KMLM → {selected[0]} (highest RSI(11): {selected[1]:.1f})",
                    )
                else:
                    # Fallback to FNGO if no RSI(11) data
                    result = ("FNGO", ActionType.BUY.value, "Nova KMLM Switcher: FNGO fallback")

                self.log_decision(result[0], result[1], result[2])
                return result

        # XLK <= KMLM → L/S Rotator (same as 520/22)
        return self._evaluate_ls_rotator_nova(indicators)

    def _evaluate_ls_rotator_nova(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[str, str, str]:
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
            candidates.sort(key=lambda x: x[1])
            selected = candidates[0]
            result = (
                selected[0],
                ActionType.BUY.value,
                f"Nova L/S Rotator: {selected[0]} (lowest volatility: {selected[1]:.3f})",
            )
        else:
            # Fallback to KMLM
            result = ("KMLM", ActionType.BUY.value, "Nova L/S Rotator: KMLM fallback")

        self.log_decision(result[0], result[1], result[2])
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
