"""Business Unit: shared | Status: current.

Alpaca broker adapter (moved from execution module for architectural compliance).

This module consolidates scattered Alpaca client usage into a single, well-managed class.
It provides a clean interface that:
1. Reduces scattered imports
2. Adds consistent error handling
3. Uses Pydantic models directly
4. Provides clean domain interfaces

Phase 2 Update: Now implements domain interfaces for type safety and future migration.
Phase 3 Update: Moved to shared module to resolve architectural boundary violations.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Literal

# Type checking imports to avoid circular dependencies
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import LimitOrderRequest, MarketOrderRequest

from the_alchemiser.shared.dto.broker_dto import (
    OrderExecutionResult,
    WebSocketResult,
    WebSocketStatus,
)
from the_alchemiser.shared.dto.execution_report_dto import ExecutedOrderDTO
from the_alchemiser.shared.protocols.repository import (
    AccountRepository,
    MarketDataRepository,
    TradingRepository,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


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

    @property
    def trading_client(self) -> Any:
        """Access to underlying trading client for backward compatibility."""
        return self._trading_client

    # Helper methods for DTO mapping
    def _alpaca_order_to_execution_result(self, order: Any) -> OrderExecutionResult:
        """Convert Alpaca order object to OrderExecutionResult.

        Simple implementation that avoids circular imports.
        """
        try:
            # Extract basic fields from order object
            order_id = getattr(order, "id", "unknown")
            status = getattr(order, "status", "unknown")
            filled_qty = Decimal(str(getattr(order, "filled_qty", 0)))
            avg_fill_price = getattr(order, "avg_fill_price", None)
            if avg_fill_price is not None:
                avg_fill_price = Decimal(str(avg_fill_price))

            # Simple timestamp handling
            submitted_at = getattr(order, "submitted_at", None) or datetime.now(UTC)
            if isinstance(submitted_at, str):
                # Handle ISO format strings
                submitted_at = datetime.fromisoformat(submitted_at.replace("Z", "+00:00"))

            completed_at = getattr(order, "updated_at", None)
            if completed_at and isinstance(completed_at, str):
                completed_at = datetime.fromisoformat(completed_at.replace("Z", "+00:00"))

            # Map status to our expected values - using explicit typing to ensure Literal compliance
            status_mapping: dict[str, Literal["accepted", "filled", "partially_filled", "rejected", "canceled"]] = {
                "new": "accepted",
                "accepted": "accepted",
                "filled": "filled",
                "partially_filled": "partially_filled",
                "rejected": "rejected",
                "canceled": "canceled",
                "cancelled": "canceled",
                "expired": "rejected",
            }
            mapped_status: Literal["accepted", "filled", "partially_filled", "rejected", "canceled"] = status_mapping.get(status, "accepted")

            success = mapped_status not in ["rejected", "canceled"]

            return OrderExecutionResult(
                success=success,
                order_id=order_id,
                status=mapped_status,
                filled_qty=filled_qty,
                avg_fill_price=avg_fill_price,
                submitted_at=submitted_at,
                completed_at=completed_at,
                error=None if success else f"Order {status}",
            )
        except Exception as e:
            logger.error(f"Failed to convert order to execution result: {e}")
            return self._create_error_execution_result(e, "Order conversion")

    def _create_error_execution_result(
        self, error: Exception, context: str = "Operation", order_id: str = "unknown"
    ) -> OrderExecutionResult:
        """Create an error OrderExecutionResult."""
        status: Literal["accepted", "filled", "partially_filled", "rejected", "canceled"] = "rejected"
        return OrderExecutionResult(
            success=False,
            order_id=order_id,
            status=status,
            filled_qty=Decimal("0"),
            avg_fill_price=None,
            submitted_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
            error=f"{context} failed: {error!s}",
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
        """Get all positions as dict mapping symbol to quantity.

        Returns:
            Dictionary mapping symbol to quantity owned. Only includes non-zero positions.

        """
        # Build symbol->qty mapping from positions
        # Use qty_available to account for shares tied up in open orders
        result: dict[str, float] = {}
        try:
            for pos in self.get_positions():
                symbol = getattr(pos, "symbol", None) or (
                    pos.get("symbol") if isinstance(pos, dict) else None
                )
                # Use qty_available if available, fallback to qty for compatibility
                qty_available = (
                    getattr(pos, "qty_available", None)
                    if not isinstance(pos, dict)
                    else pos.get("qty_available")
                )
                if qty_available is not None:
                    qty_raw = qty_available
                else:
                    # Fallback to total qty if qty_available is not available
                    qty_raw = (
                        getattr(pos, "qty", None) if not isinstance(pos, dict) else pos.get("qty")
                    )

                if symbol and qty_raw is not None:
                    try:
                        result[str(symbol)] = float(qty_raw)
                    except Exception:
                        continue
        except Exception:
            # Best-effort mapping; return what we have
            pass
        return result

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

    def place_order(self, order_request: Any) -> ExecutedOrderDTO:
        """Place an order and return execution details."""
        try:
            order = self._trading_client.submit_order(order_request)

            # Avoid attribute assumptions for mypy
            order_id = str(getattr(order, "id", ""))
            order_symbol = str(getattr(order, "symbol", ""))
            order_qty = getattr(order, "qty", "0")
            order_filled_qty = getattr(order, "filled_qty", "0")
            order_filled_avg_price = getattr(order, "filled_avg_price", None)
            order_side = getattr(order, "side", "")
            order_status = getattr(order, "status", "SUBMITTED")

            logger.info(f"Successfully placed order: {order_id} for {order_symbol}")

            # Handle price - use filled_avg_price if available, otherwise estimate
            price = Decimal("0.01")  # Default minimal price
            if order_filled_avg_price:
                price = Decimal(str(order_filled_avg_price))
            elif hasattr(order_request, "limit_price") and order_request.limit_price:
                price = Decimal(str(order_request.limit_price))

            # Extract enum values properly
            action_value = (
                order_side.value.upper()
                if hasattr(order_side, "value")
                else str(order_side).upper()
            )
            status_value = (
                order_status.value.upper()
                if hasattr(order_status, "value")
                else str(order_status).upper()
            )

            # Calculate total_value: use filled_quantity if > 0, otherwise use order quantity
            # This ensures total_value > 0 for DTO validation even for unfilled orders
            filled_qty_decimal = Decimal(str(order_filled_qty))
            order_qty_decimal = Decimal(str(order_qty))
            if filled_qty_decimal > 0:
                total_value = filled_qty_decimal * price
            else:
                total_value = order_qty_decimal * price

            return ExecutedOrderDTO(
                order_id=order_id,
                symbol=order_symbol,
                action=action_value,
                quantity=order_qty_decimal,
                filled_quantity=filled_qty_decimal,
                price=price,
                total_value=total_value,
                status=status_value,
                execution_timestamp=datetime.now(UTC),
            )
        except Exception as e:
            logger.error(f"Failed to place order: {e}")

            # Return a failed order DTO with valid values
            symbol = getattr(order_request, "symbol", "UNKNOWN")
            side = getattr(order_request, "side", None)

            # Extract action from order request
            action = "BUY"  # Default fallback
            if side:
                if hasattr(side, "value"):
                    action = side.value.upper()
                else:
                    side_str = str(side).upper()
                    if "SELL" in side_str:
                        action = "SELL"
                    elif "BUY" in side_str:
                        action = "BUY"

            return ExecutedOrderDTO(
                order_id="FAILED",  # Must be non-empty
                symbol=symbol,
                action=action,
                quantity=Decimal("0.01"),  # Must be > 0
                filled_quantity=Decimal("0"),
                price=Decimal("0.01"),
                total_value=Decimal("0.01"),  # Must be > 0
                status="REJECTED",
                execution_timestamp=datetime.now(UTC),
                error_message=str(e),
            )

    def get_order_execution_result(self, order_id: str) -> OrderExecutionResult:
        """Fetch latest order state and map to execution result DTO.

        Args:
            order_id: The unique Alpaca order ID

        Returns:
            OrderExecutionResult reflecting the latest known state.

        """
        try:
            order = self._trading_client.get_order_by_id(order_id)
            return self._alpaca_order_to_execution_result(order)
        except Exception as e:
            logger.error(f"Failed to refresh order {order_id}: {e}")
            return self._create_error_execution_result(
                e, context="Order refresh", order_id=order_id
            )

    def _validate_market_order_params(
        self, symbol: str, side: str, qty: float | None, notional: float | None
    ) -> tuple[str, str]:
        """Validate market order parameters.

        Args:
            symbol: Stock symbol
            side: 'buy' or 'sell'
            qty: Quantity to trade
            notional: Dollar amount to trade

        Returns:
            Tuple of (normalized_symbol, normalized_side)

        Raises:
            ValueError: If validation fails

        """
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

        return symbol.upper(), side_normalized

    def _adjust_quantity_for_complete_exit(
        self, symbol: str, side: str, qty: float | None, is_complete_exit: bool
    ) -> float | None:
        """Adjust quantity for complete exit if needed.

        Args:
            symbol: Stock symbol
            side: Order side
            qty: Original quantity
            is_complete_exit: Whether this is a complete exit

        Returns:
            Adjusted quantity or original quantity

        """
        if not (is_complete_exit and side == "sell" and qty is not None):
            return qty

        try:
            position = self.get_position(symbol)
            if not position:
                return qty
            # Use qty_available if available, fallback to qty
            available_qty = getattr(position, "qty_available", None)
            if available_qty is not None:
                final_qty = float(available_qty)
                logger.info(
                    f"Complete exit detected for {symbol}: using Alpaca's available quantity "
                    f"{final_qty} instead of calculated {qty}"
                )
                return final_qty

            # Fallback to total qty if qty_available not available
            total_qty = getattr(position, "qty", None)
            if total_qty is not None:
                final_qty = float(total_qty)
                logger.info(
                    f"Complete exit detected for {symbol}: using total quantity "
                    f"{final_qty} instead of calculated {qty}"
                )
                return final_qty
        except Exception as e:
            logger.warning(f"Failed to get position for complete exit of {symbol}: {e}")

        return qty

    def _create_error_dto(
        self, order_id: str, symbol: str, side: str, qty: float | None, error_message: str
    ) -> ExecutedOrderDTO:
        """Create error ExecutedOrderDTO for failed orders.

        Args:
            order_id: Error order ID
            symbol: Stock symbol
            side: Order side
            qty: Order quantity
            error_message: Error description

        Returns:
            ExecutedOrderDTO with error details

        """
        return ExecutedOrderDTO(
            order_id=order_id,
            symbol=symbol.upper() if symbol else "UNKNOWN",
            action=side.upper() if side and side.upper() in ["BUY", "SELL"] else "BUY",
            quantity=Decimal(str(qty)) if qty and qty > 0 else Decimal("0.01"),
            filled_quantity=Decimal("0"),
            price=Decimal("0.01"),
            total_value=Decimal("0.01"),  # Must be > 0
            status="REJECTED",
            execution_timestamp=datetime.now(UTC),
            error_message=error_message,
        )

    def place_market_order(
        self,
        symbol: str,
        side: str,
        qty: float | None = None,
        notional: float | None = None,
        is_complete_exit: bool = False,
    ) -> ExecutedOrderDTO:
        """Place a market order with validation and execution result return.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            side: 'buy' or 'sell'
            qty: Quantity to trade (use either qty OR notional)
            notional: Dollar amount to trade (use either qty OR notional)
            is_complete_exit: If True and side is 'sell', use Alpaca's available quantity

        Returns:
            ExecutedOrderDTO with execution details

        """
        try:
            # Validation
            normalized_symbol, side_normalized = self._validate_market_order_params(
                symbol, side, qty, notional
            )

            # Adjust quantity for complete exits
            final_qty = self._adjust_quantity_for_complete_exit(
                normalized_symbol, side_normalized, qty, is_complete_exit
            )

            # Create order request
            order_request = MarketOrderRequest(
                symbol=normalized_symbol,
                qty=final_qty,
                notional=notional,
                side=OrderSide.BUY if side_normalized == "buy" else OrderSide.SELL,
                time_in_force=TimeInForce.DAY,
            )

            # Use the updated place_order method that returns ExecutedOrderDTO
            return self.place_order(order_request)

        except ValueError as e:
            logger.error(f"Invalid order parameters: {e}")
            return self._create_error_dto("INVALID", symbol, side, qty, str(e))
        except Exception as e:
            logger.error(f"Failed to place market order for {symbol}: {e}")
            return self._create_error_dto("FAILED", symbol, side, qty, str(e))

    def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        limit_price: float,
        time_in_force: str = "day",
    ) -> OrderExecutionResult:
        """Place a limit order with validation and DTO conversion.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            side: 'buy' or 'sell'
            quantity: Number of shares
            limit_price: Limit price for the order
            time_in_force: Order time in force (default: 'day')

        Returns:
            OrderExecutionResult with execution details

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

            # Use the updated place_order method that returns ExecutedOrderDTO
            executed_order_dto = self.place_order(order_request)

            # Convert ExecutedOrderDTO to OrderExecutionResult
            # Map ExecutedOrderDTO status to OrderExecutionResult Literal status
            dto_status_to_result_status: dict[str, Literal["accepted", "filled", "partially_filled", "rejected", "canceled"]] = {
                "FILLED": "filled",
                "PARTIAL": "partially_filled", 
                "REJECTED": "rejected",
                "CANCELLED": "canceled",
                "CANCELED": "canceled",
                "PENDING": "accepted",
                "FAILED": "rejected",
                "ACCEPTED": "accepted",
            }
            
            result_status: Literal["accepted", "filled", "partially_filled", "rejected", "canceled"] = dto_status_to_result_status.get(
                executed_order_dto.status.upper(), "accepted"
            )
            
            success = result_status not in ["rejected", "canceled"]
            
            return OrderExecutionResult(
                success=success,
                order_id=executed_order_dto.order_id,
                status=result_status,
                filled_qty=executed_order_dto.filled_quantity,
                avg_fill_price=executed_order_dto.price if executed_order_dto.filled_quantity > 0 else None,
                submitted_at=executed_order_dto.execution_timestamp,
                completed_at=executed_order_dto.execution_timestamp if success else None,
                error=executed_order_dto.error_message if not success else None,
            )

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

        TODO: Consider migrating callers to use structured pricing types:
        - RealTimePricingService.get_quote_data() for bid/ask spreads with market depth
        - RealTimePricingService.get_price_data() for volume and enhanced trade data
        - Enhanced price discovery with QuoteModel and PriceDataModel
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
        """Get latest bid/ask quote for a symbol.

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

    def get_quote(self, symbol: str) -> dict[str, Any] | None:
        """Get quote information for a symbol (MarketDataRepository interface).

        Args:
            symbol: Symbol to get quote for

        Returns:
            Dictionary with quote information or None if failed

        """
        try:
            request = StockLatestQuoteRequest(symbol_or_symbols=[symbol])
            quotes = self._data_client.get_stock_latest_quote(request)
            quote = quotes.get(symbol)

            if quote:
                # Use Pydantic model_dump() for consistent field names
                quote_dict = quote.model_dump()
                # Ensure we have symbol in the output
                quote_dict["symbol"] = symbol
                return quote_dict
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

        Returns:
            List of dictionaries with bar data using Pydantic model field names

        """
        try:
            # Map timeframe strings to Alpaca TimeFrame objects (case-insensitive)
            timeframe_map = {
                "1min": TimeFrame(1, TimeFrameUnit.Minute),
                "5min": TimeFrame(5, TimeFrameUnit.Minute),
                "15min": TimeFrame(15, TimeFrameUnit.Minute),
                "1hour": TimeFrame(1, TimeFrameUnit.Hour),
                "1day": TimeFrame(1, TimeFrameUnit.Day),
            }

            timeframe_lower = timeframe.lower()
            if timeframe_lower not in timeframe_map:
                raise ValueError(f"Unsupported timeframe: {timeframe}")

            from datetime import datetime

            start_dt = datetime.fromisoformat(start_date)
            end_dt = datetime.fromisoformat(end_date)

            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=timeframe_map[timeframe_lower],
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

            # Use Pydantic model_dump() to get proper dictionaries with full field names
            result: list[dict[str, Any]] = []
            for bar in bars:
                try:
                    # Alpaca SDK uses Pydantic models, use model_dump()
                    bar_dict = bar.model_dump()
                    result.append(bar_dict)
                except Exception as e:
                    logger.warning(f"Failed to convert bar for {symbol}: {e}")
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
            # Convert to dictionary
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
            # Convert to list of dictionaries
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
            # Convert to dictionary
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
            # Convert to list of dictionaries
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
        """Place a smart sell order using execution manager.

        Args:
            symbol: Symbol to sell
            qty: Quantity to sell

        Returns:
            Order ID if successful, None if failed

        """
        try:
            # Use the place_market_order method which now returns ExecutedOrderDTO
            result = self.place_market_order(symbol, "sell", qty=qty)

            # Check if the order was successful and return order_id
            if result.status not in ["REJECTED", "CANCELED"] and result.order_id:
                return result.order_id
            logger.error(f"Smart sell order failed for {symbol}: {result.error_message}")
            return None

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

    def _check_order_completion_status(self, order_id: str) -> str | None:
        """Check if a single order has reached a final state.

        Args:
            order_id: The order ID to check

        Returns:
            Order status if completed, None if still pending or error occurred

        """
        try:
            order = self._trading_client.get_order_by_id(order_id)
            order_status = getattr(order, "status", "").upper()

            # Check if order is in a final state
            if order_status in ["FILLED", "CANCELED", "REJECTED", "EXPIRED"]:
                return order_status
            return None
        except Exception as e:
            logger.warning(f"Failed to check order {order_id} status: {e}")
            return None

    def _process_pending_orders(self, order_ids: list[str], completed_orders: list[str]) -> None:
        """Process pending orders and update completed_orders list.

        Args:
            order_ids: All order IDs to monitor
            completed_orders: List of completed order IDs (modified in place)

        """
        for order_id in order_ids:
            if order_id not in completed_orders:
                final_status = self._check_order_completion_status(order_id)
                if final_status:
                    completed_orders.append(order_id)
                    logger.info(f"Order {order_id} completed with status: {final_status}")

    def _should_continue_waiting(
        self,
        completed_orders: list[str],
        order_ids: list[str],
        start_time: float,
        max_wait_seconds: int,
    ) -> bool:
        """Check if we should continue waiting for order completion.

        Args:
            completed_orders: List of completed order IDs
            order_ids: All order IDs being monitored
            start_time: When monitoring started
            max_wait_seconds: Maximum wait time

        Returns:
            True if should continue waiting, False otherwise

        """
        import time

        return (
            len(completed_orders) < len(order_ids) and (time.time() - start_time) < max_wait_seconds
        )

    def wait_for_order_completion(
        self, order_ids: list[str], max_wait_seconds: int = 30
    ) -> WebSocketResult:
        """Wait for orders to reach a final state using polling.

        Args:
            order_ids: List of order IDs to monitor
            max_wait_seconds: Maximum time to wait for completion

        Returns:
            WebSocketResult with completion status and completed order IDs

        """
        import time

        completed_orders: list[str] = []
        start_time = time.time()

        try:
            while self._should_continue_waiting(
                completed_orders, order_ids, start_time, max_wait_seconds
            ):
                self._process_pending_orders(order_ids, completed_orders)

                # Sleep briefly between checks to avoid hammering the API
                if len(completed_orders) < len(order_ids):
                    time.sleep(0.5)

            success = len(completed_orders) == len(order_ids)

            return WebSocketResult(
                status=WebSocketStatus.COMPLETED if success else WebSocketStatus.TIMEOUT,
                message=f"Completed {len(completed_orders)}/{len(order_ids)} orders",
                completed_order_ids=completed_orders,
                metadata={"total_wait_time": time.time() - start_time},
            )

        except Exception as e:
            logger.error(f"Error monitoring order completion: {e}")
            return WebSocketResult(
                status=WebSocketStatus.ERROR,
                message=f"Error monitoring orders: {e}",
                completed_order_ids=completed_orders,
                metadata={"error": str(e)},
            )

    # Note: MarketDataPort implementation removed to avoid protocol compliance issues
    # AlpacaManager provides market data functionality through direct methods
    # without implementing the full MarketDataPort protocol

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
