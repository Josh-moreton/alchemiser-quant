#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Strategy signal data transfer objects for inter-module communication.

Provides typed DTOs for strategy signals with correlation tracking and
serialization helpers for communication between strategy and portfolio modules.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrategySignalDTO(BaseModel):
    """DTO for strategy signal data transfer.

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
    causation_id: str = Field(..., min_length=1, description="Causation identifier for traceability")
    timestamp: datetime = Field(..., description="Signal generation timestamp")

    # Signal fields
    symbol: str = Field(..., min_length=1, max_length=10, description="Trading symbol")
    action: str = Field(..., description="Trading action (BUY, SELL, HOLD)")
    confidence: Decimal = Field(..., ge=0, le=1, description="Signal confidence (0-1)")
    reasoning: str = Field(..., min_length=1, description="Human-readable signal reasoning")
    
    # Optional strategy context
    strategy_name: str | None = Field(default=None, description="Strategy that generated the signal")
    allocation_weight: Decimal | None = Field(
        default=None, ge=0, le=1, description="Recommended allocation weight (0-1)"
    )
    
    # Optional signal metadata
    signal_strength: Decimal | None = Field(
        default=None, ge=0, description="Raw signal strength value"
    )
    metadata: dict[str, Any] | None = Field(
        default=None, description="Additional signal metadata"
    )

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        """Normalize symbol to uppercase."""
        return v.strip().upper()

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        """Validate action is supported."""
        valid_actions = {"BUY", "SELL", "HOLD"}
        action_upper = v.strip().upper()
        if action_upper not in valid_actions:
            raise ValueError(f"Action must be one of {valid_actions}, got {action_upper}")
        return action_upper

    @field_validator("timestamp")
    @classmethod
    def ensure_timezone_aware(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware."""
        if v.tzinfo is None:
            return v.replace(tzinfo=UTC)
        return v

    def to_dict(self) -> dict[str, Any]:
        """Convert DTO to dictionary for serialization.
        
        Returns:
            Dictionary representation of the DTO with properly serialized values.

        """
        data = self.model_dump()
        
        # Convert datetime to ISO string
        if self.timestamp:
            data["timestamp"] = self.timestamp.isoformat()
            
        # Convert Decimal fields to string for JSON serialization
        for field_name in ["confidence", "allocation_weight", "signal_strength"]:
            if data.get(field_name) is not None:
                data[field_name] = str(data[field_name])
                
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StrategySignalDTO:
        """Create DTO from dictionary.
        
        Args:
            data: Dictionary containing DTO data
            
        Returns:
            StrategySignalDTO instance
            
        Raises:
            ValueError: If data is invalid or missing required fields

        """
        # Convert string timestamp back to datetime
        if "timestamp" in data and isinstance(data["timestamp"], str):
            try:
                # Handle both ISO format and other common formats
                timestamp_str = data["timestamp"]
                if timestamp_str.endswith("Z"):
                    timestamp_str = timestamp_str[:-1] + "+00:00"
                data["timestamp"] = datetime.fromisoformat(timestamp_str)
            except ValueError as e:
                raise ValueError(f"Invalid timestamp format: {data['timestamp']}") from e
                
        # Convert string decimal fields back to Decimal
        for field_name in ["confidence", "allocation_weight", "signal_strength"]:
            if field_name in data and data[field_name] is not None and isinstance(data[field_name], str):
                try:
                    data[field_name] = Decimal(data[field_name])
                except (ValueError, TypeError) as e:
                    raise ValueError(f"Invalid {field_name} value: {data[field_name]}") from e
                        
        return cls(**data)