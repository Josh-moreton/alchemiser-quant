"""Business Unit: strategy & signal generation | Status: current.

Market data client adapter for strategy context.

Handles market data REST API calls to Alpaca for strategy signal generation.
Focused on data retrieval without trading operations.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any, cast

import pandas as pd
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from the_alchemiser.strategy.domain.exceptions import MarketDataError
from the_alchemiser.services.repository.alpaca_manager import AlpacaManager


class MarketDataClient:
    """Client adapter for market data operations via Alpaca API."""

    def __init__(self, api_key: str, secret_key: str) -> None:
        """Initialize market data client.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key

        """
        self.api_key = api_key
        self.secret_key = secret_key
        self._alpaca_manager = AlpacaManager(api_key, secret_key)

    def get_historical_bars(
        self, symbol: str, period: str = "1y", interval: str = "1d"
    ) -> pd.DataFrame:
        """Get historical bar data for a symbol.

        Args:
            symbol: Stock symbol
            period: Time period (1y, 6mo, 3mo, 1mo, 200d)
            interval: Data interval (1d, 1h, 1m)

        Returns:
            DataFrame with historical bar data

        Raises:
            MarketDataError: If data retrieval fails

        """
        try:
            # Calculate date range based on period
            end_date = datetime.now(UTC).date()

            if period.endswith("d"):
                days = int(period[:-1])
                start_date = (datetime.now(UTC) - timedelta(days=days)).date()
            elif period == "1y":
                start_date = (datetime.now(UTC) - timedelta(days=365)).date()
            elif period == "6mo":
                start_date = (datetime.now(UTC) - timedelta(days=180)).date()
            elif period == "3mo":
                start_date = (datetime.now(UTC) - timedelta(days=90)).date()
            elif period == "1mo":
                start_date = (datetime.now(UTC) - timedelta(days=30)).date()
            else:
                start_date = (datetime.now(UTC) - timedelta(days=365)).date()

            # Map interval to Alpaca TimeFrame
            timeframe_map = {
                "1m": TimeFrame.Minute,
                "5m": TimeFrame(5, "minute"),
                "15m": TimeFrame(15, "minute"),
                "30m": TimeFrame(30, "minute"),
                "1h": TimeFrame.Hour,
                "1d": TimeFrame.Day,
                "1Day": TimeFrame.Day,
            }

            timeframe = timeframe_map.get(interval, TimeFrame.Day)

            # Create the request
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=timeframe,
                start=start_date,
                end=end_date,
            )

            # Get data from Alpaca
            data_client = self._alpaca_manager.get_data_client()
            bars = data_client.get_stock_bars(request)

            # Convert to DataFrame
            if hasattr(bars, "df"):
                df = bars.df
            else:
                # Fallback for different Alpaca SDK versions
                df = pd.DataFrame(
                    [
                        {
                            "timestamp": bar.timestamp,
                            "open": bar.open,
                            "high": bar.high,
                            "low": bar.low,
                            "close": bar.close,
                            "volume": bar.volume,
                        }
                        for bar in bars[symbol]
                    ]
                )
                df.set_index("timestamp", inplace=True)

            return df

        except Exception as e:
            error_msg = f"Failed to get historical bars for {symbol}: {e}"
            logging.error(error_msg)
            raise MarketDataError(error_msg) from e

    def get_current_price(self, symbol: str) -> float:
        """Get current price for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Current price as float

        Raises:
            MarketDataError: If price retrieval fails

        """
        try:
            data_client = self._alpaca_manager.get_data_client()
            latest_trade = data_client.get_stock_latest_trade(symbol)

            if latest_trade and symbol in latest_trade:
                return float(latest_trade[symbol].price)

            # Fallback to latest quote
            latest_quote = data_client.get_stock_latest_quote(symbol)
            if latest_quote and symbol in latest_quote:
                quote = latest_quote[symbol]
                return float((quote.bid_price + quote.ask_price) / 2)

            raise MarketDataError(f"No price data available for {symbol}")

        except Exception as e:
            error_msg = f"Failed to get current price for {symbol}: {e}"
            logging.error(error_msg)
            raise MarketDataError(error_msg) from e

    def get_current_prices(self, symbols: list[str]) -> dict[str, float]:
        """Get current prices for multiple symbols.

        Args:
            symbols: List of stock symbols

        Returns:
            Dictionary mapping symbols to current prices

        """
        prices = {}
        for symbol in symbols:
            try:
                prices[symbol] = self.get_current_price(symbol)
            except MarketDataError:
                logging.warning(f"Failed to get price for {symbol}, setting to 0.0")
                prices[symbol] = 0.0

        return prices

    def get_latest_quote(self, symbol: str) -> dict[str, Any]:
        """Get latest quote for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Dictionary with quote data

        Raises:
            MarketDataError: If quote retrieval fails

        """
        try:
            data_client = self._alpaca_manager.get_data_client()
            latest_quote = data_client.get_stock_latest_quote(symbol)

            if latest_quote and symbol in latest_quote:
                quote = latest_quote[symbol]
                return {
                    "symbol": symbol,
                    "bid_price": float(quote.bid_price),
                    "ask_price": float(quote.ask_price),
                    "bid_size": int(quote.bid_size),
                    "ask_size": int(quote.ask_size),
                    "timestamp": quote.timestamp,
                }

            raise MarketDataError(f"No quote data available for {symbol}")

        except Exception as e:
            error_msg = f"Failed to get latest quote for {symbol}: {e}"
            logging.error(error_msg)
            raise MarketDataError(error_msg) from e

    def get_market_status(self) -> dict[str, Any]:
        """Get current market status.

        Returns:
            Dictionary with market status information

        """
        try:
            trading_client = self._alpaca_manager.get_trading_client()
            clock = trading_client.get_clock()

            return {
                "is_open": clock.is_open,
                "next_open": clock.next_open,
                "next_close": clock.next_close,
                "timestamp": clock.timestamp,
            }

        except Exception as e:
            logging.error(f"Failed to get market status: {e}")
            return {
                "is_open": False,
                "next_open": None,
                "next_close": None,
                "timestamp": datetime.now(UTC),
            }

    def validate_symbol(self, symbol: str) -> bool:
        """Validate if a symbol exists and is tradeable.

        Args:
            symbol: Stock symbol to validate

        Returns:
            True if symbol is valid and tradeable

        """
        try:
            # Try to get latest quote as a validation method
            self.get_latest_quote(symbol)
            return True
        except MarketDataError:
            return False

    def get_historical_data_for_date_range(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """Get historical data for a specific date range.

        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date
            interval: Data interval

        Returns:
            DataFrame with historical data

        """
        try:
            timeframe_map = {
                "1m": TimeFrame.Minute,
                "5m": TimeFrame(5, "minute"),
                "15m": TimeFrame(15, "minute"),
                "30m": TimeFrame(30, "minute"),
                "1h": TimeFrame.Hour,
                "1d": TimeFrame.Day,
                "1Day": TimeFrame.Day,
            }

            timeframe = timeframe_map.get(interval, TimeFrame.Day)

            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=timeframe,
                start=start_date.date(),
                end=end_date.date(),
            )

            data_client = self._alpaca_manager.get_data_client()
            bars = data_client.get_stock_bars(request)

            if hasattr(bars, "df"):
                return bars.df
            else:
                # Fallback conversion
                df = pd.DataFrame(
                    [
                        {
                            "timestamp": bar.timestamp,
                            "open": bar.open,
                            "high": bar.high,
                            "low": bar.low,
                            "close": bar.close,
                            "volume": bar.volume,
                        }
                        for bar in bars[symbol]
                    ]
                )
                df.set_index("timestamp", inplace=True)
                return df

        except Exception as e:
            error_msg = (
                f"Failed to get historical data for {symbol} from {start_date} to {end_date}: {e}"
            )
            logging.error(error_msg)
            raise MarketDataError(error_msg) from e
