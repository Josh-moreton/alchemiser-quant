"""Business Unit: shared | Status: current.

Alpaca Trading Service for order operations.

Extracted from AlpacaManager to provide dedicated trading functionality with
proper separation of concerns. Handles all trading operations including order
placement, execution monitoring, and smart execution logic.
"""

from __future__ import annotations

import logging
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
)

from the_alchemiser.shared.constants import UTC_TIMEZONE_SUFFIX
from the_alchemiser.shared.dto.broker_dto import (
    OrderExecutionResult,
    WebSocketResult,
    WebSocketStatus,
)
from the_alchemiser.shared.dto.execution_report_dto import ExecutedOrderDTO
from the_alchemiser.shared.utils.alpaca_error_handler import AlpacaErrorHandler
from the_alchemiser.shared.utils.order_tracker import OrderTracker

if TYPE_CHECKING:
    from the_alchemiser.shared.services.websocket_manager import (
        WebSocketConnectionManager,
    )

logger = logging.getLogger(__name__)


class AlpacaTradingService:
    """Service for trading operations using Alpaca API.

    Provides all trading functionality extracted from AlpacaManager including:
    - Order placement (market, limit, smart execution)
    - Order management (cancellation, retrieval, monitoring)
    - WebSocket integration for real-time order updates
    - DTO creation and conversion utilities
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
            trading_client: Alpaca trading client
            websocket_manager: WebSocket manager for order updates
            paper_trading: Whether using paper trading mode

        """
        self._trading_client = trading_client
        self._websocket_manager = websocket_manager
        self._paper_trading = paper_trading

        # Order tracking for WebSocket updates (centralized utility)
        self._order_tracker = OrderTracker()

        # WebSocket trading stream state
        self._trading_service_active = False

        logger.info(f"🏪 AlpacaTradingService initialized ({'paper' if paper_trading else 'live'})")

    def __del__(self) -> None:
        """Cleanup WebSocket resources when service is garbage collected."""
        self.cleanup()

    def cleanup(self) -> None:
        """Release WebSocket resources."""
        if self._trading_service_active:
            try:
                self._websocket_manager.release_trading_service()
                self._trading_service_active = False
                logger.debug("🧹 AlpacaTradingService WebSocket resources released")
            except Exception as e:
                logger.error(f"Error releasing WebSocket resources: {e}")

        # Clean up order tracking
        self._order_tracker.cleanup_all()

    @property
    def is_paper_trading(self) -> bool:
        """Check if this is paper trading."""
        return self._paper_trading

    def place_order(
        self, order_request: LimitOrderRequest | MarketOrderRequest
    ) -> ExecutedOrderDTO:
        """Place an order and return execution details."""
        try:
            self._ensure_trading_stream()
            order = self._trading_client.submit_order(order_request)
            self._track_submitted_order(order)
            return self._create_success_order_dto(order, order_request)
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            return self._create_failed_order_dto(order_request, e)

    def place_market_order(
        self,
        symbol: str,
        side: str,
        qty: float | None = None,
        notional: float | None = None,
        *,
        is_complete_exit: bool = False,
    ) -> ExecutedOrderDTO:
        """Place a market order with validation and execution result return.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            side: 'buy' or 'sell'
            qty: Quantity to trade (use either qty OR notional)
            notional: Dollar amount to trade (use either qty OR notional)
            is_complete_exit: If True and side is 'sell', use available quantity

        Returns:
            ExecutedOrderDTO with execution details

        """
        try:
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
                    f"Complete exit requested for {symbol}, using provided qty={qty} (caller should have adjusted)"
                )

            # Create order request
            order_request = MarketOrderRequest(
                symbol=normalized_symbol,
                qty=final_qty,
                notional=notional,
                side=OrderSide.BUY if side_normalized == "buy" else OrderSide.SELL,
                time_in_force=TimeInForce.DAY,
            )

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
        """Place a limit order and return execution result.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            side: 'buy' or 'sell'
            quantity: Number of shares to trade
            limit_price: Maximum price for buy orders, minimum for sell orders
            time_in_force: Order duration ('day', 'gtc', 'ioc', 'fok')

        Returns:
            OrderExecutionResult with execution details

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
            logger.error(f"Failed to place limit order for {symbol}: {e}")
            return AlpacaErrorHandler.create_error_result(e, "Limit order placement")

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order by ID.

        Args:
            order_id: Order ID to cancel

        Returns:
            True if successful, False otherwise

        """
        try:
            self._trading_client.cancel_order_by_id(order_id)
            logger.info(f"Cancelled order: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            return False

    def get_orders(self, status: str | None = None) -> list[Any]:
        """Get orders filtered by status.

        Args:
            status: Optional status filter (e.g., 'open', 'closed', 'all')

        Returns:
            List of order objects

        """
        try:
            if status == "open":
                request = GetOrdersRequest(status=QueryOrderStatus.OPEN)
            elif status == "closed":
                request = GetOrdersRequest(status=QueryOrderStatus.CLOSED)
            else:
                request = GetOrdersRequest()

            orders = self._trading_client.get_orders(request)
            return list(orders)
        except Exception as e:
            logger.error(f"Failed to get orders: {e}")
            return []

    def get_order_execution_result(self, order_id: str) -> OrderExecutionResult:
        """Fetch latest order state and map to execution result DTO.

        Args:
            order_id: The unique Alpaca order ID

        Returns:
            OrderExecutionResult with current order state

        """
        try:
            order = self._trading_client.get_order_by_id(order_id)
            return self._alpaca_order_to_execution_result(order)
        except Exception as e:
            logger.error(f"Failed to get order execution result for {order_id}: {e}")
            return AlpacaErrorHandler.create_error_result(e, "Order status fetch", order_id)

    def place_smart_sell_order(self, symbol: str, qty: float) -> str | None:
        """Place a smart sell order using execution logic.

        Args:
            symbol: Symbol to sell
            qty: Quantity to sell

        Returns:
            Order ID if successful, None if failed

        """
        try:
            # Use the place_market_order method which returns ExecutedOrderDTO
            result = self.place_market_order(symbol, "sell", qty=qty)

            # Check if the order was successful and return order_id
            if result.status not in ["REJECTED", "CANCELED"] and result.order_id:
                return result.order_id
            logger.error(f"Smart sell order failed for {symbol}: {result.error_message}")
            return None

        except Exception as e:
            logger.error(f"Smart sell order failed for {symbol}: {e}")
            return None

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

    def wait_for_order_completion(
        self, order_ids: list[str], max_wait_seconds: int = 30
    ) -> WebSocketResult:
        """Wait for orders to reach a final state using TradingStream (with polling fallback).

        Args:
            order_ids: List of order IDs to monitor
            max_wait_seconds: Maximum time to wait for completion

        Returns:
            WebSocketResult with completion status and completed order IDs

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
                        time.sleep(0.3)

            success = len(completed_orders) == len(order_ids)

            return WebSocketResult(
                status=(WebSocketStatus.COMPLETED if success else WebSocketStatus.TIMEOUT),
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

    # --- DTO Creation Methods ---

    def _create_success_order_dto(
        self,
        order: Order | dict[str, Any],
        order_request: LimitOrderRequest | MarketOrderRequest,
    ) -> ExecutedOrderDTO:
        """Create ExecutedOrderDTO from successful order placement."""
        # Extract basic order attributes
        order_data = self._extract_order_attributes(order)

        logger.info(
            f"Successfully placed order: {order_data['order_id']} for {order_data['symbol']}"
        )

        # Calculate price and total value
        price = self._calculate_order_price(order_data["filled_avg_price"], order_request)
        total_value = self._calculate_total_value(
            order_data["filled_qty_decimal"], order_data["order_qty_decimal"], price
        )

        return ExecutedOrderDTO(
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

    def _create_failed_order_dto(
        self, order_request: LimitOrderRequest | MarketOrderRequest, error: Exception
    ) -> ExecutedOrderDTO:
        """Create ExecutedOrderDTO for failed order placement."""
        symbol = getattr(order_request, "symbol", "UNKNOWN")
        action = self._extract_action_from_request(order_request)

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
            error_message=str(error),
        )

    def _create_error_dto(
        self, order_id: str, symbol: str, side: str, qty: float | None, error: str
    ) -> ExecutedOrderDTO:
        """Create error ExecutedOrderDTO for validation failures."""
        return ExecutedOrderDTO(
            order_id=order_id,
            symbol=symbol,
            action=side.upper(),
            quantity=Decimal(str(qty)) if qty else Decimal("0.01"),
            filled_quantity=Decimal("0"),
            price=Decimal("0.01"),
            total_value=Decimal("0.01"),
            status="REJECTED",
            execution_timestamp=datetime.now(UTC),
            error_message=error,
        )

    def _alpaca_order_to_execution_result(
        self, order: Order | dict[str, Any]
    ) -> OrderExecutionResult:
        """Convert Alpaca order object to OrderExecutionResult."""
        try:
            # Extract basic fields from order object
            order_id_raw = getattr(order, "id", None)
            order_id = str(order_id_raw) if order_id_raw is not None else "unknown"
            status = getattr(order, "status", "unknown")
            filled_qty = Decimal(str(getattr(order, "filled_qty", 0)))
            avg_fill_price = getattr(order, "avg_fill_price", None)
            if avg_fill_price is not None:
                avg_fill_price = Decimal(str(avg_fill_price))

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
            ] = status_mapping.get(status, "accepted")

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
        """Calculate order price from filled price or request."""
        if filled_avg_price:
            return Decimal(str(filled_avg_price))
        if hasattr(order_request, "limit_price") and order_request.limit_price:
            return Decimal(str(order_request.limit_price))
        return Decimal("0.01")  # Default minimal price

    def _calculate_total_value(
        self, filled_qty_decimal: Decimal, order_qty_decimal: Decimal, price: Decimal
    ) -> Decimal:
        """Calculate total value ensuring positive result for DTO validation."""
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
            logger.error(f"WebSocket order monitoring failed: {e}")
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
        except Exception as exc:
            logger.debug(f"Skipping order tracking for submitted order: {exc}")

    def _ensure_trading_stream(self) -> None:
        """Ensure TradingStream is running via WebSocketConnectionManager."""
        if self._trading_service_active:
            return

        try:
            # Use the websocket manager to get trading stream with order update callback
            if self._websocket_manager.get_trading_service(self._on_trading_update):
                self._trading_service_active = True
                logger.info("✅ TradingStream service activated via WebSocketConnectionManager")
            else:
                logger.error("❌ Failed to activate TradingStream service")
                self._trading_service_active = False
        except Exception as e:
            logger.error(f"Failed to ensure trading stream: {e}")
            self._trading_service_active = False

    async def _on_trading_update(self, data: object) -> None:
        """Handle order updates from TradingStream.

        Args:
            data: Order update data from TradingStream

        """
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
            logger.error(f"Error in trading stream update: {e}")

    def _extract_trading_update_info(self, data: object) -> tuple[str, str | None, str | None]:
        """Extract event type, order ID, and status from trading update data."""
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

        except Exception as e:
            logger.error(f"Error extracting trading update info: {e}")
            return "", None, None

    def _is_terminal_trading_event(self, event_type: str, status: str | None) -> bool:
        """Check if event/status indicates terminal order state."""
        terminal_events = {"fill", "canceled", "rejected", "expired"}
        terminal_statuses = {"filled", "canceled", "rejected", "expired"}

        return event_type in terminal_events or (status is not None and status in terminal_statuses)

    def _process_pending_orders(self, order_ids: list[str], completed_orders: list[str]) -> None:
        """Check pending orders for completion via polling."""
        for order_id in order_ids[:]:  # Create copy to avoid modification during iteration
            try:
                status = self._check_order_completion_status(order_id)
                if status:
                    completed_orders.append(order_id)
                    order_ids.remove(order_id)
            except Exception as e:
                logger.error(f"Error checking order {order_id}: {e}")

    def _check_order_completion_status(self, order_id: str) -> str | None:
        """Check if a single order has reached a final state."""
        try:
            order = self._trading_client.get_order_by_id(order_id)
            order_status = getattr(order, "status", "").upper()

            # Check if order is in a final state
            if order_status in ["FILLED", "CANCELED", "REJECTED", "EXPIRED"]:
                return order_status
            return None

        except Exception as e:
            logger.error(f"Failed to check order {order_id} status: {e}")
            return None
