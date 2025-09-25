"""Business Unit: execution | Status: current.

New execution module built around DTO consumption principle.

This module provides a clean, minimal execution system that:
- Consumes RebalancePlan without recalculation
- Delegates order placement to shared AlpacaManager
- Focuses solely on order execution
- Maintains clean module boundaries
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from the_alchemiser.execution_v2.handlers.trading_execution_handler import (
        TradingExecutionHandler,
    )
    from the_alchemiser.shared.config.container import ApplicationContainer
    from the_alchemiser.shared.registry.handler_registry import EventHandlerRegistry

from the_alchemiser.execution_v2.core.execution_manager import ExecutionManager
from the_alchemiser.execution_v2.models.execution_result import ExecutionResult

__all__ = [
    "ExecutionManager",
    "ExecutionResult",
    "register_execution_handlers",
]


def register_execution_handlers(
    container: ApplicationContainer, registry: EventHandlerRegistry
) -> None:
    """Register execution event handlers with the handler registry.

    Args:
        container: Application DI container
        registry: Event handler registry

    """
    from .handlers.trading_execution_handler import TradingExecutionHandler

    def execution_handler_factory() -> TradingExecutionHandler:
        """Create TradingExecutionHandler."""
        return TradingExecutionHandler(container)

    # Register handler for events this module can handle
    registry.register_handler(
        event_type="RebalancePlanned",
        handler_factory=execution_handler_factory,
        module_name="execution_v2",
        priority=100,
        metadata={"description": "Executes trades from rebalance plan"},
    )
