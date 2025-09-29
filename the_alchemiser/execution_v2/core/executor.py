"""Business Unit: execution | Status: current.

Core executor for order placement and smart execution.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import ROUND_DOWN, Decimal
from typing import TYPE_CHECKING, TypedDict

from the_alchemiser.execution_v2.core.market_order_executor import MarketOrderExecutor
from the_alchemiser.execution_v2.core.order_finalizer import OrderFinalizer
from the_alchemiser.execution_v2.core.order_monitor import OrderMonitor
from the_alchemiser.execution_v2.core.position_utils import PositionUtils
from the_alchemiser.execution_v2.core.smart_execution_strategy import (
    SmartExecutionStrategy,
    SmartOrderRequest,
    SmartOrderResult,
)
from the_alchemiser.execution_v2.models.execution_result import (
    ExecutionResult,
    ExecutionStatus,
    OrderResult,
)
from the_alchemiser.execution_v2.utils.execution_validator import (
    ExecutionValidator,
    OrderValidationResult,
)
from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.schemas.execution_report import ExecutedOrder
from the_alchemiser.shared.schemas.rebalance_plan import (
    RebalancePlan,
    RebalancePlanItem,
)
from the_alchemiser.shared.services.buying_power_service import BuyingPowerService
from the_alchemiser.shared.services.real_time_pricing import RealTimePricingService
from the_alchemiser.shared.services.websocket_manager import WebSocketConnectionManager

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
        self._market_order_executor: MarketOrderExecutor | None = None
        self._order_monitor: OrderMonitor | None = None
        self._order_finalizer: OrderFinalizer | None = None
        self._position_utils: PositionUtils | None = None

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
        try:
            self._market_order_executor = MarketOrderExecutor(
                self.alpaca_manager, self.validator, self.buying_power_service
            )
            self._order_monitor = OrderMonitor(self.smart_strategy, self.execution_config)
            self._order_finalizer = OrderFinalizer(self.alpaca_manager, self.execution_config)
            self._position_utils = PositionUtils(
                self.alpaca_manager, self.pricing_service, self.enable_smart_execution
            )
            logger.debug("✅ Helper modules initialized")
        except Exception as e:
            logger.warning(f"⚠️ Error initializing helper modules: {e}")
            # Helper modules remain None to use fallback methods

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
                    logger.info(f"✅ Smart execution placed order for {symbol}")
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
        validation_result = self._validate_market_order(symbol, quantity, side)

        if not validation_result.is_valid:
            return self._build_validation_failure_result(symbol, side, quantity, validation_result)

        final_quantity = validation_result.adjusted_quantity or quantity

        self._log_validation_warnings(validation_result)

        try:
            if side.lower() == "buy":
                self._ensure_buying_power(symbol, final_quantity)

            broker_result = self._place_market_order_with_broker(symbol, side, final_quantity)
            return self._build_market_order_execution_result(
                symbol, side, final_quantity, broker_result
            )
        except Exception as exc:
            return self._handle_market_order_exception(symbol, side, final_quantity, exc)














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

        # Check for stale orders to free up buying power
        logger.debug("About to check for stale orders...")

        # Cancel any stale orders to free up buying power
        stale_timeout_minutes = 30  # Default timeout
        if self.execution_config:
            stale_timeout_minutes = self.execution_config.stale_order_timeout_minutes
            logger.debug(f"Using execution_config timeout: {stale_timeout_minutes}")
        else:
            logger.debug("No execution_config found, using default timeout")

        logger.info(f"🧹 Checking for stale orders (older than {stale_timeout_minutes} minutes)...")
        stale_result = self.alpaca_manager.cancel_stale_orders(stale_timeout_minutes)
        logger.debug(f"Stale order result: {stale_result}")

        if stale_result["cancelled_count"] > 0:
            logger.info(f"🗑️ Cancelled {stale_result['cancelled_count']} stale orders")
        if stale_result["errors"]:
            logger.warning(f"⚠️ Errors during stale order cancellation: {stale_result['errors']}")

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
            metadata={"stale_orders_cancelled": stale_result["cancelled_count"]},
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

        return execution_result

    def _extract_all_symbols(self, plan: RebalancePlan) -> list[str]:
        """Extract all symbols from the rebalance plan."""
        if self._position_utils:
            return self._position_utils.extract_all_symbols(plan)
        # Fallback implementation
        symbols = {item.symbol for item in plan.items if item.action in ["BUY", "SELL"]}
        return sorted(symbols)

    def _bulk_subscribe_symbols(self, symbols: list[str]) -> dict[str, bool]:
        """Bulk subscribe to all symbols for efficient real-time pricing."""
        if self._position_utils:
            return self._position_utils.bulk_subscribe_symbols(symbols)
        # Fallback: return empty dict if position utils not available
        return {}

    async def _execute_sell_phase(
        self, sell_items: list[RebalancePlanItem], correlation_id: str | None = None
    ) -> tuple[list[OrderResult], ExecutionStats]:
        """Execute sell orders phase with integrated re-pegging monitoring.

        Args:
            sell_items: List of sell order items
            correlation_id: Optional correlation ID for tracking

        Returns:
            Tuple of (order results, execution statistics)

        """
        orders = []
        placed = 0
        succeeded = 0

        # Execute all sell orders first (placement only)
        for item in sell_items:
            order_result = await self._execute_single_item(item)
            orders.append(order_result)
            placed += 1

            if order_result.order_id:
                logger.info(f"🧾 SELL {item.symbol} order placed (ID: {order_result.order_id})")
            elif not order_result.success:
                logger.error(
                    f"❌ SELL {item.symbol} placement failed: {order_result.error_message}"
                )

        # Monitor and re-peg sell orders that haven't filled and await completion
        if self.smart_strategy and self.enable_smart_execution:
            logger.info("🔄 Monitoring SELL orders for re-pegging opportunities...")
            orders = await self._monitor_and_repeg_phase_orders("SELL", orders, correlation_id)

        # Await completion and finalize statuses
        orders, succeeded, trade_value = self._finalize_phase_orders(
            phase_type="SELL", orders=orders, items=sell_items
        )

        return orders, {
            "placed": placed,
            "succeeded": succeeded,
            "trade_value": trade_value,
        }

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
        """Execute buy orders phase with integrated re-pegging monitoring.

        Args:
            buy_items: List of buy order items
            correlation_id: Optional correlation ID for tracking

        Returns:
            Tuple of (order results, execution statistics)

        """
        orders = []
        placed = 0
        succeeded = 0

        # Execute all buy orders first (placement only)
        for item in buy_items:
            # Pre-check for micro orders that will be rejected by broker constraints
            if self.execution_config is not None:
                try:
                    min_notional = getattr(
                        self.execution_config,
                        "min_fractional_notional_usd",
                        Decimal("1.00"),
                    )
                    asset_info = self.alpaca_manager.get_asset_info(item.symbol)
                    # Estimate shares and notional for skip logic
                    est_price = self._get_price_for_estimation(item.symbol) or Decimal("0")
                    est_shares = (
                        abs(item.trade_amount) / est_price if est_price > 0 else Decimal("0")
                    )
                    if asset_info and asset_info.fractionable:
                        est_notional = (est_shares * est_price).quantize(Decimal("0.01"))
                        if est_notional < min_notional:
                            logger.warning(
                                f"  ❌ Skipping BUY {item.symbol}: estimated notional ${est_notional} < ${min_notional} (fractional min)"
                            )
                            # Record as a skipped/no-op, not a failure
                            orders.append(
                                OrderResult(
                                    symbol=item.symbol,
                                    action="BUY",
                                    trade_amount=Decimal("0"),
                                    shares=Decimal("0"),
                                    price=None,
                                    order_id=None,
                                    success=True,
                                    error_message=None,
                                    timestamp=datetime.now(UTC),
                                )
                            )
                            # Do not count as placed
                            continue
                    else:
                        # Non-fractionable: if rounding would produce zero shares, skip
                        raw_shares = (
                            abs(item.trade_amount) / est_price if est_price > 0 else Decimal("0")
                        )
                        rounded = raw_shares.quantize(Decimal("1"), rounding=ROUND_DOWN)
                        if rounded <= 0:
                            logger.warning(
                                f"  ❌ Skipping BUY {item.symbol}: non-fractionable and rounded shares {rounded} <= 0"
                            )
                            orders.append(
                                OrderResult(
                                    symbol=item.symbol,
                                    action="BUY",
                                    trade_amount=Decimal("0"),
                                    shares=Decimal("0"),
                                    price=None,
                                    order_id=None,
                                    success=True,
                                    error_message=None,
                                    timestamp=datetime.now(UTC),
                                )
                            )
                            continue
                except Exception as _skip_err:
                    logger.debug(
                        f"Skip pre-check failed (continuing with normal flow): {_skip_err}"
                    )

            order_result = await self._execute_single_item(item)
            orders.append(order_result)
            placed += 1

            if order_result.order_id:
                logger.info(f"🧾 BUY {item.symbol} order placed (ID: {order_result.order_id})")
            elif not order_result.success:
                logger.error(f"❌ BUY {item.symbol} placement failed: {order_result.error_message}")

        # Monitor and re-peg buy orders that haven't filled and await completion
        if self.smart_strategy and self.enable_smart_execution:
            logger.info("🔄 Monitoring BUY orders for re-pegging opportunities...")
            orders = await self._monitor_and_repeg_phase_orders("BUY", orders, correlation_id)

        # Await completion and finalize statuses
        orders, succeeded, trade_value = self._finalize_phase_orders(
            phase_type="BUY", orders=orders, items=buy_items
        )

        return orders, {
            "placed": placed,
            "succeeded": succeeded,
            "trade_value": trade_value,
        }

    async def _monitor_and_repeg_phase_orders(
        self,
        phase_type: str,
        orders: list[OrderResult],
        correlation_id: str | None = None,
    ) -> list[OrderResult]:
        """Monitor and re-peg orders from a specific execution phase."""
        if self._order_monitor:
            return await self._order_monitor.monitor_and_repeg_phase_orders(
                phase_type, orders, correlation_id
            )
        # Fallback: return orders unchanged if monitor not available
        logger.info(f"📊 {phase_type} phase: Order monitor not available; skipping re-peg loop")
        return orders





    async def _execute_repeg_monitoring_loop(
        self,
        phase_type: str,
        orders: list[OrderResult],
        config: dict[str, int],
        start_time: float,
        correlation_id: str | None = None,
    ) -> list[OrderResult]:
        """Execute the main repeg monitoring loop.

        Args:
            phase_type: Type of phase ("SELL" or "BUY")
            orders: List of orders to monitor
            config: Configuration parameters
            start_time: Start time of monitoring
            correlation_id: Optional correlation ID for tracking

        Returns:
            Updated list of orders with any re-pegged order IDs swapped in.

        """
        import asyncio
        import time

        attempts = 0
        last_repeg_action_time = start_time

        while (time.time() - start_time) < config["max_total_wait"]:
            elapsed_total = time.time() - start_time

            # Give existing orders time to fill before checking
            await asyncio.sleep(config["wait_between_checks"])

            repeg_results = []
            if self.smart_strategy:
                repeg_results = await self.smart_strategy.check_and_repeg_orders()

            if repeg_results:
                last_repeg_action_time = time.time()
                orders = self._process_repeg_results(
                    phase_type, orders, repeg_results, elapsed_total
                )
            else:
                self._log_no_repeg_activity(phase_type, attempts, elapsed_total)

            attempts += 1

            # Check for early termination conditions
            if self._should_terminate_early(last_repeg_action_time, config["fill_wait_seconds"]):
                logger.info(
                    f"📊 {phase_type} phase: No active orders remaining, ending monitoring early "
                    f"(after {elapsed_total:.1f}s)"
                )
                break

        self._log_monitoring_completion(phase_type, start_time, attempts, correlation_id)
        # Ultimate fallback: if any active smart orders remain after monitoring window, escalate to market
        try:
            if self.smart_strategy and self.smart_strategy.get_active_order_count() > 0:
                logger.warning(
                    f"🚨 {phase_type} phase: Monitoring window ended with active orders; escalating remaining to market"
                )
                # Explicitly escalate remaining active orders to market and update order IDs
                active = self.smart_strategy.order_tracker.get_active_orders()
                if active:
                    import asyncio as _asyncio

                    tasks = [
                        self.smart_strategy.repeg_manager._escalate_to_market(oid, req)
                        for oid, req in active.items()
                    ]
                    results = [r for r in await _asyncio.gather(*tasks) if r]
                    if results:
                        # Process as if they were standard repeg results (will replace order IDs)
                        orders = self._process_repeg_results(
                            phase_type, orders, results, elapsed_total=0.0
                        )
        except Exception as _err:
            logger.debug(f"Skipped final escalation due to error: {_err}")
        return orders

    def _process_repeg_results(
        self,
        phase_type: str,
        orders: list[OrderResult],
        repeg_results: list[SmartOrderResult],
        elapsed_total: float,
    ) -> list[OrderResult]:
        """Process repeg results and update orders.

        Args:
            phase_type: Type of phase ("SELL" or "BUY")
            orders: Current list of orders
            repeg_results: Results from repeg operation
            elapsed_total: Total elapsed time

        Returns:
            Updated list of orders.

        """
        escalations = sum(
            1 for r in repeg_results if "escalation" in getattr(r, "execution_strategy", "")
        )
        repegs = sum(1 for r in repeg_results if "repeg" in getattr(r, "execution_strategy", ""))

        logger.info(
            f"📊 {phase_type} phase: {len(repeg_results)} orders processed "
            f"(repegs: {repegs}, escalations: {escalations}) at {elapsed_total:.1f}s"
        )

        # Log escalations prominently as warnings
        if escalations > 0:
            logger.warning(f"🚨 {phase_type} phase: {escalations} orders ESCALATED TO MARKET")

        replacement_map = self._build_replacement_map_from_repeg_results(phase_type, repeg_results)
        if replacement_map:
            orders = self._replace_order_ids(orders, replacement_map)
            logger.info(f"📊 {phase_type} phase: {len(replacement_map)} order IDs replaced")

        return orders

    def _log_no_repeg_activity(self, phase_type: str, attempts: int, elapsed_total: float) -> None:
        """Log when no repeg activity occurred."""
        active_orders = self.smart_strategy.get_active_order_count() if self.smart_strategy else 0
        logger.debug(
            f"📊 {phase_type} phase: No re-pegging needed "
            f"(attempt {attempts + 1}, {elapsed_total:.1f}s elapsed, {active_orders} active orders)"
        )

    def _should_terminate_early(
        self, last_repeg_action_time: float, fill_wait_seconds: int
    ) -> bool:
        """Check if monitoring should terminate early.

        Args:
            last_repeg_action_time: Time of last repeg action
            fill_wait_seconds: Fill wait time configuration

        Returns:
            True if monitoring should terminate early.

        """
        import time

        time_since_last_action = time.time() - last_repeg_action_time

        # If smart strategy is not available, use the old logic
        if self.smart_strategy is None:
            return time_since_last_action > fill_wait_seconds * 2

        active_order_count = self.smart_strategy.get_active_order_count()

        # If no active orders, use a short grace window instead of full 2x wait
        if active_order_count == 0:
            grace_window_seconds = 5  # Short grace period for zero active orders
            return time_since_last_action > grace_window_seconds

        # If there are active orders, use the original longer timeout
        return time_since_last_action > fill_wait_seconds * 2

    def _log_monitoring_completion(
        self,
        phase_type: str,
        start_time: float,
        attempts: int,
        correlation_id: str | None = None,
    ) -> None:
        """Log completion of monitoring phase.

        Args:
            phase_type: Type of phase ("SELL" or "BUY")
            start_time: Start time of monitoring
            attempts: Number of attempts made
            correlation_id: Optional correlation ID for tracking

        """
        import time

        final_elapsed = time.time() - start_time
        correlation_info = f" (correlation_id: {correlation_id})" if correlation_id else ""
        logger.info(
            f"📊 {phase_type} phase monitoring completed after {final_elapsed:.1f}s "
            f"({attempts} check attempts){correlation_info}"
        )

    def _cleanup_subscriptions(self, symbols: list[str]) -> None:
        """Clean up pricing subscriptions after execution."""
        if self._position_utils:
            self._position_utils.cleanup_subscriptions(symbols)
        # No fallback needed - cleanup is optional

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
                raw_shares = self._get_position_quantity(item.symbol)
                shares = self._adjust_quantity_for_fractionability(item.symbol, raw_shares)
                logger.info(
                    f"📊 Liquidating {item.symbol}: selling {shares} shares (full position)"
                )
            else:
                # Estimate shares from trade amount using best available price
                price = self._get_price_for_estimation(item.symbol)
                if price is None or price <= Decimal("0"):
                    # Safety fallback to 1 share if price discovery fails
                    shares = Decimal("1")
                    logger.warning(f"⚠️ Price unavailable for {item.symbol}; defaulting to 1 share")
                else:
                    raw_shares = abs(item.trade_amount) / price
                    shares = self._adjust_quantity_for_fractionability(item.symbol, raw_shares)

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
            )






    def _finalize_phase_orders(
        self,
        *,
        phase_type: str,
        orders: list[OrderResult],
        items: list[RebalancePlanItem],
    ) -> tuple[list[OrderResult], int, Decimal]:
        """Wait for placed orders to complete and rebuild results based on final status."""
        if self._order_finalizer:
            return self._order_finalizer.finalize_phase_orders(orders, items, phase_type)
        # Fallback: return orders as-is
        logger.warning(f"Order finalizer not available; returning {len(orders)} orders as-is")
        return orders, len([o for o in orders if o.success]), sum((o.trade_amount for o in orders), Decimal("0"))

    def _log_repeg_status(self, phase_type: str, repeg_result: SmartOrderResult) -> None:
        """Log repeg status with appropriate message for escalation or standard repeg."""
        strategy = getattr(repeg_result, "execution_strategy", "")
        order_id = getattr(repeg_result, "order_id", "")
        repegs_used = getattr(repeg_result, "repegs_used", 0)
        symbol = getattr(repeg_result, "symbol", "")

        if "escalation" in strategy:
            logger.warning(
                f"🚨 {phase_type} ESCALATED_TO_MARKET: {symbol} {order_id} (after {repegs_used} re-pegs)"
            )
        else:
            # Use configured max repegs if available for accurate logging
            max_repegs = (
                getattr(self.execution_config, "max_repegs_per_order", 3)
                if self.execution_config
                else 3
            )
            logger.debug(f"✅ {phase_type} REPEG {repegs_used}/{max_repegs}: {symbol} {order_id}")

    def _extract_order_ids(self, repeg_result: SmartOrderResult) -> tuple[str, str]:
        """Extract original and new order IDs from repeg result.

        Returns:
            Tuple of (original_id, new_id). Both will be empty strings if not found.

        """
        meta = getattr(repeg_result, "metadata", None) or {}
        original_id = str(meta.get("original_order_id")) if isinstance(meta, dict) else ""
        new_id = getattr(repeg_result, "order_id", None) or ""
        return original_id, new_id

    def _handle_failed_repeg(self, phase_type: str, repeg_result: SmartOrderResult) -> None:
        """Handle logging for failed repeg results."""
        error_message = getattr(repeg_result, "error_message", "")
        logger.warning(f"⚠️ {phase_type} re-peg failed: {error_message}")

    def _build_replacement_map_from_repeg_results(
        self, phase_type: str, repeg_results: list[SmartOrderResult]
    ) -> dict[str, str]:
        """Build mapping from original to new order IDs for successful re-pegs."""
        replacement_map: dict[str, str] = {}

        for repeg_result in repeg_results:
            try:
                if not getattr(repeg_result, "success", False):
                    self._handle_failed_repeg(phase_type, repeg_result)
                    continue

                self._log_repeg_status(phase_type, repeg_result)
                original_id, new_id = self._extract_order_ids(repeg_result)

                if original_id and new_id:
                    replacement_map[original_id] = new_id

            except Exception as exc:
                logger.debug(f"Failed to process re-peg result for replacement mapping: {exc}")

        return replacement_map

    def _replace_order_ids(
        self, orders: list[OrderResult], replacement_map: dict[str, str]
    ) -> list[OrderResult]:
        """Replace order IDs in the given order list according to replacement_map."""
        updated: list[OrderResult] = []
        for o in orders:
            if o.order_id and o.order_id in replacement_map:
                updated.append(o.model_copy(update={"order_id": replacement_map[o.order_id]}))
            else:
                updated.append(o)
        return updated















    def shutdown(self) -> None:
        """Shutdown the executor and cleanup resources."""
        if self.pricing_service:
            try:
                self.pricing_service.stop()
                logger.info("✅ Pricing service stopped")
            except Exception as e:
                logger.debug(f"Error stopping pricing service: {e}")
