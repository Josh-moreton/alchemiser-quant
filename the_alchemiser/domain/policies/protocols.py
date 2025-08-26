"""Protocol interfaces for external dependencies used by policies.

These protocols define the minimal interface contracts that policies need
from external services, providing type safety while maintaining loose coupling.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Protocol


class TradingClientProtocol(Protocol):
    """Protocol for trading client dependencies used by policies."""

    def get_account(self) -> Any:
        """Get account information including buying power and balances."""
        ...

    def get_all_positions(self) -> list[Any]:
        """Get all current positions."""
        ...


class DataProviderProtocol(Protocol):
    """Protocol for data provider dependencies used by policies."""

    def get_current_price(self, symbol: str) -> Decimal:
        """Get current market price for a symbol."""
        ...
