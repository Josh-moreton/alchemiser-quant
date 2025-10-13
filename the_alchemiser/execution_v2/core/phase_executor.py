"""Business Unit: execution | Status: current.

Phase execution functionality for sell and buy phases extracted from the main executor.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import ROUND_DOWN, Decimal
from typing import TYPE_CHECKING, Protocol

import structlog

from the_alchemiser.execution_v2.models.execution_result import OrderResult
from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlanItem

if TYPE_CHECKING:
    from the_alchemiser.execution_v2.core.executor import ExecutionStats
    from the_alchemiser.execution_v2.core.smart_execution_strategy import (
        ExecutionConfig,
        SmartExecutionStrategy,
    )
    from the_alchemiser.execution_v2.utils.position_utils import PositionUtils

logger: structlog.stdlib.BoundLogger = get_logger(__name__)


# Callback Protocol Definitions for Type Safety
class OrderExecutionCallback(Protocol):
    """Protocol for order execution callbacks.

    Defines the contract for callbacks that execute individual orders.
    """

    async def __call__(self, item: RebalancePlanItem) -> OrderResult:
        """Execute an order for the given rebalance plan item.

        Args:
            item: The rebalance plan item to execute

        Returns:
            OrderResult containing execution details

        """
        ...


class OrderMonitorCallback(Protocol):
    """Protocol for order monitoring callbacks.

    Defines the contract for callbacks that monitor and potentially repeg orders.
    """

    async def __call__(
        self,
        phase_type: str,
        orders: list[OrderResult],
        correlation_id: str | None,
    ) -> list[OrderResult]:
        """Monitor and potentially repeg orders.

        Args:
            phase_type: Type of phase (SELL or BUY)
            orders: List of orders to monitor
            correlation_id: Optional correlation ID for tracking

        Returns:
            Updated list of order results

        """
        ...


class OrderFinalizerCallback(Protocol):
    """Protocol for order finalization callbacks.

    Defines the contract for callbacks that finalize order statuses.
    """

    def __call__(
        self,
        *,
        phase_type: str,
        orders: list[OrderResult],
        items: list[RebalancePlanItem],
    ) -> tuple[list[OrderResult], int, Decimal]:
        """Finalize order statuses and calculate metrics.

        Args:
            phase_type: Type of phase (SELL or BUY)
            orders: List of orders to finalize
            items: Original rebalance plan items

        Returns:
            Tuple of (finalized orders, succeeded count, trade value)

        """
        ...


class PhaseExecutor:
    """Handles execution of sell and buy phases with smart execution.

    This class orchestrates the execution of portfolio rebalancing orders in two phases:
    1. SELL phase: Liquidates positions to free up capital
    2. BUY phase: Allocates freed capital to new/increased positions

    Pre-conditions:
        - AlpacaManager must be initialized and authenticated
        - RebalancePlanItems must have valid symbols and trade amounts
        - Callbacks (if provided) must be async-compatible

    Post-conditions:
        - Returns OrderResults for all executed/attempted orders
        - ExecutionStats reflect actual order placement and success counts
        - Failed orders are logged with error context

    Invariants:
        - SELL phase always executes before BUY phase (enforced by caller)
        - All monetary values use Decimal for precision
        - Order execution is idempotent within a single phase invocation

    Idempotency:
        - Each phase invocation maintains an execution context
        - Duplicate items within same phase are detected and skipped
        - Cross-invocation idempotency relies on correlation_id uniqueness
        - Callers should use unique correlation_id per rebalance cycle

    Thread-safety: Not thread-safe - designed for single-thread async execution
    """

    def __init__(
        self,
        alpaca_manager: AlpacaManager,
        position_utils: PositionUtils | None,
        smart_strategy: SmartExecutionStrategy | None,
        execution_config: ExecutionConfig | None,
        *,
        enable_smart_execution: bool = True,
    ) -> None:
        """Initialize the phase executor.

        Args:
            alpaca_manager: Alpaca broker manager
            position_utils: Position utilities for price and quantity calculations
            smart_strategy: Smart execution strategy
            execution_config: Execution configuration
            enable_smart_execution: Whether smart execution is enabled

        """
        self.alpaca_manager = alpaca_manager
        self.position_utils = position_utils
        self.smart_strategy = smart_strategy
        self.execution_config = execution_config
        self.enable_smart_execution = enable_smart_execution

        # Idempotency tracking: tracks executed items within current session
        # Key: (symbol, action, trade_amount_str)
        # Value: OrderResult
        self._execution_cache: dict[tuple[str, str, str], OrderResult] = {}

    def _get_idempotency_key(self, item: RebalancePlanItem) -> tuple[str, str, str]:
        """Generate idempotency key for a rebalance item.

        Creates a unique key based on symbol, action, and trade amount to detect
        duplicate execution requests within the same phase.

        Args:
            item: RebalancePlanItem to generate key for

        Returns:
            Tuple of (symbol, action, trade_amount_str) as idempotency key

        """
        # Use string representation of Decimal to ensure exact matching
        return (item.symbol, item.action, str(item.trade_amount))

    def _check_duplicate_execution(
        self,
        item: RebalancePlanItem,
        bound_logger: structlog.stdlib.BoundLogger,
    ) -> OrderResult | None:
        """Check if item has already been executed in this phase.

        Implements idempotency protection by tracking executed items.
        If a duplicate is detected, returns the cached result instead
        of re-executing.

        Args:
            item: RebalancePlanItem to check
            bound_logger: Logger instance with bound context

        Returns:
            Cached OrderResult if duplicate detected, None otherwise

        """
        idempotency_key = self._get_idempotency_key(item)

        if idempotency_key in self._execution_cache:
            cached_result = self._execution_cache[idempotency_key]
            bound_logger.warning(
                f"🔁 Duplicate execution detected for {item.symbol} {item.action}, "
                f"returning cached result",
                extra={
                    "symbol": item.symbol,
                    "action": item.action,
                    "trade_amount": float(item.trade_amount),
                    "cached_order_id": cached_result.order_id,
                    "reason": "duplicate_execution_prevented",
                },
            )
            return cached_result

        return None

    def _cache_execution_result(
        self, item: RebalancePlanItem, result: OrderResult
    ) -> None:
        """Cache execution result for idempotency tracking.

        Stores the result in the execution cache to prevent duplicate
        execution of the same item within this phase.

        Args:
            item: RebalancePlanItem that was executed
            result: OrderResult from execution

        """
        idempotency_key = self._get_idempotency_key(item)
        self._execution_cache[idempotency_key] = result

    def clear_execution_cache(self) -> None:
        """Clear the execution cache.

        Should be called between different rebalance cycles to allow
        the same items to be executed again in a new context.
        Typically called by the parent Executor between plan executions.

        """
        self._execution_cache.clear()

    async def execute_sell_phase(
        self,
        sell_items: list[RebalancePlanItem],
        correlation_id: str | None = None,
        execute_order_callback: OrderExecutionCallback | None = None,
        monitor_orders_callback: OrderMonitorCallback | None = None,
        finalize_orders_callback: OrderFinalizerCallback | None = None,
    ) -> tuple[list[OrderResult], ExecutionStats]:
        """Execute sell orders phase with integrated re-pegging monitoring.

        Args:
            sell_items: List of sell order items
            correlation_id: Optional correlation ID for tracking
            execute_order_callback: Callback to execute individual orders
            monitor_orders_callback: Callback to monitor and repeg orders
            finalize_orders_callback: Callback to finalize orders

        Returns:
            Tuple of (order results, execution statistics)

        """
        # Bind correlation_id to logger context for observability
        bound_logger = logger.bind(correlation_id=correlation_id) if correlation_id else logger

        orders = []
        placed = 0
        succeeded = 0

        # Execute all sell orders first (placement only)
        for item in sell_items:
            # Check for duplicate execution (idempotency)
            duplicate_result = self._check_duplicate_execution(item, bound_logger)
            if duplicate_result:
                orders.append(duplicate_result)
                continue  # Skip execution, use cached result

            if execute_order_callback:
                order_result = await execute_order_callback(item)
            else:
                order_result = await self._execute_single_item(item, bound_logger)

            # Cache result for idempotency
            self._cache_execution_result(item, order_result)

            orders.append(order_result)
            placed += 1

            if order_result.order_id:
                bound_logger.info(f"🧾 SELL {item.symbol} order placed (ID: {order_result.order_id})")
            elif not order_result.success:
                bound_logger.error(
                    f"❌ SELL {item.symbol} placement failed: {order_result.error_message}"
                )

        # Monitor and re-peg sell orders that haven't filled and await completion
        if monitor_orders_callback and self.smart_strategy and self.enable_smart_execution:
            bound_logger.info("🔄 Monitoring SELL orders for re-pegging opportunities...")
            orders = await monitor_orders_callback("SELL", orders, correlation_id)

        # Await completion and finalize statuses
        if finalize_orders_callback:
            orders, succeeded, trade_value = finalize_orders_callback(
                phase_type="SELL", orders=orders, items=sell_items
            )

        return orders, {
            "placed": placed,
            "succeeded": succeeded,
            "trade_value": trade_value if finalize_orders_callback else Decimal("0"),
        }

    async def execute_buy_phase(
        self,
        buy_items: list[RebalancePlanItem],
        correlation_id: str | None = None,
        execute_order_callback: OrderExecutionCallback | None = None,
        monitor_orders_callback: OrderMonitorCallback | None = None,
        finalize_orders_callback: OrderFinalizerCallback | None = None,
    ) -> tuple[list[OrderResult], ExecutionStats]:
        """Execute buy orders phase with integrated re-pegging monitoring.

        Args:
            buy_items: List of buy order items
            correlation_id: Optional correlation ID for tracking
            execute_order_callback: Callback to execute individual orders
            monitor_orders_callback: Callback to monitor and repeg orders
            finalize_orders_callback: Callback to finalize orders

        Returns:
            Tuple of (order results, execution statistics)

        """
        # Bind correlation_id to logger context for observability
        bound_logger = logger.bind(correlation_id=correlation_id) if correlation_id else logger

        orders = []
        placed = 0
        succeeded = 0

        # Execute all buy orders first (placement only)
        for item in buy_items:
            # Check for duplicate execution (idempotency)
            duplicate_result = self._check_duplicate_execution(item, bound_logger)
            if duplicate_result:
                orders.append(duplicate_result)
                continue  # Skip execution, use cached result

            # Pre-check for micro orders that will be rejected by broker constraints
            skip_result = self._check_micro_order_skip(item, bound_logger)
            if skip_result:
                self._cache_execution_result(item, skip_result)  # Cache skip results too
                orders.append(skip_result)
                continue

            if execute_order_callback:
                order_result = await execute_order_callback(item)
            else:
                order_result = await self._execute_single_item(item, bound_logger)

            # Cache result for idempotency
            self._cache_execution_result(item, order_result)

            orders.append(order_result)
            placed += 1

            if order_result.order_id:
                bound_logger.info(f"🧾 BUY {item.symbol} order placed (ID: {order_result.order_id})")
            elif not order_result.success:
                bound_logger.error(f"❌ BUY {item.symbol} placement failed: {order_result.error_message}")

        # Monitor and re-peg buy orders that haven't filled and await completion
        if monitor_orders_callback and self.smart_strategy and self.enable_smart_execution:
            bound_logger.info("🔄 Monitoring BUY orders for re-pegging opportunities...")
            orders = await monitor_orders_callback("BUY", orders, correlation_id)

        # Await completion and finalize statuses
        if finalize_orders_callback:
            orders, succeeded, trade_value = finalize_orders_callback(
                phase_type="BUY", orders=orders, items=buy_items
            )

        return orders, {
            "placed": placed,
            "succeeded": succeeded,
            "trade_value": trade_value if finalize_orders_callback else Decimal("0"),
        }

    def _check_micro_order_skip(
        self, item: RebalancePlanItem, bound_logger: structlog.stdlib.BoundLogger
    ) -> OrderResult | None:
        """Check if order should be skipped due to micro-order constraints.

        This method validates that the order meets minimum notional value requirements
        for fractional shares. Orders below the minimum are skipped to avoid broker rejection.

        Args:
            item: RebalancePlanItem to validate
            bound_logger: Logger instance with bound context

        Returns:
            OrderResult if order should be skipped, None otherwise

        Raises:
            AlpacaAPIError: If asset info retrieval fails
            ValueError: If price estimation fails critically

        """
        if self.execution_config is None:
            return None

        try:
            # Get minimum notional threshold from config
            if hasattr(self.execution_config, "min_fractional_notional_usd"):
                min_notional = self.execution_config.min_fractional_notional_usd
            else:
                min_notional = Decimal("1.00")  # Safe default

            asset_info = self.alpaca_manager.get_asset_info(item.symbol)

            # Estimate shares and notional for skip logic
            est_price = (
                self.position_utils.get_price_for_estimation(item.symbol)
                if self.position_utils
                else Decimal("0")
            ) or Decimal("0")

            if est_price <= Decimal("0"):
                # Can't validate without price, let order proceed
                return None

            est_shares = abs(item.trade_amount) / est_price

            # Only check for fractional assets
            if asset_info and asset_info.fractionable:
                est_notional = (est_shares * est_price).quantize(Decimal("0.01"))
                if est_notional < min_notional:
                    bound_logger.warning(
                        f"❌ Skipping BUY {item.symbol}: estimated notional "
                        f"${est_notional} < ${min_notional} (fractional min)",
                        extra={
                            "symbol": item.symbol,
                            "estimated_notional": float(est_notional),
                            "min_notional": float(min_notional),
                            "reason": "below_minimum_notional",
                        },
                    )
                    return self._create_skipped_order_result(item)
        except ValueError as exc:
            # Critical calculation error - log and let order proceed
            bound_logger.warning(
                f"Price estimation failed for {item.symbol}, skipping validation: {exc}",
                exc_info=True,
                extra={"symbol": item.symbol, "error_type": "price_estimation_failed"},
            )
        except Exception as exc:
            # Unexpected error - log with full context but don't block order
            bound_logger.warning(
                f"Error checking micro order for {item.symbol}: {exc}",
                exc_info=True,
                extra={"symbol": item.symbol, "error_type": type(exc).__name__},
            )

        return None

    def _should_skip_micro_order(self, item: RebalancePlanItem) -> bool:
        """Check if order should be skipped due to micro order constraints.

        DEPRECATED: Use _check_micro_order_skip instead for better error handling.
        Kept for backward compatibility.
        """
        result = self._check_micro_order_skip(item, logger)
        return result is not None

    def _create_skipped_order_result(self, item: RebalancePlanItem) -> OrderResult:
        """Create an OrderResult for a skipped order."""
        return OrderResult(
            symbol=item.symbol,
            action=item.action,
            trade_amount=Decimal("0"),
            shares=Decimal("0"),
            price=None,
            order_id=None,
            success=False,
            error_message="Skipped: estimated notional below minimum",
            timestamp=datetime.now(UTC),
            order_type="MARKET",  # Default to MARKET for skipped orders
            filled_at=None,  # Not filled since order was skipped
        )

    def _calculate_liquidation_shares(self, symbol: str) -> Decimal:
        """Calculate shares for liquidation (full position sell).

        For liquidation, we MUST sell the exact position quantity regardless
        of fractionability rules. This is critical because:
        1. We need to close out the position completely
        2. Brokers accept fractional sells even for non-fractionable assets
        3. Rounding down would leave orphaned fractional positions

        Args:
            symbol: Stock symbol

        Returns:
            Number of shares to sell (exact position quantity)

        """
        if not self.position_utils:
            return Decimal("0")

        # For liquidation, return the EXACT position quantity without rounding
        # Fractionability rules only apply to NEW purchases, not position closes
        return self.position_utils.get_position_quantity(symbol)

    def _calculate_shares_from_amount(self, symbol: str, trade_amount: Decimal) -> Decimal:
        """Calculate shares from trade amount using estimated price.

        Args:
            symbol: Stock symbol
            trade_amount: Dollar amount to trade

        Returns:
            Number of shares to trade

        """
        price = (
            self.position_utils.get_price_for_estimation(symbol) if self.position_utils else None
        )

        if price is None or price <= Decimal("0"):
            logger.warning(f"⚠️ Price unavailable for {symbol}; defaulting to 1 share")
            return Decimal("1")

        raw_shares = abs(trade_amount) / price
        if self.position_utils:
            return self.position_utils.adjust_quantity_for_fractionability(symbol, raw_shares)
        return raw_shares.quantize(Decimal("1"), rounding=ROUND_DOWN)

    def _determine_shares_to_trade(self, item: RebalancePlanItem) -> Decimal:
        """Determine the number of shares to trade for a given item.

        Args:
            item: RebalancePlanItem to process

        Returns:
            Number of shares to trade

        """
        if item.action == "SELL" and item.target_weight == Decimal("0.0"):
            shares = self._calculate_liquidation_shares(item.symbol)
            logger.info(f"📊 Liquidating {item.symbol}: selling {shares} shares (full position)")
        else:
            shares = self._calculate_shares_from_amount(item.symbol, item.trade_amount)
            amount_fmt = Decimal(str(abs(item.trade_amount))).quantize(Decimal("0.01"))
            logger.info(
                f"📊 Executing {item.action} for {item.symbol}: "
                f"${amount_fmt} (estimated {shares} shares)"
            )
        return shares

    async def _execute_single_item(
        self, item: RebalancePlanItem, bound_logger: structlog.stdlib.BoundLogger
    ) -> OrderResult:
        """Execute a single rebalance plan item.

        Args:
            item: RebalancePlanItem to execute
            bound_logger: Logger instance with bound context

        Returns:
            OrderResult with execution results

        """
        try:
            # Yield control to event loop for proper async behavior
            await asyncio.sleep(0)

            # Determine quantity (shares) to trade
            shares = self._determine_shares_to_trade(item)

            # This would need to be passed in as a callback in real usage
            # For now, create a simple fallback result
            bound_logger.error(
                f"⚠️ No order execution callback provided for {item.symbol}",
                extra={
                    "symbol": item.symbol,
                    "action": item.action,
                    "shares": float(shares),
                    "reason": "missing_callback",
                },
            )
            return OrderResult(
                symbol=item.symbol,
                action=item.action,
                trade_amount=abs(item.trade_amount),
                shares=shares,
                price=None,
                order_id=None,
                success=False,
                error_message="No execution callback provided",
                timestamp=datetime.now(UTC),
                order_type="MARKET",  # Default to MARKET for fallback
                filled_at=None,  # Not filled due to missing callback
            )

        except ValueError as e:
            # Specific handling for value/calculation errors
            bound_logger.error(
                f"❌ Value error executing {item.action} for {item.symbol}: {e}",
                exc_info=True,
                extra={
                    "symbol": item.symbol,
                    "action": item.action,
                    "error_type": "value_error",
                },
            )
            return OrderResult(
                symbol=item.symbol,
                action=item.action,
                trade_amount=abs(item.trade_amount),
                shares=Decimal("0"),
                price=None,
                order_id=None,
                success=False,
                error_message=f"Value error: {e}",
                timestamp=datetime.now(UTC),
                order_type="MARKET",
                filled_at=None,
            )
        except Exception as e:
            # Catch-all for unexpected errors with full stack trace
            bound_logger.error(
                f"❌ Error executing {item.action} for {item.symbol}: {e}",
                exc_info=True,
                extra={
                    "symbol": item.symbol,
                    "action": item.action,
                    "error_type": type(e).__name__,
                },
            )
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
