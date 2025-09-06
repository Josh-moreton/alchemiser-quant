"""Business Unit: shared | Status: current.

Alpaca broker manager for unified broker operations across all modules.

This module provides the primary AlpacaManager class that implements trading,
market data, and account repository interfaces. It was moved from the execution
module to shared to resolve architectural boundary violations where strategy
and shared modules were importing from execution.

The AlpacaManager consolidates scattered Alpaca client usage into a single,
well-managed class with:
1. Consistent error handling
2. Proper logging
3. Type-safe interfaces
4. Unified testing capabilities

This provides a transitional approach that maintains backward compatibility
while setting up for future broker abstraction improvements.
"""

from __future__ import annotations

import logging

# Type checking imports to avoid circular dependencies
from typing import TYPE_CHECKING, Any

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import LimitOrderRequest, MarketOrderRequest

from the_alchemiser.shared.protocols.repository import (
    AccountRepository,
    MarketDataRepository,
    TradingRepository,
)

if TYPE_CHECKING:
    from the_alchemiser.execution.core.execution_schemas import WebSocketResultDTO
    from the_alchemiser.execution.mappers.alpaca_dto_mapping import (
        alpaca_order_to_execution_result,
        create_error_execution_result,
    )
    from the_alchemiser.execution.orders.order_schemas import OrderExecutionResultDTO, RawOrderEnvelope
    from the_alchemiser.execution.strategies.smart_execution import DataProvider

logger = logging.getLogger(__name__)


