"""Business Unit: order execution/placement; Status: current."""

from __future__ import annotations

from typing import Protocol


class TradingRepository(Protocol):
    """Trading repository interface (domain-level).

    Intentionally abstract and independent of external client models.
    Concrete infrastructure adapters (e.g., Alpaca) should implement this.
    """

    # Placeholder methods to be refined alongside adapters and mappings.
    # Using domain-friendly contracts avoids leaking infrastructure types.

    def get_account_portfolio_value(self) -> str:
        """Return portfolio value as stringified decimal to avoid float leaks."""
        ...
