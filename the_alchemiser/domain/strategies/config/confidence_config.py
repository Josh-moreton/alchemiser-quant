"""
Typed configuration for strategy confidence calculations.

This module provides configurable parameters for confidence calculations across
all strategy engines, replacing hardcoded constants with validated, type-safe configuration.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class TECLConfidenceConfig:
    """Configuration for TECL strategy confidence calculation."""

    # Base confidence levels
    base_confidence: Decimal = Decimal("0.6")
    max_confidence: Decimal = Decimal("0.9")
    min_confidence: Decimal = Decimal("0.3")

    # RSI-based adjustments
    rsi_oversold_threshold: Decimal = Decimal("30")
    rsi_overbought_threshold: Decimal = Decimal("70")
    rsi_confidence_weight: Decimal = Decimal("0.2")  # Max adjustment from RSI

    # Moving average distance adjustments
    ma_distance_confidence_weight: Decimal = Decimal("0.15")  # Max adjustment from MA distance
    ma_distance_threshold: Decimal = Decimal("0.05")  # 5% distance threshold

    # Volatility adjustments
    volatility_confidence_weight: Decimal = Decimal("0.1")  # Max adjustment from volatility
    high_volatility_threshold: Decimal = Decimal("0.8")  # High volatility RSI threshold

    # Market regime adjustments
    bull_market_bonus: Decimal = Decimal("0.1")
    bear_market_penalty: Decimal = Decimal("0.1")
    defensive_position_penalty: Decimal = Decimal("0.2")


@dataclass(frozen=True)
class NuclearConfidenceConfig:
    """Configuration for Nuclear strategy confidence calculation."""

    # Base confidence levels
    base_confidence: Decimal = Decimal("0.5")
    max_confidence: Decimal = Decimal("0.9")
    min_confidence: Decimal = Decimal("0.3")

    # RSI-based confidence tiers
    extremely_oversold_rsi: Decimal = Decimal("20")
    oversold_rsi: Decimal = Decimal("30")
    overbought_rsi: Decimal = Decimal("70")
    extremely_overbought_rsi: Decimal = Decimal("80")

    # Confidence mappings for RSI conditions
    extremely_oversold_confidence: Decimal = Decimal("0.9")
    oversold_buy_confidence: Decimal = Decimal("0.85")
    overbought_sell_confidence: Decimal = Decimal("0.8")
    extremely_overbought_confidence: Decimal = Decimal("0.9")

    # Market regime confidence adjustments
    bull_market_confidence: Decimal = Decimal("0.7")
    bear_market_confidence: Decimal = Decimal("0.7")
    volatility_hedge_confidence: Decimal = Decimal("0.8")
    hold_confidence: Decimal = Decimal("0.6")

    # Moving average confirmations
    ma_confirmation_bonus: Decimal = Decimal("0.1")
    ma_divergence_penalty: Decimal = Decimal("0.1")


@dataclass(frozen=True)
class KLMConfidenceConfig:
    """Configuration for KLM strategy confidence calculation."""

    # Base confidence levels
    base_confidence: Decimal = Decimal("0.5")
    max_confidence: Decimal = Decimal("0.9")
    min_confidence: Decimal = Decimal("0.3")

    # Action-specific confidence parameters
    buy_base_confidence: Decimal = Decimal("0.5")
    buy_weight_multiplier: Decimal = Decimal("0.4")  # Linear weight influence
    buy_max_confidence: Decimal = Decimal("0.9")

    sell_confidence: Decimal = Decimal("0.7")
    hold_confidence: Decimal = Decimal("0.3")

    # Weight-based confidence curve parameters
    weight_confidence_curve: str = "linear"  # "linear" or "logistic"
    logistic_steepness: Decimal = Decimal("2.0")  # For logistic curve
    weight_threshold: Decimal = Decimal("0.1")  # Minimum weight for confidence bonus


@dataclass(frozen=True)
class AggregationConfig:
    """Configuration for strategy signal aggregation and conflict resolution."""

    # Minimum confidence thresholds for actions
    min_buy_confidence: Decimal = Decimal("0.55")
    min_sell_confidence: Decimal = Decimal("0.55")
    min_hold_confidence: Decimal = Decimal("0.35")

    # Tie-breaking preferences (ordered by priority)
    strategy_priority_order: tuple[str, ...] = ("NUCLEAR", "TECL", "KLM")

    # Allocation blending settings
    enable_allocation_blending: bool = False  # Feature flag for blended allocations

    # Conflict resolution settings
    enable_confidence_gating: bool = True  # Gate signals below minimum thresholds
    log_detailed_scores: bool = True  # Log detailed scoring for diagnostics


@dataclass(frozen=True)
class ConfidenceConfig:
    """Master configuration for all strategy confidence calculations."""

    tecl: TECLConfidenceConfig = TECLConfidenceConfig()
    nuclear: NuclearConfidenceConfig = NuclearConfidenceConfig()
    klm: KLMConfidenceConfig = KLMConfidenceConfig()
    aggregation: AggregationConfig = AggregationConfig()


def load_confidence_config() -> ConfidenceConfig:
    """
    Load confidence configuration from environment variables with fallback to defaults.
    
    Environment variable format: CONFIDENCE_<STRATEGY>_<PARAMETER>
    Example: CONFIDENCE_TECL_BASE_CONFIDENCE=0.65
    """
    # For now, return defaults. In the future, this can be extended to read from env vars
    # and validate the configuration against business rules
    return ConfidenceConfig()


def get_confidence_thresholds() -> dict[str, Decimal]:
    """Get minimum confidence thresholds by action for validation."""
    config = load_confidence_config()
    return {
        "BUY": config.aggregation.min_buy_confidence,
        "SELL": config.aggregation.min_sell_confidence,
        "HOLD": config.aggregation.min_hold_confidence,
    }
