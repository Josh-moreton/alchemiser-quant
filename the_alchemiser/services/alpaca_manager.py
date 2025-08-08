"""
Centralized Alpaca client management - Phase 1 of incremental improvements.

This module consolidates scattered Alpaca client usage into a single, well-managed class.
It provides a transitional approach that:
1. Reduces scattered imports
2. Adds consistent error handling
3. Maintains backward compatibility
4. Sets up for future improvements
"""

import logging
from decimal import Decimal
from typing import Any

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import LimitOrderRequest, MarketOrderRequest

logger = logging.getLogger(__name__)


class AlpacaManager:
    """
    Centralized Alpaca client management.

    This class consolidates all Alpaca API interactions into a single, well-managed interface.
    It provides consistent error handling, logging, and sets up for future architectural
    improvements.
    """

    def __init__(
        self, api_key: str, secret_key: str, paper: bool = True, base_url: str | None = None
    ):
        """
        Initialize Alpaca clients.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            paper: Whether to use paper trading (default: True for safety)
            base_url: Optional custom base URL
        """
        self._api_key = api_key
        self._secret_key = secret_key
        self._paper = paper
        self._base_url = base_url

        # Initialize clients
        try:
            client_kwargs = {}
            if base_url:
                client_kwargs["base_url"] = base_url

            self._trading_client = TradingClient(
                api_key=api_key, secret_key=secret_key, paper=paper, **client_kwargs
            )

            self._data_client = StockHistoricalDataClient(api_key=api_key, secret_key=secret_key)

            logger.info(f"AlpacaManager initialized - Paper: {paper}")

        except Exception as e:
            logger.error(f"Failed to initialize Alpaca clients: {e}")
            raise

    @property
    def trading_client(self) -> TradingClient:
        """Get the trading client for backward compatibility."""
        return self._trading_client

    @property
    def data_client(self) -> StockHistoricalDataClient:
        """Get the data client for backward compatibility."""
        return self._data_client

    @property
    def is_paper_trading(self) -> bool:
        """Check if using paper trading."""
        return self._paper

    # Trading Operations
    def get_account(self) -> Any:
        """Get account information with error handling."""
        try:
            account = self._trading_client.get_account()
            logger.debug("Successfully retrieved account information")
            return account
        except Exception as e:
            logger.error(f"Failed to get account information: {e}")
            raise

    def get_positions(self) -> list[Any]:
        """Get all positions with error handling."""
        try:
            positions = self._trading_client.get_all_positions()
            logger.debug(f"Successfully retrieved {len(positions)} positions")
            return positions
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            raise

    def get_position(self, symbol: str) -> Any | None:
        """Get position for a specific symbol."""
        try:
            position = self._trading_client.get_open_position(symbol)
            logger.debug(f"Successfully retrieved position for {symbol}")
            return position
        except Exception as e:
            if "position does not exist" in str(e).lower():
                logger.debug(f"No position found for {symbol}")
                return None
            logger.error(f"Failed to get position for {symbol}: {e}")
            raise

    def place_order(self, order_request: Any) -> Any:
        """Place an order with error handling."""
        try:
            order = self._trading_client.submit_order(order_request)
            logger.info(f"Successfully placed order: {order.id} for {order.symbol}")
            return order
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            raise

    def place_market_order(
        self, symbol: str, side: str, quantity: float, time_in_force: str = "day"
    ) -> Any:
        """
        Place a market order with validation.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            side: 'buy' or 'sell'
            quantity: Number of shares
            time_in_force: Order time in force (default: 'day')
        """
        try:
            # Validation
            if not symbol or not symbol.strip():
                raise ValueError("Symbol cannot be empty")

            if quantity <= 0:
                raise ValueError("Quantity must be positive")

            side_normalized = side.lower().strip()
            if side_normalized not in ["buy", "sell"]:
                raise ValueError("Side must be 'buy' or 'sell'")

            # Create order request
            order_request = MarketOrderRequest(
                symbol=symbol.upper(),
                qty=quantity,
                side=OrderSide.BUY if side_normalized == "buy" else OrderSide.SELL,
                time_in_force=(
                    TimeInForce.DAY if time_in_force.lower() == "day" else TimeInForce.GTC
                ),
            )

            return self.place_order(order_request)

        except ValueError as e:
            logger.error(f"Invalid order parameters: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to place market order for {symbol}: {e}")
            raise

    def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        limit_price: float,
        time_in_force: str = "day",
    ) -> Any:
        """
        Place a limit order with validation.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            side: 'buy' or 'sell'
            quantity: Number of shares
            limit_price: Limit price for the order
            time_in_force: Order time in force (default: 'day')
        """
        try:
            # Validation
            if not symbol or not symbol.strip():
                raise ValueError("Symbol cannot be empty")

            if quantity <= 0:
                raise ValueError("Quantity must be positive")

            if limit_price <= 0:
                raise ValueError("Limit price must be positive")

            side_normalized = side.lower().strip()
            if side_normalized not in ["buy", "sell"]:
                raise ValueError("Side must be 'buy' or 'sell'")

            # Create order request
            order_request = LimitOrderRequest(
                symbol=symbol.upper(),
                qty=quantity,
                side=OrderSide.BUY if side_normalized == "buy" else OrderSide.SELL,
                limit_price=limit_price,
                time_in_force=(
                    TimeInForce.DAY if time_in_force.lower() == "day" else TimeInForce.GTC
                ),
            )

            return self.place_order(order_request)

        except ValueError as e:
            logger.error(f"Invalid limit order parameters: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to place limit order for {symbol}: {e}")
            raise

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order by ID."""
        try:
            self._trading_client.cancel_order_by_id(order_id)
            logger.info(f"Successfully cancelled order: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            raise

    def get_orders(self, status: str | None = None) -> list[Any]:
        """Get orders, optionally filtered by status."""
        try:
            orders = self._trading_client.get_orders(status=status)
            logger.debug(f"Successfully retrieved {len(orders)} orders")
            return orders
        except Exception as e:
            logger.error(f"Failed to get orders: {e}")
            raise

    # Market Data Operations
    def get_current_price(self, symbol: str) -> float | None:
        """
        Get current price for a symbol.

        Returns the mid price between bid and ask, or None if not available.
        """
        try:
            quote = self.get_latest_quote(symbol)
            if quote and hasattr(quote, "bid_price") and hasattr(quote, "ask_price"):
                if quote.bid_price and quote.ask_price:
                    return float((quote.bid_price + quote.ask_price) / 2)
            return None
        except Exception as e:
            logger.error(f"Failed to get current price for {symbol}: {e}")
            raise

    def get_latest_quote(self, symbol: str) -> Any | None:
        """Get latest quote for a symbol."""
        try:
            request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
            response = self._data_client.get_stock_latest_quote(request)

            if symbol in response:
                quote = response[symbol]
                logger.debug(f"Successfully retrieved quote for {symbol}")
                return quote

            logger.warning(f"No quote found for {symbol}")
            return None

        except Exception as e:
            logger.error(f"Failed to get quote for {symbol}: {e}")
            raise

    def get_historical_bars(
        self, symbol: str, start_date: str, end_date: str, timeframe: str = "1Day"
    ) -> Any | None:
        """
        Get historical bar data for a symbol.

        Args:
            symbol: Stock symbol
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)
            timeframe: Timeframe (1Min, 5Min, 15Min, 1Hour, 1Day)
        """
        try:
            # Map timeframe strings to Alpaca TimeFrame objects
            timeframe_map = {
                "1Min": TimeFrame.Minute,
                "5Min": TimeFrame(5, "Minute"),
                "15Min": TimeFrame(15, "Minute"),
                "1Hour": TimeFrame.Hour,
                "1Day": TimeFrame.Day,
            }

            if timeframe not in timeframe_map:
                raise ValueError(f"Unsupported timeframe: {timeframe}")

            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=timeframe_map[timeframe],
                start=start_date,
                end=end_date,
            )

            response = self._data_client.get_stock_bars(request)

            if symbol in response:
                bars = response[symbol]
                logger.debug(f"Successfully retrieved {len(bars)} bars for {symbol}")
                return bars

            logger.warning(f"No historical data found for {symbol}")
            return None

        except Exception as e:
            logger.error(f"Failed to get historical data for {symbol}: {e}")
            raise

    # Utility Methods
    def validate_connection(self) -> bool:
        """Validate that the connection to Alpaca is working."""
        try:
            account = self.get_account()
            if account:
                logger.info("Alpaca connection validated successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"Alpaca connection validation failed: {e}")
            return False

    def get_buying_power(self) -> Decimal | None:
        """Get current buying power."""
        try:
            account = self.get_account()
            if account and hasattr(account, "buying_power"):
                return Decimal(str(account.buying_power))
            return None
        except Exception as e:
            logger.error(f"Failed to get buying power: {e}")
            raise

    def get_portfolio_value(self) -> Decimal | None:
        """Get current portfolio value."""
        try:
            account = self.get_account()
            if account and hasattr(account, "portfolio_value"):
                return Decimal(str(account.portfolio_value))
            return None
        except Exception as e:
            logger.error(f"Failed to get portfolio value: {e}")
            raise

    def __repr__(self) -> str:
        """String representation."""
        return f"AlpacaManager(paper={self._paper})"


# Factory function for easy creation
def create_alpaca_manager(
    api_key: str, secret_key: str, paper: bool = True, base_url: str | None = None
) -> AlpacaManager:
    """
    Factory function to create an AlpacaManager instance.

    This function provides a clean way to create AlpacaManager instances
    and can be easily extended with additional configuration options.
    """
    return AlpacaManager(api_key=api_key, secret_key=secret_key, paper=paper, base_url=base_url)
