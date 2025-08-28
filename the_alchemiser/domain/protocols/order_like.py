"""Business Unit: utilities; Status: current.

Protocol for order-like objects with common order attributes.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class OrderLikeProtocol(Protocol):
    """Protocol for objects that behave like order data.

    This covers both Alpaca order objects and order dictionaries.
    Used to replace unsafe Any usage in order handling code.
    """

    @property
    def id(self) -> str:
        """Order ID."""
        ...

    @property
    def symbol(self) -> str:
        """Order symbol."""
        ...

    @property
    def qty(self) -> float:
        """Order quantity."""
        ...

    @property
    def side(self) -> str:
        """Order side (buy/sell)."""
        ...

    @property
    def order_type(self) -> str:
        """Order type (market/limit/stop)."""
        ...

    @property
    def status(self) -> str:
        """Order status."""
        ...

    @property
    def limit_price(self) -> float | None:
        """Limit price (if applicable)."""
        ...

    @property
    def stop_price(self) -> float | None:
        """Stop price (if applicable)."""
        ...
