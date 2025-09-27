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
def register_execution_handlers(container: ApplicationContainer) -> None:
    """Register execution event handlers with the orchestration system.
    
    This is the primary integration point for the execution module in
    the event-driven architecture.
    
    Args:
        container: Application container for dependency injection
    """
    from .handlers import TradingExecutionHandler
    
    # Get event bus from container
    event_bus = container.services.event_bus()
    
    # Initialize and register handlers
    execution_handler = TradingExecutionHandler(container)
    
    # Register handlers for their respective events using event type strings
    event_bus.subscribe("RebalancePlanned", execution_handler)


# Legacy imports for migration compatibility - these will be removed
from the_alchemiser.execution_v2.core.execution_manager import ExecutionManager
from the_alchemiser.execution_v2.models.execution_result import ExecutionResult

__all__ = [
    "register_execution_handlers",  # Primary event-driven API
    # Legacy exports (being phased out)
    "ExecutionManager",
    "ExecutionResult",
]
