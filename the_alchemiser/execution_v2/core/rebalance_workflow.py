"""Business Unit: execution | Status: current.

Rebalance workflow orchestrator.

Orchestrates SELL → settlement → BUY phases, delegating to helpers and invoking
SettlementMonitor for proper workflow coordination.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from the_alchemiser.execution_v2.core.phase_executor import PhaseExecutor
from the_alchemiser.execution_v2.core.repeg_monitor import RepegMonitor
from the_alchemiser.execution_v2.core.settlement_monitor import SettlementMonitor
from the_alchemiser.execution_v2.models.execution_result import (
    ExecutionResultDTO,
    ExecutionStatus,
    OrderResultDTO,
)
from the_alchemiser.shared.schemas.broker import WebSocketStatus
from the_alchemiser.shared.schemas.rebalance_plan import (
    RebalancePlanDTO,
    RebalancePlanItemDTO,
)

if TYPE_CHECKING:
    from the_alchemiser.execution_v2.core.smart_execution_strategy import (
        ExecutionConfig,
        SmartExecutionStrategy,
    )
    from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
    from the_alchemiser.shared.services.real_time_pricing import RealTimePricingService

logger = logging.getLogger(__name__)


class RebalanceWorkflow:
    """Orchestrates rebalance execution workflow with settlement monitoring."""

    def __init__(
        self,
        alpaca_manager: AlpacaManager,
        pricing_service: RealTimePricingService | None = None,
        smart_strategy: SmartExecutionStrategy | None = None,
        execution_config: ExecutionConfig | None = None,
    ) -> None:
        """Initialize rebalance workflow orchestrator.

        Args:
            alpaca_manager: Alpaca broker manager
            pricing_service: Optional pricing service
            smart_strategy: Optional smart execution strategy
            execution_config: Optional execution configuration

        """
        self.alpaca_manager = alpaca_manager
        self.pricing_service = pricing_service
        self.smart_strategy = smart_strategy
        self.execution_config = execution_config

        # Initialize collaborators
        self.phase_executor = PhaseExecutor(alpaca_manager, pricing_service)
        self.repeg_monitor = RepegMonitor(smart_strategy, execution_config)
        self.settlement_monitor = SettlementMonitor(alpaca_manager)

    async def execute_rebalance_plan(self, plan: RebalancePlanDTO) -> ExecutionResultDTO:
        """Execute a rebalance plan with settlement-aware sell-first, buy-second workflow.

        Enhanced execution flow:
        1. Execute SELL orders in parallel where possible
        2. Monitor settlement and buying power release
        3. Execute BUY orders once sufficient buying power is available

        Args:
            plan: RebalancePlanDTO containing the rebalance plan

        Returns:
            ExecutionResultDTO with execution results

        """
        logger.info(
            f"🚀 Executing rebalance plan {plan.plan_id} with {len(plan.items)} items "
            "(enhanced settlement-aware)"
        )

        # Check for stale orders to free up buying power
        await self._cancel_stale_orders()

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
            orders_placed += int(sell_stats["placed"])
            orders_succeeded += int(sell_stats["succeeded"])
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
            orders_placed += int(buy_stats["placed"])
            orders_succeeded += int(buy_stats["succeeded"])
            total_trade_value += buy_stats["trade_value"]

        elif buy_items:
            # No sells to wait for, execute buys immediately
            logger.info("🔄 Phase 2: Executing BUY orders (no settlement monitoring needed)...")

            buy_orders, buy_stats = await self._execute_buy_phase(buy_items, plan.correlation_id)
            orders.extend(buy_orders)
            orders_placed += int(buy_stats["placed"])
            orders_succeeded += int(buy_stats["succeeded"])
            total_trade_value += buy_stats["trade_value"]

        # Log HOLD items
        for item in hold_items:
            logger.info(f"⏸️ Holding {item.symbol} - no action required")

        # Classify execution status
        success, status = ExecutionResultDTO.classify_execution_status(
            orders_placed, orders_succeeded
        )

        # Create execution result
        execution_result = ExecutionResultDTO(
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

        return execution_result

    async def _cancel_stale_orders(self) -> None:
        """Cancel any stale orders to free up buying power."""
        stale_timeout_minutes = 30  # Default timeout
        if self.execution_config:
            stale_timeout_minutes = self.execution_config.stale_order_timeout_minutes
            logger.debug(f"Using execution_config timeout: {stale_timeout_minutes}")
        else:
            logger.debug("No execution_config found, using default timeout")

        logger.info(f"🧹 Checking for stale orders (older than {stale_timeout_minutes} minutes)...")
        stale_result = await asyncio.to_thread(
            self.alpaca_manager.cancel_stale_orders, stale_timeout_minutes
        )
        logger.debug(f"Stale order result: {stale_result}")

        if stale_result["cancelled_count"] > 0:
            logger.info(f"🗑️ Cancelled {stale_result['cancelled_count']} stale orders")
        if stale_result["errors"]:
            logger.warning(f"⚠️ Errors during stale order cancellation: {stale_result['errors']}")

    async def _execute_sell_phase(
        self, sell_items: list[RebalancePlanItemDTO], correlation_id: str
    ) -> tuple[list[OrderResultDTO], dict[str, int | Decimal]]:
        """Execute SELL phase with re-peg monitoring."""
        # Execute sell orders
        orders, _ = await self.phase_executor.execute_phase_items(sell_items, "SELL")

        # Monitor and re-peg if smart execution is enabled
        orders = await self.repeg_monitor.monitor_and_repeg_phase_orders(
            "SELL", orders, correlation_id
        )

        # Finalize orders (wait for completion)
        orders = await self._finalize_phase_orders("SELL", orders)

        # Recalculate stats after finalization
        final_stats = self._calculate_phase_stats(orders)

        return orders, final_stats

    async def _execute_buy_phase(
        self, buy_items: list[RebalancePlanItemDTO], correlation_id: str
    ) -> tuple[list[OrderResultDTO], dict[str, int | Decimal]]:
        """Execute BUY phase without settlement monitoring."""
        # Execute buy orders
        orders, _ = await self.phase_executor.execute_phase_items(buy_items, "BUY")

        # Monitor and re-peg if smart execution is enabled
        orders = await self.repeg_monitor.monitor_and_repeg_phase_orders(
            "BUY", orders, correlation_id
        )

        # Finalize orders (wait for completion)
        orders = await self._finalize_phase_orders("BUY", orders)

        # Recalculate stats after finalization
        final_stats = self._calculate_phase_stats(orders)

        return orders, final_stats

    async def _execute_buy_phase_with_settlement_monitoring(
        self,
        buy_items: list[RebalancePlanItemDTO],
        sell_order_ids: list[str],
        correlation_id: str,
        plan_id: str | None = None,
    ) -> tuple[list[OrderResultDTO], dict[str, int | Decimal]]:
        """Execute BUY phase with settlement monitoring."""
        # Monitor sell orders for settlement
        settlement_result = await self.settlement_monitor.monitor_sell_orders_settlement(
            sell_order_ids, correlation_id, plan_id
        )

        logger.info(
            f"💰 Settlement complete: ${settlement_result.total_buying_power_released} "
            f"buying power released from {len(settlement_result.settled_order_ids)} orders"
        )

        # Now execute buy orders
        return await self._execute_buy_phase(buy_items, correlation_id)

    async def _finalize_phase_orders(
        self,
        phase_type: str,
        orders: list[OrderResultDTO],
    ) -> list[OrderResultDTO]:
        """Wait for placed orders to complete and update results based on final status."""
        try:
            order_ids = [o.order_id for o in orders if o.order_id]
            if not order_ids:
                return orders

            max_wait = self._derive_max_wait_seconds()
            final_status_map = await self._get_final_status_map(order_ids, max_wait, phase_type)
            updated_orders = self._rebuild_orders_with_final_status(orders, final_status_map)

            succeeded = sum(1 for o in updated_orders if o.success)
            logger.info(f"📊 {phase_type} phase completion: {succeeded}/{len(orders)} FILLED")
            return updated_orders
        except Exception as e:
            logger.error(f"Error finalizing {phase_type} phase orders: {e}")
            return orders

    def _derive_max_wait_seconds(self) -> int:
        """Derive maximum wait time for order completion."""
        if self.execution_config:
            return getattr(self.execution_config, "order_completion_timeout_seconds", 60)
        return 60

    async def _get_final_status_map(
        self, order_ids: list[str], max_wait: int, phase_type: str
    ) -> dict[str, tuple[str, Decimal | None]]:
        """Poll broker and return final status map for each order ID."""
        valid_order_ids, invalid_order_ids = self._validate_order_ids(order_ids, phase_type)

        final_status_map: dict[str, tuple[str, Decimal | None]] = {}
        for oid in invalid_order_ids:
            final_status_map[oid] = ("rejected", None)

        if not valid_order_ids:
            return final_status_map

        try:
            ws_result = await asyncio.to_thread(
                self.alpaca_manager.wait_for_order_completion,
                valid_order_ids,
                max_wait,
            )

            if ws_result.status != WebSocketStatus.COMPLETED:
                logger.warning(
                    "%s phase: completion wait returned %s (message: %s)",
                    phase_type,
                    ws_result.status.value,
                    ws_result.message,
                )

            completed_ids = set(ws_result.completed_order_ids)
        except Exception as exc:
            logger.warning(
                "%s phase: error while waiting for order completion: %s",
                phase_type,
                exc,
            )
            completed_ids = set()

        for oid in valid_order_ids:
            try:
                execution = await asyncio.to_thread(
                    self.alpaca_manager.get_order_execution_result, oid
                )
                status = str(getattr(execution, "status", "accepted"))
                avg_price_obj = getattr(execution, "avg_fill_price", None)
                avg_price: Decimal | None = (
                    avg_price_obj if isinstance(avg_price_obj, Decimal) else None
                )

                if oid not in completed_ids and status == "accepted":
                    status = "pending"

                final_status_map[oid] = (status, avg_price)
            except Exception as exc:
                logger.warning(f"Failed to refresh order {oid}: {exc}")
                final_status_map[oid] = ("rejected", None)

        return final_status_map

    def _rebuild_orders_with_final_status(
        self,
        orders: list[OrderResultDTO],
        final_status_map: dict[str, tuple[str, Decimal | None]],
    ) -> list[OrderResultDTO]:
        """Rebuild OrderResultDTOs with final semantics."""
        updated_orders: list[OrderResultDTO] = []

        for order in orders:
            if not order.order_id:
                updated_orders.append(order)
                continue

            status, avg_price = final_status_map.get(order.order_id, ("rejected", None))
            is_filled = status == "filled"
            error_message = None if is_filled else f"final status: {status}"
            final_price = avg_price if avg_price is not None else order.price

            updated_orders.append(
                order.model_copy(
                    update={
                        "success": is_filled,
                        "price": final_price,
                        "error_message": error_message,
                    }
                )
            )

        return updated_orders

    def _validate_order_ids(
        self, order_ids: list[str], phase_type: str
    ) -> tuple[list[str], list[str]]:
        """Validate order IDs and separate valid from invalid ones."""

        def _is_valid_uuid(value: str) -> bool:
            try:
                import uuid

                uuid.UUID(str(value))
                return True
            except Exception:
                return False

        valid = [oid for oid in order_ids if oid and _is_valid_uuid(oid)]
        invalid = [oid for oid in order_ids if not oid or not _is_valid_uuid(oid)]

        if invalid:
            logger.warning(
                "%s phase: %s invalid order IDs will be marked rejected",
                phase_type,
                len(invalid),
            )

        return valid, invalid

    def _calculate_phase_stats(self, orders: list[OrderResultDTO]) -> dict[str, int | Decimal]:
        """Calculate statistics for a completed phase."""
        placed = sum(1 for o in orders if o.order_id)
        succeeded = sum(1 for o in orders if o.success)
        trade_value = sum(abs(o.trade_amount) for o in orders if o.trade_amount and o.success)

        return {
            "placed": placed,
            "succeeded": succeeded,
            "trade_value": trade_value,
        }
