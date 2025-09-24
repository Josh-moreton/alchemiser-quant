#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Strategy allocation schemas for inter-module communication.

Provides typed schemas for strategy allocation plans with correlation tracking
and serialization helpers for communication between strategy and portfolio modules.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..utils.timezone_utils import ensure_timezone_aware


class StrategyAllocation(BaseModel):
    """Schema for strategy allocation plan.

    Contains target weights for portfolio rebalancing with optional constraints
    and metadata for correlation tracking.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    target_weights: dict[str, Decimal] = Field(
        ..., description="Target allocation weights by symbol (symbol -> weight 0-1)"
    )
    portfolio_value: Decimal | None = Field(
        default=None,
        ge=0,
        description="Optional portfolio value; if None, compute from snapshot",
    )
    correlation_id: str = Field(
        ..., min_length=1, max_length=100, description="Correlation ID for tracking"
    )
    as_of: datetime | None = Field(
        default=None, description="Optional timestamp when allocation was calculated"
    )
    constraints: dict[str, Any] | None = Field(
        default=None, description="Optional allocation constraints and metadata"
    )

    @field_validator("target_weights")
    @classmethod
    def validate_weights(cls, v: dict[str, Decimal]) -> dict[str, Decimal]:
        """Validate target weights."""
        if not v:
            msg = "target_weights cannot be empty"
            raise ValueError(msg)

        # Normalize symbols to uppercase
        normalized = {}
        for symbol, weight in v.items():
            symbol_key = symbol.strip().upper()
            if symbol_key in normalized:
                msg = f"Duplicate symbol after normalization: {symbol_key}"
                raise ValueError(msg)
            if weight < 0 or weight > 1:
                msg = f"Weight for {symbol_key} must be between 0 and 1, got {weight}"
                raise ValueError(msg)
            normalized[symbol_key] = weight

        # Check total weight doesn't exceed 1.0 (allowing slight precision error)
        total_weight = sum(normalized.values())
        if total_weight > Decimal("1.01"):
            msg = f"Total weight {total_weight} exceeds 1.0"
            raise ValueError(msg)

        return normalized

    @field_validator("as_of")
    @classmethod
    def ensure_timezone_aware_as_of(cls, v: datetime | None) -> datetime | None:
        """Ensure as_of timestamp is timezone-aware."""
        return ensure_timezone_aware(v)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StrategyAllocation:
        """Create StrategyAllocation from dictionary data with type conversion.

        Args:
            data: Dictionary containing allocation data

        Returns:
            StrategyAllocation instance with properly typed fields

        """
        # Create a copy to avoid mutating the original
        processed_data = data.copy()

        # Convert target_weights from string decimals if needed
        if "target_weights" in processed_data:
            weights = processed_data["target_weights"]
            if isinstance(weights, dict):
                processed_weights = {}
                for symbol, weight in weights.items():
                    if isinstance(weight, str):
                        processed_weights[symbol] = Decimal(weight)
                    else:
                        processed_weights[symbol] = weight
                processed_data["target_weights"] = processed_weights

        # Convert portfolio_value from string if needed
        if (
            "portfolio_value" in processed_data
            and processed_data["portfolio_value"] is not None
            and isinstance(processed_data["portfolio_value"], str)
        ):
            processed_data["portfolio_value"] = Decimal(processed_data["portfolio_value"])

        # Convert as_of from string if needed
        if (
            "as_of" in processed_data
            and processed_data["as_of"] is not None
            and isinstance(processed_data["as_of"], str)
        ):
            processed_data["as_of"] = datetime.fromisoformat(processed_data["as_of"])

        return cls(**processed_data)

    def to_dict(self) -> dict[str, Any]:
        """Convert schema to dictionary for serialization.

        Returns:
            Dictionary representation with properly serialized values.

        """
        data = self.model_dump()

        # Convert target_weights decimals to strings
        if data.get("target_weights"):
            weights = {}
            for symbol, weight in data["target_weights"].items():
                weights[symbol] = str(weight)
            data["target_weights"] = weights

        # Convert portfolio_value to string
        if data.get("portfolio_value") is not None:
            data["portfolio_value"] = str(data["portfolio_value"])

        # Convert as_of to ISO string
        if data.get("as_of"):
            data["as_of"] = data["as_of"].isoformat()

        return data