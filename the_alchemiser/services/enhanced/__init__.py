"""
Enhanced Services Layer

This package contains enhanced services that build on top of our domain interfaces.
These services provide higher-level business logic operations while maintaining
type safety and testability.

Following our incremental improvement strategy, these services are:
1. Optional - existing code continues to work
2. Interface-based - depend on abstractions, not implementations
3. Type-safe - full mypy compliance
4. Testable - easy to mock dependencies
5. Focused - single responsibility per service

Current services:
- OrderService: Enhanced order placement with validation
- PositionService: Position management and tracking
- MarketDataService: Intelligent market data operations with caching
- AccountService: Account management with risk metrics and validation
- TradingServiceManager: Centralized facade for all trading operations

These services represent a step toward our eventual architecture vision while
providing immediate value and maintaining backward compatibility.
"""

from .account_service import AccountService
from .market_data_service import MarketDataService
from .order_service import OrderService, OrderType, OrderValidationError
from .position_service import (
    PortfolioSummary,
    PositionInfo,
    PositionService,
    PositionValidationError,
)
from .trading_service_manager import TradingServiceManager

__all__ = [
    "AccountService",
    "MarketDataService",
    "OrderService",
    "OrderValidationError",
    "OrderType",
    "PositionInfo",
    "PositionService",
    "PositionValidationError",
    "PortfolioSummary",
    "TradingServiceManager",
]
