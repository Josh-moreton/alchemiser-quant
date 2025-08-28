"""Business Unit: order execution/placement; Status: current."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Quantity:
    """Order quantity with validation (whole number > 0)."""

    value: Decimal

    def __post_init__(self) -> None:  # pragma: no cover - trivial validation
        if self.value < 0:
            raise ValueError("Quantity must be non-negative")
        if self.value != self.value.to_integral_value():
            raise ValueError("Quantity must be whole number")
