"""Business Unit: execution | Status: current

Core executor for order placement and smart execution.
"""

from __future__ import annotations

import logging
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

        Args:
            plan: RebalancePlanDTO containing the rebalance plan

        Returns:
            ExecutionResultDTO with execution results

        """
        logger.info(
            f"🚀 Executing rebalance plan {plan.plan_id} with {len(plan.items)} items"
        )

        orders: list[OrderResultDTO] = []
        orders_placed = 0
        orders_succeeded = 0
        total_trade_value = Decimal("0")

        for item in plan.items:
            if item.action == "HOLD":
                logger.info(f"⏸️ Holding {item.symbol} - no action required")
                continue

            try:
                # Execute order for this item
                side = "buy" if item.action == "BUY" else "sell"
                shares = abs(item.trade_amount / Decimal("100"))  # Simple approximation

                logger.info(
                    f"📊 Executing {item.action} for {item.symbol}: "
                    f"${item.trade_amount} ({shares} shares)"
                )

                # Use synchronous execution for now (could be made async later)
                result = self._execute_market_order(
                    symbol=item.symbol,
                    side=side,
                    quantity=float(shares),
                )

                orders_placed += 1

                # Create order result
                order_result = OrderResultDTO(
                    symbol=item.symbol,
                    action=item.action,
                    trade_amount=abs(item.trade_amount),
                    shares=shares,
                    price=Decimal(str(result.price)) if result.price else None,
                    order_id=result.order_id,
                    success=result.success,
                    error_message=getattr(result, "error", None),
                    timestamp=datetime.now(UTC),
                )
                orders.append(order_result)

                if result.success:
                    orders_succeeded += 1
                    total_trade_value += abs(item.trade_amount)
                    logger.info(
                        f"✅ Successfully executed {item.action} for {item.symbol}"
                    )
                else:
                    logger.error(
                        f"❌ Failed to execute {item.action} for {item.symbol}"
                    )

            except Exception as e:
                logger.error(f"❌ Error executing {item.action} for {item.symbol}: {e}")
                orders_placed += 1

                order_result = OrderResultDTO(
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
                orders.append(order_result)

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

    def shutdown(self) -> None:
        """Shutdown the executor and cleanup resources."""
        if self.pricing_service:
            try:
                self.pricing_service.stop()
                logger.info("✅ Pricing service stopped")
            except Exception as e:
                logger.debug(f"Error stopping pricing service: {e}")
