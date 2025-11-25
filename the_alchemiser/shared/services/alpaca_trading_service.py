"""Business Unit: shared | Status: current.

Alpaca Trading Service for order operations.

Extracted from AlpacaManager to provide dedicated trading functionality with
proper separation of concerns. Handles all trading operations including order
placement, execution monitoring, and smart execution logic.
"""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Literal

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, QueryOrderStatus, TimeInForce
from alpaca.trading.models import Order
from alpaca.trading.requests import (
    GetOrdersRequest,
    LimitOrderRequest,
    MarketOrderRequest,
    ReplaceOrderRequest,
)

from the_alchemiser.shared.constants import UTC_TIMEZONE_SUFFIX
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.broker import (
    OrderExecutionResult,
    WebSocketResult,
    WebSocketStatus,
)
from the_alchemiser.shared.schemas.execution_report import ExecutedOrder
from the_alchemiser.shared.schemas.operations import OrderCancellationResult
from the_alchemiser.shared.services.circuit_breaker import (
    CircuitBreakerConfig,
    CircuitBreakerError,
    get_circuit_breaker,
)
from the_alchemiser.shared.utils.alpaca_error_handler import AlpacaErrorHandler
from the_alchemiser.shared.utils.order_tracker import OrderTracker

if TYPE_CHECKING:
    from the_alchemiser.shared.services.websocket_manager import (
        WebSocketConnectionManager,
    )

logger = get_logger(__name__)

# Module-level constants for configuration and defaults
MIN_ORDER_PRICE = Decimal("0.01")
MIN_ORDER_QUANTITY = Decimal("0.01")
MIN_TOTAL_VALUE = Decimal("0.01")
POLL_INTERVAL_SECONDS = 0.3
DEFAULT_ORDER_TIMEOUT_SECONDS = 30.0

# Terminal order statuses used for completion detection
TERMINAL_ORDER_STATUSES = {"FILLED", "CANCELED", "REJECTED", "EXPIRED"}
TERMINAL_ORDER_EVENTS = {"fill", "canceled", "rejected", "expired"}
TERMINAL_ORDER_STATUSES_LOWER = {"filled", "canceled", "rejected", "expired"}


