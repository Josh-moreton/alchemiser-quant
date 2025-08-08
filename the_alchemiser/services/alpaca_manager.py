"""
Centralized Alpaca client management - Phase 1 of incremental improvements.

This module consolidates scattered Alpaca client usage into a single, well-managed class.
It provides a transitional approach that:
1. Reduces scattered imports
2. Adds consistent error handling
3. Maintains backward compatibility
4. Sets up for future improvements

Phase 2 Update: Now implements domain interfaces for type safety and future migration.
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

from the_alchemiser.domain.interfaces import (
    AccountRepository,
    MarketDataRepository,
    TradingRepository,
)

logger = logging.getLogger(__name__)


class AlpacaManager(TradingRepository, MarketDataRepository, AccountRepository):
    """
    Centralized Alpaca client management implementing domain interfaces.

    This class consolidates all Alpaca API interactions into a single, well-managed interface.
    It provides consistent error handling, logging, and implements the domain layer interfaces
    for type safety and future architectural improvements.

    Implements:
    - TradingRepository: For order placement and position management
    - MarketDataRepository: For market data and quotes
    - AccountRepository: For account information and portfolio data
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
        """
        Get all positions as list of position objects (AccountRepository interface).

        Returns:
            List of position objects with attributes like symbol, qty, market_value, etc.
        """
        try:
            positions = self._trading_client.get_all_positions()
            logger.debug(f"Successfully retrieved {len(positions)} positions")
            return positions
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            raise

    def get_positions_dict(self) -> dict[str, float]:
        """
        Get all positions as dict mapping symbol to quantity (legacy method - use get_positions).

        Returns:
            Dictionary mapping symbol to quantity owned. Only includes non-zero positions.
        """
        # Delegate to the main get_positions method
        return self.get_positions()

    def get_all_positions(self) -> list[Any]:
        """Get all positions as list (backward compatibility)."""
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
        self,
        symbol: str,
        side: str,
        qty: float | None = None,
        notional: float | None = None,
    ) -> str | None:
        """
        Place a market order with validation.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            side: 'buy' or 'sell'
            qty: Quantity to trade (use either qty OR notional)
            notional: Dollar amount to trade (use either qty OR notional)
        """
        try:
            # Validation
            if not symbol or not symbol.strip():
                raise ValueError("Symbol cannot be empty")

            if qty is None and notional is None:
                raise ValueError("Either qty or notional must be specified")

            if qty is not None and notional is not None:
                raise ValueError("Cannot specify both qty and notional")

            if qty is not None and qty <= 0:
                raise ValueError("Quantity must be positive")

            if notional is not None and notional <= 0:
                raise ValueError("Notional amount must be positive")

            side_normalized = side.lower().strip()
            if side_normalized not in ["buy", "sell"]:
                raise ValueError("Side must be 'buy' or 'sell'")

            # Create order request
            order_request = MarketOrderRequest(
                symbol=symbol.upper(),
                qty=qty,
                notional=notional,
                side=OrderSide.BUY if side_normalized == "buy" else OrderSide.SELL,
                time_in_force=TimeInForce.DAY,
            )

            result = self.place_order(order_request)

            # Return order ID as string or None
            if result and hasattr(result, "id"):
                return str(result.id)
            elif isinstance(result, dict) and "id" in result:
                return str(result["id"])
            return None

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

    def get_latest_quote(self, symbol: str) -> tuple[float, float] | None:
        """
        Get latest bid/ask quote for a symbol (interface compatible).

        Args:
            symbol: Stock symbol

        Returns:
            Tuple of (bid, ask) prices, or None if not available.
        """
        try:
            request = StockLatestQuoteRequest(symbol_or_symbols=[symbol])
            quotes = self._data_client.get_stock_latest_quote(request)
            quote = quotes.get(symbol)

            if quote:
                bid = float(getattr(quote, "bid_price", 0))
                ask = float(getattr(quote, "ask_price", 0))
                if bid > 0 and ask > 0:
                    return (bid, ask)

            logger.warning(f"No valid quote data available for {symbol}")
            return None
        except Exception as e:
            logger.error(f"Failed to get latest quote for {symbol}: {e}")
            return None

    def get_latest_quote_raw(self, symbol: str) -> Any | None:
        """Get latest quote as raw object (backward compatibility)."""
        try:
            request = StockLatestQuoteRequest(symbol_or_symbols=[symbol])
            quotes = self._data_client.get_stock_latest_quote(request)
            quote = quotes.get(symbol)

            if quote:
                logger.debug(f"Successfully retrieved quote for {symbol}")
                return quote
            else:
                logger.warning(f"No quote data available for {symbol}")
                return None
        except Exception as e:
            logger.error(f"Failed to get latest quote for {symbol}: {e}")
            return None

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

    # Additional methods to match interface contracts

    def cancel_all_orders(self, symbol: str | None = None) -> bool:
        """
        Cancel all orders, optionally filtered by symbol.

        Args:
            symbol: If provided, only cancel orders for this symbol

        Returns:
            True if successful, False otherwise.
        """
        try:
            if symbol:
                # Get orders for specific symbol and cancel them
                orders = self.get_orders(status="open")
                symbol_orders = [
                    order for order in orders if getattr(order, "symbol", None) == symbol
                ]
                for order in symbol_orders:
                    order_id = getattr(order, "id", None)
                    if order_id:
                        self.cancel_order(str(order_id))
            else:
                # Cancel all open orders
                self._trading_client.cancel_orders()

            logger.info("Successfully cancelled orders" + (f" for {symbol}" if symbol else ""))
            return True
        except Exception as e:
            logger.error(f"Failed to cancel orders: {e}")
            return False

    def liquidate_position(self, symbol: str) -> str | None:
        """
        Liquidate entire position using close_position API.

        Args:
            symbol: Symbol to liquidate

        Returns:
            Order ID if successful, None if failed.
        """
        try:
            order = self._trading_client.close_position(symbol)
            order_id = str(getattr(order, "id", "unknown"))
            logger.info(f"Successfully liquidated position for {symbol}: {order_id}")
            return order_id
        except Exception as e:
            logger.error(f"Failed to liquidate position for {symbol}: {e}")
            return None

    def get_asset_info(self, symbol: str) -> dict[str, Any] | None:
        """
        Get asset information.

        Args:
            symbol: Stock symbol

        Returns:
            Asset information dictionary, or None if not found.
        """
        try:
            asset = self._trading_client.get_asset(symbol)
            # Convert to dictionary for interface compatibility
            return {
                "symbol": getattr(asset, "symbol", symbol),
                "name": getattr(asset, "name", None),
                "exchange": getattr(asset, "exchange", None),
                "asset_class": getattr(asset, "asset_class", None),
                "tradable": getattr(asset, "tradable", None),
                "fractionable": getattr(asset, "fractionable", None),
            }
        except Exception as e:
            logger.error(f"Failed to get asset info for {symbol}: {e}")
            return None

    def is_market_open(self) -> bool:
        """
        Check if the market is currently open.

        Returns:
            True if market is open, False otherwise.
        """
        try:
            clock = self._trading_client.get_clock()
            return getattr(clock, "is_open", False)
        except Exception as e:
            logger.error(f"Failed to get market status: {e}")
            return False

    def get_market_calendar(self, start_date: str, end_date: str) -> list[dict[str, Any]]:
        """
        Get market calendar information.

        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)

        Returns:
            List of market calendar entries.
        """
        try:
            calendar = self._trading_client.get_calendar(start=start_date, end=end_date)
            # Convert to list of dictionaries for interface compatibility
            return [
                {
                    "date": str(getattr(day, "date", "")),
                    "open": str(getattr(day, "open", "")),
                    "close": str(getattr(day, "close", "")),
                }
                for day in calendar
            ]
        except Exception as e:
            logger.error(f"Failed to get market calendar: {e}")
            return []

    def get_portfolio_history(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
        timeframe: str = "1Day",
    ) -> dict[str, Any] | None:
        """
        Get portfolio performance history.

        Args:
            start_date: Start date (ISO format), defaults to 1 month ago
            end_date: End date (ISO format), defaults to today
            timeframe: Timeframe for data points

        Returns:
            Portfolio history data, or None if failed.
        """
        try:
            history = self._trading_client.get_portfolio_history(
                start=start_date, end=end_date, timeframe=timeframe
            )
            # Convert to dictionary for interface compatibility
            return {
                "timestamp": getattr(history, "timestamp", []),
                "equity": getattr(history, "equity", []),
                "profit_loss": getattr(history, "profit_loss", []),
                "profit_loss_pct": getattr(history, "profit_loss_pct", []),
                "base_value": getattr(history, "base_value", None),
                "timeframe": timeframe,
            }
        except Exception as e:
            logger.error(f"Failed to get portfolio history: {e}")
            return None

    def get_activities(
        self,
        activity_type: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get account activities (trades, dividends, etc.).

        Args:
            activity_type: Filter by activity type (optional)
            start_date: Start date (ISO format), defaults to 1 week ago
            end_date: End date (ISO format), defaults to today

        Returns:
            List of activity records.
        """
        try:
            activities = self._trading_client.get_activities(
                activity_type=activity_type, date=start_date, until=end_date
            )
            # Convert to list of dictionaries for interface compatibility
            return [
                {
                    "id": str(getattr(activity, "id", "")),
                    "activity_type": str(getattr(activity, "activity_type", "")),
                    "date": str(getattr(activity, "date", "")),
                    "symbol": getattr(activity, "symbol", None),
                    "side": getattr(activity, "side", None),
                    "qty": getattr(activity, "qty", None),
                    "price": getattr(activity, "price", None),
                }
                for activity in activities
            ]
        except Exception as e:
            logger.error(f"Failed to get activities: {e}")
            return []

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
