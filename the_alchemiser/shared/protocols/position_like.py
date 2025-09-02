"""Business Unit: utilities; Status: current.

Protocol for position-like objects with common position attributes.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class PositionLikeProtocol(Protocol):
    """Protocol for objects that behave like position data.

    This covers both Alpaca position objects and position dictionaries.
    Used to replace unsafe Any usage in position handling code.
    """

    @property
    def symbol(self) -> str:
        """Position symbol."""
        ...

    @property
    def qty(self) -> float:
        """Position quantity."""
        ...

    @property
    def market_value(self) -> float:
        """Current market value of position."""
        ...

    @property
    def unrealized_pl(self) -> float:
        """Unrealized P&L."""
        ...

    @property
    def unrealized_plpc(self) -> float:
        """Unrealized P&L percentage."""
        ...

    @property
    def avg_entry_price(self) -> float:
        """Average entry price."""
        ...

    @property
    def current_price(self) -> float:
        """Current price."""
        ...
