import logging
import time
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from collections.abc import Callable

import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient

from the_alchemiser.core.secrets.secrets_manager import SecretsManager

from ..exceptions import DataProviderError, MarketDataError, TradingClientError

# TODO: Phase 11 - Types available for future migration to structured data types
# from the_alchemiser.core.types import DataProviderResult, MarketDataPoint, PriceData


class UnifiedDataProvider:
    """
    Unified data provider that consolidates market data and trading functionality.

    This class combines the best features of both DataProvider and AlpacaDataProvider:
    - Proper paper_trading parameter handling
    - Unified caching system
    - Consistent error handling
    - Both market data and trading functionality
    - Proper type safety
    """

    def __init__(
        self,
        paper_trading: bool = True,
        cache_duration: int | None = None,
        config: Any | None = None,  # TODO: Phase 11 - Add proper Settings type when available
        enable_real_time: bool = True,
    ) -> None:
        """
        Initialize UnifiedDataProvider for Alpaca market data and trading.

        Args:
            paper_trading: Whether to use paper trading keys (default: True for safety)
            cache_duration: Cache duration in seconds (default from config)
            config: Configuration object. If None, will load from global config.
            enable_real_time: Whether to enable real-time WebSocket pricing (default: True)
        """
        self.paper_trading = paper_trading

        # Use provided config or load global config
        if config is None:
            from the_alchemiser.core.config import load_settings

            config = load_settings()
        self.config = config

        # Set cache duration
        if cache_duration is None:
            cache_duration = (
                self.config.data.cache_duration or 3600
            )  # Default 1 hour if config is None
        self.cache_duration: int = int(cache_duration) if cache_duration is not None else 3600
        self.cache: dict[tuple[str, str, str], tuple[float, pd.DataFrame]] = (
            {}
        )  # TODO: Phase 11 - Typed cache structure

        # Initialize secrets manager - region will be loaded from config
        secrets_manager = SecretsManager()

        # Get API keys from AWS Secrets Manager
        api_key_result = secrets_manager.get_alpaca_keys(paper_trading=paper_trading)
        self.api_key: str | None
        self.secret_key: str | None
        self.api_key, self.secret_key = api_key_result

        if not self.api_key or not self.secret_key:
            raise ValueError(
                f"Alpaca API keys not found in AWS Secrets Manager for {'paper' if paper_trading else 'live'} trading"
            )

        # Initialize Alpaca clients
        self.data_client = StockHistoricalDataClient(self.api_key, self.secret_key)
        self.trading_client = TradingClient(self.api_key, self.secret_key, paper=paper_trading)

        # Set endpoints (for reference)
        if paper_trading:
            self.api_endpoint = self.config.alpaca.paper_endpoint
        else:
            self.api_endpoint = self.config.alpaca.endpoint

        # Initialize real-time pricing service (type will be set dynamically)
        self.real_time_pricing = None
        if enable_real_time:
            try:
                from the_alchemiser.core.data.real_time_pricing import RealTimePricingManager

                self.real_time_pricing = RealTimePricingManager(
                    self.api_key, self.secret_key, paper_trading
                )
                self.real_time_pricing.set_fallback_provider(self.get_current_price_rest)
                self.real_time_pricing.start()
                logging.info("✅ Real-time pricing enabled")
            except DataProviderError as e:
                from ..logging.logging_utils import get_logger, log_error_with_context

                logger = get_logger(__name__)
                log_error_with_context(
                    logger,
                    e,
                    "real_time_pricing_initialization",
                    function="__init__",
                    error_type=type(e).__name__,
                )
                logging.warning(f"Data provider error initializing real-time pricing: {e}")
                self.real_time_pricing = None
            except Exception as e:
                from ..logging.logging_utils import get_logger, log_error_with_context

                logger = get_logger(__name__)
                log_error_with_context(
                    logger,
                    e,
                    "real_time_pricing_initialization",
                    function="__init__",
                    error_type="unexpected_error",
                    original_error=type(e).__name__,
                )
                logging.warning(f"Unexpected error initializing real-time pricing: {e}")
                self.real_time_pricing = None

        logging.debug(
            f"Initialized UnifiedDataProvider with {'paper' if paper_trading else 'live'} trading keys"
        )

    def get_data(
        self, symbol: str, period: str = "1y", interval: str = "1d"
    ) -> pd.DataFrame | None:  # TODO: Phase 11 - Consider migrating to MarketDataPoint structure
        """
        Get historical market data with caching.

        Args:
            symbol: Stock symbol
            period: Time period (1y, 6mo, 3mo, 1mo, 200d)
            interval: Data interval (1d, 1h, 1m)

        Returns:
            pandas.DataFrame with OHLCV data
        """
        now = time.time()
        cache_key = (symbol, period, interval)

        # Check cache
        if cache_key in self.cache:
            cached_time, data = self.cache[cache_key]
            if now - cached_time < self.cache_duration:
                logging.debug(f"Returning cached data for {symbol}")
                return data

        # Fetch fresh data
        try:
            df = self._fetch_historical_data(symbol, period, interval)

            if df is not None and not df.empty:
                # Cache the data
                self.cache[cache_key] = (now, df)
                logging.debug(f"Fetched and cached {len(df)} bars for {symbol}")
                return df
            else:
                logging.warning(f"No data returned for {symbol}")
                return pd.DataFrame()

        except MarketDataError as e:
            from ..logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "historical_data_fetch",
                function="get_historical_data",
                symbol=symbol,
                period=period,
                interval=interval,
                error_type=type(e).__name__,
            )
            logging.error(f"Market data error fetching data for {symbol}: {e}")
            return pd.DataFrame()
        except Exception as e:
            from ..logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "historical_data_fetch",
                function="get_historical_data",
                symbol=symbol,
                period=period,
                interval=interval,
                error_type="unexpected_error",
                original_error=type(e).__name__,
            )
            logging.error(f"Unexpected error fetching data for {symbol}: {e}")
            return pd.DataFrame()

    def _fetch_historical_data(self, symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
        """Fetch historical data from Alpaca API."""
        try:
            # Convert period to start/end dates
            end_date = datetime.now()

            period_mapping = {"1y": 365, "6mo": 180, "3mo": 90, "1mo": 30, "200d": 200}
            days = period_mapping.get(period, 365)
            start_date = end_date - timedelta(days=days)

            # Convert interval to TimeFrame
            interval_mapping = {"1d": TimeFrame.Day, "1h": TimeFrame.Hour, "1m": TimeFrame.Minute}
            timeframe = interval_mapping.get(interval, TimeFrame.Day)

            # Create request
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=cast(TimeFrame, timeframe),
                start=start_date,
                # Don't set end - let it default to 15 minutes ago for free tier
            )

            # Fetch data
            bars = self.data_client.get_stock_bars(request)

            if not bars:
                return pd.DataFrame()

            # Extract bar data - handle different response formats safely
            bar_data = None
            try:
                # Try direct symbol access first (most common)
                if hasattr(bars, symbol):
                    bar_data = getattr(bars, symbol)
                # Try data dictionary access as fallback
                elif hasattr(bars, "data"):
                    data_dict = getattr(bars, "data", {})
                    if hasattr(data_dict, "get"):
                        bar_data = data_dict.get(symbol, [])
                    elif symbol in data_dict:
                        bar_data = data_dict[symbol]
            except (AttributeError, KeyError, TypeError):
                pass

            if not bar_data:
                return pd.DataFrame()

            # Convert to DataFrame
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
                return pd.DataFrame()

            # Create DataFrame with datetime index
            df = pd.DataFrame(data_rows)
            df.index = pd.to_datetime(timestamps)
            df.index.name = "Date"

            return df

        except MarketDataError as e:
            from ..logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "historical_data_fetch_internal",
                function="_fetch_historical_data",
                symbol=symbol,
                period=period,
                interval=interval,
                error_type=type(e).__name__,
            )
            logging.error(f"Market data error fetching historical data for {symbol}: {e}")
            return pd.DataFrame()
        except Exception as e:
            from ..logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "historical_data_fetch_internal",
                function="_fetch_historical_data",
                symbol=symbol,
                period=period,
                interval=interval,
                error_type="unexpected_error",
                original_error=type(e).__name__,
            )
            logging.error(f"Unexpected error fetching historical data for {symbol}: {e}")
            return pd.DataFrame()

    def get_current_price(self, symbol: str) -> float | None:
        """
        Get current market price for a symbol with real-time data priority.
        Uses just-in-time subscription for efficient resource usage.

        Args:
            symbol: Stock symbol
        Returns:
            float: Current price or None if unavailable
        """
        # Try real-time pricing first if available
        if self.real_time_pricing and self.real_time_pricing.is_connected():
            # Just-in-time subscription: subscribe only when we need pricing
            self.real_time_pricing.subscribe_for_trading(symbol)

            # Give a moment for real-time data to flow
            import time

            time.sleep(0.5)  # Brief wait for subscription to activate

            # Get real-time price
            price = self.real_time_pricing.get_current_price(symbol)
            if price is not None:
                logging.debug(f"Real-time price for {symbol}: ${price:.2f}")
                return price

        # Fallback to REST API
        return self.get_current_price_rest(symbol)

    def get_current_price_for_order(self, symbol: str) -> tuple[float | None, Callable[[], None]]:
        """
        Get current price specifically for order placement with optimized subscription management.

        This method:
        1. Subscribes to real-time data for the symbol
        2. Gets the most accurate price available
        3. Returns both price and cleanup function

        Args:
            symbol: Stock symbol
        Returns:
            tuple: (price, cleanup_function) where cleanup_function unsubscribes
        """
        from the_alchemiser.utils.price_fetching_utils import (
            create_cleanup_function,
            subscribe_for_real_time,
        )

        # Create cleanup function (type: Callable[[], None])
        cleanup: Callable[[], None] = create_cleanup_function(self.real_time_pricing, symbol)  # type: ignore[no-untyped-call]

        # Try real-time pricing with just-in-time subscription
        if subscribe_for_real_time(self.real_time_pricing, symbol):  # type: ignore[no-untyped-call]
            # Try to get real-time price
            if self.real_time_pricing:
                price = self.real_time_pricing.get_current_price(symbol)
                if price is not None:
                    logging.info(f"Using real-time price for {symbol} order: ${price:.2f}")
                    return price, cleanup
                else:
                    logging.debug(f"Real-time price not yet available for {symbol}, using REST API")

        # Fallback to REST API
        price = self.get_current_price_rest(symbol)
        logging.info(f"Using REST API price for {symbol} order: ${price:.2f}")
        return price, cleanup

    def get_current_price_rest(self, symbol: str) -> float | None:
        """
        Get current market price for a symbol using REST API.

        Args:
            symbol: Stock symbol
        Returns:
            float: Current price or None if unavailable
        """
        from the_alchemiser.utils.price_fetching_utils import (
            get_price_from_historical_fallback,
            get_price_from_quote_api,
        )

        try:
            # Try to get price from quote API
            price: float | None = get_price_from_quote_api(self.data_client, symbol)  # type: ignore[no-untyped-call]
            if price is not None:
                return price

            # Fallback to recent historical data
            fallback_price: float | None = get_price_from_historical_fallback(self, symbol)  # type: ignore[no-untyped-call]
            return fallback_price

        except MarketDataError as e:
            from ..logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "current_price_rest_fetch",
                function="get_current_price_rest",
                symbol=symbol,
                error_type=type(e).__name__,
            )
            logging.error(f"Market data error getting current price for {symbol}: {e}")
            return None
        except Exception as e:
            from ..logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "current_price_rest_fetch",
                function="get_current_price_rest",
                symbol=symbol,
                error_type="unexpected_error",
                original_error=type(e).__name__,
            )
            logging.error(f"Unexpected error getting current price for {symbol}: {e}")
            return None

    def get_latest_quote(self, symbol: str) -> tuple[float, float]:
        """Get the latest bid and ask quote for a symbol."""
        try:
            request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            latest_quote = self.data_client.get_stock_latest_quote(request)
            if latest_quote and symbol in latest_quote:
                quote = latest_quote[symbol]
                bid = float(getattr(quote, "bid_price", 0) or 0)
                ask = float(getattr(quote, "ask_price", 0) or 0)
                return bid, ask
        except MarketDataError as e:
            from ..logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "latest_quote_fetch",
                function="get_latest_quote",
                symbol=symbol,
                error_type=type(e).__name__,
            )
            logging.error(f"Market data error fetching latest quote for {symbol}: {e}")
        except Exception as e:
            from ..logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "latest_quote_fetch",
                function="get_latest_quote",
                symbol=symbol,
                error_type="unexpected_error",
                original_error=type(e).__name__,
            )
            logging.error(f"Unexpected error fetching latest quote for {symbol}: {e}")
        return 0.0, 0.0

    def get_historical_data(self, symbol: str, start: datetime, end: datetime, timeframe: TimeFrame | str | None = None) -> list[Any]:
        """
        Get historical data for a specific date range.

        Args:
            symbol: Stock symbol
            start: Start datetime
            end: End datetime
            timeframe: TimeFrame enum or string

        Returns:
            List of bar objects or empty list
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
                symbol_or_symbols=symbol, timeframe=cast(TimeFrame, timeframe), start=start, end=end
            )

            # Fetch data
            bars = self.data_client.get_stock_bars(request)

            # Extract bars for the symbol safely
            try:
                # Try direct symbol access first
                if hasattr(bars, symbol):
                    bar_data = getattr(bars, symbol)
                    return list(bar_data) if bar_data else []
                # Try data dictionary access as fallback
                elif hasattr(bars, "data"):
                    data_dict = getattr(bars, "data", {})
                    if hasattr(data_dict, "get"):
                        bar_data = data_dict.get(symbol, [])
                        return list(bar_data) if bar_data else []
                    elif symbol in data_dict:
                        bar_data = data_dict[symbol]
                        return list(bar_data) if bar_data else []
            except (AttributeError, KeyError, TypeError):
                pass

            return []

        except MarketDataError as e:
            from ..logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "historical_data_date_range_fetch",
                function="get_historical_data",
                symbol=symbol,
                start_date=str(start),
                end_date=str(end),
                timeframe=str(timeframe),
                error_type=type(e).__name__,
            )
            logging.error(
                f"Market data error fetching historical data for {symbol} from {start} to {end}: {e}"
            )
            return []
        except Exception as e:
            from ..logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "historical_data_date_range_fetch",
                function="get_historical_data",
                symbol=symbol,
                start_date=str(start),
                end_date=str(end),
                timeframe=str(timeframe),
                error_type="unexpected_error",
                original_error=type(e).__name__,
            )
            logging.error(
                f"Unexpected error fetching historical data for {symbol} from {start} to {end}: {e}"
            )
            return []

    def get_account_info(self) -> dict[str, Any] | None:
        """Get account information."""
        try:
            account = self.trading_client.get_account()
            # Convert account object to dict for consistency
            if hasattr(account, 'model_dump'):
                return account.model_dump()  # type: ignore[return-value,attr-defined]
            elif hasattr(account, '__dict__'):
                return account.__dict__  # type: ignore[return-value]
            else:
                # Fallback: return as Any and cast
                return dict(account) if account else None  # type: ignore[call-arg]
        except TradingClientError as e:
            from ..logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "account_info_fetch",
                function="get_account_info",
                error_type=type(e).__name__,
            )
            logging.error(f"Trading client error fetching account info: {e}")
            return None
        except Exception as e:
            from ..logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "account_info_fetch",
                function="get_account_info",
                error_type="unexpected_error",
                original_error=type(e).__name__,
            )
            logging.error(f"Unexpected error fetching account info: {e}")
            return None

    def get_positions(self) -> list[dict[str, Any]]:
        """Get all positions."""
        try:
            positions = self.trading_client.get_all_positions()
            # Convert positions to list of dicts for consistency
            if isinstance(positions, list):
                result: list[dict[str, Any]] = []
                for pos in positions:
                    if hasattr(pos, 'model_dump'):
                        result.append(pos.model_dump())  # type: ignore[arg-type]
                    elif hasattr(pos, '__dict__'):
                        result.append(pos.__dict__)  # type: ignore[arg-type]
                    else:
                        result.append(dict(pos))  # type: ignore[arg-type,call-arg]
                return result
            else:
                # Handle RawData case - return empty list if not a list
                return []
        except TradingClientError as e:
            from ..logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "positions_fetch",
                function="get_positions",
                error_type=type(e).__name__,
            )
            logging.error(f"Trading client error fetching positions: {e}")
            return []
        except Exception as e:
            from ..logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "positions_fetch",
                function="get_positions",
                error_type="unexpected_error",
                original_error=type(e).__name__,
            )
            logging.error(f"Unexpected error fetching positions: {e}")
            return []

    def clear_cache(self) -> None:
        """Clear the data cache."""
        self.cache.clear()
        logging.debug("Data cache cleared")

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return {
            "cache_size": len(self.cache),
            "cache_duration": self.cache_duration,
            "paper_trading": self.paper_trading,
        }

    def get_portfolio_history(
        self,
        intraday_reporting: str = "market_hours",
        pnl_reset: str = "per_day",
        timeframe: str = "1D"
    ) -> dict[str, Any]:
        """
        Get account portfolio history (closed P&L, equity curve).
        Returns: dict with keys: timestamp, equity, profit_loss, profit_loss_pct, base_value, etc.
        """
        url = f"{self.api_endpoint}/account/portfolio/history"
        params = {
            "intraday_reporting": intraday_reporting,
            "pnl_reset": pnl_reset,
            "timeframe": timeframe,
        }
        headers = {
            "accept": "application/json",
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.secret_key,
        }
        try:
            import requests

            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]
        except MarketDataError as e:
            from ..logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "portfolio_history_fetch",
                function="get_portfolio_history",
                intraday_reporting=intraday_reporting,
                pnl_reset=pnl_reset,
                timeframe=timeframe,
                error_type=type(e).__name__,
            )
            logging.error(f"Market data error fetching portfolio history: {e}")
            return {}
        except Exception as e:
            from ..logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "portfolio_history_fetch",
                function="get_portfolio_history",
                intraday_reporting=intraday_reporting,
                pnl_reset=pnl_reset,
                timeframe=timeframe,
                error_type="unexpected_error",
                original_error=type(e).__name__,
            )
            logging.error(f"Unexpected error fetching portfolio history: {e}")
            return {}

    def get_open_positions(self) -> list[dict[str, Any]]:
        """
        Get all open positions (for open P&L, market value, etc).
        Returns: list of position dicts.
        """
        url = f"{self.api_endpoint}/positions"
        headers = {
            "accept": "application/json",
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.secret_key,
        }
        try:
            import requests

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]
        except MarketDataError as e:
            from ..logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "open_positions_fetch",
                function="get_open_positions",
                error_type=type(e).__name__,
            )
            logging.error(f"Market data error fetching open positions: {e}")
            return []
        except Exception as e:
            from ..logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "open_positions_fetch",
                function="get_open_positions",
                error_type="unexpected_error",
                original_error=type(e).__name__,
            )
            logging.error(f"Unexpected error fetching open positions: {e}")
            return []

    def get_account_activities(
        self,
        activity_type: str = "FILL",
        direction: str = "desc",
        page_size: int = 50
    ) -> list[dict[str, Any]]:
        """
        Get account activities including filled orders to track closed position P&L.

        Args:
            activity_type: Type of activity ('FILL', 'TRANS', 'DIV', etc.)
            direction: Sort direction ('desc' for most recent first)
            page_size: Number of results to return (max 100)

        Returns:
            List of activity dicts including recent fills/trades
        """
        url = f"{self.api_endpoint}/account/activities/{activity_type}"
        headers = {
            "accept": "application/json",
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.secret_key,
        }
        params = {"direction": direction, "page_size": min(page_size, 100)}  # Alpaca max is 100
        try:
            import requests

            response = requests.get(url, headers=headers, params=params, timeout=10)  # type: ignore[arg-type]
            response.raise_for_status()
            return response.json()  # type: ignore[no-any-return]
        except MarketDataError as e:
            from ..logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "account_activities_fetch",
                function="get_account_activities",
                activity_type=activity_type,
                direction=direction,
                page_size=page_size,
                error_type=type(e).__name__,
            )
            logging.error(f"Market data error fetching account activities: {e}")
            return []
        except Exception as e:
            from ..logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "account_activities_fetch",
                function="get_account_activities",
                activity_type=activity_type,
                direction=direction,
                page_size=page_size,
                error_type="unexpected_error",
                original_error=type(e).__name__,
            )
            logging.error(f"Unexpected error fetching account activities: {e}")
            return []

    def get_recent_closed_positions_pnl(self, days_back: int = 7) -> list[dict[str, Any]]:
        """
        Calculate P&L from recent closed positions by analyzing filled orders.

        Args:
            days_back: Number of days to look back for closed positions

        Returns:
            List of dicts with closed position P&L information
        """
        try:
            from collections import defaultdict
            from datetime import datetime, timedelta

            # Get recent fill activities
            activities = self.get_account_activities(activity_type="FILL", page_size=100)

            if not activities:
                return []

            # Filter activities to last N days
            cutoff_date = datetime.now() - timedelta(days=days_back)
            recent_activities = []

            for activity in activities:
                try:
                    activity_time_str = activity.get("transaction_time", "")
                    # Handle timezone-aware datetime parsing
                    if activity_time_str.endswith("Z"):
                        activity_time_str = activity_time_str[:-1] + "+00:00"

                    activity_date = datetime.fromisoformat(activity_time_str)

                    # Make cutoff_date timezone-aware if activity_date is timezone-aware
                    if activity_date.tzinfo is not None and cutoff_date.tzinfo is None:

                        cutoff_date = cutoff_date.replace(tzinfo=UTC)
                    elif activity_date.tzinfo is None and cutoff_date.tzinfo is not None:
                        cutoff_date = cutoff_date.replace(tzinfo=None)

                    if activity_date >= cutoff_date:
                        recent_activities.append(activity)
                except (ValueError, AttributeError) as e:
                    logging.debug(f"Error parsing activity date {activity_time_str}: {e}")
                    continue

            # Group activities by symbol to calculate position P&L
            symbol_trades = defaultdict(list)
            for activity in recent_activities:
                symbol = activity.get("symbol")
                if symbol:
                    symbol_trades[symbol].append(activity)

            closed_positions = []

            for symbol, trades in symbol_trades.items():
                # Sort trades by date
                trades.sort(key=lambda x: x.get("transaction_time", ""))

                position_qty: float = 0.0
                total_cost: float = 0.0
                realized_pnl: float = 0.0
                total_sold_cost_basis: float = (
                    0.0  # Track cost basis of sold shares for % calculation
                )

                for trade in trades:
                    side = trade.get("side", "").upper()
                    qty = float(trade.get("qty", 0))
                    price = float(trade.get("price", 0))

                    if side == "BUY":
                        position_qty += qty
                        total_cost += qty * price
                    elif side == "SELL" and position_qty > 0:
                        # Calculate realized P&L for the sale
                        avg_cost = total_cost / position_qty if position_qty > 0 else 0
                        sale_pnl = qty * (price - avg_cost)
                        realized_pnl += sale_pnl

                        # Track the cost basis of shares sold for percentage calculation
                        total_sold_cost_basis += qty * avg_cost

                        # Update position
                        position_qty -= qty
                        if position_qty <= 0:
                            # Position fully closed
                            total_cost = 0
                            position_qty = 0
                        else:
                            # Partial close - adjust cost basis proportionally
                            total_cost = position_qty * avg_cost

                # If we have realized P&L from this symbol, record it
                if abs(realized_pnl) > 0.01:  # Only include if P&L > 1 cent
                    latest_trade = trades[-1]
                    # Calculate percentage based on the total cost basis of sold shares
                    realized_pnl_pct = (
                        (realized_pnl / total_sold_cost_basis) * 100
                        if total_sold_cost_basis > 0
                        else 0
                    )
                    closed_positions.append(
                        {
                            "symbol": symbol,
                            "realized_pnl": realized_pnl,
                            "realized_pnl_pct": realized_pnl_pct,
                            "last_trade_date": latest_trade.get("transaction_time"),
                            "trade_count": len(trades),
                            "final_position_qty": position_qty,
                        }
                    )

            # Sort by absolute P&L (biggest movers first)
            closed_positions.sort(key=lambda x: abs(x["realized_pnl"]), reverse=True)

            return closed_positions

        except DataProviderError as e:
            from ..logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "closed_positions_pnl_calculation",
                function="get_recent_closed_positions_pnl",
                days_back=days_back,
                error_type=type(e).__name__,
            )
            logging.error(f"Data provider error calculating closed positions P&L: {e}")
            return []
        except Exception as e:
            from ..logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "closed_positions_pnl_calculation",
                function="get_recent_closed_positions_pnl",
                days_back=days_back,
                error_type="unexpected_error",
                original_error=type(e).__name__,
            )
            logging.error(f"Unexpected error calculating closed positions P&L: {e}")
            return []
