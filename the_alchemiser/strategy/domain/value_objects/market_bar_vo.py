"""Business Unit: strategy & signal generation | Status: current

Market data value object for OHLCV bars.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from the_alchemiser.shared_kernel.value_objects.symbol import Symbol


@dataclass(frozen=True)
class MarketBarVO:
    """Immutable market price bar with volume."""

    symbol: Symbol
    timestamp: datetime
    open_price: Decimal
    high_price: Decimal
    low_price: Decimal
    close_price: Decimal
    volume: Decimal
    timeframe: str
    
    def __post_init__(self) -> None:
        """Validate price relationships.
        
        TODO: Add validation for timestamp ranges and trading hours
        FIXME: Consider adding validation for reasonable price ranges
        """
        if not (self.low_price <= self.open_price <= self.high_price):
            raise ValueError("Invalid OHLC relationship: open not within high/low range")
        if not (self.low_price <= self.close_price <= self.high_price):
            raise ValueError("Invalid OHLC relationship: close not within high/low range")
        if self.volume < Decimal("0"):
            raise ValueError("Volume cannot be negative")