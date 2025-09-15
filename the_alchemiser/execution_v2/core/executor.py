"""Business Unit: execution | Status: current.

Executor that consumes RebalancePlanDTO and places orders.

Core principle: iterate through plan items and place orders - nothing more.
No portfolio calculations, position fetching, or trade recalculation.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from the_alchemiser.execution_v2.models.execution_result import (
    ExecutionResultDTO,
    OrderResultDTO,
)
from the_alchemiser.execution_v2.strategies.async_smart_strategy import AsyncSmartExecutionStrategy
from the_alchemiser.execution_v2.strategies.smart_limit_strategy import SmartLimitExecutionStrategy
from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.config.config import load_settings
from the_alchemiser.shared.dto.rebalance_plan_dto import RebalancePlanDTO, RebalancePlanItemDTO
from the_alchemiser.shared.services.real_time_pricing import RealTimePricingService

logger = logging.getLogger(__name__)


class Executor:
    """Executor that processes RebalancePlanDTO items."""

    def __init__(self, alpaca_manager: AlpacaManager) -> None:
        """Initialize with AlpacaManager."""
        self.alpaca_manager = alpaca_manager
        self.config = load_settings().execution
        
        # Initialize smart execution strategy if enabled
        self.smart_strategy: SmartLimitExecutionStrategy | None = None
        self.async_strategy: AsyncSmartExecutionStrategy | None = None
        
        if self.config.use_smart_limit_execution:
            pricing_service = RealTimePricingService()
            self.smart_strategy = SmartLimitExecutionStrategy(
                alpaca_manager=alpaca_manager,
                pricing_service=pricing_service,
                config=self.config
            )
            
            # Also create async strategy for enhanced concurrent execution
            self.async_strategy = AsyncSmartExecutionStrategy(
                alpaca_manager=alpaca_manager,
                pricing_service=pricing_service,
                config=self.config
            )

    def execute_rebalance_plan(self, plan: RebalancePlanDTO) -> ExecutionResultDTO:
        """Execute rebalance plan using optimal strategy based on configuration and order mix.

        Combines smart execution with phased execution strategy:
        - For mixed SELL/BUY orders: Uses phased SELL-first strategy to prevent buying power issues
        - For single-type orders: Uses smart execution if enabled, otherwise sequential execution
        - Async execution available for concurrent processing when beneficial

        Args:
            plan: RebalancePlanDTO with items to execute

        Returns:
            ExecutionResultDTO with order results and success status

        """
        logger.info(f"🚀 Executing rebalance plan {plan.plan_id} with {len(plan.items)} items")

        # Analyze order mix to determine optimal execution strategy
        sell_items = [item for item in plan.items if item.action == "SELL"]
        buy_items = [item for item in plan.items if item.action == "BUY"]
        
        # For mixed SELL/BUY orders, use phased execution to prevent buying power issues
        if sell_items and buy_items:
            logger.info(f"📊 Using phased execution: {len(sell_items)} SELL orders → monitor buying power → {len(buy_items)} BUY orders")
            return self._execute_phased_plan(plan, sell_items, buy_items)
        
        # For single-type orders, use smart execution if available
        if self.smart_strategy:
            # Use async execution for multiple items if enabled and beneficial
            if self.async_strategy and len(plan.items) > 1 and self.config.use_async_execution:
                logger.info("Using async smart execution strategy for concurrent execution")
                return asyncio.run(self._execute_plan_with_async_strategy(plan))
            else:
                logger.info("Using smart limit execution strategy")
                return asyncio.run(self._execute_plan_async(plan))
        
        # Fallback to sequential execution
        logger.info(f"📦 Using sequential execution for {len(plan.items)} items")
        return self._execute_sequential_plan(plan)

    async def _execute_plan_with_async_strategy(self, plan: RebalancePlanDTO) -> ExecutionResultDTO:
        """Execute plan using enhanced async strategy with full concurrency."""
        logger.info(f"🌊 Concurrent async execution for {len(plan.items)} items")
        
        # Execute with full async capabilities
        execution_results = await self.async_strategy.execute_rebalance_plan_async(plan)
        
        # Convert to ExecutionResultDTO format
        orders: list[OrderResultDTO] = []
        total_trade_value = Decimal("0")
        
        for symbol, executed_order in execution_results.items():
            # Find corresponding plan item
            plan_item = next(
                (item for item in plan.items if item.symbol == symbol), 
                None
            )
            if not plan_item:
                continue
                
            order_result = self._convert_executed_order_to_result(executed_order, plan_item)
            orders.append(order_result)
            
            if order_result.success:
                total_trade_value += abs(plan_item.trade_amount)
        
        # Calculate summary
        orders_placed = len(orders)
        orders_succeeded = sum(1 for order in orders if order.success)
        overall_success = orders_succeeded == orders_placed if orders_placed > 0 else True
        
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
            f"✅ Async execution complete: {orders_succeeded}/{orders_placed} orders succeeded "
            f"(${total_trade_value} traded)"
        )
        
        return result

    async def _execute_plan_async(self, plan: RebalancePlanDTO) -> ExecutionResultDTO:
        """Execute plan using async smart limit strategy."""
        orders: list[OrderResultDTO] = []
        total_trade_value = Decimal("0")

        for item in plan.items:
            # Skip HOLD actions - only process trades
            if item.action == "HOLD":
                logger.debug(f"⏭️ Skipping HOLD action for {item.symbol}")
                continue

            logger.info(f"📦 Processing {item.action} ${item.trade_amount} {item.symbol}")

            # Execute using smart strategy if available, otherwise legacy execution
            if self.smart_strategy:
                price_fallback = self._get_current_price_fallback(item.symbol)
                quantity = float(abs(item.trade_amount) / price_fallback)
                executed_order = self.smart_strategy.execute_smart_limit_order(
                    symbol=item.symbol,
                    side=item.action.lower(),
                    quantity=quantity
                )
                order_result = self._convert_executed_order_to_result(executed_order, item)
            else:
                # Use legacy market order execution
                order_result = self._execute_trade_item(item)
            
            orders.append(order_result)

            if order_result.success:
                total_trade_value += abs(item.trade_amount)

        # Calculate summary statistics
        orders_placed = len(orders)
        orders_succeeded = sum(1 for order in orders if order.success)
        overall_success = orders_succeeded == orders_placed if orders_placed > 0 else True

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
            f"✅ Sequential execution complete: {orders_succeeded}/{orders_placed} orders succeeded "
            f"(${total_trade_value} traded)"
        )

        return result

    def _execute_phased_plan(
        self, 
        plan: RebalancePlanDTO, 
        sell_items: list[RebalancePlanItemDTO], 
        buy_items: list[RebalancePlanItemDTO]
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
        logger.info(f"🔴 Phase 1: Executing {len(sell_items)} SELL orders to release buying power")
        sell_order_ids = []
        
        for item in sell_items:
            logger.info(f"📦 Processing SELL ${item.trade_amount} {item.symbol}")
            
            # Use smart execution if available, otherwise legacy execution
            if self.smart_strategy:
                price_fallback = self._get_current_price_fallback(item.symbol)
                quantity = float(abs(item.trade_amount) / price_fallback)
                executed_order = self.smart_strategy.execute_smart_limit_order(
                    symbol=item.symbol,
                    side=item.action.lower(),
                    quantity=quantity
                )
                order_result = self._convert_executed_order_to_result(executed_order, item)
            else:
                order_result = self._execute_trade_item(item)
                
            all_orders.append(order_result)
            
            if order_result.success:
                total_trade_value += abs(item.trade_amount)
                if order_result.order_id:
                    sell_order_ids.append(order_result.order_id)

        # Phase 2: Monitor SELL order completion and buying power
        if sell_order_ids:
            logger.info(f"⏱️ Phase 2: Monitoring {len(sell_order_ids)} SELL orders for completion")
            initial_buying_power = self._get_current_buying_power()
            
            # Wait for SELL orders to complete (max 60 seconds)
            websocket_result = self.alpaca_manager.wait_for_order_completion(
                sell_order_ids, max_wait_seconds=60
            )
            
            if websocket_result.status.value == "completed":
                logger.info(f"✅ All SELL orders completed successfully")
                
                # Monitor buying power increase
                self._wait_for_buying_power_increase(initial_buying_power, buy_items)
            else:
                logger.warning(f"⚠️ SELL order monitoring completed with status: {websocket_result.status.value}")
                logger.warning(f"Completed {len(websocket_result.completed_order_ids)}/{len(sell_order_ids)} orders")

        # Phase 3: Execute BUY orders with available buying power
        logger.info(f"🟢 Phase 3: Executing {len(buy_items)} BUY orders")
        
        for item in buy_items:
            logger.info(f"📦 Processing BUY ${item.trade_amount} {item.symbol}")
            
            # Use smart execution if available, otherwise legacy execution
            if self.smart_strategy:
                price_fallback = self._get_current_price_fallback(item.symbol)
                quantity = float(abs(item.trade_amount) / price_fallback)
                executed_order = self.smart_strategy.execute_smart_limit_order(
                    symbol=item.symbol,
                    side=item.action.lower(),
                    quantity=quantity
                )
                order_result = self._convert_executed_order_to_result(executed_order, item)
            else:
                order_result = self._execute_trade_item(item)
                
            all_orders.append(order_result)
            
            if order_result.success:
                total_trade_value += abs(item.trade_amount)

        # Calculate combined results
        orders_placed = len(all_orders)
        orders_succeeded = sum(1 for order in all_orders if order.success)
        overall_success = orders_succeeded == orders_placed if orders_placed > 0 else True

        result = ExecutionResultDTO(
            success=overall_success,
            plan_id=plan.plan_id,
            correlation_id=plan.correlation_id,
            orders=all_orders,
            orders_placed=orders_placed,
            orders_succeeded=orders_succeeded,
            total_trade_value=total_trade_value,
            execution_timestamp=datetime.now(UTC),
            metadata={"execution_strategy": "phased_sell_first"}
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

    def _calculate_required_buying_power(self, buy_items: list[RebalancePlanItemDTO]) -> Decimal:
        """Calculate total buying power required for BUY orders.

        Args:
            buy_items: List of BUY order items

        Returns:
            Total dollar amount needed for all BUY orders

        """
        return sum(abs(item.trade_amount) for item in buy_items)

    def _wait_for_buying_power_increase(
        self, 
        initial_buying_power: Decimal, 
        buy_items: list[RebalancePlanItemDTO],
        max_wait_seconds: int = 30
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
        logger.info(f"💰 Monitoring buying power increase (need ${required_buying_power})")
        
        import time
        start_time = time.time()
        check_interval = 2  # Check every 2 seconds
        
        while (time.time() - start_time) < max_wait_seconds:
            current_buying_power = self._get_current_buying_power()
            buying_power_increase = current_buying_power - initial_buying_power
            
            logger.debug(f"💰 Buying power: ${current_buying_power} (increase: ${buying_power_increase})")
            
            # Check if we have sufficient buying power for all BUY orders
            if current_buying_power >= required_buying_power:
                logger.info(f"✅ Sufficient buying power available: ${current_buying_power} >= ${required_buying_power}")
                return True
            
            # Also check if buying power increased significantly (SELL proceeds available)
            if buying_power_increase > Decimal("100"):  # At least $100 increase suggests SELL completion
                logger.info(f"✅ Buying power increased by ${buying_power_increase}, proceeding with BUY orders")
                return True
            
            time.sleep(check_interval)
        
        current_buying_power = self._get_current_buying_power()
        logger.warning(f"⚠️ Buying power monitoring timeout after {max_wait_seconds}s")
        logger.warning(f"💰 Final buying power: ${current_buying_power}, required: ${required_buying_power}")
        
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
            # Get current price
            # TODO: Migrate to enhanced pricing with real-time quotes for better execution
            # Consider using get_quote_data() for bid/ask spreads and market depth
            # or get_price_data() for volume-weighted pricing from structured types
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
                symbol=item.symbol, side=side, qty=float(shares), is_complete_exit=is_complete_exit
            )

            # Extract results from ExecutedOrderDTO
            order_id = (
                executed_order.order_id
                if executed_order.order_id != "FAILED" and executed_order.order_id != "INVALID"
                else None
            )
            success = executed_order.status not in ["REJECTED", "FAILED"] and order_id is not None
            error_message = executed_order.error_message if not success else None

            if success:
                logger.info(
                    f"✅ Order placed: {item.action} {shares:.4f} shares {item.symbol} → {order_id}"
                )
            else:
                logger.error(f"❌ Order failed: {item.action} {item.symbol} - {error_message}")

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
            logger.error(f"❌ Unexpected error executing {item.action} {item.symbol}: {e}")
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

    def _convert_executed_order_to_result(
        self, executed_order: Any, item: RebalancePlanItemDTO
    ) -> OrderResultDTO:
        """Convert ExecutedOrderDTO to OrderResultDTO for consistency."""
        timestamp = datetime.now(UTC)
        
        # Handle different types of executed order results
        if hasattr(executed_order, "order_id"):
            order_id = (
                executed_order.order_id 
                if executed_order.order_id not in ["FAILED", "DELAYED"] 
                else None
            )
            success = executed_order.status not in ["REJECTED", "FAILED", "DELAYED"]
            error_message = getattr(executed_order, "error_message", None)
            price = (
                executed_order.price 
                if hasattr(executed_order, "price") 
                else Decimal("0")
            )
            shares = (
                executed_order.quantity 
                if hasattr(executed_order, "quantity") 
                else Decimal("0")
            )
        else:
            # Fallback for unexpected result types
            order_id = None
            success = False
            error_message = "Unexpected result format"
            price = Decimal("0")
            shares = Decimal("0")

        return OrderResultDTO(
            symbol=item.symbol,
            action=item.action,
            trade_amount=item.trade_amount,
            shares=shares,
            price=price,
            order_id=order_id,
            success=success,
            error_message=error_message,
            timestamp=timestamp,
        )

    def _get_current_price_fallback(self, symbol: str) -> float:
        """Get current price with fallback for quantity calculation."""
        try:
            price = self.alpaca_manager.get_current_price(symbol)
            return price if price and price > 0 else 1.0  # Fallback to $1 to avoid division by zero
        except Exception:
            return 1.0  # Safe fallback

    def get_execution_capabilities(self) -> dict[str, Any]:
        """Get information about current execution capabilities.
        
        Returns:
            Dictionary with execution capability information

        """
        capabilities = {
            "smart_execution_enabled": self.config.use_smart_limit_execution,
            "async_execution_enabled": self.config.use_async_execution,
            "legacy_execution_available": True,
            "market_timing_aware": True,
            "spread_validation": True,
            "volume_validation": True,
            "re_pegging_supported": True,
        }
        
        if self.async_strategy:
            capabilities.update(self.async_strategy.get_execution_statistics())
        
        return capabilities
