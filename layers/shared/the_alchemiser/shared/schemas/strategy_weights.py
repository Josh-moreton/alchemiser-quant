"""Business Unit: shared | Status: current.

Strategy weights schemas for Calmar-tilted capital allocation.

This module provides DTOs for managing strategy weights with Calmar ratio
adjustments, base weights, and live weights for dynamic capital allocation.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..constants import CONTRACT_VERSION
from ..utils.timezone_utils import ensure_timezone_aware


class CalmarMetrics(BaseModel):
    """DTO for Calmar ratio metrics per strategy.
    
    Contains 12-month rolling return and max drawdown for Calmar calculation.
    Supports partial month data for gradual buildup from starter values.
    """

    __schema_version__: str = CONTRACT_VERSION

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    strategy_name: str = Field(..., min_length=1, description="Strategy identifier (DSL file name)")
    twelve_month_return: Decimal = Field(
        ..., description="12-month annualized return (as decimal, e.g., 0.15 = 15%)"
    )
    twelve_month_max_drawdown: Decimal = Field(
        ..., gt=0, description="12-month max drawdown (as positive decimal, e.g., 0.10 = 10%)"
    )
    calmar_ratio: Decimal = Field(..., description="Calmar ratio (return / max_drawdown)")
    months_of_data: int = Field(
        default=12,
        ge=1,
        le=12,
        description="Number of months of actual data (1-12, for gradual buildup)",
    )
    as_of: datetime = Field(..., description="Timestamp when metrics were calculated")

    @field_validator("as_of")
    @classmethod
    def ensure_timezone_aware_as_of(cls, v: datetime) -> datetime:
        """Ensure as_of timestamp is timezone-aware."""
        return ensure_timezone_aware(v)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CalmarMetrics:
        """Create DTO from dictionary with type conversion.
        
        Args:
            data: Dictionary containing DTO fields
            
        Returns:
            CalmarMetrics instance
        """
        converted_data = data.copy()

        # Convert numeric fields to Decimal
        for field in ["twelve_month_return", "twelve_month_max_drawdown", "calmar_ratio"]:
            if field in converted_data:
                converted_data[field] = Decimal(str(converted_data[field]))

        return cls(**converted_data)


class StrategyWeights(BaseModel):
    """DTO for strategy weight allocation with Calmar-tilted adjustments.
    
    Stores base weights (from strategy.prod.json), target weights (Calmar-tilted),
    and realized weights (with partial adjustment smoothing).
    """

    __schema_version__: str = CONTRACT_VERSION

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    version: str = Field(..., min_length=1, description="Version identifier (e.g., 'v1', 'v2')")
    base_weights: dict[str, Decimal] = Field(
        ..., description="Base weights from strategy.prod.json (sum = 1.0)"
    )
    target_weights: dict[str, Decimal] = Field(
        ..., description="Target weights after Calmar tilt (sum = 1.0)"
    )
    realized_weights: dict[str, Decimal] = Field(
        ..., description="Realized weights after partial adjustment (sum = 1.0)"
    )
    calmar_metrics: dict[str, CalmarMetrics] = Field(
        default_factory=dict, description="Calmar metrics by strategy name"
    )
    adjustment_lambda: Decimal = Field(
        default=Decimal("0.1"),
        ge=0,
        le=1,
        description="Partial adjustment rate (0.1-0.25 recommended)",
    )
    rebalance_frequency_days: int = Field(
        default=30, ge=7, description="Days between weight rebalances (default: monthly)"
    )
    last_rebalance: datetime | None = Field(
        default=None, description="Timestamp of last weight rebalance"
    )
    next_rebalance: datetime | None = Field(
        default=None, description="Timestamp of next scheduled rebalance"
    )
    created_at: datetime = Field(..., description="Timestamp when weights were created")
    updated_at: datetime = Field(..., description="Timestamp when weights were last updated")

    @field_validator("base_weights", "target_weights", "realized_weights")
    @classmethod
    def validate_weights_sum(cls, v: dict[str, Decimal]) -> dict[str, Decimal]:
        """Validate that weights sum to approximately 1.0."""
        total = sum(v.values())
        # Allow small tolerance for floating point conversions
        if not (Decimal("0.99") <= total <= Decimal("1.01")):
            raise ValueError(f"Weights must sum to ~1.0, got {total}")
        return v

    @field_validator("last_rebalance", "next_rebalance", "created_at", "updated_at")
    @classmethod
    def ensure_timezone_aware_timestamps(cls, v: datetime | None) -> datetime | None:
        """Ensure timestamps are timezone-aware."""
        if v is None:
            return None
        return ensure_timezone_aware(v)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StrategyWeights:
        """Create DTO from dictionary with type conversion.
        
        Args:
            data: Dictionary containing DTO fields
            
        Returns:
            StrategyWeights instance
        """
        converted_data = data.copy()

        # Convert weight dictionaries to Decimal
        for field in ["base_weights", "target_weights", "realized_weights"]:
            if field in converted_data:
                converted_data[field] = {
                    k: Decimal(str(v)) for k, v in converted_data[field].items()
                }

        # Convert adjustment_lambda
        if "adjustment_lambda" in converted_data:
            converted_data["adjustment_lambda"] = Decimal(str(converted_data["adjustment_lambda"]))

        # Convert nested calmar_metrics
        if "calmar_metrics" in converted_data and isinstance(converted_data["calmar_metrics"], dict):
            converted_data["calmar_metrics"] = {
                k: CalmarMetrics.from_dict(v) if isinstance(v, dict) else v
                for k, v in converted_data["calmar_metrics"].items()
            }

        return cls(**converted_data)


class StrategyWeightsHistory(BaseModel):
    """DTO for historical strategy weight records.
    
    Used for audit trail and analysis of weight adjustments over time.
    """

    __schema_version__: str = CONTRACT_VERSION

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    version: str = Field(..., min_length=1, description="Version identifier")
    weights: StrategyWeights = Field(..., description="Weight snapshot at this version")
    reason: str = Field(
        ..., min_length=1, description="Reason for weight adjustment (e.g., 'monthly_rebalance')"
    )
    correlation_id: str = Field(
        ..., min_length=1, description="Correlation ID for traceability"
    )
    created_at: datetime = Field(..., description="Timestamp when snapshot was created")

    @field_validator("created_at")
    @classmethod
    def ensure_timezone_aware_created_at(cls, v: datetime) -> datetime:
        """Ensure created_at timestamp is timezone-aware."""
        return ensure_timezone_aware(v)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StrategyWeightsHistory:
        """Create DTO from dictionary with type conversion.
        
        Args:
            data: Dictionary containing DTO fields
            
        Returns:
            StrategyWeightsHistory instance
        """
        converted_data = data.copy()

        # Convert nested weights
        if "weights" in converted_data and isinstance(converted_data["weights"], dict):
            converted_data["weights"] = StrategyWeights.from_dict(converted_data["weights"])

        return cls(**converted_data)
