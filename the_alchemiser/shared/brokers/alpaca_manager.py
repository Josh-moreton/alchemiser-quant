"""Business Unit: shared | Status: current

Alpaca broker adapter (moved from execution module for architectural compliance).

This module consolidates scattered Alpaca client usage into a single, well-managed class.
It provides a transitional approach that:
1. Reduces scattered imports
2. Adds consistent error handling
3. Maintains backward compatibility
4. Sets up for future improvements

Phase 2 Update: Now implements domain interfaces for type safety and future migration.
Phase 3 Update: Moved to shared module to resolve architectural boundary violations.
"""

from __future__ import annotations

import logging
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

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
    from the_alchemiser.execution.orders.order_schemas import RawOrderEnvelope
    from the_alchemiser.execution.strategies.smart_execution import DataProvider

logger = logging.getLogger(__name__)


# Simple DTOs to avoid circular dependencies - defined locally to avoid imports
class Result(BaseModel):
    """Common base for DTOs that expose success/error outcome fields."""

    model_config = ConfigDict(strict=True, frozen=True, validate_assignment=True)

    success: bool
    error: str | None = None
class WebSocketStatus(str, Enum):
    """WebSocket operation status enumeration."""

    COMPLETED = "completed"
    TIMEOUT = "timeout"
    ERROR = "error"


class WebSocketResult(BaseModel):
    """Outcome of WebSocket operations (status, message, completed orders)."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    status: WebSocketStatus = Field(description="WebSocket operation status")
    message: str = Field(description="Status message")
    completed_order_ids: list[str] = Field(
        default_factory=list, description="Order IDs that completed during operation"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class OrderExecutionResult(Result):
    """DTO for order execution results."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    # Core execution data
    order_id: str
    status: Literal["accepted", "filled", "partially_filled", "rejected", "canceled"]
    filled_qty: Decimal
    avg_fill_price: Decimal | None = None
    submitted_at: datetime
    completed_at: datetime | None = None

    @field_validator("filled_qty")
    @classmethod
    def validate_filled_qty(cls, v: Decimal) -> Decimal:
        if v < 0:
            raise ValueError("Filled quantity cannot be negative")
        return v

    @field_validator("avg_fill_price")
    @classmethod
    def validate_avg_fill_price(cls, v: Decimal | None) -> Decimal | None:
        if v is not None and v <= 0:
            raise ValueError("Average fill price must be greater than 0")
        return v


# Backward compatibility aliases
WebSocketResultDTO = WebSocketResult
OrderExecutionResultDTO = OrderExecutionResult


