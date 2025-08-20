"""Strategy Market Data Service - Typed implementation of MarketDataPort for strategies.

This service provides the typed implementation of the MarketDataPort protocol,
serving as the bridge between strategy requirements and the underlying market data
infrastructure (MarketDataService and AlpacaManager).
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from the_alchemiser.domain.strategies.protocols.market_data_port import MarketDataPort
from the_alchemiser.services.market_data.market_data_client import MarketDataClient

logger = logging.getLogger(__name__)


class StrategyMarketDataService:
    """Typed implementation of MarketDataPort for strategy layer.
    
    This service implements the MarketDataPort protocol using the existing
    MarketDataClient infrastructure, providing strategies with a clean,
    typed interface without exposing infrastructure details.
    """

    def __init__(self, api_key: str, secret_key: str) -> None:
        """Initialize the strategy market data service.
        
        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
        """
        self._client = MarketDataClient(api_key, secret_key)

    def get_data(
        self,
        symbol: str,
        timeframe: str = "1day",
        period: str = "1y",
        **kwargs: Any,
    ) -> pd.DataFrame:
        """Retrieve historical market data for a symbol.
        
        Args:
            symbol: The ticker symbol to fetch data for
            timeframe: The data timeframe (e.g., "1day", "1hour", "1min")
            period: The historical period to fetch (e.g., "1y", "6m", "1m")
            **kwargs: Additional parameters for data fetching
            
        Returns:
            DataFrame with OHLCV data indexed by timestamp
        """
        try:
            # Map timeframe to interval format expected by MarketDataClient
            interval = self._map_timeframe_to_interval(timeframe)
            
            # Use MarketDataClient to fetch historical bars
            return self._client.get_historical_bars(
                symbol=symbol,
                period=period,
                interval=interval
            )
            
        except Exception as e:
            logger.error(f"Failed to get data for {symbol}: {e}")
            # Return empty DataFrame on error to maintain compatibility
            return pd.DataFrame()

    def get_current_price(self, symbol: str, **kwargs: Any) -> float | None:
        """Get the current/latest price for a symbol.
        
        Args:
            symbol: The ticker symbol to get price for
            **kwargs: Additional parameters
            
        Returns:
            Current price as float, or None if unavailable
        """
        try:
            return self._client.get_current_price_from_quote(symbol)
        except Exception as e:
            logger.error(f"Failed to get current price for {symbol}: {e}")
            return None

    def get_latest_quote(self, symbol: str, **kwargs: Any) -> tuple[float | None, float | None]:
        """Get the latest bid/ask quote for a symbol.
        
        Args:
            symbol: The ticker symbol to get quote for
            **kwargs: Additional parameters
            
        Returns:
            Tuple of (bid_price, ask_price), either can be None if unavailable
        """
        try:
            return self._client.get_latest_quote(symbol)
        except Exception as e:
            logger.error(f"Failed to get latest quote for {symbol}: {e}")
            return (None, None)

    def _map_timeframe_to_interval(self, timeframe: str) -> str:
        """Map strategy timeframe to MarketDataClient interval format.
        
        Args:
            timeframe: Strategy timeframe (e.g., "1day", "1hour", "1min")
            
        Returns:
            Interval format expected by MarketDataClient
        """
        # Normalize timeframe to lowercase for comparison
        timeframe_lower = timeframe.lower()
        
        # Map common timeframe variations to standard intervals
        if timeframe_lower in {"1day", "1d", "day", "daily"}:
            return "1d"
        elif timeframe_lower in {"1hour", "1h", "hour", "hourly"}:
            return "1h"
        elif timeframe_lower in {"1min", "1m", "minute", "min"}:
            return "1m"
        else:
            # Default to daily if unknown timeframe
            logger.warning(f"Unknown timeframe '{timeframe}', defaulting to '1d'")
            return "1d"