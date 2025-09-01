"""Business Unit: strategy & signal generation; Status: current."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal

from the_alchemiser.domain.shared_kernel.value_objects.percentage import (
    Percentage,
)
from .confidence import Confidence
from the_alchemiser.domain.trading.value_objects.symbol import Symbol

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
        if self.action not in ("BUY", "SELL", "HOLD"):
            raise ValueError("Invalid signal action")
