"""Business Unit: execution | Status: current.

Core executor for order placement and smart execution.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import ROUND_DOWN, Decimal
from typing import TYPE_CHECKING, Any, TypedDict

from the_alchemiser.execution_v2.core.smart_execution_strategy import (
    SmartExecutionStrategy,
    SmartOrderRequest,
    SmartOrderResult,
)
from the_alchemiser.execution_v2.models.execution_result import (
    ExecutionResultDTO,
    OrderResultDTO,
)
from the_alchemiser.execution_v2.utils.execution_validator import (
    ExecutionValidator,
    OrderValidationResult,
)
from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.dto.execution_dto import ExecutionResult
from the_alchemiser.shared.dto.execution_report_dto import ExecutedOrderDTO
from the_alchemiser.shared.dto.rebalance_plan_dto import (
    RebalancePlanDTO,
    RebalancePlanItemDTO,
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

        # Initialize execution validator for preflight checks
        self.validator = ExecutionValidator(alpaca_manager)

        # Initialize buying power service for verification
        self.buying_power_service = BuyingPowerService(alpaca_manager)

        # Initialize pricing service for smart execution
        self.pricing_service: RealTimePricingService | None = None
        self.smart_strategy: SmartExecutionStrategy | None = None
        self.websocket_manager = None

        # Initialize smart execution if enabled
        if enable_smart_execution:
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

            except Exception as e:
                logger.error(f"❌ Error initializing smart execution: {e}", exc_info=True)
                self.enable_smart_execution = False
                self.pricing_service = None
                self.smart_strategy = None
                self.websocket_manager = None

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
                    # Success here means order was placed; fill will be checked later
                    logger.info(f"✅ Smart execution placed order for {symbol}")
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
                logger.warning(f"⚠️ Smart execution failed for {symbol}: {result.error_message}")

            except Exception as e:
                logger.error(f"❌ Smart execution failed for {symbol}: {e}")

        # Fallback to regular market order
        logger.info(f"📈 Using standard market order for {symbol}")
        return self._execute_market_order(symbol, side, Decimal(str(quantity)))

    def _execute_market_order(self, symbol: str, side: str, quantity: Decimal) -> ExecutionResult:
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

    def _validate_market_order(
        self,
        symbol: str,
        quantity: Decimal,
        side: str,
    ) -> OrderValidationResult:
        """Run preflight validation for the market order."""
        return self.validator.validate_order(
            symbol=symbol,
            quantity=quantity,
            side=side,
            auto_adjust=True,
        )

    def _build_validation_failure_result(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        validation_result: OrderValidationResult,
    ) -> ExecutionResult:
        """Construct execution result for validation failure."""
        error_msg = validation_result.error_message or f"Validation failed for {symbol}"
        logger.error(f"❌ Preflight validation failed for {symbol}: {error_msg}")
        return ExecutionResult(
            symbol=symbol,
            side=side,
            quantity=quantity,
            status="rejected",
            success=False,
            error=error_msg,
            execution_strategy="validation_failed",
        )

    def _log_validation_warnings(self, validation_result: OrderValidationResult) -> None:
        """Log any warnings produced during validation."""
        for warning in validation_result.warnings:
            logger.warning(f"⚠️ Order validation: {warning}")

    def _ensure_buying_power(self, symbol: str, quantity: Decimal) -> None:
        """Ensure sufficient buying power before placing a buy order."""
        (
            is_sufficient,
            current_bp,
            estimated_cost,
        ) = self.buying_power_service.check_sufficient_buying_power(
            symbol,
            quantity,
            buffer_pct=5.0,
        )

        if not is_sufficient and estimated_cost:
            logger.warning(
                f"⚠️ Insufficient buying power for {symbol}: "
                f"need ~${estimated_cost}, have ${current_bp}"
            )
            if self.buying_power_service.force_account_refresh():
                logger.info("💰 Account refreshed, proceeding with order attempt")
            else:
                logger.warning("⚠️ Account refresh failed, proceeding anyway")

    def _place_market_order_with_broker(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
    ) -> ExecutedOrderDTO:
        """Submit the market order via the broker."""
        return self.alpaca_manager.place_market_order(
            symbol=symbol,
            side=side.lower(),
            qty=float(quantity),
        )

    def _build_market_order_execution_result(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        broker_result: ExecutedOrderDTO,
    ) -> ExecutionResult:
        """Convert broker response into ExecutionResult."""
        status = broker_result.status.lower() if broker_result.status else "submitted"
        success = broker_result.status not in ["REJECTED", "CANCELED"]
        price = broker_result.price if broker_result.price is not None else None

        return ExecutionResult(
            order_id=broker_result.order_id,
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            status=status,
            success=success,
            execution_strategy="market_order",
        )

    def _handle_market_order_exception(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        exc: Exception,
    ) -> ExecutionResult:
        """Handle exceptions raised during market order submission."""
        error_str = str(exc)

        if "insufficient buying power" in error_str.lower():
            logger.error(f"💳 Insufficient buying power for {symbol}: {exc}")
            try:
                account = self.alpaca_manager.get_account_dict()
                if account:
                    buying_power = account.get("buying_power", "unknown")
                    logger.error(f"💳 Current account state - Buying power: ${buying_power}")
            except Exception as diagnostic_error:
                logger.debug(f"Diagnostic account retrieval failed: {diagnostic_error}")

            return ExecutionResult(
                symbol=symbol,
                side=side,
                quantity=quantity,
                status="insufficient_buying_power",
                success=False,
                error=f"Insufficient buying power: {exc}",
                execution_strategy="buying_power_error",
            )

        logger.error(f"❌ Market order failed for {symbol}: {exc}")
        return ExecutionResult(
            symbol=symbol,
            side=side,
            quantity=quantity,
            status="failed",
            success=False,
            error=error_str,
            execution_strategy="market_order_failed",
        )

    async def execute_rebalance_plan(self, plan: RebalancePlanDTO) -> ExecutionResultDTO:
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

        # DEBUG: Add explicit debug logging
        logger.info("🔧 DEBUG: About to check for stale orders...")

        # Cancel any stale orders to free up buying power
        stale_timeout_minutes = 30  # Default timeout
        if self.execution_config:
            stale_timeout_minutes = self.execution_config.stale_order_timeout_minutes
            logger.info(f"🔧 DEBUG: Using execution_config timeout: {stale_timeout_minutes}")
        else:
            logger.info("🔧 DEBUG: No execution_config found, using default timeout")

        logger.info(f"🧹 Checking for stale orders (older than {stale_timeout_minutes} minutes)...")
        stale_result = self.alpaca_manager.cancel_stale_orders(stale_timeout_minutes)
        logger.info(f"🔧 DEBUG: Stale order result: {stale_result}")

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

        orders: list[OrderResultDTO] = []
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
            metadata={"stale_orders_cancelled": stale_result["cancelled_count"]},
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

        logger.info(f"📡 Bulk subscribing to {len(symbols)} symbols for real-time pricing")

        # Use the enhanced bulk subscription method
        subscription_results = self.pricing_service.bulk_subscribe_symbols(
            symbols,
            priority=5.0,  # High priority for execution
        )

        successful_subscriptions = sum(1 for success in subscription_results.values() if success)
        logger.info(
            f"✅ Bulk subscription complete: {successful_subscriptions}/{len(symbols)} "
            "symbols subscribed"
        )

        return subscription_results

    async def _execute_sell_phase(
        self, sell_items: list[RebalancePlanItemDTO], correlation_id: str | None = None
    ) -> tuple[list[OrderResultDTO], ExecutionStats]:
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
        self, buy_items: list[RebalancePlanItemDTO], correlation_id: str | None = None
    ) -> tuple[list[OrderResultDTO], ExecutionStats]:
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
        self, phase_type: str, orders: list[OrderResultDTO], correlation_id: str | None = None
    ) -> list[OrderResultDTO]:
        """Monitor and re-peg orders from a specific execution phase.

        Args:
            phase_type: Type of phase ("SELL" or "BUY")
            orders: List of orders from this phase to monitor
            correlation_id: Optional correlation ID for tracking

        Returns:
            Updated list of orders with any re-pegged order IDs swapped in.

        """
        import time

        if not self.smart_strategy:
            logger.info(f"📊 {phase_type} phase: Smart strategy disabled; skipping re-peg loop")
            return orders

        config = self._get_repeg_monitoring_config()
        self._log_monitoring_config(phase_type, config)

        return await self._execute_repeg_monitoring_loop(
            phase_type, orders, config, time.time(), correlation_id
        )

    def _get_repeg_monitoring_config(self) -> dict[str, int]:
        """Get configuration parameters for repeg monitoring.

        Returns:
            Dictionary containing monitoring configuration parameters.

        """
        config = {
            "max_repegs": 5,
            "fill_wait_seconds": 15,
            "wait_between_checks": 1,
            "max_total_wait": 60,
        }

        try:
            if self.execution_config is not None:
                config["max_repegs"] = getattr(self.execution_config, "max_repegs_per_order", 5)
                config["fill_wait_seconds"] = int(
                    getattr(self.execution_config, "fill_wait_seconds", 15)
                )
                config["wait_between_checks"] = max(
                    1, min(config["fill_wait_seconds"] // 5, 5)
                )  # Check 5x per fill_wait period
                placement_timeout = int(
                    getattr(self.execution_config, "order_placement_timeout_seconds", 30)
                )
                # Fix: Use fill_wait_seconds for total time calculation, not wait_between_checks
                config["max_total_wait"] = int(
                    placement_timeout
                    + config["fill_wait_seconds"] * (config["max_repegs"] + 1)
                    + 30  # +30s safety margin
                )
                config["max_total_wait"] = max(
                    60, min(config["max_total_wait"], 600)
                )  # Increased max to 10 minutes
        except Exception as exc:
            logger.debug(f"Error deriving re-peg loop bounds: {exc}")

        return config

    def _log_monitoring_config(self, phase_type: str, config: dict[str, int]) -> None:
        """Log the monitoring configuration parameters."""
        logger.info(
            f"📊 {phase_type} re-peg monitoring: max_repegs={config['max_repegs']}, "
            f"fill_wait_seconds={config['fill_wait_seconds']}, max_total_wait={config['max_total_wait']}s"
        )

    async def _execute_repeg_monitoring_loop(
        self,
        phase_type: str,
        orders: list[OrderResultDTO],
        config: dict[str, int],
        start_time: float,
        correlation_id: str | None = None,
    ) -> list[OrderResultDTO]:
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
        return orders

    def _process_repeg_results(
        self,
        phase_type: str,
        orders: list[OrderResultDTO],
        repeg_results: list[SmartOrderResult],
        elapsed_total: float,
    ) -> list[OrderResultDTO]:
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

        # Log escalations prominently
        if escalations > 0:
            logger.info(f"🚨 {phase_type} phase: {escalations} orders ESCALATED TO MARKET")

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
        self, phase_type: str, start_time: float, attempts: int, correlation_id: str | None = None
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
                price=(Decimal(str(execution_result.price)) if execution_result.price else None),
                order_id=execution_result.order_id,
                success=execution_result.success,
                error_message=getattr(execution_result, "error", None),
                timestamp=datetime.now(UTC),
            )

            if execution_result.success:
                logger.info(
                    f"✅ {item.action} {item.symbol} order placed (ID: {execution_result.order_id})"
                )
            else:
                logger.error(f"❌ Failed to place {item.action} for {item.symbol}")

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
                        price_rt = self.pricing_service.get_optimized_price_for_order(symbol)
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

    def _adjust_quantity_for_fractionability(self, symbol: str, raw_quantity: Decimal) -> Decimal:
        """Adjust quantity for asset fractionability constraints.

        Args:
            symbol: Asset symbol
            raw_quantity: Raw calculated quantity

        Returns:
            Adjusted quantity (whole shares for non-fractionable assets)

        """
        # Defensive guard
        if raw_quantity <= 0:
            return Decimal("0")

        # Fetch asset info to decide quantization strategy
        asset_info = self.alpaca_manager.get_asset_info(symbol)

        # Unknown asset: default to fractional quantization
        if asset_info is None:
            logger.debug(f"Could not determine fractionability for {symbol}, using fractional")
            return raw_quantity.quantize(Decimal("0.000001"))

        # Fractionable: preserve fractional shares with 6dp quantization
        if asset_info.fractionable:
            return raw_quantity.quantize(Decimal("0.000001"))

        # Non-fractionable: delegate rounding to validator for consistency
        validation = self.validator.validate_order(
            symbol=symbol,
            quantity=raw_quantity,
            side="buy",
            auto_adjust=True,
        )

        if not validation.is_valid and validation.error_code == "ZERO_QUANTITY_AFTER_ROUNDING":
            return Decimal("0")

        adjusted = (
            validation.adjusted_quantity
            if validation.adjusted_quantity is not None
            else raw_quantity.quantize(Decimal("1"), rounding=ROUND_DOWN)
        )

        if adjusted != raw_quantity:
            logger.info(
                f"🔄 Portfolio sizing: {symbol} non-fractionable, adjusted {raw_quantity:.6f} → {adjusted} shares"
            )

        return max(adjusted, Decimal("0"))

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
            qty = getattr(position, "qty_available", None) or getattr(position, "qty", 0)
            return Decimal(str(qty))
        except Exception as e:
            logger.warning(f"Error getting position for {symbol}: {e}")
            return Decimal("0")

    def _finalize_phase_orders(
        self,
        *,
        phase_type: str,
        orders: list[OrderResultDTO],
        items: list[RebalancePlanItemDTO],
    ) -> tuple[list[OrderResultDTO], int, Decimal]:
        """Wait for placed orders to complete and rebuild results based on final status.

        Args:
            phase_type: "SELL" or "BUY" for logging context
            orders: Initial order DTOs created at placement time
            items: Corresponding plan items in the same order as orders

        Returns:
            Tuple of (updated_orders, succeeded_count, trade_value)

        Notes:
            - Success is defined strictly as FILLED
            - PARTIALLY_FILLED is treated as not succeeded; we annotate error_message

        """
        try:
            order_ids = [o.order_id for o in orders if o.order_id]
            if not order_ids:
                return orders, 0, Decimal("0")

            max_wait = self._derive_max_wait_seconds()
            final_status_map = self._get_final_status_map(order_ids, max_wait, phase_type)
            updated_orders, succeeded, trade_value = self._rebuild_orders_with_final_status(
                orders, items, final_status_map
            )
            logger.info(f"📊 {phase_type} phase completion: {succeeded}/{len(orders)} FILLED")
            return updated_orders, succeeded, trade_value
        except Exception as e:
            logger.error(f"Error finalizing {phase_type} phase orders: {e}")
            return orders, 0, Decimal("0")

    def _log_repeg_status(self, phase_type: str, repeg_result: Any) -> None:  # noqa: ANN401
        """Log repeg status with appropriate message for escalation or standard repeg."""
        strategy = getattr(repeg_result, "execution_strategy", "")
        order_id = getattr(repeg_result, "order_id", "")
        repegs_used = getattr(repeg_result, "repegs_used", 0)

        if "escalation" in strategy:
            logger.info(
                f"🚨 {phase_type} ESCALATED_TO_MARKET: {order_id} (after {repegs_used} re-pegs)"
            )
        else:
            logger.info(f"✅ {phase_type} REPEG {repegs_used}/5: {order_id}")

    def _extract_order_ids(self, repeg_result: Any) -> tuple[str, str]:  # noqa: ANN401
        """Extract original and new order IDs from repeg result.

        Returns:
            Tuple of (original_id, new_id). Both will be empty strings if not found.

        """
        meta = getattr(repeg_result, "metadata", None) or {}
        original_id = str(meta.get("original_order_id")) if isinstance(meta, dict) else ""
        new_id = getattr(repeg_result, "order_id", None) or ""
        return original_id, new_id

    def _handle_failed_repeg(self, phase_type: str, repeg_result: Any) -> None:  # noqa: ANN401
        """Handle logging for failed repeg results."""
        error_message = getattr(repeg_result, "error_message", "")
        logger.warning(f"⚠️ {phase_type} re-peg failed: {error_message}")

    def _build_replacement_map_from_repeg_results(
        self, phase_type: str, repeg_results: list[Any]
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
        self, orders: list[OrderResultDTO], replacement_map: dict[str, str]
    ) -> list[OrderResultDTO]:
        """Replace order IDs in the given order list according to replacement_map."""
        updated: list[OrderResultDTO] = []
        for o in orders:
            if o.order_id and o.order_id in replacement_map:
                updated.append(o.model_copy(update={"order_id": replacement_map[o.order_id]}))
            else:
                updated.append(o)
        return updated

    def _derive_max_wait_seconds(self) -> int:
        """Compute a conservative max wait time for order fills from config."""
        try:
            if self.execution_config is not None:
                fill_wait_seconds = getattr(self.execution_config, "fill_wait_seconds", 15)
                max_repegs = getattr(self.execution_config, "max_repegs_per_order", 5)
                placement_timeout = getattr(
                    self.execution_config, "order_placement_timeout_seconds", 30
                )
                # Fix: Use fill_wait_seconds for calculation, not wait_base
                max_wait = int(placement_timeout + fill_wait_seconds * (max_repegs + 1) + 30)
                return max(60, min(max_wait, 600))  # Increased max to 10 minutes
        except Exception as exc:
            logger.debug(f"Using default max wait due to config error: {exc}")
        return 120  # Increased default from 60s

    def _get_final_status_map(
        self,
        order_ids: list[str],
        max_wait: int,
        phase_type: str,
    ) -> dict[str, tuple[str, Decimal | None]]:
        """Poll broker and return final status map for each order ID."""
        valid_order_ids, invalid_order_ids = self._validate_order_ids(order_ids, phase_type)

        if valid_order_ids:
            self._poll_order_completion(valid_order_ids, max_wait, phase_type)

        return self._build_final_status_map(valid_order_ids, invalid_order_ids)

    def _validate_order_ids(
        self, order_ids: list[str], phase_type: str
    ) -> tuple[list[str], list[str]]:
        """Validate order IDs and separate valid from invalid ones.

        Args:
            order_ids: List of order IDs to validate
            phase_type: Phase type for logging

        Returns:
            Tuple of (valid_order_ids, invalid_order_ids)

        """

        def _is_valid_uuid(val: str) -> bool:
            try:
                import uuid

                uuid.UUID(str(val))
                return True
            except Exception:
                return False

        valid_order_ids = [oid for oid in order_ids if oid and _is_valid_uuid(oid)]
        invalid_order_ids = [oid for oid in order_ids if not (oid and _is_valid_uuid(oid))]

        if invalid_order_ids:
            logger.warning(
                f"{phase_type} phase: {len(invalid_order_ids)} invalid order IDs will be marked rejected"
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
        orders: list[OrderResultDTO],
        items: list[RebalancePlanItemDTO],
        final_status_map: dict[str, tuple[str, Decimal | None]],
    ) -> tuple[list[OrderResultDTO], int, Decimal]:
        """Rebuild OrderResultDTOs with final semantics, compute success and trade value."""
        updated_orders: list[OrderResultDTO] = []
        succeeded = 0
        trade_value = Decimal("0")

        for idx, o in enumerate(orders):
            if not o.order_id:
                updated_orders.append(o)
                continue

            status, avg_price = final_status_map.get(o.order_id, ("rejected", None))
            is_filled = status == "filled"
            error_msg = None if is_filled else f"final status: {status}"
            final_price = avg_price if avg_price is not None else o.price

            new_o = o.model_copy(
                update={
                    "success": is_filled,
                    "price": final_price,
                    "error_message": error_msg,
                }
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

    def shutdown(self) -> None:
        """Shutdown the executor and cleanup resources."""
        if self.pricing_service:
            try:
                self.pricing_service.stop()
                logger.info("✅ Pricing service stopped")
            except Exception as e:
                logger.debug(f"Error stopping pricing service: {e}")
