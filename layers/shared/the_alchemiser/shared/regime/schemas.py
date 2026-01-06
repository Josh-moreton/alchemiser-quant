"""Business Unit: shared | Status: current.

Frozen DTOs for market regime detection and strategy weighting.

These schemas define the data structures for HMM-based regime classification
and per-regime strategy weight adjustments. All schemas are frozen (immutable)
for thread safety and deterministic behavior.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RegimeType(str, Enum):
    """Market regime classification types.

    The HMM classifier identifies these regimes based on SPY features:
    - RISK_ON: Bullish market with >60% probability in uptrend state
    - RISK_OFF: Bearish market with >60% probability in downtrend state
    - RECOVERY: High volatility but improving returns (Risk-Off transitioning up)
    - PIVOT_PLUS: Transitioning from Risk-Off to Risk-On (40-60% probability)
    - PIVOT_MINUS: Transitioning from Risk-On to Risk-Off (40-60% probability)
    """

    RISK_ON = "Risk-On"
    RISK_OFF = "Risk-Off"
    RECOVERY = "Recovery"
    PIVOT_PLUS = "Pivot+"
    PIVOT_MINUS = "Pivot-"


class RegimeState(BaseModel):
    """Current market regime state from HMM classifier.

    This DTO is stored in DynamoDB by the regime detector Lambda and
    read by the Strategy Orchestrator to adjust allocations.

    Attributes:
        regime: Current classified regime type
        probability: Confidence probability for the regime (0.0-1.0)
        bull_probability: Probability of bullish state from HMM
        timestamp: When this regime was classified
        spy_close: SPY closing price used for classification
        lookback_days: Number of days used for HMM features
        model_score: Log-likelihood score of the fitted HMM model

    """

    model_config = ConfigDict(strict=True, frozen=True)

    regime: RegimeType = Field(description="Current market regime classification")
    probability: Decimal = Field(
        ge=Decimal("0.0"),
        le=Decimal("1.0"),
        description="Confidence probability for this regime",
    )
    bull_probability: Decimal = Field(
        ge=Decimal("0.0"),
        le=Decimal("1.0"),
        description="Raw probability of bullish HMM state",
    )
    timestamp: datetime = Field(description="Regime classification timestamp")
    spy_close: Decimal = Field(description="SPY closing price at classification time")
    lookback_days: int = Field(
        default=20, ge=1, description="Lookback window for HMM features"
    )
    model_score: Decimal | None = Field(
        default=None, description="HMM log-likelihood score (optional)"
    )
    schema_version: str = Field(default="1.0.0", description="Schema version for evolution")

    @field_validator("probability", "bull_probability", "spy_close", mode="before")
    @classmethod
    def _coerce_to_decimal(cls, v: Any) -> Decimal:
        """Coerce numeric values to Decimal."""
        if isinstance(v, Decimal):
            return v
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return Decimal(str(v))

    @field_validator("model_score", mode="before")
    @classmethod
    def _coerce_optional_decimal(cls, v: Any) -> Decimal | None:
        """Coerce optional numeric values to Decimal."""
        if v is None:
            return None
        if isinstance(v, Decimal):
            return v
        if isinstance(v, (int, float)):
            return Decimal(str(v))
        return Decimal(str(v))


class StrategyRegimeMetrics(BaseModel):
    """Per-regime performance metrics for a single strategy.

    Contains historical Sharpe ratios and suggested weight multipliers
    for each regime type. Used to adjust strategy allocations.

    Attributes:
        strategy_file: DSL strategy filename (e.g., 'simons_kmlm.clj')
        sharpe_by_regime: Historical Sharpe ratio in each regime
        weight_multiplier_by_regime: Weight multiplier for each regime (1.0 = no change)
        sample_days_by_regime: Number of days in each regime for Sharpe calculation

    """

    model_config = ConfigDict(strict=True, frozen=True)

    strategy_file: str = Field(description="DSL strategy filename")
    sharpe_by_regime: dict[RegimeType, Decimal] = Field(
        default_factory=dict,
        description="Historical Sharpe ratio per regime",
    )
    weight_multiplier_by_regime: dict[RegimeType, Decimal] = Field(
        default_factory=dict,
        description="Weight multiplier per regime (1.0 = no change)",
    )
    sample_days_by_regime: dict[RegimeType, int] = Field(
        default_factory=dict,
        description="Number of sample days per regime",
    )
    schema_version: str = Field(default="1.0.0", description="Schema version")

    @field_validator("sharpe_by_regime", "weight_multiplier_by_regime", mode="before")
    @classmethod
    def _coerce_dict_values_to_decimal(
        cls, v: dict[str, Any] | None
    ) -> dict[RegimeType, Decimal]:
        """Convert dict values to Decimal and keys to RegimeType."""
        if v is None:
            return {}
        result: dict[RegimeType, Decimal] = {}
        for key, val in v.items():
            regime_key = RegimeType(key) if isinstance(key, str) else key
            decimal_val = Decimal(str(val)) if not isinstance(val, Decimal) else val
            result[regime_key] = decimal_val
        return result

    @field_validator("sample_days_by_regime", mode="before")
    @classmethod
    def _coerce_sample_days(cls, v: dict[str, Any] | None) -> dict[RegimeType, int]:
        """Convert dict keys to RegimeType."""
        if v is None:
            return {}
        result: dict[RegimeType, int] = {}
        for key, val in v.items():
            regime_key = RegimeType(key) if isinstance(key, str) else key
            result[regime_key] = int(val)
        return result


class RegimeWeightConfig(BaseModel):
    """Configuration for regime-based weight adjustment.

    Contains all strategy metrics and adjustment parameters.

    Attributes:
        strategies: Per-strategy regime metrics
        adjustment_method: How to adjust weights ('sharpe_weighted', 'multiplier', 'hybrid')
        min_weight: Minimum weight for any strategy (prevents zero allocation)
        max_weight: Maximum weight for any strategy (prevents concentration)
        sharpe_floor: Minimum Sharpe to consider (below = zero weight)
        enable_regime_adjustment: Master switch to enable/disable regime weighting

    """

    model_config = ConfigDict(strict=True, frozen=True)

    strategies: dict[str, StrategyRegimeMetrics] = Field(
        default_factory=dict,
        description="Per-strategy regime metrics keyed by filename",
    )
    adjustment_method: str = Field(
        default="sharpe_weighted",
        description="Weight adjustment method: sharpe_weighted, multiplier, hybrid",
    )
    min_weight: Decimal = Field(
        default=Decimal("0.02"),
        ge=Decimal("0.0"),
        description="Minimum weight for any strategy (2% default)",
    )
    max_weight: Decimal = Field(
        default=Decimal("0.40"),
        le=Decimal("1.0"),
        description="Maximum weight for any strategy (40% default)",
    )
    sharpe_floor: Decimal = Field(
        default=Decimal("0.0"),
        description="Minimum Sharpe ratio; below this = zero weight",
    )
    enable_regime_adjustment: bool = Field(
        default=True,
        description="Master switch to enable regime-based weight adjustment",
    )
    schema_version: str = Field(default="1.0.0", description="Schema version")

    @field_validator("min_weight", "max_weight", "sharpe_floor", mode="before")
    @classmethod
    def _coerce_to_decimal(cls, v: Any) -> Decimal:
        """Coerce numeric values to Decimal."""
        if isinstance(v, Decimal):
            return v
        return Decimal(str(v))
