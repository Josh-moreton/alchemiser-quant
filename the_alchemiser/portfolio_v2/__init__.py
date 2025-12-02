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
    from the_alchemiser.portfolio_v2.adapters.transports import EventTransport
    from the_alchemiser.shared.config.container import ApplicationContainer


# Event-driven public API
def register_portfolio_handlers(
    container: ApplicationContainer, event_bus: EventTransport | None = None
) -> None:
    """Register portfolio event handlers with the orchestration system.

    This is the primary integration point for the portfolio module in
    the event-driven architecture.

    Args:
        container: Application container for dependency injection

    """
    from .handlers import PortfolioAnalysisHandler

    # Get event bus from container unless an adapter is supplied
    event_bus = event_bus or container.services.event_bus()

    # Initialize and register handlers
    portfolio_handler = PortfolioAnalysisHandler(container)

    # Register handlers for their respective events using event type strings
    event_bus.subscribe("SignalGenerated", portfolio_handler)


def __getattr__(name: str) -> object:
    if name == "PortfolioServiceV2":
        from .core import PortfolioServiceV2 as _PortfolioServiceV2

        return _PortfolioServiceV2
    if name == "RebalancePlanCalculator":
        from .core import RebalancePlanCalculator as _RebalancePlanCalculator

        return _RebalancePlanCalculator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__: list[str] = [
    "PortfolioServiceV2",
    "RebalancePlanCalculator",
    "register_portfolio_handlers",
]