class AlpacaManager(TradingRepository, MarketDataRepository, AccountRepository):
    """Unified Alpaca broker manager implementing all repository interfaces.
    
    This class provides a single point of integration with Alpaca APIs,
    implementing trading, market data, and account repository protocols.
    
    Key features:
    - Unified error handling and logging
    - Type-safe interface implementations
    - Backward compatibility with existing AlpacaManager usage
    - Support for both paper and live trading
    
    Example:
        >>> manager = AlpacaManager(api_key="key", secret_key="secret", paper=True)
        >>> positions = manager.get_positions_dict()
        >>> account = manager.get_account()
        >>> price = manager.get_current_price("AAPL")
    """

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        paper: bool = True,
        base_url: str | None = None,
    ) -> None:
        """Initialize AlpacaManager with credentials.
        
        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key  
            paper: Whether to use paper trading (default: True)
            base_url: Optional custom base URL for API
            
        Raises:
            Exception: If client initialization fails
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.paper = paper
        self.base_url = base_url

        try:
            # Initialize trading client
            if base_url:
                self._trading_client = TradingClient(
                    api_key=api_key,
                    secret_key=secret_key,
                    paper=paper,
                    url_override=base_url,
                )
            else:
                self._trading_client = TradingClient(
                    api_key=api_key, secret_key=secret_key, paper=paper
                )

            # Initialize data client
            self._data_client = StockHistoricalDataClient(api_key=api_key, secret_key=secret_key)

            logger.info(f"AlpacaManager initialized - Paper: {paper}")

        except Exception as e:
            logger.error(f"Failed to initialize Alpaca clients: {e}")
            raise

    @property
    def trading_client(self) -> TradingClient:
        """Access to underlying trading client for backward compatibility."""
        return self._trading_client

    @property
    def is_paper_trading(self) -> bool:
        """Check if this is paper trading."""
        return self.paper

    def validate_connection(self) -> bool:
        """Validate connection to trading service.
        
        Returns:
            True if connection is valid, False otherwise.
        """
        try:
            self._trading_client.get_account()
            return True
        except Exception as e:
            logger.error(f"Connection validation failed: {e}")
            return False

    # Account Repository Implementation
    def get_account(self) -> dict[str, Any] | None:
        """Get account information.
        
        Returns:
            Account information as dictionary, or None if failed.
        """
        try:
            account = self._trading_client.get_account()
            return account.__dict__ if hasattr(account, "__dict__") else account._raw
        except Exception as e:
            logger.error(f"Failed to get account: {e}")
            return None

    def get_buying_power(self) -> float | None:
        """Get current buying power.
        
        Returns:
            Available buying power in dollars, or None if failed.
        """
        try:
            account = self._trading_client.get_account()
            return float(account.buying_power)
        except Exception as e:
            logger.error(f"Failed to get buying power: {e}")
            return None

    def get_positions_dict(self) -> dict[str, float]:
        """Get all current positions as dict.
        
        Returns:
            Dictionary mapping symbol to quantity owned. Only includes non-zero positions.
        """
        try:
            positions = self._trading_client.get_all_positions()
            return {pos.symbol: float(pos.qty) for pos in positions if float(pos.qty) != 0}
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return {}

    def get_portfolio_value(self) -> float | None:
        """Get total portfolio value.
        
        Returns:
            Total portfolio value in dollars, or None if failed.
        """
        try:
            account = self._trading_client.get_account()
            return float(account.portfolio_value)
        except Exception as e:
            logger.error(f"Failed to get portfolio value: {e}")
            return None

    # Market Data Repository Implementation
    def get_current_price(self, symbol: str) -> float | None:
        """Get current price for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Current price, or None if failed.
        """
        try:
            quote_request = StockLatestQuoteRequest(symbol_or_symbols=[symbol])
            quotes = self._data_client.get_stock_latest_quote(quote_request)
            
            if symbol in quotes:
                quote = quotes[symbol]
                # Use mid-price (average of bid and ask)
                return (float(quote.bid_price) + float(quote.ask_price)) / 2
            else:
                logger.warning(f"No quote data available for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get current price for {symbol}: {e}")
            return None

    def get_quote(self, symbol: str) -> dict[str, Any] | None:
        """Get quote information for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Quote information as dictionary, or None if failed.
        """
        try:
            quote_request = StockLatestQuoteRequest(symbol_or_symbols=[symbol])
            quotes = self._data_client.get_stock_latest_quote(quote_request)
            
            if symbol in quotes:
                quote = quotes[symbol]
                return {
                    "symbol": symbol,
                    "bid_price": float(quote.bid_price),
                    "ask_price": float(quote.ask_price),
                    "bid_size": int(quote.bid_size),
                    "ask_size": int(quote.ask_size),
                    "timestamp": quote.timestamp,
                }
            else:
                logger.warning(f"No quote data available for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get quote for {symbol}: {e}")
            return None

    def get_historical_bars(
        self, symbol: str, start_date: str, end_date: str, timeframe: str = "1Day"
    ) -> list[dict[str, Any]]:
        """Get historical bar data for a symbol.
        
        Args:
            symbol: Stock symbol
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)
            timeframe: Timeframe (1Day, 1Hour, etc.)
            
        Returns:
            List of bar dictionaries with OHLCV data.
        """
        try:
            # Parse timeframe
            if timeframe == "1Day":
                tf = TimeFrame(1, TimeFrameUnit.Day)
            elif timeframe == "1Hour":
                tf = TimeFrame(1, TimeFrameUnit.Hour)
            elif timeframe == "1Min":
                tf = TimeFrame(1, TimeFrameUnit.Minute)
            else:
                logger.warning(f"Unknown timeframe: {timeframe}, using 1Day")
                tf = TimeFrame(1, TimeFrameUnit.Day)

            # Create request
            request = StockBarsRequest(
                symbol_or_symbols=[symbol],
                timeframe=tf,
                start=start_date,
                end=end_date,
            )

            # Get data
            bars = self._data_client.get_stock_bars(request)
            
            if symbol not in bars:
                logger.warning(f"No bar data available for {symbol}")
                return []

            # Convert to list of dictionaries
            result = []
            for bar in bars[symbol]:
                result.append({
                    "timestamp": bar.timestamp,
                    "open": float(bar.open),
                    "high": float(bar.high),
                    "low": float(bar.low),
                    "close": float(bar.close),
                    "volume": int(bar.volume),
                })

            return result

        except Exception as e:
            logger.error(f"Failed to get historical data for {symbol}: {e}")
            raise

    # Trading Repository Implementation
    def place_order(self, order_request: Any) -> Any:
        """Place an order using raw Alpaca order request.
        
        Args:
            order_request: Alpaca order request object
            
        Returns:
            RawOrderEnvelope with execution details and status.
        """
        try:
            from the_alchemiser.execution.mappers.alpaca_dto_mapping import alpaca_order_to_execution_result
            
            order = self._trading_client.submit_order(order_request)
            return alpaca_order_to_execution_result(order)
        except Exception as e:
            from the_alchemiser.execution.mappers.alpaca_dto_mapping import create_error_execution_result
            
            logger.error(f"Failed to place order: {e}")
            return create_error_execution_result(str(e))

    def place_market_order(
        self,
        symbol: str,
        side: str,
        qty: float | None = None,
        notional: float | None = None,
    ) -> Any:
        """Place a market order.
        
        Args:
            symbol: Stock symbol
            side: "buy" or "sell"
            qty: Quantity to trade (use either qty OR notional)
            notional: Dollar amount to trade (use either qty OR notional)
            
        Returns:
            RawOrderEnvelope with execution details and status.
        """
        try:
            from the_alchemiser.execution.mappers.alpaca_dto_mapping import create_error_execution_result
            
            # Convert side to Alpaca enum
            alpaca_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL

            # Create market order request
            if qty is not None:
                order_request = MarketOrderRequest(
                    symbol=symbol,
                    side=alpaca_side,
                    qty=qty,
                    time_in_force=TimeInForce.DAY,
                )
            elif notional is not None:
                order_request = MarketOrderRequest(
                    symbol=symbol,
                    side=alpaca_side,
                    notional=notional,
                    time_in_force=TimeInForce.DAY,
                )
            else:
                raise ValueError("Either qty or notional must be provided")

            return self.place_order(order_request)

        except Exception as e:
            logger.error(f"Failed to place market order: {e}")
            return create_error_execution_result(str(e))

    def place_limit_order(
        self,
        symbol: str,
        side: str,
        qty: float,
        limit_price: float,
        time_in_force: str = "day",
    ) -> Any:
        """Place a limit order.
        
        Args:
            symbol: Stock symbol
            side: "buy" or "sell"
            qty: Quantity to trade
            limit_price: Limit price
            time_in_force: Time in force ("day", "gtc", "ioc", "fok")
            
        Returns:
            RawOrderEnvelope with execution details and status.
        """
        try:
            from the_alchemiser.execution.mappers.alpaca_dto_mapping import create_error_execution_result
            
            # Convert side to Alpaca enum
            alpaca_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL

            # Convert time in force to Alpaca enum
            tif_map = {
                "day": TimeInForce.DAY,
                "gtc": TimeInForce.GTC,
                "ioc": TimeInForce.IOC,
                "fok": TimeInForce.FOK,
            }
            alpaca_tif = tif_map.get(time_in_force.lower(), TimeInForce.DAY)

            # Create limit order request
            order_request = LimitOrderRequest(
                symbol=symbol,
                side=alpaca_side,
                qty=qty,
                limit_price=limit_price,
                time_in_force=alpaca_tif,
            )

            return self.place_order(order_request)

        except Exception as e:
            logger.error(f"Failed to place limit order: {e}")
            return create_error_execution_result(str(e))

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            self._trading_client.cancel_order_by_id(order_id)
            logger.info(f"Order {order_id} cancelled successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False

    def cancel_all_orders(self, symbol: str | None = None) -> bool:
        """Cancel all orders, optionally filtered by symbol.
        
        Args:
            symbol: If provided, only cancel orders for this symbol
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            if symbol:
                # Get orders for specific symbol and cancel them
                orders = self._trading_client.get_orders(filter={"symbols": [symbol]})
                for order in orders:
                    self._trading_client.cancel_order_by_id(order.id)
                logger.info(f"All orders for {symbol} cancelled successfully")
            else:
                # Cancel all orders
                self._trading_client.cancel_orders()
                logger.info("All orders cancelled successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel orders: {e}")
            return False

    def liquidate_position(self, symbol: str) -> str | None:
        """Liquidate entire position using close_position API.
        
        Args:
            symbol: Symbol to liquidate
            
        Returns:
            Order ID if successful, None if failed.
        """
        try:
            order = self._trading_client.close_position(symbol)
            logger.info(f"Position {symbol} liquidated successfully")
            return order.id
        except Exception as e:
            logger.error(f"Failed to liquidate position {symbol}: {e}")
            return None

    # Convenience methods for backward compatibility
    def get_order(self, order_id: str) -> dict[str, Any] | None:
        """Get order details by ID.
        
        Args:
            order_id: Order ID
            
        Returns:
            Order details as dictionary, or None if failed.
        """
        try:
            order = self._trading_client.get_order_by_id(order_id)
            return order.__dict__ if hasattr(order, "__dict__") else order._raw
        except Exception as e:
            logger.error(f"Failed to get order {order_id}: {e}")
            return None

    def get_orders(self, status: str | None = None, limit: int = 500) -> list[dict[str, Any]]:
        """Get orders with optional status filter.
        
        Args:
            status: Order status filter ("open", "closed", "all")
            limit: Maximum number of orders to return
            
        Returns:
            List of order dictionaries.
        """
        try:
            filter_params = {"limit": limit}
            if status and status != "all":
                filter_params["status"] = status

            orders = self._trading_client.get_orders(filter=filter_params)
            return [order.__dict__ if hasattr(order, "__dict__") else order._raw for order in orders]
        except Exception as e:
            logger.error(f"Failed to get orders: {e}")
            return []

    def wait_for_order_completion(self, order_id: str, timeout: int = 30) -> Any:
        """Wait for order completion with timeout.
        
        Args:
            order_id: Order ID to monitor
            timeout: Timeout in seconds
            
        Returns:
            OrderExecutionResultDTO with final status.
        """
        import time
        
        from the_alchemiser.execution.mappers.alpaca_dto_mapping import alpaca_order_to_execution_result
        from the_alchemiser.execution.orders.order_schemas import OrderExecutionResultDTO
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                order = self._trading_client.get_order_by_id(order_id)
                
                if order.status in ["filled", "canceled", "rejected", "expired"]:
                    # Order is complete
                    result = alpaca_order_to_execution_result(order)
                    return OrderExecutionResultDTO(
                        success=order.status == "filled",
                        order_id=order.id,
                        status=order.status,
                        filled_qty=float(order.filled_qty) if order.filled_qty else 0.0,
                        filled_avg_price=float(order.filled_avg_price) if order.filled_avg_price else 0.0,
                        message=f"Order completed with status: {order.status}",
                        raw_response=result.raw_response,
                    )
                
                # Wait before checking again
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error checking order status: {e}")
                return OrderExecutionResultDTO(
                    success=False,
                    order_id=order_id,
                    status="error",
                    filled_qty=0.0,
                    filled_avg_price=0.0,
                    message=f"Error monitoring order: {e}",
                    raw_response={},
                )
        
        # Timeout reached
        return OrderExecutionResultDTO(
            success=False,
            order_id=order_id,
            status="timeout",
            filled_qty=0.0,
            filled_avg_price=0.0,
            message=f"Timeout waiting for order completion after {timeout}s",
            raw_response={},
        )

    # WebSocket support methods
    def create_websocket_connection(self) -> Any:
        """Create WebSocket connection for real-time data.
        
        Returns:
            WebSocket connection object.
        """
        from alpaca.data.live import StockDataStream
        
        try:
            stream = StockDataStream(api_key=self.api_key, secret_key=self.secret_key)
            return stream
        except Exception as e:
            logger.error(f"Failed to create WebSocket connection: {e}")
            raise

    def subscribe_to_trades(self, symbols: list[str], callback: Any) -> Any:
        """Subscribe to trade updates for symbols.
        
        Args:
            symbols: List of symbols to monitor
            callback: Callback function for trade updates
            
        Returns:
            WebSocketResultDTO with subscription status.
        """
        try:
            from the_alchemiser.execution.core.execution_schemas import WebSocketResultDTO
            
            stream = self.create_websocket_connection()
            stream.subscribe_trades(callback, *symbols)
            
            return WebSocketResultDTO(
                success=True,
                message=f"Subscribed to trades for {symbols}",
                symbols=symbols,
                subscription_type="trades",
            )
        except Exception as e:
            from the_alchemiser.execution.core.execution_schemas import WebSocketResultDTO
            
            logger.error(f"Failed to subscribe to trades: {e}")
            return WebSocketResultDTO(
                success=False,
                message=f"Failed to subscribe to trades: {e}",
                symbols=symbols,
                subscription_type="trades",
            )

    def subscribe_to_quotes(self, symbols: list[str], callback: Any) -> Any:
        """Subscribe to quote updates for symbols.
        
        Args:
            symbols: List of symbols to monitor
            callback: Callback function for quote updates
            
        Returns:
            WebSocketResultDTO with subscription status.
        """
        try:
            from the_alchemiser.execution.core.execution_schemas import WebSocketResultDTO
            
            stream = self.create_websocket_connection()
            stream.subscribe_quotes(callback, *symbols)
            
            return WebSocketResultDTO(
                success=True,
                message=f"Subscribed to quotes for {symbols}",
                symbols=symbols,
                subscription_type="quotes",
            )
        except Exception as e:
            from the_alchemiser.execution.core.execution_schemas import WebSocketResultDTO
            
            logger.error(f"Failed to subscribe to quotes: {e}")
            return WebSocketResultDTO(
                success=False,
                message=f"Failed to subscribe to quotes: {e}",
                symbols=symbols,
                subscription_type="quotes",
            )


# Factory function for easy creation
def create_alpaca_manager(
    api_key: str, secret_key: str, paper: bool = True, base_url: str | None = None
) -> AlpacaManager:
    """Factory function to create AlpacaManager instance.
    
    Args:
        api_key: Alpaca API key
        secret_key: Alpaca secret key
        paper: Whether to use paper trading (default: True)
        base_url: Optional custom base URL for API
        
    Returns:
        Configured AlpacaManager instance.
    """
    return AlpacaManager(
        api_key=api_key,
        secret_key=secret_key,
        paper=paper,
        base_url=base_url,
    )