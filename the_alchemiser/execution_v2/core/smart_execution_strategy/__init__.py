"""Business Unit: execution | Status: current.

Smart execution strategy package.

This package provides a modular, liquidity-aware order execution strategy
with intelligent re-pegging and market timing capabilities.
"""

from .models import ExecutionConfig, LiquidityMetadata, SmartOrderRequest, SmartOrderResult
from .strategy import SmartExecutionStrategy

__all__ = [
    "ExecutionConfig",
    "LiquidityMetadata",
    "SmartExecutionStrategy",
    "SmartOrderRequest",
    "SmartOrderResult",
]