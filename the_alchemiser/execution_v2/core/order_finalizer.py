"""Business Unit: execution | Status: current.

Order status finalization functionality extracted from the main executor.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from the_alchemiser.execution_v2.models.execution_result import OrderResult
from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlanItem

if TYPE_CHECKING:
    from the_alchemiser.execution_v2.core.smart_execution_strategy import ExecutionConfig

logger = get_logger(__name__)

# Default timeout for order completion polling
DEFAULT_ORDER_COMPLETION_TIMEOUT_SECONDS = 30


class OrderFinalizer:
    """Handles order status finalization and completion polling.

    This class is responsible for:
    - Validating order IDs and filtering invalid ones
    - Polling the broker for order completion status
    - Updating order results with final status and prices
    - Computing execution statistics (success count, trade value)

    The finalizer ensures that all orders have accurate final status
    from the broker before returning execution results.

    Attributes:
        alpaca_manager: Alpaca broker manager for API calls
        execution_config: Optional execution configuration for timeouts

    """

    def __init__(
        self, alpaca_manager: AlpacaManager, execution_config: ExecutionConfig | None
    ) -> None:
        """Initialize the order finalizer.

        Args:
            alpaca_manager: Alpaca broker manager for order status queries
            execution_config: Optional execution configuration with timeout settings

        Raises:
            ValueError: If alpaca_manager is None (validation should be done by caller)

        """
        self.alpaca_manager = alpaca_manager
        self.execution_config = execution_config

    def finalize_phase_orders(
        self,
        orders: list[OrderResult],
        items: list[RebalancePlanItem],
        phase_type: str,
        correlation_id: str | None = None,
    ) -> tuple[list[OrderResult], int, Decimal]:
        """Finalize orders by checking completion status and updating results.

        This method:
        1. Validates order IDs and filters invalid ones
        2. Polls broker for order completion (if valid IDs exist)
        3. Updates each order with final status and prices from broker
        4. Computes success statistics and total trade value

        Args:
            orders: List of orders to finalize
            items: Corresponding rebalance plan items (must match order indices)
            phase_type: Type of phase for logging (e.g., "BUY", "SELL", "CLEANUP")
            correlation_id: Optional correlation ID for distributed tracing

        Returns:
            Tuple of (updated_orders, succeeded_count, total_trade_value)
            - updated_orders: Orders with final status/prices from broker
            - succeeded_count: Number of successfully filled orders
            - total_trade_value: Sum of absolute trade amounts for filled orders

        Examples:
            >>> finalizer = OrderFinalizer(alpaca_manager, config)
            >>> orders, success_count, value = finalizer.finalize_phase_orders(
            ...     orders=[order1, order2],
            ...     items=[item1, item2],
            ...     phase_type="BUY",
            ...     correlation_id="abc-123"
            ... )

        """
        log_extra = {"correlation_id": correlation_id} if correlation_id else {}

        if not orders:
            logger.debug(
                f"📊 {phase_type} phase: No orders to finalize",
                extra=log_extra,
            )
            return orders, 0, Decimal("0")

        logger.info(
            f"📊 {phase_type} phase: Finalizing {len(orders)} orders...",
            extra=log_extra,
        )

        # Derive maximum wait time
        max_wait = self._derive_max_wait_seconds()

        # Get final status for all orders
        final_status_map = self._get_final_status_map(orders, max_wait, phase_type, correlation_id)

        # Rebuild orders with final status and compute statistics
        return self._rebuild_orders_with_final_status(orders, items, final_status_map)

    def _derive_max_wait_seconds(self) -> int:
        """Derive maximum wait time for order completion.

        Checks execution_config for custom timeout, falls back to default.

        Returns:
            Maximum wait time in seconds (defaults to 30)

        """
        try:
            if self.execution_config is not None:
                return int(
                    getattr(
                        self.execution_config,
                        "order_placement_timeout_seconds",
                        DEFAULT_ORDER_COMPLETION_TIMEOUT_SECONDS,
                    )
                )
        except Exception as exc:
            logger.debug(
                f"Error deriving max wait seconds: {exc}",
                extra={"error_type": type(exc).__name__},
            )
        return DEFAULT_ORDER_COMPLETION_TIMEOUT_SECONDS

    def _get_final_status_map(
        self,
        orders: list[OrderResult],
        max_wait: int,
        phase_type: str,
        correlation_id: str | None = None,
    ) -> dict[str, tuple[str, Decimal | None]]:
        """Get final status map for all orders.

        Args:
            orders: List of orders to check
            max_wait: Maximum wait time
            phase_type: Phase type for logging
            correlation_id: Optional correlation ID for distributed tracing

        Returns:
            Dictionary mapping order IDs to (status, price) tuples

        """
        # Validate order IDs and separate valid from invalid
        valid_order_ids, invalid_order_ids = self._validate_order_ids(orders, correlation_id)

        # Poll for completion if we have valid order IDs
        if valid_order_ids:
            self._poll_order_completion(valid_order_ids, max_wait, phase_type, correlation_id)

        # Build final status map
        return self._build_final_status_map(valid_order_ids, invalid_order_ids)

    def _validate_order_ids(
        self, orders: list[OrderResult], correlation_id: str | None = None
    ) -> tuple[list[str], list[str]]:
        """Validate order IDs and separate valid from invalid.

        Args:
            orders: List of orders to validate
            correlation_id: Optional correlation ID for distributed tracing

        Returns:
            Tuple of (valid_order_ids, invalid_order_ids)

        """
        valid_order_ids = []
        invalid_order_ids = []

        for order in orders:
            if order.order_id and self._is_valid_uuid(order.order_id):
                valid_order_ids.append(order.order_id)
            elif order.order_id:
                invalid_order_ids.append(order.order_id)

        log_extra = {"correlation_id": correlation_id} if correlation_id else {}
        logger.debug(
            f"📋 Order ID validation: {len(valid_order_ids)} valid, "
            f"{len(invalid_order_ids)} invalid",
            extra=log_extra,
        )

        return valid_order_ids, invalid_order_ids

    @staticmethod
    def _is_valid_uuid(val: str) -> bool:
        """Check if a string is a valid UUID.

        Args:
            val: String to validate as UUID

        Returns:
            True if valid UUID, False otherwise

        """
        try:
            uuid.UUID(val)
            return True
        except (ValueError, TypeError):
            return False

    def _poll_order_completion(
        self,
        valid_order_ids: list[str],
        max_wait: int,
        phase_type: str,
        correlation_id: str | None = None,
    ) -> None:
        """Poll broker for order completion status.

        Args:
            valid_order_ids: List of valid order IDs to poll
            max_wait: Maximum wait time in seconds
            phase_type: Phase type for logging
            correlation_id: Optional correlation ID for distributed tracing

        """
        log_extra = {"correlation_id": correlation_id} if correlation_id else {}

        try:
            ws_result = self.alpaca_manager.wait_for_order_completion(
                valid_order_ids, max_wait_seconds=max_wait
            )
            if getattr(ws_result, "status", None) is None:
                logger.warning(
                    f"⚠️ {phase_type} phase: Could not determine completion status via polling",
                    extra=log_extra,
                )
        except Exception as exc:
            logger.warning(
                f"{phase_type} phase: error while polling for completion: {exc}",
                extra={
                    **log_extra,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                },
            )

    def _build_final_status_map(
        self, valid_order_ids: list[str], invalid_order_ids: list[str]
    ) -> dict[str, tuple[str, Decimal | None]]:
        """Build final status map for all order IDs.

        Args:
            valid_order_ids: List of valid order IDs
            invalid_order_ids: List of invalid order IDs

        Returns:
            Dictionary mapping order IDs to (status, price) tuples

        """
        final_status_map: dict[str, tuple[str, Decimal | None]] = {}

        # Pre-populate invalid IDs as rejected without broker calls
        for oid in invalid_order_ids:
            final_status_map[oid] = ("rejected", None)

        # Get status for valid order IDs
        for oid in valid_order_ids:
            status, price = self._get_order_status_and_price(oid)
            final_status_map[oid] = (status, price)

        return final_status_map

    def _get_order_status_and_price(self, order_id: str) -> tuple[str, Decimal | None]:
        """Get status and price for a single order ID.

        Args:
            order_id: Order ID to check

        Returns:
            Tuple of (status_string, average_price)

        """
        try:
            exec_res = self.alpaca_manager.get_order_execution_result(order_id)
            status_str = str(getattr(exec_res, "status", "accepted"))
            avg_price_obj = getattr(exec_res, "avg_fill_price", None)
            avg_price: Decimal | None = (
                avg_price_obj if isinstance(avg_price_obj, Decimal) else None
            )

            # CRITICAL: Warn if order stuck in "accepted" without price
            # This indicates potential Alpaca API issue where price never settles
            if status_str == "accepted" and avg_price is None:
                filled_qty_obj = getattr(exec_res, "filled_qty", Decimal("0"))
                if filled_qty_obj > 0:
                    logger.error(
                        "🚨 Order has fills but stuck in 'accepted' status without price - potential API issue",
                        extra={
                            "order_id": order_id,
                            "status": status_str,
                            "filled_qty": str(filled_qty_obj),
                            "alert": "MANUAL_REVIEW_REQUIRED",
                            "risk": "HIGH",
                        },
                    )

            return status_str, avg_price
        except Exception as exc:
            logger.warning(
                f"Failed to refresh order {order_id}: {exc}",
                extra={
                    "order_id": order_id,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                },
            )
            return "rejected", None

    def _rebuild_orders_with_final_status(
        self,
        orders: list[OrderResult],
        items: list[RebalancePlanItem],
        final_status_map: dict[str, tuple[str, Decimal | None]],
    ) -> tuple[list[OrderResult], int, Decimal]:
        """Rebuild OrderResults with final semantics, compute success and trade value.

        Args:
            orders: Original orders
            items: Corresponding rebalance plan items
            final_status_map: Final status for each order

        Returns:
            Tuple of (updated_orders, succeeded_count, total_trade_value)

        """
        updated_orders = []
        succeeded = 0
        trade_value = Decimal("0")

        for idx, o in enumerate(orders):
            # Apply final status updates to the order
            final_price, is_filled, final_error = self._apply_final_status_to_order(
                o, final_status_map
            )

            # Create updated order result
            new_o = OrderResult(
                symbol=o.symbol,
                action=o.action,
                trade_amount=o.trade_amount,
                shares=o.shares,
                price=final_price,
                order_id=o.order_id,
                success=is_filled,
                error_message=final_error,
                timestamp=o.timestamp,
                order_type=o.order_type,  # Preserve order type
                filled_at=o.filled_at
                if not is_filled
                else (o.filled_at or o.timestamp),  # Set filled_at on success
            )
            updated_orders.append(new_o)

            # Update statistics for filled orders
            if is_filled:
                succeeded += 1
                trade_value += self._calculate_order_trade_value(o, items, idx)

        return updated_orders, succeeded, trade_value

    def _apply_final_status_to_order(
        self,
        order: OrderResult,
        final_status_map: dict[str, tuple[str, Decimal | None]],
    ) -> tuple[Decimal | None, bool, str | None]:
        """Apply final status from broker to order, updating price, filled status, and error.

        Args:
            order: Original order result
            final_status_map: Final status for each order

        Returns:
            Tuple of (final_price, is_filled, final_error)

        """
        final_price = order.price
        is_filled = order.success
        final_error = order.error_message

        if order.order_id and order.order_id in final_status_map:
            status_str, avg_price = final_status_map[order.order_id]
            is_filled = status_str.lower() in ["filled", "partially_filled"]
            if avg_price is not None:
                final_price = avg_price
            if not is_filled and status_str.lower() in ["rejected", "canceled"]:
                final_error = f"Order {status_str.lower()}"

        return final_price, is_filled, final_error

    def _calculate_order_trade_value(
        self, order: OrderResult, items: list[RebalancePlanItem], idx: int
    ) -> Decimal:
        """Calculate trade value for an order from corresponding rebalance plan item.

        Args:
            order: Order result
            items: List of rebalance plan items
            idx: Index of order in the list

        Returns:
            Trade value as absolute Decimal

        """
        try:
            corresponding_item = items[idx]
            return abs(corresponding_item.trade_amount)
        except IndexError:
            logger.debug(
                f"Index {idx} out of range for items list (length {len(items)}), "
                f"using order trade_amount as fallback",
                extra={
                    "order_symbol": order.symbol,
                    "order_id": order.order_id,
                    "index": idx,
                    "items_length": len(items),
                },
            )
            return abs(order.trade_amount)
        except Exception as exc:
            logger.warning(
                f"Unexpected error calculating trade value: {exc}",
                extra={
                    "order_symbol": order.symbol,
                    "order_id": order.order_id,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                },
            )
            return abs(order.trade_amount)
