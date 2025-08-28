"""Business Unit: utilities; Status: current.

Shared kernel type exports for cross-context value objects and enums.
"""

from __future__ import annotations

from enum import Enum

from .value_objects.identifier import Identifier
from .value_objects.money import Money
from .value_objects.percentage import Percentage


class ActionType(Enum):
    """Enumeration of possible trading actions.

    This enum defines the three fundamental trading actions that can be
    recommended by trading strategies or executed by the trading system.
    
    This is a cross-context enum that can be safely used across different
    domain boundaries without introducing coupling.

    Attributes:
        BUY: Indicates a buy/long position should be opened or increased
        SELL: Indicates a sell/short position should be opened or position closed
        HOLD: Indicates no action should be taken, maintain current position

    Example:
        >>> action = ActionType.BUY
        >>> print(f"Recommended action: {action.value}")
        Recommended action: BUY

    """

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


__all__ = ["ActionType", "Identifier", "Money", "Percentage"]
