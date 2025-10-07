"""Business Unit: shared; Status: current."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

# ISO 4217 currency codes with their decimal precision
# Source: https://www.iso.org/iso-4217-currency-codes.html
_CURRENCY_PRECISION: dict[str, int] = {
    # Major currencies (2 decimals)
    "USD": 2, "EUR": 2, "GBP": 2, "AUD": 2, "CAD": 2, "CHF": 2, "CNY": 2,
    "SEK": 2, "NZD": 2, "MXN": 2, "SGD": 2, "HKD": 2, "NOK": 2,
    "TRY": 2, "INR": 2, "RUB": 2, "BRL": 2, "ZAR": 2, "DKK": 2, "PLN": 2,
    "TWD": 2, "THB": 2, "MYR": 2, "IDR": 2, "HUF": 2, "CZK": 2, "ILS": 2,
    "PHP": 2, "AED": 2, "COP": 2, "SAR": 2, "RON": 2,
    "ARS": 2, "UAH": 2, "NGN": 2, "EGP": 2, "PKR": 2, "QAR": 2, "KES": 2,
    
    # Zero decimal currencies (no minor units)
    "JPY": 0,  # Japanese Yen
    "KRW": 0,  # South Korean Won
    "VND": 0,  # Vietnamese Dong
    "CLP": 0,  # Chilean Peso
    "ISK": 0,  # Icelandic Króna
    "PYG": 0,  # Paraguayan Guaraní
    "UGX": 0,  # Ugandan Shilling
    "VUV": 0,  # Vanuatu Vatu
    "XAF": 0,  # Central African CFA Franc
    "XOF": 0,  # West African CFA Franc
    "XPF": 0,  # CFP Franc
    
    # Three decimal currencies (1/1000 unit)
    "BHD": 3,  # Bahraini Dinar
    "JOD": 3,  # Jordanian Dinar
    "KWD": 3,  # Kuwaiti Dinar
    "OMR": 3,  # Omani Rial
    "TND": 3,  # Tunisian Dinar
    
    # Cryptocurrencies (8 decimals for satoshi-level precision)
    "BTC": 8,  # Bitcoin
    "ETH": 8,  # Ethereum
}


class MoneyError(ValueError):
    """Base exception for Money-related errors."""


class CurrencyMismatchError(MoneyError):
    """Raised when operations are attempted on Money with different currencies."""


class NegativeMoneyError(MoneyError):
    """Raised when attempting to create Money with negative amount."""


class InvalidCurrencyError(MoneyError):
    """Raised when currency code is invalid."""


class InvalidOperationError(MoneyError):
    """Raised when an invalid operation is attempted (e.g., division by zero)."""


@dataclass(frozen=True, order=True)
class Money:
    """Immutable money value object with currency and precision.

    Represents a monetary amount with an associated ISO 4217 currency code.
    All arithmetic operations use Decimal to avoid floating-point precision errors.

    Attributes:
        amount: The monetary amount as a Decimal, normalized to currency precision.
        currency: The ISO 4217 3-letter currency code (e.g., "USD", "EUR", "JPY").

    Examples:
        >>> m1 = Money(Decimal("100.50"), "USD")
        >>> m2 = Money(Decimal("50.25"), "USD")
        >>> m1.add(m2)
        Money(amount=Decimal('150.75'), currency='USD')

        >>> m1.multiply(Decimal("2"))
        Money(amount=Decimal('201.00'), currency='USD')
        
        >>> # Japanese Yen (0 decimals)
        >>> yen = Money(Decimal("1000"), "JPY")
        >>> str(yen)
        '1000 JPY'

    Notes:
        - Use Decimal for all arithmetic to avoid float precision errors.
        - Amount is normalized to currency-specific precision (USD=2, JPY=0, BHD=3).
        - Money objects are immutable and hashable (can be used in sets/dicts).
        - Money objects are comparable (supports ==, !=, <, >, <=, >=).
        - Amounts must be non-negative (use negate() for representation purposes).
        - Supports 50+ ISO 4217 currencies with correct decimal precision.

    Raises:
        NegativeMoneyError: If amount is negative.
        InvalidCurrencyError: If currency code is not a valid ISO 4217 code.
        CurrencyMismatchError: If operations are attempted on different currencies.

    """

    amount: Decimal
    currency: str  # ISO 4217 code, e.g., "USD"

    def __post_init__(self) -> None:
        """Normalize the amount to standard precision after initialization.

        Validates amount and currency, then normalizes amount to the appropriate
        decimal places for the currency using ROUND_HALF_UP rounding mode.

        Raises:
            NegativeMoneyError: If amount is negative.
            InvalidCurrencyError: If currency is not a valid ISO 4217 code.

        """
        if self.amount < 0:
            raise NegativeMoneyError(f"Money amount cannot be negative, got: {self.amount}")
        
        # Validate currency against ISO 4217 codes
        if self.currency not in _CURRENCY_PRECISION:
            raise InvalidCurrencyError(
                f"Currency must be a valid ISO 4217 code, got: {self.currency!r}. "
                f"Supported currencies: {', '.join(sorted(_CURRENCY_PRECISION.keys()))}"
            )
        
        # Get precision for this currency
        precision = _CURRENCY_PRECISION[self.currency]
        quantizer = Decimal(10) ** -precision
        normalized = self.amount.quantize(quantizer, rounding=ROUND_HALF_UP)
        object.__setattr__(self, "amount", normalized)

    def __str__(self) -> str:
        """Return string representation for display."""
        return f"{self.amount} {self.currency}"

    def __repr__(self) -> str:
        """Return detailed string representation for debugging."""
        return f"Money(amount={self.amount!r}, currency={self.currency!r})"

    def add(self, other: Money) -> Money:
        """Add two Money amounts of the same currency.

        Args:
            other: Another Money object with the same currency.

        Returns:
            A new Money object with the sum of both amounts.

        Raises:
            CurrencyMismatchError: If currencies don't match.

        Examples:
            >>> m1 = Money(Decimal("100.00"), "USD")
            >>> m2 = Money(Decimal("50.00"), "USD")
            >>> m1.add(m2)
            Money(amount=Decimal('150.00'), currency='USD')

        """
        if self.currency != other.currency:
            raise CurrencyMismatchError(
                f"Cannot add different currencies: {self.currency} and {other.currency}"
            )
        return Money(self.amount + other.amount, self.currency)

    def subtract(self, other: Money) -> Money:
        """Subtract another Money amount from this one.

        Args:
            other: Another Money object with the same currency.

        Returns:
            A new Money object with the difference.

        Raises:
            CurrencyMismatchError: If currencies don't match.
            NegativeMoneyError: If result would be negative.

        Examples:
            >>> m1 = Money(Decimal("100.00"), "USD")
            >>> m2 = Money(Decimal("50.00"), "USD")
            >>> m1.subtract(m2)
            Money(amount=Decimal('50.00'), currency='USD')

        """
        if self.currency != other.currency:
            raise CurrencyMismatchError(
                f"Cannot subtract different currencies: {self.currency} and {other.currency}"
            )
        result_amount = self.amount - other.amount
        if result_amount < 0:
            raise NegativeMoneyError(
                f"Subtraction would result in negative amount: "
                f"{self.amount} - {other.amount} = {result_amount}"
            )
        return Money(result_amount, self.currency)

    def multiply(self, factor: Decimal) -> Money:
        """Multiply Money amount by a decimal factor.

        Args:
            factor: A Decimal multiplier (must be non-negative).

        Returns:
            A new Money object with the product.

        Raises:
            TypeError: If factor is not a Decimal.
            ValueError: If factor is negative.

        Examples:
            >>> m = Money(Decimal("100.00"), "USD")
            >>> m.multiply(Decimal("1.5"))
            Money(amount=Decimal('150.00'), currency='USD')

        """
        if not isinstance(factor, Decimal):
            raise TypeError(f"Factor must be Decimal, got {type(factor).__name__}")
        if factor < 0:
            raise ValueError(f"Factor must be non-negative, got: {factor}")
        return Money(self.amount * factor, self.currency)

    def divide(self, divisor: Decimal) -> Money:
        """Divide Money amount by a decimal divisor.

        Args:
            divisor: A Decimal divisor (must be positive).

        Returns:
            A new Money object with the quotient.

        Raises:
            TypeError: If divisor is not a Decimal.
            InvalidOperationError: If divisor is zero or negative.

        Examples:
            >>> m = Money(Decimal("100.00"), "USD")
            >>> m.divide(Decimal("2"))
            Money(amount=Decimal('50.00'), currency='USD')

        """
        if not isinstance(divisor, Decimal):
            raise TypeError(f"Divisor must be Decimal, got {type(divisor).__name__}")
        if divisor <= 0:
            raise InvalidOperationError(f"Divisor must be positive, got: {divisor}")
        return Money(self.amount / divisor, self.currency)

    @classmethod
    def zero(cls, currency: str) -> Money:
        """Create a Money object with zero amount.

        Args:
            currency: The ISO 4217 currency code.

        Returns:
            A Money object with amount 0.00.

        Examples:
            >>> Money.zero("USD")
            Money(amount=Decimal('0.00'), currency='USD')

        """
        return cls(Decimal("0.00"), currency)

    @classmethod
    def from_decimal(cls, amount: Decimal, currency: str) -> Money:
        """Create a Money object from a Decimal amount.

        This is a convenience factory method for converting raw Decimal values
        (e.g., from DTOs or external APIs) into Money objects.

        Args:
            amount: The monetary amount as a Decimal.
            currency: The ISO 4217 currency code.

        Returns:
            A Money object with the given amount and currency.

        Examples:
            >>> Money.from_decimal(Decimal("100.50"), "USD")
            Money(amount=Decimal('100.50'), currency='USD')

        """
        return cls(amount, currency)

    def to_decimal(self) -> Decimal:
        """Convert Money amount to a raw Decimal.

        This is useful when interfacing with DTOs, external APIs, or database
        storage that expect primitive Decimal types rather than Money objects.

        Returns:
            The monetary amount as a Decimal.

        Examples:
            >>> m = Money(Decimal("100.50"), "USD")
            >>> m.to_decimal()
            Decimal('100.50')

        """
        return self.amount

    def is_zero(self) -> bool:
        """Check if the Money amount is zero.

        Returns:
            True if amount is zero, False otherwise.

        Examples:
            >>> Money.zero("USD").is_zero()
            True
            >>> Money(Decimal("100.00"), "USD").is_zero()
            False

        """
        precision = _CURRENCY_PRECISION[self.currency]
        quantizer = Decimal(10) ** -precision
        return self.amount == Decimal("0").quantize(quantizer)


def get_supported_currencies() -> list[str]:
    """Get list of supported ISO 4217 currency codes.
    
    Returns:
        Sorted list of supported currency codes.
    
    Examples:
        >>> "USD" in get_supported_currencies()
        True
        >>> "JPY" in get_supported_currencies()
        True
    
    """
    return sorted(_CURRENCY_PRECISION.keys())


def get_currency_precision(currency: str) -> int:
    """Get decimal precision for a currency.
    
    Args:
        currency: ISO 4217 currency code.
    
    Returns:
        Number of decimal places for the currency.
    
    Raises:
        InvalidCurrencyError: If currency is not supported.
    
    Examples:
        >>> get_currency_precision("USD")
        2
        >>> get_currency_precision("JPY")
        0
        >>> get_currency_precision("BHD")
        3
    
    """
    if currency not in _CURRENCY_PRECISION:
        raise InvalidCurrencyError(
            f"Currency {currency!r} is not supported. "
            f"Use get_supported_currencies() for a list of supported currencies."
        )
    return _CURRENCY_PRECISION[currency]


__all__ = [
    "CurrencyMismatchError",
    "InvalidCurrencyError",
    "InvalidOperationError",
    "Money",
    "MoneyError",
    "NegativeMoneyError",
    "get_currency_precision",
    "get_supported_currencies",
]
