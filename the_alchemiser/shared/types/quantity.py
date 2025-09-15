"""Business Unit: shared | Status: current.

Shared domain types with validation.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from the_alchemiser.shared.utils.validation_utils import validate_non_negative_integer


@dataclass(frozen=True)
class Quantity:
    """Order quantity with validation (whole number > 0)."""

    value: Decimal

    def __post_init__(self) -> None:  # pragma: no cover - trivial validation
        """Validate the quantity after initialization."""
        validate_non_negative_integer(self.value, "Quantity")
