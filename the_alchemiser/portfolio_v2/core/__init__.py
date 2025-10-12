#!/usr/bin/env python3
"""Business Unit: portfolio | Status: current.

Core portfolio state management and rebalancing logic.

Provides portfolio state reading, rebalance plan calculation, and 
orchestration services for the portfolio_v2 module.

Components:
- PortfolioServiceV2: Main orchestration facade for portfolio operations
- RebalancePlanCalculator: Core calculator for rebalance plans (BUY/SELL/HOLD)
- PortfolioStateReader: Builds immutable portfolio snapshots from current state

This module exports the core components used by both the event-driven architecture
(via handlers) and legacy direct-access patterns (via parent module's __getattr__).
"""

from __future__ import annotations

from .planner import RebalancePlanCalculator
from .portfolio_service import PortfolioServiceV2
from .state_reader import PortfolioStateReader

__all__ = [
    "PortfolioServiceV2",
    "RebalancePlanCalculator",
    "PortfolioStateReader",
]
