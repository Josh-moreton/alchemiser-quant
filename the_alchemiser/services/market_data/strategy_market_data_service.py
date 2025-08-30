"""Business Unit: strategy & signal generation; Status: current.

Strategy Market Data Service - Canonical MarketDataPort implementation.

This service implements the canonical MarketDataPort protocol using typed domain
models while providing backward-compatible DataFrame adapters for strategies.
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from the_alchemiser.anti_corruption.market_data.market_data_mapping import (
    bars_to_dataframe,
    quote_to_current_price,
    quote_to_tuple,
    symbol_str_to_symbol,
)
from the_alchemiser.domain.market_data.models.bar import BarModel
from the_alchemiser.domain.market_data.models.quote import QuoteModel
from the_alchemiser.services.market_data.market_data_client import MarketDataClient
from the_alchemiser.infrastructure.market_data.market_data_service import MarketDataService
from the_alchemiser.shared_kernel.value_objects.symbol import Symbol

logger = logging.getLogger(__name__)


class StrategyMarketDataService:
    """Implementation of canonical MarketDataPort for strategy layer.

    This service implements the canonical domain MarketDataPort protocol using
    typed domain models (Symbol, BarModel, QuoteModel) while providing
    backward-compatible adapters for strategies that need DataFrame formats.
    """

    def __init__(self, api_key: str, secret_key: str) -> None:
        """Initialize the strategy market data service.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key

        """
        self._client = MarketDataClient(api_key, secret_key)

        # TODO: Initialize MarketDataService when AlpacaManager integration is available
        # For now, use MarketDataClient directly
        self._service: MarketDataService | None = None

    # --- Canonical MarketDataPort Interface ---

    def get_bars(self, symbol: Symbol, period: str, timeframe: str) -> list[BarModel]:
        """Historical bars for a symbol.

        Args:
            symbol: Symbol value object
            period: Historical period (e.g., "1y", "6m", "1m")
            timeframe: Data timeframe (e.g., "1day", "1hour", "1min")

        Returns:
            List of BarModel domain objects

        """
        if self._service:
            return self._service.get_bars(symbol, period, timeframe)

        # Fallback to direct client usage with conversion
        try:
            interval = self._map_timeframe_to_interval(timeframe)
            df = self._client.get_historical_bars(
                symbol=symbol.as_str(), period=period, interval=interval
            )

            # Convert DataFrame to BarModel list
            from the_alchemiser.anti_corruption.market_data.market_data_mapping import (
                dataframe_to_bars,
            )

            return dataframe_to_bars(df, symbol)

        except Exception as e:
            logger.error(f"Failed to get bars for {symbol}: {e}")
            return []

    def get_latest_quote(self, symbol: Symbol) -> QuoteModel | None:
        """Get latest quote as QuoteModel.

        Args:
            symbol: Symbol value object

        Returns:
            QuoteModel domain object or None if unavailable

        """
        if self._service:
            return self._service.get_latest_quote(symbol)

        # Fallback to direct client usage with conversion
        try:
            bid, ask = self._client.get_latest_quote(symbol.as_str())

            from decimal import Decimal

            return QuoteModel(
                ts=None,  # MarketDataClient doesn't provide timestamp
                bid=Decimal(str(bid)),
                ask=Decimal(str(ask)),
            )

        except Exception as e:
            logger.error(f"Failed to get latest quote for {symbol}: {e}")
            return None

    def get_mid_price(self, symbol: Symbol) -> float | None:
        """Get mid-price from latest quote.

        Args:
            symbol: Symbol value object

        Returns:
            Mid-price as float, or None if unavailable

        """
        quote = self.get_latest_quote(symbol)
        return quote_to_current_price(quote)

    # --- Legacy Adapter Methods (for backward compatibility) ---

    def get_data(
        self,
        symbol: str,
        timeframe: str = "1day",
        period: str = "1y",
        **kwargs: Any,
    ) -> pd.DataFrame:
        """Retrieve historical market data as DataFrame (adapter method).

        Args:
            symbol: The ticker symbol to fetch data for
            timeframe: The data timeframe (e.g., "1day", "1hour", "1min")
            period: The historical period to fetch (e.g., "1y", "6m", "1m")
            **kwargs: Additional parameters for data fetching

        Returns:
            DataFrame with OHLCV data indexed by timestamp

        """
        try:
            symbol_obj = symbol_str_to_symbol(symbol)
            bars = self.get_bars(symbol_obj, period, timeframe)
            return bars_to_dataframe(bars)
        except Exception as e:
            logger.error(f"Failed to get data for {symbol}: {e}")
            return pd.DataFrame()

    def get_current_price(self, symbol: str, **kwargs: Any) -> float | None:
        """Get current price from quote (adapter method).

        Args:
            symbol: The ticker symbol to get price for
            **kwargs: Additional parameters

        Returns:
            Current price as float, or None if unavailable

        """
        try:
            symbol_obj = symbol_str_to_symbol(symbol)
            return self.get_mid_price(symbol_obj)
        except Exception as e:
            logger.error(f"Failed to get current price for {symbol}: {e}")
            return None

    def get_latest_quote_tuple(
        self, symbol: str, **kwargs: Any
    ) -> tuple[float | None, float | None]:
        """Get latest quote as tuple (adapter method).

        Args:
            symbol: The ticker symbol to get quote for
            **kwargs: Additional parameters

        Returns:
            Tuple of (bid_price, ask_price), either can be None if unavailable

        """
        try:
            symbol_obj = symbol_str_to_symbol(symbol)
            quote = self.get_latest_quote(symbol_obj)
            return quote_to_tuple(quote)
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
        if timeframe_lower in {"1hour", "1h", "hour", "hourly"}:
            return "1h"
        if timeframe_lower in {"1min", "1m", "minute", "min"}:
            return "1m"
        # Default to daily if unknown timeframe
        logger.warning(f"Unknown timeframe '{timeframe}', defaulting to '1d'")
        return "1d"
