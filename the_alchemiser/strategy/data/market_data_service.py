"""Business Unit: utilities; Status: current.

Market Data Service - Enhanced market data operations with caching and validation.

This service builds on the MarketDataRepository interface to provide:
- Intelligent caching of market data
- Data validation and quality checks
- Batch operations for multiple symbols
- Market timing and schedule awareness

Typed Domain additions:
- Implements methods compatible with MarketDataPort (get_bars, get_latest_quote, get_mid_price)
    to support the Typed Domain V2 migration without legacy fallbacks.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pandas as pd

from the_alchemiser.shared.mappers.market_data_mappers import bars_to_domain
from the_alchemiser.shared.protocols.repository import MarketDataRepository
from the_alchemiser.shared.types.quote import QuoteModel
from the_alchemiser.shared.utils.decorators import translate_market_data_errors
from the_alchemiser.shared.value_objects.symbol import Symbol
from the_alchemiser.strategy.types.bar import BarModel

logger = logging.getLogger(__name__)


class MarketDataService:
    """Enhanced market data service with caching and validation.

    This service provides high-level market data operations built on top of
    the MarketDataRepository interface, adding intelligent caching, validation,
    and batch processing capabilities.
    """

    def __init__(
        self,
        market_data_repo: MarketDataRepository,
        cache_ttl_seconds: int = 5,
        enable_validation: bool = True,
    ) -> None:
        """Initialize the market data service.

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

    # --- Typed Domain V2: MarketDataPort-compatible methods ---
    @translate_market_data_errors()
    def get_bars(self, symbol: Symbol, period: str, timeframe: str) -> list[BarModel]:
        """Fetch historical bars mapped to domain models (BarModel list).

        Args:
            symbol: Domain Symbol
            period: e.g., '1y', '6mo', '3mo', '1mo', '200d'
            timeframe: e.g., '1d', '1h', '1m', '5m', '15m'

        Returns:
            List[BarModel] (may be empty on failure)

        """
        # Map period to start/end ISO strings
        end_dt = datetime.now(UTC)
        start_dt = end_dt - timedelta(days=self._map_period_to_days(period))
        start_iso = start_dt.date().isoformat()
        end_iso = end_dt.date().isoformat()

        repo_timeframe = self._map_timeframe_for_repo(timeframe)

        rows = self._market_data.get_historical_bars(
            symbol=str(symbol),
            start_date=start_iso,
            end_date=end_iso,
            timeframe=repo_timeframe,
        )
        return bars_to_domain(rows)

    @translate_market_data_errors(default_return=None)
    def get_latest_quote(self, symbol: Symbol) -> QuoteModel | None:
        """Fetch latest quote and map to domain QuoteModel.

        Note: Repository interface returns a (bid, ask) tuple; timestamp may be unavailable.
        """
        quote = self._market_data.get_latest_quote(str(symbol))
        if quote is None:
            return None
        bid, ask = quote
        # Validate basic positivity, allow bid == ask for cases where only one side is available
        if bid <= 0 or ask <= 0 or bid > ask:
            logger.warning(f"Invalid latest quote for {symbol}: bid={bid}, ask={ask}")
            return None
        return QuoteModel(ts=None, bid=Decimal(str(bid)), ask=Decimal(str(ask)))

    def get_mid_price(self, symbol: Symbol) -> float | None:
        """Return mid price from latest quote as float (protocol-compatible)."""
        q = self.get_latest_quote(symbol)
        if q is None:
            return None
        try:
            return float(q.mid)
        except Exception:
            return None

    @translate_market_data_errors(default_return=None)
    def get_validated_price(self, symbol: str, max_age_seconds: int | None = None) -> float | None:
        """Get current price with validation and optional caching.

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
            age = (datetime.now(UTC) - cached_time).total_seconds()

            if age <= max_age:
                logger.debug(f"Cache hit for {symbol} price: ${cached_price:.2f} (age: {age:.1f}s)")
                return cached_price

        # Fetch fresh data
        price = self._market_data.get_current_price(symbol)

        if price is None:
            logger.warning(f"No price data available for {symbol}")
            return None

        # Validate price
        if self._enable_validation and not self._is_valid_price(price, symbol):
            logger.warning(f"Invalid price for {symbol}: ${price}")
            return None

        # Cache the result
        self._price_cache[symbol] = (price, datetime.now(UTC))
        logger.debug(f"Fresh price for {symbol}: ${price:.2f}")

        return price

    @translate_market_data_errors(default_return=None)
    def get_validated_quote(
        self, symbol: str, max_age_seconds: int | None = None
    ) -> tuple[float, float] | None:
        """Get bid/ask quote with validation and optional caching.

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
            age = (datetime.now(UTC) - cached_time).total_seconds()

            if age <= max_age:
                logger.debug(f"Cache hit for {symbol} quote (age: {age:.1f}s)")
                return cached_quote

        # Fetch fresh data
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
        self._quote_cache[symbol] = (quote, datetime.now(UTC))
        logger.debug(f"Fresh quote for {symbol}: bid=${bid:.2f}, ask=${ask:.2f}")

        return quote

    def get_batch_prices(self, symbols: list[str]) -> dict[str, float]:
        """Get current prices for multiple symbols efficiently.

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
        """Analyze bid-ask spread for a symbol.

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
            "timestamp": datetime.now(UTC).isoformat(),
        }

    @translate_market_data_errors(default_return=False)
    def is_market_hours(self) -> bool:
        """Check if market is currently in trading hours.

        Returns:
            True if market is open, False otherwise

        """
        return self._market_data.is_market_open()

    def clear_cache(self, symbol: str | None = None) -> None:
        """Clear cached data.

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
        """Get cache statistics.

        Returns:
            Cache statistics dictionary

        """
        return {
            "price_cache_size": len(self._price_cache),
            "quote_cache_size": len(self._quote_cache),
            "cache_ttl_seconds": self._cache_ttl,
            "validation_enabled": self._enable_validation,
        }

    # --- Strategy compatibility helpers (pandas DataFrame API) ---
    def get_data(
        self,
        symbol: str,
        timeframe: str = "1day",
        period: str = "1y",
        **_: Any,
    ) -> pd.DataFrame:
        """Compatibility method to provide pandas DataFrame bars.

        This adapts the typed domain get_bars API to the strategies' expected
        DataFrame shape with columns: Open, High, Low, Close, Volume and a Date index.

        Args:
            symbol: Ticker symbol
            timeframe: "1day" | "1hour" | "1min" (case-insensitive)
            period: Historical window e.g. "1y", "6mo", "3mo", "1mo", "200d"

        Returns:
            Pandas DataFrame. Empty on failure.

        """
        try:
            # Map to typed domain inputs and fetch bars
            tf = self._map_timeframe_for_client(timeframe)
            bars = self.get_bars(Symbol(symbol), period, tf)

            if not bars:
                return pd.DataFrame()

            # Convert BarModel list to DataFrame
            data = {
                "Open": [float(b.open) for b in bars],
                "High": [float(b.high) for b in bars],
                "Low": [float(b.low) for b in bars],
                "Close": [float(b.close) for b in bars],
                "Volume": [float(b.volume) for b in bars],
            }
            idx = [b.ts for b in bars]
            df = pd.DataFrame(data, index=pd.to_datetime(idx))
            df.index.name = "Date"
            return df
        except Exception as e:  # pragma: no cover - best-effort compatibility
            logger.warning(f"get_data failed for {symbol}: {e}")
            return pd.DataFrame()

    def _is_valid_price(self, price: float, symbol: str) -> bool:
        """Validate a price value.

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
        """Validate a bid/ask quote.

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

        # Bid should be less than or equal to ask (allow equal for single-side quotes)
        if bid > ask:
            logger.warning(f"Invalid quote for {symbol}: bid=${bid} > ask=${ask}")
            return False

        # Spread shouldn't be too wide (more than 10%)
        spread_pct = ((ask - bid) / ((bid + ask) / 2)) * 100
        if spread_pct > 10:
            logger.warning(f"Very wide spread for {symbol}: {spread_pct:.1f}%")
            # Don't return False here, just warn - wide spreads can be legitimate

        return True

    # --- helpers ---
    def _map_period_to_days(self, period: str) -> int:
        mapping: dict[str, int] = {
            "1y": 365,
            "6mo": 180,
            "3mo": 90,
            "1mo": 30,
            "200d": 200,
        }
        return mapping.get(period, 365)

    def _map_timeframe_for_repo(self, tf: str) -> str:
        tf_norm = tf.lower().strip()
        if tf_norm in {"1d", "1day", "day", "d"}:
            return "1Day"
        if tf_norm in {"1h", "1hour", "hour", "h"}:
            return "1Hour"
        if tf_norm in {"15m", "15min"}:
            return "15Min"
        if tf_norm in {"5m", "5min"}:
            return "5Min"
        # default minute granularity
        return "1Min"

    def _map_timeframe_for_client(self, tf: str) -> str:
        """Map human timeframe to the get_bars-friendly shorthand."""
        tf_norm = tf.lower().strip()
        if tf_norm in {"1d", "1day", "day", "daily", "d"}:
            return "1d"
        if tf_norm in {"1h", "1hour", "hour", "hourly", "h"}:
            return "1h"
        if tf_norm in {"1m", "1min", "minute", "min", "m"}:
            return "1m"
        return "1d"
