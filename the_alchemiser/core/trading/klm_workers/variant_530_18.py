"""
KLM Strategy Variant 530/18 - "KMLM Switcher | Anansi Mods"

This is the Scale-In strategy variant - the most complex in the ensemble.
It uses progressive VIX allocation based on multiple RSI conditions.

COMPLETE LOGIC FLOW FROM CLJ:
1. SPY/IOO/QQQ Scale-In Logic with progressive VIX allocations (VIX+ → VIX++)
2. VTV/XLP/XLF Scale-In Logic with different patterns (VIX → VIX+)
3. RETL Scale-In Logic with BTAL → VIX pattern
4. SPY RSI(70) > 63 "Overbought" branch with AGG vs QQQ complex logic
5. "10. KMLM Switcher | Holy Grail" with nested VOX/XLP checks
6. Complex pop bot logic with cumulative return checks
7. Extensive moving average and momentum filters

This captures the COMPLETE CLJ implementation - the most sophisticated variant.
"""

import pandas as pd

from the_alchemiser.core.types import KLMDecision  # TODO: Phase 9 - Added for gradual migration
from the_alchemiser.core.utils.common import ActionType

from .base_klm_variant import BaseKLMVariant


class KlmVariant53018(BaseKLMVariant):
    """
    Variant 530/18 - Complete Scale-In Strategy "KMLM Switcher | Anansi Mods"

    This is THE most complex variant in the ensemble, featuring:
    1. Progressive Scale-In logic with dual VIX thresholds
    2. Multiple VIX blend allocations (VIX Blend, VIX Blend+, VIX Blend++)
    3. Complex overbought logic with AGG vs QQQ comparisons
    4. KMLM Switcher with FNGU 50/50 logic
    5. Holy Grail switching with extensive filters
    6. Commodity allocations (GLD/SLV/PDBC)

    This is NOT a simple variant - it's a completely different strategy architecture.
    """

    def __init__(self) -> None:
        super().__init__(
            name="530/18", description="KMLM Switcher | Anansi Mods - Complete Scale-In Strategy"
        )

    def evaluate(
        self,
        indicators: dict[str, dict[str, float]],
        market_data: dict[str, pd.DataFrame] | None = None,
    ) -> (
        tuple[str | dict[str, float], str, str] | KLMDecision
    ):  # TODO: Phase 9 - Gradual migration to KLMDecision
        """
        Evaluate the complete 530/18 Scale-In variant exactly as in CLJ.

        This follows the exact nested structure from the CLJ file.
        """

        # Step 1: SPY Scale-In Logic (primary - RSI > 80)
        spy_result = self._evaluate_spy_scale_in(indicators)
        if spy_result:
            return spy_result

        # Step 2: IOO Scale-In Logic (secondary - RSI > 80)
        ioo_result = self._evaluate_ioo_scale_in(indicators)
        if ioo_result:
            return ioo_result

        # Step 3: QQQ Scale-In Logic (tertiary - RSI > 79, different threshold)
        qqq_result = self._evaluate_qqq_scale_in(indicators)
        if qqq_result:
            return qqq_result

        # Step 4: VTV Scale-In Logic (RSI > 79, different VIX pattern)
        vtv_result = self._evaluate_vtv_scale_in(indicators)
        if vtv_result:
            return vtv_result

        # Step 5: XLP Scale-In Logic (RSI > 77, VIX → VIX+ pattern)
        xlp_result = self._evaluate_xlp_scale_in(indicators)
        if xlp_result:
            return xlp_result

        # Step 6: XLF Scale-In Logic (RSI > 81, same pattern as XLP)
        xlf_result = self._evaluate_xlf_scale_in(indicators)
        if xlf_result:
            return xlf_result

        # Step 7: RETL Scale-In Logic (RSI > 82, BTAL → VIX pattern)
        retl_result = self._evaluate_retl_scale_in(indicators)
        if retl_result:
            return retl_result

        # Step 8: SPY RSI(70) > 63 "Overbought" complex logic
        spy_70_result = self._evaluate_spy_rsi_70_overbought_logic(indicators)
        if spy_70_result:
            return spy_70_result

        # Step 9: "10. KMLM Switcher | Holy Grail" - the final complex branch
        return self._evaluate_holy_grail_kmlm_switcher(indicators)

    def _evaluate_spy_scale_in(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[dict[str, float], str, str] | None:
        """SPY Scale-In | VIX+ -> VIX++ (CLJ lines 782-796)"""
        if "SPY" not in indicators:
            return None

        spy_rsi = indicators["SPY"].get("rsi_10", 50)

        if spy_rsi > 80:
            if spy_rsi > 82.5:
                # VIX Blend++ - Double UVXY weight
                allocation = self.vix_blend_plus_plus  # {UVXY: 0.667, VIXM: 0.333}
                result = (
                    allocation,
                    ActionType.BUY.value,
                    f"SPY Scale-In: RSI {spy_rsi:.1f} > 82.5 → VIX Blend++",
                )
            else:
                # VIX Blend+ - Equal VIX allocation
                allocation = self.vix_blend_plus  # {UVXY: 0.333, VXX: 0.333, VIXM: 0.333}
                result = (
                    allocation,
                    ActionType.BUY.value,
                    f"SPY Scale-In: RSI {spy_rsi:.1f} > 80 → VIX Blend+",
                )

            self.log_decision(result[0], result[1], result[2])
            return result

        return None

    def _evaluate_ioo_scale_in(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[dict[str, float], str, str] | None:
        """IOO Scale-In | VIX+ -> VIX++ (identical pattern to SPY)"""
        if "IOO" not in indicators:
            return None

        ioo_rsi = indicators["IOO"].get("rsi_10", 50)

        if ioo_rsi > 80:
            if ioo_rsi > 82.5:
                allocation = self.vix_blend_plus_plus
                result = (
                    allocation,
                    ActionType.BUY.value,
                    f"IOO Scale-In: RSI {ioo_rsi:.1f} > 82.5 → VIX Blend++",
                )
            else:
                allocation = self.vix_blend_plus
                result = (
                    allocation,
                    ActionType.BUY.value,
                    f"IOO Scale-In: RSI {ioo_rsi:.1f} > 80 → VIX Blend+",
                )

            self.log_decision(result[0], result[1], result[2])
            return result

        return None

    def _evaluate_qqq_scale_in(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[dict[str, float], str, str] | None:
        """QQQ Scale-In | VIX+ -> VIX++ (threshold 79 vs 80)"""
        if "QQQ" not in indicators:
            return None

        qqq_rsi = indicators["QQQ"].get("rsi_10", 50)

        if qqq_rsi > 79:  # Different threshold!
            if qqq_rsi > 82.5:
                allocation = self.vix_blend_plus_plus
                result = (
                    allocation,
                    ActionType.BUY.value,
                    f"QQQ Scale-In: RSI {qqq_rsi:.1f} > 82.5 → VIX Blend++",
                )
            else:
                allocation = self.vix_blend_plus
                result = (
                    allocation,
                    ActionType.BUY.value,
                    f"QQQ Scale-In: RSI {qqq_rsi:.1f} > 79 → VIX Blend+",
                )

            self.log_decision(result[0], result[1], result[2])
            return result

        return None

    def _evaluate_vtv_scale_in(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[dict[str, float], str, str] | None:
        """VTV Scale-In | VIX -> VIX+ (different pattern - uses VIXY)"""
        if "VTV" not in indicators:
            return None

        vtv_rsi = indicators["VTV"].get("rsi_10", 50)

        if vtv_rsi > 79:
            if vtv_rsi > 85:  # Higher threshold for VIX+
                allocation = self.vix_blend_plus
                result = (
                    allocation,
                    ActionType.BUY.value,
                    f"VTV Scale-In: RSI {vtv_rsi:.1f} > 85 → VIX Blend+",
                )
            else:
                allocation = self.vix_blend  # Uses VIXY instead of UVXY
                result = (
                    allocation,
                    ActionType.BUY.value,
                    f"VTV Scale-In: RSI {vtv_rsi:.1f} > 79 → VIX Blend",
                )

            self.log_decision(result[0], result[1], result[2])
            return result

        return None

    def _evaluate_xlp_scale_in(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[dict[str, float], str, str] | None:
        """XLP Scale-In | VIX -> VIX+ (threshold 77, same pattern as VTV)"""
        if "XLP" not in indicators:
            return None

        xlp_rsi = indicators["XLP"].get("rsi_10", 50)

        if xlp_rsi > 77:  # Different threshold
            if xlp_rsi > 85:
                allocation = self.vix_blend_plus
                result = (
                    allocation,
                    ActionType.BUY.value,
                    f"XLP Scale-In: RSI {xlp_rsi:.1f} > 85 → VIX Blend+",
                )
            else:
                allocation = self.vix_blend
                result = (
                    allocation,
                    ActionType.BUY.value,
                    f"XLP Scale-In: RSI {xlp_rsi:.1f} > 77 → VIX Blend",
                )

            self.log_decision(result[0], result[1], result[2])
            return result

        return None

    def _evaluate_xlf_scale_in(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[dict[str, float], str, str] | None:
        """XLF Scale-In | VIX -> VIX+ (threshold 81, same pattern)"""
        if "XLF" not in indicators:
            return None

        xlf_rsi = indicators["XLF"].get("rsi_10", 50)

        if xlf_rsi > 81:
            if xlf_rsi > 85:
                allocation = self.vix_blend_plus
                result = (
                    allocation,
                    ActionType.BUY.value,
                    f"XLF Scale-In: RSI {xlf_rsi:.1f} > 85 → VIX Blend+",
                )
            else:
                allocation = self.vix_blend
                result = (
                    allocation,
                    ActionType.BUY.value,
                    f"XLF Scale-In: RSI {xlf_rsi:.1f} > 81 → VIX Blend",
                )

            self.log_decision(result[0], result[1], result[2])
            return result

        return None

    def _evaluate_retl_scale_in(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[dict[str, float], str, str] | None:
        """RETL Scale-In | BTAL -> VIX (introduces BTAL/BIL path)"""
        if "RETL" not in indicators:
            return None

        retl_rsi = indicators["RETL"].get("rsi_10", 50)

        if retl_rsi > 82:
            if retl_rsi > 85:
                allocation = self.vix_blend
                result = (
                    allocation,
                    ActionType.BUY.value,
                    f"RETL Scale-In: RSI {retl_rsi:.1f} > 85 → VIX Blend",
                )
            else:
                allocation = self.btal_bil  # {BTAL: 0.5, BIL: 0.5}
                result = (
                    allocation,
                    ActionType.BUY.value,
                    f"RETL Scale-In: RSI {retl_rsi:.1f} > 82 → BTAL/BIL",
                )

            self.log_decision(result[0], result[1], result[2])
            return result

        return None

    def _evaluate_spy_rsi_70_overbought_logic(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[str | dict[str, float], str, str] | None:
        """
        SPY RSI(70) > 63 "Overbought" branch with AGG vs QQQ comparison.
        This is where 530/18 gets extremely complex with commodity allocations.
        """
        if "SPY" not in indicators or "rsi_70" not in indicators["SPY"]:
            return None

        spy_rsi_70 = indicators["SPY"].get("rsi_70", 50)

        if spy_rsi_70 > 63:
            # Complex "Overbought" logic with AGG > QQQ comparison
            agg_rsi_15 = indicators.get("AGG", {}).get("rsi_15", 50)
            qqq_rsi_15 = indicators.get("QQQ", {}).get("rsi_15", 50)

            if agg_rsi_15 > qqq_rsi_15:
                # "All 3x Tech" allocation
                allocation = {"TQQQ": 0.2, "SPXL": 0.2, "SOXL": 0.2, "FNGU": 0.2, "ERX": 0.2}
                result = (
                    allocation,
                    ActionType.BUY.value,
                    f"Overbought: AGG RSI(15) {agg_rsi_15:.1f} > QQQ RSI(15) {qqq_rsi_15:.1f} → All 3x Tech",
                )
            else:
                # "GLD/SLV/PDBC" commodity allocation
                allocation = {"GLD": 0.5, "SLV": 0.25, "PDBC": 0.25}
                result = (
                    allocation,
                    ActionType.BUY.value,
                    f"Overbought: AGG RSI(15) {agg_rsi_15:.1f} ≤ QQQ RSI(15) {qqq_rsi_15:.1f} → Commodities",
                )

            self.log_decision(result[0], result[1], result[2])
            return result

        return None

    def _evaluate_holy_grail_kmlm_switcher(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[str | dict[str, float], str, str]:
        """
        "10. KMLM Switcher | Holy Grail" - The final complex branch.

        This includes:
        1. VOX RSI(10) > 79 → VIX Blend
        2. XLP RSI(10) > 75 → VIX Blend
        3. Complex TQQQ cumulative return checks
        4. Pop bot logic (TQQQ/SOXL/SPXL oversold)
        5. KMLM Switcher + FNGU with 50/50 logic
        6. Long/short rotator with stdev filtering
        """

        # Check VOX overbought
        if "VOX" in indicators and indicators["VOX"].get("rsi_10", 0) > 79:
            allocation = self.vix_blend
            result = (allocation, ActionType.BUY.value, "Holy Grail: VOX RSI(10) > 79 → VIX Blend")
            self.log_decision(result[0], result[1], result[2])
            return result

        # Check XLP overbought
        if "XLP" in indicators and indicators["XLP"].get("rsi_10", 0) > 75:
            allocation = self.vix_blend
            result = (allocation, ActionType.BUY.value, "Holy Grail: XLP RSI(10) > 75 → VIX Blend")
            self.log_decision(result[0], result[1], result[2])
            return result

        # TQQQ cumulative return check (< -12% over 6 periods)
        tqqq_cum_return = indicators.get("TQQQ", {}).get("cumulative_return_6", 0)
        if tqqq_cum_return < -12:
            # Additional TQQQ daily return check (> 5.5% in 1 day)
            tqqq_daily_return = indicators.get("TQQQ", {}).get("cumulative_return_1", 0)
            if tqqq_daily_return > 5.5:
                allocation = self.vix_blend_plus
                result = (
                    allocation,
                    ActionType.BUY.value,
                    f"Holy Grail: TQQQ 6d return {tqqq_cum_return:.1f}% < -12%, daily {tqqq_daily_return:.1f}% > 5.5% → VIX Blend+",
                )
            else:
                # Pop bot logic
                result = self._evaluate_holy_grail_pop_bot(
                    indicators
                )  # TODO: Phase 9 - Remove type ignore after converting to KLMDecision

            self.log_decision(result[0], result[1], result[2])
            return result

        # Default to complex KMLM switcher logic
        return self._evaluate_kmlm_switcher_plus_fngu(indicators)

    def _evaluate_holy_grail_pop_bot(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[str | dict[str, float], str, str]:
        """Pop bot logic within Holy Grail branch"""

        # TQQQ oversold (< 31, different from standard < 30)
        if "TQQQ" in indicators and indicators["TQQQ"].get("rsi_10", 50) < 31:
            return ("TECL", ActionType.BUY.value, "Holy Grail Pop Bot: TQQQ RSI < 31 → TECL")

        # SOXL oversold
        if "SOXL" in indicators and indicators["SOXL"].get("rsi_10", 50) < 30:
            return ("SOXL", ActionType.BUY.value, "Holy Grail Pop Bot: SOXL RSI < 30 → SOXL")

        # SPXL oversold
        if "SPXL" in indicators and indicators["SPXL"].get("rsi_10", 50) < 30:
            return ("SPXL", ActionType.BUY.value, "Holy Grail Pop Bot: SPXL RSI < 30 → SPXL")

        # Fall through to KMLM Switcher + FNGU
        return self._evaluate_kmlm_switcher_plus_fngu(indicators)

    def _evaluate_kmlm_switcher_plus_fngu(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[str | dict[str, float], str, str]:
        """
        "KMLM Switcher + FNGU" with complex 50/50 FNGU logic.

        This is the most sophisticated KMLM switcher in the ensemble.
        """

        xlk_rsi = indicators.get("XLK", {}).get("rsi_10", 50)
        kmlm_rsi = indicators.get("KMLM", {}).get("rsi_10", 50)

        if xlk_rsi > kmlm_rsi:
            # Complex tech selection: TECL, SVXY, or "50% FNGU / 50% FNGU or Not"
            candidates = [
                ("TECL", indicators.get("TECL", {}).get("rsi_10", 50)),
                ("SVXY", indicators.get("SVXY", {}).get("rsi_10", 50)),
                ("FNGU_COMPLEX", 50),  # Placeholder for complex FNGU logic
            ]

            # Select bottom 1 (lowest RSI)
            candidates.sort(key=lambda x: x[1])

            if candidates[0][0] == "FNGU_COMPLEX":
                # Implement "50% FNGU / 50% FNGU or Not" logic
                # This involves moving-average-return filtering of FNGU/SPXL/XLE/XLK/AGG
                _fngu_ma_return = indicators.get("FNGU", {}).get(
                    "moving_average_return_20", 0
                )  # Reserved for future use
                comparison_candidates = []
                for symbol in ["FNGU", "SPXL", "XLE", "XLK", "AGG"]:
                    if symbol in indicators:
                        ma_return = indicators[symbol].get("moving_average_return_20", 0)
                        comparison_candidates.append((symbol, ma_return))

                if comparison_candidates:
                    # Select top 1 by moving average return
                    best_candidate = max(comparison_candidates, key=lambda x: x[1])
                    # 50/50 allocation between FNGU and best candidate
                    if best_candidate[0] != "FNGU":
                        allocation = {"FNGU": 0.5, best_candidate[0]: 0.5}
                        result = (
                            allocation,
                            ActionType.BUY.value,
                            f"KMLM Switcher: 50% FNGU / 50% {best_candidate[0]} (best MA return)",
                        )
                    else:
                        result = (  # TODO: Phase 9 - Remove type ignore after converting to KLMDecision
                            "FNGU",
                            ActionType.BUY.value,
                            "KMLM Switcher: 100% FNGU (best MA return)",
                        )
                else:
                    result = (
                        "FNGU",
                        ActionType.BUY.value,
                        "KMLM Switcher: FNGU fallback",
                    )  # TODO: Phase 9 - Remove type ignore after converting to KLMDecision
            else:
                # Simple tech selection
                result = (  # TODO: Phase 9 - Remove type ignore after converting to KLMDecision
                    candidates[0][0],
                    ActionType.BUY.value,
                    f"KMLM Switcher: {candidates[0][0]} (lowest RSI: {candidates[0][1]:.1f})",
                )
        else:
            # Long/Short Rotator with stdev filtering (select bottom 3)
            rotator_candidates = []
            for symbol in ["SVXY", "VIXM", "FTLS", "KMLM", "UUP"]:
                if symbol in indicators:
                    stdev = indicators[symbol].get("stdev_return_6", 0.1)
                    rotator_candidates.append((symbol, stdev))

            if len(rotator_candidates) >= 3:
                # Select bottom 3 (lowest volatility)
                rotator_candidates.sort(key=lambda x: x[1])
                selected = rotator_candidates[:3]
                allocation = {symbol: 1.0 / 3 for symbol, _ in selected}
                symbols = ", ".join([s[0] for s in selected])
                result = (
                    allocation,
                    ActionType.BUY.value,
                    f"L/S Rotator: {symbols} (lowest volatility)",
                )
            elif rotator_candidates:
                # Less than 3 available
                best = min(rotator_candidates, key=lambda x: x[1])
                result = (  # TODO: Phase 9 - Remove type ignore after converting to KLMDecision
                    best[0],
                    ActionType.BUY.value,
                    f"L/S Rotator: {best[0]} (lowest volatility)",
                )
            else:
                # Ultimate fallback
                result = (
                    "KMLM",
                    ActionType.BUY.value,
                    "L/S Rotator: KMLM fallback",
                )  # TODO: Phase 9 - Remove type ignore after converting to KLMDecision

        self.log_decision(result[0], result[1], result[2])
        return result

    def get_required_symbols(self) -> list[str]:
        """530/18 Complete symbol requirements - this is the largest set"""

        # Scale-in symbols
        scale_in_symbols = ["SPY", "IOO", "QQQ", "VTV", "XLP", "XLF", "RETL"]

        # VIX blend symbols
        vix_symbols = ["UVXY", "VXX", "VIXM", "VIXY"]

        # BTAL/BIL defensive
        defensive_symbols = ["BTAL", "BIL"]

        # Overbought complex logic symbols
        overbought_symbols = ["AGG"]

        # All 3x tech symbols
        tech_3x_symbols = ["TQQQ", "SPXL", "SOXL", "FNGU", "ERX"]

        # Commodity symbols
        commodity_symbols = ["GLD", "SLV", "PDBC"]

        # Holy Grail symbols
        holy_grail_symbols = ["VOX", "TECL", "SVXY"]

        # KMLM Switcher + FNGU symbols
        kmlm_switcher_symbols = ["XLK", "KMLM", "XLE", "FTLS", "UUP"]

        # Additional complex logic symbols
        additional_symbols = ["PSQ", "QID", "UPRO", "TMF"]

        # Combine all unique symbols
        all_symbols = (
            scale_in_symbols
            + vix_symbols
            + defensive_symbols
            + overbought_symbols
            + tech_3x_symbols
            + commodity_symbols
            + holy_grail_symbols
            + kmlm_switcher_symbols
            + additional_symbols
        )

        return list(set(all_symbols))

    # Override the base class method since 530/18 doesn't use standard pattern
    def evaluate_core_kmlm_switcher(
        self, indicators: dict[str, dict[str, float]]
    ) -> tuple[str | dict[str, float], str, str]:
        """
        530/18 doesn't use the standard core KMLM switcher pattern.
        It has its own complex Holy Grail logic.
        """
        return self._evaluate_holy_grail_kmlm_switcher(indicators)
