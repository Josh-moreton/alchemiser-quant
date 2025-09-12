"""Business Unit: portfolio | Status: current

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

from .core.planner import RebalancePlanCalculator
from .core.portfolio_service import PortfolioServiceV2

__all__ = [
    "PortfolioServiceV2",
    "RebalancePlanCalculator",
]