class AlpacaTradingService:
    """Service for trading operations using Alpaca API.

    Provides all trading functionality extracted from AlpacaManager including:
    - Order placement (market, limit, smart execution)
    - Order management (cancellation, retrieval, monitoring)
    - WebSocket integration for real-time order updates
    - DTO creation and conversion utilities

    Thread Safety:
        This class is not thread-safe. WebSocket handlers run in async context.
        Order tracking uses thread-safe OrderTracker internally.

    Idempotency:
        Order operations do not automatically deduplicate. Callers should implement
        idempotency keys at the application layer if replay protection is required.
    """

    def __init__(
        self,
        trading_client: TradingClient,
        websocket_manager: WebSocketConnectionManager,
        *,
        paper_trading: bool = True,
    ) -> None:
        """Initialize trading service.

        Args:
            trading_client: Alpaca trading client for API interactions
            websocket_manager: WebSocket manager for real-time order updates
            paper_trading: Whether using paper trading mode (default: True)

        Post-conditions:
            - Trading service is initialized but WebSocket stream is not active
            - Order tracker is ready for order monitoring
            - Service is ready to accept trading requests

        Thread Safety:
            Safe to call from any thread. WebSocket initialization is lazy.

        """
        self._trading_client = trading_client
        self._websocket_manager = websocket_manager
        self._paper_trading = paper_trading

        # Order tracking for WebSocket updates (centralized utility)
        self._order_tracker = OrderTracker()

        # WebSocket trading stream state
        self._trading_service_active = False

        # Initialize circuit breaker for API resilience
        # More conservative settings for trading to avoid missed opportunities
        breaker_config = CircuitBreakerConfig(
            failure_threshold=3,  # Trip after 3 consecutive failures
            success_threshold=2,  # Need 2 successes to recover
            timeout_seconds=30.0,  # Try again after 30 seconds
            half_open_max_calls=1,  # Allow 1 test call in half-open
        )
        self._circuit_breaker = get_circuit_breaker("alpaca_trading", breaker_config)

        logger.debug(
            "AlpacaTradingService initialized",
            paper_trading=paper_trading,
            mode="paper" if paper_trading else "live",
            circuit_breaker="alpaca_trading",
        )

    def cleanup(self) -> None:
        """Release WebSocket resources.

        This method should be called explicitly before service shutdown.
        Safe to call multiple times (idempotent).

        Post-conditions:
            - WebSocket trading stream is released
            - All order tracking events are cleaned up
            - Service can no longer receive order updates

        Raises:
            Logs errors but does not raise exceptions to ensure cleanup completes.

        """
        if self._trading_service_active:
            try:
                self._websocket_manager.release_trading_service()
                self._trading_service_active = False
                logger.debug("AlpacaTradingService WebSocket resources released")
            except Exception as e:
                logger.error(
                    "Error releasing WebSocket resources",
                    error=str(e),
                    error_type=type(e).__name__,
                )

        # Clean up order tracking
        self._order_tracker.cleanup_all()

    @property
    def is_paper_trading(self) -> bool:
        """Check if this is paper trading."""
        return self._paper_trading

    def _normalize_response_to_dict_list(
        self, response: list[object] | dict[str, object] | object
    ) -> list[dict[str, Any]]:
        """Normalize various response formats to consistent list of dicts.

        Args:
            response: Response from Alpaca API (can be list or dict)

        Returns:
            List of dictionaries with normalized response data

        """
        result = []
        if isinstance(response, list):
            for item in response:
                if hasattr(item, "__dict__"):
                    result.append(vars(item))
                elif isinstance(item, dict):
                    result.append(item)
                else:
                    # Fallback: convert to dict representation
                    result.append({"response": str(item)})
        else:
            # Handle dict response
            result = [response] if isinstance(response, dict) else []
        return result

    def place_order(
        self,
        order_request: LimitOrderRequest | MarketOrderRequest,
        *,
        correlation_id: str | None = None,
    ) -> ExecutedOrder:
        """Place an order and return execution details.

        Args:
            order_request: Alpaca order request (market or limit order)
            correlation_id: Optional correlation ID for event tracing

        Returns:
            ExecutedOrder with execution details and status

        Raises:
            Does not raise - returns ExecutedOrder with REJECTED status on failure

        Post-conditions:
            - Order is submitted to Alpaca API
            - Order is tracked via WebSocket for status updates
            - ExecutedOrder DTO is returned with current status

        Side Effects:
            - Ensures WebSocket trading stream is active
            - Registers order with OrderTracker for monitoring

        """
        try:
            self._ensure_trading_stream()

            # Use circuit breaker to protect against cascading failures during outages
            def _submit_order() -> Order:
                return self._trading_client.submit_order(order_request)

            try:
                order = self._circuit_breaker.call(_submit_order)
            except CircuitBreakerError as cbe:
                logger.error(
                    "Circuit breaker blocking order placement - Alpaca API may be degraded",
                    circuit_state=cbe.state.value,
                    failure_count=cbe.failure_count,
                    time_until_reset=cbe.time_until_reset,
                    symbol=getattr(order_request, "symbol", "unknown"),
                    correlation_id=correlation_id,
                )
                return self._create_failed_order_result(order_request, cbe)

            self._track_submitted_order(order)
            return self._create_success_order_result(order, order_request)
        except Exception as e:
            logger.error(
                "Failed to place order",
                error=str(e),
                error_type=type(e).__name__,
                symbol=getattr(order_request, "symbol", "unknown"),
                correlation_id=correlation_id,
            )
            return self._create_failed_order_result(order_request, e)

    def place_market_order(
        self,
        symbol: str,
        side: str,
        qty: float | None = None,
        notional: float | None = None,
        *,
        is_complete_exit: bool = False,
        correlation_id: str | None = None,
    ) -> ExecutedOrder:
        """Place a market order with validation and execution result return.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            side: 'buy' or 'sell'
            qty: Quantity to trade (use either qty OR notional)
            notional: Dollar amount to trade (use either qty OR notional)
            is_complete_exit: If True and side is 'sell', use available quantity
            correlation_id: Optional correlation ID for event tracing

        Returns:
            ExecutedOrder with execution details

        Raises:
            ValueError: If validation fails (via AlpacaErrorHandler)

        Pre-conditions:
            - Either qty or notional must be provided (not both)
            - Symbol must be non-empty
            - Side must be 'buy' or 'sell'
            - Quantities must be positive if provided

        Note:
            is_complete_exit is passed through but not implemented in the trading service
            by design. Position data access should be handled by the calling code (AlpacaManager)
            which calls _adjust_quantity_for_complete_exit() before delegating to this service.
            This maintains proper separation of concerns between trading operations and position management.

        """

        def _place_order() -> ExecutedOrder:
            # Validation
            normalized_symbol, side_normalized = self._validate_market_order_params(
                symbol, side, qty, notional
            )

            # Handle complete exit functionality
            # Note: is_complete_exit is passed through but not implemented in the trading service
            # by design. Position data access should be handled by the calling code (AlpacaManager)
            # which calls _adjust_quantity_for_complete_exit() before delegating to this service.
            # This maintains proper separation of concerns between trading operations and position management.
            final_qty = qty

            # Log warning if is_complete_exit is True but qty wasn't adjusted by caller
            if is_complete_exit and qty:
                logger.debug(
                    "Complete exit requested, using provided quantity",
                    symbol=symbol,
                    qty=qty,
                    note="caller should have adjusted quantity",
                    correlation_id=correlation_id,
                )

            # Create order request
            order_request = MarketOrderRequest(
                symbol=normalized_symbol,
                qty=final_qty,
                notional=notional,
                side=OrderSide.BUY if side_normalized == "buy" else OrderSide.SELL,
                time_in_force=TimeInForce.DAY,
            )

            return self.place_order(order_request, correlation_id=correlation_id)

        return AlpacaErrorHandler.handle_market_order_errors(symbol, side, qty, _place_order)

    def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        limit_price: float,
        time_in_force: str = "day",
        *,
        correlation_id: str | None = None,
    ) -> OrderExecutionResult:
        """Place a limit order and return execution result.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            side: 'buy' or 'sell'
            quantity: Number of shares to trade
            limit_price: Maximum price for buy orders, minimum for sell orders
            time_in_force: Order duration ('day', 'gtc', 'ioc', 'fok')
            correlation_id: Optional correlation ID for event tracing

        Returns:
            OrderExecutionResult with execution details

        Raises:
            ValueError: If validation fails (symbol empty, quantity/price non-positive, invalid side)

        Pre-conditions:
            - Symbol must be non-empty
            - Quantity must be positive
            - Limit price must be positive
            - Side must be 'buy' or 'sell'
            - time_in_force must be valid ('day', 'gtc', 'ioc', 'fok')

        """
        try:
            # Validate inputs
            if not symbol or not symbol.strip():
                raise ValueError("Symbol cannot be empty")
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
            if limit_price <= 0:
                raise ValueError("Limit price must be positive")

            symbol = symbol.strip().upper()
            side = side.strip().lower()
            if side not in ["buy", "sell"]:
                raise ValueError(f"Invalid side: {side}. Must be 'buy' or 'sell'")

            # Map time in force
            tif_mapping = {
                "day": TimeInForce.DAY,
                "gtc": TimeInForce.GTC,
                "ioc": TimeInForce.IOC,
                "fok": TimeInForce.FOK,
            }
            tif = tif_mapping.get(time_in_force.lower(), TimeInForce.DAY)

            # Create limit order request
            order_request = LimitOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
                time_in_force=tif,
                limit_price=limit_price,
            )

            # Submit order
            self._ensure_trading_stream()
            order = self._trading_client.submit_order(order_request)
            self._track_submitted_order(order)
            return self._alpaca_order_to_execution_result(order)

        except Exception as e:
            logger.error(
                "Failed to place limit order",
                symbol=symbol,
                error=str(e),
                error_type=type(e).__name__,
                correlation_id=correlation_id,
            )
            return AlpacaErrorHandler.create_error_result(e, "Limit order placement")

    def cancel_order(
        self, order_id: str, *, correlation_id: str | None = None
    ) -> OrderCancellationResult:
        """Cancel an order by ID.

        Args:
            order_id: Order ID to cancel
            correlation_id: Optional correlation ID for event tracing

        Returns:
            OrderCancellationResult with success status and detailed error information

        Raises:
            Does not raise - returns OrderCancellationResult with success=False on failure

        Note:
            If the order is already in a terminal state (filled, cancelled, etc.),
            this is treated as a successful cancellation.

        """
        try:
            self._trading_client.cancel_order_by_id(order_id)
            logger.info(
                "Cancelled order",
                order_id=order_id,
                correlation_id=correlation_id,
            )
            return OrderCancellationResult(
                success=True,
                error=None,
                order_id=order_id,
            )
        except Exception as e:
            # Check if order is already in a terminal state (filled, cancelled, etc.)
            is_terminal, terminal_error = AlpacaErrorHandler.is_order_already_in_terminal_state(e)

            if is_terminal and terminal_error:
                # This is not really an error - the order already reached a final state
                logger.info(
                    "Order already in terminal state, treating as successful cancellation",
                    order_id=order_id,
                    terminal_state=terminal_error.value,
                    correlation_id=correlation_id,
                )
                return OrderCancellationResult(
                    success=True,
                    error=terminal_error.value,
                    order_id=order_id,
                )

            # Genuine cancellation failure
            logger.error(
                "Failed to cancel order",
                order_id=order_id,
                error=str(e),
                error_type=type(e).__name__,
                correlation_id=correlation_id,
            )
            return OrderCancellationResult(
                success=False,
                error=str(e),
                order_id=order_id,
            )

    def cancel_all_orders(
        self, symbol: str | None = None, *, correlation_id: str | None = None
    ) -> bool:
        """Cancel all orders, optionally filtered by symbol.

        Args:
            symbol: If provided, only cancel orders for this symbol
            correlation_id: Optional correlation ID for event tracing

        Returns:
            True if successful, False otherwise

        Raises:
            Does not raise - returns False on failure

        Side Effects:
            Cancels all open orders (or symbol-filtered orders) via Alpaca API

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
                        self.cancel_order(str(order_id), correlation_id=correlation_id)
            else:
                # Cancel all open orders
                self._trading_client.cancel_orders()

            logger.info(
                "Successfully cancelled orders",
                symbol=symbol if symbol else "all",
                correlation_id=correlation_id,
            )
            return True
        except Exception as e:
            logger.error(
                "Failed to cancel orders",
                error=str(e),
                error_type=type(e).__name__,
                symbol=symbol,
                correlation_id=correlation_id,
            )
            return False

    def replace_order(
        self,
        order_id: str,
        order_data: ReplaceOrderRequest | None = None,
        *,
        correlation_id: str | None = None,
    ) -> OrderExecutionResult:
        """Replace an order with new parameters.

        Args:
            order_id: The unique order ID to replace
            order_data: The parameters to update (quantity, limit_price, etc.).
                       If None, no changes will be made (no-op)
            correlation_id: Optional correlation ID for event tracing

        Returns:
            OrderExecutionResult with the updated order details

        Raises:
            Does not raise - returns OrderExecutionResult with error on failure

        Pre-conditions:
            - order_id must be a valid existing order ID
            - If order_data is provided, it must contain valid update parameters

        """
        try:
            updated_order = self._trading_client.replace_order_by_id(order_id, order_data)
            logger.info(
                "Replaced order",
                order_id=order_id,
                correlation_id=correlation_id,
            )
            return self._alpaca_order_to_execution_result(updated_order)
        except Exception as e:
            logger.error(
                "Failed to replace order",
                order_id=order_id,
                error=str(e),
                error_type=type(e).__name__,
                correlation_id=correlation_id,
            )
            return AlpacaErrorHandler.create_error_result(e, "Order replacement", order_id)

    def get_orders(
        self, status: str | None = None, *, correlation_id: str | None = None
    ) -> list[Order]:
        """Get orders filtered by status.

        Args:
            status: Optional status filter ('open', 'closed', or None for all)
            correlation_id: Optional correlation ID for event tracing

        Returns:
            List of Order objects from Alpaca API

        Raises:
            Does not raise - returns empty list on failure

        Note:
            Returns all orders if status is None or not recognized.

        """
        try:
            if status == "open":
                request = GetOrdersRequest(status=QueryOrderStatus.OPEN)
            elif status == "closed":
                request = GetOrdersRequest(status=QueryOrderStatus.CLOSED)
            else:
                request = GetOrdersRequest()

            orders = self._trading_client.get_orders(request)
            # API can return list or dict, ensure we have a list
            if isinstance(orders, dict):
                return []
            return list(orders)
        except Exception as e:
            logger.error(
                "Failed to get orders",
                error=str(e),
                error_type=type(e).__name__,
                status=status,
                correlation_id=correlation_id,
            )
            return []

    def get_order_execution_result(
        self, order_id: str, *, correlation_id: str | None = None
    ) -> OrderExecutionResult:
        """Fetch latest order state and map to execution result schema.

        Args:
            order_id: The unique Alpaca order ID
            correlation_id: Optional correlation ID for event tracing

        Returns:
            OrderExecutionResult with current order state

        Raises:
            Does not raise - returns OrderExecutionResult with error on failure

        """
        try:
            order = self._trading_client.get_order_by_id(order_id)
            return self._alpaca_order_to_execution_result(order)
        except Exception as e:
            logger.error(
                "Failed to get order execution result",
                order_id=order_id,
                error=str(e),
                error_type=type(e).__name__,
                correlation_id=correlation_id,
            )
            return AlpacaErrorHandler.create_error_result(e, "Order status fetch", order_id)

    def place_smart_sell_order(
        self, symbol: str, qty: float, *, correlation_id: str | None = None
    ) -> str | None:
        """Place a smart sell order using execution logic.

        This method places a market sell order and returns the order ID if successful.
        The "smart" aspect refers to the use of AlpacaErrorHandler for error handling.

        Args:
            symbol: Symbol to sell
            qty: Quantity to sell
            correlation_id: Optional correlation ID for event tracing

        Returns:
            Order ID if successful, None if failed

        Raises:
            Does not raise - returns None on failure

        """
        try:
            # Use the place_market_order method which returns ExecutedOrder
            result = self.place_market_order(symbol, "sell", qty=qty, correlation_id=correlation_id)

            # Check if the order was successful and return order_id
            if result.status not in ["REJECTED", "CANCELED"] and result.order_id:
                return result.order_id
            logger.error(
                "Smart sell order failed for",
                symbol=symbol,
                error_message=result.error_message,
            )
            return None

        except Exception as e:
            logger.error(
                "Smart sell order failed",
                symbol=symbol,
                error=str(e),
                error_type=type(e).__name__,
                correlation_id=correlation_id,
            )
            return None

    def liquidate_position(self, symbol: str, *, correlation_id: str | None = None) -> str | None:
        """Liquidate entire position using close_position API.

        Closes the entire position for the specified symbol by placing a market order
        for the full quantity held.

        Args:
            symbol: Symbol to liquidate
            correlation_id: Optional correlation ID for event tracing

        Returns:
            Order ID if successful, None if failed

        Raises:
            Does not raise - returns None on failure

        Note:
            Uses Alpaca's close_position endpoint which automatically determines
            the correct quantity and side based on current position.

        """
        try:
            order = self._trading_client.close_position(symbol)
            order_id = str(getattr(order, "id", "unknown"))
            logger.info(
                "Successfully liquidated position",
                symbol=symbol,
                order_id=order_id,
                correlation_id=correlation_id,
            )
            return order_id
        except Exception as e:
            logger.error(
                "Failed to liquidate position",
                symbol=symbol,
                error=str(e),
                error_type=type(e).__name__,
                correlation_id=correlation_id,
            )
            return None

    def close_all_positions(
        self, *, cancel_orders: bool = True, correlation_id: str | None = None
    ) -> list[dict[str, Any]]:
        """Liquidate all positions for an account.

        Places an order for each open position to liquidate.

        Args:
            cancel_orders: If True, cancel all open orders before liquidating positions
            correlation_id: Optional correlation ID for event tracing

        Returns:
            List of responses from each closed position containing status and order info

        Raises:
            Does not raise - returns empty list on failure

        Side Effects:
            - Cancels all open orders if cancel_orders=True
            - Places market orders to close all positions

        """
        try:
            logger.info(
                "Closing all positions",
                cancel_orders=cancel_orders,
                correlation_id=correlation_id,
            )
            response = self._trading_client.close_all_positions(cancel_orders=cancel_orders)

            # Convert response to list of dicts for consistent interface
            result = self._normalize_response_to_dict_list(response)

            logger.info(
                "Successfully closed positions",
                count=len(result),
                correlation_id=correlation_id,
            )
            return result
        except Exception as e:
            logger.error(
                "Failed to close all positions",
                error=str(e),
                error_type=type(e).__name__,
                correlation_id=correlation_id,
            )
            return []

    def wait_for_order_completion(
        self,
        order_ids: list[str],
        max_wait_seconds: float = DEFAULT_ORDER_TIMEOUT_SECONDS,
        *,
        correlation_id: str | None = None,
    ) -> WebSocketResult:
        """Wait for orders to reach a final state using TradingStream (with polling fallback).

        Args:
            order_ids: List of order IDs to monitor
            max_wait_seconds: Maximum time to wait for completion (default: 30.0)
            correlation_id: Optional correlation ID for event tracing

        Returns:
            WebSocketResult with completion status and completed order IDs

        Raises:
            Does not raise - returns WebSocketResult with ERROR status on failure

        Side Effects:
            - Ensures WebSocket trading stream is active
            - Polls Alpaca API as fallback if WebSocket doesn't complete
            - Updates internal order tracking state

        Note:
            Uses WebSocket for primary monitoring with polling fallback.
            Sleep interval is POLL_INTERVAL_SECONDS (0.3s) between polls.

        """
        completed_orders: list[str] = []
        start_time = time.time()

        try:
            # Prefer websocket order updates
            completed_orders = self._wait_for_orders_via_ws(order_ids, max_wait_seconds)

            # Fallback to polling for any remaining orders within remaining time
            remaining = [oid for oid in order_ids if oid not in completed_orders]
            if remaining:
                time_left = max(0.0, max_wait_seconds - (time.time() - start_time))
                local_start = time.time()
                while remaining and (time.time() - local_start) < time_left:
                    self._process_pending_orders(remaining, completed_orders)
                    remaining = [oid for oid in remaining if oid not in completed_orders]
                    if remaining:
                        time.sleep(POLL_INTERVAL_SECONDS)

            success = len(completed_orders) == len(order_ids)

            return WebSocketResult(
                status=(WebSocketStatus.COMPLETED if success else WebSocketStatus.TIMEOUT),
                message=f"Completed {len(completed_orders)}/{len(order_ids)} orders",
                completed_order_ids=completed_orders,
                metadata={
                    "total_wait_time": time.time() - start_time,
                    "correlation_id": correlation_id,
                },
            )

        except Exception as e:
            logger.error(
                "Error monitoring order completion",
                error=str(e),
                error_type=type(e).__name__,
                order_count=len(order_ids),
                correlation_id=correlation_id,
            )
            return WebSocketResult(
                status=WebSocketStatus.ERROR,
                message=f"Error monitoring orders: {e}",
                completed_order_ids=completed_orders,
                metadata={"error": str(e), "correlation_id": correlation_id},
            )

    # --- DTO Creation Methods ---

    def _create_success_order_result(
        self,
        order: Order | dict[str, Any],
        order_request: LimitOrderRequest | MarketOrderRequest,
    ) -> ExecutedOrder:
        """Create ExecutedOrder from successful order placement."""
        # Extract basic order attributes
        order_data = self._extract_order_attributes(order)

        logger.info(
            "Successfully placed order",
            order_id=order_data["order_id"],
            symbol=order_data["symbol"],
        )

        # Calculate price and total value
        price = self._calculate_order_price(order_data["filled_avg_price"], order_request)
        total_value = self._calculate_total_value(
            order_data["filled_qty_decimal"], order_data["order_qty_decimal"], price
        )

        return ExecutedOrder(
            order_id=order_data["order_id"],
            symbol=order_data["symbol"],
            action=order_data["action_value"],
            quantity=order_data["order_qty_decimal"],
            filled_quantity=order_data["filled_qty_decimal"],
            price=price,
            total_value=total_value,
            status=order_data["status_value"],
            execution_timestamp=datetime.now(UTC),
        )

    def _create_failed_order_result(
        self, order_request: LimitOrderRequest | MarketOrderRequest, error: Exception
    ) -> ExecutedOrder:
        """Create ExecutedOrder for failed order placement."""
        symbol = getattr(order_request, "symbol", "UNKNOWN")
        action = self._extract_action_from_request(order_request)

        return ExecutedOrder(
            order_id="FAILED",  # Must be non-empty
            symbol=symbol,
            action=action,
            quantity=MIN_ORDER_QUANTITY,  # Must be > 0
            filled_quantity=Decimal("0"),
            price=MIN_ORDER_PRICE,
            total_value=MIN_TOTAL_VALUE,  # Must be > 0
            status="REJECTED",
            execution_timestamp=datetime.now(UTC),
            error_message=str(error),
        )

    def _alpaca_order_to_execution_result(
        self, order: Order | dict[str, Any]
    ) -> OrderExecutionResult:
        """Convert Alpaca order object to OrderExecutionResult."""
        try:
            # Extract basic fields from order object
            order_id_raw = getattr(order, "id", None)
            order_id = str(order_id_raw) if order_id_raw is not None else "unknown"

            # Normalize status to lowercase string to match mapping keys
            status_raw = getattr(order, "status", "unknown")
            status_str = (
                self._extract_enum_value(status_raw).lower()
                if status_raw is not None
                else "accepted"
            )

            filled_qty = Decimal(str(getattr(order, "filled_qty", 0)))

            # Some Alpaca SDK versions expose filled_avg_price instead of avg_fill_price
            avg_price_raw = getattr(order, "avg_fill_price", None)
            if avg_price_raw is None:
                avg_price_raw = getattr(order, "filled_avg_price", None)
            avg_fill_price = Decimal(str(avg_price_raw)) if avg_price_raw is not None else None

            # Simple timestamp handling
            submitted_at = getattr(order, "submitted_at", None) or datetime.now(UTC)
            if isinstance(submitted_at, str):
                # Handle ISO format strings
                submitted_at = datetime.fromisoformat(
                    submitted_at.replace("Z", UTC_TIMEZONE_SUFFIX)
                )

            completed_at = getattr(order, "updated_at", None)
            if completed_at and isinstance(completed_at, str):
                completed_at = datetime.fromisoformat(
                    completed_at.replace("Z", UTC_TIMEZONE_SUFFIX)
                )

            # Map status to our expected values
            status_mapping: dict[
                str,
                Literal["accepted", "filled", "partially_filled", "rejected", "canceled"],
            ] = {
                "new": "accepted",
                "accepted": "accepted",
                "pending_new": "accepted",
                "filled": "filled",
                "partially_filled": "partially_filled",
                "rejected": "rejected",
                "canceled": "canceled",
                "cancelled": "canceled",
                "expired": "rejected",
            }
            mapped_status: Literal[
                "accepted", "filled", "partially_filled", "rejected", "canceled"
            ] = status_mapping.get(status_str, "accepted")

            # CRITICAL: If status is filled/partially_filled but avg_fill_price is None,
            # treat as "accepted" (pending) to avoid validation error. This handles race
            # conditions where Alpaca reports status before price settlement.
            # We must also reset filled_qty to 0 since "accepted" status requires filled_qty == 0.
            if mapped_status in ["filled", "partially_filled"] and avg_fill_price is None:
                logger.warning(
                    "Order marked as filled but avg_fill_price is None - treating as accepted",
                    order_id=order_id,
                    original_status=mapped_status,
                    original_filled_qty=filled_qty,
                )
                mapped_status = "accepted"
                filled_qty = Decimal("0")  # Reset to 0 for "accepted" status validation

            success = mapped_status not in ["rejected", "canceled"]

            return OrderExecutionResult(
                success=success,
                order_id=order_id,
                status=mapped_status,
                filled_qty=filled_qty,
                avg_fill_price=avg_fill_price,
                submitted_at=submitted_at,
                completed_at=completed_at,
                error=None if success else f"Order {status_str}",
            )
        except (ValueError, AttributeError, TypeError) as e:
            logger.error(
                "Failed to convert order to execution result",
                error=str(e),
                error_type=type(e).__name__,
            )
            return AlpacaErrorHandler.create_error_result(e, "Order conversion")
        except Exception as e:
            logger.error(
                "Unexpected error converting order to execution result",
                error=str(e),
                error_type=type(e).__name__,
            )
            return AlpacaErrorHandler.create_error_result(e, "Order conversion")

    # --- Helper Methods ---

    def _extract_order_attributes(self, order: Order | dict[str, Any]) -> dict[str, Any]:
        """Extract attributes from order object safely."""
        order_id = str(getattr(order, "id", ""))
        order_symbol = str(getattr(order, "symbol", ""))
        order_qty = getattr(order, "qty", "0")
        order_filled_qty = getattr(order, "filled_qty", "0")
        order_filled_avg_price = getattr(order, "filled_avg_price", None)
        order_side = getattr(order, "side", "")
        order_status = getattr(order, "status", "SUBMITTED")

        # Extract enum values properly
        action_value = self._extract_enum_value(order_side)
        status_value = self._extract_enum_value(order_status)

        return {
            "order_id": order_id,
            "symbol": order_symbol,
            "filled_avg_price": order_filled_avg_price,
            "filled_qty_decimal": Decimal(str(order_filled_qty)),
            "order_qty_decimal": Decimal(str(order_qty)),
            "action_value": action_value,
            "status_value": status_value,
        }

    def _extract_enum_value(self, enum_obj: object) -> str:
        """Extract string value from enum object safely."""
        return enum_obj.value.upper() if hasattr(enum_obj, "value") else str(enum_obj).upper()

    def _calculate_order_price(
        self,
        filled_avg_price: float | None,
        order_request: LimitOrderRequest | MarketOrderRequest,
    ) -> Decimal:
        """Calculate order price from filled price or request.

        Falls back to MIN_ORDER_PRICE if no price information is available.
        """
        if filled_avg_price:
            return Decimal(str(filled_avg_price))
        if hasattr(order_request, "limit_price") and order_request.limit_price:
            return Decimal(str(order_request.limit_price))
        return MIN_ORDER_PRICE  # Default minimal price

    def _calculate_total_value(
        self, filled_qty_decimal: Decimal, order_qty_decimal: Decimal, price: Decimal
    ) -> Decimal:
        """Calculate total value ensuring positive result for schema validation.

        Uses filled quantity if available, otherwise uses order quantity.
        """
        if filled_qty_decimal > 0:
            return filled_qty_decimal * price
        return order_qty_decimal * price

    def _extract_action_from_request(
        self, order_request: LimitOrderRequest | MarketOrderRequest
    ) -> str:
        """Extract action from order request safely."""
        side = getattr(order_request, "side", None)
        if not side:
            return "BUY"  # Default fallback

        if hasattr(side, "value"):
            return str(side.value).upper()

        side_str = str(side).upper()
        if "SELL" in side_str:
            return "SELL"
        return "BUY"

    def _validate_market_order_params(
        self, symbol: str, side: str, qty: float | None, notional: float | None
    ) -> tuple[str, str]:
        """Validate market order parameters."""
        if not symbol or not symbol.strip():
            raise ValueError("Symbol cannot be empty")

        symbol = symbol.strip().upper()
        side = side.strip().lower()

        if side not in ["buy", "sell"]:
            raise ValueError(f"Invalid side: {side}. Must be 'buy' or 'sell'")

        if qty is None and notional is None:
            raise ValueError("Either qty or notional must be provided")
        if qty is not None and notional is not None:
            raise ValueError("Cannot specify both qty and notional")
        if qty is not None and qty <= 0:
            raise ValueError("Quantity must be positive")
        if notional is not None and notional <= 0:
            raise ValueError("Notional amount must be positive")

        return symbol, side

    # --- WebSocket Integration Methods ---

    def _wait_for_orders_via_ws(self, order_ids: list[str], timeout: float) -> list[str]:
        """Wait for orders to complete using WebSocket updates."""
        try:
            self._ensure_trading_stream()

            # Initialize order tracking
            for order_id in order_ids:
                self._order_tracker.create_event(order_id)
                self._order_tracker.update_order_status(order_id, "pending")

            # Wait for completion with timeout
            completed = []
            start_time = time.time()

            for order_id in order_ids:
                remaining_time = max(0, timeout - (time.time() - start_time))
                if remaining_time <= 0:
                    break

                event_completed = self._order_tracker.wait_for_completion(
                    order_id, timeout=remaining_time
                )
                status = self._order_tracker.get_status(order_id)

                if event_completed or self._order_tracker.is_terminal_status(status):
                    completed.append(order_id)

            return completed

        except Exception as e:
            logger.error(
                "WebSocket order monitoring failed",
                error=str(e),
                error_type=type(e).__name__,
                order_count=len(order_ids),
            )
            return []

    def _track_submitted_order(self, order: Order | dict[str, Any]) -> None:
        """Register submitted orders with the tracker for websocket completion."""
        try:
            order_id: str | None = None
            status_raw: Any = None
            avg_price_raw: Any = None

            if hasattr(order, "id"):
                order_id = str(getattr(order, "id", "") or "")
                status_raw = getattr(order, "status", None)
                avg_price_raw = getattr(order, "filled_avg_price", None)
            elif isinstance(order, dict):
                order_id = str(order.get("id", "") or "")
                status_raw = order.get("status")
                avg_price_raw = order.get("filled_avg_price")

            if not order_id:
                return

            self._order_tracker.create_event(order_id)

            status: str | None = None
            if status_raw is not None:
                status = self._extract_enum_value(status_raw).lower()

            avg_price: Decimal | None = None
            if avg_price_raw is not None:
                avg_price = Decimal(str(avg_price_raw))

            self._order_tracker.update_order_status(order_id, status, avg_price)

            if self._order_tracker.is_terminal_status(status):
                self._order_tracker.signal_completion(order_id)
        except (AttributeError, TypeError, ValueError) as exc:
            logger.debug(
                "Skipping order tracking for submitted order",
                error=str(exc),
                error_type=type(exc).__name__,
            )

    def _ensure_trading_stream(self) -> None:
        """Ensure TradingStream is running via WebSocketConnectionManager.

        Raises:
            Does not raise - logs errors and sets _trading_service_active to False on failure

        Post-conditions:
            - _trading_service_active is set to True if successful, False otherwise
            - WebSocket trading stream is active if successful

        """
        if self._trading_service_active:
            return

        try:
            # Use the websocket manager to get trading stream with order update callback
            if self._websocket_manager.get_trading_service(self._on_trading_update):
                self._trading_service_active = True
                logger.info("TradingStream service activated via WebSocketConnectionManager")
            else:
                logger.error("Failed to activate TradingStream service")
                self._trading_service_active = False
        except Exception as e:
            logger.error(
                "Failed to ensure trading stream",
                error=str(e),
                error_type=type(e).__name__,
            )
            self._trading_service_active = False

    async def _on_trading_update(self, data: object) -> None:
        """Handle order updates from TradingStream.

        Args:
            data: Order update data from TradingStream

        Side Effects:
            - Updates order status in OrderTracker
            - Signals completion for terminal order states

        Note:
            Async method that yields control to event loop. Errors are logged but not raised.

        """
        # Yield control to event loop for proper async behavior
        await asyncio.sleep(0)

        try:
            # Extract event and order information
            event_type, order_id, status = self._extract_trading_update_info(data)

            if not order_id:
                return

            # Update order tracking
            self._order_tracker.update_order_status(order_id, status or event_type or "")

            # Signal completion for terminal events
            if self._is_terminal_trading_event(event_type, status):
                self._order_tracker.signal_completion(order_id)

        except Exception as e:
            logger.error(
                "Error in trading stream update",
                error=str(e),
                error_type=type(e).__name__,
            )

    def _extract_trading_update_info(self, data: object) -> tuple[str, str | None, str | None]:
        """Extract event type, order ID, and status from trading update data.

        Args:
            data: Trading update data (SDK model or dict)

        Returns:
            Tuple of (event_type, order_id, status), with empty/None values on failure

        """
        try:
            # Handle SDK model objects
            if hasattr(data, "event"):
                event_type = str(getattr(data, "event", "")).lower()
                order = getattr(data, "order", None)
                if order:
                    order_id = str(getattr(order, "id", ""))
                    status = str(getattr(order, "status", "")).lower()
                    return event_type, order_id or None, status or None

            # Handle dict payloads
            elif isinstance(data, dict):
                event_type = str(data.get("event", "")).lower()
                order = data.get("order", {})
                if isinstance(order, dict):
                    order_id = str(order.get("id", ""))
                    status = str(order.get("status", "")).lower()
                    return event_type, order_id or None, status or None

            return "", None, None

        except (AttributeError, TypeError, KeyError) as e:
            logger.error(
                "Error extracting trading update info",
                error=str(e),
                error_type=type(e).__name__,
            )
            return "", None, None

    def _is_terminal_trading_event(self, event_type: str, status: str | None) -> bool:
        """Check if event/status indicates terminal order state.

        Uses module-level constants TERMINAL_ORDER_EVENTS and TERMINAL_ORDER_STATUSES_LOWER.
        """
        return event_type in TERMINAL_ORDER_EVENTS or (
            status is not None and status in TERMINAL_ORDER_STATUSES_LOWER
        )

    def _process_pending_orders(self, order_ids: list[str], completed_orders: list[str]) -> None:
        """Check pending orders for completion via polling.

        Args:
            order_ids: List of order IDs to check (modified in-place)
            completed_orders: List to append completed order IDs (modified in-place)

        Side Effects:
            - Removes completed order IDs from order_ids list
            - Appends completed order IDs to completed_orders list

        """
        # Iterate in reverse to safely modify list during iteration
        for i in range(len(order_ids) - 1, -1, -1):
            order_id = order_ids[i]
            try:
                status = self._check_order_completion_status(order_id)
                if status:
                    completed_orders.append(order_id)
                    del order_ids[i]
            except Exception as e:
                logger.error(
                    "Error checking order",
                    order_id=order_id,
                    error=str(e),
                    error_type=type(e).__name__,
                )

    def _check_order_completion_status(self, order_id: str) -> str | None:
        """Check if a single order has reached a final state.

        Args:
            order_id: Order ID to check

        Returns:
            Status string if terminal, None if still pending or on error

        Note:
            Uses module-level constant TERMINAL_ORDER_STATUSES for terminal states.

        """
        try:
            order = self._trading_client.get_order_by_id(order_id)
            order_status = getattr(order, "status", "").upper()

            # Check if order is in a final state (uses module constant)
            if order_status in TERMINAL_ORDER_STATUSES:
                return order_status
            return None

        except Exception as e:
            logger.error(
                "Failed to check order status",
                order_id=order_id,
                error=str(e),
                error_type=type(e).__name__,
            )
            return None
