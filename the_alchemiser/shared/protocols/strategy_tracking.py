"""Business Unit: shared | Status: current.

Strategy tracking protocols for typing.

Defines minimal interfaces for strategy tracking objects to provide type safety
while maintaining flexibility for different implementations and avoiding direct imports.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, runtime_checkable


@runtime_checkable
class StrategyPositionProtocol(Protocol):
    """Protocol for strategy position objects."""

    @property
    def strategy(self) -> str:
        """Strategy name."""
        ...

    @property
    def symbol(self) -> str:
        """Trading symbol."""
        ...

    @property
    def quantity(self) -> float:
        """Position quantity."""
        ...

    @property
    def average_cost(self) -> float:
        """Average entry cost."""
        ...

    @property
    def total_cost(self) -> float:
        """Total cost basis."""
        ...

    @property
    def last_updated(self) -> datetime:
        """Last update timestamp."""
        ...


@runtime_checkable
class StrategyPnLSummaryProtocol(Protocol):
    """Protocol for strategy PnL summary objects."""

    @property
    def total_pnl(self) -> float:
        """Total profit and loss."""
        ...

    @property
    def total_profit_loss(self) -> float:
        """Total profit and loss (alias for total_pnl)."""
        ...

    @property
    def total_orders(self) -> int:
        """Total number of orders."""
        ...

    @property
    def success_rate(self) -> float:
        """Success rate as a percentage."""
        ...

    @property
    def avg_profit_per_trade(self) -> float:
        """Average profit per trade."""
        ...

    @property
    def total_return_pct(self) -> float:
        """Total return percentage."""
        ...

    @property
    def position_count(self) -> int:
        """Number of positions."""
        ...

    @property
    def realized_pnl(self) -> float:
        """Realized profit and loss."""
        ...

    @property
    def unrealized_pnl(self) -> float:
        """Unrealized profit and loss."""
        ...

    @property
    def cost_basis(self) -> float:
        """Cost basis for return calculation."""
        ...

    @property
    def last_updated(self) -> datetime:
        """Last update timestamp."""
        ...


@runtime_checkable
class StrategyOrderProtocol(Protocol):
    """Protocol for strategy order objects."""

    # Basic order-like interface - minimal requirements for tracking display


@runtime_checkable
class StrategyOrderTrackerProtocol(Protocol):
    """Protocol for strategy order tracker interface."""

    def get_positions_summary(self) -> list[StrategyPositionProtocol]:
        """Get positions summary."""
        ...

    def get_pnl_summary(self, strategy_name: str) -> StrategyPnLSummaryProtocol:
        """Get PnL summary for strategy."""
        ...

    def get_orders_for_strategy(self, strategy_name: str) -> list[StrategyOrderProtocol]:
        """Get orders for strategy."""
        ...

    def get_strategy_summary(self, strategy_name: str) -> StrategyPnLSummaryProtocol | None:
        """Get strategy summary for strategy."""
        ...
