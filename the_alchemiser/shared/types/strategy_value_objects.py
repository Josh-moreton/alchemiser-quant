"""Business Unit: shared | Status: current

Strategy value objects used across modules.

Core domain objects for strategy signals and confidence levels.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel

from the_alchemiser.shared.value_objects.symbol import Symbol


class Confidence(BaseModel):
    """Represents confidence level in a strategy signal."""

    value: Decimal

    def __init__(self, value: Decimal | float | str) -> None:
        if isinstance(value, (float, str)):
            value = Decimal(str(value))
        super().__init__(value=value)


class StrategySignal(BaseModel):
    """Represents a strategy signal with all required metadata."""

    symbol: Symbol
    action: str  # BUY, SELL, HOLD
    confidence: Confidence
    target_allocation: Decimal | None = None
    reasoning: str = ""
    timestamp: datetime

    def __init__(
        self,
        symbol: Symbol | str,
        action: str,
        confidence: Confidence | Decimal | float,
        target_allocation: Decimal | float | None = None,
        reasoning: str = "",
        timestamp: datetime | None = None,
        **kwargs: Any,
    ) -> None:
        if isinstance(symbol, str):
            symbol = Symbol(symbol)
        if not isinstance(confidence, Confidence):
            confidence = Confidence(confidence)
        if target_allocation is not None and not isinstance(target_allocation, Decimal):
            target_allocation = Decimal(str(target_allocation))
        if timestamp is None:
            timestamp = datetime.now()

        super().__init__(
            symbol=symbol,
            action=action,
            confidence=confidence,
            target_allocation=target_allocation,
            reasoning=reasoning,
            timestamp=timestamp,
            **kwargs,
        )
