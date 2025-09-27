"""Business Unit: portfolio | Status: current.

Portfolio state management and rebalancing logic.

Portfolio_v2 is a minimal, DTO-first module that:
- Consumes StrategyAllocation (from shared.schemas)
- Uses shared Alpaca capabilities for current positions/prices
- Produces clean RebalancePlan with BUY/SELL/HOLD items
- Does no order placement, execution hinting, or analytics
- Communicates exclusively via events in the event-driven architecture

This module implements the core design principle:
- Inputs: StrategyAllocation (weights and constraints) + current snapshot (positions, prices, cash)
- Output: RebalancePlan containing BUY/SELL/HOLD items and trade_amounts (Decimal)
- No side effects; no cross-module state; single pass O(n) over symbols

Public API (Event-Driven):
- register_portfolio_handlers: Event handler registration for orchestration

Legacy API (Being Phased Out):
- PortfolioServiceV2: Direct access service (for migration only)
- RebalancePlanCalculator: Internal calculator (for migration only)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from the_alchemiser.shared.config.container import ApplicationContainer


# Event-driven public API
def register_portfolio_handlers(container: ApplicationContainer) -> None:
    """Register portfolio event handlers with the orchestration system.

    This is the primary integration point for the portfolio module in
    the event-driven architecture.

    Args:
        container: Application container for dependency injection

    """
    from .handlers import PortfolioAnalysisHandler

    # Get event bus from container
    event_bus = container.services.event_bus()

    # Initialize and register handlers
    portfolio_handler = PortfolioAnalysisHandler(container)

    # Register handlers for their respective events using event type strings
    event_bus.subscribe("SignalGenerated", portfolio_handler)


# Legacy imports for migration compatibility - these will be removed
from .core.planner import RebalancePlanCalculator
from .core.portfolio_service import PortfolioServiceV2

__all__ = [
    "register_portfolio_handlers",  # Primary event-driven API
    # Legacy exports (being phased out)
    "PortfolioServiceV2",
    "RebalancePlanCalculator",
]
