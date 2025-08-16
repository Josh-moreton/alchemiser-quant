from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Symbol:
    """Stock/ETF symbol with validation."""

    value: str

    def __post_init__(self) -> None:  # pragma: no cover - trivial validation
        if not self.value or not self.value.isalpha():
            raise ValueError("Symbol must be alphabetic characters only")
        if len(self.value) > 5:
            raise ValueError("Symbol cannot exceed 5 characters")
        object.__setattr__(self, "value", self.value.upper())
