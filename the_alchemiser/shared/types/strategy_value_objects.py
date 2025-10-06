"""Business Unit: shared | Status: current.

Strategy value objects used across modules.

This module defines StrategySignal, an immutable value object representing
trading signals from strategy engines. Uses Pydantic v2 for validation.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from the_alchemiser.shared.types.percentage import Percentage
from the_alchemiser.shared.value_objects.symbol import Symbol

# Type alias for valid trading actions
ActionLiteral = Literal["BUY", "SELL", "HOLD"]


class StrategySignal(BaseModel):
    """Represents an immutable strategy signal with all required metadata.

    A StrategySignal is a value object representing a trading decision from
    a strategy engine. It includes the symbol, action (BUY/SELL/HOLD),
    optional target allocation, reasoning, and timestamp.

    All monetary allocations use Decimal for precision. The signal is immutable
    after creation (frozen=True) to ensure value object semantics.

    Attributes:
        symbol: Trading symbol (e.g., "AAPL", "SPY"). Accepts Symbol or str.
        action: Trading action - one of "BUY", "SELL", or "HOLD"
        target_allocation: Optional target portfolio allocation as Decimal (0.0-1.0)
                          where 0.5 = 50% of portfolio. None means no allocation.
        reasoning: Human-readable explanation for the signal (max 1000 chars)
        timestamp: Timezone-aware datetime when signal was generated (UTC)

    Examples:
        >>> # Simple buy signal
        >>> signal = StrategySignal(
        ...     symbol="AAPL",
        ...     action="BUY",
        ...     reasoning="Strong momentum detected",
        ...     timestamp=datetime.now(UTC)
        ... )

        >>> # Signal with allocation from Percentage
        >>> signal = StrategySignal(
        ...     symbol=Symbol("SPY"),
        ...     action="BUY",
        ...     target_allocation=Percentage.from_percent(30.0),
        ...     reasoning="Defensive allocation",
        ...     timestamp=datetime.now(UTC)
        ... )

    Raises:
        ValidationError: If action is not BUY/SELL/HOLD
        ValidationError: If target_allocation is outside [0, 1]
        ValidationError: If timestamp is timezone-naive
        ValueError: If symbol validation fails (from Symbol class)

    Note:
        This is an immutable value object. All fields are frozen after creation.
        For flexibility, validators accept Symbol or str for symbol,
        and Decimal/float/Percentage for target_allocation.

        Default timestamp behavior: If None provided, defaults to current UTC time.
        For deterministic testing, always provide explicit timestamp.

    """

    model_config = ConfigDict(
        frozen=True,
        strict=True,
        validate_assignment=True,
        str_strip_whitespace=True,
        extra="allow",  # Allow extra fields for correlation_id, causation_id, etc.
    )

    symbol: Symbol
    action: ActionLiteral
    target_allocation: Decimal | None = None
    reasoning: str = Field(default="", max_length=1000)
    timestamp: datetime

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
            return Symbol(v)
        return v

    @field_validator("target_allocation", mode="before")
    @classmethod
    def normalize_allocation(cls, v: Decimal | float | Percentage | None) -> Decimal | None:
        """Convert allocation to Decimal and validate range.

        Accepts Decimal, float, int, or Percentage. Converts to Decimal with
        proper precision handling (float -> str -> Decimal to avoid precision loss).

        Args:
            v: Allocation value in various formats, or None

        Returns:
            Decimal value in range [0, 1], or None

        Raises:
            ValidationError: If allocation is outside [0, 1] range

        """
        if v is None:
            return None
        if isinstance(v, Percentage):
            v = v.value
        elif isinstance(v, (float, int)):
            v = Decimal(str(v))

        # Validate range [0, 1]
        if not (Decimal("0") <= v <= Decimal("1")):
            raise ValueError(f"target_allocation must be between 0 and 1, got {v}")

        return v

    @field_validator("timestamp", mode="before")
    @classmethod
    def normalize_and_validate_timestamp(cls, v: datetime | None) -> datetime:
        """Default to current UTC time if None, and validate timezone awareness.

        Args:
            v: Datetime value or None

        Returns:
            Timezone-aware datetime (defaults to now(UTC) if None)

        Raises:
            ValidationError: If datetime is timezone-naive

        """
        if v is None:
            v = datetime.now(UTC)

        # Ensure timezone-aware
        if v.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware (use datetime.now(UTC))")

        return v


__all__ = ["ActionLiteral", "StrategySignal"]
