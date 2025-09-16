"""Business Unit: execution | Status: current

Core executor for order placement and smart execution.
"""

from __future__ import annotations

import logging
import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from the_alchemiser.execution_v2.core.smart_execution_strategy import (
    SmartExecutionStrategy,
    SmartOrderRequest,
)
from the_alchemiser.execution_v2.models.execution_result import (
    ExecutionResultDTO,
    OrderResultDTO,
)
from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.dto.rebalance_plan_dto import RebalancePlanItemDTO
from the_alchemiser.shared.dto.execution_dto import ExecutionResult
from the_alchemiser.shared.dto.rebalance_plan_dto import RebalancePlanDTO
from the_alchemiser.shared.services.real_time_pricing import RealTimePricingService

if TYPE_CHECKING:
    from the_alchemiser.execution_v2.core.smart_execution_strategy import (
        ExecutionConfig,
    )

logger = logging.getLogger(__name__)


class Executor:
    """Core executor for order placement."""

    def __init__(
        self,
        alpaca_manager: AlpacaManager,
        execution_config: ExecutionConfig | None = None,
        enable_smart_execution: bool = True,
    ) -> None:
        """Initialize the executor.

        Args:
            alpaca_manager: Alpaca broker manager
            execution_config: Execution configuration
            enable_smart_execution: Whether to enable smart execution

        """
        self.alpaca_manager = alpaca_manager
        self.enable_smart_execution = enable_smart_execution
        self.execution_config = execution_config

        # Initialize pricing service for smart execution
        self.pricing_service: RealTimePricingService | None = None
        self.smart_strategy: SmartExecutionStrategy | None = None

        if enable_smart_execution:
            try:
                logger.info("🚀 Initializing smart execution with real-time pricing...")

                # Create pricing service with proper credentials
                self.pricing_service = RealTimePricingService()

                # Start the pricing service
                if self.pricing_service.start():
                    logger.info("✅ Real-time pricing service started successfully")

                    # Create smart execution strategy
                    self.smart_strategy = SmartExecutionStrategy(
                        alpaca_manager=alpaca_manager,
                        pricing_service=self.pricing_service,
                        config=execution_config,
                    )
                    logger.info("✅ Smart execution strategy initialized")
                else:
                    logger.error("❌ Failed to start real-time pricing service")
                    self.enable_smart_execution = False

            except Exception as e:
                logger.error(
                    f"❌ Error initializing smart execution: {e}", exc_info=True
                )
                self.enable_smart_execution = False
                self.pricing_service = None
                self.smart_strategy = None

    async def execute_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = "market",
        correlation_id: str | None = None,
    ) -> ExecutionResult:
        """Execute an order with smart execution if enabled.

        Args:
            symbol: Stock symbol
            side: "buy" or "sell"
            quantity: Number of shares
            order_type: "market" or "limit"
            correlation_id: Correlation ID for tracking

        Returns:
            ExecutionResult with order details

        """
        # Try smart execution first if enabled
        if self.enable_smart_execution and self.smart_strategy:
            try:
                logger.info(f"🎯 Attempting smart execution for {symbol}")

                request = SmartOrderRequest(
                    symbol=symbol,
                    side=side.upper(),
                    quantity=quantity,
                    correlation_id=correlation_id or "",
                    urgency="NORMAL",
                )

                result = await self.smart_strategy.place_smart_order(request)

                if result.success:
                    logger.info(f"✅ Smart execution succeeded for {symbol}")
                    return ExecutionResult(
                        order_id=result.order_id,
                        symbol=symbol,
                        side=side,
                        quantity=quantity,
                        price=float(result.final_price) if result.final_price else None,
                        status="submitted",
                        success=True,
                        execution_strategy=result.execution_strategy,
                    )
                logger.warning(
                    f"⚠️ Smart execution failed for {symbol}: {result.error_message}"
                )

            except Exception as e:
                logger.error(f"❌ Smart execution failed for {symbol}: {e}")

        # Fallback to regular market order
        logger.info(f"📈 Using standard market order for {symbol}")
        return self._execute_market_order(symbol, side, quantity)

    def _execute_market_order(
        self, symbol: str, side: str, quantity: float
    ) -> ExecutionResult:
        """Execute a standard market order.

        Args:
            symbol: Stock symbol
            side: "buy" or "sell"
            quantity: Number of shares

        Returns:
            ExecutionResult with order details

        """
        try:
            result = self.alpaca_manager.place_market_order(
                symbol=symbol,
                side=side.lower(),
                qty=quantity,
            )

            return ExecutionResult(
                order_id=result.order_id,
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=result.price,
                status=result.status.lower() if result.status else "submitted",
                success=result.status not in ["REJECTED", "CANCELED"],
                execution_strategy="market_order",
            )

        except Exception as e:
            logger.error(f"❌ Market order failed for {symbol}: {e}")
            return ExecutionResult(
                symbol=symbol,
                side=side,
                quantity=quantity,
                status="failed",
                success=False,
                error=str(e),
                execution_strategy="market_order_failed",
            )

    def execute_rebalance_plan(self, plan: RebalancePlanDTO) -> ExecutionResultDTO:
        """Execute a rebalance plan with all its items.

        Executes in two phases:
        1. Pre-subscribe to all symbols to avoid connection limit issues
        2. SELL orders first to free up buying power
        3. BUY orders second with the freed buying power

        Args:
            plan: RebalancePlanDTO containing the rebalance plan

        Returns:
            ExecutionResultDTO with execution results

        """
        logger.info(
            f"🚀 Executing rebalance plan {plan.plan_id} with {len(plan.items)} items"
        )

        # Pre-subscribe to all symbols at once to avoid connection limits
        if self.pricing_service and self.enable_smart_execution:
            all_symbols = {
                item.symbol for item in plan.items if item.action in ["BUY", "SELL"]
            }
            if all_symbols:
                logger.info(f"📡 Pre-subscribing to all symbols: {sorted(all_symbols)}")
                for symbol in sorted(all_symbols):  # Sort for consistent ordering
                    self.pricing_service.subscribe_for_order_placement(symbol)
                logger.info(f"✅ Pre-subscribed to {len(all_symbols)} symbols")

        orders: list[OrderResultDTO] = []
        orders_placed = 0
        orders_succeeded = 0
        total_trade_value = Decimal("0")

        # Separate SELL and BUY orders
        sell_items = [item for item in plan.items if item.action == "SELL"]
        buy_items = [item for item in plan.items if item.action == "BUY"]
        hold_items = [item for item in plan.items if item.action == "HOLD"]

        logger.info(
            f"📊 Execution plan: {len(sell_items)} SELLs, {len(buy_items)} BUYs, {len(hold_items)} HOLDs"
        )

        # Phase 1: Execute SELL orders first to free up buying power
        if sell_items:
            logger.info("🔄 Phase 1: Executing SELL orders to free buying power...")
            for item in sell_items:
                order_result = self._execute_single_item(item)
                orders.append(order_result)
                orders_placed += 1
                if order_result.success:
                    orders_succeeded += 1
                    total_trade_value += abs(item.trade_amount)
                    logger.info(f"✅ SELL {item.symbol} completed successfully")
                else:
                    logger.error(f"❌ SELL {item.symbol} failed")

        # Phase 2: Execute BUY orders with freed buying power
        if buy_items:
            logger.info("🔄 Phase 2: Executing BUY orders with freed buying power...")
            for item in buy_items:
                order_result = self._execute_single_item(item)
                orders.append(order_result)
                orders_placed += 1
                if order_result.success:
                    orders_succeeded += 1
                    total_trade_value += abs(item.trade_amount)
                    logger.info(f"✅ BUY {item.symbol} completed successfully")
                else:
                    logger.error(f"❌ BUY {item.symbol} failed")

        # Log HOLD items
        for item in hold_items:
            logger.info(f"⏸️ Holding {item.symbol} - no action required")

        # Create execution result
        execution_result = ExecutionResultDTO(
            success=orders_succeeded == orders_placed and orders_placed > 0,
            plan_id=plan.plan_id,
            correlation_id=plan.correlation_id,
            orders=orders,
            orders_placed=orders_placed,
            orders_succeeded=orders_succeeded,
            total_trade_value=total_trade_value,
            execution_timestamp=datetime.now(UTC),
        )

        logger.info(
            f"✅ Rebalance plan {plan.plan_id} completed: "
            f"{orders_succeeded}/{orders_placed} orders succeeded"
        )

        return execution_result

    def _execute_single_item(self, item: RebalancePlanItemDTO) -> OrderResultDTO:
        """Execute a single rebalance plan item.

        Args:
            item: RebalancePlanItemDTO to execute

        Returns:
            OrderResultDTO with execution results

        """
        try:
            side = "buy" if item.action == "BUY" else "sell"

            # Calculate shares based on action type
            if item.action == "SELL" and item.target_weight == Decimal("0.0"):
                # For liquidation (0% target), get actual position quantity
                shares = self._get_position_quantity(item.symbol)
                logger.info(
                    f"📊 Liquidating {item.symbol}: selling {shares} shares (full position)"
                )
            else:
                # For other orders, estimate shares from trade amount
                # This is a simplified calculation - could be improved with real-time price
                estimated_price = abs(
                    item.trade_amount
                    / max(item.current_value / Decimal("100"), Decimal("1"))
                )
                shares = (
                    abs(item.trade_amount / estimated_price)
                    if estimated_price > 0
                    else Decimal("1")
                )
                logger.info(
                    f"📊 Executing {item.action} for {item.symbol}: "
                    f"${item.trade_amount} (estimated {shares} shares)"
                )

            # Use smart execution with async context
            execution_result = asyncio.run(
                self.execute_order(
                    symbol=item.symbol,
                    side=side,
                    quantity=float(shares),
                    order_type="limit",  # Use limit orders for smart execution
                    correlation_id=f"rebalance-{item.symbol}",
                )
            )

            # Create order result
            order_result = OrderResultDTO(
                symbol=item.symbol,
                action=item.action,
                trade_amount=abs(item.trade_amount),
                shares=shares,
                price=(
                    Decimal(str(execution_result.price))
                    if execution_result.price
                    else None
                ),
                order_id=execution_result.order_id,
                success=execution_result.success,
                error_message=getattr(execution_result, "error", None),
                timestamp=datetime.now(UTC),
            )

            if execution_result.success:
                logger.info(f"✅ Successfully executed {item.action} for {item.symbol}")
            else:
                logger.error(f"❌ Failed to execute {item.action} for {item.symbol}")

            return order_result

        except Exception as e:
            logger.error(f"❌ Error executing {item.action} for {item.symbol}: {e}")

            return OrderResultDTO(
                symbol=item.symbol,
                action=item.action,
                trade_amount=abs(item.trade_amount),
                shares=Decimal("0"),
                price=None,
                order_id=None,
                success=False,
                error_message=str(e),
                timestamp=datetime.now(UTC),
            )

    def _get_position_quantity(self, symbol: str) -> Decimal:
        """Get the actual quantity held for a symbol.

        Args:
            symbol: Stock symbol to check

        Returns:
            Decimal quantity owned, or 0 if no position exists

        """
        try:
            position = self.alpaca_manager.get_position(symbol)
            if position is None:
                logger.debug(f"No position found for {symbol}")
                return Decimal("0")

            # Use qty_available to account for shares tied up in orders
            qty = getattr(position, "qty_available", None) or getattr(
                position, "qty", 0
            )
            return Decimal(str(qty))
        except Exception as e:
            logger.warning(f"Error getting position for {symbol}: {e}")
            return Decimal("0")

    def shutdown(self) -> None:
        """Shutdown the executor and cleanup resources."""
        if self.pricing_service:
            try:
                self.pricing_service.stop()
                logger.info("✅ Pricing service stopped")
            except Exception as e:
                logger.debug(f"Error stopping pricing service: {e}")
