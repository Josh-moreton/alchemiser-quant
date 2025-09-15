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
from the_alchemiser.execution_v2.strategies.smart_limit_strategy import SmartLimitExecutionStrategy
from the_alchemiser.execution_v2.strategies.async_smart_strategy import AsyncSmartExecutionStrategy
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
        """Execute rebalance plan by iterating items and placing orders.

        Args:
            plan: RebalancePlanDTO with items to execute

        Returns:
            ExecutionResultDTO with order results and success status

        """
        logger.info(f"🚀 Executing rebalance plan {plan.plan_id} with {len(plan.items)} items")

        # Use async execution if smart strategy is enabled and plan has multiple items
        if self.async_strategy and len(plan.items) > 1 and self.config.use_async_execution:
            logger.info("Using async smart execution strategy for concurrent execution")
            return asyncio.run(self._execute_plan_with_async_strategy(plan))
        elif self.smart_strategy:
            logger.info("Using smart limit execution strategy")
            return asyncio.run(self._execute_plan_async(plan))
        else:
            logger.info("Using legacy market order execution")
            return self._execute_plan_legacy(plan)

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

            # Execute using smart strategy
            price_fallback = self._get_current_price_fallback(item.symbol)
            quantity = float(abs(item.trade_amount) / price_fallback)
            executed_order = await self.smart_strategy.execute_smart_limit_order(
                symbol=item.symbol,
                side=item.action.lower(),
                quantity=quantity
            )

            # Convert to OrderResultDTO
            order_result = self._convert_executed_order_to_result(executed_order, item)
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
            f"✅ Smart execution complete: {orders_succeeded}/{orders_placed} orders succeeded "
            f"(${total_trade_value} traded)"
        )

        return result

    def _execute_plan_legacy(self, plan: RebalancePlanDTO) -> ExecutionResultDTO:
        """Execute plan using legacy market order strategy."""
        orders: list[OrderResultDTO] = []
        total_trade_value = Decimal("0")

        for item in plan.items:
            # Skip HOLD actions - only process trades
            if item.action == "HOLD":
                logger.debug(f"⏭️ Skipping HOLD action for {item.symbol}")
                continue

            logger.info(f"📦 Processing {item.action} ${item.trade_amount} {item.symbol}")

            # Execute the trade using legacy method
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
            f"✅ Legacy execution complete: {orders_succeeded}/{orders_placed} orders succeeded "
            f"(${total_trade_value} traded)"
        )

        return result

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
        if hasattr(executed_order, 'order_id'):
            order_id = (
                executed_order.order_id 
                if executed_order.order_id not in ["FAILED", "DELAYED"] 
                else None
            )
            success = executed_order.status not in ["REJECTED", "FAILED", "DELAYED"]
            error_message = getattr(executed_order, 'error_message', None)
            price = (
                executed_order.price 
                if hasattr(executed_order, 'price') 
                else Decimal("0")
            )
            shares = (
                executed_order.quantity 
                if hasattr(executed_order, 'quantity') 
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
