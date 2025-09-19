"""Business Unit: shared | Status: current.

Alpaca order management.

Handles order placement, cancellation, status tracking, and order lifecycle management.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Literal

from alpaca.trading.enums import QueryOrderStatus
from alpaca.trading.models import Order
from alpaca.trading.requests import GetOrdersRequest, LimitOrderRequest, MarketOrderRequest

from ...dto.broker_dto import OrderExecutionResult
from ...dto.execution_report_dto import ExecutedOrderDTO
from .exceptions import AlpacaOrderError, normalize_alpaca_error
from .models import OrderExecutionModel, OrderModel

if TYPE_CHECKING:
    from .client import AlpacaClient

logger = logging.getLogger(__name__)


class OrderManager:
    """Manages order placement, cancellation, and lifecycle."""

    def __init__(self, client: AlpacaClient) -> None:
        """Initialize with Alpaca client.
        
        Args:
            client: AlpacaClient instance
        """
        self._client = client

    def place_order(
        self, order_request: LimitOrderRequest | MarketOrderRequest
    ) -> ExecutedOrderDTO:
        """Place an order and return execution details.
        
        Args:
            order_request: Order request to submit
            
        Returns:
            ExecutedOrderDTO with order details
        """
        try:
            order = self._client.trading_client.submit_order(order_request)

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
            order = self._client.trading_client.get_order_by_id(order_id)
            if isinstance(order, Order):
                return self._alpaca_order_to_execution_result(order)
            logger.error(f"Unexpected order type: {type(order)}")
            return self._create_error_execution_result(
                Exception("Invalid order type"),
                context="Order type validation",
                order_id=order_id,
            )
        except Exception as e:
            logger.error(f"Failed to get order execution result for {order_id}: {e}")
            return self._create_error_execution_result(e, "Get order execution result", order_id)

    def cancel_order(self, order_id: str) -> bool:
        """Cancel an order by ID.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if successful, False otherwise
            
        Raises:
            AlpacaOrderError: If operation fails
        """
        try:
            self._client.trading_client.cancel_order_by_id(order_id)
            logger.info(f"Successfully cancelled order: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {e}")
            raise normalize_alpaca_error(e, f"Cancel order {order_id}") from e

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
                self._client.trading_client.cancel_orders()

            logger.info("Successfully cancelled orders" + (f" for {symbol}" if symbol else ""))
            return True
        except Exception as e:
            logger.error(f"Failed to cancel orders: {e}")
            return False

    def cancel_stale_orders(self, timeout_minutes: int = 30) -> dict[str, Any]:
        """Cancel orders older than the specified timeout.

        Args:
            timeout_minutes: Orders older than this many minutes will be cancelled

        Returns:
            Dictionary containing:
            - cancelled_count: Number of orders cancelled
            - errors: List of any errors encountered
            - cancelled_orders: List of order IDs that were cancelled
        """
        try:
            current_time = datetime.now(UTC)
            cutoff_time = current_time - timedelta(minutes=timeout_minutes)

            # Get all open orders
            open_orders = self.get_orders(status="open")

            cancelled_orders = []
            errors = []

            logger.info(
                f"🔍 Checking {len(open_orders)} open orders for staleness (>{timeout_minutes} minutes)"
            )

            for order in open_orders:
                try:
                    # Get order submission time
                    submitted_at = getattr(order, "submitted_at", None)
                    if not submitted_at:
                        continue

                    # Handle string timestamps
                    if isinstance(submitted_at, str):
                        submitted_at = datetime.fromisoformat(submitted_at.replace("Z", "+00:00"))

                    # Check if order is stale
                    if submitted_at < cutoff_time:
                        order_id = str(getattr(order, "id", "unknown"))
                        symbol = getattr(order, "symbol", "unknown")
                        age_minutes = (current_time - submitted_at).total_seconds() / 60

                        logger.info(
                            f"🗑️ Cancelling stale order {order_id} for {symbol} "
                            f"(age: {age_minutes:.1f} minutes)"
                        )

                        if self.cancel_order(order_id):
                            cancelled_orders.append(order_id)
                        else:
                            errors.append(f"Failed to cancel order {order_id}")

                except Exception as e:
                    order_id = str(getattr(order, "id", "unknown"))
                    error_msg = f"Error processing order {order_id}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)

            result = {
                "cancelled_count": len(cancelled_orders),
                "errors": errors,
                "cancelled_orders": cancelled_orders,
            }

            if cancelled_orders:
                logger.info(
                    f"✅ Cancelled {len(cancelled_orders)} stale orders: {cancelled_orders}"
                )
            else:
                logger.info("✅ No stale orders found to cancel")

            return result

        except Exception as e:
            error_msg = f"Failed to cancel stale orders: {e}"
            logger.error(error_msg)
            return {
                "cancelled_count": 0,
                "errors": [error_msg],
                "cancelled_orders": [],
            }

    def get_orders(self, status: str | None = None) -> list[Any]:
        """Get orders, optionally filtered by status.
        
        Args:
            status: Optional status filter (e.g., 'open', 'filled', 'cancelled')
            
        Returns:
            List of order objects
            
        Raises:
            AlpacaOrderError: If operation fails
        """
        try:
            # Use proper request to get more orders (default limit is very low)
            if status and status.lower() == "open":
                # Use the API's built-in open status filter for efficiency
                request = GetOrdersRequest(status=QueryOrderStatus.OPEN)
                orders = self._client.trading_client.get_orders(request)
            else:
                # Get recent orders with higher limit to catch all relevant orders
                request = GetOrdersRequest(limit=100)  # Increased from default
                orders = self._client.trading_client.get_orders(request)

            orders_list = list(orders)

            # Apply manual filtering for non-open status requests
            if status and status.lower() != "open":
                status_lower = status.lower()
                # For other statuses, try exact match on the enum name
                orders_list = [
                    o for o in orders_list if str(getattr(o, "status", "")).lower() == status_lower
                ]

            logger.debug(f"Successfully retrieved {len(orders_list)} orders")
            return orders_list
        except Exception as e:
            logger.error(f"Failed to get orders: {e}")
            raise normalize_alpaca_error(e, "Get orders") from e

    def check_order_completion_status(self, order_id: str) -> str | None:
        """Check if a single order has reached a final state.
        
        Args:
            order_id: Order ID to check
            
        Returns:
            Order status string if order is in final state, None otherwise
        """
        try:
            order = self._client.trading_client.get_order_by_id(order_id)
            status = str(getattr(order, "status", "")).upper()
            
            # Return status only if it's a final state
            if status in ["FILLED", "CANCELED", "REJECTED", "EXPIRED"]:
                return status
            return None
        except Exception as e:
            logger.warning(f"Failed to check order status for {order_id}: {e}")
            return None

    def _alpaca_order_to_execution_result(self, order: Order) -> OrderExecutionResult:
        """Convert Alpaca order object to OrderExecutionResult.

        Simple implementation that avoids circular imports.
        """
        try:
            # Extract basic fields from order object
            order_id_raw = getattr(order, "id", None)
            order_id = str(order_id_raw) if order_id_raw is not None else "unknown"
            status = getattr(order, "status", "unknown")
            filled_qty = Decimal(str(getattr(order, "filled_qty", 0)))
            avg_fill_price = getattr(order, "filled_avg_price", None)
            submitted_at = getattr(order, "submitted_at", None)
            filled_at = getattr(order, "filled_at", None)

            # Map Alpaca status to OrderExecutionResult status
            status_str = str(status).upper()
            mapped_status: Literal["accepted", "filled", "partially_filled", "rejected", "canceled"]
            if status_str in ["FILLED", "CLOSED"]:
                mapped_status = "filled"
            elif status_str == "CANCELED":
                mapped_status = "canceled"
            elif status_str in ["REJECTED", "EXPIRED", "STOPPED"]:
                mapped_status = "rejected"
            elif status_str in ["PARTIALLY_FILLED"]:
                mapped_status = "partially_filled"
            else:
                mapped_status = "accepted"

            # Handle timestamps
            submitted_dt = submitted_at if isinstance(submitted_at, datetime) else datetime.now(UTC)
            completed_dt = filled_at if isinstance(filled_at, datetime) else datetime.now(UTC)

            # Handle average fill price
            avg_price = None
            if avg_fill_price is not None:
                try:
                    avg_price = Decimal(str(avg_fill_price))
                except (ValueError, TypeError):
                    avg_price = None

            return OrderExecutionResult(
                success=True,
                order_id=order_id,
                status=mapped_status,
                filled_qty=filled_qty,
                avg_fill_price=avg_price,
                submitted_at=submitted_dt,
                completed_at=completed_dt,
                error=None,
            )

        except Exception as e:
            logger.error(f"Failed to convert order to execution result: {e}")
            return self._create_error_execution_result(e, "Order conversion")

    def _create_error_execution_result(
        self, error: Exception, context: str = "Operation", order_id: str = "unknown"
    ) -> OrderExecutionResult:
        """Create an error OrderExecutionResult."""
        status: Literal["accepted", "filled", "partially_filled", "rejected", "canceled"] = (
            "rejected"
        )
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