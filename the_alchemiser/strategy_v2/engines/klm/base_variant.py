"""Business Unit: strategy | Status: current.

Base KLM Strategy Variant.

Abstract base class for all KLM strategy variants. Provides common functionality
and enforces a consistent interface across all variants.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

import numpy as np
import pandas as pd

from the_alchemiser.shared.utils.common import ActionType
from the_alchemiser.shared.value_objects.core_types import KLMDecision


class BaseKLMVariant(ABC):
    """Abstract base class for all KLM strategy variants.

    Each variant must implement the evaluate() method to return trading decisions.
    Common functionality like filter operations and allocation logic is shared.
    """

    def __init__(self, name: str, description: str) -> None:
        """Initialize KLM variant with name and description."""
        self.name = name
        self.description = description
        self.performance_history: list[float] = []
        self.logger = logging.getLogger(f"KLM.{name}")

    @abstractmethod
    def evaluate(
        self,
        indicators: dict[str, dict[str, float]],
        market_data: dict[str, pd.DataFrame] | None = None,
    ) -> KLMDecision:
        """Evaluate the strategy variant and return trading decision.

        Args:
            indicators: Dictionary of calculated technical indicators
            market_data: Raw market data (optional)

        Returns:
            Structured KLMDecision object with symbol, action, and reasoning

        Note:
            Phase 9 migration complete: All variants now return KLMDecision format.
            Legacy tuple support maintained in engine during transition.

        """

    # Common filter operations used across variants
    def apply_stdev_return_filter(
        self, candidates: list[str], indicators: dict[str, Any], window: int = 6
    ) -> list[tuple[str, float]]:
        """Apply (stdev-return {:window N}) filter as in Clojure."""
        filtered_candidates = []
        for symbol in candidates:
            if symbol in indicators and "stdev_return_6" in indicators[symbol]:
                stdev = indicators[symbol].get(f"stdev_return_{window}", 1.0)
                filtered_candidates.append((symbol, stdev))

        # Sort by standard deviation (ascending for select-bottom)
        return sorted(filtered_candidates, key=lambda x: x[1])

    def apply_select_bottom_filter(
        self, candidates: list[tuple[str, float]], count: int = 1
    ) -> list[tuple[str, float]]:
        """Apply (select-bottom N) logic - select lowest value candidates."""
        sorted_candidates = sorted(candidates, key=lambda x: x[1])
        return sorted_candidates[:count]

    def apply_select_top_filter(
        self, candidates: list[tuple[str, float]], count: int = 1
    ) -> list[tuple[str, float]]:
        """Apply (select-top N) logic - select highest value candidates."""
        sorted_candidates = sorted(candidates, key=lambda x: x[1], reverse=True)
        return sorted_candidates[:count]

    def apply_rsi_filter(
        self, candidates: list[str], indicators: dict[str, Any], window: int = 10
    ) -> list[str]:
        """Filter candidates by RSI values.

        Filters out symbols that don't have valid RSI data for the specified window.
        This ensures only symbols with complete RSI indicators are considered for strategy decisions.

        Args:
            candidates: List of symbol strings to filter
            indicators: Dictionary containing RSI indicator data
            window: RSI calculation window (default 10)

        Returns:
            List of symbols that have valid RSI data for the specified window

        """
        filtered = []
        rsi_key = f"rsi_{window}"

        for symbol in candidates:
            if symbol in indicators and rsi_key in indicators[symbol]:
                rsi_value = indicators[symbol][rsi_key]
                # Ensure RSI value is valid (between 0 and 100)
                if isinstance(rsi_value, int | float) and 0 <= rsi_value <= 100:
                    filtered.append(symbol)

        return filtered

    def create_klm_decision(
        self, symbol_or_allocation: str | dict[str, float], action: str, reasoning: str
    ) -> KLMDecision:
        """Create a structured KLMDecision from individual components.

        Helper method for Phase 9 migration to support variants transitioning
        from tuple returns to structured KLMDecision objects.

        Args:
            symbol_or_allocation: Single symbol string or allocation dict
            action: Action type (BUY, SELL, HOLD)
            reasoning: Human-readable explanation

        Returns:
            Structured KLMDecision object

        """
        return {
            "symbol": symbol_or_allocation,
            "action": action,  # type: ignore[typeddict-item]
            "reasoning": reasoning,
        }

    # Common allocation patterns from Clojure
    @property
    def vix_blend_plus_plus(self) -> dict[str, float]:
        """VIX Blend++ allocation: Double weight UVXY."""
        return {"UVXY": 0.667, "VIXM": 0.333}  # 2 out of 3 assets

    @property
    def vix_blend_plus(self) -> dict[str, float]:
        """VIX Blend+ allocation: Equal weight VIX assets."""
        return {"UVXY": 0.333, "VXX": 0.333, "VIXM": 0.333}

    @property
    def vix_blend(self) -> dict[str, float]:
        """VIX Blend allocation: Uses VIXY instead of UVXY."""
        return {"VIXY": 0.333, "VXX": 0.333, "VIXM": 0.333}

    @property
    def btal_bil(self) -> dict[str, float]:
        """BTAL/BIL allocation for defensive positioning."""
        return {"BTAL": 0.5, "BIL": 0.5}

    # Common RSI overbought checks
    def check_primary_overbought_conditions(
        self, indicators: dict[str, dict[str, float]]
    ) -> KLMDecision | None:
        """Complete 11-step overbought detection chain from CLJ.

        ALL standard variants follow this exact sequence before "Single Popped KMLM".

        Sequence: QQQE → VTV → VOX → TECL → VOOG → VOOV → XLP → TQQQ → XLY → FAS → SPY

        Returns KLMDecision if overbought condition met, None otherwise.
        """
        # Step 1: QQQE RSI(10) > 79
        if "QQQE" in indicators and indicators["QQQE"].get("rsi_10", 0) > 79:
            return self.create_klm_decision("UVXY", "BUY", "QQQE RSI(10) > 79 → UVXY")

        # Step 2: VTV RSI(10) > 79
        if "VTV" in indicators and indicators["VTV"].get("rsi_10", 0) > 79:
            return self.create_klm_decision("UVXY", "BUY", "VTV RSI(10) > 79 → UVXY")

        # Step 3: VOX RSI(10) > 79
        if "VOX" in indicators and indicators["VOX"].get("rsi_10", 0) > 79:
            return self.create_klm_decision("UVXY", "BUY", "VOX RSI(10) > 79 → UVXY")

        # Step 4: TECL RSI(10) > 79
        if "TECL" in indicators and indicators["TECL"].get("rsi_10", 0) > 79:
            return self.create_klm_decision("UVXY", "BUY", "TECL RSI(10) > 79 → UVXY")

        # Step 5: VOOG RSI(10) > 79
        if "VOOG" in indicators and indicators["VOOG"].get("rsi_10", 0) > 79:
            return self.create_klm_decision("UVXY", "BUY", "VOOG RSI(10) > 79 → UVXY")

        # Step 6: VOOV RSI(10) > 79
        if "VOOV" in indicators and indicators["VOOV"].get("rsi_10", 0) > 79:
            return self.create_klm_decision("UVXY", "BUY", "VOOV RSI(10) > 79 → UVXY")

        # Step 7: XLP RSI(10) > 75 (different threshold!)
        if "XLP" in indicators and indicators["XLP"].get("rsi_10", 0) > 75:
            return self.create_klm_decision("UVXY", "BUY", "XLP RSI(10) > 75 → UVXY")

        # Step 8: TQQQ RSI(10) > 79
        if "TQQQ" in indicators and indicators["TQQQ"].get("rsi_10", 0) > 79:
            return self.create_klm_decision("UVXY", "BUY", "TQQQ RSI(10) > 79 → UVXY")

        # Step 9: XLY RSI(10) > 80 (different threshold!)
        if "XLY" in indicators and indicators["XLY"].get("rsi_10", 0) > 80:
            return self.create_klm_decision("UVXY", "BUY", "XLY RSI(10) > 80 → UVXY")

        # Step 10: FAS RSI(10) > 80
        if "FAS" in indicators and indicators["FAS"].get("rsi_10", 0) > 80:
            return self.create_klm_decision("UVXY", "BUY", "FAS RSI(10) > 80 → UVXY")

        # Step 11: SPY RSI(10) > 80
        if "SPY" in indicators and indicators["SPY"].get("rsi_10", 0) > 80:
            return self.create_klm_decision("UVXY", "BUY", "SPY RSI(10) > 80 → UVXY")

        # No overbought conditions met - proceed to Single Popped KMLM
        return None

    def evaluate_single_popped_kmlm(
        self, indicators: dict[str, dict[str, float]]
    ) -> KLMDecision:
        """Single Popped KMLM logic - common across most standard variants.

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
            # UVXY normal - use Combined Pop Bot
            return self.evaluate_combined_pop_bot(indicators)

        # Fallback if UVXY data unavailable
        return self.evaluate_combined_pop_bot(indicators)

    def evaluate_bsc_strategy(
        self, indicators: dict[str, dict[str, float]]
    ) -> KLMDecision:
        """BSC (Bond/Stock/Commodity) strategy when UVXY RSI(21) > 65.

        Logic from CLJ:
        - If SPY RSI(21) > 30: VIXM (moderate VIX position)
        - Else: SPXL (leveraged long position)
        """
        if "SPY" in indicators:
            spy_rsi_21 = indicators["SPY"].get("rsi_21", 50)

            if spy_rsi_21 > 30:
                result = self.create_klm_decision(
                    "VIXM",
                    ActionType.BUY.value,
                    f"BSC: SPY RSI(21) {spy_rsi_21:.1f} > 30 → VIXM",
                )
            else:
                result = self.create_klm_decision(
                    "SPXL",
                    ActionType.BUY.value,
                    f"BSC: SPY RSI(21) {spy_rsi_21:.1f} ≤ 30 → SPXL",
                )
        else:
            # Fallback
            result = self.create_klm_decision(
                "VIXM", ActionType.BUY.value, "BSC: Default VIXM (no SPY data)"
            )

        self.log_klm_decision(result)
        return result

    def evaluate_combined_pop_bot(
        self, indicators: dict[str, dict[str, float]]
    ) -> KLMDecision:
        """Evaluate Combined Pop Bot strategy - standard across most variants.

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
                result = self.create_klm_decision(
                    "TECL",
                    ActionType.BUY.value,
                    f"Pop Bot: TQQQ RSI(10) {tqqq_rsi:.1f} < 30 → TECL",
                )
                self.log_klm_decision(result)
                return result

        # Priority 2: SOXL oversold check
        if "SOXL" in indicators:
            soxl_rsi = indicators["SOXL"].get("rsi_10", 50)
            if soxl_rsi < 30:
                result = self.create_klm_decision(
                    "SOXL",
                    ActionType.BUY.value,
                    f"Pop Bot: SOXL RSI(10) {soxl_rsi:.1f} < 30 → SOXL",
                )
                self.log_klm_decision(result)
                return result

        # Priority 3: SPXL oversold check
        if "SPXL" in indicators:
            spxl_rsi = indicators["SPXL"].get("rsi_10", 50)
            if spxl_rsi < 30:
                result = self.create_klm_decision(
                    "SPXL",
                    ActionType.BUY.value,
                    f"Pop Bot: SPXL RSI(10) {spxl_rsi:.1f} < 30 → SPXL",
                )
                self.log_klm_decision(result)
                return result

        # No oversold conditions - proceed to variant-specific KMLM switcher
        return self.evaluate_core_kmlm_switcher(indicators)

    @abstractmethod
    def evaluate_core_kmlm_switcher(
        self, indicators: dict[str, dict[str, float]]
    ) -> KLMDecision:
        """Core KMLM switcher - each variant implements its own logic.

        This is where variants differ after the common overbought/pop bot logic.
        """

    def log_decision(
        self, symbol_or_allocation: str | dict[str, float], action: str, reason: str
    ) -> None:
        """Log trading decision with context."""
        if isinstance(symbol_or_allocation, dict):
            symbols = list(symbol_or_allocation.keys())
            self.logger.info(f"{self.name}: {action} {symbols} - {reason}")
        else:
            self.logger.info(f"{self.name}: {action} {symbol_or_allocation} - {reason}")

    def log_klm_decision(self, decision: KLMDecision) -> None:
        """Log KLMDecision with context."""
        symbol = decision["symbol"]
        action = decision["action"]
        reason = decision["reasoning"]
        self.log_decision(symbol, action, reason)

    def get_base_required_symbols(self) -> list[str]:
        """Get base symbols required by the standard 11-step overbought chain and pop bot logic.

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

    def create_equal_weight_allocation(
        self, symbols: list[str], indicators: dict[str, Any]
    ) -> dict[str, float]:
        """Create equal weight allocation among available symbols."""
        available_symbols = [s for s in symbols if s in indicators]
        if not available_symbols:
            return {}

        weight = 1.0 / len(available_symbols)
        return dict.fromkeys(available_symbols, weight)

    def calculate_performance_metric(self, window: int = 5) -> float:
        """Calculate performance metric for ensemble selection.

        This should track the 5-day standard deviation of returns.
        """
        if len(self.performance_history) < window:
            return 0.0

        recent_performance = self.performance_history[-window:]
        return float(np.std(recent_performance)) if recent_performance else 0.0

    def update_performance(self, return_value: float) -> None:
        """Update performance history for ensemble selection."""
        self.performance_history.append(return_value)
        # Keep only last 100 values to prevent memory bloat
        if len(self.performance_history) > 100:
            self.performance_history = self.performance_history[-100:]
