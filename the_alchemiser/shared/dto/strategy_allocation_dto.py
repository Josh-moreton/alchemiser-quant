#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Strategy allocation data transfer objects for inter-module communication.

Provides typed DTOs for strategy allocation plans with correlation tracking
and serialization helpers for communication between strategy and portfolio modules.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..utils.timezone_utils import ensure_timezone_aware


class StrategyAllocationDTO(BaseModel):
    """DTO for strategy allocation plan.

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
            raise ValueError("target_weights cannot be empty")

        # Normalize symbols to uppercase
        normalized = {}
        total_weight = Decimal("0")

        for symbol, weight in v.items():
            if not symbol or not isinstance(symbol, str):
                raise ValueError(f"Invalid symbol: {symbol}")

            symbol_upper = symbol.strip().upper()
            if symbol_upper in normalized:
                raise ValueError(f"Duplicate symbol: {symbol_upper}")

            if weight < 0 or weight > 1:
                raise ValueError(f"Weight for {symbol_upper} must be between 0 and 1, got {weight}")

            normalized[symbol_upper] = weight
            total_weight += weight

        # Allow small tolerance for weight sum (common with floating point conversions)
        if not (Decimal("0.99") <= total_weight <= Decimal("1.01")):
            raise ValueError(f"Total weights must sum to ~1.0, got {total_weight}")

        return normalized

    @field_validator("correlation_id")
    @classmethod
    def validate_correlation_id(cls, v: str) -> str:
        """Validate correlation ID format."""
        v = v.strip()
        if not v:
            raise ValueError("correlation_id cannot be empty")
        return v

    @field_validator("as_of")
    @classmethod
    def ensure_timezone_aware_as_of(cls, v: datetime | None) -> datetime | None:
        """Ensure as_of timestamp is timezone-aware."""
        if v is None:
            return None
        return ensure_timezone_aware(v)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StrategyAllocationDTO:
        """Create DTO from dictionary with type conversion.

        Args:
            data: Dictionary containing DTO fields

        Returns:
            StrategyAllocationDTO instance

        Raises:
            ValueError: If data is invalid or cannot be converted

        """
        converted_data = data.copy()

        # Convert target weights
        if "target_weights" in converted_data:
            converted_data["target_weights"] = cls._convert_target_weights(
                converted_data["target_weights"]
            )

        # Convert portfolio value
        if "portfolio_value" in converted_data:
            converted_data["portfolio_value"] = cls._convert_portfolio_value(
                converted_data["portfolio_value"]
            )

        return cls(**converted_data)

    @classmethod
    def _convert_target_weights(
        cls, weights_data: dict[str, float | Decimal | int | str]
    ) -> dict[str, Decimal]:
        """Convert target weights to Decimal format."""
        if not isinstance(weights_data, dict):
            return weights_data

        converted_weights = {}
        for symbol, weight in weights_data.items():
            try:
                if isinstance(weight, str):
                    converted_weights[symbol] = Decimal(weight)
                else:
                    converted_weights[symbol] = Decimal(str(weight))
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid weight value for {symbol}: {weight}") from e

        return converted_weights

    @classmethod
    def _convert_portfolio_value(
        cls, portfolio_value: float | Decimal | int | str | None
    ) -> Decimal | None:
        """Convert portfolio value to Decimal if needed."""
        if portfolio_value is None:
            return None

        if not isinstance(portfolio_value, str):
            return Decimal(portfolio_value)

        try:
            return Decimal(portfolio_value)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid portfolio_value: {portfolio_value}") from e
