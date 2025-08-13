"""Event models for the backtest engine.

These are intentionally small and will grow as the engine evolves.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass(slots=True)
class MarketEvent:
    """Simple market data event used by the replayer."""

    timestamp: datetime
    symbol: str
    price: float
    size: int = 1


@dataclass(slots=True)
class TimerEvent:
    """Scheduled timer event for strategies."""

    timestamp: datetime


@dataclass(slots=True)
class OrderEvent:
    """Order lifecycle event emitted by the broker."""

    timestamp: datetime
    order_id: str
    status: Literal["submitted", "filled", "cancelled"]
