"""
Common constants and enums shared across the trading system.
"""

from enum import Enum


class ActionType(Enum):
    """Trading action types"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
