"""Business Unit: shared | Status: current.

Trading strategy base class and related models.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

# Constants for strategy types
STRATEGY_TYPE_MOMENTUM = "momentum"
STRATEGY_TYPE_MEAN_REVERSION = "mean_reversion"
STRATEGY_TYPE_BREAKOUT = "breakout"


class TradingStrategy(ABC):
    """Base class for all trading strategies.
    
    This class provides a common interface for strategy encapsulation,
    allowing different trading strategies to be implemented consistently
    across the system.
    """
    
    def __init__(self, name: str, parameters: dict[str, Any] | None = None) -> None:
        """Initialize the trading strategy.
        
        Args:
            name: The name of the strategy
            parameters: Optional dictionary of strategy parameters

        """
        self.name = name
        self.parameters = parameters or {}
        self._is_active = False
        self._last_execution_time = None
        self._execution_count = 0
        self._performance_metrics = {}
        
    def __str__(self) -> str:
        """Return string representation of the strategy.
        
        Returns:
            String representation including strategy name and class

        """
        return f"{self.__class__.__name__}(name={self.name})"

    @abstractmethod
    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        """Execute the trading strategy logic.
        
        This method must be implemented by all concrete strategy classes
        to define their specific trading behavior.
        
        Args:
            context: Dictionary containing market data and other context
            
        Returns:
            Dictionary containing strategy signals and metadata

        """
