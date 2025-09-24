"""Business Unit: shared | Status: current.

Alpaca market data operations adapter implementing MarketDataRepository protocol.

This adapter focuses specifically on market data operations including price retrieval,
quotes, and historical data. It delegates to the Alpaca StockHistoricalDataClient
for all market data operations.
"""

from __future__ import annotations

import logging
from typing import Any

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockLatestQuoteRequest

from the_alchemiser.shared.brokers.alpaca_utils import (
    create_data_client,
    get_alpaca_quote_type,
)
from the_alchemiser.shared.protocols.repository import MarketDataRepository

logger = logging.getLogger(__name__)


class AlpacaMarketDataAdapter(MarketDataRepository):
    """Alpaca market data operations adapter.
    
    Implements the MarketDataRepository protocol for all market data operations
    including current prices, quotes, and historical data retrieval.
    """

    def __init__(
        self,
        api_key: str,
        secret_key: str,
    ) -> None:
        """Initialize the market data adapter.
        
        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
        """
        self._api_key = api_key
        self._secret_key = secret_key
        
        # Initialize data client
        self._data_client = create_data_client(
            api_key=api_key, secret_key=secret_key
        )
        
        logger.info("AlpacaMarketDataAdapter initialized")

    def get_current_price(self, symbol: str) -> float | None:
        """Get current price for a symbol.
        
        Returns the mid price between bid and ask, or None if not available.
        Uses centralized price discovery utility for consistent calculation.
        """
        from the_alchemiser.shared.utils.price_discovery_utils import (
            get_current_price_from_quote,
        )

        try:
            return get_current_price_from_quote(self, symbol)
        except Exception as e:
            logger.error(f"Failed to get current price for {symbol}: {e}")
            raise

    def get_quote(self, symbol: str) -> dict[str, Any] | None:
        """Get quote information for a symbol.
        
        Returns:
            Dictionary with quote data including bid, ask, timestamp, etc.
            Returns None if quote is not available.
        """
        try:
            request = StockLatestQuoteRequest(symbol_or_symbols=[symbol])
            response = self._data_client.get_stock_latest_quote(request)
            
            if not response or symbol not in response:
                logger.warning(f"No quote data returned for {symbol}")
                return None
                
            quote = response[symbol]
            if quote is None:
                logger.warning(f"Quote for {symbol} is None")
                return None
                
            # Convert quote object to dictionary
            quote_dict = self._convert_quote_to_dict(quote)
            logger.debug(f"Retrieved quote for {symbol}: bid={quote_dict.get('bid_price')}, "
                        f"ask={quote_dict.get('ask_price')}")
            return quote_dict
            
        except Exception as e:
            logger.error(f"Failed to get quote for {symbol}: {e}")
            return None

    def _convert_quote_to_dict(self, quote: Any) -> dict[str, Any]:
        """Convert Alpaca quote object to dictionary.
        
        Args:
            quote: Alpaca quote object
            
        Returns:
            Dictionary representation of the quote
        """
        Quote = get_alpaca_quote_type()
        
        if isinstance(quote, Quote):
            # Handle SDK quote object
            return {
                "symbol": getattr(quote, "symbol", None),
                "ask_price": float(getattr(quote, "ask_price", 0)),
                "ask_size": int(getattr(quote, "ask_size", 0)),
                "bid_price": float(getattr(quote, "bid_price", 0)),
                "bid_size": int(getattr(quote, "bid_size", 0)),
                "timestamp": getattr(quote, "timestamp", None),
            }
        elif isinstance(quote, dict):
            # Handle dictionary quote
            return {
                "symbol": quote.get("symbol"),
                "ask_price": float(quote.get("ask_price", 0)),
                "ask_size": int(quote.get("ask_size", 0)),
                "bid_price": float(quote.get("bid_price", 0)),
                "bid_size": int(quote.get("bid_size", 0)),
                "timestamp": quote.get("timestamp"),
            }
        else:
            # Fallback: try to extract attributes dynamically
            try:
                return {
                    "symbol": getattr(quote, "symbol", None),
                    "ask_price": float(getattr(quote, "ask_price", 0)),
                    "ask_size": int(getattr(quote, "ask_size", 0)),
                    "bid_price": float(getattr(quote, "bid_price", 0)),
                    "bid_size": int(getattr(quote, "bid_size", 0)),
                    "timestamp": getattr(quote, "timestamp", None),
                }
            except Exception as e:
                logger.warning(f"Failed to convert quote to dict: {e}")
                return {
                    "symbol": None,
                    "ask_price": 0.0,
                    "ask_size": 0,
                    "bid_price": 0.0,
                    "bid_size": 0,
                    "timestamp": None,
                }

    def get_latest_quote(self, symbol: str) -> tuple[float, float] | None:
        """Get latest bid/ask quote for a symbol.
        
        Returns:
            Tuple of (bid_price, ask_price) or None if not available
        """
        try:
            quote_dict = self.get_quote(symbol)
            if not quote_dict:
                return None
                
            bid_price = quote_dict.get("bid_price", 0.0)
            ask_price = quote_dict.get("ask_price", 0.0)
            
            if bid_price > 0 and ask_price > 0:
                return (bid_price, ask_price)
            else:
                logger.warning(f"Invalid bid/ask prices for {symbol}: "
                              f"bid={bid_price}, ask={ask_price}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get latest quote for {symbol}: {e}")
            return None

    def get_current_prices(self, symbols: list[str]) -> dict[str, float]:
        """Get current prices for multiple symbols.
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dictionary mapping symbols to their current prices
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
            logger.error(f"Failed to get current prices: {e}")
            return {}