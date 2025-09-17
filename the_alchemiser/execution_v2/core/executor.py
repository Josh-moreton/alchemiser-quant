"""Business Unit: execution | Status: current.

Core executor for order placement and smart execution.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, TypedDict

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
from the_alchemiser.shared.dto.rebalance_plan_dto import (
    RebalancePlanDTO,
    RebalancePlanItemDTO,
)
from the_alchemiser.shared.services.real_time_pricing import RealTimePricingService

if TYPE_CHECKING:
    from the_alchemiser.execution_v2.core.smart_execution_strategy import (
        ExecutionConfig,
    )

logger = logging.getLogger(__name__)


class ExecutionStats(TypedDict):
    """Statistics for execution phase results."""

    placed: int
    succeeded: int
    trade_value: Decimal


class Executor:
    """Core executor for order placement."""

    def __init__(
        self,
        alpaca_manager: AlpacaManager,
        execution_config: ExecutionConfig | None = None,
        *,
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
        quantity: Decimal,
        correlation_id: str | None = None,
    ) -> ExecutionResult:
        """Execute an order with smart execution if enabled.

        Args:
            symbol: Stock symbol
            side: "buy" or "sell"
            quantity: Number of shares
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
                    quantity=Decimal(str(quantity)),
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
                        quantity=Decimal(str(quantity)),
                        price=(result.final_price if result.final_price else None),
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
        return self._execute_market_order(symbol, side, Decimal(str(quantity)))

    def _execute_market_order(
        self, symbol: str, side: str, quantity: Decimal
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
                qty=float(quantity),
            )

            return ExecutionResult(
                order_id=result.order_id,
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=(result.price if result.price is not None else None),
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

    async def execute_rebalance_plan(
        self, plan: RebalancePlanDTO
    ) -> ExecutionResultDTO:
        """Execute a rebalance plan with settlement-aware sell-first, buy-second workflow.

        Enhanced execution flow:
        1. Extract and bulk-subscribe to all symbols upfront
        2. Execute SELL orders in parallel where possible
        3. Monitor settlement and buying power release
        4. Execute BUY orders once sufficient buying power is available

        Args:
            plan: RebalancePlanDTO containing the rebalance plan

        Returns:
            ExecutionResultDTO with execution results

        """
        logger.info(
            f"🚀 Executing rebalance plan {plan.plan_id} with {len(plan.items)} items "
            "(enhanced settlement-aware)"
        )

        # Extract all symbols upfront for bulk subscription
        all_symbols = self._extract_all_symbols(plan)

        # Bulk subscribe to all symbols for efficient pricing
        self._bulk_subscribe_symbols(all_symbols)

        # Separate orders by type
        sell_items = [item for item in plan.items if item.action == "SELL"]
        buy_items = [item for item in plan.items if item.action == "BUY"]
        hold_items = [item for item in plan.items if item.action == "HOLD"]

        logger.info(
            f"📊 Execution plan: {len(sell_items)} SELLs, {len(buy_items)} BUYs, "
            f"{len(hold_items)} HOLDs"
        )

        orders: list[OrderResultDTO] = []
        orders_placed = 0
        orders_succeeded = 0
        total_trade_value = Decimal("0")

        # Phase 1: Execute SELL orders and monitor settlement
        sell_order_ids: list[str] = []
        if sell_items:
            logger.info(
                "🔄 Phase 1: Executing SELL orders with settlement monitoring..."
            )

            sell_orders, sell_stats = await self._execute_sell_phase(sell_items)
            orders.extend(sell_orders)
            orders_placed += sell_stats["placed"]
            orders_succeeded += sell_stats["succeeded"]
            total_trade_value += sell_stats["trade_value"]

            # Collect successful sell order IDs for settlement monitoring
            sell_order_ids = [
                order.order_id
                for order in sell_orders
                if order.success and order.order_id
            ]

        # Phase 2: Monitor settlement and execute BUY orders
        if buy_items and sell_order_ids:
            logger.info("🔄 Phase 2: Monitoring settlement and executing BUY orders...")

            # Wait for settlement and then execute buys
            buy_orders, buy_stats = (
                await self._execute_buy_phase_with_settlement_monitoring(
                    buy_items, sell_order_ids, plan.correlation_id, plan.plan_id
                )
            )

            orders.extend(buy_orders)
            orders_placed += buy_stats["placed"]
            orders_succeeded += buy_stats["succeeded"]
            total_trade_value += buy_stats["trade_value"]

        elif buy_items:
            # No sells to wait for, execute buys immediately
            logger.info(
                "🔄 Phase 2: Executing BUY orders (no settlement monitoring needed)..."
            )

            buy_orders, buy_stats = await self._execute_buy_phase(buy_items)
            orders.extend(buy_orders)
            orders_placed += buy_stats["placed"]
            orders_succeeded += buy_stats["succeeded"]
            total_trade_value += buy_stats["trade_value"]

        # Log HOLD items
        for item in hold_items:
            logger.info(f"⏸️ Holding {item.symbol} - no action required")

        # Clean up subscriptions after execution
        self._cleanup_subscriptions(all_symbols)

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

    def _extract_all_symbols(self, plan: RebalancePlanDTO) -> list[str]:
        """Extract all symbols from the rebalance plan.

        Args:
            plan: Rebalance plan to extract symbols from

        Returns:
            List of unique symbols in the plan

        """
        symbols = {item.symbol for item in plan.items if item.action in ["BUY", "SELL"]}
        sorted_symbols = sorted(symbols)
        logger.info(f"📋 Extracted {len(sorted_symbols)} unique symbols for execution")
        return sorted_symbols

    def _bulk_subscribe_symbols(self, symbols: list[str]) -> dict[str, bool]:
        """Bulk subscribe to all symbols for efficient real-time pricing.

        Args:
            symbols: List of symbols to subscribe to

        Returns:
            Dictionary mapping symbol to subscription success

        """
        if not self.pricing_service or not self.enable_smart_execution:
            logger.info("📡 Smart execution disabled, skipping bulk subscription")
            return {}

        if not symbols:
            return {}

        logger.info(
            f"📡 Bulk subscribing to {len(symbols)} symbols for real-time pricing"
        )

        # Use the enhanced bulk subscription method
        subscription_results = self.pricing_service.subscribe_symbols_bulk(
            symbols,
            priority=5.0,  # High priority for execution
        )

        successful_subscriptions = sum(
            1 for success in subscription_results.values() if success
        )
        logger.info(
            f"✅ Bulk subscription complete: {successful_subscriptions}/{len(symbols)} "
            "symbols subscribed"
        )

        return subscription_results

    async def _execute_sell_phase(
        self, sell_items: list[RebalancePlanItemDTO]
    ) -> tuple[list[OrderResultDTO], ExecutionStats]:
        """Execute sell orders phase with integrated re-pegging monitoring.

        Args:
            sell_items: List of sell order items

        Returns:
            Tuple of (order results, execution statistics)

        """
        orders = []
        placed = 0
        succeeded = 0
        trade_value = Decimal("0")

        # Execute all sell orders first
        for item in sell_items:
            order_result = await self._execute_single_item(item)
            orders.append(order_result)
            placed += 1

            if order_result.success:
                succeeded += 1
                trade_value += abs(item.trade_amount)
                logger.info(
                    f"✅ SELL {item.symbol} completed successfully (ID: {order_result.order_id})"
                )
            else:
                logger.error(
                    f"❌ SELL {item.symbol} failed: {order_result.error_message}"
                )

        # Monitor and re-peg sell orders that haven't filled
        if self.smart_strategy and self.enable_smart_execution:
            logger.info("🔄 Monitoring SELL orders for re-pegging opportunities...")
            await self._monitor_and_repeg_phase_orders("SELL", orders)

        return orders, {
            "placed": placed,
            "succeeded": succeeded,
            "trade_value": trade_value,
        }

    async def _execute_buy_phase_with_settlement_monitoring(
        self,
        buy_items: list[RebalancePlanItemDTO],
        sell_order_ids: list[str],
        correlation_id: str,
        plan_id: str,
    ) -> tuple[list[OrderResultDTO], ExecutionStats]:
        """Execute buy phase with settlement monitoring.

        Args:
            buy_items: List of buy order items
            sell_order_ids: List of sell order IDs to monitor
            correlation_id: Correlation ID for tracking
            plan_id: Execution plan ID

        Returns:
            Tuple of (order results, execution statistics)

        """
        # Initialize settlement monitor
        from .settlement_monitor import SettlementMonitor

        settlement_monitor = SettlementMonitor(
            alpaca_manager=self.alpaca_manager,
            event_bus=None,  # Could integrate with event bus later
            polling_interval_seconds=0.5,
            max_wait_seconds=60,
        )

        # Monitor sell order settlements
        logger.info(f"👀 Monitoring settlement of {len(sell_order_ids)} sell orders...")
        settlement_result = await settlement_monitor.monitor_sell_orders_settlement(
            sell_order_ids, correlation_id, plan_id
        )

        logger.info(
            f"💰 Settlement complete: ${settlement_result.total_buying_power_released} "
            "buying power released"
        )

        # Now execute buy orders with released buying power
        return await self._execute_buy_phase(buy_items)

    async def _execute_buy_phase(
        self, buy_items: list[RebalancePlanItemDTO]
    ) -> tuple[list[OrderResultDTO], ExecutionStats]:
        """Execute buy orders phase with integrated re-pegging monitoring.

        Args:
            buy_items: List of buy order items

        Returns:
            Tuple of (order results, execution statistics)

        """
        orders = []
        placed = 0
        succeeded = 0
        trade_value = Decimal("0")

        # Execute all buy orders first
        for item in buy_items:
            order_result = await self._execute_single_item(item)
            orders.append(order_result)
            placed += 1

            if order_result.success:
                succeeded += 1
                trade_value += abs(item.trade_amount)
                logger.info(
                    f"✅ BUY {item.symbol} completed successfully (ID: {order_result.order_id})"
                )
            else:
                logger.error(
                    f"❌ BUY {item.symbol} failed: {order_result.error_message}"
                )

        # Monitor and re-peg buy orders that haven't filled
        if self.smart_strategy and self.enable_smart_execution:
            logger.info("🔄 Monitoring BUY orders for re-pegging opportunities...")
            await self._monitor_and_repeg_phase_orders("BUY", orders)

        return orders, {
            "placed": placed,
            "succeeded": succeeded,
            "trade_value": trade_value,
        }

    async def _monitor_and_repeg_phase_orders(
        self, phase_type: str, orders: list[OrderResultDTO]
    ) -> None:
        """Monitor and re-peg orders from a specific execution phase.

        Args:
            phase_type: Type of phase ("SELL" or "BUY")
            orders: List of orders from this phase to monitor

        """
        # Wait a moment for orders to potentially fill before checking for re-pegging
        import asyncio

        await asyncio.sleep(1)

        # Check for re-pegging opportunities on orders from this phase
        if self.smart_strategy is not None:
            repeg_results = await self.smart_strategy.check_and_repeg_orders()
        else:
            repeg_results = []

        if repeg_results:
            logger.info(
                f"📊 {phase_type} phase re-pegging: {len(repeg_results)} orders processed"
            )
            for repeg_result in repeg_results:
                if repeg_result.success:
                    logger.info(
                        f"✅ {phase_type} re-peg successful: {repeg_result.order_id} "
                        f"(attempt {repeg_result.repegs_used})"
                    )
                else:
                    logger.warning(
                        f"⚠️ {phase_type} re-peg failed: {repeg_result.error_message}"
                    )
        else:
            logger.info(f"📊 {phase_type} phase: No re-pegging needed")

    def _cleanup_subscriptions(self, symbols: list[str]) -> None:
        """Clean up pricing subscriptions after execution.

        Args:
            symbols: List of symbols to clean up subscriptions for

        """
        if not self.pricing_service or not symbols:
            return

        logger.info(f"🧹 Cleaning up pricing subscriptions for {len(symbols)} symbols")

        for symbol in symbols:
            try:
                self.pricing_service.unsubscribe_after_order(symbol)
            except Exception as e:
                logger.warning(f"Error cleaning up subscription for {symbol}: {e}")

        logger.info("✅ Subscription cleanup complete")

    async def _execute_single_item(self, item: RebalancePlanItemDTO) -> OrderResultDTO:
        """Execute a single rebalance plan item.

        Args:
            item: RebalancePlanItemDTO to execute

        Returns:
            OrderResultDTO with execution results

        """
        try:
            side = "buy" if item.action == "BUY" else "sell"

            # Determine quantity (shares) to trade
            if item.action == "SELL" and item.target_weight == Decimal("0.0"):
                # For liquidation (0% target), use actual position quantity
                raw_shares = self._get_position_quantity(item.symbol)
                shares = raw_shares.quantize(Decimal("0.000001"))
                logger.info(
                    f"📊 Liquidating {item.symbol}: selling {shares} shares (full position)"
                )
            else:
                # Estimate shares from trade amount using best available price
                price = self._get_price_for_estimation(item.symbol)
                if price is None or price <= Decimal("0"):
                    # Safety fallback to 1 share if price discovery fails
                    shares = Decimal("1")
                    logger.warning(
                        f"⚠️ Price unavailable for {item.symbol}; defaulting to 1 share"
                    )
                else:
                    shares = (abs(item.trade_amount) / price).quantize(
                        Decimal("0.000001")
                    )

                amount_fmt = Decimal(str(abs(item.trade_amount))).quantize(
                    Decimal("0.01")
                )
                logger.info(
                    f"📊 Executing {item.action} for {item.symbol}: "
                    f"${amount_fmt} (estimated {shares} shares)"
                )

            # Use smart execution with async context
            execution_result = await self.execute_order(
                symbol=item.symbol,
                side=side,
                quantity=shares,
                correlation_id=f"rebalance-{item.symbol}",
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

    def _get_price_for_estimation(self, symbol: str) -> Decimal | None:
        """Get best-available current price for share estimation.

        Preference order:
        1) Real-time pricing service (mid/optimized)
        2) AlpacaManager current price utility

        Returns:
            Decimal price if available, otherwise None.

        """
        try:
            # Try real-time pricing first if smart execution enabled
            if self.pricing_service and self.enable_smart_execution:
                try:
                    price_rt = self.pricing_service.get_real_time_price(symbol)
                    if price_rt is None:
                        price_rt = self.pricing_service.get_optimized_price_for_order(
                            symbol
                        )
                    if price_rt is not None and price_rt > 0:
                        return Decimal(str(price_rt))
                except Exception as exc:
                    logger.debug(f"Real-time price lookup failed for {symbol}: {exc}")

            # Fallback to AlpacaManager's current price
            try:
                price = self.alpaca_manager.get_current_price(symbol)
                if price is not None and price > 0:
                    return Decimal(str(price))
            except Exception:
                return None
        except Exception:
            return None
        return None

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
