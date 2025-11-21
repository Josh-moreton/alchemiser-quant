"""Business Unit: execution | Status: current.

Unified order placement components.

This package provides a clean, unified interface for order placement that:
- Uses a single quote acquisition path (streaming-first with REST fallback)
- Has clear order intent abstractions (BUY/SELL_PARTIAL/SELL_FULL)
- Implements explicit "walk the book" strategy (75% → 85% → 95% → market)
- Validates portfolio state after execution
- Provides a single entry point for all order placement
"""

from .order_intent import CloseType, OrderIntent, OrderSide, Urgency
from .placement_service import ExecutionResult, UnifiedOrderPlacementService
from .portfolio_validator import PortfolioValidator, ValidationResult
from .quote_service import QuoteResult, QuoteSource, UnifiedQuoteService
from .walk_the_book import OrderAttempt, OrderStatus, WalkResult, WalkTheBookStrategy

__all__ = [
    # Order intent abstractions
    "OrderIntent",
    "OrderSide",
    "CloseType",
    "Urgency",
    # Quote service
    "UnifiedQuoteService",
    "QuoteResult",
    "QuoteSource",
    # Walk the book strategy
    "WalkTheBookStrategy",
    "WalkResult",
    "OrderAttempt",
    "OrderStatus",
    # Portfolio validation
    "PortfolioValidator",
    "ValidationResult",
    # Main service
    "UnifiedOrderPlacementService",
    "ExecutionResult",
]
