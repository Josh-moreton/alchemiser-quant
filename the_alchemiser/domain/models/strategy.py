"""Strategy domain models."""

from dataclasses import dataclass
from typing import Literal, cast

from the_alchemiser.domain.types import StrategyPositionData, StrategySignal


@dataclass(frozen=True)
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
        # Normalize symbol - extract first symbol if it's a dict
        symbol = data["symbol"]
        if isinstance(symbol, dict):
            # Take the first symbol from the portfolio dict
            symbol = next(iter(symbol.keys()))

        # Normalize action - ensure it's a valid literal
        action = str(data["action"]).upper()
        if action not in ["BUY", "SELL", "HOLD"]:
            action = "HOLD"  # Default fallback

        return cls(
            symbol=symbol,
            action=cast(Literal["BUY", "SELL", "HOLD"], action),
            confidence=data["confidence"],
            reasoning=data.get("reasoning", data.get("reason", "")),  # Handle both field names
            allocation_percentage=data.get("allocation_percentage", 0.0),
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
        if self.confidence >= 0.6:
            return "MEDIUM"
        return "LOW"


@dataclass(frozen=True)
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
