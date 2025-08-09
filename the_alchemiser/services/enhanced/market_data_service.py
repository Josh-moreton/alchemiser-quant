"""
Market Data Service - Enhanced market data operations with caching and validation.

This service builds on the MarketDataRepository interface to provide:
- Intelligent caching of market data
- Data validation and quality checks
- Batch operations for multiple symbols
- Market timing and schedule awareness
"""

import logging
from datetime import datetime
from typing import Any

from the_alchemiser.domain.interfaces import MarketDataRepository

logger = logging.getLogger(__name__)


class MarketDataService:
    """
    Enhanced market data service with caching and validation.

    This service provides high-level market data operations built on top of
    the MarketDataRepository interface, adding intelligent caching, validation,
    and batch processing capabilities.
    """

    def __init__(
        self,
        market_data_repo: MarketDataRepository,
        cache_ttl_seconds: int = 5,
        enable_validation: bool = True,
    ):
        """
        Initialize the market data service.

        Args:
            market_data_repo: Market data repository implementation
            cache_ttl_seconds: Cache time-to-live in seconds
            enable_validation: Whether to enable data validation
        """
        self._market_data = market_data_repo
        self._cache_ttl = cache_ttl_seconds
        self._enable_validation = enable_validation
        self._price_cache: dict[str, tuple[float, datetime]] = {}
        self._quote_cache: dict[str, tuple[tuple[float, float], datetime]] = {}

    def get_validated_price(self, symbol: str, max_age_seconds: int | None = None) -> float | None:
        """
        Get current price with validation and optional caching.

        Args:
            symbol: Stock symbol
            max_age_seconds: Maximum age for cached data (None uses default TTL)

        Returns:
            Validated current price, or None if not available or invalid
        """
        max_age = max_age_seconds or self._cache_ttl

        # Check cache first
        if symbol in self._price_cache:
            cached_price, cached_time = self._price_cache[symbol]
            age = (datetime.now() - cached_time).total_seconds()

            if age <= max_age:
                logger.debug(f"Cache hit for {symbol} price: ${cached_price:.2f} (age: {age:.1f}s)")
                return cached_price

        # Fetch fresh data
        try:
            price = self._market_data.get_current_price(symbol)

            if price is None:
                logger.warning(f"No price data available for {symbol}")
                return None

            # Validate price
            if self._enable_validation and not self._is_valid_price(price, symbol):
                logger.warning(f"Invalid price for {symbol}: ${price}")
                return None

            # Cache the result
            self._price_cache[symbol] = (price, datetime.now())
            logger.debug(f"Fresh price for {symbol}: ${price:.2f}")

            return price

        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            return None

    def get_validated_quote(
        self, symbol: str, max_age_seconds: int | None = None
    ) -> tuple[float, float] | None:
        """
        Get bid/ask quote with validation and optional caching.

        Args:
            symbol: Stock symbol
            max_age_seconds: Maximum age for cached data (None uses default TTL)

        Returns:
            Tuple of (bid, ask) prices, or None if not available or invalid
        """
        max_age = max_age_seconds or self._cache_ttl

        # Check cache first
        if symbol in self._quote_cache:
            cached_quote, cached_time = self._quote_cache[symbol]
            age = (datetime.now() - cached_time).total_seconds()

            if age <= max_age:
                logger.debug(f"Cache hit for {symbol} quote (age: {age:.1f}s)")
                return cached_quote

        # Fetch fresh data
        try:
            quote = self._market_data.get_latest_quote(symbol)

            if quote is None:
                logger.warning(f"No quote data available for {symbol}")
                return None

            bid, ask = quote

            # Validate quote
            if self._enable_validation and not self._is_valid_quote(bid, ask, symbol):
                logger.warning(f"Invalid quote for {symbol}: bid=${bid}, ask=${ask}")
                return None

            # Cache the result
            self._quote_cache[symbol] = (quote, datetime.now())
            logger.debug(f"Fresh quote for {symbol}: bid=${bid:.2f}, ask=${ask:.2f}")

            return quote

        except Exception as e:
            logger.error(f"Failed to get quote for {symbol}: {e}")
            return None

    def get_batch_prices(self, symbols: list[str]) -> dict[str, float]:
        """
        Get current prices for multiple symbols efficiently.

        Args:
            symbols: List of stock symbols

        Returns:
            Dictionary mapping symbols to their current prices
        """
        results = {}

        for symbol in symbols:
            price = self.get_validated_price(symbol)
            if price is not None:
                results[symbol] = price

        logger.info(f"Retrieved prices for {len(results)}/{len(symbols)} symbols")
        return results

    def get_spread_analysis(self, symbol: str) -> dict[str, Any] | None:
        """
        Analyze bid-ask spread for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Spread analysis data or None if not available
        """
        quote = self.get_validated_quote(symbol)

        if quote is None:
            return None

        bid, ask = quote
        spread = ask - bid
        mid_price = (bid + ask) / 2
        spread_pct = (spread / mid_price) * 100 if mid_price > 0 else 0

        return {
            "symbol": symbol,
            "bid": bid,
            "ask": ask,
            "spread": spread,
            "spread_pct": spread_pct,
            "mid_price": mid_price,
            "timestamp": datetime.now().isoformat(),
        }

    def is_market_hours(self) -> bool:
        """
        Check if market is currently in trading hours.

        Returns:
            True if market is open, False otherwise
        """
        try:
            return self._market_data.is_market_open()
        except Exception as e:
            logger.error(f"Failed to check market hours: {e}")
            return False

    def clear_cache(self, symbol: str | None = None) -> None:
        """
        Clear cached data.

        Args:
            symbol: Specific symbol to clear, or None to clear all
        """
        if symbol:
            self._price_cache.pop(symbol, None)
            self._quote_cache.pop(symbol, None)
            logger.debug(f"Cleared cache for {symbol}")
        else:
            self._price_cache.clear()
            self._quote_cache.clear()
            logger.debug("Cleared all cached data")

    def get_cache_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Cache statistics dictionary
        """
        return {
            "price_cache_size": len(self._price_cache),
            "quote_cache_size": len(self._quote_cache),
            "cache_ttl_seconds": self._cache_ttl,
            "validation_enabled": self._enable_validation,
        }

    def _is_valid_price(self, price: float, symbol: str) -> bool:
        """
        Validate a price value.

        Args:
            price: Price to validate
            symbol: Symbol for context

        Returns:
            True if price is valid, False otherwise
        """
        if price <= 0:
            return False

        # Basic sanity checks
        if price > 100000:  # Extremely high price
            logger.warning(f"Suspiciously high price for {symbol}: ${price}")
            return False

        if price < 0.01:  # Extremely low price
            logger.warning(f"Suspiciously low price for {symbol}: ${price}")
            return False

        return True

    def _is_valid_quote(self, bid: float, ask: float, symbol: str) -> bool:
        """
        Validate a bid/ask quote.

        Args:
            bid: Bid price
            ask: Ask price
            symbol: Symbol for context

        Returns:
            True if quote is valid, False otherwise
        """
        # Basic price validation
        if not (self._is_valid_price(bid, symbol) and self._is_valid_price(ask, symbol)):
            return False

        # Bid should be less than ask
        if bid >= ask:
            logger.warning(f"Invalid quote for {symbol}: bid=${bid} >= ask=${ask}")
            return False

        # Spread shouldn't be too wide (more than 10%)
        spread_pct = ((ask - bid) / ((bid + ask) / 2)) * 100
        if spread_pct > 10:
            logger.warning(f"Very wide spread for {symbol}: {spread_pct:.1f}%")
            # Don't return False here, just warn - wide spreads can be legitimate

        return True
