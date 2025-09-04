"""Business Unit: strategy | Status: current

Canonical strategy signal and position types.

This module provides the canonical implementations of strategy signals and positions,
consolidating logic that was previously duplicated across multiple files.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal, cast

from the_alchemiser.shared.types.percentage import Percentage
from the_alchemiser.shared.value_objects.core_types import (
    StrategyPositionData as StrategyPositionDTO,
)
from the_alchemiser.shared.value_objects.core_types import (
    StrategySignal as StrategySignalDTO,
)
from the_alchemiser.shared.value_objects.symbol import Symbol

# Import confidence from engines value objects for now, will be moved later
from ..engines.value_objects.confidence import Confidence

Action = Literal["BUY", "SELL", "HOLD"]


@dataclass(frozen=True)
class StrategySignal:
    """Canonical trading signal from a strategy.

    This consolidates signal logic that was previously duplicated across:
    - strategy/engines/models/strategy_signal_model.py
    - strategy/engines/value_objects/strategy_signal.py
    """

    symbol: Symbol
    action: Action
    confidence: Confidence
    target_allocation: Percentage
    reasoning: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:  # pragma: no cover - trivial validation
        if self.action not in ("BUY", "SELL", "HOLD"):
            raise ValueError("Invalid signal action")

    @classmethod
    def from_dto(cls, data: StrategySignalDTO) -> StrategySignal:
        """Create from StrategySignal TypedDict DTO."""
        # Handle flexible symbol field (can be string or dict for portfolio)
        symbol_value = data["symbol"]
        if isinstance(symbol_value, dict):
            # Portfolio allocation - use a standard label that fits Symbol constraints
            symbol = Symbol("PORT")  # Shortened to fit 5-char limit
        else:
            symbol_str = str(symbol_value)
            # Ensure symbol fits constraints: <= 5 chars, alphabetic only
            if len(symbol_str) > 5:
                symbol_str = symbol_str[:5]
            # Remove non-alphabetic characters
            symbol_str = "".join(c for c in symbol_str if c.isalpha()).upper()
            if not symbol_str:
                symbol_str = "UNK"  # Unknown symbol fallback
            symbol = Symbol(symbol_str)

        # Parse confidence as Decimal
        confidence = Confidence(Decimal(str(data["confidence"])))

        # Parse allocation percentage as Decimal
        allocation_pct = data.get("allocation_percentage", 0.0)
        target_allocation = Percentage(Decimal(str(allocation_pct)) / Decimal("100"))

        # Handle both reasoning and reason fields
        reasoning = data.get("reasoning") or data.get("reason", "")

        return cls(
            symbol=symbol,
            action=cast(Action, data["action"]),  # Cast to Action type
            confidence=confidence,
            target_allocation=target_allocation,
            reasoning=str(reasoning),
            timestamp=datetime.now(UTC),  # DTO doesn't have timestamp
        )

    def to_dto(self) -> StrategySignalDTO:
        """Convert to StrategySignal TypedDict DTO."""
        return {
            "symbol": self.symbol.value,
            "action": self.action,
            "confidence": float(self.confidence.value),
            "reasoning": self.reasoning,
            "allocation_percentage": float(self.target_allocation.to_percent()),
        }

    @property
    def is_buy_signal(self) -> bool:
        """Check if this is a buy signal."""
        return self.action == "BUY"

    @property
    def is_sell_signal(self) -> bool:
        """Check if this is a sell signal."""
        return self.action == "SELL"

    @property
    def is_hold_signal(self) -> bool:
        """Check if this is a hold signal."""
        return self.action == "HOLD"

    @property
    def is_high_confidence(self) -> bool:
        """Check if signal has high confidence."""
        return self.confidence.is_high

    @property
    def is_low_confidence(self) -> bool:
        """Check if signal has low confidence."""
        return self.confidence.is_low

    @property
    def confidence_level(self) -> str:
        """Get confidence level as string."""
        if self.confidence.value >= Decimal("0.8"):
            return "HIGH"
        if self.confidence.value >= Decimal("0.6"):
            return "MEDIUM"
        return "LOW"

    @property
    def allocation_percentage(self) -> Decimal:
        """Get allocation as percentage (0-100)."""
        return self.target_allocation.to_percent()


@dataclass(frozen=True)
class StrategyPosition:
    """Canonical strategy position model.

    This consolidates position logic that was previously duplicated in:
    - strategy/engines/models/strategy_position_model.py
    """

    symbol: Symbol
    quantity: Decimal  # Using Decimal directly since positions can be fractional
    entry_price: Decimal  # Using Decimal for price precision
    current_price: Decimal  # Using Decimal for price precision
    strategy_type: str

    def __post_init__(self) -> None:  # pragma: no cover - trivial validation
        """Validate position data."""
        if self.entry_price < 0:
            raise ValueError("Entry price cannot be negative")
        if self.current_price < 0:
            raise ValueError("Current price cannot be negative")

    @classmethod
    def from_dto(cls, data: StrategyPositionDTO) -> StrategyPosition:
        """Create from StrategyPositionData TypedDict DTO."""
        symbol = Symbol(str(data["symbol"]))

        # Convert to Decimal for financial precision
        quantity = Decimal(str(data["quantity"]))
        entry_price = Decimal(str(data["entry_price"]))
        current_price = Decimal(str(data["current_price"]))

        return cls(
            symbol=symbol,
            quantity=quantity,
            entry_price=entry_price,
            current_price=current_price,
            strategy_type=str(data["strategy_type"]),
        )

    def to_dto(self) -> StrategyPositionDTO:
        """Convert to StrategyPositionData TypedDict DTO."""
        return {
            "symbol": self.symbol.value,
            "quantity": float(self.quantity),
            "entry_price": float(self.entry_price),
            "current_price": float(self.current_price),
            "strategy_type": self.strategy_type,
        }

    @property
    def unrealized_pnl(self) -> Decimal:
        """Calculate unrealized P&L as Decimal."""
        price_diff = self.current_price - self.entry_price
        return price_diff * self.quantity

    @property
    def unrealized_pnl_percentage(self) -> Decimal:
        """Calculate unrealized P&L percentage."""
        if self.entry_price == 0:
            return Decimal("0")
        price_diff = self.current_price - self.entry_price
        return (price_diff / self.entry_price) * Decimal("100")

    @property
    def total_value(self) -> Decimal:
        """Calculate total value at current price."""
        return abs(self.quantity) * self.current_price

    @property
    def is_long(self) -> bool:
        """Check if position is long."""
        return self.quantity > 0

    @property
    def is_short(self) -> bool:
        """Check if position is short."""
        return self.quantity < 0

    @property
    def is_profitable(self) -> bool:
        """Check if position is profitable."""
        return self.unrealized_pnl > 0

    # Convenience methods for backward compatibility
    @property
    def unrealized_pnl_float(self) -> float:
        """Get unrealized P&L as float for backward compatibility."""
        return float(self.unrealized_pnl)

    @property
    def unrealized_pnl_percentage_float(self) -> float:
        """Get unrealized P&L percentage as float for backward compatibility."""
        return float(self.unrealized_pnl_percentage)

    @property
    def total_value_float(self) -> float:
        """Get total value as float for backward compatibility."""
        return float(self.total_value)
