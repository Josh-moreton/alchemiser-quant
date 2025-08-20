from __future__ import annotations

from typing import Protocol, runtime_checkable

from the_alchemiser.domain.strategies.value_objects.alert import Alert
from the_alchemiser.domain.strategies.value_objects.strategy_signal import (
    StrategySignal,
)


@runtime_checkable
class StrategyEngine(Protocol):
    """Strategy engine protocol with precise typing."""

    def generate_signals(self) -> list[StrategySignal]:
        """Generate trading signals."""
        ...

    def run_once(self) -> list[Alert] | None:
        """Run strategy once and return alerts."""
        ...

    def validate_signal(self, signal: StrategySignal) -> bool:
        """Validate generated signal."""
        ...
