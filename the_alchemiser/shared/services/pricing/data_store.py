"""Business Unit: shared | Status: current.

Thread-safe quote and trade data storage encapsulating lock usage.
"""

from __future__ import annotations

import threading
from datetime import UTC, datetime

from the_alchemiser.shared.types.market_data import PriceDataModel, QuoteModel

from .models import AlpacaQuoteData, RealTimeQuote


class PricingDataStore:
    """Thread-safe storage for pricing data with encapsulated locking."""

    def __init__(self) -> None:
        """Initialize data storage with thread-safe containers."""
        # Legacy storage for backward compatibility
        self._quotes: dict[str, RealTimeQuote] = {}
        
        # New structured data storage
        self._price_data: dict[str, PriceDataModel] = {}
        self._quote_data: dict[str, QuoteModel] = {}
        
        # Quote tracking data
        self._latest_quotes: dict[str, AlpacaQuoteData] = {}
        self._latest_bid: dict[str, float] = {}
        self._latest_ask: dict[str, float] = {}
        self._last_quote_time: dict[str, datetime] = {}
        self._last_update: dict[str, datetime] = {}
        
        # Thread safety
        self._quotes_lock = threading.Lock()

    def get_real_time_quote(self, symbol: str) -> RealTimeQuote | None:
        """Get legacy real-time quote for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            RealTimeQuote object or None if not available

        """
        with self._quotes_lock:
            return self._quotes.get(symbol)

    def get_quote_data(self, symbol: str) -> QuoteModel | None:
        """Get structured quote data for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            QuoteModel object with bid/ask prices and sizes, or None if not available

        """
        with self._quotes_lock:
            return self._quote_data.get(symbol)

    def get_price_data(self, symbol: str) -> PriceDataModel | None:
        """Get structured price data for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            PriceDataModel object with price, bid/ask, and volume, or None if not available

        """
        with self._quotes_lock:
            return self._price_data.get(symbol)

    def get_latest_quote_raw(self, symbol: str) -> AlpacaQuoteData | None:
        """Get latest raw quote data for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Raw Alpaca quote data or None if not available

        """
        with self._quotes_lock:
            return self._latest_quotes.get(symbol)

    def get_latest_bid_ask(self, symbol: str) -> tuple[float, float] | None:
        """Get latest bid/ask prices for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Tuple of (bid, ask) or None if not available

        """
        with self._quotes_lock:
            bid = self._latest_bid.get(symbol)
            ask = self._latest_ask.get(symbol)
            if bid is not None and ask is not None:
                return bid, ask
            return None

    def update_quote_data(
        self,
        symbol: str,
        bid_price: float,
        ask_price: float,
        bid_size: float | None,
        ask_size: float | None,
        timestamp: datetime,
    ) -> None:
        """Update quote data with thread safety.
        
        Args:
            symbol: Stock symbol
            bid_price: Bid price
            ask_price: Ask price
            bid_size: Bid size (optional)
            ask_size: Ask size (optional)
            timestamp: Quote timestamp

        """
        with self._quotes_lock:
            current_quote = self._quotes.get(symbol)

            # Legacy RealTimeQuote storage (for backward compatibility)
            if current_quote:
                # Update existing quote
                self._quotes[symbol] = RealTimeQuote(
                    bid=bid_price,
                    ask=ask_price,
                    last_price=current_quote.last_price,
                    timestamp=timestamp,
                )
            else:
                # Create new quote
                self._quotes[symbol] = RealTimeQuote(
                    bid=bid_price,
                    ask=ask_price,
                    last_price=0.0,
                    timestamp=timestamp,
                )

            # New structured QuoteModel storage
            self._quote_data[symbol] = QuoteModel(
                symbol=symbol,
                bid_price=bid_price,
                ask_price=ask_price,
                bid_size=bid_size or 0.0,
                ask_size=ask_size or 0.0,
                timestamp=timestamp,
            )

    def update_trade_data(
        self,
        symbol: str,
        price: float,
        timestamp: datetime,
        volume: int | float | None = None,
    ) -> None:
        """Update trade data with thread safety.
        
        Args:
            symbol: Stock symbol
            price: Trade price
            timestamp: Trade timestamp
            volume: Trade volume (optional)

        """
        with self._quotes_lock:
            current_quote = self._quotes.get(symbol)
            current_quote_data = self._quote_data.get(symbol)

            # Legacy RealTimeQuote storage (for backward compatibility)
            if current_quote:
                # Update existing quote with new trade price
                self._quotes[symbol] = RealTimeQuote(
                    bid=current_quote.bid,
                    ask=current_quote.ask,
                    last_price=float(price or 0),
                    timestamp=timestamp,
                )
            else:
                # Create new quote with trade price only
                self._quotes[symbol] = RealTimeQuote(
                    bid=0.0,
                    ask=0.0,
                    last_price=float(price or 0),
                    timestamp=timestamp,
                )

            # New structured PriceDataModel storage
            bid_price = current_quote_data.bid_price if current_quote_data else None
            ask_price = current_quote_data.ask_price if current_quote_data else None

            self._price_data[symbol] = PriceDataModel(
                symbol=symbol,
                price=float(price or 0),
                timestamp=timestamp,
                bid=bid_price,
                ask=ask_price,
                volume=int(volume or 0) if volume else None,
            )

            self._last_update[symbol] = datetime.now(UTC)

    def update_latest_quote(self, symbol: str, quote_data: AlpacaQuoteData) -> None:
        """Update latest raw quote data.
        
        Args:
            symbol: Stock symbol
            quote_data: Raw Alpaca quote data

        """
        with self._quotes_lock:
            self._latest_quotes[symbol] = quote_data

    def update_latest_bid_ask(self, symbol: str, bid: float, ask: float) -> None:
        """Update latest bid/ask tracking.
        
        Args:
            symbol: Stock symbol
            bid: Bid price
            ask: Ask price

        """
        with self._quotes_lock:
            self._latest_bid[symbol] = bid
            self._latest_ask[symbol] = ask

    def update_quote_timestamp(self, symbol: str) -> None:
        """Update last quote time for a symbol.
        
        Args:
            symbol: Stock symbol

        """
        with self._quotes_lock:
            self._last_quote_time[symbol] = datetime.now(UTC)

    def cleanup_old_quotes(self, max_age_seconds: int) -> int:
        """Remove old quotes to prevent memory bloat.
        
        Args:
            max_age_seconds: Maximum age of quotes in seconds
            
        Returns:
            Number of quotes removed

        """
        cutoff_time = datetime.now(UTC).timestamp() - max_age_seconds
        removed_count = 0

        with self._quotes_lock:
            symbols_to_remove = []
            
            for symbol, quote in self._quotes.items():
                if quote.timestamp.timestamp() < cutoff_time:
                    symbols_to_remove.append(symbol)

            for symbol in symbols_to_remove:
                self._quotes.pop(symbol, None)
                self._price_data.pop(symbol, None)
                self._quote_data.pop(symbol, None)
                self._latest_quotes.pop(symbol, None)
                self._latest_bid.pop(symbol, None)
                self._latest_ask.pop(symbol, None)
                self._last_quote_time.pop(symbol, None)
                self._last_update.pop(symbol, None)
                removed_count += 1

        return removed_count

    def get_stats(self) -> dict[str, int]:
        """Get data storage statistics.
        
        Returns:
            Dictionary with storage statistics

        """
        with self._quotes_lock:
            return {
                "symbols_tracked_legacy": len(self._quotes),
                "symbols_tracked_structured_prices": len(self._price_data),
                "symbols_tracked_structured_quotes": len(self._quote_data),
                "symbols_tracked": len(self._quotes),  # For backward compatibility
            }