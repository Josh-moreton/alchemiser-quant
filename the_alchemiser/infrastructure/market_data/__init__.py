"""Business Unit: utilities; Status: current.

Market data services package exports.

Prefer MarketDataService as the canonical typed service. StrategyMarketDataService
is deprecated and will be removed once all callers are migrated.
"""

from __future__ import annotations

from .market_data_service import MarketDataService
from .strategy_market_data_service import (
    StrategyMarketDataService,
)

__all__ = ["MarketDataService", "StrategyMarketDataService"]
