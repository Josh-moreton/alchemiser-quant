"""Business Unit: shared | Status: current.

Quantity value object implementation.

This module provides the Quantity class, an immutable value object that represents
order quantities with validation. It ensures quantities are positive whole numbers,
preventing fractional shares where not supported.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Quantity:
    """Order quantity with validation for whole number values.

    Represents a quantity of shares or units for trading orders. Ensures that
    quantities are non-negative whole numbers, which is required for most
    order types and broker implementations.

    Attributes:
        value: The quantity as a Decimal, must be a non-negative whole number.

    Raises:
        ValueError: If value is negative or not a whole number.

    Examples:
        >>> qty = Quantity(Decimal("100"))
        >>> qty.value
        Decimal('100')
        
        >>> # This would raise ValueError
        >>> Quantity(Decimal("100.5"))  # doctest: +SKIP
        ValueError: Quantity must be whole number

    """

    value: Decimal

    def __post_init__(self) -> None:  # pragma: no cover - trivial validation
        """Validate quantity constraints after initialization.
        
        Raises:
            ValueError: If quantity is negative or fractional.

        """
        if self.value < 0:
            raise ValueError("Quantity must be non-negative")
        if self.value != self.value.to_integral_value():
            raise ValueError("Quantity must be whole number")
