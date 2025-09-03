"""Business Unit: shared | Status: current.."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class TimeInForce:
    """Time-in-force specification with validation."""

    value: Literal["day", "gtc", "ioc", "fok"]

    def __post_init__(self) -> None:  # pragma: no cover - trivial validation
        valid_values = {"day", "gtc", "ioc", "fok"}
        if self.value not in valid_values:
            raise ValueError(f"TimeInForce must be one of {valid_values}")
