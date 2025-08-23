"""Market Data Port Protocol for Strategy Layer.

DEPRECATED: This protocol is deprecated in favor of the canonical MarketDataPort
from the_alchemiser.domain.market_data.protocols.market_data_port.

The canonical version uses Symbol value objects and domain models (BarModel, QuoteModel)
rather than raw strings and pandas DataFrames.

For backward compatibility, use StrategyMarketDataAdapter from 
the_alchemiser.application.mapping.strategy_market_data_adapter to bridge
DataFrame-expecting strategies to the canonical port.

This protocol defines the minimal contract that strategies need for market data access.
It provides a clean abstraction that strategies can depend on without coupling to
specific infrastructure implementations.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

import pandas as pd


@runtime_checkable
class MarketDataPort(Protocol):
    """Protocol for market data access in strategy implementations.

    This port provides the essential market data operations that trading strategies
    need, with a focus on simplicity and decoupling from infrastructure concerns.
    """

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
        ...

    def get_current_price(self, symbol: str, **kwargs: Any) -> float | None:
        """Get the current/latest price for a symbol.

        Args:
            symbol: The ticker symbol to get price for
            **kwargs: Additional parameters

        Returns:
            Current price as float, or None if unavailable
        """
        ...

    def get_latest_quote(self, symbol: str, **kwargs: Any) -> tuple[float | None, float | None]:
        """Get the latest bid/ask quote for a symbol.

        Args:
            symbol: The ticker symbol to get quote for
            **kwargs: Additional parameters

        Returns:
            Tuple of (bid_price, ask_price), either can be None if unavailable
        """
        ...
