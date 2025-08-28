"""Business Unit: order execution/placement; Status: current."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class OrderType:
    """Order type specification with validation."""

    value: Literal["market", "limit"]

    def __post_init__(self) -> None:  # pragma: no cover - trivial validation
        valid_values = {"market", "limit"}
        if self.value not in valid_values:
            raise ValueError(f"OrderType must be one of {valid_values}")
