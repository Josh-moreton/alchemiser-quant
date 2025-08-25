"""Strategy signal model using domain value objects."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, cast

from the_alchemiser.domain.shared_kernel.value_objects.percentage import Percentage
from the_alchemiser.domain.strategies.value_objects.confidence import Confidence
from the_alchemiser.domain.strategies.value_objects.strategy_signal import Action
from the_alchemiser.domain.trading.value_objects.symbol import Symbol
from the_alchemiser.domain.types import StrategySignal as StrategySignalDTO


@dataclass(frozen=True)
class StrategySignalModel:
    """Immutable strategy signal model using domain value objects.

    This model uses proper domain value objects with Decimal for financial values
    and type-safe value objects for all fields. It provides mapping to/from
    TypedDict DTOs for interface boundaries.
    """

    symbol: Symbol
    action: Action
    confidence: Confidence
    target_allocation: Percentage
    reasoning: str
    timestamp: datetime

    @classmethod
    def from_domain_signal(
        cls,
        signal: Any,  # Use Any to avoid forward reference issues
    ) -> StrategySignalModel:
        """Create from domain StrategySignal value object."""
        # Import here to avoid circular dependency
        from the_alchemiser.domain.strategies.value_objects.strategy_signal import StrategySignal

        if not isinstance(signal, StrategySignal):
            raise TypeError("Expected StrategySignal value object")

        return cls(
            symbol=signal.symbol,
            action=signal.action,
            confidence=signal.confidence,
            target_allocation=signal.target_allocation,
            reasoning=signal.reasoning,
            timestamp=signal.timestamp,
        )

    @classmethod
    def from_dto(cls, data: StrategySignalDTO) -> StrategySignalModel:
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
        elif self.confidence.value >= Decimal("0.6"):
            return "MEDIUM"
        else:
            return "LOW"

    @property
    def allocation_percentage(self) -> Decimal:
        """Get allocation as percentage (0-100)."""
        return self.target_allocation.to_percent()
