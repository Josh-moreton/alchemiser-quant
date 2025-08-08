"""Strategy domain models."""

from dataclasses import (
    dataclass,
)  # TODO(PYDANTIC-MIGRATION): Convert Strategy* models to Pydantic BaseModel for validation (e.g. confidence range 0-1) & enums for action.
from typing import Literal

from the_alchemiser.core.types import StrategyPositionData, StrategySignal


@dataclass(
    frozen=True
)  # TODO(PYDANTIC-MIGRATION): Replace with StrategySignalModel(BaseModel) with action Enum and confidence validators.
class StrategySignalModel:
    """Immutable strategy signal model."""

    symbol: str
    action: Literal["BUY", "SELL", "HOLD"]
    confidence: float
    reasoning: str
    allocation_percentage: float

    @classmethod
    def from_dict(cls, data: StrategySignal) -> "StrategySignalModel":
        """Create from StrategySignal TypedDict."""
        return cls(
            symbol=data["symbol"],
            action=data["action"],
            confidence=data["confidence"],
            reasoning=data["reasoning"],
            allocation_percentage=data["allocation_percentage"],
        )

    def to_dict(self) -> StrategySignal:
        """Convert to StrategySignal TypedDict."""
        return {
            "symbol": self.symbol,
            "action": self.action,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "allocation_percentage": self.allocation_percentage,
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
        """Check if signal has high confidence (>0.7)."""
        return self.confidence > 0.7

    @property
    def confidence_level(self) -> str:
        """Get confidence level as string."""
        if self.confidence >= 0.8:
            return "HIGH"
        elif self.confidence >= 0.6:
            return "MEDIUM"
        else:
            return "LOW"


@dataclass(
    frozen=True
)  # TODO(PYDANTIC-MIGRATION): Replace with StrategyPositionModel(BaseModel) and validate non-zero entry_price for percentage calculations.
class StrategyPositionModel:
    """Immutable strategy position model."""

    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    strategy_type: str

    @classmethod
    def from_dict(cls, data: StrategyPositionData) -> "StrategyPositionModel":
        """Create from StrategyPositionData TypedDict."""
        return cls(
            symbol=data["symbol"],
            quantity=data["quantity"],
            entry_price=data["entry_price"],
            current_price=data["current_price"],
            strategy_type=data["strategy_type"],
        )

    def to_dict(self) -> StrategyPositionData:
        """Convert to StrategyPositionData TypedDict."""
        return {
            "symbol": self.symbol,
            "quantity": self.quantity,
            "entry_price": self.entry_price,
            "current_price": self.current_price,
            "strategy_type": self.strategy_type,
        }

    @property
    def unrealized_pnl(self) -> float:
        """Calculate unrealized P&L."""
        return (self.current_price - self.entry_price) * self.quantity

    @property
    def unrealized_pnl_percentage(self) -> float:
        """Calculate unrealized P&L percentage."""
        if self.entry_price == 0:
            return 0.0
        return ((self.current_price - self.entry_price) / self.entry_price) * 100

    @property
    def total_value(self) -> float:
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
