"""Business Unit: shared | Status: current

Alpaca-specific Protocol Definitions.

Protocols for interacting with Alpaca SDK objects while maintaining type safety.
These are more specific than the generic OrderLikeProtocol and include
Alpaca-specific attributes like time_in_force and timestamps.
"""

from __future__ import annotations

from typing import Protocol


class AlpacaOrderProtocol(Protocol):
    """Protocol for Alpaca order objects."""

    id: str
    symbol: str
    qty: str
    side: str
    order_type: str
    time_in_force: str
    status: str
    filled_qty: str
    filled_avg_price: str | None
    created_at: str
    updated_at: str


class AlpacaOrderObject(Protocol):
    """Protocol for Alpaca order objects used in monitoring."""

    id: str
    status: str
    filled_qty: str
