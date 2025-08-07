#!/usr/bin/env python3
"""
Unified Data Provider Facade (Refactored)

This is the new service-based implementation that maintains the same interface
as the original monolithic UnifiedDataProvider while delegating to specialized services.
"""

import logging
import time
from collections.abc import Callable
from datetime import datetime
from typing import Any

import pandas as pd
import requests
from alpaca.data.timeframe import TimeFrame

from the_alchemiser.core.config import Settings
from the_alchemiser.core.exceptions import (
    ConfigurationError,
    MarketDataError,
)
from the_alchemiser.core.services import (
    ConfigService,
    MarketDataClient,
    SecretsService,
    StreamingService,
    TradingClientService,
)

# TODO: Phase 11 - Types available for future migration to structured data types
# from the_alchemiser.core.types import DataProviderResult, MarketDataPoint, PriceData


class UnifiedDataProvider:
    """
    Unified data provider facade that composes specialized services.

    Maintains the same interface as the original monolithic implementation
    while delegating to focused, testable services.
    """

    def __init__(
        self,
        paper_trading: bool = True,
        cache_duration: int | None = None,
        config: Settings | None = None,
        enable_real_time: bool = True,
    ) -> None:
        """
        Initialize UnifiedDataProvider with service composition.

        Args:
            paper_trading: Whether to use paper trading keys (default: True for safety)
            cache_duration: Cache duration in seconds (default from config)
            config: Configuration object. If None, will load from global config.
            enable_real_time: Whether to enable real-time WebSocket pricing (default: True)
        """
        self.paper_trading = paper_trading

        # Initialize services
        self._config_service = ConfigService(config)
        self._secrets_service = SecretsService()

        # Get credentials
        try:
            self.api_key, self.secret_key = self._secrets_service.get_alpaca_credentials(
                paper_trading
            )
        except ConfigurationError:
            raise  # Re-raise configuration errors

        # Initialize data and trading services
        self._market_data_client = MarketDataClient(self.api_key, self.secret_key)
        self._trading_client_service = TradingClientService(
            self.api_key, self.secret_key, paper_trading
        )

        # Initialize streaming service
        self._streaming_service = StreamingService(self.api_key, self.secret_key, paper_trading)
        if enable_real_time:
            try:
                self._streaming_service.set_fallback_provider(self.get_current_price_rest)
                self._streaming_service.start()
            except Exception as e:
                logging.warning(f"Failed to initialize real-time pricing: {e}")

        # Set up caching
        if cache_duration is None:
            cache_duration = self._config_service.cache_duration
        self.cache_duration: int = cache_duration
        self.cache: dict[tuple[str, str, str], tuple[float, pd.DataFrame]] = {}

        # Set endpoints (for compatibility)
        self.api_endpoint = self._config_service.get_endpoint(paper_trading)

        # Legacy properties for compatibility
        self.real_time_pricing = self._streaming_service._real_time_pricing

        logging.debug(
            f"Initialized UnifiedDataProvider with {'paper' if paper_trading else 'live'} trading keys"
        )

    @property
    def config(self) -> Settings:
        """Get configuration."""
        return self._config_service.config

    @property
    def trading_client(self) -> Any:
        """Get the trading client for compatibility."""
        return self._trading_client_service.client

    def get_data(
        self, symbol: str, period: str = "1y", interval: str = "1d"
    ) -> pd.DataFrame | None:
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
            df = self._market_data_client.get_historical_bars(symbol, period, interval)

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
                function="get_data",
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
                "historical_data_error",
                function="get_data",
                symbol=symbol,
                period=period,
                interval=interval,
                error_type=type(e).__name__,
            )
            logging.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()

    def get_current_price(self, symbol: str) -> float | None:
        """
        Get current market price for a symbol with real-time data priority.

        Args:
            symbol: Stock symbol
        Returns:
            float: Current price or None if unavailable
        """
        return self._streaming_service.get_current_price(symbol)

    def get_current_price_for_order(self, symbol: str) -> tuple[float | None, Callable[[], None]]:
        """
        Get current price specifically for order placement with optimized subscription management.

        Args:
            symbol: Stock symbol
        Returns:
            tuple: (price, cleanup_function)
        """
        return self._streaming_service.get_current_price_for_order(symbol)

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
            price = get_price_from_quote_api(self._market_data_client._client, symbol)
            if price is not None:
                return price

            # Fallback to recent historical data
            fallback_price = get_price_from_historical_fallback(self, symbol)
            return fallback_price

        except Exception as e:
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
            logging.error(f"Error getting current price for {symbol}: {e}")
            return None

    def get_latest_quote(self, symbol: str) -> tuple[float, float]:
        """Get the latest bid and ask quote for a symbol."""
        try:
            return self._market_data_client.get_latest_quote(symbol)
        except Exception as e:
            logging.error(f"Error fetching latest quote for {symbol}: {e}")
            return 0.0, 0.0

    def get_historical_data(
        self, symbol: str, start: datetime, end: datetime, timeframe: TimeFrame | str | None = None
    ) -> list[Any]:
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
            return self._market_data_client.get_historical_bars_date_range(
                symbol, start, end, timeframe
            )
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
            logging.error(f"Error fetching historical data for {symbol}: {e}")
            return []
        except Exception as e:
            from ..logging.logging_utils import get_logger, log_error_with_context

            logger = get_logger(__name__)
            log_error_with_context(
                logger,
                e,
                "historical_data_error",
                function="get_historical_data",
                symbol=symbol,
                start_date=str(start),
                end_date=str(end),
                timeframe=str(timeframe),
                error_type=type(e).__name__,
            )
            logging.error(f"Error fetching historical data for {symbol}: {e}")
            return []

    def get_account_info(self) -> dict[str, Any] | None:
        """Get account information."""
        return self._trading_client_service.get_account_info()

    def get_positions(self) -> list[dict[str, Any]]:
        """Get all positions."""
        return self._trading_client_service.get_all_positions()

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

    # Legacy methods for backward compatibility
    def get_portfolio_history(
        self,
        intraday_reporting: str = "market_hours",
        pnl_reset: str = "per_day",
        timeframe: str = "1D",
    ) -> dict[str, Any]:
        """Get account portfolio history (maintained for compatibility)."""
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
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Error fetching portfolio history: {e}")
            return {}

    def get_open_positions(self) -> list[dict[str, Any]]:
        """Get all open positions (maintained for compatibility)."""
        url = f"{self.api_endpoint}/positions"
        headers = {
            "accept": "application/json",
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.secret_key,
        }
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Error fetching open positions: {e}")
            return []

    def get_account_activities(
        self, activity_type: str = "FILL", direction: str = "desc", page_size: int = 50
    ) -> list[dict[str, Any]]:
        """Get account activities (maintained for compatibility)."""
        url = f"{self.api_endpoint}/account/activities/{activity_type}"
        headers = {
            "accept": "application/json",
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.secret_key,
        }
        params = {"direction": direction, "page_size": min(page_size, 100)}
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Error fetching account activities: {e}")
            return []

    def get_recent_closed_positions_pnl(self, days_back: int = 7) -> list[dict[str, Any]]:
        """Calculate P&L from recent closed positions (maintained for compatibility)."""
        try:
            from collections import defaultdict
            from datetime import UTC, timedelta

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
                    if activity_time_str.endswith("Z"):
                        activity_time_str = activity_time_str[:-1] + "+00:00"

                    activity_date = datetime.fromisoformat(activity_time_str)

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
                trades.sort(key=lambda x: x.get("transaction_time", ""))

                position_qty = 0.0
                total_cost = 0.0
                realized_pnl = 0.0
                total_sold_cost_basis = 0.0

                for trade in trades:
                    side = trade.get("side", "").upper()
                    qty = float(trade.get("qty", 0))
                    price = float(trade.get("price", 0))

                    if side == "BUY":
                        position_qty += qty
                        total_cost += qty * price
                    elif side == "SELL" and position_qty > 0:
                        avg_cost = total_cost / position_qty if position_qty > 0 else 0
                        sale_pnl = qty * (price - avg_cost)
                        realized_pnl += sale_pnl
                        total_sold_cost_basis += qty * avg_cost

                        position_qty -= qty
                        if position_qty <= 0:
                            total_cost = 0
                            position_qty = 0
                        else:
                            total_cost = position_qty * avg_cost

                if abs(realized_pnl) > 0.01:
                    latest_trade = trades[-1]
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

            closed_positions.sort(key=lambda x: abs(x["realized_pnl"]), reverse=True)
            return closed_positions

        except Exception as e:
            logging.error(f"Error calculating closed positions P&L: {e}")
            return []
