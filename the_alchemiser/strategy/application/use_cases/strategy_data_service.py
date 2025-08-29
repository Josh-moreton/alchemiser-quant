"""Business Unit: strategy & signal generation | Status: current.

Strategy data service use case for strategy context.

Canonical MarketDataPort implementation providing typed domain models
while maintaining backward-compatible DataFrame adapters for strategies.
"""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from the_alchemiser.application.mapping.market_data_mapping import (
    bars_to_dataframe,
    quote_to_current_price,
    quote_to_tuple,
    symbol_str_to_symbol,
)
from the_alchemiser.domain.market_data.models.bar import BarModel
from the_alchemiser.domain.market_data.models.quote import QuoteModel
from the_alchemiser.shared_kernel.value_objects.symbol import Symbol
from the_alchemiser.strategy.infrastructure.adapters.market_data_client import MarketDataClient
from the_alchemiser.strategy.application.use_cases.market_data_operations import (
    MarketDataOperations,
)

logger = logging.getLogger(__name__)


class StrategyDataService:
    """Strategy data service implementing canonical MarketDataPort for strategy layer.

    This service implements the canonical domain MarketDataPort protocol using
    typed domain models (Symbol, BarModel, QuoteModel) while providing
    backward-compatible adapters for strategies that need DataFrame formats.
    """

    def __init__(self, api_key: str, secret_key: str) -> None:
        """Initialize the strategy data service.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key

        """
        self._client = MarketDataClient(api_key, secret_key)

        # TODO: Initialize MarketDataOperations when AlpacaManager integration is available
        # For now, use MarketDataClient directly
        self._operations: MarketDataOperations | None = None

    def get_bars(
        self,
        symbol: Symbol,
        start: Any,
        end: Any,
        timeframe: str = "1Day",
    ) -> list[BarModel]:
        """Get market bars using typed domain objects.

        Args:
            symbol: Symbol domain object
            start: Start datetime
            end: End datetime
            timeframe: Timeframe string

        Returns:
            List of BarModel domain objects

        """
        if self._operations:
            return self._operations.get_bars(symbol, start, end, timeframe)

        # Fallback to client
        try:
            df = self._client.get_historical_data_for_date_range(
                symbol.value, start, end, timeframe
            )

            # Convert DataFrame to BarModel list
            bars = []
            for timestamp, row in df.iterrows():
                bars.append(
                    BarModel(
                        symbol=symbol,
                        timestamp=timestamp,
                        open_price=row["open"],
                        high_price=row["high"],
                        low_price=row["low"],
                        close_price=row["close"],
                        volume=row["volume"],
                    )
                )

            return bars
        except Exception as e:
            logger.error(f"Failed to get bars for {symbol.value}: {e}")
            return []

    def get_latest_quote(self, symbol: Symbol) -> QuoteModel:
        """Get latest quote using typed domain objects.

        Args:
            symbol: Symbol domain object

        Returns:
            QuoteModel domain object

        """
        if self._operations:
            return self._operations.get_latest_quote(symbol)

        # Fallback to client
        try:
            quote_data = self._client.get_latest_quote(symbol.value)

            return QuoteModel(
                symbol=symbol,
                bid_price=quote_data["bid_price"],
                ask_price=quote_data["ask_price"],
                bid_size=quote_data["bid_size"],
                ask_size=quote_data["ask_size"],
                timestamp=quote_data["timestamp"],
            )
        except Exception as e:
            logger.error(f"Failed to get quote for {symbol.value}: {e}")
            # Return default quote
            from datetime import datetime, UTC
            from decimal import Decimal

            return QuoteModel(
                symbol=symbol,
                bid_price=Decimal("0"),
                ask_price=Decimal("0"),
                bid_size=0,
                ask_size=0,
                timestamp=datetime.now(UTC),
            )

    def get_mid_price(self, symbol: Symbol) -> float:
        """Get mid price using typed domain objects.

        Args:
            symbol: Symbol domain object

        Returns:
            Mid price as float

        """
        if self._operations:
            return float(self._operations.get_mid_price(symbol))

        # Fallback to client
        try:
            quote = self.get_latest_quote(symbol)
            return float((quote.bid_price + quote.ask_price) / 2)
        except Exception as e:
            logger.error(f"Failed to get mid price for {symbol.value}: {e}")
            return 0.0

    # Backward-compatible DataFrame methods for existing strategies
    def get_historical_data(
        self,
        symbol: str,
        period: str = "1y",
        interval: str = "1d",
    ) -> pd.DataFrame:
        """Get historical data as DataFrame for backward compatibility.

        Args:
            symbol: Symbol string
            period: Time period
            interval: Data interval

        Returns:
            DataFrame with historical data

        """
        try:
            if self._operations:
                return self._operations.get_historical_data_dataframe(symbol, period, interval)

            # Fallback to client
            return self._client.get_historical_bars(symbol, period, interval)
        except Exception as e:
            logger.error(f"Failed to get historical data for {symbol}: {e}")
            return pd.DataFrame()

    def get_current_price(self, symbol: str) -> float:
        """Get current price for backward compatibility.

        Args:
            symbol: Symbol string

        Returns:
            Current price as float

        """
        try:
            return self._client.get_current_price(symbol)
        except Exception as e:
            logger.error(f"Failed to get current price for {symbol}: {e}")
            return 0.0

    def get_current_prices(self, symbols: list[str]) -> dict[str, float]:
        """Get current prices for multiple symbols.

        Args:
            symbols: List of symbol strings

        Returns:
            Dictionary mapping symbols to prices

        """
        if self._operations:
            return self._operations.get_current_prices(symbols)

        return self._client.get_current_prices(symbols)

    def get_market_status(self) -> dict[str, Any]:
        """Get market status information.

        Returns:
            Dictionary with market status

        """
        return self._client.get_market_status()

    def validate_symbol(self, symbol: str) -> bool:
        """Validate if symbol is tradeable.

        Args:
            symbol: Symbol string

        Returns:
            True if symbol is valid

        """
        return self._client.validate_symbol(symbol)

    # Domain mapping utilities for advanced use cases
    def symbol_str_to_domain(self, symbol_str: str) -> Symbol:
        """Convert symbol string to domain Symbol object.

        Args:
            symbol_str: Symbol string

        Returns:
            Symbol domain object

        """
        return symbol_str_to_symbol(symbol_str)

    def quote_to_price_tuple(self, quote: QuoteModel) -> tuple[float, float]:
        """Convert quote to (bid, ask) tuple.

        Args:
            quote: QuoteModel object

        Returns:
            Tuple of (bid_price, ask_price)

        """
        return quote_to_tuple(quote)

    def bars_to_dataframe_mapped(self, bars: list[BarModel]) -> pd.DataFrame:
        """Convert domain BarModel list to DataFrame.

        Args:
            bars: List of BarModel objects

        Returns:
            DataFrame with bar data

        """
        return bars_to_dataframe(bars)

    def quote_to_current_price_mapped(self, quote: QuoteModel) -> float:
        """Convert quote to current price (mid price).

        Args:
            quote: QuoteModel object

        Returns:
            Mid price as float

        """
        return quote_to_current_price(quote)
