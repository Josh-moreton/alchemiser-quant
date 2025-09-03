"""Business Unit: strategy & signal generation; Status: legacy

DEPRECATED: Strategy Market Data Service

This service is deprecated. Use the canonical MarketDataService from 
strategy.data.market_data_service instead. All functionality has been 
consolidated into the canonical service.
"""

# This file is kept for backward compatibility but will be removed
# All functionality has been moved to the canonical MarketDataService
from the_alchemiser.strategy.data.market_data_service import MarketDataService as StrategyMarketDataService

__all__ = ["StrategyMarketDataService"]