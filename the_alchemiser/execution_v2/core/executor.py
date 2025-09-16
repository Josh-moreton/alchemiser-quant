"""Business Unit: execution | Status: current.

Executor that consumes RebalancePlanDTO and places orders with smart execution.

Core principle: iterate through plan items and place orders using intelligent execution
strategies. Now supports both legacy market orders and smart limit order execution.

Enhanced with:
- Smart limit order execution for improved fills
- Liquidity-aware anchoring to bid/ask spreads
- Market timing awareness (avoids 9:30-9:35am)
- Configurable execution strategies per order urgency
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from decimal import Decimal

from the_alchemiser.execution_v2.core.smart_execution_strategy import (
    ExecutionConfig,
    SmartExecutionStrategy,
    SmartOrderRequest,
)
from the_alchemiser.execution_v2.models.execution_result import (
    ExecutionResultDTO,
    OrderResultDTO,
)
from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.dto.rebalance_plan_dto import (
    RebalancePlanDTO,
    RebalancePlanItemDTO,
)
from the_alchemiser.shared.services.real_time_pricing import RealTimePricingService

logger = logging.getLogger(__name__)


class Executor:
    """Executor that processes RebalancePlanDTO items with smart execution strategies."""

    def __init__(
        self,
        alpaca_manager: AlpacaManager,
        execution_config: ExecutionConfig | None = None,
        *,
        enable_smart_execution: bool = True,
    ) -> None:
        """Initialize with AlpacaManager and optional smart execution.

        Args:
            alpaca_manager: AlpacaManager for broker operations
            execution_config: Configuration for smart execution
            enable_smart_execution: Whether to use smart limit orders (default: True)

        """
        self.alpaca_manager = alpaca_manager
        self.enable_smart_execution = enable_smart_execution
        self.smart_strategy: SmartExecutionStrategy | None = None

        # Initialize smart execution strategy if enabled
        if enable_smart_execution:
            # Try to set up real-time pricing for smart execution
            pricing_service = self._setup_pricing_service()
            self.smart_strategy = SmartExecutionStrategy(
                alpaca_manager=alpaca_manager,
                pricing_service=pricing_service,
                config=execution_config or ExecutionConfig(),
            )
            logger.info("🎯 Smart execution enabled with liquidity-aware anchoring")
        else:
            self.smart_strategy = None
            logger.info("📦 Using legacy market order execution only")

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
            # For smart execution, we need to use async
            if self.enable_smart_execution:
                return asyncio.run(
                    self._execute_phased_plan_async(plan, sell_items, buy_items)
                )
            return self._execute_phased_plan(plan, sell_items, buy_items)
        # No mixed orders - use sequential execution
        logger.info(f"📦 Using sequential execution for {len(plan.items)} items")

        # For smart execution, we need to use async
        if self.enable_smart_execution:
            return asyncio.run(self._execute_sequential_plan_async(plan))
        return self._execute_sequential_plan_sync(plan)

    def _execute_sequential_plan_sync(
        self, plan: RebalancePlanDTO
    ) -> ExecutionResultDTO:
        """Execute rebalance plan using synchronous sequential strategy (legacy).

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

            # Execute the trade using legacy method
            order_result = self._execute_trade_item_legacy(item)
            orders.append(order_result)

            if order_result.success:
                total_trade_value += abs(item.trade_amount)

        return self._create_execution_result(
            plan, orders, total_trade_value, "sequential_sync"
        )

    async def _execute_sequential_plan_async(
        self, plan: RebalancePlanDTO
    ) -> ExecutionResultDTO:
        """Execute rebalance plan using asynchronous sequential strategy with smart execution.

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
                f"🎯 Processing {item.action} ${item.trade_amount} {item.symbol} (smart execution)"
            )

            # Execute the trade using smart method
            order_result = await self._execute_trade_item_smart(item)
            orders.append(order_result)

            if order_result.success:
                total_trade_value += abs(item.trade_amount)

        return self._create_execution_result(
            plan, orders, total_trade_value, "sequential_smart"
        )

    def _create_execution_result(
        self,
        plan: RebalancePlanDTO,
        orders: list[OrderResultDTO],
        total_trade_value: Decimal,
        strategy: str,
    ) -> ExecutionResultDTO:
        """Create ExecutionResultDTO from order results.

        Args:
            plan: Original rebalance plan
            orders: List of order results
            total_trade_value: Total value traded
            strategy: Execution strategy used

        Returns:
            ExecutionResultDTO with summary statistics

        """
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
            metadata={"execution_strategy": strategy},
        )

        logger.info(
            f"✅ Sequential execution complete: {orders_succeeded}/{orders_placed} orders succeeded "
            f"(${total_trade_value} traded) using {strategy}"
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
            order_result = self._execute_trade_item_legacy(item)
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
            order_result = self._execute_trade_item_legacy(item)
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

    async def _execute_phased_plan_async(
        self,
        plan: RebalancePlanDTO,
        sell_items: list[RebalancePlanItemDTO],
        buy_items: list[RebalancePlanItemDTO],
    ) -> ExecutionResultDTO:
        """Execute rebalance plan using async phased strategy with smart execution: SELL → monitor → BUY.

        Args:
            plan: Original rebalance plan
            sell_items: SELL order items to execute first
            buy_items: BUY order items to execute after SELL completion

        Returns:
            ExecutionResultDTO with combined results from both phases

        """
        all_orders: list[OrderResultDTO] = []
        total_trade_value = Decimal("0")

        # Phase 1: Execute SELL orders to release buying power (using smart execution)
        logger.info(
            f"🔴 Phase 1: Executing {len(sell_items)} SELL orders to release buying power (smart execution)"
        )
        sell_order_ids = []

        for item in sell_items:
            logger.info(
                f"🎯 Processing SELL ${item.trade_amount} {item.symbol} (smart execution)"
            )
            order_result = await self._execute_trade_item_smart(item)
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

        # Phase 3: Execute BUY orders with available buying power (using smart execution)
        logger.info(
            f"🟢 Phase 3: Executing {len(buy_items)} BUY orders (smart execution)"
        )

        for item in buy_items:
            logger.info(
                f"🎯 Processing BUY ${item.trade_amount} {item.symbol} (smart execution)"
            )
            order_result = await self._execute_trade_item_smart(item)
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
            metadata={"execution_strategy": "phased_sell_first_smart"},
        )

        logger.info(
            f"✅ Phased smart execution complete: {orders_succeeded}/{orders_placed} orders succeeded "
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

    def _setup_pricing_service(self) -> RealTimePricingService | None:
        """Set up real-time pricing service for smart execution.

        Returns:
            RealTimePricingService instance or None if setup fails

        """
        try:
            # Extract credentials from alpaca_manager for pricing service
            pricing_service = RealTimePricingService(
                api_key=self.alpaca_manager.api_key,
                secret_key=self.alpaca_manager.secret_key,
                paper_trading=self.alpaca_manager.paper,
            )

            # Start the service and return if successful
            if pricing_service.start():
                logger.info("📡 Real-time pricing service started for smart execution")
                return pricing_service
            logger.warning(
                "⚠️ Real-time pricing service failed to start, using fallback execution"
            )
            return None

        except Exception as e:
            logger.warning(f"⚠️ Could not initialize real-time pricing: {e}")
            return None

    def _determine_execution_urgency(self, item: RebalancePlanItemDTO) -> str:
        """Determine execution urgency for an order item.

        Args:
            item: Rebalance plan item

        Returns:
            Urgency level: "LOW", "NORMAL", or "HIGH"

        """
        # Check if this is a complete exit (urgency should be higher)
        is_complete_exit = (
            item.action == "SELL"
            and hasattr(item, "target_weight")
            and item.target_weight == Decimal("0")
        )

        if is_complete_exit:
            return "HIGH"

        # Check trade size relative to typical amounts (simplified heuristic)
        if abs(item.trade_amount) > Decimal("10000"):  # Large trades get normal urgency
            return "NORMAL"
        return "LOW"  # Smaller trades can wait for better execution

    async def _execute_trade_item_smart(
        self, item: RebalancePlanItemDTO
    ) -> OrderResultDTO:
        """Execute a single trade item using smart execution strategy.

        Args:
            item: RebalancePlanItemDTO to execute

        Returns:
            OrderResultDTO with execution result

        """
        timestamp = datetime.now(UTC)

        if not self.smart_strategy:
            # Fallback to legacy execution
            return self._execute_trade_item_legacy(item)

        try:
            # Determine execution parameters
            urgency = self._determine_execution_urgency(item)
            is_complete_exit = (
                item.action == "SELL"
                and hasattr(item, "target_weight")
                and item.target_weight == Decimal("0")
            )

            # Calculate shares for the order
            # Get current price for quantity calculation
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

            price_decimal = Decimal(str(price))
            shares = abs(item.trade_amount) / price_decimal

            # Create smart order request
            smart_request = SmartOrderRequest(
                symbol=item.symbol,
                side=item.action,
                quantity=shares,
                correlation_id=getattr(item, "correlation_id", "unknown"),
                urgency=urgency,
                is_complete_exit=is_complete_exit,
            )

            # Execute smart order
            smart_result = await self.smart_strategy.place_smart_order(smart_request)

            # Convert smart result to OrderResultDTO
            if smart_result.success:
                logger.info(
                    f"✅ Smart order executed: {item.action} {shares:.4f} shares {item.symbol} → {smart_result.order_id}"
                )

                return OrderResultDTO(
                    symbol=item.symbol,
                    action=item.action,
                    trade_amount=item.trade_amount,
                    shares=shares,
                    price=smart_result.final_price or price_decimal,
                    order_id=smart_result.order_id,
                    success=True,
                    error_message=None,
                    timestamp=smart_result.placement_timestamp or timestamp,
                )
            # Smart execution failed, try fallback based on urgency
            if urgency in ["HIGH", "NORMAL"]:
                logger.warning(
                    f"Smart execution failed for {item.symbol}, falling back to market order"
                )
                return self._execute_trade_item_legacy(item)
            # For low urgency, fail gracefully rather than using market orders
            logger.error(
                f"❌ Smart execution failed for {item.symbol}: {smart_result.error_message}"
            )
            return OrderResultDTO(
                symbol=item.symbol,
                action=item.action,
                trade_amount=item.trade_amount,
                shares=shares,
                price=price_decimal,
                order_id=None,
                success=False,
                error_message=smart_result.error_message,
                timestamp=timestamp,
            )

        except Exception as e:
            logger.error(
                f"❌ Unexpected error in smart execution for {item.action} {item.symbol}: {e}"
            )
            # Fallback to legacy execution for any unexpected errors
            return self._execute_trade_item_legacy(item)

    def _execute_trade_item_legacy(self, item: RebalancePlanItemDTO) -> OrderResultDTO:
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
