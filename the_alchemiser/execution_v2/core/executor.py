"""Business Unit: execution | Status: current.

Core executor for order placement and smart execution.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, TypedDict

from the_alchemiser.execution_v2.core.market_order_executor import MarketOrderExecutor
from the_alchemiser.execution_v2.core.order_finalizer import OrderFinalizer
from the_alchemiser.execution_v2.core.order_monitor import OrderMonitor
from the_alchemiser.execution_v2.core.phase_executor import PhaseExecutor
from the_alchemiser.execution_v2.core.smart_execution_strategy import (
    SmartExecutionStrategy,
    SmartOrderRequest,
)
from the_alchemiser.execution_v2.models.execution_result import (
    ExecutionResult,
    ExecutionStatus,
    OrderResult,
)
from the_alchemiser.execution_v2.services.trade_ledger import TradeLedgerService
from the_alchemiser.execution_v2.utils.execution_validator import (
    ExecutionValidator,
)
from the_alchemiser.execution_v2.utils.position_utils import PositionUtils
from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.logging import get_logger, log_order_flow
from the_alchemiser.shared.schemas.rebalance_plan import (
    RebalancePlan,
    RebalancePlanItem,
)
from the_alchemiser.shared.services.buying_power_service import BuyingPowerService
from the_alchemiser.shared.services.real_time_pricing import RealTimePricingService
from the_alchemiser.shared.services.websocket_manager import WebSocketConnectionManager
from the_alchemiser.shared.types.market_data import QuoteModel

if TYPE_CHECKING:
    from the_alchemiser.execution_v2.core.smart_execution_strategy import (
        ExecutionConfig,
    )

logger = get_logger(__name__)


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
    ) -> None:
        """Initialize the executor.

        Args:
            alpaca_manager: Alpaca broker manager
            execution_config: Execution configuration

        """
        self.alpaca_manager = alpaca_manager
        self.execution_config = execution_config

        # Initialize execution validator for preflight checks
        self.validator = ExecutionValidator(alpaca_manager)

        # Initialize buying power service for verification
        self.buying_power_service = BuyingPowerService(alpaca_manager)

        # Initialize pricing service for smart execution
        self.pricing_service: RealTimePricingService | None = None
        self.smart_strategy: SmartExecutionStrategy | None = None
        self.websocket_manager = None
        self.enable_smart_execution = True

        # Initialize extracted helper modules (will be set in _initialize_helper_modules)
        self._market_order_executor: MarketOrderExecutor
        self._order_monitor: OrderMonitor
        self._order_finalizer: OrderFinalizer
        self._position_utils: PositionUtils
        self._phase_executor: PhaseExecutor

        # Initialize trade ledger service
        self.trade_ledger = TradeLedgerService()

        # Initialize smart execution if enabled
        try:
            logger.info("🚀 Initializing smart execution with shared WebSocket connection...")

            # Use shared WebSocket connection manager to prevent connection limits
            self.websocket_manager = WebSocketConnectionManager(
                api_key=alpaca_manager.api_key,
                secret_key=alpaca_manager.secret_key,
                paper_trading=alpaca_manager.is_paper_trading,
            )

            # Get shared pricing service
            self.pricing_service = self.websocket_manager.get_pricing_service()
            logger.info("✅ Using shared real-time pricing service")

            # Create smart execution strategy with shared service
            self.smart_strategy = SmartExecutionStrategy(
                alpaca_manager=alpaca_manager,
                pricing_service=self.pricing_service,
                config=execution_config,
            )
            logger.info("✅ Smart execution strategy initialized with shared WebSocket")

            # Initialize helper modules for cleaner separation of concerns
            self._initialize_helper_modules()

        except Exception as e:
            logger.error(f"❌ Error initializing smart execution: {e}", exc_info=True)
            self.enable_smart_execution = False
            self.pricing_service = None
            self.smart_strategy = None
            self.websocket_manager = None
            # Initialize fallback modules
            self._initialize_helper_modules()

    def _initialize_helper_modules(self) -> None:
        """Initialize extracted helper modules."""
        self._market_order_executor = MarketOrderExecutor(
            self.alpaca_manager, self.validator, self.buying_power_service
        )
        self._order_monitor = OrderMonitor(self.smart_strategy, self.execution_config)
        self._order_finalizer = OrderFinalizer(self.alpaca_manager, self.execution_config)
        self._position_utils = PositionUtils(
            self.alpaca_manager,
            self.pricing_service,
            enable_smart_execution=self.enable_smart_execution,
        )
        self._phase_executor = PhaseExecutor(
            self.alpaca_manager,
            self._position_utils,
            self.smart_strategy,
            self.execution_config,
            enable_smart_execution=self.enable_smart_execution,
        )
        logger.debug("✅ Helper modules initialized")

    def __del__(self) -> None:
        """Clean up WebSocket connection when executor is destroyed."""
        if hasattr(self, "websocket_manager") and self.websocket_manager is not None:
            try:
                self.websocket_manager.release_pricing_service()
            except Exception as e:
                logger.debug(f"Error releasing WebSocket manager: {e}")

    async def execute_order(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        correlation_id: str | None = None,
    ) -> OrderResult:
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
                    # Success here means order was placed; fill will be checked later
                    log_order_flow(
                        logger,
                        stage="submission",
                        symbol=symbol,
                        quantity=Decimal(str(quantity)),
                        price=result.final_price,
                        order_id=result.order_id,
                        execution_strategy="smart_limit",
                    )
                    return OrderResult(
                        symbol=symbol,
                        action=side.upper(),
                        trade_amount=abs(
                            Decimal(str(quantity)) * (result.final_price or Decimal("0"))
                        ),
                        shares=Decimal(str(quantity)),
                        price=(result.final_price if result.final_price else None),
                        order_id=result.order_id,
                        success=True,
                        error_message=None,
                        timestamp=datetime.now(UTC),
                        order_type="LIMIT",  # Smart execution uses LIMIT orders
                        filled_at=result.placement_timestamp,  # Use placement timestamp from smart result
                    )
                logger.warning(f"⚠️ Smart execution failed for {symbol}: {result.error_message}")

            except Exception as e:
                logger.error(f"❌ Smart execution failed for {symbol}: {e}")

        # Fallback to regular market order
        logger.info(f"📈 Using standard market order for {symbol}")
        return self._execute_market_order(symbol, side, Decimal(str(quantity)))

    def _execute_market_order(self, symbol: str, side: str, quantity: Decimal) -> OrderResult:
        """Execute a standard market order with preflight validation.

        Args:
            symbol: Stock symbol
            side: "buy" or "sell"
            quantity: Number of shares

        Returns:
            ExecutionResult with order details

        """
        return self._market_order_executor.execute_market_order(symbol, side, quantity)

    async def execute_rebalance_plan(self, plan: RebalancePlan) -> ExecutionResult:
        """Execute a rebalance plan with settlement-aware sell-first, buy-second workflow.

        Enhanced execution flow:
        1. Extract and bulk-subscribe to all symbols upfront
        2. Execute SELL orders in parallel where possible
        3. Monitor settlement and buying power release
        4. Execute BUY orders once sufficient buying power is available

        Args:
            plan: RebalancePlan containing the rebalance plan

        Returns:
            ExecutionResult with execution results

        """
        logger.info(
            f"🚀 Executing rebalance plan {plan.plan_id} with {len(plan.items)} items "
            "(enhanced settlement-aware)"
        )

        # Cancel all orders to ensure clean order book at start
        logger.info("🧹 Cancelling all open orders to ensure clean order book...")
        cancel_success = self.alpaca_manager.cancel_all_orders()

        if cancel_success:
            logger.info("✅ All open orders cancelled successfully")
        else:
            logger.warning("⚠️ Failed to cancel all orders")

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

        orders: list[OrderResult] = []
        orders_placed = 0
        orders_succeeded = 0
        total_trade_value = Decimal("0")

        # Phase 1: Execute SELL orders and monitor settlement
        sell_order_ids: list[str] = []
        if sell_items:
            logger.info("🔄 Phase 1: Executing SELL orders with settlement monitoring...")

            sell_orders, sell_stats = await self._execute_sell_phase(
                sell_items, plan.correlation_id
            )
            orders.extend(sell_orders)
            orders_placed += sell_stats["placed"]
            orders_succeeded += sell_stats["succeeded"]
            total_trade_value += sell_stats["trade_value"]

            # Collect successful sell order IDs for settlement monitoring
            sell_order_ids = [
                order.order_id for order in sell_orders if order.success and order.order_id
            ]

        # Phase 2: Monitor settlement and execute BUY orders
        if buy_items and sell_order_ids:
            logger.info("🔄 Phase 2: Monitoring settlement and executing BUY orders...")

            # Wait for settlement and then execute buys
            buy_orders, buy_stats = await self._execute_buy_phase_with_settlement_monitoring(
                buy_items, sell_order_ids, plan.correlation_id, plan.plan_id
            )

            orders.extend(buy_orders)
            orders_placed += buy_stats["placed"]
            orders_succeeded += buy_stats["succeeded"]
            total_trade_value += buy_stats["trade_value"]

        elif buy_items:
            # No sells to wait for, execute buys immediately
            logger.info("🔄 Phase 2: Executing BUY orders (no settlement monitoring needed)...")

            buy_orders, buy_stats = await self._execute_buy_phase(buy_items, plan.correlation_id)
            orders.extend(buy_orders)
            orders_placed += buy_stats["placed"]
            orders_succeeded += buy_stats["succeeded"]
            total_trade_value += buy_stats["trade_value"]

        # Log HOLD items
        for item in hold_items:
            logger.info(f"⏸️ Holding {item.symbol} - no action required")

        # Clean up subscriptions after execution
        self._cleanup_subscriptions(all_symbols)

        # Record filled orders to trade ledger
        self._record_orders_to_ledger(orders, plan)

        # Classify execution status
        success, status = ExecutionResult.classify_execution_status(orders_placed, orders_succeeded)

        # Create execution result
        execution_result = ExecutionResult(
            success=success,
            status=status,
            plan_id=plan.plan_id,
            correlation_id=plan.correlation_id,
            orders=orders,
            orders_placed=orders_placed,
            orders_succeeded=orders_succeeded,
            total_trade_value=total_trade_value,
            execution_timestamp=datetime.now(UTC),
            metadata={},
        )

        # Enhanced logging with status classification
        if status == ExecutionStatus.SUCCESS:
            status_emoji = "✅"
        elif status == ExecutionStatus.PARTIAL_SUCCESS:
            status_emoji = "⚠️"
        else:
            status_emoji = "❌"
        logger.info(
            f"{status_emoji} Rebalance plan {plan.plan_id} completed: "
            f"{orders_succeeded}/{orders_placed} orders succeeded (status: {status.value})"
        )

        # Additional logging for partial success to aid in debugging
        if status == ExecutionStatus.PARTIAL_SUCCESS:
            failed_orders = [order for order in orders if not order.success]
            failed_symbols = [order.symbol for order in failed_orders]
            logger.warning(
                f"⚠️ Partial execution: {len(failed_orders)} orders failed for symbols: {failed_symbols}"
            )

        # Persist trade ledger to S3
        self.trade_ledger.persist_to_s3(correlation_id=plan.correlation_id)

        return execution_result

    def _extract_all_symbols(self, plan: RebalancePlan) -> list[str]:
        """Extract all symbols from the rebalance plan."""
        return self._position_utils.extract_all_symbols(plan)

    def _bulk_subscribe_symbols(self, symbols: list[str]) -> dict[str, bool]:
        """Bulk subscribe to all symbols for efficient real-time pricing."""
        return self._position_utils.bulk_subscribe_symbols(symbols)

    async def _execute_sell_phase(
        self, sell_items: list[RebalancePlanItem], correlation_id: str | None = None
    ) -> tuple[list[OrderResult], ExecutionStats]:
        """Execute sell orders phase with integrated re-pegging monitoring."""
        return await self._phase_executor.execute_sell_phase(
            sell_items,
            correlation_id,
            execute_order_callback=self._execute_single_item,
            monitor_orders_callback=self._monitor_and_repeg_phase_orders,
            finalize_orders_callback=self._finalize_phase_orders,
        )

    async def _execute_buy_phase_with_settlement_monitoring(
        self,
        buy_items: list[RebalancePlanItem],
        sell_order_ids: list[str],
        correlation_id: str,
        plan_id: str,
    ) -> tuple[list[OrderResult], ExecutionStats]:
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

        # Verify buying power is actually available before proceeding with BUY orders
        # This addresses the Alpaca account state synchronization lag
        (
            buying_power_available,
            actual_buying_power,
        ) = await settlement_monitor.verify_buying_power_available_after_settlement(
            settlement_result.total_buying_power_released,
            correlation_id,
            max_wait_seconds=30,
        )

        if not buying_power_available:
            logger.warning(
                f"⚠️ Proceeding with BUY phase despite buying power shortfall: "
                f"${actual_buying_power} available vs ${settlement_result.total_buying_power_released} expected"
            )
        else:
            logger.info("✅ Buying power verified, proceeding with BUY phase")

        # Now execute buy orders with released buying power
        return await self._execute_buy_phase(buy_items, correlation_id)

    async def _execute_buy_phase(
        self, buy_items: list[RebalancePlanItem], correlation_id: str | None = None
    ) -> tuple[list[OrderResult], ExecutionStats]:
        """Execute buy orders phase with integrated re-pegging monitoring."""
        return await self._phase_executor.execute_buy_phase(
            buy_items,
            correlation_id,
            execute_order_callback=self._execute_single_item,
            monitor_orders_callback=self._monitor_and_repeg_phase_orders,
            finalize_orders_callback=self._finalize_phase_orders,
        )

    async def _monitor_and_repeg_phase_orders(
        self,
        phase_type: str,
        orders: list[OrderResult],
        correlation_id: str | None = None,
    ) -> list[OrderResult]:
        """Monitor and re-peg orders from a specific execution phase."""
        return await self._order_monitor.monitor_and_repeg_phase_orders(
            phase_type, orders, correlation_id
        )

    def _cleanup_subscriptions(self, symbols: list[str]) -> None:
        """Clean up pricing subscriptions after execution."""
        self._position_utils.cleanup_subscriptions(symbols)

    async def _execute_single_item(self, item: RebalancePlanItem) -> OrderResult:
        """Execute a single rebalance plan item.

        Args:
            item: RebalancePlanItem to execute

        Returns:
            OrderResult with execution results

        """
        try:
            side = "buy" if item.action == "BUY" else "sell"

            # Determine quantity (shares) to trade
            if item.action == "SELL" and item.target_weight == Decimal("0.0"):
                # For liquidation (0% target), use actual position quantity
                raw_shares = self._position_utils.get_position_quantity(item.symbol)
                shares = self._position_utils.adjust_quantity_for_fractionability(
                    item.symbol, raw_shares
                )
                logger.info(
                    f"📊 Liquidating {item.symbol}: selling {shares} shares (full position)"
                )
            else:
                # Estimate shares from trade amount using best available price
                price = self._position_utils.get_price_for_estimation(item.symbol)
                if price is None or price <= Decimal("0"):
                    # Safety fallback to 1 share if price discovery fails
                    shares = Decimal("1")
                    logger.warning(f"⚠️ Price unavailable for {item.symbol}; defaulting to 1 share")
                else:
                    raw_shares = abs(item.trade_amount) / price
                    shares = self._position_utils.adjust_quantity_for_fractionability(
                        item.symbol, raw_shares
                    )

                amount_fmt = Decimal(str(abs(item.trade_amount))).quantize(Decimal("0.01"))
                logger.info(
                    f"📊 Executing {item.action} for {item.symbol}: "
                    f"${amount_fmt} (estimated {shares} shares)"
                )

            # Use smart execution with async context
            order_result = await self.execute_order(
                symbol=item.symbol,
                side=side,
                quantity=shares,
                correlation_id=f"rebalance-{item.symbol}",
            )

            if order_result.success:
                logger.info(
                    f"✅ {item.action} {item.symbol} order placed (ID: {order_result.order_id})"
                )
            else:
                logger.error(f"❌ Failed to place {item.action} for {item.symbol}")

            return order_result

        except Exception as e:
            logger.error(f"❌ Error executing {item.action} for {item.symbol}: {e}")

            return OrderResult(
                symbol=item.symbol,
                action=item.action,
                trade_amount=abs(item.trade_amount),
                shares=Decimal("0"),
                price=None,
                order_id=None,
                success=False,
                error_message=str(e),
                timestamp=datetime.now(UTC),
                order_type="MARKET",  # Default to MARKET for error cases
                filled_at=None,  # Not filled due to error
            )

    def _finalize_phase_orders(
        self,
        *,
        phase_type: str,
        orders: list[OrderResult],
        items: list[RebalancePlanItem],
    ) -> tuple[list[OrderResult], int, Decimal]:
        """Wait for placed orders to complete and rebuild results based on final status."""
        return self._order_finalizer.finalize_phase_orders(orders, items, phase_type)

    def _record_orders_to_ledger(self, orders: list[OrderResult], plan: RebalancePlan) -> None:
        """Record filled orders to trade ledger.

        Args:
            orders: List of order results to record
            plan: Rebalance plan with strategy attribution metadata

        """
        for order in orders:
            if order.success and order.order_id:
                # Attempt to fetch quote data for more complete trade records
                quote_at_fill = None
                if self.pricing_service:
                    try:
                        market_quote = self.pricing_service.get_quote_data(order.symbol)
                        if market_quote:
                            # Enhanced QuoteModel is already in the correct format
                            quote_at_fill = market_quote
                    except Exception as e:
                        logger.debug(f"Could not fetch quote for {order.symbol}: {e}")

                # Record order to ledger with quote data when available
                self.trade_ledger.record_filled_order(
                    order_result=order,
                    correlation_id=plan.correlation_id,
                    rebalance_plan=plan,
                    quote_at_fill=quote_at_fill,
                )

    def shutdown(self) -> None:
        """Shutdown the executor and cleanup resources."""
        if self.pricing_service:
            try:
                self.pricing_service.stop()
                logger.info("✅ Pricing service stopped")
            except Exception as e:
                logger.debug(f"Error stopping pricing service: {e}")
