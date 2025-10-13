"""Business Unit: execution | Status: current.

Phase execution functionality for sell and buy phases extracted from the main executor.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from decimal import ROUND_DOWN, Decimal
from typing import TYPE_CHECKING

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

logger = get_logger(__name__)


class PhaseExecutor:
    """Handles execution of sell and buy phases with smart execution."""

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

    async def execute_sell_phase(
        self,
        sell_items: list[RebalancePlanItem],
        correlation_id: str | None = None,
        execute_order_callback: (
            Callable[[RebalancePlanItem], Awaitable[OrderResult]] | None
        ) = None,
        monitor_orders_callback: (
            Callable[[str, list[OrderResult], str | None], Awaitable[list[OrderResult]]] | None
        ) = None,
        finalize_orders_callback: (
            Callable[..., tuple[list[OrderResult], int, Decimal]] | None
        ) = None,
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
        orders = []
        placed = 0
        succeeded = 0

        # Execute all sell orders first (placement only)
        for item in sell_items:
            if execute_order_callback:
                order_result = await execute_order_callback(item)
            else:
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
        if monitor_orders_callback and self.smart_strategy and self.enable_smart_execution:
            logger.info("🔄 Monitoring SELL orders for re-pegging opportunities...")
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
        execute_order_callback: (
            Callable[[RebalancePlanItem], Awaitable[OrderResult]] | None
        ) = None,
        monitor_orders_callback: (
            Callable[[str, list[OrderResult], str | None], Awaitable[list[OrderResult]]] | None
        ) = None,
        finalize_orders_callback: (
            Callable[..., tuple[list[OrderResult], int, Decimal]] | None
        ) = None,
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
        orders = []
        placed = 0
        succeeded = 0

        # Execute all buy orders first (placement only)
        for item in buy_items:
            # Pre-check for micro orders that will be rejected by broker constraints
            if self._should_skip_micro_order(item):
                orders.append(self._create_skipped_order_result(item))
                continue

            if execute_order_callback:
                order_result = await execute_order_callback(item)
            else:
                order_result = await self._execute_single_item(item)
            orders.append(order_result)
            placed += 1

            if order_result.order_id:
                logger.info(f"🧾 BUY {item.symbol} order placed (ID: {order_result.order_id})")
            elif not order_result.success:
                logger.error(f"❌ BUY {item.symbol} placement failed: {order_result.error_message}")

        # Monitor and re-peg buy orders that haven't filled and await completion
        if monitor_orders_callback and self.smart_strategy and self.enable_smart_execution:
            logger.info("🔄 Monitoring BUY orders for re-pegging opportunities...")
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

    def _should_skip_micro_order(self, item: RebalancePlanItem) -> bool:
        """Check if order should be skipped due to micro order constraints."""
        if self.execution_config is None:
            return False

        try:
            min_notional = getattr(
                self.execution_config,
                "min_fractional_notional_usd",
                Decimal("1.00"),
            )
            asset_info = self.alpaca_manager.get_asset_info(item.symbol)
            # Estimate shares and notional for skip logic
            est_price = (
                self.position_utils.get_price_for_estimation(item.symbol)
                if self.position_utils
                else Decimal("0")
            ) or Decimal("0")
            est_shares = abs(item.trade_amount) / est_price if est_price > 0 else Decimal("0")
            if asset_info and asset_info.fractionable:
                est_notional = (est_shares * est_price).quantize(Decimal("0.01"))
                if est_notional < min_notional:
                    logger.warning(
                        f"  ❌ Skipping BUY {item.symbol}: estimated notional ${est_notional} < ${min_notional} (fractional min)"
                    )
                    return True
        except Exception as exc:
            logger.debug(f"Error checking micro order for {item.symbol}: {exc}")

        return False

    def _create_skipped_order_result(self, item: RebalancePlanItem) -> OrderResult:
        """Create an OrderResult for a skipped order."""
        from datetime import UTC, datetime

        action = item.action.upper()
        if action not in ("BUY", "SELL"):
            action = "BUY"  # Fallback to BUY if invalid
        return OrderResult(
            symbol=item.symbol,
            action=action,  # type: ignore[arg-type]
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

    async def _execute_single_item(self, item: RebalancePlanItem) -> OrderResult:
        """Execute a single rebalance plan item.

        Args:
            item: RebalancePlanItem to execute

        Returns:
            OrderResult with execution results

        """
        import asyncio
        from datetime import UTC, datetime

        try:
            # Yield control to event loop for proper async behavior
            await asyncio.sleep(0)

            # Determine quantity (shares) to trade
            shares = self._determine_shares_to_trade(item)

            # This would need to be passed in as a callback in real usage
            # For now, create a simple fallback result
            logger.warning(f"⚠️ No order execution callback provided for {item.symbol}")
            action = item.action.upper()
            if action not in ("BUY", "SELL"):
                action = "BUY"  # Fallback to BUY if invalid
            return OrderResult(
                symbol=item.symbol,
                action=action,  # type: ignore[arg-type]
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

        except Exception as e:
            logger.error(f"❌ Error executing {item.action} for {item.symbol}: {e}")

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
                error_message=str(e),
                timestamp=datetime.now(UTC),
                order_type="MARKET",  # Default to MARKET for error cases
                filled_at=None,  # Not filled due to error
            )
