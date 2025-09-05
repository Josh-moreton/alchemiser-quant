#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Market Data Service Adapter for backward compatibility.

This adapter provides a compatibility layer for existing code that uses
MarketDataClient from the strategy module, allowing gradual migration to
the shared service without breaking existing functionality.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import pandas as pd
from alpaca.data.timeframe import TimeFrame

from the_alchemiser.shared.services.market_data_service import SharedMarketDataService

logger = logging.getLogger(__name__)


class MarketDataServiceAdapter:
    """Adapter to provide MarketDataClient-compatible interface using SharedMarketDataService.
    
    This adapter allows existing code to continue working while gradually migrating
    to the shared service. It provides the same method signatures as the original
    MarketDataClient but uses the shared service under the hood.
    """

    def __init__(self, api_key: str, secret_key: str) -> None:
        """Initialize the adapter with a shared market data service.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key

        """
        self.api_key = api_key
        self.secret_key = secret_key
        self._shared_service = SharedMarketDataService(
            api_key=api_key,
            secret_key=secret_key,
        )

    def get_historical_bars(
        self, symbol: str, period: str = "1y", interval: str = "1d"
    ) -> pd.DataFrame:
        """Get historical bar data - compatible with MarketDataClient interface."""
        return self._shared_service.get_historical_bars(symbol, period, interval)

    def get_historical_bars_date_range(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        timeframe: TimeFrame | str | None = None,
    ) -> list[Any]:
        """Get historical data for date range - compatible with MarketDataClient interface."""
        return self._shared_service.get_historical_bars_date_range(symbol, start, end, timeframe)

    def get_latest_quote(self, symbol: str) -> tuple[float, float]:
        """Get latest quote - compatible with MarketDataClient interface."""
        return self._shared_service.get_latest_quote(symbol)

    def get_current_price_from_quote(self, symbol: str) -> float | None:
        """Get current price from quote - compatible with MarketDataClient interface."""
        return self._shared_service.get_current_price(symbol)

    @property
    def _alpaca_manager(self) -> Any:  # noqa: ANN401
        """Backward compatibility property."""
        return self._shared_service._alpaca_manager


def create_market_data_adapter(api_key: str, secret_key: str) -> MarketDataServiceAdapter:
    """Create a market data adapter for backward compatibility.

    Args:
        api_key: Alpaca API key
        secret_key: Alpaca secret key

    Returns:
        MarketDataServiceAdapter instance

    """
    return MarketDataServiceAdapter(api_key, secret_key)