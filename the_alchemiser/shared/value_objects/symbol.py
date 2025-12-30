"""Business Unit: shared | Status: current.

DTOs and immutable value objects shared across modules.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Symbol:
    """Stock/ETF symbol with validation.

    Represents a trading symbol (stock, ETF, crypto, etc.) with proper validation
    and normalization. Symbols are immutable value objects.

    Validation rules:
    - Must not be empty after stripping whitespace
    - Must not contain spaces
    - Allowed characters: alphanumeric (A-Z, 0-9), dots (.), hyphens (-), and slashes (/)
    - Maximum length: 10 characters (accommodates OTC stocks and crypto pairs)
    - Automatically normalized to uppercase

    Examples:
        >>> Symbol("AAPL")
        Symbol(value='AAPL')
        >>> Symbol("brk.b")  # Normalized to uppercase
        Symbol(value='BRK.B')
        >>> Symbol("BTCUSD")  # Crypto pairs allowed
        Symbol(value='BTCUSD')
        >>> Symbol("BRK-B")  # Hyphens allowed
        Symbol(value='BRK-B')
        >>> Symbol("BRK/B")  # Slashes allowed (Berkshire Class B)
        Symbol(value='BRK/B')

    Raises:
        ValueError: If symbol is empty, contains spaces, has invalid characters,
                   or exceeds maximum length.

    """

    value: str

    def __post_init__(self) -> None:
        """Validate and normalize the symbol after initialization.

        Raises:
            ValueError: If validation fails with specific error message.

        """
        # Strip whitespace and normalize to uppercase
        normalized = self.value.strip().upper()

        # Validate not empty
        if not normalized or normalized.replace(".", "").replace("-", "").replace("/", "") == "":
            raise ValueError("Symbol must not be empty")

        # Validate no internal spaces
        if " " in normalized:
            raise ValueError("Symbol must not contain spaces")

        # Validate allowed characters: alphanumeric, dots, hyphens, and slashes
        # But disallow multiple consecutive dots or leading/trailing special chars
        if ".." in normalized or "--" in normalized or "//" in normalized:
            raise ValueError(
                "Symbol contains invalid characters: consecutive dots, hyphens, or slashes"
            )
        if normalized[0] in ".-/" or normalized[-1] in ".-/":
            raise ValueError(
                "Symbol contains invalid characters: leading or trailing dot/hyphen/slash"
            )

        # Check for invalid characters
        allowed_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-/")
        if not all(c in allowed_chars for c in normalized):
            raise ValueError(
                "Symbol contains invalid characters: "
                "only alphanumeric, dots, hyphens, and slashes allowed"
            )

        # Validate length (max 10 for OTC stocks and crypto pairs)
        if len(normalized) > 10:
            raise ValueError("Symbol cannot exceed 10 characters")

        # Set normalized value
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        """Return the symbol value as string for API compatibility.

        Returns:
            The uppercase symbol string.

        """
        return self.value
