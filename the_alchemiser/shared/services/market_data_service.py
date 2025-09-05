#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Canonical Market Data Service for Alpaca Integration.

This service provides the single, canonical way to interact with Alpaca historical 
market data APIs across all modules (strategy, portfolio, execution). It consolidates
scattered market data functionality and provides a clean, consistent interface.

Features:
- Historical bar data retrieval with flexible timeframes and periods
- Real-time quote data access
- Intelligent caching with TTL
- Data validation and quality checks
- Consistent error handling across all market data operations
- Support for both pandas DataFrame and domain model outputs

Usage:
    from the_alchemiser.shared.services.market_data_service import SharedMarketDataService
    
    service = SharedMarketDataService(api_key="...", secret_key="...")
    
    # Get historical data as DataFrame
    df = service.get_historical_bars("AAPL", period="1y", interval="1d")
    
    # Get latest quote
    bid, ask = service.get_latest_quote("AAPL")
    
    # Get current price
    price = service.get_current_price("AAPL")
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import pandas as pd
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from the_alchemiser.shared.types.exceptions import MarketDataError

logger = logging.getLogger(__name__)


class SharedMarketDataService:
    """Canonical market data service for Alpaca integration.
    
    This service provides the single, consolidated interface for all Alpaca
    market data operations across strategy, portfolio, and execution modules.
    """

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        *,
        paper: bool = True,
        cache_ttl_seconds: int = 5,
        enable_validation: bool = True,
    ) -> None:
        """Initialize the shared market data service.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            paper: Whether to use paper trading environment
            cache_ttl_seconds: Cache time-to-live in seconds
            enable_validation: Whether to enable data validation

        """
        self.api_key = api_key
        self.secret_key = secret_key
        self._paper = paper
        self._cache_ttl = cache_ttl_seconds
        self._enable_validation = enable_validation
        
        # Lazy import to avoid circular dependencies
        self._alpaca_manager = None
        
        # Caching for performance
        self._price_cache: dict[str, tuple[float, datetime]] = {}
        self._quote_cache: dict[str, tuple[tuple[float, float], datetime]] = {}

    def _get_alpaca_manager(self) -> Any:  # noqa: ANN401
        """Get or create AlpacaManager instance with lazy loading."""
        if self._alpaca_manager is None:
            # Import here to avoid circular dependency issues
            from the_alchemiser.execution.brokers.alpaca import AlpacaManager
            self._alpaca_manager = AlpacaManager(self.api_key, self.secret_key, paper=self._paper)
        return self._alpaca_manager

    def get_historical_bars(
        self, symbol: str, period: str = "1y", interval: str = "1d"
    ) -> pd.DataFrame:
        """Get historical bar data for a symbol.

        Args:
            symbol: Stock symbol (e.g., "AAPL", "TSLA")
            period: Time period - "1y", "6mo", "3mo", "1mo", "200d"
            interval: Data interval - "1d", "1h", "1m"

        Returns:
            DataFrame with OHLCV data, indexed by timestamp

        Raises:
            MarketDataError: If data retrieval fails

        Example:
            >>> service = SharedMarketDataService(api_key="...", secret_key="...")
            >>> df = service.get_historical_bars("AAPL", period="6mo", interval="1d")
            >>> print(df.head())

        """
        try:
            # Convert period to start/end dates
            end_date = datetime.now(UTC)
            period_mapping = {"1y": 365, "6mo": 180, "3mo": 90, "1mo": 30, "200d": 200}
            days = period_mapping.get(period, 365)
            start_date = end_date - timedelta(days=days)

            # Convert interval to TimeFrame
            interval_mapping = {
                "1d": TimeFrame.Day,
                "1h": TimeFrame.Hour,
                "1m": TimeFrame.Minute,
            }
            timeframe = interval_mapping.get(interval, TimeFrame.Day)

            # Create request
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=cast(TimeFrame, timeframe),
                start=start_date,
                # Don't set end - let it default to 15 minutes ago for free tier
            )

            # Fetch data using AlpacaManager's data client
            alpaca_manager = self._get_alpaca_manager()
            bars = alpaca_manager.data_client.get_stock_bars(request)

            if not bars:
                logger.warning(f"No historical data received for {symbol}")
                return pd.DataFrame()

            # Extract bar data - handle different response formats safely
            bar_data = self._extract_bar_data(bars, symbol)

            if not bar_data:
                logger.warning(f"No bar data found for {symbol}")
                return pd.DataFrame()

            return self._convert_to_dataframe(bar_data)

        except Exception as e:
            logger.error(f"Failed to fetch historical data for {symbol}: {e}")
            raise MarketDataError(f"Failed to fetch historical data for {symbol}: {e}") from e

    def get_historical_bars_date_range(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        timeframe: TimeFrame | str | None = None,
    ) -> list[Any]:
        """Get historical data for a specific date range.

        Args:
            symbol: Stock symbol
            start: Start datetime
            end: End datetime
            timeframe: TimeFrame enum or string representation

        Returns:
            List of bar objects from Alpaca API

        Raises:
            MarketDataError: If data retrieval fails

        """
        try:
            # Handle timeframe parameter
            if timeframe is None:
                timeframe = TimeFrame.Day
            elif isinstance(timeframe, str):
                # Convert string to TimeFrame enum
                timeframe_mapping = {
                    "Day": TimeFrame.Day,
                    "Hour": TimeFrame.Hour,
                    "Minute": TimeFrame.Minute,
                    "1d": TimeFrame.Day,
                    "1h": TimeFrame.Hour,
                    "1m": TimeFrame.Minute,
                }
                timeframe = timeframe_mapping.get(timeframe, TimeFrame.Day)

            # Create request
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=cast(TimeFrame, timeframe),
                start=start,
                end=end,
            )

            # Fetch data using AlpacaManager's data client
            alpaca_manager = self._get_alpaca_manager()
            bars = alpaca_manager.data_client.get_stock_bars(request)

            # Extract bars for the symbol safely
            bar_data = self._extract_bar_data(bars, symbol)
            return list(bar_data) if bar_data else []

        except Exception as e:
            logger.error(f"Failed to fetch historical data for {symbol} from {start} to {end}: {e}")
            raise MarketDataError(
                f"Failed to fetch historical data for {symbol} from {start} to {end}: {e}"
            ) from e

    def get_latest_quote(self, symbol: str) -> tuple[float, float]:
        """Get the latest bid and ask quote for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Tuple of (bid, ask) prices

        Raises:
            MarketDataError: If quote retrieval fails

        """
        # Check cache first
        if symbol in self._quote_cache:
            cached_quote, cached_time = self._quote_cache[symbol]
            if (datetime.now(UTC) - cached_time).total_seconds() < self._cache_ttl:
                logger.debug(f"Using cached quote for {symbol}: {cached_quote}")
                return cached_quote

        try:
            alpaca_manager = self._get_alpaca_manager()
            quote = alpaca_manager.get_latest_quote(symbol)

            if quote:
                bid = float(getattr(quote, "bid_price", 0) or 0)
                ask = float(getattr(quote, "ask_price", 0) or 0)
                
                # Validate quote if enabled
                if self._enable_validation and not self._is_valid_quote(bid, ask, symbol):
                    logger.warning(f"Invalid quote for {symbol}: bid=${bid}, ask=${ask}")
                    return 0.0, 0.0
                
                # Cache the result
                result = (bid, ask)
                self._quote_cache[symbol] = (result, datetime.now(UTC))
                logger.debug(f"Fresh quote for {symbol}: bid=${bid:.2f}, ask=${ask:.2f}")
                return result

            logger.warning(f"No quote data available for {symbol}")
            return 0.0, 0.0

        except Exception as e:
            logger.error(f"Failed to fetch latest quote for {symbol}: {e}")
            return 0.0, 0.0

    def get_current_price(self, symbol: str) -> float | None:
        """Get current price from the latest quote using mid-price calculation.

        Args:
            symbol: Stock symbol

        Returns:
            Current price or None if unavailable

        """
        # Check cache first
        if symbol in self._price_cache:
            cached_price, cached_time = self._price_cache[symbol]
            if (datetime.now(UTC) - cached_time).total_seconds() < self._cache_ttl:
                logger.debug(f"Using cached price for {symbol}: ${cached_price:.2f}")
                return cached_price

        try:
            bid, ask = self.get_latest_quote(symbol)
            
            if bid > 0 and ask > 0:
                # Calculate mid-price
                price = (bid + ask) / 2.0
                
                # Validate price if enabled
                if self._enable_validation and not self._is_valid_price(price, symbol):
                    logger.warning(f"Invalid price for {symbol}: ${price}")
                    return None
                
                # Cache the result
                self._price_cache[symbol] = (price, datetime.now(UTC))
                logger.debug(f"Fresh price for {symbol}: ${price:.2f}")
                return price
            
            logger.warning(f"No valid quote data for price calculation: {symbol}")
            return None

        except Exception as e:
            logger.error(f"Failed to get current price for {symbol}: {e}")
            return None

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._price_cache.clear()
        self._quote_cache.clear()
        logger.debug("Market data cache cleared")

    def _extract_bar_data(self, bars: Any, symbol: str) -> Any:  # noqa: ANN401
        """Extract bar data from API response.
        
        Handles various response formats from Alpaca API safely.
        """
        try:
            # Try direct symbol access first (most common)
            if hasattr(bars, symbol):
                return getattr(bars, symbol)
            # Try data dictionary access as fallback
            if hasattr(bars, "data"):
                data_dict = getattr(bars, "data", {})
                if hasattr(data_dict, "get"):
                    return data_dict.get(symbol, [])
                if symbol in data_dict:
                    return data_dict[symbol]
        except (AttributeError, KeyError, TypeError) as e:
            logger.warning(f"Failed to extract bar data for {symbol}: {e}")

        return None

    def _convert_to_dataframe(self, bar_data: Any) -> pd.DataFrame:  # noqa: ANN401
        """Convert bar data to pandas DataFrame."""
        data_rows = []
        timestamps = []

        for bar in bar_data:
            if hasattr(bar, "open") and hasattr(bar, "high"):  # Validate bar structure
                data_rows.append(
                    {
                        "Open": float(bar.open),
                        "High": float(bar.high),
                        "Low": float(bar.low),
                        "Close": float(bar.close),
                        "Volume": int(bar.volume) if hasattr(bar, "volume") else 0,
                    }
                )
                timestamps.append(bar.timestamp)

        if not data_rows:
            logger.warning("No valid bar data to convert to DataFrame")
            return pd.DataFrame()

        # Create DataFrame with datetime index
        df = pd.DataFrame(data_rows)
        df.index = pd.to_datetime(timestamps)
        df.index.name = "Date"

        logger.debug(f"Converted {len(data_rows)} bars to DataFrame")
        return df

    def _is_valid_quote(self, bid: float, ask: float, symbol: str) -> bool:
        """Validate quote data for reasonableness."""
        if bid <= 0 or ask <= 0:
            return False
        
        if bid > ask:
            logger.warning(f"Invalid quote for {symbol}: bid (${bid}) > ask (${ask})")
            return False
        
        # Check for unreasonably wide spreads (>50% of mid-price)
        mid_price = (bid + ask) / 2
        spread_pct = ((ask - bid) / mid_price) * 100 if mid_price > 0 else 0
        
        if spread_pct > 50:
            logger.warning(f"Wide spread for {symbol}: {spread_pct:.1f}% (bid=${bid}, ask=${ask})")
            # Don't return False here, just warn - wide spreads can be legitimate

        return True

    def _is_valid_price(self, price: float, symbol: str) -> bool:
        """Validate price data for reasonableness."""
        if price <= 0:
            return False
        
        # Basic sanity checks - prices should be reasonable for typical stocks
        if price > 100000:  # Unreasonably high
            logger.warning(f"Unreasonably high price for {symbol}: ${price}")
            return False
        
        return True


def create_shared_market_data_service(
    api_key: str,
    secret_key: str,
    *,
    paper: bool = True,
    **kwargs: dict[str, Any],
) -> SharedMarketDataService:
    """Create a shared market data service.

    Args:
        api_key: Alpaca API key
        secret_key: Alpaca secret key
        paper: Whether to use paper trading environment
        **kwargs: Additional configuration options

    Returns:
        Configured SharedMarketDataService instance

    """
    return SharedMarketDataService(
        api_key=api_key,
        secret_key=secret_key,
        paper=paper,
        **kwargs,
    )