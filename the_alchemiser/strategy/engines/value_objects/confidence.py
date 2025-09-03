"""Business Unit: utilities; Status: current."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Confidence:
    """Signal confidence level (0.0 to 1.0)."""

    value: Decimal

    def __post_init__(self) -> None:  # pragma: no cover - trivial validation
        if not (Decimal("0") <= self.value <= Decimal("1")):
            raise ValueError("Confidence must be between 0.0 and 1.0")

    @property
    def is_high(self) -> bool:
        """Check if confidence level is high (>=0.7).
        
        Returns:
            True if confidence value is 0.7 or higher.

        """
        return self.value >= Decimal("0.7")

    @property
    def is_low(self) -> bool:
        """Check if confidence level is low (<=0.3).
        
        Returns:
            True if confidence value is 0.3 or lower.

        """
        return self.value <= Decimal("0.3")
