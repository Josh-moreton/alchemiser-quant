"""Business Unit: utilities; Status: current."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from the_alchemiser.shared.utils.validation_utils import (
    PERCENTAGE_RANGE,
    validate_decimal_range,
)


@dataclass(frozen=True)
class Percentage:
    """Immutable percentage value object with validation.

    Value is in range [0, 1] where 1 == 100%.
    """

    value: Decimal

    def __post_init__(self) -> None:  # pragma: no cover - trivial validation
        validate_decimal_range(
            self.value,
            PERCENTAGE_RANGE[0],
            PERCENTAGE_RANGE[1],
            "Percentage",
        )

    @classmethod
    def from_percent(cls, percent: float) -> Percentage:
        return cls(Decimal(str(percent)) / Decimal("100"))

    def to_percent(self) -> Decimal:
        return self.value * Decimal("100")
