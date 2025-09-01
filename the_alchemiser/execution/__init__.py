"""Business Unit: execution | Status: current.

Broker API integrations and order placement.

This module contains order routing, broker connectors, execution strategies, 
and order lifecycle management.
"""

from __future__ import annotations

__all__: list[str] = [
    # Core execution
    "ExecutionManager",
    "CanonicalOrderExecutor",
    
    # Order management
    "OrderValidator", 
    "OrderService",
    "OrderRequestBuilder",
    
    # Broker integration
    "AlpacaManager",
    
    # Execution strategies
    "SmartExecutionEngine",
    "AggressiveLimitStrategy",
    "RepegStrategy",
    
    # Utilities
    "SmartPricingHandler",
    "SpreadAssessment"
]

from .core import ExecutionManager, CanonicalOrderExecutor
from .orders import OrderValidator, OrderService, OrderRequestBuilder
from .brokers import AlpacaManager
from .strategies import SmartExecutionEngine, AggressiveLimitStrategy, RepegStrategy
from .utils import SmartPricingHandler, SpreadAssessment