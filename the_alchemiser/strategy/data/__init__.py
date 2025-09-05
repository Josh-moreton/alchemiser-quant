# Strategy data services and utilities
from .market_data_client import MarketDataClient  # ⚠️ DEPRECATED - use SharedMarketDataService
from .price_fetching_utils import *
from .price_service import *
from .price_utils import *
from .strategy_market_data_service import StrategyMarketDataService
from .streaming_service import StreamingService

# Import shared service for easier access
from the_alchemiser.shared.services import SharedMarketDataService

__all__ = [
    "MarketDataClient",  # Deprecated
    "SharedMarketDataService",  # Recommended
    "StrategyMarketDataService",
    "StreamingService",
]
