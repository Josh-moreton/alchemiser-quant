"""Business Unit: portfolio | Status: current.

Portfolio state management and rebalancing logic.

Portfolio_v2 is a minimal, DTO-first module that:
- Consumes StrategyAllocationDTO (from shared.dto)
- Uses shared Alpaca capabilities for current positions/prices
- Produces clean RebalancePlanDTO with BUY/SELL/HOLD items
- Does no order placement, execution hinting, or analytics

This module implements the core design principle:
- Inputs: StrategyAllocationDTO (weights and constraints) + current snapshot (positions, prices, cash)
- Output: RebalancePlanDTO containing BUY/SELL/HOLD items and trade_amounts (Decimal)
- No side effects; no cross-module state; single pass O(n) over symbols
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from the_alchemiser.portfolio_v2.handlers.portfolio_analysis_handler import (
        PortfolioAnalysisHandler,
    )
    from the_alchemiser.shared.config.container import ApplicationContainer
    from the_alchemiser.shared.registry.handler_registry import EventHandlerRegistry

from .core.planner import RebalancePlanCalculator
from .core.portfolio_service import PortfolioServiceV2

__all__ = [
    "PortfolioServiceV2",
    "RebalancePlanCalculator", 
    "register_portfolio_handlers",
]


def register_portfolio_handlers(
    container: ApplicationContainer, registry: EventHandlerRegistry
) -> None:
    """Register portfolio event handlers with the handler registry.
    
    Args:
        container: Application DI container
        registry: Event handler registry

    """
    from .handlers.portfolio_analysis_handler import PortfolioAnalysisHandler
    
    def portfolio_handler_factory() -> PortfolioAnalysisHandler:
        """Create PortfolioAnalysisHandler."""
        return PortfolioAnalysisHandler(container)
    
    # Register handler for events this module can handle
    registry.register_handler(
        event_type="SignalGenerated",
        handler_factory=portfolio_handler_factory,
        module_name="portfolio_v2",
        priority=100,
        metadata={"description": "Analyzes portfolio and creates rebalance plan"}
    )
