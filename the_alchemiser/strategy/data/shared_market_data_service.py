"""Business Unit: strategy | Status: legacy

Market data services package exports.

StrategyMarketDataService is DEPRECATED and has been removed. Use MarketDataService
as the canonical typed service for all market data operations.
"""

from __future__ import annotations

from the_alchemiser.strategy.data.market_data_service import MarketDataService

# Import deprecated service for backward compatibility
from the_alchemiser.strategy.data.strategy_market_data_service import (
    StrategyMarketDataService,
)

__all__ = ["MarketDataService", "StrategyMarketDataService"]
