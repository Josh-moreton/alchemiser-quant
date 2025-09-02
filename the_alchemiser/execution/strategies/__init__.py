#!/usr/bin/env python3
"""Business Unit: order execution/placement; Status: current.

Execution strategies package.

Contains strategy classes for order execution patterns including
repeg strategies and aggressive limit strategies.
"""

from __future__ import annotations

from .aggressive_limit_strategy import AggressiveLimitStrategy
from .config import StrategyConfig
from .execution_context_adapter import ExecutionContextAdapter
from .repeg_strategy import RepegStrategy
from .smart_execution import OrderExecutor, SmartExecution, is_market_open

__all__ = [
    "AggressiveLimitStrategy",
    "ExecutionContextAdapter",
    "OrderExecutor",
    "RepegStrategy",
    "SmartExecution",
    "StrategyConfig",
    "is_market_open",
]
