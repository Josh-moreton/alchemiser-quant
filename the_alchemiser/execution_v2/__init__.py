"""Business Unit: execution | Status: current.

Execution module for smart order placement and trade execution.

This module provides a clean, minimal execution system that:
- Consumes RebalancePlanDTO without recalculation
- Delegates order placement to shared AlpacaManager
- Focuses solely on order execution with smart strategies
- Maintains clean module boundaries
- Supports liquidity-aware anchoring and market timing
"""

from the_alchemiser.execution_v2.core.execution_manager import ExecutionManager
from the_alchemiser.execution_v2.core.executor import Executor
from the_alchemiser.execution_v2.models.execution_result import ExecutionResultDTO
from the_alchemiser.execution_v2.strategies.smart_limit_strategy import SmartLimitExecutionStrategy
from the_alchemiser.execution_v2.strategies.async_smart_strategy import AsyncSmartExecutionStrategy
from the_alchemiser.execution_v2.utils.market_timing import MarketTimingUtils

__all__ = [
    "ExecutionManager",
    "Executor", 
    "ExecutionResultDTO",
    "SmartLimitExecutionStrategy",
    "AsyncSmartExecutionStrategy",
    "MarketTimingUtils",
]
