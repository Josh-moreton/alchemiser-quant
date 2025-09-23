"""Business Unit: shared | Status: current.

Strategy value objects used across modules.

Core domain objects for strategy signals without confidence levels.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from pydantic import BaseModel

from the_alchemiser.shared.types.percentage import Percentage
from the_alchemiser.shared.value_objects.symbol import Symbol


class StrategySignal(BaseModel):
    """Represents a strategy signal with all required metadata."""

    symbol: Symbol
    action: str  # BUY, SELL, HOLD
    target_allocation: Decimal | None = None
    reasoning: str = ""
    timestamp: datetime

    def __init__(
        self,
        symbol: Symbol | str,
        action: str,
        target_allocation: Decimal | float | Percentage | None = None,
        reasoning: str = "",
        timestamp: datetime | None = None,
        **kwargs: str | int | float | bool,
    ) -> None:
        """Build a normalized `StrategySignal` from flexible input types."""
        if isinstance(symbol, str):
            symbol = Symbol(symbol)
        if target_allocation is not None and not isinstance(target_allocation, Decimal):
            if isinstance(target_allocation, Percentage):
                target_allocation = target_allocation.value
            else:
                target_allocation = Decimal(str(target_allocation))
        if timestamp is None:
            timestamp = datetime.now(UTC)

        super().__init__(
            symbol=symbol,
            action=action,
            target_allocation=target_allocation,
            reasoning=reasoning,
            timestamp=timestamp,
            **kwargs,
        )
