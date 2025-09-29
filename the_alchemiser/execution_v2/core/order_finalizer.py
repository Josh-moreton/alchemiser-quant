"""Business Unit: execution | Status: current.

Order status finalization functionality extracted from the main executor.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING

from the_alchemiser.execution_v2.models.execution_result import OrderResult
from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlanItem

if TYPE_CHECKING:
    from the_alchemiser.execution_v2.core.smart_execution_strategy import ExecutionConfig

logger = logging.getLogger(__name__)


class OrderFinalizer:
    """Handles order status finalization and completion polling."""

    def __init__(self, alpaca_manager: AlpacaManager, execution_config: ExecutionConfig | None) -> None:
        """Initialize the order finalizer.

        Args:
            alpaca_manager: Alpaca broker manager
            execution_config: ExecutionConfig | None

        """
        self.alpaca_manager = alpaca_manager
        self.execution_config = execution_config

    def finalize_phase_orders(
        self,
        orders: list[OrderResult],
        items: list[RebalancePlanItem],
        phase_type: str,
    ) -> tuple[list[OrderResult], int, Decimal]:
        """Finalize orders by checking completion status and updating results.

        Args:
            orders: List of orders to finalize
            items: Corresponding rebalance plan items
            phase_type: Type of phase for logging

        Returns:
            Tuple of (updated_orders, succeeded_count, total_trade_value)

        """
        if not orders:
            logger.debug(f"📊 {phase_type} phase: No orders to finalize")
            return orders, 0, Decimal("0")

        logger.info(f"📊 {phase_type} phase: Finalizing {len(orders)} orders...")

        # Derive maximum wait time
        max_wait = self._derive_max_wait_seconds()

        # Get final status for all orders
        final_status_map = self._get_final_status_map(orders, max_wait, phase_type)

        # Rebuild orders with final status and compute statistics
        return self._rebuild_orders_with_final_status(orders, items, final_status_map)

    def _derive_max_wait_seconds(self) -> int:
        """Derive maximum wait time for order completion.

        Returns:
            Maximum wait time in seconds

        """
        default_wait = 30
        try:
            if self.execution_config is not None:
                return int(
                    getattr(self.execution_config, "order_placement_timeout_seconds", default_wait)
                )
        except Exception as exc:
            logger.debug(f"Error deriving max wait seconds: {exc}")
        return default_wait

    def _get_final_status_map(
        self, orders: list[OrderResult], max_wait: int, phase_type: str
    ) -> dict[str, tuple[str, Decimal | None]]:
        """Get final status map for all orders.

        Args:
            orders: List of orders to check
            max_wait: Maximum wait time
            phase_type: Phase type for logging

        Returns:
            Dictionary mapping order IDs to (status, price) tuples

        """
        # Validate order IDs and separate valid from invalid
        valid_order_ids, invalid_order_ids = self._validate_order_ids(orders)

        # Poll for completion if we have valid order IDs
        if valid_order_ids:
            self._poll_order_completion(valid_order_ids, max_wait, phase_type)

        # Build final status map
        return self._build_final_status_map(valid_order_ids, invalid_order_ids)

    def _validate_order_ids(
        self, orders: list[OrderResult]
    ) -> tuple[list[str], list[str]]:
        """Validate order IDs and separate valid from invalid.

        Args:
            orders: List of orders to validate

        Returns:
            Tuple of (valid_order_ids, invalid_order_ids)

        """
        def _is_valid_uuid(val: str) -> bool:
            """Check if a string is a valid UUID."""
            try:
                import uuid
                uuid.UUID(val)
                return True
            except (ValueError, TypeError):
                return False

        valid_order_ids = []
        invalid_order_ids = []

        for order in orders:
            if order.order_id and _is_valid_uuid(order.order_id):
                valid_order_ids.append(order.order_id)
            elif order.order_id:
                invalid_order_ids.append(order.order_id)

        logger.debug(
            f"📋 Order ID validation: {len(valid_order_ids)} valid, "
            f"{len(invalid_order_ids)} invalid"
        )

        return valid_order_ids, invalid_order_ids

    def _poll_order_completion(
        self, valid_order_ids: list[str], max_wait: int, phase_type: str
    ) -> None:
        """Poll broker for order completion status.

        Args:
            valid_order_ids: List of valid order IDs to poll
            max_wait: Maximum wait time in seconds
            phase_type: Phase type for logging

        """
        try:
            ws_result = self.alpaca_manager.wait_for_order_completion(
                valid_order_ids, max_wait_seconds=max_wait
            )
            if getattr(ws_result, "status", None) is None:
                logger.warning(
                    f"⚠️ {phase_type} phase: Could not determine completion status via polling"
                )
        except Exception as exc:
            logger.warning(f"{phase_type} phase: error while polling for completion: {exc}")

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
            return status_str, avg_price
        except Exception as exc:
            logger.warning(f"Failed to refresh order {order_id}: {exc}")
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
            # Default to existing values
            final_price = o.price
            is_filled = o.success
            final_error = o.error_message

            # Update with final status if available
            if o.order_id and o.order_id in final_status_map:
                status_str, avg_price = final_status_map[o.order_id]
                is_filled = status_str.lower() in ["filled", "partially_filled"]
                if avg_price is not None:
                    final_price = avg_price
                if not is_filled and status_str.lower() in ["rejected", "canceled"]:
                    final_error = f"Order {status_str.lower()}"

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
            )
            updated_orders.append(new_o)

            if is_filled:
                succeeded += 1
                try:
                    corresponding_item = items[idx]
                    trade_value += abs(corresponding_item.trade_amount)
                except Exception:
                    trade_value += abs(o.trade_amount)

        return updated_orders, succeeded, trade_value