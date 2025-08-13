"""Core execution models used across the backtest engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

OrderType = Literal["market", "limit"]
OrderSide = Literal["buy", "sell"]


@dataclass(slots=True)
class Order:
    """Represents an order submitted to the broker."""

    id: str
    symbol: str
    qty: int
    side: OrderSide
    type: OrderType
    limit_price: float | None = None
    filled_qty: int = 0


@dataclass(slots=True)
class Fill:
    """Fill resulting from order execution."""

    order_id: str
    symbol: str
    qty: int
    price: float
    timestamp: datetime


@dataclass(slots=True)
class PositionLot:
    """Single FIFO lot."""

    qty: int
    price: float


@dataclass(slots=True)
class Position:
    symbol: str
    lots: list[PositionLot] = field(default_factory=list)


@dataclass(slots=True)
class Account:
    """Simplified account model."""

    cash: float = 0.0
