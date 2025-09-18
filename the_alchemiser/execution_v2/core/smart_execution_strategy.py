"""Business Unit: execution | Status: current.

Smart execution strategy for canonical order placement and execution.

This module provides the public interface for smart execution by re-exporting
the refactored SmartExecutionStrategy from the modular package structure.

The original large file has been split into cohesive modules for better
maintainability, testability, and separation of concerns while preserving
the same external API.
"""

# Re-export the main strategy class and types from the modular structure
from .smart_execution_strategy import (
    ExecutionConfig,
    LiquidityMetadata,
    SmartExecutionStrategy,
    SmartOrderRequest,
    SmartOrderResult,
)

__all__ = [
    "ExecutionConfig",
    "LiquidityMetadata",
    "SmartExecutionStrategy",
    "SmartOrderRequest",
    "SmartOrderResult",
]
