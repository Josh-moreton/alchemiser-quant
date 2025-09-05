"""Business Unit: shared | Status: current.

Shared services module - Common services used across modules.

This module provides canonical implementations of shared services that can be
used by strategy, portfolio, and execution modules following the modular
architecture guidelines.
"""

# Import only the new market data service to avoid dependency issues
from .market_data_service import SharedMarketDataService, create_shared_market_data_service

__all__ = ["SharedMarketDataService", "create_shared_market_data_service"]
