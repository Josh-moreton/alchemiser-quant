"""Business Unit: utilities; Status: current."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal

from the_alchemiser.shared.value_objects.symbol import Symbol

Severity = Literal["INFO", "WARNING", "ERROR"]


@dataclass(frozen=True)
class Alert:
    """Trading alert value object."""

    message: str
    severity: Severity
    symbol: Symbol | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:  # pragma: no cover - trivial validation
        if self.severity not in ("INFO", "WARNING", "ERROR"):
            raise ValueError("Invalid alert severity")
