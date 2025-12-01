#!/usr/bin/env python3
"""Business Unit: execution | Status: current.

New execution module built around DTO consumption principle.

This module provides a clean, minimal execution system that:
- Consumes RebalancePlan without recalculation
- Delegates order placement to shared AlpacaManager
- Focuses solely on order execution
- Maintains clean module boundaries
- Communicates exclusively via events in the event-driven architecture

Public API (Event-Driven):
- register_execution_handlers: Event handler registration for orchestration

Legacy API (Being Phased Out):
- ExecutionManager: Direct access manager (for migration only)
- ExecutionResult: Result DTO (for migration only)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer


# Event-driven public API
def register_execution_handlers(
    container: ApplicationContainer, event_bus: object | None = None
) -> None:
    """Register execution event handlers with the orchestration system.

    This is the primary integration point for the execution module in
    the event-driven architecture.

    Args:
        container: Application container for dependency injection

    Example:
        >>> from the_alchemiser.shared.config.container import ApplicationContainer
        >>> container = ApplicationContainer.create_for_environment("development")
        >>> register_execution_handlers(container)

    """
    from .handlers import TradingExecutionHandler

    # Get event bus from container unless an adapter is supplied
    event_bus = event_bus or container.services.event_bus()

    # Initialize and register handlers
    execution_handler = TradingExecutionHandler(container)

    # Register handlers for their respective events using event type strings
    event_bus.subscribe("RebalancePlanned", execution_handler)


def __getattr__(name: str) -> object:
    """Lazy attribute access for legacy exports.

    Avoids importing heavy legacy modules at import time while preserving the
    public API during the migration period.
    """
    if name == "ExecutionManager":
        from .core.execution_manager import ExecutionManager as _ExecutionManager

        return _ExecutionManager
    if name == "ExecutionResult":
        from .models.execution_result import ExecutionResult as _ExecutionResult

        return _ExecutionResult
    if name == "TradeLedgerService":
        from .services.trade_ledger import TradeLedgerService as _TradeLedgerService

        return _TradeLedgerService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "ExecutionManager",
    "ExecutionResult",
    "TradeLedgerService",
    "register_execution_handlers",
]

# Version for compatibility tracking
__version__ = "2.0.0"
