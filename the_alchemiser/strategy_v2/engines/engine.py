"""Business Unit: strategy | Status: current

Strategy engine protocol and base types for strategy_v2.

Defines the interface that strategy engines must implement.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable

from ...shared.types.market_data_port import MarketDataPort


@runtime_checkable
class StrategyEngine(Protocol):
    """Protocol for strategy engine implementations."""

    def __init__(self, market_data_port: MarketDataPort) -> None:
        """Initialize strategy engine with market data port."""
        ...

    def generate_signals(self, timestamp: datetime) -> list:
        """Generate strategy signals for the given timestamp.
        
        Args:
            timestamp: Timestamp for signal generation
            
        Returns:
            List of strategy signals
        """
        ...

    def validate_signals(self, signals: list) -> None:
        """Validate generated signals.
        
        Args:
            signals: List of signals to validate
            
        Raises:
            ValueError: If signals are invalid
        """
        ...