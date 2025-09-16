"""Business Unit: utilities; Status: current.

Domain model for a bid/ask quote.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class QuoteModel:
    """Market quote with bid/ask prices and timestamp.
    
    Represents a point-in-time bid/ask quote for a financial instrument.
    """
    
    ts: datetime | None
    bid: Decimal
    ask: Decimal

    @property
    def mid(self) -> Decimal:
        """Calculate the mid-point price between bid and ask."""
        return (self.bid + self.ask) / Decimal("2")
