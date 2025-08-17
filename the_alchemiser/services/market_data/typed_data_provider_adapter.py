"""
Typed data provider adapter for pandas-based strategy operations.

This adapter provides a strongly typed interface over the UnifiedDataProviderFacade
for strategies that expect typed pandas DataFrame operations. It maintains backward
compatibility while enabling the migration to typed services.
"""

import logging
from typing import Any, Protocol

import pandas as pd

from the_alchemiser.infrastructure.data_providers.unified_data_provider_facade import (
    UnifiedDataProviderFacade,
)

logger = logging.getLogger(__name__)


class DataProviderProtocol(Protocol):
    """Protocol defining the interface that strategies expect from data providers."""

    def get_data(
        self,
        symbol: str,
        timeframe: str = "1day",
        period: str = "1y",
        start_date: str | None = None,
        end_date: str | None = None,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """Get historical market data as a pandas DataFrame."""
        ...

    def get_current_price(self, symbol: str, **kwargs: Any) -> float | None:
        """Get current price for a symbol."""
        ...


class TypedDataProviderAdapter:
    """
    Typed adapter for data provider operations in strategies.
    
    This adapter wraps the UnifiedDataProviderFacade to provide strongly typed
    pandas DataFrame operations for strategy engines while maintaining the
    exact same interface and behavior.
    """

    def __init__(self, underlying_provider: UnifiedDataProviderFacade) -> None:
        """
        Initialize the typed adapter.
        
        Args:
            underlying_provider: The UnifiedDataProviderFacade to wrap
        """
        self._provider = underlying_provider
        self.logger = logger

    def get_data(
        self,
        symbol: str,
        timeframe: str = "1day",
        period: str = "1y",
        start_date: str | None = None,
        end_date: str | None = None,
        **kwargs: Any,
    ) -> pd.DataFrame:
        """
        Get historical market data as a typed pandas DataFrame.
        
        Args:
            symbol: Stock symbol (e.g. 'AAPL', 'TSLA')
            timeframe: Time frame for data ('1day', '1hour', '1minute')
            period: Time period ('1y', '6m', '3m', '1m')
            start_date: Optional start date string
            end_date: Optional end date string
            **kwargs: Additional arguments for backward compatibility
            
        Returns:
            pandas DataFrame with historical market data
            
        Raises:
            ValueError: If symbol is invalid or data cannot be retrieved
        """
        if not symbol or not isinstance(symbol, str):
            raise ValueError(f"Invalid symbol: {symbol}")
            
        self.logger.debug(f"Fetching data for {symbol} with timeframe={timeframe}, period={period}")
        
        # Delegate to underlying provider
        result = self._provider.get_data(
            symbol=symbol,
            timeframe=timeframe,
            period=period,
            start_date=start_date,
            end_date=end_date,
            **kwargs
        )
        
        if not isinstance(result, pd.DataFrame):
            raise ValueError(f"Expected pandas DataFrame, got {type(result)}")
            
        self.logger.debug(f"Retrieved {len(result)} rows for {symbol}")
        return result

    def get_current_price(self, symbol: str, **kwargs: Any) -> float | None:
        """
        Get current price for a symbol.
        
        Args:
            symbol: Stock symbol (e.g. 'AAPL', 'TSLA')
            **kwargs: Additional arguments for backward compatibility
            
        Returns:
            Current price as float or None if unavailable
        """
        if not symbol or not isinstance(symbol, str):
            raise ValueError(f"Invalid symbol: {symbol}")
            
        self.logger.debug(f"Fetching current price for {symbol}")
        return self._provider.get_current_price(symbol, **kwargs)

    @property
    def trading_client(self) -> Any:
        """
        Provide access to trading client for backward compatibility.
        
        Returns:
            The underlying trading client instance
        """
        return self._provider.trading_client

    # Forward other methods for compatibility
    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics from underlying provider."""
        return self._provider.get_cache_stats()

    def clear_cache(self, pattern: str | None = None) -> None:
        """Clear cache in underlying provider."""
        return self._provider.clear_cache(pattern)
