"""Business Unit: shared | Status: current.

Strategy tracking protocols for typing.

Defines minimal interfaces for strategy tracking objects to provide type safety
while maintaining flexibility for different implementations and avoiding direct imports.

These protocols enforce financial precision (Decimal for money) and timezone awareness
(UTC datetime) in accordance with system guardrails.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Protocol, runtime_checkable

__all__ = [
    "StrategyOrderProtocol",
    "StrategyOrderTrackerProtocol",
    "StrategyPnLSummaryProtocol",
    "StrategyPositionProtocol",
]


@runtime_checkable
class StrategyPositionProtocol(Protocol):
    """Protocol for strategy position objects.

    Defines the interface for tracking individual position details within a strategy.
    All monetary values use Decimal for precision, and timestamps must be timezone-aware (UTC).

    Implementations must ensure:
    - strategy and symbol are non-empty strings
    - quantity uses Decimal for precision
    - average_cost and total_cost use Decimal for money
    - last_updated is timezone-aware datetime in UTC
    - All properties are read-only

    Example conforming implementation:
        class StrategyPosition:
            def __init__(self, strategy: str, symbol: str, qty: Decimal, cost: Decimal):
                self._strategy = strategy
                self._symbol = symbol
                self._quantity = qty
                self._average_cost = cost
                self._total_cost = qty * cost
                self._last_updated = datetime.now(UTC)

            @property
            def strategy(self) -> str:
                return self._strategy
            # ... other properties
    """

    @property
    def strategy(self) -> str:
        """Strategy name.

        Returns:
            Non-empty string identifying the strategy (e.g., "NUCLEAR", "TECL").

        """
        ...

    @property
    def symbol(self) -> str:
        """Trading symbol.

        Returns:
            Non-empty uppercase ticker symbol (e.g., "SPY", "AAPL").

        """
        ...

    @property
    def quantity(self) -> Decimal:
        """Position quantity.

        Returns:
            Position size as Decimal for precision.
            Positive for long positions, negative for short positions.

        """
        ...

    @property
    def average_cost(self) -> Decimal:
        """Average entry cost per share.

        Returns:
            Average cost basis per share as Decimal for money precision.
            Must be non-negative.

        """
        ...

    @property
    def total_cost(self) -> Decimal:
        """Total cost basis.

        Returns:
            Total cost basis (quantity * average_cost) as Decimal.
            Must be non-negative for long positions.

        """
        ...

    @property
    def last_updated(self) -> datetime:
        """Last update timestamp.

        Returns:
            Timezone-aware datetime in UTC indicating when position was last updated.

        Note:
            Must be timezone-aware (tzinfo is not None).
            System enforces UTC timezone for all trading timestamps.

        """
        ...


@runtime_checkable
class StrategyPnLSummaryProtocol(Protocol):
    """Protocol for strategy P&L summary objects.

    Defines the interface for strategy performance and P&L tracking.
    All monetary values use Decimal for precision. Percentages are floats (0.0-1.0 or 0-100 as documented).
    Timestamps must be timezone-aware (UTC).

    Implementations must ensure:
    - All P&L and cost values use Decimal for money precision
    - Counts (total_orders, position_count) are non-negative integers
    - success_rate is in range [0.0, 100.0] representing percentage (0-100%)
    - total_return_pct is in range [-100.0, +inf] representing percentage return
    - total_pnl equals sum of realized_pnl and unrealized_pnl
    - total_profit_loss is an alias for total_pnl (returns same value)
    - last_updated is timezone-aware datetime in UTC
    - All properties are read-only

    Note on edge cases:
    - success_rate returns 0.0 when total_orders is 0
    - avg_profit_per_trade returns Decimal('0') when total_orders is 0
    - total_return_pct calculated as (total_pnl / cost_basis * 100) if cost_basis > 0, else 0.0

    Example conforming implementation:
        class StrategyPnLSummary:
            def __init__(self, realized: Decimal, unrealized: Decimal, basis: Decimal):
                self._realized_pnl = realized
                self._unrealized_pnl = unrealized
                self._cost_basis = basis
                self._total_orders = 10
                self._successful_orders = 8
                self._last_updated = datetime.now(UTC)

            @property
            def total_pnl(self) -> Decimal:
                return self._realized_pnl + self._unrealized_pnl

            @property
            def success_rate(self) -> float:
                return (self._successful_orders / self._total_orders * 100.0
                        if self._total_orders > 0 else 0.0)
            # ... other properties
    """

    @property
    def total_pnl(self) -> Decimal:
        """Total profit and loss.

        Returns:
            Sum of realized and unrealized P&L as Decimal.
            Positive values indicate profit, negative indicate loss.

        """
        ...

    @property
    def total_profit_loss(self) -> Decimal:
        """Total profit and loss (alias for total_pnl).

        Returns:
            Same value as total_pnl. Provided for backward compatibility.
            Positive values indicate profit, negative indicate loss.

        Note:
            This is an alias property. Implementations should return
            the same value as total_pnl to maintain consistency.

        """
        ...

    @property
    def total_orders(self) -> int:
        """Total number of orders.

        Returns:
            Non-negative integer count of all orders (both successful and failed).

        """
        ...

    @property
    def success_rate(self) -> float:
        """Success rate as a percentage.

        Returns:
            Success rate in range [0.0, 100.0] where 100.0 represents 100%.
            Calculated as (successful_orders / total_orders * 100).
            Returns 0.0 when total_orders is 0.

        """
        ...

    @property
    def avg_profit_per_trade(self) -> Decimal:
        """Average profit per trade.

        Returns:
            Average P&L per trade as Decimal.
            Calculated as (total_pnl / total_orders).
            Returns Decimal('0') when total_orders is 0.

        """
        ...

    @property
    def total_return_pct(self) -> float:
        """Total return percentage.

        Returns:
            Total return as percentage in range [-100.0, +inf].
            Calculated as (total_pnl / cost_basis * 100).
            Returns 0.0 when cost_basis is 0.
            -100.0 represents total loss, 0.0 is break-even, positive is profit.

        """
        ...

    @property
    def position_count(self) -> int:
        """Number of open positions.

        Returns:
            Non-negative integer count of currently open positions.

        """
        ...

    @property
    def realized_pnl(self) -> Decimal:
        """Realized profit and loss.

        Returns:
            P&L from closed positions as Decimal.
            Positive for realized gains, negative for realized losses.

        """
        ...

    @property
    def unrealized_pnl(self) -> Decimal:
        """Unrealized profit and loss.

        Returns:
            Mark-to-market P&L from open positions as Decimal.
            Positive for unrealized gains, negative for unrealized losses.

        """
        ...

    @property
    def cost_basis(self) -> Decimal:
        """Cost basis for return calculation.

        Returns:
            Total cost basis of positions as Decimal.
            Used as denominator for calculating total_return_pct.
            Must be non-negative.

        """
        ...

    @property
    def last_updated(self) -> datetime:
        """Last update timestamp.

        Returns:
            Timezone-aware datetime in UTC indicating when summary was last updated.

        Note:
            Must be timezone-aware (tzinfo is not None).
            System enforces UTC timezone for all trading timestamps.

        """
        ...


@runtime_checkable
class StrategyOrderProtocol(Protocol):
    """Protocol for strategy order objects.

    Defines minimal interface for order tracking and display.
    This is a lightweight protocol for tracking order metadata without
    requiring full order object dependencies.

    Implementations must ensure:
    - order_id is a unique non-empty string
    - strategy identifies the originating strategy
    - symbol is the traded ticker symbol
    - All properties are read-only

    Example conforming implementation:
        class StrategyOrder:
            def __init__(self, order_id: str, strategy: str, symbol: str):
                self._order_id = order_id
                self._strategy = strategy
                self._symbol = symbol

            @property
            def order_id(self) -> str:
                return self._order_id

            @property
            def strategy(self) -> str:
                return self._strategy

            @property
            def symbol(self) -> str:
                return self._symbol
    """

    @property
    def order_id(self) -> str:
        """Unique order identifier.

        Returns:
            Non-empty string uniquely identifying this order.

        """
        ...

    @property
    def strategy(self) -> str:
        """Strategy name that created this order.

        Returns:
            Non-empty string identifying the strategy (e.g., "NUCLEAR", "TECL").

        """
        ...

    @property
    def symbol(self) -> str:
        """Trading symbol for this order.

        Returns:
            Non-empty uppercase ticker symbol (e.g., "SPY", "AAPL").

        """
        ...


@runtime_checkable
class StrategyOrderTrackerProtocol(Protocol):
    """Protocol for strategy order tracker interface.

    Defines the interface for tracking and retrieving strategy positions, P&L, and orders.
    This protocol is implemented by tracking services that aggregate and report
    strategy performance data.

    Implementations must ensure:
    - Methods return appropriate data structures or handle missing strategies gracefully
    - All returned objects conform to their respective protocols
    - Thread-safe access if used in concurrent contexts
    - Methods are idempotent (can be called multiple times safely)

    Method contracts:
    - get_positions_summary: Always returns a list (empty if no positions)
    - get_pnl_summary: May raise KeyError if strategy_name not found
    - get_orders_for_strategy: Always returns a list (empty if no orders)
    - get_strategy_summary: Returns None if strategy_name not found, otherwise summary

    Example conforming implementation:
        class StrategyOrderTracker:
            def __init__(self):
                self._positions: dict[str, list[StrategyPositionProtocol]] = {}
                self._summaries: dict[str, StrategyPnLSummaryProtocol] = {}
                self._orders: dict[str, list[StrategyOrderProtocol]] = {}

            def get_positions_summary(self) -> list[StrategyPositionProtocol]:
                return [pos for positions in self._positions.values() for pos in positions]

            def get_pnl_summary(self, strategy_name: str) -> StrategyPnLSummaryProtocol:
                if strategy_name not in self._summaries:
                    raise KeyError(f"Strategy {strategy_name} not found")
                return self._summaries[strategy_name]

            def get_orders_for_strategy(self, strategy_name: str) -> list[StrategyOrderProtocol]:
                return self._orders.get(strategy_name, [])

            def get_strategy_summary(self, strategy_name: str) -> StrategyPnLSummaryProtocol | None:
                return self._summaries.get(strategy_name)
    """

    def get_positions_summary(self) -> list[StrategyPositionProtocol]:
        """Get all positions across all strategies.

        Returns:
            List of position objects conforming to StrategyPositionProtocol.
            Returns empty list if no positions exist.

        Note:
            This method aggregates positions from all tracked strategies.
            The returned list is a snapshot at call time.

        """
        ...

    def get_pnl_summary(self, strategy_name: str) -> StrategyPnLSummaryProtocol:
        """Get P&L summary for a specific strategy.

        Args:
            strategy_name: Name of the strategy to query (e.g., "NUCLEAR", "TECL").

        Returns:
            P&L summary object conforming to StrategyPnLSummaryProtocol.

        Raises:
            KeyError: If strategy_name is not found in tracked strategies.

        Note:
            The returned summary is a snapshot at call time.
            For real-time P&L, implementations should recalculate on each call.

        """
        ...

    def get_orders_for_strategy(self, strategy_name: str) -> list[StrategyOrderProtocol]:
        """Get all orders for a specific strategy.

        Args:
            strategy_name: Name of the strategy to query (e.g., "NUCLEAR", "TECL").

        Returns:
            List of order objects conforming to StrategyOrderProtocol.
            Returns empty list if strategy has no orders or strategy not found.

        Note:
            Unlike get_pnl_summary, this method does not raise KeyError for unknown strategies.
            It returns an empty list for graceful handling of missing strategies.

        """
        ...

    def get_strategy_summary(self, strategy_name: str) -> StrategyPnLSummaryProtocol | None:
        """Get strategy summary for a specific strategy (optional variant).

        Args:
            strategy_name: Name of the strategy to query (e.g., "NUCLEAR", "TECL").

        Returns:
            P&L summary object conforming to StrategyPnLSummaryProtocol if found.
            Returns None if strategy_name is not found in tracked strategies.

        Note:
            This is a convenience method that returns None instead of raising KeyError.
            Use get_pnl_summary if you want an exception for missing strategies.
            The returned summary is a snapshot at call time.

        """
        ...
