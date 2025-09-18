"""Business Unit: shared | Status: current.

Alpaca market data management.

Handles market data retrieval including quotes, historical bars, and current prices.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

from .exceptions import AlpacaDataError, normalize_alpaca_error
from .models import BarModel, QuoteModel

if TYPE_CHECKING:
    from .client import AlpacaClient

logger = logging.getLogger(__name__)


class MarketDataManager:
    """Manages market data retrieval and operations."""

    def __init__(self, client: AlpacaClient) -> None:
        """Initialize with Alpaca client.
        
        Args:
            client: AlpacaClient instance
        """
        self._client = client

    def get_current_price(self, symbol: str) -> float | None:
        """Get current price for a symbol.

        Returns the mid price between bid and ask, or None if not available.
        Uses centralized price discovery utility for consistent calculation.

        TODO: Consider migrating callers to use structured pricing types:
        - RealTimePricingService.get_quote_data() for bid/ask spreads with market depth
        - RealTimePricingService.get_price_data() for volume and enhanced trade data
        - Enhanced price discovery with QuoteModel and PriceDataModel
        
        Args:
            symbol: Symbol to get price for
            
        Returns:
            Current price as float, None if unavailable
            
        Raises:
            AlpacaDataError: If operation fails
        """
        try:
            # Import here to avoid circular dependency
            from the_alchemiser.shared.utils.price_discovery_utils import (
                get_current_price_from_quote,
            )
            
            # Use price discovery utility with self as the manager
            return get_current_price_from_quote(self._get_manager_for_price_discovery(), symbol)
        except Exception as e:
            logger.error(f"Failed to get current price for {symbol}: {e}")
            raise normalize_alpaca_error(e, f"Get current price for {symbol}") from e

    def get_current_prices(self, symbols: list[str]) -> dict[str, float]:
        """Get current prices for multiple symbols.

        Args:
            symbols: List of stock symbols

        Returns:
            Dictionary mapping symbols to their current prices
            
        Raises:
            AlpacaDataError: If operation fails
        """
        try:
            prices = {}
            for symbol in symbols:
                price = self.get_current_price(symbol)
                if price is not None:
                    prices[symbol] = price
                else:
                    logger.warning(f"Could not get price for {symbol}")
            return prices
        except Exception as e:
            logger.error(f"Failed to get current prices for {symbols}: {e}")
            raise normalize_alpaca_error(e, f"Get current prices for {symbols}") from e

    def get_latest_quote(self, symbol: str) -> tuple[float, float] | None:
        """Get latest bid/ask quote for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Tuple of (bid, ask) prices, or None if not available.
        """
        try:
            request = StockLatestQuoteRequest(symbol_or_symbols=[symbol])
            quotes = self._client.data_client.get_stock_latest_quote(request)
            quote = quotes.get(symbol)

            if quote:
                bid = float(getattr(quote, "bid_price", 0))
                ask = float(getattr(quote, "ask_price", 0))

                # Allow quotes where we have at least a valid bid or ask
                # This handles cases like LEU where bid exists but ask is 0
                if bid > 0 or ask > 0:
                    # If only one side is available, use it for both bid and ask
                    # This allows trading while acknowledging the spread uncertainty
                    if bid > 0 and ask <= 0:
                        logger.info(
                            f"Using bid price for both bid/ask for {symbol} (ask unavailable)"
                        )
                        return (bid, bid)
                    if ask > 0 and bid <= 0:
                        logger.info(
                            f"Using ask price for both bid/ask for {symbol} (bid unavailable)"
                        )
                        return (ask, ask)
                    # Both bid and ask are available and positive
                    return (bid, ask)

            logger.warning(f"No valid quote data available for {symbol}")
            return None
        except Exception as e:
            logger.error(f"Failed to get latest quote for {symbol}: {e}")
            return None

    def get_quote(self, symbol: str) -> dict[str, Any] | None:
        """Get quote information for a symbol (MarketDataRepository interface).

        Args:
            symbol: Symbol to get quote for

        Returns:
            Dictionary with quote information or None if failed
        """
        try:
            request = StockLatestQuoteRequest(symbol_or_symbols=[symbol])
            quotes = self._client.data_client.get_stock_latest_quote(request)
            quote = quotes.get(symbol)

            if quote:
                # Use Pydantic model_dump() for consistent field names
                quote_dict = quote.model_dump()
                # Ensure we have symbol in the output
                quote_dict["symbol"] = symbol
                return quote_dict
            return None
        except Exception as e:
            logger.error(f"Failed to get quote for {symbol}: {e}")
            return None

    def get_quote_model(self, symbol: str) -> QuoteModel | None:
        """Get quote information as typed model.
        
        Args:
            symbol: Symbol to get quote for
            
        Returns:
            QuoteModel instance, None if unavailable
        """
        quote_data = self.get_latest_quote(symbol)
        if not quote_data:
            return None
        
        try:
            bid, ask = quote_data
            return QuoteModel(
                symbol=symbol,
                bid=self._safe_decimal(bid),
                ask=self._safe_decimal(ask),
                timestamp=datetime.now(),
            )
        except Exception as e:
            logger.error(f"Failed to create quote model for {symbol}: {e}")
            return None

    def get_historical_bars(
        self, symbol: str, start_date: str, end_date: str, timeframe: str = "1Day"
    ) -> list[dict[str, Any]]:
        """Get historical bar data for a symbol.

        Args:
            symbol: Stock symbol
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)
            timeframe: Timeframe (1Min, 5Min, 15Min, 1Hour, 1Day)

        Returns:
            List of dictionaries with bar data using Pydantic model field names
            
        Raises:
            AlpacaDataError: If operation fails
        """
        try:
            # Map timeframe strings to Alpaca TimeFrame objects (case-insensitive)
            timeframe_map = {
                "1min": TimeFrame(1, TimeFrameUnit.Minute),
                "5min": TimeFrame(5, TimeFrameUnit.Minute),
                "15min": TimeFrame(15, TimeFrameUnit.Minute),
                "1hour": TimeFrame(1, TimeFrameUnit.Hour),
                "1day": TimeFrame(1, TimeFrameUnit.Day),
            }

            timeframe_lower = timeframe.lower()
            if timeframe_lower not in timeframe_map:
                raise ValueError(f"Unsupported timeframe: {timeframe}")

            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)

            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=timeframe_map[timeframe_lower],
                start=start_dt,
                end=end_dt,
            )

            response = self._client.data_client.get_stock_bars(request)

            # Extract bars for symbol from various possible response shapes
            bars_obj: Any | None = None
            try:
                # Preferred: BarsBySymbol has a `.data` dict
                data_attr = getattr(response, "data", None)
                if isinstance(data_attr, dict) and symbol in data_attr:
                    bars_obj = data_attr[symbol]
                # Some SDKs expose attributes per symbol
                elif hasattr(response, symbol):
                    bars_obj = getattr(response, symbol)
                # Fallback: mapping-like access
                elif isinstance(response, dict) and symbol in response:
                    bars_obj = response[symbol]
            except Exception:
                bars_obj = None

            if not bars_obj:
                logger.warning(f"No historical data found for {symbol}")
                return []

            bars = list(bars_obj)
            logger.debug(f"Successfully retrieved {len(bars)} bars for {symbol}")

            # Use Pydantic model_dump() to get proper dictionaries with full field names
            result: list[dict[str, Any]] = []
            for bar in bars:
                try:
                    # Alpaca SDK uses Pydantic models, use model_dump()
                    bar_dict = bar.model_dump()
                    result.append(bar_dict)
                except Exception as e:
                    logger.warning(f"Failed to convert bar for {symbol}: {e}")
                    continue
            return result

        except Exception as e:
            logger.error(f"Failed to get historical data for {symbol}: {e}")
            raise normalize_alpaca_error(e, f"Get historical bars for {symbol}") from e

    def get_historical_bars_models(
        self, symbol: str, start_date: str, end_date: str, timeframe: str = "1Day"
    ) -> list[BarModel]:
        """Get historical bar data as typed models.
        
        Args:
            symbol: Stock symbol
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)
            timeframe: Timeframe (1Min, 5Min, 15Min, 1Hour, 1Day)
            
        Returns:
            List of BarModel instances
        """
        bars_data = self.get_historical_bars(symbol, start_date, end_date, timeframe)
        result = []
        
        for bar_dict in bars_data:
            try:
                result.append(BarModel(
                    symbol=symbol,
                    timestamp=bar_dict.get("timestamp", datetime.now()),
                    open=self._safe_decimal(bar_dict.get("open", 0)),
                    high=self._safe_decimal(bar_dict.get("high", 0)),
                    low=self._safe_decimal(bar_dict.get("low", 0)),
                    close=self._safe_decimal(bar_dict.get("close", 0)),
                    volume=int(bar_dict.get("volume", 0)),
                    vwap=self._safe_decimal(bar_dict.get("vwap")),
                ))
            except Exception as e:
                logger.warning(f"Failed to create bar model for {symbol}: {e}")
                continue
        
        return result

    def _get_manager_for_price_discovery(self) -> Any:
        """Get a manager object compatible with price discovery utils.
        
        This creates a wrapper that provides the expected interface for
        the price discovery utility functions.
        """
        # Create a simple wrapper that provides the get_latest_quote method
        class ManagerWrapper:
            def __init__(self, market_data_manager: MarketDataManager) -> None:
                self._manager = market_data_manager
            
            def get_latest_quote(self, symbol: str) -> tuple[float, float] | None:
                return self._manager.get_latest_quote(symbol)
        
        return ManagerWrapper(self)

    def _safe_decimal(self, value: Any) -> Any:
        """Safely convert value to Decimal.
        
        Args:
            value: Value to convert
            
        Returns:
            Decimal value or original value if conversion fails
        """
        if value is None:
            return None
        try:
            from decimal import Decimal
            return Decimal(str(value))
        except (ValueError, TypeError):
            return value