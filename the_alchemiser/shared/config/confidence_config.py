"""Business Unit: shared | Status: current.

Confidence calculation configuration for strategy engines.
Centralizes all confidence parameters for strategy weighting.

NOTE: Confidence is ONLY used for weighting between strategies during conflict resolution.
Strategy signals are concrete and preserved intact. High confidence strategies get up to 
10% additional weighting vs low confidence strategies for gentle weighting adjustments.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar


@dataclass(frozen=True)
class TECLConfidenceConfig:
    """TECL strategy confidence calculation parameters."""

    # Base confidence levels (standardized range)
    base_confidence: Decimal = Decimal("0.60")
    max_confidence: Decimal = Decimal("0.90")
    min_confidence: Decimal = Decimal("0.45")  # Increased floor for consistency

    # RSI-based adjustments (standardized)
    rsi_extreme_threshold: Decimal = Decimal("80.0")  # RSI > 80 or < 20 = extreme
    rsi_moderate_threshold: Decimal = Decimal("70.0")  # RSI > 70 or < 30 = moderate
    rsi_extreme_boost: Decimal = Decimal("0.15")  # Reduced from 0.20
    rsi_moderate_boost: Decimal = Decimal("0.08")  # Reduced from 0.10

    # Moving average distance adjustments (standardized)
    ma_distance_threshold: Decimal = Decimal("0.05")  # 5% distance from MA
    ma_distance_boost: Decimal = Decimal("0.08")  # Reduced from 0.10

    # Defensive position adjustments (balanced)
    defensive_adjustment: Decimal = Decimal("0.08")  # Reduced from 0.15


@dataclass(frozen=True)
class NuclearConfidenceConfig:
    """Nuclear strategy confidence calculation parameters."""

    # Base confidence levels (standardized range)
    base_confidence: Decimal = Decimal("0.60")  # Increased from 0.50 for consistency
    max_confidence: Decimal = Decimal("0.90")
    min_confidence: Decimal = Decimal("0.45")  # Increased floor for consistency

    # Indicator-based confidence tiers (more balanced)
    extreme_overbought_confidence: Decimal = Decimal("0.85")  # Reduced from 0.90
    oversold_buy_confidence: Decimal = Decimal("0.80")  # Reduced from 0.85
    volatility_hedge_confidence: Decimal = Decimal("0.75")  # Reduced from 0.80
    market_regime_confidence: Decimal = Decimal("0.70")
    hold_confidence: Decimal = Decimal("0.50")  # Reduced from 0.60

    # RSI thresholds for confidence tiers (standardized with TECL)
    rsi_extreme_overbought: Decimal = Decimal("80.0")  # Reduced from 85.0
    rsi_oversold: Decimal = Decimal("25.0")
    rsi_moderate_overbought: Decimal = Decimal("70.0")  # Reduced from 75.0
    rsi_moderate_oversold: Decimal = Decimal("35.0")


@dataclass(frozen=True)
class KLMConfidenceConfig:
    """KLM strategy confidence calculation parameters."""

    # Base confidence levels (more balanced approach)
    base_confidence: Decimal = Decimal("0.60")  # Consistent with TECL base
    max_confidence: Decimal = Decimal("0.90")
    min_confidence: Decimal = Decimal("0.45")  # Higher floor than before

    # Weight-based adjustments (much gentler scaling)
    weight_adjustment_factor: Decimal = Decimal("0.15")  # Reduced from 0.40
    high_weight_threshold: Decimal = Decimal("0.75")  # Weight > 75% = high confidence
    high_weight_boost: Decimal = Decimal("0.05")  # +0.05 for high weight positions

    # Action-based modifiers
    sell_confidence: Decimal = Decimal("0.70")
    hold_confidence: Decimal = Decimal("0.45")  # Increased from 0.30


@dataclass(frozen=True)
class AggregationConfig:
    """Configuration for signal aggregation and conflict resolution.

    Confidence is only used for weighting between strategies during conflict resolution.
    High confidence strategies get up to 10% additional weighting vs low confidence.
    """

    # Tie-breaking priority order (first = highest priority)
    strategy_priority: ClassVar[list[str]] = ["NUCLEAR", "TECL", "KLM"]

    # Whether to blend allocations when strategies agree (conservative: False)
    blend_agreeing_allocations: bool = False

    # Maximum confidence-based weight adjustment (10% boost/reduction)
    max_confidence_weight_adjustment: Decimal = Decimal("0.10")


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
