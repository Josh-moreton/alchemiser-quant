"""Protocol interfaces for external dependencies used by policies.

These protocols define the minimal interface contracts that policies need
from external services, providing type safety while maintaining loose coupling.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Protocol


class DataProviderProtocol(Protocol):
    """Protocol for data provider dependencies used by execution components."""

    def get_current_price(self, symbol: str) -> float | None:
        """Get current market price for a symbol."""
        ...

    def get_latest_quote(self, symbol: str) -> tuple[float, float] | None:
        """Get latest bid/ask quote for a symbol."""
        ...

    def get_positions(self) -> list[Any]:
        """Get all current positions."""
        ...


class TradingClientProtocol(Protocol):
    """Protocol for trading client dependencies used by policies."""

    def get_account(self) -> Any:
        """Get account information including buying power and balances."""
        ...

    def get_all_positions(self) -> list[Any]:
        """Get all current positions."""
        ...

    def get_clock(self) -> Any:
        """Get market clock information."""
        ...

    def get_order_by_id(self, order_id: str) -> Any:
        """Get order by ID."""
        ...
