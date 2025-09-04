"""Business Unit: utilities; Status: current."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from the_alchemiser.shared.utils.validation_utils import (
    CONFIDENCE_RANGE,
    validate_decimal_range,
)


@dataclass(frozen=True)
class Confidence:
    """Signal confidence level (0.0 to 1.0)."""

    value: Decimal

    def __post_init__(self) -> None:  # pragma: no cover - trivial validation
        validate_decimal_range(
            self.value,
            CONFIDENCE_RANGE[0],
            CONFIDENCE_RANGE[1],
            "Confidence",
        )

    @property
    def is_high(self) -> bool:
        return self.value >= Decimal("0.7")

    @property
    def is_low(self) -> bool:
        return self.value <= Decimal("0.3")
