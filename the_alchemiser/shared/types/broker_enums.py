"""Business Unit: shared | Status: current.

Broker-agnostic enums and constants for trading operations.

This module provides broker-independent enums that abstract away specific
broker implementations (like Alpaca) from the rest of the system. This
allows modules to use trading concepts without tight coupling to any
specific broker API.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

# Order side enumeration
OrderSideType = Literal["buy", "sell"]

# Time in force enumeration  
TimeInForceType = Literal["day", "gtc", "ioc", "fok"]


class BrokerOrderSide(Enum):
    """Broker-agnostic order side enumeration."""
    
    BUY = "buy"
    SELL = "sell"
    
    @classmethod
    def from_string(cls, side: str) -> BrokerOrderSide:
        """Convert string to BrokerOrderSide."""
        side_normalized = side.lower().strip()
        if side_normalized == "buy":
            return cls.BUY
        elif side_normalized == "sell":
            return cls.SELL
        else:
            raise ValueError(f"Invalid order side: {side}")
    
    def to_alpaca(self) -> str:
        """Convert to Alpaca OrderSide value."""
        # Import here to avoid circular dependency
        from alpaca.trading.enums import OrderSide as AlpacaOrderSide
        
        if self == BrokerOrderSide.BUY:
            return AlpacaOrderSide.BUY.value
        elif self == BrokerOrderSide.SELL:
            return AlpacaOrderSide.SELL.value
        else:
            raise ValueError(f"Unknown order side: {self}")


class BrokerTimeInForce(Enum):
    """Broker-agnostic time in force enumeration."""
    
    DAY = "day"
    GTC = "gtc"  # Good Till Canceled
    IOC = "ioc"  # Immediate or Cancel
    FOK = "fok"  # Fill or Kill
    
    @classmethod
    def from_string(cls, tif: str) -> BrokerTimeInForce:
        """Convert string to BrokerTimeInForce."""
        tif_normalized = tif.lower().strip()
        mapping = {
            "day": cls.DAY,
            "gtc": cls.GTC,
            "ioc": cls.IOC,
            "fok": cls.FOK,
        }
        
        if tif_normalized in mapping:
            return mapping[tif_normalized]
        else:
            raise ValueError(f"Invalid time in force: {tif}")
    
    def to_alpaca(self) -> str:
        """Convert to Alpaca TimeInForce value."""
        # Import here to avoid circular dependency
        from alpaca.trading.enums import TimeInForce as AlpacaTimeInForce
        
        mapping = {
            BrokerTimeInForce.DAY: AlpacaTimeInForce.DAY,
            BrokerTimeInForce.GTC: AlpacaTimeInForce.GTC, 
            BrokerTimeInForce.IOC: AlpacaTimeInForce.IOC,
            BrokerTimeInForce.FOK: AlpacaTimeInForce.FOK,
        }
        
        if self in mapping:
            return mapping[self]
        else:
            raise ValueError(f"Unknown time in force: {self}")


__all__ = [
    "OrderSideType",
    "TimeInForceType", 
    "BrokerOrderSide",
    "BrokerTimeInForce",
]