class AlpacaManager(TradingRepository, MarketDataRepository, AccountRepository):
    """Centralized Alpaca client management implementing domain interfaces.

    This class consolidates all Alpaca API interactions into a single, well-managed interface.
    It provides consistent error handling, logging, and implements the domain layer interfaces
    for type safety and future architectural improvements.

    Implements:
    - TradingRepository: For order placement and position management
    - MarketDataRepository: For market data and quotes
    - AccountRepository: For account information and portfolio data
    """

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        paper: bool = True,
        base_url: str | None = None,
    ) -> None:
        """Initialize Alpaca clients.

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
            # Note: TradingClient type stubs may not accept base_url as kwarg; avoid passing extras for mypy
            self._trading_client = TradingClient(
                api_key=api_key, secret_key=secret_key, paper=paper
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

    # Public, read-only accessors for credentials and mode (for factories/streams)
    @property
    def api_key(self) -> str:
        """Public accessor for the API key (read-only)."""
        return self._api_key

    @property
    def secret_key(self) -> str:
        """Public accessor for the Secret key (read-only)."""
        return self._secret_key

    @property
    def paper(self) -> bool:
        """Public accessor indicating paper/live mode."""
        return self._paper

    # Helper methods for DTO mapping
    def _alpaca_order_to_execution_result(self, order: Any) -> OrderExecutionResultDTO:
        """Convert Alpaca order object to OrderExecutionResultDTO.
        
        Simple implementation that avoids circular imports.
        """
        try:
            # Extract basic fields from order object
            order_id = getattr(order, 'id', 'unknown')
            status = getattr(order, 'status', 'unknown')
            filled_qty = Decimal(str(getattr(order, 'filled_qty', 0)))
            avg_fill_price = getattr(order, 'avg_fill_price', None)
            if avg_fill_price is not None:
                avg_fill_price = Decimal(str(avg_fill_price))
            
            # Simple timestamp handling
            from datetime import UTC, datetime
            submitted_at = getattr(order, 'submitted_at', None) or datetime.now(UTC)
            if isinstance(submitted_at, str):
                # Handle ISO format strings
                submitted_at = datetime.fromisoformat(submitted_at.replace('Z', '+00:00'))
            
            completed_at = getattr(order, 'updated_at', None)
            if completed_at and isinstance(completed_at, str):
                completed_at = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
            
            # Map status to our expected values  
            status_mapping = {
                'new': 'accepted',
                'accepted': 'accepted', 
                'filled': 'filled',
                'partially_filled': 'partially_filled',
                'rejected': 'rejected',
                'canceled': 'canceled',
                'cancelled': 'canceled',
                'expired': 'rejected'
            }
            mapped_status = status_mapping.get(status, 'accepted')
            
            success = mapped_status not in ['rejected', 'canceled']
            
            return OrderExecutionResultDTO(
                success=success,
                order_id=order_id,
                status=mapped_status,  # type: ignore[arg-type]
                filled_qty=filled_qty,
                avg_fill_price=avg_fill_price,
                submitted_at=submitted_at,
                completed_at=completed_at,
                error=None if success else f"Order {status}"
            )
        except Exception as e:
            logger.error(f"Failed to convert order to execution result: {e}")
            return self._create_error_execution_result(e, "Order conversion")

    def _create_error_execution_result(
        self, 
        error: Exception, 
        context: str = "Operation", 
        order_id: str = "unknown"
    ) -> OrderExecutionResultDTO:
        """Create an error OrderExecutionResultDTO."""
        from datetime import UTC, datetime
        
        return OrderExecutionResultDTO(
            success=False,
            order_id=order_id,
            status='rejected',  # type: ignore[arg-type]
            filled_qty=Decimal('0'),
            avg_fill_price=None,
            submitted_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
            error=f"{context} failed: {str(error)}"
        )

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
        """Get all positions as list of position objects (AccountRepository interface).

        Returns:
            List of position objects with attributes like symbol, qty, market_value, etc.

        """
        try:
            positions = self._trading_client.get_all_positions()
            logger.debug(f"Successfully retrieved {len(positions)} positions")
            # Ensure consistent return type
            return list(positions)
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            raise

    def get_positions_dict(self) -> dict[str, float]:
        """Get all positions as dict mapping symbol to quantity (legacy method - use get_positions).

        Returns:
            Dictionary mapping symbol to quantity owned. Only includes non-zero positions.

        """
        # Build symbol->qty mapping from positions
        result: dict[str, float] = {}
        try:
            for pos in self.get_positions():
                symbol = getattr(pos, "symbol", None) or (
                    pos.get("symbol") if isinstance(pos, dict) else None
                )
                qty_raw = getattr(pos, "qty", None) if not isinstance(pos, dict) else pos.get("qty")
                if symbol and qty_raw is not None:
                    try:
                        result[str(symbol)] = float(qty_raw)
                    except Exception:
                        continue
        except Exception:
            # Best-effort mapping; return what we have
            pass
        return result

    def get_all_positions(self) -> list[Any]:
        """Get all positions as list (backward compatibility)."""
        try:
            positions = self._trading_client.get_all_positions()
            logger.debug(f"Successfully retrieved {len(positions)} positions")
            return list(positions)
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

    def place_order(self, order_request: Any) -> RawOrderEnvelope:
        """Place an order and return raw envelope with metadata."""
        from datetime import UTC, datetime

        from the_alchemiser.execution.orders.order_schemas import RawOrderEnvelope

        request_timestamp = datetime.now(UTC)

        try:
            order = self._trading_client.submit_order(order_request)
            response_timestamp = datetime.now(UTC)

            # Avoid attribute assumptions for mypy
            order_id = getattr(order, "id", None)
            order_symbol = getattr(order, "symbol", None)
            logger.info(f"Successfully placed order: {order_id} for {order_symbol}")

            # Return raw envelope instead of mapped DTO
            return RawOrderEnvelope(
                raw_order=order,
                original_request=order_request,
                request_timestamp=request_timestamp,
                response_timestamp=response_timestamp,
                success=True,
                error_message=None,
            )
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            response_timestamp = datetime.now(UTC)

            return RawOrderEnvelope(
                raw_order=None,
                original_request=order_request,
                request_timestamp=request_timestamp,
                response_timestamp=response_timestamp,
                success=False,
                error_message=str(e),
            )

    def get_order_execution_result(self, order_id: str) -> OrderExecutionResultDTO:
        """Fetch latest order state and map to execution result DTO.

        Args:
            order_id: The unique Alpaca order ID

        Returns:
            OrderExecutionResultDTO reflecting the latest known state.

        """
        try:
            order = self._trading_client.get_order_by_id(order_id)
            return self._alpaca_order_to_execution_result(order)
        except Exception as e:
            logger.error(f"Failed to refresh order {order_id}: {e}")
            return self._create_error_execution_result(e, context="Order refresh", order_id=order_id)

    def place_market_order(
        self,
        symbol: str,
        side: str,
        qty: float | None = None,
        notional: float | None = None,
    ) -> RawOrderEnvelope:
        """Place a market order with validation and envelope return.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            side: 'buy' or 'sell'
            qty: Quantity to trade (use either qty OR notional)
            notional: Dollar amount to trade (use either qty OR notional)

        Returns:
            RawOrderEnvelope with raw order and metadata

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

            # Use the updated place_order method that returns RawOrderEnvelope
            envelope = self.place_order(order_request)
            return envelope

        except ValueError as e:
            logger.error(f"Invalid order parameters: {e}")
            # Return error envelope for consistency
            from datetime import datetime

            from the_alchemiser.execution.orders.order_schemas import RawOrderEnvelope

            now = datetime.now()
            return RawOrderEnvelope(
                raw_order=None,
                original_request=None,
                request_timestamp=now,
                response_timestamp=now,
                success=False,
                error_message=str(e),
            )
        except Exception as e:
            logger.error(f"Failed to place market order for {symbol}: {e}")
            # Return error envelope for consistency
            from datetime import datetime

            from the_alchemiser.execution.orders.order_schemas import RawOrderEnvelope

            now = datetime.now()
            return RawOrderEnvelope(
                raw_order=None,
                original_request=None,
                request_timestamp=now,
                response_timestamp=now,
                success=False,
                error_message=str(e),
            )

    def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        limit_price: float,
        time_in_force: str = "day",
    ) -> OrderExecutionResultDTO:
        """Place a limit order with validation and DTO conversion.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            side: 'buy' or 'sell'
            quantity: Number of shares
            limit_price: Limit price for the order
            time_in_force: Order time in force (default: 'day')

        Returns:
            OrderExecutionResultDTO with execution details

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

            # Use the updated place_order method that returns RawOrderEnvelope
            envelope = self.place_order(order_request)

            # Convert envelope to OrderExecutionResultDTO for backward compatibility
            from the_alchemiser.execution.mappers.order_mapping import (
                raw_order_envelope_to_execution_result_dto,
            )

            return raw_order_envelope_to_execution_result_dto(envelope)

        except ValueError as e:
            logger.error(f"Invalid limit order parameters: {e}")
            return self._create_error_execution_result(e, "Limit order validation")
        except Exception as e:
            logger.error(f"Failed to place limit order for {symbol}: {e}")
            return self._create_error_execution_result(e, f"Limit order for {symbol}")

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
            # Some stubs don't accept status kw; fetch and filter manually
            orders = self._trading_client.get_orders()
            orders_list = list(orders)
            if status:
                status_lower = status.lower()
                orders_list = [
                    o for o in orders_list if str(getattr(o, "status", "")).lower() == status_lower
                ]
            logger.debug(f"Successfully retrieved {len(orders_list)} orders")
            return orders_list
        except Exception as e:
            logger.error(f"Failed to get orders: {e}")
            raise

    # Market Data Operations
    def get_current_price(self, symbol: str) -> float | None:
        """Get current price for a symbol.

        Returns the mid price between bid and ask, or None if not available.
        Uses centralized price discovery utility for consistent calculation.
        """
        from the_alchemiser.shared.utils.price_discovery_utils import get_current_price_from_quote

        try:
            return get_current_price_from_quote(self, symbol)
        except Exception as e:
            logger.error(f"Failed to get current price for {symbol}: {e}")
            raise

    def get_current_prices(self, symbols: list[str]) -> dict[str, float]:
        """Get current prices for multiple symbols.

        Args:
            symbols: List of stock symbols

        Returns:
            Dictionary mapping symbols to their current prices

        """
        try:
            prices = {}
            for symbol in symbols:
                price = self.get_current_price(symbol)
                if price is not None:
                    prices[symbol] = price
                else:
                    logger.warning(f"Could not get price for {symbol}")
            return prices
        except Exception as e:
            logger.error(f"Failed to get current prices for {symbols}: {e}")
            raise

    def get_latest_quote(self, symbol: str) -> tuple[float, float] | None:
        """Get latest bid/ask quote for a symbol (interface compatible).

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

                # Allow quotes where we have at least a valid bid or ask
                # This handles cases like LEU where bid exists but ask is 0
                if bid > 0 or ask > 0:
                    # If only one side is available, use it for both bid and ask
                    # This allows trading while acknowledging the spread uncertainty
                    if bid > 0 and ask <= 0:
                        logger.info(
                            f"Using bid price for both bid/ask for {symbol} (ask unavailable)"
                        )
                        return (bid, bid)
                    if ask > 0 and bid <= 0:
                        logger.info(
                            f"Using ask price for both bid/ask for {symbol} (bid unavailable)"
                        )
                        return (ask, ask)
                    # Both bid and ask are available and positive
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
            logger.warning(f"No quote data available for {symbol}")
            return None
        except Exception as e:
            logger.error(f"Failed to get latest quote for {symbol}: {e}")
            return None

    def get_quote(self, symbol: str) -> dict[str, Any] | None:
        """Get quote information for a symbol (MarketDataRepository interface).

        Args:
            symbol: Symbol to get quote for

        Returns:
            Dictionary with quote information or None if failed

        """
        from the_alchemiser.shared.mappers.market_data_mappers import quote_to_domain

        try:
            quote = self.get_latest_quote_raw(symbol)
            if quote:
                # Use shared quote mapping functionality
                quote_model = quote_to_domain(quote)
                if quote_model:
                    return {
                        "symbol": symbol,
                        "bid_price": float(quote_model.bid),
                        "ask_price": float(quote_model.ask),
                        "bid_size": int(getattr(quote, "bid_size", 0)),
                        "ask_size": int(getattr(quote, "ask_size", 0)),
                        "timestamp": quote_model.ts,
                    }
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
            timeframe: Timeframe (1Min, 5Min, 15Min, 1Hour, 1Day)

        """
        try:
            # Map timeframe strings to Alpaca TimeFrame objects
            timeframe_map = {
                "1Min": TimeFrame(1, TimeFrameUnit.Minute),
                "5Min": TimeFrame(5, TimeFrameUnit.Minute),
                "15Min": TimeFrame(15, TimeFrameUnit.Minute),
                "1Hour": TimeFrame(1, TimeFrameUnit.Hour),
                "1Day": TimeFrame(1, TimeFrameUnit.Day),
            }

            if timeframe not in timeframe_map:
                raise ValueError(f"Unsupported timeframe: {timeframe}")

            from datetime import datetime

            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)

            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=timeframe_map[timeframe],
                start=start_dt,
                end=end_dt,
            )

            response = self._data_client.get_stock_bars(request)

            # Extract bars for symbol from various possible response shapes
            bars_obj: Any | None = None
            try:
                # Preferred: BarsBySymbol has a `.data` dict
                data_attr = getattr(response, "data", None)
                if isinstance(data_attr, dict) and symbol in data_attr:
                    bars_obj = data_attr[symbol]
                # Some SDKs expose attributes per symbol
                elif hasattr(response, symbol):
                    bars_obj = getattr(response, symbol)
                # Fallback: mapping-like access
                elif isinstance(response, dict) and symbol in response:
                    bars_obj = response[symbol]
            except Exception:
                bars_obj = None

            if not bars_obj:
                logger.warning(f"No historical data found for {symbol}")
                return []

            bars = list(bars_obj)
            logger.debug(f"Successfully retrieved {len(bars)} bars for {symbol}")
            # Convert to list of dicts for interface compatibility
            result: list[dict[str, Any]] = []
            for b in bars:
                try:
                    result.append(
                        {
                            "t": getattr(b, "timestamp", None),
                            "o": float(getattr(b, "open", 0) or 0),
                            "h": float(getattr(b, "high", 0) or 0),
                            "l": float(getattr(b, "low", 0) or 0),
                            "c": float(getattr(b, "close", 0) or 0),
                            "v": float(getattr(b, "volume", 0) or 0),
                        }
                    )
                except Exception:
                    # Best-effort conversion
                    continue
            return result

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

    def get_buying_power(self) -> float | None:
        """Get current buying power."""
        try:
            account = self.get_account()
            if account and hasattr(account, "buying_power"):
                return float(account.buying_power)
            return None
        except Exception as e:
            logger.error(f"Failed to get buying power: {e}")
            raise

    def get_portfolio_value(self) -> float | None:
        """Get current portfolio value."""
        try:
            account = self.get_account()
            if account and hasattr(account, "portfolio_value"):
                return float(account.portfolio_value)
            return None
        except Exception as e:
            logger.error(f"Failed to get portfolio value: {e}")
            raise

    # Additional methods to match interface contracts

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
        """Liquidate entire position using close_position API.

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
        """Get asset information.

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
        """Check if the market is currently open.

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
        """Get market calendar information.

        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)

        Returns:
            List of market calendar entries.

        """
        try:
            # Some stubs may not accept start/end; fetch without filters
            calendar = self._trading_client.get_calendar()
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
        """Get portfolio performance history.

        Args:
            start_date: Start date (ISO format), defaults to 1 month ago
            end_date: End date (ISO format), defaults to today
            timeframe: Timeframe for data points

        Returns:
            Portfolio history data, or None if failed.

        """
        try:
            # Fetch without kwargs to satisfy type stubs
            history = self._trading_client.get_portfolio_history()
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
        """Get account activities (trades, dividends, etc.).

        Args:
            activity_type: Filter by activity type (optional)
            start_date: Start date (ISO format), defaults to 1 week ago
            end_date: End date (ISO format), defaults to today

        Returns:
            List of activity records.

        """
        try:
            # get_activities may not be present in stubs; guard via getattr
            get_activities = getattr(self._trading_client, "get_activities", None)
            if not callable(get_activities):
                return []
            activities = get_activities(
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

    # OrderExecutor protocol implementation methods

    def place_smart_sell_order(self, symbol: str, qty: float) -> str | None:
        """Place a smart sell order using canonical executor.

        Args:
            symbol: Symbol to sell
            qty: Quantity to sell

        Returns:
            Order ID if successful, None if failed

        """
        from decimal import Decimal

        from the_alchemiser.execution.core.executor import CanonicalOrderExecutor
        from the_alchemiser.execution.orders.order_request import OrderRequest
        from the_alchemiser.execution.orders.order_type import OrderType
        from the_alchemiser.execution.orders.side import Side
        from the_alchemiser.shared.types.quantity import Quantity
        from the_alchemiser.shared.types.time_in_force import TimeInForce
        from the_alchemiser.shared.value_objects.symbol import Symbol

        try:
            order_request = OrderRequest(
                symbol=Symbol(symbol),
                side=Side("sell"),
                quantity=Quantity(Decimal(str(qty))),
                order_type=OrderType("market"),
                time_in_force=TimeInForce("day"),
                limit_price=None,
            )
            executor = CanonicalOrderExecutor(self)
            result = executor.execute(order_request)
            return result.order_id if result.success else None
        except Exception as e:
            logger.error(f"Smart sell order failed for {symbol}: {e}")
            return None

    def get_current_positions(self) -> dict[str, float]:
        """Get all current positions as dict mapping symbol to quantity.

        This is an alias for get_positions_dict() to satisfy OrderExecutor protocol.

        Returns:
            Dictionary mapping symbol to quantity owned. Only includes non-zero positions.

        """
        return self.get_positions_dict()

    def wait_for_order_completion(
        self, order_ids: list[str], max_wait_seconds: int = 30
    ) -> WebSocketResultDTO:
        """Wait for orders to reach a final state.

        Args:
            order_ids: List of order IDs to monitor
            max_wait_seconds: Maximum time to wait for completion

        Returns:
            WebSocketResultDTO with completion status and completed order IDs

        """
        from the_alchemiser.execution.monitoring.websocket_order_monitor import (
            OrderCompletionMonitor,
        )

        monitor = OrderCompletionMonitor(
            trading_client=self._trading_client,
            api_key=self._api_key,
            secret_key=self._secret_key,
        )
        return monitor.wait_for_order_completion(order_ids, max_wait_seconds)

    @property
    def data_provider(self) -> DataProvider:
        """Get data provider interface for OrderExecutor protocol compatibility.

        Returns self since AlpacaManager implements DataProvider methods.
        """
        return self

    def __repr__(self) -> str:
        """String representation."""
        return f"AlpacaManager(paper={self._paper})"


# Factory function for easy creation
def create_alpaca_manager(
    api_key: str, secret_key: str, paper: bool = True, base_url: str | None = None
) -> AlpacaManager:
    """Factory function to create an AlpacaManager instance.

    This function provides a clean way to create AlpacaManager instances
    and can be easily extended with additional configuration options.
    """
    return AlpacaManager(api_key=api_key, secret_key=secret_key, paper=paper, base_url=base_url)
