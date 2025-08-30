"""Business Unit: strategy & signal generation | Status: current.

Alpaca market data adapter for strategy context.

Handles market data retrieval, quotes, and historical data via Alpaca API.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

from the_alchemiser.domain.interfaces import MarketDataRepository
from the_alchemiser.shared_kernel.infrastructure.base_alpaca_adapter import BaseAlpacaAdapter

logger = logging.getLogger(__name__)


class AlpacaMarketDataAdapter(BaseAlpacaAdapter, MarketDataRepository):
    """Alpaca adapter for market data operations."""

    def get_current_price(self, symbol: str) -> float | None:
        """Get current price for a symbol.

        Args:
            symbol: Symbol to get price for

        Returns:
            Current price or None if unavailable

        """
        try:
            data_client = self.get_data_client()

            # Try to get latest trade first
            try:
                latest_trade = data_client.get_stock_latest_trade(symbol)
                if latest_trade and symbol in latest_trade:
                    price = float(latest_trade[symbol].price)
                    self.logger.debug(f"Got latest trade price for {symbol}: ${price}")
                    return price
            except Exception:
                pass

            # Fallback to latest quote
            latest_quote = data_client.get_stock_latest_quote(symbol)
            if latest_quote and symbol in latest_quote:
                quote = latest_quote[symbol]
                mid_price = (float(quote.bid_price) + float(quote.ask_price)) / 2
                self.logger.debug(f"Got mid price for {symbol}: ${mid_price}")
                return mid_price

            self.logger.warning(f"No price data available for {symbol}")
            return None

        except Exception as e:
            self.logger.error(f"Failed to get current price for {symbol}: {e}")
            return None

    def get_current_prices(self, symbols: list[str]) -> dict[str, float]:
        """Get current prices for multiple symbols.

        Args:
            symbols: List of symbols to get prices for

        Returns:
            Dictionary mapping symbols to prices

        """
        prices = {}

        # Batch request for quotes
        try:
            data_client = self.get_data_client()
            latest_quotes = data_client.get_stock_latest_quote(symbols)

            for symbol in symbols:
                try:
                    if symbol in latest_quotes:
                        quote = latest_quotes[symbol]
                        mid_price = (float(quote.bid_price) + float(quote.ask_price)) / 2
                        prices[symbol] = mid_price
                    else:
                        prices[symbol] = 0.0
                except Exception as e:
                    self.logger.warning(f"Failed to get price for {symbol}: {e}")
                    prices[symbol] = 0.0

            self.logger.debug(f"Retrieved prices for {len(symbols)} symbols")

        except Exception as e:
            self.logger.error(f"Failed to get batch prices: {e}")
            # Fallback to individual requests
            for symbol in symbols:
                price = self.get_current_price(symbol)
                prices[symbol] = price if price is not None else 0.0

        return prices

    def get_latest_quote(self, symbol: str) -> tuple[float, float] | None:
        """Get latest quote (bid, ask) for a symbol.

        Args:
            symbol: Symbol to get quote for

        Returns:
            Tuple of (bid_price, ask_price) or None if unavailable

        """
        try:
            data_client = self.get_data_client()
            latest_quote = data_client.get_stock_latest_quote(symbol)

            if latest_quote and symbol in latest_quote:
                quote = latest_quote[symbol]
                bid_price = float(quote.bid_price)
                ask_price = float(quote.ask_price)
                self.logger.debug(f"Got quote for {symbol}: bid=${bid_price}, ask=${ask_price}")
                return (bid_price, ask_price)

            return None

        except Exception as e:
            self.logger.error(f"Failed to get quote for {symbol}: {e}")
            return None

    def get_latest_quote_raw(self, symbol: str) -> Any | None:
        """Get raw latest quote object for a symbol.

        Args:
            symbol: Symbol to get quote for

        Returns:
            Raw quote object or None if unavailable

        """
        try:
            data_client = self.get_data_client()
            latest_quote = data_client.get_stock_latest_quote(symbol)

            if latest_quote and symbol in latest_quote:
                return latest_quote[symbol]

            return None

        except Exception as e:
            self.logger.error(f"Failed to get raw quote for {symbol}: {e}")
            return None

    def get_latest_quote_detailed(self, symbol: str) -> dict[str, Any] | None:
        """Get detailed latest quote information.

        Args:
            symbol: Symbol to get quote for

        Returns:
            Dictionary with detailed quote information

        """
        try:
            quote = self.get_latest_quote_raw(symbol)
            if not quote:
                return None

            return {
                "symbol": symbol,
                "bid_price": float(quote.bid_price),
                "ask_price": float(quote.ask_price),
                "bid_size": int(quote.bid_size),
                "ask_size": int(quote.ask_size),
                "timestamp": quote.timestamp.isoformat() if quote.timestamp else None,
                "mid_price": (float(quote.bid_price) + float(quote.ask_price)) / 2,
                "spread": float(quote.ask_price) - float(quote.bid_price),
            }

        except Exception as e:
            self.logger.error(f"Failed to get detailed quote for {symbol}: {e}")
            return None

    def get_historical_bars(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
        timeframe: str = "1Day",
    ) -> Any:
        """Get historical bar data.

        Args:
            symbol: Symbol to get bars for
            start: Start datetime
            end: End datetime
            timeframe: Timeframe string

        Returns:
            Historical bars data

        """
        try:
            data_client = self.get_data_client()

            # Convert timeframe string to Alpaca TimeFrame
            timeframe_map = {
                "1Min": TimeFrame(1, TimeFrameUnit.Minute),
                "5Min": TimeFrame(5, TimeFrameUnit.Minute),
                "15Min": TimeFrame(15, TimeFrameUnit.Minute),
                "30Min": TimeFrame(30, TimeFrameUnit.Minute),
                "1Hour": TimeFrame(1, TimeFrameUnit.Hour),
                "1Day": TimeFrame(1, TimeFrameUnit.Day),
                "1Week": TimeFrame(1, TimeFrameUnit.Week),
                "1Month": TimeFrame(1, TimeFrameUnit.Month),
            }

            tf = timeframe_map.get(timeframe, TimeFrame(1, TimeFrameUnit.Day))

            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=tf,
                start=start,
                end=end,
            )

            bars = data_client.get_stock_bars(request)
            self.logger.debug(f"Retrieved historical bars for {symbol} from {start} to {end}")
            return bars

        except Exception as e:
            self.logger.error(f"Failed to get historical bars for {symbol}: {e}")
            raise

    def get_asset_info(self, symbol: str) -> dict[str, Any] | None:
        """Get asset information for a symbol.

        Args:
            symbol: Symbol to get asset info for

        Returns:
            Dictionary with asset information or None if unavailable

        """
        try:
            client = self.get_trading_client()
            asset = client.get_asset(symbol)

            return {
                "symbol": asset.symbol,
                "name": asset.name,
                "asset_class": asset.asset_class.value if asset.asset_class else None,
                "exchange": asset.exchange.value if asset.exchange else None,
                "status": asset.status.value if asset.status else None,
                "tradable": asset.tradable,
                "marginable": asset.marginable,
                "shortable": asset.shortable,
                "easy_to_borrow": asset.easy_to_borrow,
                "fractionable": asset.fractionable,
            }

        except Exception as e:
            self.logger.error(f"Failed to get asset info for {symbol}: {e}")
            return None

    def validate_symbol(self, symbol: str) -> bool:
        """Validate if a symbol exists and is tradeable.

        Args:
            symbol: Symbol to validate

        Returns:
            True if symbol is valid and tradeable

        """
        try:
            asset_info = self.get_asset_info(symbol)
            if asset_info:
                return asset_info.get("tradable", False)
            return False
        except Exception:
            return False

    def get_market_hours(self) -> dict[str, Any]:
        """Get market hours information.

        Returns:
            Dictionary with market hours information

        """
        try:
            client = self.get_trading_client()
            clock = client.get_clock()

            return {
                "is_open": clock.is_open,
                "next_open": clock.next_open.isoformat() if clock.next_open else None,
                "next_close": clock.next_close.isoformat() if clock.next_close else None,
                "timestamp": clock.timestamp.isoformat() if clock.timestamp else None,
            }

        except Exception as e:
            self.logger.error(f"Failed to get market hours: {e}")
            return {
                "is_open": False,
                "next_open": None,
                "next_close": None,
                "timestamp": datetime.now(UTC).isoformat(),
            }

    def get_market_status(self) -> dict[str, Any]:
        """Get comprehensive market status.

        Returns:
            Dictionary with market status information

        """
        try:
            hours = self.get_market_hours()

            status = {
                "market_open": hours["is_open"],
                "next_open": hours["next_open"],
                "next_close": hours["next_close"],
                "timestamp": hours["timestamp"],
                "session": "regular" if hours["is_open"] else "closed",
            }

            # Add extended hours information if available
            now = datetime.now(UTC)
            if hours["next_open"] and hours["next_close"]:
                next_open = datetime.fromisoformat(hours["next_open"].replace("Z", "+00:00"))
                next_close = datetime.fromisoformat(hours["next_close"].replace("Z", "+00:00"))

                # Check if we're in pre-market or after-hours
                if not hours["is_open"]:
                    if now.hour >= 4 and now.hour < 9:  # Pre-market hours (EST)
                        status["session"] = "pre_market"
                    elif now.hour >= 16 and now.hour < 20:  # After-hours (EST)
                        status["session"] = "after_hours"

            return status

        except Exception as e:
            self.logger.error(f"Failed to get market status: {e}")
            return {
                "market_open": False,
                "session": "unknown",
                "timestamp": datetime.now(UTC).isoformat(),
            }

    def get_quote_with_spread_analysis(self, symbol: str) -> dict[str, Any] | None:
        """Get quote with spread analysis.

        Args:
            symbol: Symbol to analyze

        Returns:
            Dictionary with quote and spread analysis

        """
        try:
            quote_detail = self.get_latest_quote_detailed(symbol)
            if not quote_detail:
                return None

            bid_price = quote_detail["bid_price"]
            ask_price = quote_detail["ask_price"]
            mid_price = quote_detail["mid_price"]
            spread = quote_detail["spread"]

            # Calculate spread metrics
            spread_percentage = (spread / mid_price * 100) if mid_price > 0 else 0

            # Classify spread tightness
            if spread_percentage < 0.1:
                spread_category = "tight"
            elif spread_percentage < 0.5:
                spread_category = "normal"
            elif spread_percentage < 1.0:
                spread_category = "wide"
            else:
                spread_category = "very_wide"

            result = quote_detail.copy()
            result.update(
                {
                    "spread_percentage": spread_percentage,
                    "spread_category": spread_category,
                    "liquidity_quality": "good" if spread_percentage < 0.2 else "poor",
                }
            )

            return result

        except Exception as e:
            self.logger.error(f"Failed to get spread analysis for {symbol}: {e}")
            return None
