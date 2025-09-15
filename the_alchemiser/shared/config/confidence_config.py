"""Business Unit: shared | Status: current

Confidence calculation configuration for strategy engines.
Centralizes all confidence parameters, thresholds, and mappings.

NOTE: Confidence thresholds for signal filtering have been DEPRECATED.
Strategy signals are concrete and should not be filtered by confidence.
Confidence is now ONLY used for weighting between strategies during conflict resolution.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar


@dataclass(frozen=True)
class ConfidenceThresholds:
    """DEPRECATED: Minimum confidence thresholds - no longer used for filtering.
    
    Strategy signals are concrete and should not be filtered by confidence.
    Confidence is only used for weighting between strategies.
    Kept for backward compatibility only.
    """

    buy_min: Decimal = Decimal("0.00")  # No filtering
    sell_min: Decimal = Decimal("0.00")  # No filtering
    hold_min: Decimal = Decimal("0.00")  # No filtering

    def get_threshold(self, action: str) -> Decimal:
        """DEPRECATED: Get minimum confidence threshold for an action.
        
        Always returns 0.00 since filtering is disabled.
        """
        return Decimal("0.00")  # No filtering - all signals are valid


@dataclass(frozen=True)
class TECLConfidenceConfig:
    """TECL strategy confidence calculation parameters."""

    # Base confidence levels
    base_confidence: Decimal = Decimal("0.60")
    max_confidence: Decimal = Decimal("0.90")
    min_confidence: Decimal = Decimal("0.40")

    # RSI-based adjustments
    rsi_extreme_threshold: Decimal = Decimal("80.0")  # RSI > 80 or < 20 = extreme
    rsi_moderate_threshold: Decimal = Decimal("70.0")  # RSI > 70 or < 30 = moderate
    rsi_extreme_boost: Decimal = Decimal("0.20")  # +0.20 for extreme RSI
    rsi_moderate_boost: Decimal = Decimal("0.10")  # +0.10 for moderate RSI

    # Moving average distance adjustments
    ma_distance_threshold: Decimal = Decimal("0.05")  # 5% distance from MA
    ma_distance_boost: Decimal = Decimal("0.10")  # +0.10 for significant MA distance

    # Defensive position penalties
    defensive_penalty: Decimal = Decimal("0.15")  # -0.15 for defensive/hold positions


@dataclass(frozen=True)
class NuclearConfidenceConfig:
    """Nuclear strategy confidence calculation parameters."""

    # Base confidence levels
    base_confidence: Decimal = Decimal("0.50")
    max_confidence: Decimal = Decimal("0.90")
    min_confidence: Decimal = Decimal("0.40")

    # Indicator-based confidence tiers
    extreme_overbought_confidence: Decimal = Decimal("0.90")  # RSI > 85
    oversold_buy_confidence: Decimal = Decimal("0.85")  # RSI < 25 + BUY
    volatility_hedge_confidence: Decimal = Decimal("0.80")  # High VIX conditions
    market_regime_confidence: Decimal = Decimal("0.70")  # Bull/bear regime signals
    hold_confidence: Decimal = Decimal("0.60")  # Default HOLD confidence

    # RSI thresholds for confidence tiers
    rsi_extreme_overbought: Decimal = Decimal("85.0")
    rsi_oversold: Decimal = Decimal("25.0")
    rsi_moderate_overbought: Decimal = Decimal("75.0")
    rsi_moderate_oversold: Decimal = Decimal("35.0")


@dataclass(frozen=True)
class KLMConfidenceConfig:
    """KLM strategy confidence calculation parameters."""

    # Action-based base confidence
    buy_base: Decimal = Decimal("0.50")
    buy_weight_multiplier: Decimal = Decimal("0.40")  # weight * 0.40
    buy_max: Decimal = Decimal("0.90")

    sell_confidence: Decimal = Decimal("0.70")
    hold_confidence: Decimal = Decimal("0.30")

    # Weight-based adjustments
    high_weight_threshold: Decimal = Decimal("0.75")  # Weight > 75% = high confidence
    high_weight_boost: Decimal = Decimal("0.05")  # +0.05 for high weight positions


@dataclass(frozen=True)
class AggregationConfig:
    """Configuration for signal aggregation and conflict resolution.
    
    Note: Confidence thresholds are deprecated. All strategy signals are preserved
    and confidence is only used for weighting between strategies.
    """

    # DEPRECATED: Confidence thresholds (kept for backward compatibility)
    thresholds: ConfidenceThresholds = ConfidenceThresholds()

    # Tie-breaking priority order (first = highest priority)
    strategy_priority: ClassVar[list[str]] = ["NUCLEAR", "TECL", "KLM"]

    # Minimum confidence to win a conflict (deprecated, not used)
    min_winning_confidence: Decimal = Decimal("0.00")

    # Whether to blend allocations when strategies agree (conservative: False)
    blend_agreeing_allocations: bool = False


@dataclass(frozen=True)
class ConfidenceConfig:
    """Master confidence configuration combining all strategy configs."""

    # Strategy-specific configurations
    tecl: TECLConfidenceConfig = TECLConfidenceConfig()
    nuclear: NuclearConfidenceConfig = NuclearConfidenceConfig()
    klm: KLMConfidenceConfig = KLMConfidenceConfig()

    # Aggregation and conflict resolution
    aggregation: AggregationConfig = AggregationConfig()

    @classmethod
    def default(cls) -> ConfidenceConfig:
        """Get default confidence configuration."""
        return cls()
