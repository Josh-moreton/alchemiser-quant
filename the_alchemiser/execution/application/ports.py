"""Business Unit: order execution/placement; Status: current.

Application-layer ports module for trading engine.

This module aggregates stable Protocol interfaces that the decomposed trading
engine depends upon. It reuses existing domain protocols and introduces minimal
new abstractions only where no suitable existing protocol covers the seam.

Design decisions:
- Reuse canonical MarketDataPort from domain/market_data (Symbol + domain models)
- Introduce minimal new protocols only for application-level concerns
- Use existing domain value objects (Symbol, StrategySignal, Order, etc.)
- Enable parallel refactors while preventing signature drift
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from datetime import datetime
from decimal import Decimal
from typing import Protocol, runtime_checkable

# Re-export canonical MarketDataPort (reuse; no duplication)
from the_alchemiser.strategy.infrastructure.protocols.market_data_port import MarketDataPort
from the_alchemiser.shared_kernel.value_objects.symbol import Symbol
from the_alchemiser.strategy.domain.value_objects.strategy_signal import StrategySignal
from the_alchemiser.execution.domain.entities.order import Order


@runtime_checkable
class AccountReadPort(Protocol):
    """Read-only account information access.

    No existing narrow read-only abstraction exposed in domain layer.
    This protocol provides essential account data without broad service interface.
    """

    def get_cash(self) -> Decimal:
        """Get available cash balance."""
        ...

    def get_positions(self) -> Sequence[Order]:
        """Get current positions as domain Order entities."""
        ...

    def get_equity(self) -> Decimal:
        """Get total account equity."""
        ...

    def get_buying_power(self) -> Decimal:
        """Get available buying power."""
        ...


@runtime_checkable
class OrderExecutionPort(Protocol):
    """Order submission and management operations.

    No existing ExecutionPort found in domain layer covering batch operations
    and cancellation by symbols. This protocol provides essential order execution
    operations for the application layer.
    """

    def submit_orders(self, orders: Sequence[Order]) -> list[Order]:
        """Submit multiple orders and return updated orders with execution details."""
        ...

    def cancel_open_orders(self, symbols: Iterable[Symbol]) -> None:
        """Cancel all open orders for specified symbols."""
        ...


@runtime_checkable
class StrategyAdapterPort(Protocol):
    """Strategy signal generation adapter.

    No existing protocol aggregates all active strategies into typed StrategySignal
    objects. This protocol provides unified strategy signal generation for the
    application orchestrator.
    """

    def generate_signals(self, now: datetime) -> list[StrategySignal]:
        """Generate signals from all active strategies."""
        ...


@runtime_checkable
class RebalancingOrchestratorPort(Protocol):
    """High-level portfolio rebalancing orchestration.

    No existing protocol covers the sequential SELL → settle → BUY orchestration
    pattern. This protocol provides the high-level rebalancing workflow that
    the application layer requires.
    """

    def execute_rebalance_cycle(self, now: datetime) -> None:
        """Execute complete rebalancing cycle with settlement handling."""
        ...

    def dry_run(self, now: datetime) -> dict[str, float]:
        """Perform dry run and return target allocations preview."""
        ...


class ReportingPort(Protocol):
    """Optional reporting abstraction for rendering/notification.

    This protocol is optional and may be moved to interface layer if rendering
    is kept concrete rather than abstract.
    """

    def emit_rebalance_summary(self, preview: dict[str, float]) -> None:
        """Emit rebalancing summary for reporting/notification."""
        ...


# Export list for explicit re-exports
__all__ = [
    "AccountReadPort",
    "MarketDataPort",  # Re-exported from domain/market_data
    "OrderExecutionPort",
    "RebalancingOrchestratorPort",
    "ReportingPort",
    "StrategyAdapterPort",
]
