#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Consolidated portfolio schemas for inter-module communication.

Provides typed schemas for consolidated portfolio allocation data from strategy
signal aggregation, ensuring type safety in orchestrator communication.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..utils.timezone_utils import ensure_timezone_aware


class ConsolidatedPortfolio(BaseModel):
    """Schema for consolidated portfolio allocation from multiple strategies.

    Contains aggregated target allocations from strategy signals with
    correlation tracking and metadata for orchestrator communication.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Core allocation data
    target_allocations: dict[str, Decimal] = Field(
        ..., description="Target allocation weights by symbol (symbol -> weight 0-1)"
    )

    # Correlation tracking
    correlation_id: str = Field(
        ..., min_length=1, max_length=100, description="Correlation ID for tracking"
    )

    # Metadata
    timestamp: datetime = Field(..., description="When the consolidation was performed")
    strategy_count: int = Field(..., ge=1, description="Number of strategies that contributed")
    source_strategies: list[str] = Field(
        default_factory=list, description="Names of contributing strategies"
    )

    # Optional context
    constraints: dict[str, Any] | None = Field(
        default=None, description="Optional consolidation constraints and metadata"
    )

    @field_validator("target_allocations")
    @classmethod
    def validate_allocations(cls, v: dict[str, Decimal]) -> dict[str, Decimal]:
        """Validate target allocations."""
        if not v:
            raise ValueError("target_allocations cannot be empty")

        # Normalize symbols to uppercase and validate weights
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
            raise ValueError(f"Total allocations must sum to ~1.0, got {total_weight}")

        return normalized

    @field_validator("correlation_id")
    @classmethod
    def validate_correlation_id(cls, v: str) -> str:
        """Validate correlation ID format."""
        v = v.strip()
        if not v:
            raise ValueError("correlation_id cannot be empty")
        return v

    @field_validator("timestamp")
    @classmethod
    def ensure_timezone_aware_timestamp(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware."""
        result = ensure_timezone_aware(v)
        if result is None:
            raise ValueError("timestamp cannot be None")
        return result

    @field_validator("source_strategies")
    @classmethod
    def validate_strategies(cls, v: list[str]) -> list[str]:
        """Validate and normalize strategy names."""
        return [strategy.strip() for strategy in v if strategy.strip()]

    @classmethod
    def from_dict_allocation(
        cls,
        allocation_dict: dict[str, float],
        correlation_id: str,
        source_strategies: list[str] | None = None,
    ) -> ConsolidatedPortfolio:
        """Create DTO from dict allocation data.

        Args:
            allocation_dict: Dictionary of symbol -> weight allocations
            correlation_id: Correlation ID for tracking
            source_strategies: Optional list of contributing strategy names

        Returns:
            ConsolidatedPortfolio instance

        Raises:
            ValueError: If allocation data is invalid

        """
        # Convert float allocations to Decimal
        target_allocations = {
            symbol: Decimal(str(weight)) for symbol, weight in allocation_dict.items()
        }

        return cls(
            target_allocations=target_allocations,
            correlation_id=correlation_id,
            timestamp=datetime.now(UTC),
            strategy_count=len(source_strategies) if source_strategies else 1,
            source_strategies=source_strategies or [],
        )

    def to_dict_allocation(self) -> dict[str, float]:
        """Convert to simple dict allocation format for backward compatibility.

        Returns:
            Dictionary of symbol -> weight as floats

        """
        return {symbol: float(weight) for symbol, weight in self.target_allocations.items()}
