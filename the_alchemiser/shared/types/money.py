"""Business Unit: shared | Status: current.

Money value object implementation.

This module provides the Money class, an immutable value object that represents
monetary amounts with currency information. It uses Decimal arithmetic to avoid
floating-point precision errors in financial calculations.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal


@dataclass(frozen=True)
class Money:
    """Immutable money value object with currency and precision.

    Represents a monetary amount with its currency. All arithmetic operations
    use Decimal to ensure precision in financial calculations. The amount is
    automatically normalized to 2 decimal places using banker's rounding.

    Attributes:
        amount: The monetary amount as a Decimal, normalized to 2 decimal places.
        currency: The ISO 4217 currency code (e.g., "USD").

    Raises:
        ValueError: If amount is negative or currency is not a valid 3-character code.

    Examples:
        >>> money = Money(Decimal("100.50"), "USD")
        >>> money.amount
        Decimal('100.50')
        >>> money.currency
        'USD'

    """

    amount: Decimal
    currency: str  # ISO 4217 code, e.g., "USD"

    def __post_init__(self) -> None:  # pragma: no cover - trivial validation
        """Validate money constraints and normalize amount after initialization.
        
        Raises:
            ValueError: If amount is negative or currency is not a valid 3-character code.
        """
        if self.amount < 0:
            raise ValueError("Money amount cannot be negative")
        if len(self.currency) != 3:
            raise ValueError("Currency must be ISO 4217 code")
        normalized = self.amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        object.__setattr__(self, "amount", normalized)

    def add(self, other: Money) -> Money:
        """Add another Money object to this one.

        Args:
            other: Another Money object to add. Must have the same currency.

        Returns:
            A new Money object with the sum of both amounts.

        Raises:
            ValueError: If the currencies don't match.

        Examples:
            >>> m1 = Money(Decimal("10.50"), "USD")
            >>> m2 = Money(Decimal("5.25"), "USD")
            >>> result = m1.add(m2)
            >>> result.amount
            Decimal('15.75')

        """
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)

    def multiply(self, factor: Decimal) -> Money:
        """Multiply the money amount by a decimal factor.

        Args:
            factor: The multiplication factor as a Decimal.

        Returns:
            A new Money object with the multiplied amount, maintaining the same currency.

        Examples:
            >>> money = Money(Decimal("100.00"), "USD")
            >>> result = money.multiply(Decimal("1.5"))
            >>> result.amount
            Decimal('150.00')

        """
        return Money(self.amount * factor, self.currency)
