"""Business Unit: shared | Status: current..

Common constants and enums shared across the trading system.

This module provides shared enumeration types and constants used throughout
the trading system to ensure consistency and type safety.
"""

from __future__ import annotations

from enum import Enum


class ActionType(Enum):
    """Enumeration of possible trading actions.

    This enum defines the three fundamental trading actions that can be
    recommended by trading strategies or executed by the trading system.

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
