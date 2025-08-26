from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Side:
    """Order side (buy/sell) specification with validation."""

    value: Literal["buy", "sell"]

    def __post_init__(self) -> None:  # pragma: no cover - trivial validation
        valid_values = {"buy", "sell"}
        if self.value not in valid_values:
            raise ValueError(f"Side must be one of {valid_values}")