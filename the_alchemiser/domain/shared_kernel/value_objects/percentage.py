"""Business Unit: utilities; Status: current."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Percentage:
    """Immutable percentage value object with validation.

    Value is in range [0, 1] where 1 == 100%.
    """

    value: Decimal

    def __post_init__(self) -> None:  # pragma: no cover - trivial validation
        if not (Decimal("0") <= self.value <= Decimal("1")):
            raise ValueError("Percentage must be between 0.0 and 1.0")

    @classmethod
    def from_percent(cls, percent: float) -> Percentage:
        return cls(Decimal(str(percent)) / Decimal("100"))

    def to_percent(self) -> Decimal:
        return self.value * Decimal("100")
