"""Business Unit: execution | Status: current.

Smart execution configuration and models.

This package provides configuration and data models for order execution.
The actual execution is now handled by the unified order placement service.
"""

from .models import ExecutionConfig, LiquidityMetadata, SmartOrderRequest, SmartOrderResult
from .quotes import QuoteProvider

__all__ = [
    "ExecutionConfig",
    "LiquidityMetadata",
    "QuoteProvider",
    "SmartOrderRequest",
    "SmartOrderResult",
]
