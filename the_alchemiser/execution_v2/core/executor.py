"""Business Unit: execution | Status: current.

Executor that consumes RebalancePlanDTO and places orders.

Core principle: iterate through plan items and place orders - nothing more.
No portfolio calculations, position fetching, or trade recalculation.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal

from the_alchemiser.execution_v2.models.execution_result import (
    ExecutionResultDTO,
    OrderResultDTO,
)
from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.dto.rebalance_plan_dto import (
    RebalancePlanDTO,
    RebalancePlanItemDTO,
)

logger = logging.getLogger(__name__)


class Executor:
    """Executor that processes RebalancePlanDTO items."""

    def __init__(self, alpaca_manager: AlpacaManager) -> None:
        """Initialize with AlpacaManager."""
        self.alpaca_manager = alpaca_manager

    def execute_rebalance_plan(self, plan: RebalancePlanDTO) -> ExecutionResultDTO:
        """Execute rebalance plan using phased execution strategy.

        Implements SELL-first strategy to release buying power before executing BUY orders.
        This prevents "insufficient buying power" errors by ensuring SELL orders complete
        and release funds before BUY orders are placed.

        Args:
            plan: RebalancePlanDTO with items to execute

        Returns:
            ExecutionResultDTO with order results and success status

        """
        logger.info(
            f"🚀 Executing rebalance plan {plan.plan_id} with {len(plan.items)} items"
        )

        # Check if we have both SELL and BUY orders - if so, use phased execution
        sell_items = [item for item in plan.items if item.action == "SELL"]
        buy_items = [item for item in plan.items if item.action == "BUY"]

        if sell_items and buy_items:
            logger.info(
                f"📊 Using phased execution: {len(sell_items)} SELL orders → monitor buying power → {len(buy_items)} BUY orders"
            )
            return self._execute_phased_plan(plan, sell_items, buy_items)
        # No mixed orders - use original sequential execution
        logger.info(f"📦 Using sequential execution for {len(plan.items)} items")
        return self._execute_sequential_plan(plan)

    def _execute_sequential_plan(self, plan: RebalancePlanDTO) -> ExecutionResultDTO:
        """Execute rebalance plan using original sequential strategy.

        Args:
            plan: RebalancePlanDTO with items to execute

        Returns:
            ExecutionResultDTO with order results and success status

        """
        orders: list[OrderResultDTO] = []
        total_trade_value = Decimal("0")

        for item in plan.items:
            # Skip HOLD actions - only process trades
            if item.action == "HOLD":
                logger.debug(f"⏭️ Skipping HOLD action for {item.symbol}")
                continue

            logger.info(
                f"📦 Processing {item.action} ${item.trade_amount} {item.symbol}"
            )

            # Execute the trade
            order_result = self._execute_trade_item(item)
            orders.append(order_result)

            if order_result.success:
                total_trade_value += abs(item.trade_amount)

        # Calculate summary statistics
        orders_placed = len(orders)
        orders_succeeded = sum(1 for order in orders if order.success)
        overall_success = (
            orders_succeeded == orders_placed if orders_placed > 0 else True
        )

        result = ExecutionResultDTO(
            success=overall_success,
            plan_id=plan.plan_id,
            correlation_id=plan.correlation_id,
            orders=orders,
            orders_placed=orders_placed,
            orders_succeeded=orders_succeeded,
            total_trade_value=total_trade_value,
            execution_timestamp=datetime.now(UTC),
        )

        logger.info(
            f"✅ Execution complete: {orders_succeeded}/{orders_placed} orders succeeded "
            f"(${total_trade_value} traded)"
        )

        return result

    def _execute_phased_plan(
        self,
        plan: RebalancePlanDTO,
        sell_items: list[RebalancePlanItemDTO],
        buy_items: list[RebalancePlanItemDTO],
    ) -> ExecutionResultDTO:
        """Execute rebalance plan using phased strategy: SELL → monitor → BUY.

        Args:
            plan: Original rebalance plan
            sell_items: SELL order items to execute first
            buy_items: BUY order items to execute after SELL completion

        Returns:
            ExecutionResultDTO with combined results from both phases

        """
        all_orders: list[OrderResultDTO] = []
        total_trade_value = Decimal("0")

        # Phase 1: Execute SELL orders to release buying power
        logger.info(
            f"🔴 Phase 1: Executing {len(sell_items)} SELL orders to release buying power"
        )
        sell_order_ids = []

        for item in sell_items:
            logger.info(f"📦 Processing SELL ${item.trade_amount} {item.symbol}")
            order_result = self._execute_trade_item(item)
            all_orders.append(order_result)

            if order_result.success:
                total_trade_value += abs(item.trade_amount)
                if order_result.order_id:
                    sell_order_ids.append(order_result.order_id)

        # Phase 2: Monitor SELL order completion and buying power
        if sell_order_ids:
            logger.info(
                f"⏱️ Phase 2: Monitoring {len(sell_order_ids)} SELL orders for completion"
            )
            initial_buying_power = self._get_current_buying_power()

            # Wait for SELL orders to complete (max 60 seconds)
            websocket_result = self.alpaca_manager.wait_for_order_completion(
                sell_order_ids, max_wait_seconds=60
            )

            if websocket_result.status.value == "completed":
                logger.info("✅ All SELL orders completed successfully")

                # Monitor buying power increase
                self._wait_for_buying_power_increase(initial_buying_power, buy_items)
            else:
                logger.warning(
                    f"⚠️ SELL order monitoring completed with status: {websocket_result.status.value}"
                )
                logger.warning(
                    f"Completed {len(websocket_result.completed_order_ids)}/{len(sell_order_ids)} orders"
                )

        # Phase 3: Execute BUY orders with available buying power
        logger.info(f"🟢 Phase 3: Executing {len(buy_items)} BUY orders")

        for item in buy_items:
            logger.info(f"📦 Processing BUY ${item.trade_amount} {item.symbol}")
            order_result = self._execute_trade_item(item)
            all_orders.append(order_result)

            if order_result.success:
                total_trade_value += abs(item.trade_amount)

        # Calculate combined results
        orders_placed = len(all_orders)
        orders_succeeded = sum(1 for order in all_orders if order.success)
        overall_success = (
            orders_succeeded == orders_placed if orders_placed > 0 else True
        )

        result = ExecutionResultDTO(
            success=overall_success,
            plan_id=plan.plan_id,
            correlation_id=plan.correlation_id,
            orders=all_orders,
            orders_placed=orders_placed,
            orders_succeeded=orders_succeeded,
            total_trade_value=total_trade_value,
            execution_timestamp=datetime.now(UTC),
            metadata={"execution_strategy": "phased_sell_first"},
        )

        logger.info(
            f"✅ Phased execution complete: {orders_succeeded}/{orders_placed} orders succeeded "
            f"(${total_trade_value} traded)"
        )

        return result

    def _get_current_buying_power(self) -> Decimal:
        """Get current buying power as Decimal for precise calculations.

        Returns:
            Current buying power, or 0 if unavailable

        """
        try:
            buying_power = self.alpaca_manager.get_buying_power()
            if buying_power is not None:
                return Decimal(str(buying_power))
            return Decimal("0")
        except Exception as e:
            logger.warning(f"Failed to get buying power: {e}")
            return Decimal("0")

    def _calculate_required_buying_power(
        self, buy_items: list[RebalancePlanItemDTO]
    ) -> Decimal:
        """Calculate total buying power required for BUY orders.

        Args:
            buy_items: List of BUY order items

        Returns:
            Total dollar amount needed for all BUY orders

        """
        return sum((abs(item.trade_amount) for item in buy_items), Decimal("0"))

    def _wait_for_buying_power_increase(
        self,
        initial_buying_power: Decimal,
        buy_items: list[RebalancePlanItemDTO],
        max_wait_seconds: int = 30,
    ) -> bool:
        """Wait for buying power to increase after SELL order completion.

        Args:
            initial_buying_power: Buying power before SELL orders
            buy_items: BUY orders that will need buying power
            max_wait_seconds: Maximum time to wait for buying power increase

        Returns:
            True if sufficient buying power is available, False if timeout

        """
        required_buying_power = self._calculate_required_buying_power(buy_items)
        logger.info(
            f"💰 Monitoring buying power increase (need ${required_buying_power})"
        )

        import time

        start_time = time.time()
        check_interval = 2  # Check every 2 seconds

        while (time.time() - start_time) < max_wait_seconds:
            current_buying_power = self._get_current_buying_power()
            buying_power_increase = current_buying_power - initial_buying_power

            logger.debug(
                f"💰 Buying power: ${current_buying_power} (increase: ${buying_power_increase})"
            )

            # Check if we have sufficient buying power for all BUY orders
            if current_buying_power >= required_buying_power:
                logger.info(
                    f"✅ Sufficient buying power available: ${current_buying_power} >= ${required_buying_power}"
                )
                return True

            # Also check if buying power increased significantly (SELL proceeds available)
            if buying_power_increase > Decimal(
                "100"
            ):  # At least $100 increase suggests SELL completion
                logger.info(
                    f"✅ Buying power increased by ${buying_power_increase}, proceeding with BUY orders"
                )
                return True

            time.sleep(check_interval)

        current_buying_power = self._get_current_buying_power()
        logger.warning(f"⚠️ Buying power monitoring timeout after {max_wait_seconds}s")
        logger.warning(
            f"💰 Final buying power: ${current_buying_power}, required: ${required_buying_power}"
        )

        return False

    def _execute_trade_item(self, item: RebalancePlanItemDTO) -> OrderResultDTO:
        """Execute a single trade item.

        Args:
            item: RebalancePlanItemDTO to execute

        Returns:
            OrderResultDTO with execution result

        """
        timestamp = datetime.now(UTC)

        try:
            # Get current price with enhanced pricing context
            # Enhanced pricing implementation: use current price with proper error handling
            # Future enhancement: Consider using get_quote_data() for bid/ask spreads
            price = self.alpaca_manager.get_current_price(item.symbol)
            if price is None:
                return OrderResultDTO(
                    symbol=item.symbol,
                    action=item.action,
                    trade_amount=item.trade_amount,
                    shares=Decimal("0"),
                    price=None,
                    order_id=None,
                    success=False,
                    error_message=f"Could not get current price for {item.symbol}",
                    timestamp=timestamp,
                )

            # Calculate shares to trade
            price_decimal = Decimal(str(price))
            shares = abs(item.trade_amount) / price_decimal

            # Check if this is a complete exit (target_weight = 0 and selling)
            is_complete_exit = (
                item.action == "SELL"
                and hasattr(item, "target_weight")
                and item.target_weight == Decimal("0")
            )

            # Place market order - returns ExecutedOrderDTO
            side = item.action.lower()  # "BUY" -> "buy", "SELL" -> "sell"
            executed_order = self.alpaca_manager.place_market_order(
                symbol=item.symbol,
                side=side,
                qty=float(shares),
                is_complete_exit=is_complete_exit,
            )

            # Extract results from ExecutedOrderDTO
            order_id = (
                executed_order.order_id
                if executed_order.order_id != "FAILED"
                and executed_order.order_id != "INVALID"
                else None
            )
            success = (
                executed_order.status not in ["REJECTED", "FAILED"]
                and order_id is not None
            )
            error_message = executed_order.error_message if not success else None

            if success:
                logger.info(
                    f"✅ Order placed: {item.action} {shares:.4f} shares {item.symbol} → {order_id}"
                )
            else:
                logger.error(
                    f"❌ Order failed: {item.action} {item.symbol} - {error_message}"
                )

            return OrderResultDTO(
                symbol=item.symbol,
                action=item.action,
                trade_amount=item.trade_amount,
                shares=shares,
                price=price_decimal,
                order_id=order_id,
                success=success,
                error_message=error_message,
                timestamp=timestamp,
            )

        except Exception as e:
            logger.error(
                f"❌ Unexpected error executing {item.action} {item.symbol}: {e}"
            )
            return OrderResultDTO(
                symbol=item.symbol,
                action=item.action,
                trade_amount=item.trade_amount,
                shares=Decimal("0"),
                price=None,
                order_id=None,
                success=False,
                error_message=str(e),
                timestamp=timestamp,
            )
