"""Business Unit: execution | Status: legacy

Order types for backward compatibility.
"""

from enum import Enum


class OrderType(str, Enum):
    """Order types for backward compatibility."""

    MARKET = "market"
    LIMIT = "limit"
    
    def __init__(self, value: str) -> None:
        self._value_ = value


class Side(str, Enum):
    """Order sides for backward compatibility."""

    BUY = "buy"
    SELL = "sell"
    
    def __init__(self, value: str) -> None:
        self._value_ = value