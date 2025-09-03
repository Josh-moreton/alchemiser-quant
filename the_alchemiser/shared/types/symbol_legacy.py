"""Business Unit: shared | Status: current..

Typed value object for Symbols used across the domain.

Keep domain free of external libs; normalize to upper-case and strip whitespace.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Symbol:
    """Ticker symbol value object.

    Invariants:
    - Non-empty
    - Upper-case normalized
    """

    value: str

    def __post_init__(self) -> None:  # pragma: no cover (tiny)
        v = (self.value or "").strip()
        if not v:
            raise ValueError("Symbol cannot be empty")
        # Normalize to upper-case
        object.__setattr__(self, "value", v.upper())

    def __str__(self) -> str:
        return self.value

    def as_str(self) -> str:
        """Explicit accessor for interop with external APIs."""
        return self.value
