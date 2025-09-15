"""Business Unit: shared | Status: current.

DTOs and immutable value objects shared across modules.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Symbol:
    """Stock/ETF symbol with validation."""

    value: str

    def __post_init__(self) -> None:  # pragma: no cover - trivial validation
        """Validate and normalize the symbol after initialization."""
        if not self.value or not self.value.isalnum():
            raise ValueError("Symbol must be alphanumeric characters only")
        if len(self.value) > 5:
            raise ValueError("Symbol cannot exceed 5 characters")
        object.__setattr__(self, "value", self.value.upper())

    def __str__(self) -> str:
        """Return the symbol value as string for API compatibility."""
        return self.value
