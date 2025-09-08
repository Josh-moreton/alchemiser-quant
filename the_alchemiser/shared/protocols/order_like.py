"""Business Unit: shared | Status: current.

Order-like Object Protocol.

Defines minimal interfaces for objects that have order-like attributes.
Used in mapping functions to provide type safety while maintaining flexibility
for different order object implementations (domain entities, Alpaca SDK objects, etc.).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class OrderLikeProtocol(Protocol):
    """Protocol for objects that have basic order attributes.

    Used in mapping functions where order objects from different sources
    (domain entities, broker SDK objects, dicts) need to be normalized.
    """

    @property
    def id(self) -> str | None:
        """Order identifier."""
        ...

    @property
    def symbol(self) -> str:
        """Trading symbol."""
        ...

    @property
    def qty(self) -> float | int | str | None:
        """Order quantity."""
        ...

    @property
    def side(self) -> str:
        """Order side (buy/sell)."""
        ...

    @property
    def order_type(self) -> str | None:
        """Order type (market/limit)."""
        ...

    @property
    def status(self) -> str | None:
        """Order status."""
        ...

    @property
    def filled_qty(self) -> float | int | str | None:
        """Filled quantity."""
        ...


@runtime_checkable
class PositionLikeProtocol(Protocol):
    """Protocol for objects that have basic position attributes.

    Used in mapping functions where position objects from different sources
    need to be normalized.
    """

    @property
    def symbol(self) -> str:
        """Trading symbol."""
        ...

    @property
    def qty(self) -> float | int | str:
        """Position quantity."""
        ...

    @property
    def market_value(self) -> float | int | str | None:
        """Current market value."""
        ...

    @property
    def avg_entry_price(self) -> float | int | str | None:
        """Average entry price."""
        ...
