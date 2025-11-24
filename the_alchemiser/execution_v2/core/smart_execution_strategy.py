"""Business Unit: execution | Status: current.

Smart execution configuration and models.

This module provides the public interface for execution configuration by re-exporting
models from the modular package structure.

Note: The SmartExecutionStrategy class has been replaced by UnifiedOrderPlacementService.
This module now only exports configuration and data models for backward compatibility.
"""

# Re-export configuration and models from the modular structure
from .smart_execution_strategy import (
    ExecutionConfig,
    LiquidityMetadata,
    SmartOrderRequest,
    SmartOrderResult,
)

__all__ = [
    "ExecutionConfig",
    "LiquidityMetadata",
    "SmartOrderRequest",
    "SmartOrderResult",
]
