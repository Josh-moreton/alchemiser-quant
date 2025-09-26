"""Business Unit: execution | Status: current.

Repeg monitor for smart execution strategy integration.

Thin adapter bridging existing smart strategy RepegManager into the workflow phases
without duplicating logic.
"""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from the_alchemiser.execution_v2.models.execution_result import OrderResultDTO

if TYPE_CHECKING:
    from the_alchemiser.execution_v2.core.smart_execution_strategy import (
        ExecutionConfig,
        SmartExecutionStrategy,
        SmartOrderResult,
    )

logger = logging.getLogger(__name__)


class RepegMonitor:
    """Repeg monitoring adapter for smart execution strategy integration."""

    def __init__(
        self,
        smart_strategy: SmartExecutionStrategy | None = None,
        execution_config: ExecutionConfig | None = None,
    ) -> None:
        """Initialize repeg monitor.

        Args:
            smart_strategy: Smart execution strategy instance
            execution_config: Execution configuration

        """
        self.smart_strategy = smart_strategy
        self.execution_config = execution_config

    async def monitor_and_repeg_phase_orders(
        self,
        phase_type: str,
        orders: list[OrderResultDTO],
        correlation_id: str | None = None,
    ) -> list[OrderResultDTO]:
        """Monitor and re-peg orders from a specific execution phase.

        Args:
            phase_type: Type of phase ("SELL" or "BUY")
            orders: List of orders from this phase to monitor
            correlation_id: Optional correlation ID for tracking

        Returns:
            Updated list of orders with any re-pegged order IDs swapped in.

        """
        if not self.smart_strategy:
            logger.info(
                f"📊 {phase_type} phase: Smart strategy disabled; skipping re-peg loop"
            )
            return orders

        config = self._get_repeg_monitoring_config()
        self._log_monitoring_config(phase_type, config)

        return await self._execute_repeg_monitoring_loop(
            phase_type, orders, config, time.time(), correlation_id
        )

    def _get_repeg_monitoring_config(self) -> dict[str, int]:
        """Get configuration parameters for repeg monitoring."""
        config = {
            "max_repegs": 5,
            "fill_wait_seconds": 15,
            "wait_between_checks": 1,
            "max_total_wait": 60,
        }

        try:
            if self.execution_config is not None:
                config["max_repegs"] = getattr(
                    self.execution_config, "max_repegs_per_order", 5
                )
                config["fill_wait_seconds"] = int(
                    getattr(self.execution_config, "fill_wait_seconds", 15)
                )
                config["wait_between_checks"] = max(
                    1, min(config["fill_wait_seconds"] // 5, 5)
                )  # Check 5x per fill_wait period
                placement_timeout = int(
                    getattr(
                        self.execution_config, "order_placement_timeout_seconds", 30
                    )
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
        logger.debug(
            f"{phase_type} re-peg monitoring: max_repegs={config['max_repegs']}, "
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
        """Execute the main repeg monitoring loop."""
        # Extract orders with valid IDs for monitoring
        monitorable_orders = [o for o in orders if o.order_id and o.success]
        if not monitorable_orders:
            logger.info(f"📊 {phase_type} phase: No orders to monitor for re-pegging")
            return orders

        logger.info(
            f"🔄 {phase_type} monitoring: tracking {len(monitorable_orders)} orders for re-peg"
        )

        # Create a mapping from original order ID to order index
        order_id_to_index = {o.order_id: i for i, o in enumerate(orders) if o.order_id}

        iteration = 0
        max_iterations = config["max_total_wait"] // config["wait_between_checks"]

        while iteration < max_iterations:
            elapsed = time.time() - start_time
            if elapsed > config["max_total_wait"]:
                logger.warning(
                    f"⏰ {phase_type} monitoring timeout after {elapsed:.1f}s"
                )
                break

            try:
                # Check each monitorable order for re-peg opportunities
                for order in monitorable_orders[:]:  # Copy list to allow modification
                    if not order.order_id:
                        continue

                    # Delegate to smart strategy for re-peg logic
                    repeg_result = await self._check_and_repeg_order(
                        order, phase_type, config, correlation_id
                    )

                    if repeg_result and hasattr(repeg_result, "order_id"):
                        # Update the order in the original list
                        original_index = order_id_to_index.get(order.order_id)
                        if original_index is not None:
                            # Create updated order with new ID
                            updated_order = self._create_updated_order_from_repeg(
                                orders[original_index], repeg_result
                            )
                            orders[original_index] = updated_order

                            # Update tracking
                            if updated_order.order_id:
                                order_id_to_index[updated_order.order_id] = (
                                    original_index
                                )

                            self._log_repeg_status(phase_type, repeg_result)

                # Wait before next iteration
                await asyncio.sleep(config["wait_between_checks"])
                iteration += 1

            except Exception as exc:
                logger.error(f"❌ Error in {phase_type} re-peg monitoring: {exc}")
                break

        return orders

    async def _check_and_repeg_order(
        self,
        order: OrderResultDTO,
        phase_type: str,
        config: dict[str, int],
        correlation_id: str | None = None,
    ) -> SmartOrderResult | None:
        """Check and potentially re-peg a single order."""
        if not self.smart_strategy or not order.order_id:
            return None

        try:
            await asyncio.sleep(0)
            # This would delegate to the smart strategy's repeg logic
            # For now, we return None to indicate no re-peg needed
            # In a full implementation, this would call smart_strategy.check_and_repeg_order()
            return None
        except Exception as exc:
            logger.debug(f"Re-peg check failed for {order.order_id}: {exc}")
            return None

    def _create_updated_order_from_repeg(
        self, original_order: OrderResultDTO, repeg_result: SmartOrderResult
    ) -> OrderResultDTO:
        """Create updated order DTO from repeg result."""
        # Extract new order ID and other details from repeg result
        new_order_id = getattr(repeg_result, "order_id", original_order.order_id)

        # Create updated order with new information
        return OrderResultDTO(
            symbol=original_order.symbol,
            action=original_order.action,
            trade_amount=original_order.trade_amount,
            shares=original_order.shares,
            price=original_order.price,
            order_id=new_order_id,
            success=original_order.success,
            error_message=original_order.error_message,
            timestamp=datetime.now(UTC),
        )

    def _log_repeg_status(
        self, phase_type: str, repeg_result: SmartOrderResult
    ) -> None:
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
            logger.debug(f"✅ {phase_type} REPEG {repegs_used}/5: {symbol} {order_id}")
