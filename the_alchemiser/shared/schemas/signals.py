#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Strategy signal schemas for inter-module communication.

Provides typed schemas for strategy signals with correlation tracking and
serialization helpers for communication between strategy and portfolio modules.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..utils.timezone_utils import ensure_timezone_aware


class StrategySignal(BaseModel):
    """Schema for strategy signal data transfer.

    Used for communication between strategy and portfolio modules.
    Includes correlation tracking and serialization helpers.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Required correlation fields
    correlation_id: str = Field(..., min_length=1, description="Unique correlation identifier")
    causation_id: str = Field(
        ..., min_length=1, description="Causation identifier for traceability"
    )
    timestamp: datetime = Field(..., description="Signal generation timestamp")

    # Signal identification
    signal_id: str = Field(..., min_length=1, description="Unique signal identifier")
    strategy_name: str = Field(..., min_length=1, description="Strategy that generated the signal")
    signal_type: str = Field(..., min_length=1, description="Type of signal (BUY, SELL, HOLD)")

    # Signal data
    symbol: str = Field(..., min_length=1, max_length=10, description="Trading symbol")
    confidence: Decimal = Field(..., ge=0, le=1, description="Signal confidence (0-1)")
    strength: Decimal = Field(..., ge=0, le=1, description="Signal strength (0-1)")
    target_weight: Decimal | None = Field(
        default=None, ge=0, le=1, description="Target portfolio weight (0-1)"
    )

    # Optional signal metadata
    price_target: Decimal | None = Field(default=None, ge=0, description="Price target if available")
    time_horizon: str | None = Field(default=None, description="Expected time horizon")
    risk_level: str | None = Field(default=None, description="Risk level assessment")

    # Signal context
    market_conditions: dict[str, Any] = Field(
        default_factory=dict, description="Market conditions when signal was generated"
    )
    technical_indicators: dict[str, Any] = Field(
        default_factory=dict, description="Technical indicators supporting the signal"
    )

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        """Normalize symbol to uppercase."""
        return v.strip().upper()

    @field_validator("signal_type")
    @classmethod
    def normalize_signal_type(cls, v: str) -> str:
        """Normalize signal type to uppercase."""
        return v.strip().upper()

    @field_validator("timestamp")
    @classmethod
    def ensure_timezone_aware_timestamp(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware."""
        return ensure_timezone_aware(v)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StrategySignal:
        """Create StrategySignal from dictionary data with type conversion.

        Args:
            data: Dictionary containing signal data

        Returns:
            StrategySignal instance with properly typed fields

        """
        # Create a copy to avoid mutating the original
        processed_data = data.copy()

        # Convert datetime fields from strings if needed
        if "timestamp" in processed_data and isinstance(processed_data["timestamp"], str):
            processed_data["timestamp"] = datetime.fromisoformat(processed_data["timestamp"])

        # Convert decimal fields from strings if needed
        decimal_fields = ["confidence", "strength", "target_weight", "price_target"]
        for field_name in decimal_fields:
            if (
                field_name in processed_data
                and processed_data[field_name] is not None
                and isinstance(processed_data[field_name], str)
            ):
                processed_data[field_name] = Decimal(processed_data[field_name])

        return cls(**processed_data)

    def to_dict(self) -> dict[str, Any]:
        """Convert schema to dictionary for serialization.

        Returns:
            Dictionary representation with properly serialized values.

        """
        data = self.model_dump()

        # Convert datetime to ISO string
        if data.get("timestamp"):
            data["timestamp"] = data["timestamp"].isoformat()

        # Convert decimals to strings
        decimal_fields = ["confidence", "strength", "target_weight", "price_target"]
        for field_name in decimal_fields:
            if data.get(field_name) is not None:
                data[field_name] = str(data[field_name])

        return data