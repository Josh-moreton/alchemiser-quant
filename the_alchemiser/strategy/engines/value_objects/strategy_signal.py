"""Business Unit: strategy & signal generation; Status: current."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal

from the_alchemiser.shared.types.percentage import (
    Percentage,
)
from the_alchemiser.shared.value_objects.symbol import Symbol

from .confidence import Confidence

Action = Literal["BUY", "SELL", "HOLD"]


@dataclass(frozen=True)
class StrategySignal:
    """Trading signal from a strategy."""

    symbol: Symbol
    action: Action
    confidence: Confidence
    target_allocation: Percentage
    reasoning: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:  # pragma: no cover - trivial validation
        from the_alchemiser.shared.utils.validation_utils import (
            SIGNAL_ACTIONS,
            validate_enum_value,
        )

        validate_enum_value(self.action, SIGNAL_ACTIONS, "Signal action")
