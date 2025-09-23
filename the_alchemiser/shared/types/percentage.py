"""Business Unit: utilities; Status: current."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from the_alchemiser.shared.constants import PERCENTAGE_RANGE
from the_alchemiser.shared.utils.validation_utils import validate_decimal_range


@dataclass(frozen=True)
class Percentage:
    """Immutable percentage value object with validation.

    Value is in range [0, 1] where 1 == 100%.
    """

    value: Decimal

    def __post_init__(self) -> None:  # pragma: no cover - trivial validation
        """Validate that the percentage value is within acceptable bounds."""
        validate_decimal_range(
            self.value,
            PERCENTAGE_RANGE[0],
            PERCENTAGE_RANGE[1],
            "Percentage",
        )

    @classmethod
    def from_percent(cls, percent: float) -> Percentage:
        """Create a Percentage from a percentage value (e.g. 50.0 for 50%)."""
        return cls(Decimal(str(percent)) / Decimal("100"))

    def to_percent(self) -> Decimal:
        """Convert to percentage representation (e.g. 0.5 -> 50.0)."""
        return self.value * Decimal("100")
