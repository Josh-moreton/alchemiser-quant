#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Strategy signal data transfer objects for inter-module communication.

Canonical StrategySignal DTO combining best practices:
- Strong typing (Literal, Symbol) for type safety
- Event-driven fields (correlation_id, causation_id) for traceability
- Schema versioning for event evolution
- Comprehensive validation and documentation

This is the canonical definition. The version in shared/types/strategy_value_objects.py
is deprecated and will be removed in a future release.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..types.percentage import Percentage
from ..utils.timezone_utils import ensure_timezone_aware
from ..value_objects.symbol import Symbol

# Type alias for valid trading actions
ActionLiteral = Literal["BUY", "SELL", "HOLD"]


class StrategySignal(BaseModel):
    """DTO for strategy signal data transfer (v1.0).

    Used for communication between strategy and portfolio modules in event-driven architecture.
    Includes correlation tracking, serialization helpers, and schema versioning.

    Schema Version: 1.0 (introduced 2025-01-07)

    Attributes:
        schema_version: DTO schema version for evolution tracking
        correlation_id: Unique correlation identifier for event tracing
        causation_id: Causation identifier for traceability
        timestamp: Signal generation timestamp (timezone-aware UTC)
        symbol: Trading symbol (e.g., "AAPL", "SPY")
        action: Trading action (BUY, SELL, or HOLD)
        reasoning: Human-readable explanation for the signal (max 1000 chars)
        strategy_name: Optional strategy identifier
        target_allocation: Optional target portfolio allocation (0.0-1.0)
        signal_strength: Optional raw signal strength value (≥ 0)
        metadata: Optional additional signal metadata

    Examples:
        >>> from datetime import datetime, UTC
        >>> from decimal import Decimal
        >>> 
        >>> # Minimal signal
        >>> signal = StrategySignal(
        ...     correlation_id="corr-123",
        ...     causation_id="cause-456",
        ...     timestamp=datetime.now(UTC),
        ...     symbol="AAPL",
        ...     action="BUY",
        ...     reasoning="Strong momentum detected"
        ... )
        >>> 
        >>> # Full signal with allocation
        >>> signal = StrategySignal(
        ...     correlation_id="corr-789",
        ...     causation_id="cause-012",
        ...     timestamp=datetime.now(UTC),
        ...     symbol=Symbol("SPY"),
        ...     action="BUY",
        ...     reasoning="Defensive rebalance",
        ...     strategy_name="dsl_momentum",
        ...     target_allocation=Decimal("0.3"),
        ...     signal_strength=Decimal("0.85")
        ... )
        >>> 
        >>> # Serialization round-trip
        >>> data = signal.to_dict()
        >>> restored = StrategySignal.from_dict(data)

    Raises:
        ValidationError: If action is not BUY/SELL/HOLD
        ValidationError: If target_allocation is outside [0, 1]
        ValidationError: If timestamp is timezone-naive
        ValueError: If symbol validation fails

    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Schema versioning
    schema_version: str = Field(
        default="1.0",
        pattern=r"^\d+\.\d+$",
        description="DTO schema version (major.minor)"
    )

    # Required correlation fields
    correlation_id: str = Field(..., min_length=1, description="Unique correlation identifier")
    causation_id: str = Field(
        ..., min_length=1, description="Causation identifier for traceability"
    )
    timestamp: datetime = Field(..., description="Signal generation timestamp")

    # Signal fields (required)
    symbol: Symbol = Field(..., description="Trading symbol")
    action: ActionLiteral = Field(..., description="Trading action (BUY, SELL, HOLD)")
    reasoning: str = Field(..., min_length=1, max_length=1000, description="Human-readable signal reasoning")

    # Optional strategy context
    strategy_name: str | None = Field(
        default=None, description="Strategy that generated the signal"
    )
    target_allocation: Decimal | None = Field(
        default=None, ge=0, le=1, description="Recommended target allocation (0-1)"
    )

    # Optional signal metadata
    signal_strength: Decimal | None = Field(
        default=None, ge=0, description="Raw signal strength value"
    )
    metadata: dict[str, Any] | None = Field(default=None, description="Additional signal metadata")

    @field_validator("symbol", mode="before")
    @classmethod
    def normalize_symbol(cls, v: Symbol | str) -> Symbol:
        """Convert string to Symbol instance.
        
        Args:
            v: Symbol instance or string symbol
            
        Returns:
            Symbol instance (normalized to uppercase)
            
        Raises:
            ValueError: If symbol validation fails
        """
        if isinstance(v, str):
            return Symbol(v.strip().upper())
        return v

    @field_validator("timestamp")
    @classmethod
    def ensure_timezone_aware_timestamp(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware."""
        result = ensure_timezone_aware(v)
        if result is None:
            raise ValueError("timestamp cannot be None")
        return result

    @field_validator("target_allocation", mode="before")
    @classmethod
    def normalize_allocation(cls, v: Decimal | float | int | Percentage | None) -> Decimal | None:
        """Convert allocation to Decimal.
        
        Accepts Decimal, float, int, or Percentage. Converts to Decimal with
        proper precision handling (float -> str -> Decimal to avoid precision loss).
        
        Args:
            v: Allocation value in various formats, or None
            
        Returns:
            Decimal value in range [0, 1], or None
        """
        if v is None:
            return None
        if isinstance(v, Percentage):
            return v.value
        if isinstance(v, (float, int)):
            return Decimal(str(v))
        return v

    def to_dict(self) -> dict[str, Any]:
        """Convert DTO to dictionary for serialization.

        Returns:
            Dictionary representation with ISO timestamps and string Decimals.
            
        Examples:
            >>> signal = StrategySignal(...)
            >>> data = signal.to_dict()
            >>> # data contains serialized values suitable for JSON

        """
        data = self.model_dump()

        # Convert datetime to ISO string
        if self.timestamp:
            data["timestamp"] = self.timestamp.isoformat()

        # Convert Symbol to string
        if isinstance(data.get("symbol"), dict):
            data["symbol"] = data["symbol"]["value"]
        elif hasattr(self.symbol, "value"):
            data["symbol"] = self.symbol.value

        # Convert Decimal fields to string for JSON serialization
        for field_name in ["target_allocation", "signal_strength"]:
            if data.get(field_name) is not None:
                data[field_name] = str(data[field_name])

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StrategySignal:
        """Create DTO from dictionary.

        Args:
            data: Dictionary containing DTO data

        Returns:
            StrategySignal instance

        Raises:
            ValueError: If data is invalid or missing required fields
            
        Examples:
            >>> data = {
            ...     "correlation_id": "corr-123",
            ...     "causation_id": "cause-456",
            ...     "timestamp": "2025-01-07T12:00:00+00:00",
            ...     "symbol": "AAPL",
            ...     "action": "BUY",
            ...     "reasoning": "Test",
            ...     "target_allocation": "0.5"
            ... }
            >>> signal = StrategySignal.from_dict(data)

        """
        # Convert string timestamp back to datetime
        if "timestamp" in data and isinstance(data["timestamp"], str):
            try:
                timestamp_str = data["timestamp"]
                if timestamp_str.endswith("Z"):
                    timestamp_str = timestamp_str[:-1] + "+00:00"
                data["timestamp"] = datetime.fromisoformat(timestamp_str)
            except ValueError as e:
                raise ValueError(f"Invalid timestamp format: {data['timestamp']}") from e

        # Convert string decimal fields back to Decimal
        for field_name in ["target_allocation", "signal_strength"]:
            if (
                field_name in data
                and data[field_name] is not None
                and isinstance(data[field_name], str)
            ):
                try:
                    data[field_name] = Decimal(data[field_name])
                except (ValueError, TypeError) as e:
                    raise ValueError(f"Invalid {field_name} value: {data[field_name]}") from e

        return cls(**data)


__all__ = ["ActionLiteral", "StrategySignal"]
