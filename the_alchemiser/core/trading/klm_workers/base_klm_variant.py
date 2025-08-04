"""
Base KLM Strategy Variant

Abstract base class for all KLM strategy variants. Provides common functionality
and enforces a consistent interface across all variants.
"""

import logging
from abc import ABC, abstractmethod

import numpy as np
import pandas as pd

from the_alchemiser.core.utils.common import ActionType


class BaseKLMVariant(ABC):
    """
    Abstract base class for all KLM strategy variants.

    Each variant must implement the evaluate() method to return trading decisions.
    Common functionality like filter operations and allocation logic is shared.
    """

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.performance_history = []
        self.logger = logging.getLogger(f"KLM.{name}")

    @abstractmethod
    def evaluate(
        self,
        indicators: dict[str, dict[str, float]],
        market_data: dict[str, pd.DataFrame] | None = None,
    ) -> tuple[str | dict[str, float], str, str]:
        """
        Evaluate the strategy variant and return trading decision.

        Args:
            indicators: Dictionary of calculated technical indicators
            market_data: Raw market data (optional)

        Returns:
            Tuple of (symbol_or_allocation, action, reason)
            - symbol_or_allocation: Single symbol string OR dict of {symbol: weight}
            - action: Action type (BUY, SELL, HOLD)
            - reason: Human-readable explanation
        """
        pass

    # Common filter operations used across variants
    def apply_stdev_return_filter(
        self, candidates: list, indicators: dict, window: int = 6
    ) -> list:
        """Apply (stdev-return {:window N}) filter as in Clojure"""
        filtered_candidates = []
        for symbol in candidates:
            if symbol in indicators and "stdev_return_6" in indicators[symbol]:
                stdev = indicators[symbol].get(f"stdev_return_{window}", 1.0)
                filtered_candidates.append((symbol, stdev))

        # Sort by standard deviation (ascending for select-bottom)
        return sorted(filtered_candidates, key=lambda x: x[1])

    def apply_select_bottom_filter(self, candidates: list, count: int = 1) -> list:
        """Apply (select-bottom N) logic - select lowest value candidates"""
        sorted_candidates = sorted(candidates, key=lambda x: x[1])
        return sorted_candidates[:count]

    def apply_select_top_filter(self, candidates: list, count: int = 1) -> list:
        """Apply (select-top N) logic - select highest value candidates"""
        sorted_candidates = sorted(candidates, key=lambda x: x[1], reverse=True)
        return sorted_candidates[:count]

    def apply_rsi_filter(self, candidates: list, indicators: dict, window: int = 10) -> list:
        """Filter candidates by RSI values"""
        filtered = []
        for symbol in candidates:
            if symbol in indicators:
                rsi = indicators[symbol].get(f"rsi_{window}", 50)
                filtered.append((symbol, rsi))
        return filtered

    # Common allocation patterns from Clojure
    @property
    def VIX_BLEND_PLUS_PLUS(self) -> dict[str, float]:
        """VIX Blend++ allocation: Double weight UVXY"""
        return {"UVXY": 0.667, "VIXM": 0.333}  # 2 out of 3 assets

    @property
    def VIX_BLEND_PLUS(self) -> dict[str, float]:
        """VIX Blend+ allocation: Equal weight VIX assets"""
        return {"UVXY": 0.333, "VXX": 0.333, "VIXM": 0.333}

    @property
    def VIX_BLEND(self) -> dict[str, float]:
        """VIX Blend allocation: Uses VIXY instead of UVXY"""
        return {"VIXY": 0.333, "VXX": 0.333, "VIXM": 0.333}

    @property
    def BTAL_BIL(self) -> dict[str, float]:
        """BTAL/BIL allocation for defensive positioning"""
        return {"BTAL": 0.5, "BIL": 0.5}

    # Common RSI overbought checks
    def check_primary_overbought_conditions(self, indicators: dict) -> tuple[str | None, str]:
        """
        Complete 11-step overbought detection chain from CLJ.
        ALL standard variants follow this exact sequence before "Single Popped KMLM".

        Sequence: QQQE → VTV → VOX → TECL → VOOG → VOOV → XLP → TQQQ → XLY → FAS → SPY

        Returns (symbol, reason) or (None, "") if no conditions met.
        """

        # Step 1: QQQE RSI(10) > 79
        if "QQQE" in indicators and indicators["QQQE"].get("rsi_10", 0) > 79:
            return ("UVXY", "QQQE RSI(10) > 79 → UVXY")

        # Step 2: VTV RSI(10) > 79
        if "VTV" in indicators and indicators["VTV"].get("rsi_10", 0) > 79:
            return ("UVXY", "VTV RSI(10) > 79 → UVXY")

        # Step 3: VOX RSI(10) > 79
        if "VOX" in indicators and indicators["VOX"].get("rsi_10", 0) > 79:
            return ("UVXY", "VOX RSI(10) > 79 → UVXY")

        # Step 4: TECL RSI(10) > 79
        if "TECL" in indicators and indicators["TECL"].get("rsi_10", 0) > 79:
            return ("UVXY", "TECL RSI(10) > 79 → UVXY")

        # Step 5: VOOG RSI(10) > 79
        if "VOOG" in indicators and indicators["VOOG"].get("rsi_10", 0) > 79:
            return ("UVXY", "VOOG RSI(10) > 79 → UVXY")

        # Step 6: VOOV RSI(10) > 79
        if "VOOV" in indicators and indicators["VOOV"].get("rsi_10", 0) > 79:
            return ("UVXY", "VOOV RSI(10) > 79 → UVXY")

        # Step 7: XLP RSI(10) > 75 (different threshold!)
        if "XLP" in indicators and indicators["XLP"].get("rsi_10", 0) > 75:
            return ("UVXY", "XLP RSI(10) > 75 → UVXY")

        # Step 8: TQQQ RSI(10) > 79
        if "TQQQ" in indicators and indicators["TQQQ"].get("rsi_10", 0) > 79:
            return ("UVXY", "TQQQ RSI(10) > 79 → UVXY")

        # Step 9: XLY RSI(10) > 80 (different threshold!)
        if "XLY" in indicators and indicators["XLY"].get("rsi_10", 0) > 80:
            return ("UVXY", "XLY RSI(10) > 80 → UVXY")

        # Step 10: FAS RSI(10) > 80
        if "FAS" in indicators and indicators["FAS"].get("rsi_10", 0) > 80:
            return ("UVXY", "FAS RSI(10) > 80 → UVXY")

        # Step 11: SPY RSI(10) > 80
        if "SPY" in indicators and indicators["SPY"].get("rsi_10", 0) > 80:
            return ("UVXY", "SPY RSI(10) > 80 → UVXY")

        # No overbought conditions met - proceed to Single Popped KMLM
        return (None, "")

    def evaluate_single_popped_kmlm(
        self, indicators: dict
    ) -> tuple[str | dict[str, float], str, str]:
        """
        Single Popped KMLM logic - common across most standard variants.

        Logic:
        1. Check UVXY RSI(21) > 65 → BSC strategy
        2. Else → Combined Pop Bot
        """

        # Check UVXY RSI(21) for strategy branching
        if "UVXY" in indicators:
            uvxy_rsi_21 = indicators["UVXY"].get("rsi_21", 50)

            if uvxy_rsi_21 > 65:
                # UVXY elevated - use BSC (Bond/Stock/Commodity) strategy
                return self.evaluate_bsc_strategy(indicators)
            else:
                # UVXY normal - use Combined Pop Bot
                return self.evaluate_combined_pop_bot(indicators)

        # Fallback if UVXY data unavailable
        return self.evaluate_combined_pop_bot(indicators)

    def evaluate_bsc_strategy(self, indicators: dict) -> tuple[str, str, str]:
        """
        BSC (Bond/Stock/Commodity) strategy when UVXY RSI(21) > 65

        Logic from CLJ:
        - If SPY RSI(21) > 30: VIXM (moderate VIX position)
        - Else: SPXL (leveraged long position)
        """
        if "SPY" in indicators:
            spy_rsi_21 = indicators["SPY"].get("rsi_21", 50)

            if spy_rsi_21 > 30:
                result = (
                    "VIXM",
                    ActionType.BUY.value,
                    f"BSC: SPY RSI(21) {spy_rsi_21:.1f} > 30 → VIXM",
                )
            else:
                result = (
                    "SPXL",
                    ActionType.BUY.value,
                    f"BSC: SPY RSI(21) {spy_rsi_21:.1f} ≤ 30 → SPXL",
                )
        else:
            # Fallback
            result = ("VIXM", ActionType.BUY.value, "BSC: Default VIXM (no SPY data)")

        self.log_decision(result[0], result[1], result[2])
        return result

    def evaluate_combined_pop_bot(
        self, indicators: dict
    ) -> tuple[str | dict[str, float], str, str]:
        """
        Combined Pop Bot strategy - standard across most variants.

        Sequence (from CLJ):
        1. TQQQ RSI(10) < 30 → TECL
        2. SOXL RSI(10) < 30 → SOXL
        3. SPXL RSI(10) < 30 → SPXL
        4. Proceed to variant-specific KMLM switcher
        """

        # Priority 1: TQQQ oversold check
        if "TQQQ" in indicators:
            tqqq_rsi = indicators["TQQQ"].get("rsi_10", 50)
            if tqqq_rsi < 30:
                result = (
                    "TECL",
                    ActionType.BUY.value,
                    f"Pop Bot: TQQQ RSI(10) {tqqq_rsi:.1f} < 30 → TECL",
                )
                self.log_decision(result[0], result[1], result[2])
                return result

        # Priority 2: SOXL oversold check
        if "SOXL" in indicators:
            soxl_rsi = indicators["SOXL"].get("rsi_10", 50)
            if soxl_rsi < 30:
                result = (
                    "SOXL",
                    ActionType.BUY.value,
                    f"Pop Bot: SOXL RSI(10) {soxl_rsi:.1f} < 30 → SOXL",
                )
                self.log_decision(result[0], result[1], result[2])
                return result

        # Priority 3: SPXL oversold check
        if "SPXL" in indicators:
            spxl_rsi = indicators["SPXL"].get("rsi_10", 50)
            if spxl_rsi < 30:
                result = (
                    "SPXL",
                    ActionType.BUY.value,
                    f"Pop Bot: SPXL RSI(10) {spxl_rsi:.1f} < 30 → SPXL",
                )
                self.log_decision(result[0], result[1], result[2])
                return result

        # No oversold conditions - proceed to variant-specific KMLM switcher
        return self.evaluate_core_kmlm_switcher(indicators)

    @abstractmethod
    def evaluate_core_kmlm_switcher(
        self, indicators: dict
    ) -> tuple[str | dict[str, float], str, str]:
        """
        Core KMLM switcher - each variant implements its own logic.
        This is where variants differ after the common overbought/pop bot logic.
        """
        pass

    def log_decision(self, symbol_or_allocation: str | dict, action: str, reason: str):
        """Log trading decision with context"""
        if isinstance(symbol_or_allocation, dict):
            symbols = list(symbol_or_allocation.keys())
            self.logger.info(f"{self.name}: {action} {symbols} - {reason}")
        else:
            self.logger.info(f"{self.name}: {action} {symbol_or_allocation} - {reason}")

    def get_base_required_symbols(self) -> list:
        """
        Base symbols required by the standard 11-step overbought chain and pop bot logic.
        Variants should extend this list with their specific requirements.
        """
        return [
            # 11-step overbought detection
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
            # UVXY for overbought results and RSI(21) check
            "UVXY",
            # BSC strategy
            "VIXM",
            "SPXL",
            # Combined Pop Bot
            "SOXL",
            # Common KMLM switcher symbols
            "XLK",
            "KMLM",
        ]

    def create_equal_weight_allocation(self, symbols: list, indicators: dict) -> dict[str, float]:
        """Create equal weight allocation among available symbols"""
        available_symbols = [s for s in symbols if s in indicators]
        if not available_symbols:
            return {}

        weight = 1.0 / len(available_symbols)
        return dict.fromkeys(available_symbols, weight)

    def calculate_performance_metric(self, window: int = 5) -> float:
        """
        Calculate performance metric for ensemble selection.
        This should track the 5-day standard deviation of returns.
        """
        if len(self.performance_history) < window:
            return 0.0

        recent_performance = self.performance_history[-window:]
        return float(np.std(recent_performance)) if recent_performance else 0.0

    def update_performance(self, return_value: float):
        """Update performance history for ensemble selection"""
        self.performance_history.append(return_value)
        # Keep only last 100 values to prevent memory bloat
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]
