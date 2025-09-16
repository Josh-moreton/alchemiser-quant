"""Business Unit: utilities; Status: current."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal


@dataclass(frozen=True)
class Money:
    """Immutable money value object with currency and precision.

    Notes:
        - Use Decimal for all arithmetic to avoid float precision errors.
        - Amount is normalized to 2 decimal places (USD-style) by default.

    """

    amount: Decimal
    currency: str  # ISO 4217 code, e.g., "USD"

    def __post_init__(self) -> None:  # pragma: no cover - trivial validation
        """Normalize the amount to standard precision after initialization."""
        if self.amount < 0:
            raise ValueError("Money amount cannot be negative")
        if len(self.currency) != 3:
            raise ValueError("Currency must be ISO 4217 code")
        normalized = self.amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        object.__setattr__(self, "amount", normalized)

    def add(self, other: Money) -> Money:
        """Add two Money amounts of the same currency."""
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)

    def multiply(self, factor: Decimal) -> Money:
        """Multiply Money amount by a decimal factor."""
        return Money(self.amount * factor, self.currency)
