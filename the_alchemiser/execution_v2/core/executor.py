"""Business Unit: execution | Status: current.

Core executor for order placement and smart execution.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Literal, TypedDict, cast

import structlog

from the_alchemiser.execution_v2.core.market_order_executor import MarketOrderExecutor
from the_alchemiser.execution_v2.core.order_finalizer import OrderFinalizer
from the_alchemiser.execution_v2.core.order_monitor import OrderMonitor
from the_alchemiser.execution_v2.core.phase_executor import PhaseExecutor
from the_alchemiser.execution_v2.core.settlement_monitor import SettlementMonitor
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
from the_alchemiser.shared.errors import (
    OrderExecutionError,
    SymbolValidationError,
    TradingClientError,
    ValidationError,
)
from the_alchemiser.shared.logging import get_logger, log_order_flow
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

logger: structlog.stdlib.BoundLogger = get_logger(__name__)


class ExecutionStats(TypedDict):
    """Statistics for execution phase results."""

    placed: int
    succeeded: int
    trade_value: Decimal


class Executor:
    """Core executor for order placement and smart execution.

    This class provides the core execution engine for placing orders with:
    - Smart execution using real-time pricing and limit orders
    - Graceful fallback to market orders if smart execution fails
    - Settlement-aware sell-first, buy-second workflow
    - Comprehensive order monitoring and re-pegging
    - Trade ledger recording with S3 persistence

    Attributes:
        alpaca_manager: Alpaca broker manager for API access
        execution_config: Optional smart execution configuration
        validator: Execution validator for preflight checks
        buying_power_service: Service for buying power verification
        pricing_service: Real-time pricing service (via WebSocket)
        smart_strategy: Smart execution strategy (if enabled)
        websocket_manager: WebSocket connection manager
        enable_smart_execution: Flag indicating smart execution availability
        trade_ledger: Trade ledger service for audit trail

    Smart Execution:
        When enabled, orders use real-time pricing and limit orders with:
        - Best bid/ask price discovery
        - Automatic order re-pegging if not filled
        - Configurable urgency levels
        - Fallback to market orders if smart execution fails

    Settlement Monitoring:
        For rebalance plans with sells followed by buys:
        - Monitors sell order settlement
        - Tracks buying power release
        - Verifies sufficient funds before executing buys

    Failure Modes:
        - Smart execution initialization failure: Falls back to market orders
        - Order placement failure: Returns OrderResult with success=False
        - Settlement timeout: Proceeds with buy phase after warning
        - Resource cleanup failure: Logged but not raised (in __del__)

    """

    def __init__(
        self,
        alpaca_manager: AlpacaManager,
        execution_config: ExecutionConfig | None = None,
    ) -> None:
        """Initialize the executor.

        Args:
            alpaca_manager: Alpaca broker manager
            execution_config: Execution configuration

        Raises:
            ValidationError: If alpaca_manager is None

        """
        if alpaca_manager is None:
            raise ValidationError("alpaca_manager cannot be None", field_name="alpaca_manager")

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
        # These are assigned in _initialize_helper_modules() before first use

        # Initialize trade ledger service
        self.trade_ledger = TradeLedgerService()

        # Initialize idempotency cache for duplicate execution protection
        self._execution_cache: dict[str, ExecutionResult] = {}

        # Initialize smart execution if enabled
        try:
            logger.info(
                "🚀 Initializing smart execution with shared WebSocket connection",
                extra={
                    "api_key_present": bool(alpaca_manager.api_key),
                    "paper_trading": alpaca_manager.is_paper_trading,
                },
            )

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

        except OSError as e:
            # Network-related errors that shouldn't stop execution
            # OSError covers ConnectionError and TimeoutError
            logger.warning(
                "Smart execution initialization failed (non-critical network error)",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            self.enable_smart_execution = False
            self.pricing_service = None
            self.smart_strategy = None
            self.websocket_manager = None
            # Initialize fallback modules
            self._initialize_helper_modules()
        except ValueError as e:
            # Configuration errors
            logger.error(
                "Smart execution initialization failed due to configuration error",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            self.enable_smart_execution = False
            self.pricing_service = None
            self.smart_strategy = None
            self.websocket_manager = None
            # Initialize fallback modules
            self._initialize_helper_modules()
        except Exception as e:
            # Unexpected errors - log with full stack trace
            logger.error(
                "Unexpected error in smart execution initialization",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
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
        """Clean up WebSocket connection when executor is destroyed.

        Note: Best-effort cleanup. Errors are logged but not raised since
        finalizers cannot propagate exceptions.
        """
        if hasattr(self, "websocket_manager") and self.websocket_manager is not None:
            try:
                self.websocket_manager.release_pricing_service()
            except OSError as e:
                # Expected cleanup errors - log at debug level
                # OSError covers ConnectionError and TimeoutError
                logger.debug(
                    "WebSocket manager cleanup encountered network error (expected)",
                    extra={"error": str(e), "error_type": type(e).__name__},
                )
            except Exception as e:
                # Unexpected errors - log at warning level
                logger.warning(
                    "Unexpected error releasing WebSocket manager during cleanup",
                    extra={"error": str(e), "error_type": type(e).__name__},
                )

    async def _try_smart_execution(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        correlation_id: str | None,
        *,
        is_complete_exit: bool = False,
    ) -> OrderResult | None:
        """Attempt smart execution for an order.

        Args:
            symbol: Stock symbol
            side: "buy" or "sell"
            quantity: Number of shares
            correlation_id: Correlation ID for tracking
            is_complete_exit: If True and side is 'sell', use actual available quantity

        Returns:
            OrderResult if successful, None if smart execution should be skipped.

        """
        # Early return if smart_strategy is not available
        if self.smart_strategy is None:
            return None

        try:
            logger.info(
                "🎯 Attempting smart execution for symbol",
                extra={
                    "symbol": symbol,
                    "side": side,
                    "quantity": str(quantity),
                    "correlation_id": correlation_id,
                },
            )

            # Normalize side to uppercase and cast to Literal type
            normalized_side = side.upper()
            if normalized_side not in ("BUY", "SELL"):
                raise ValidationError(
                    f"Invalid side: {side}. Must be 'buy' or 'sell'",
                    field_name="side",
                    value=side,
                )

            request = SmartOrderRequest(
                symbol=symbol,
                side=cast(Literal["BUY", "SELL"], normalized_side),
                quantity=Decimal(str(quantity)),
                correlation_id=correlation_id or "",
                urgency="NORMAL",
                is_complete_exit=is_complete_exit,
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
                side_upper = side.upper()
                if side_upper not in ("BUY", "SELL"):
                    side_upper = "BUY"  # Fallback to BUY if invalid
                return OrderResult(
                    symbol=symbol,
                    action=side_upper,  # type: ignore[arg-type]
                    trade_amount=abs(Decimal(str(quantity)) * (result.final_price or Decimal("0"))),
                    shares=Decimal(str(quantity)),
                    price=(result.final_price if result.final_price else None),
                    order_id=result.order_id,
                    success=True,
                    error_message=None,
                    timestamp=datetime.now(UTC),
                    order_type="LIMIT",  # Smart execution uses LIMIT orders
                    filled_at=result.placement_timestamp,  # Use placement timestamp from smart result
                )
            logger.warning(
                "⚠️ Smart execution failed for symbol",
                extra={
                    "symbol": symbol,
                    "error": result.error_message,
                },
            )
            return None

        except (ValidationError, SymbolValidationError) as e:
            # Validation errors during smart execution
            logger.error(
                "❌ Smart execution failed due to validation error",
                extra={
                    "symbol": symbol,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            return None
        except (TradingClientError, OrderExecutionError) as e:
            # Trading client or execution errors
            logger.error(
                "❌ Smart execution failed due to trading error",
                extra={
                    "symbol": symbol,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            return None
        except Exception as e:
            # Unexpected errors during smart execution
            logger.error(
                "❌ Smart execution failed due to unexpected error",
                exc_info=True,
                extra={
                    "symbol": symbol,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            return None

    async def execute_order(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        correlation_id: str | None = None,
        *,
        is_complete_exit: bool = False,
    ) -> OrderResult:
        """Execute an order with smart execution if enabled.

        Args:
            symbol: Stock symbol
            side: "buy" or "sell"
            quantity: Number of shares
            correlation_id: Correlation ID for tracking
            is_complete_exit: If True and side is 'sell', use actual available quantity in fallback

        Returns:
            OrderResult with order details. Falls back to market order if smart execution fails.

        """
        # Try smart execution first if enabled
        if self.enable_smart_execution and self.smart_strategy:
            smart_result = await self._try_smart_execution(
                symbol, side, quantity, correlation_id, is_complete_exit=is_complete_exit
            )
            if smart_result is not None:
                return smart_result

        # Fallback to regular market order (with is_complete_exit flag)
        logger.info("📈 Using standard market order for symbol", extra={"symbol": symbol})
        return self._execute_market_order(
            symbol, side, Decimal(str(quantity)), is_complete_exit=is_complete_exit
        )

    def _execute_market_order(
        self,
        symbol: str,
        side: str,
        quantity: Decimal,
        *,
        is_complete_exit: bool = False,
    ) -> OrderResult:
        """
        Execute a standard market order with preflight validation, with fallback logic for complete exits.

        This method first attempts to place a market order with `is_complete_exit=True` if `is_complete_exit` is True and the side is 'sell'.
        If this attempt raises an exception (e.g., due to broker error or unsupported operation), the method logs the error and falls back
        to the standard market order executor without the `is_complete_exit` flag.

        Args:
            symbol: Stock symbol
            side: "buy" or "sell"
            quantity: Number of shares
            is_complete_exit: If True and side is 'sell', attempt to use actual available quantity via `is_complete_exit=True`.

        Returns:
            OrderResult with order details. If the initial attempt with `is_complete_exit=True` fails, returns the result of the fallback standard market order.

        """
        # If is_complete_exit, use place_market_order directly with the flag
        if is_complete_exit and side.lower() == "sell":
            try:
                executed_order = self.alpaca_manager.place_market_order(
                    symbol=symbol,
                    side=side,
                    qty=quantity,
                    is_complete_exit=True,
                )

                side_upper = "SELL"

                return OrderResult(
                    symbol=symbol,
                    action=side_upper,  # type: ignore[arg-type]
                    trade_amount=abs(quantity * (executed_order.price or Decimal("0"))),
                    shares=quantity,
                    price=executed_order.price,
                    order_id=executed_order.order_id,
                    success=executed_order.status not in ["REJECTED", "CANCELED"],
                    error_message=executed_order.error_message
                    if executed_order.status in ["REJECTED", "CANCELED"]
                    else None,
                    timestamp=datetime.now(UTC),
                    order_type="MARKET",
                    filled_at=executed_order.execution_timestamp,
                )
            except Exception as e:
                logger.error(
                    "Market order with is_complete_exit failed",
                    extra={"symbol": symbol, "error": str(e)},
                )
                # Fall through to standard market order executor

        return self._market_order_executor.execute_market_order(symbol, side, quantity)

    async def execute_rebalance_plan(self, plan: RebalancePlan) -> ExecutionResult:
        """Execute a rebalance plan with settlement-aware sell-first, buy-second workflow.

        This method is idempotent - repeated calls with the same plan_id will return
        the cached result without re-executing orders.

        Enhanced execution flow:
        1. Extract and bulk-subscribe to all symbols upfront
        2. Execute SELL orders in parallel where possible
        3. Monitor settlement and buying power release
        4. Execute BUY orders once sufficient buying power is available

        Args:
            plan: RebalancePlan containing the rebalance plan

        Returns:
            ExecutionResult with execution results

        Raises:
            ValidationError: If plan is None
            asyncio.TimeoutError: If execution exceeds timeout (default 900 seconds)

        """
        if plan is None:
            raise ValidationError("plan cannot be None", field_name="plan")

        # Idempotency check
        if plan.plan_id in self._execution_cache:
            logger.info(
                "⏭️ Skipping duplicate execution of plan (idempotent)",
                extra={
                    "plan_id": plan.plan_id,
                    "correlation_id": plan.correlation_id,
                    "cached": True,
                },
            )
            return self._execution_cache[plan.plan_id]

        logger.info(
            "🚀 Executing rebalance plan with items (enhanced settlement-aware)",
            extra={
                "plan_id": plan.plan_id,
                "num_items": len(plan.items),
                "correlation_id": plan.correlation_id,
            },
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

        # Trade ledger automatically persists to DynamoDB (no explicit call needed)

        # Cache result for idempotency
        self._execution_cache[plan.plan_id] = execution_result

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
        settlement_monitor = SettlementMonitor(
            alpaca_manager=self.alpaca_manager,
            event_bus=None,  # Could integrate with event bus later
            polling_interval_seconds=0.5,
            max_wait_seconds=60,
        )

        # Monitor sell order settlements
        logger.info(
            "👀 Monitoring settlement of sell orders",
            extra={
                "num_orders": len(sell_order_ids),
                "correlation_id": correlation_id,
            },
        )
        settlement_result = await settlement_monitor.monitor_sell_orders_settlement(
            sell_order_ids, correlation_id, plan_id
        )

        logger.info(
            "💰 Settlement complete with buying power released",
            extra={
                "buying_power_released": str(settlement_result.total_buying_power_released),
                "correlation_id": correlation_id,
            },
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
            shortfall = settlement_result.total_buying_power_released - actual_buying_power
            shortfall_pct = (
                (shortfall / settlement_result.total_buying_power_released * 100)
                if settlement_result.total_buying_power_released > 0
                else 0
            )

            logger.error(
                "❌ Buying power shortfall detected after sell settlement",
                extra={
                    "expected": str(settlement_result.total_buying_power_released),
                    "actual": str(actual_buying_power),
                    "shortfall": str(shortfall),
                    "shortfall_pct": f"{shortfall_pct:.1f}%",
                    "correlation_id": correlation_id,
                },
            )

            # Calculate total BUY order cost to determine if we can execute any
            total_buy_cost = sum(abs(item.trade_amount) for item in buy_items)

            logger.warning(
                f"⚠️ Total BUY orders cost ${total_buy_cost:.2f}, available ${actual_buying_power:.2f}",
                extra={
                    "total_buy_cost": str(total_buy_cost),
                    "available_buying_power": str(actual_buying_power),
                    "can_execute_all": actual_buying_power >= total_buy_cost,
                    "correlation_id": correlation_id,
                },
            )

            if actual_buying_power < total_buy_cost:
                # CRITICAL: Insufficient buying power - this means SELL orders didn't complete as expected
                logger.critical(
                    "🚨 INSUFFICIENT BUYING POWER: Cannot execute all BUY orders. "
                    "This indicates SELL phase failures. Proceeding with available capital only.",
                    extra={
                        "total_cost": str(total_buy_cost),
                        "available": str(actual_buying_power),
                        "deficit": str(total_buy_cost - actual_buying_power),
                        "correlation_id": correlation_id,
                    },
                )
                # Continue anyway - individual orders will fail with proper error messages
                # This is better than skipping all orders
        else:
            logger.info("✅ Buying power verified, proceeding with BUY phase")

        # Now execute buy orders with released buying power
        # Individual orders will fail if insufficient buying power remains
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

    def _calculate_shares_for_item(self, item: RebalancePlanItem) -> Decimal:
        """Calculate shares to trade for a rebalance plan item.

        Args:
            item: RebalancePlanItem to calculate shares for

        Returns:
            Number of shares to trade (adjusted for fractionability)

        """
        MIN_PRICE_THRESHOLD = Decimal("0.001")  # $0.001 minimum price threshold

        # For liquidation (0% target), use actual position quantity
        action = item.action.upper()
        if action == "SELL" and item.target_weight == Decimal("0.0"):
            raw_shares = self._position_utils.get_position_quantity(item.symbol)
            shares = self._position_utils.adjust_quantity_for_fractionability(
                item.symbol, raw_shares
            )
            logger.info(
                "📊 Liquidating symbol: selling shares (full position)",
                extra={
                    "symbol": item.symbol,
                    "shares": str(shares),
                    "action": item.action,
                },
            )
            return shares

        # Estimate shares from trade amount using best available price
        price = self._position_utils.get_price_for_estimation(item.symbol)
        if price is None or price <= MIN_PRICE_THRESHOLD:
            # Safety fallback to 1 share if price discovery fails
            logger.warning(
                "⚠️ Price below minimum threshold for symbol; defaulting to 1 share",
                extra={
                    "symbol": item.symbol,
                    "price": str(price) if price else None,
                    "min_threshold": str(MIN_PRICE_THRESHOLD),
                    "default_shares": "1",
                },
            )
            return Decimal("1")

        # Normal case: calculate shares from trade amount
        raw_shares = abs(item.trade_amount) / price
        shares = self._position_utils.adjust_quantity_for_fractionability(item.symbol, raw_shares)

        amount_fmt = Decimal(str(abs(item.trade_amount))).quantize(Decimal("0.01"))
        logger.info(
            "📊 Executing action for symbol",
            extra={
                "action": item.action,
                "symbol": item.symbol,
                "trade_amount": str(amount_fmt),
                "estimated_shares": str(shares),
            },
        )
        return shares

    def _create_error_order_result(self, item: RebalancePlanItem, error: Exception) -> OrderResult:
        """Create an OrderResult for a failed order.

        Args:
            item: RebalancePlanItem that failed
            error: Exception that occurred

        Returns:
            OrderResult representing the failure

        """
        action = item.action.upper()
        if action not in ("BUY", "SELL"):
            action = "BUY"  # Fallback to BUY if invalid

        return OrderResult(
            symbol=item.symbol,
            action=action,  # type: ignore[arg-type]
            trade_amount=abs(item.trade_amount),
            shares=Decimal("0"),
            price=None,
            order_id=None,
            success=False,
            error_message=str(error),
            timestamp=datetime.now(UTC),
            order_type="MARKET",  # Default to MARKET for error cases
            filled_at=None,  # Not filled due to error
        )

    async def _execute_single_item(self, item: RebalancePlanItem) -> OrderResult:
        """Execute a single rebalance plan item.

        Args:
            item: RebalancePlanItem to execute

        Returns:
            OrderResult with execution results

        Raises:
            SymbolValidationError: If item.symbol is None or empty

        """
        # Validate symbol
        if not item.symbol or not item.symbol.strip():
            raise SymbolValidationError(
                f"Invalid symbol in rebalance plan item: {item.symbol!r}",
                symbol=item.symbol,
                reason="Symbol is None or empty",
            )

        try:
            side = "buy" if item.action == "BUY" else "sell"

            # Calculate shares to trade
            shares = self._calculate_shares_for_item(item)

            # Construct correlation_id safely (symbol already validated)
            correlation_id = f"rebalance-{item.symbol.strip()}"

            # CRITICAL FIX: For full position liquidations, use Alpaca's liquidate_position API
            # This avoids fractional share precision mismatches (e.g., 7.227358 vs 7.2273576)
            is_full_liquidation = side == "sell" and item.target_weight == Decimal("0.0")

            if is_full_liquidation:
                # Try liquidate_position API first (most reliable for full exits)
                logger.info(
                    "🎯 Using liquidate_position API for full position exit",
                    extra={
                        "symbol": item.symbol,
                        "shares": str(shares),
                        "correlation_id": correlation_id,
                    },
                )
                order_id = self.alpaca_manager.liquidate_position(item.symbol)

                if order_id:
                    # Success - liquidate_position placed the order
                    logger.info(
                        "✅ Liquidate position API succeeded",
                        extra={
                            "symbol": item.symbol,
                            "order_id": order_id,
                        },
                    )
                    # Return a success OrderResult (order details will be fetched later)
                    return OrderResult(
                        symbol=item.symbol,
                        action="SELL",
                        trade_amount=abs(item.trade_amount),
                        shares=shares,
                        price=None,  # Will be filled when order completes
                        order_id=order_id,
                        success=True,
                        error_message=None,
                        timestamp=datetime.now(UTC),
                        order_type="MARKET",  # liquidate_position uses market orders
                        filled_at=None,  # Will be updated when filled
                    )
                # liquidate_position failed, fall through to smart execution with is_complete_exit
                logger.warning(
                    "⚠️ Liquidate position API failed, falling back to smart execution",
                    extra={
                        "symbol": item.symbol,
                        "correlation_id": correlation_id,
                    },
                )

            # Use smart execution with async context (with is_complete_exit for full liquidations)
            order_result = await self.execute_order(
                symbol=item.symbol,
                side=side,
                quantity=shares,
                correlation_id=correlation_id,
                is_complete_exit=is_full_liquidation,  # Flag for quantity adjustment in market fallback
            )

            # Log result
            if order_result.success:
                logger.info(
                    "✅ Order placed successfully",
                    extra={
                        "action": item.action,
                        "symbol": item.symbol,
                        "order_id": order_result.order_id,
                    },
                )
            else:
                logger.error(
                    "❌ Failed to place order",
                    extra={
                        "action": item.action,
                        "symbol": item.symbol,
                        "error": order_result.error_message,
                    },
                )

            return order_result

        except (ValidationError, SymbolValidationError) as e:
            # Validation errors during order execution
            logger.error(
                "❌ Error executing order due to validation error",
                extra={
                    "action": item.action,
                    "symbol": item.symbol,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            return self._create_error_order_result(item, e)
        except (TradingClientError, OrderExecutionError) as e:
            # Trading client or execution errors
            logger.error(
                "❌ Error executing order due to trading error",
                extra={
                    "action": item.action,
                    "symbol": item.symbol,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            return self._create_error_order_result(item, e)
        except Exception as e:
            # Unexpected errors during order execution
            logger.error(
                "❌ Error executing order due to unexpected error",
                exc_info=True,
                extra={
                    "action": item.action,
                    "symbol": item.symbol,
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
            )
            return self._create_error_order_result(item, e)

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
                        logger.debug(
                            "Could not fetch quote for symbol",
                            extra={
                                "symbol": order.symbol,
                                "error": str(e),
                                "error_type": type(e).__name__,
                            },
                        )

                # Record order to ledger with quote data when available
                self.trade_ledger.record_filled_order(
                    order_result=order,
                    correlation_id=plan.correlation_id,
                    rebalance_plan=plan,
                    quote_at_fill=quote_at_fill,
                )

    def shutdown(self) -> None:
        """Shutdown the executor and cleanup resources.

        Note: Pricing service cleanup is handled by WebSocketConnectionManager
        when release_pricing_service() is called in __del__. The pricing service
        stop() method is async and cannot be called from this sync method.
        """
        # Pricing service is managed by WebSocketConnectionManager
        # Cleanup happens via websocket_manager.release_pricing_service() in __del__
        if self.pricing_service:
            logger.debug(
                "Pricing service will be cleaned up by WebSocketConnectionManager",
                extra={"pricing_service_active": True},
            )

        # Clear execution cache to free memory
        if hasattr(self, "_execution_cache"):
            cache_size = len(self._execution_cache)
            self._execution_cache.clear()
            logger.debug("Execution cache cleared", extra={"cache_entries_cleared": cache_size})
