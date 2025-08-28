"""Business Unit: utilities; Status: current.

Market data services package exports.

Prefer MarketDataService as the canonical typed service. StrategyMarketDataService
is deprecated and will be removed once all callers are migrated.
"""

from the_alchemiser.services.market_data.market_data_service import MarketDataService
from the_alchemiser.services.market_data.strategy_market_data_service import (
    StrategyMarketDataService,
)

__all__ = ["MarketDataService", "StrategyMarketDataService"]
