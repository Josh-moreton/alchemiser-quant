"""Business Unit: shared | Status: current.

Internal data models and subscription planning structures for the pricing service.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from alpaca.data.models import Quote, Trade

    # Type aliases for static type checking - can be either dict or Alpaca objects
    AlpacaQuoteData = dict[str, str | float | int] | Quote
    AlpacaTradeData = dict[str, str | float | int] | Trade
else:
    # Runtime type aliases - no forward references, use object for flexibility
    AlpacaQuoteData = dict[str, str | float | int] | object
    AlpacaTradeData = dict[str, str | float | int] | object


@dataclass
class RealTimeQuote:
    """Real-time quote data structure (legacy compatibility)."""

    bid: float
    ask: float
    last_price: float
    timestamp: datetime

    @property
    def mid_price(self) -> float:
        """Calculate mid-point between bid and ask."""
        if self.bid > 0 and self.ask > 0:
            return (self.bid + self.ask) / 2
        if self.bid > 0:
            return self.bid
        if self.ask > 0:
            return self.ask
        return self.last_price


@dataclass
class SubscriptionPlan:
    """Internal helper class for bulk subscription planning."""

    results: dict[str, bool]
    symbols_to_add: list[str]
    symbols_to_replace: list[str]
    available_slots: int
    successfully_added: int = 0


@dataclass
class QuoteValues:
    """Container for quote values extracted from incoming data."""

    bid_price: float | None
    ask_price: float | None
    bid_size: float | None
    ask_size: float | None
    timestamp_raw: datetime | None