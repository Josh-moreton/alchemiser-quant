"""Business Unit: shared | Status: current.

Strategy engine protocol definition.

Defines the interface that strategy engines must implement.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from .market_data_port import MarketDataPort
from .strategy_value_objects import StrategySignal


@runtime_checkable
class StrategyEngine(Protocol):
    """Protocol for strategy engine implementations."""

    def __init__(self, market_data_port: MarketDataPort) -> None:
        """Initialize strategy engine with market data port."""
        ...

    def generate_signals(self, timestamp: datetime) -> list[StrategySignal]:
        """Generate strategy signals for the given timestamp.

        Args:
            timestamp: Timestamp for signal generation

        Returns:
            List of strategy signals

        """
        ...

    def validate_signals(self, signals: list[StrategySignal]) -> None:
        """Validate generated signals.

        Args:
            signals: List of signals to validate

        Raises:
            ValueError: If signals are invalid

        """
        ...
