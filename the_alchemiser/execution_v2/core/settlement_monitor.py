"""Business Unit: execution | Status: current.

Settlement monitoring service for tracking order completion and buying power release.

This module provides event-driven settlement monitoring that tracks sell order completion
and buying power release to coordinate sell-first, buy-second execution workflows.

Key Features:
- Async settlement monitoring with configurable polling intervals
- Event emission for order settlement completion
- Buying power calculation and release tracking
- Integration with existing AlpacaManager polling infrastructure
- Proper correlation ID tracking for execution workflow coordination
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from the_alchemiser.shared.events import (
    BulkSettlementCompleted,
    OrderSettlementCompleted,
)
from the_alchemiser.shared.events.bus import EventBus

if TYPE_CHECKING:
    from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager

logger = logging.getLogger(__name__)


class SettlementMonitor:
    """Settlement monitoring service for tracking order completion and buying power release."""

    def __init__(
        self,
        alpaca_manager: AlpacaManager,
        event_bus: EventBus | None = None,
        polling_interval_seconds: float = 0.5,
        max_wait_seconds: int = 60,
    ) -> None:
        """Initialize settlement monitor.

        Args:
            alpaca_manager: Alpaca broker manager for order status checking
            event_bus: Event bus for emitting settlement events (optional)
            polling_interval_seconds: How often to check order status
            max_wait_seconds: Maximum time to wait for settlement

        """
        self.alpaca_manager = alpaca_manager
        self.event_bus = event_bus
        self.polling_interval = polling_interval_seconds
        self.max_wait_seconds = max_wait_seconds

        # Track monitoring sessions
        self._active_monitors: dict[str, asyncio.Task[None]] = {}
        self._settlement_results: dict[str, dict[str, Any]] = {}

    async def monitor_sell_orders_settlement(
        self,
        sell_order_ids: list[str],
        correlation_id: str,
        plan_id: str | None = None,
    ) -> BulkSettlementCompleted:
        """Monitor sell orders for settlement and calculate buying power release.

        Args:
            sell_order_ids: List of sell order IDs to monitor
            correlation_id: Correlation ID for tracking
            plan_id: Execution plan ID (optional)

        Returns:
            BulkSettlementCompleted event with settlement details

        """
        logger.info(
            f"🔍 Starting settlement monitoring for {len(sell_order_ids)} sell orders "
            f"(correlation: {correlation_id})"
        )

        settled_orders: list[str] = []
        total_buying_power_released = Decimal("0")
        settlement_details: dict[str, dict[str, Any]] = {}
        start_time = datetime.now(UTC)

        try:
            # Monitor each sell order for completion
            for order_id in sell_order_ids:
                settlement_result = await self._monitor_single_order_settlement(
                    order_id, correlation_id
                )

                if settlement_result:
                    settled_orders.append(order_id)
                    settlement_details[order_id] = settlement_result

                    # Calculate buying power released (for sell orders, this is the settled value)
                    if settlement_result.get("side") == "SELL":
                        settled_value = settlement_result.get("settled_value", Decimal("0"))
                        total_buying_power_released += settled_value

                        logger.info(
                            f"✅ Sell order {order_id} settled: ${settled_value} "
                            "buying power released"
                        )

        except Exception as e:
            logger.error(f"❌ Error monitoring settlement: {e}")

        # Create and emit bulk settlement event
        settlement_event = BulkSettlementCompleted(
            correlation_id=correlation_id,
            causation_id=correlation_id,
            event_id=self._generate_event_id(),
            timestamp=datetime.now(UTC),
            source_module="execution_v2.settlement_monitor",
            settled_order_ids=settled_orders,
            total_buying_power_released=total_buying_power_released,
            settlement_details=settlement_details,
            execution_plan_id=plan_id,
        )

        if self.event_bus:
            self.event_bus.publish(settlement_event)

        execution_time = (datetime.now(UTC) - start_time).total_seconds()
        logger.info(
            f"🎯 Settlement monitoring complete: {len(settled_orders)}/{len(sell_order_ids)} "
            f"orders settled, ${total_buying_power_released} buying power released "
            f"in {execution_time:.1f}s"
        )

        return settlement_event

    async def _monitor_single_order_settlement(
        self, order_id: str, correlation_id: str
    ) -> dict[str, Any] | None:
        """Monitor a single order for settlement completion.

        Args:
            order_id: Order ID to monitor
            correlation_id: Correlation ID for tracking

        Returns:
            Settlement details if order completed, None if timed out

        """
        start_time = datetime.now(UTC)

        while (datetime.now(UTC) - start_time).total_seconds() < self.max_wait_seconds:
            try:
                # Check order status using existing AlpacaManager method
                order_status = self.alpaca_manager._check_order_completion_status(order_id)

                if order_status in ["FILLED", "CANCELED", "REJECTED", "EXPIRED"]:
                    # Order reached final state, get full order details
                    order_details = await self._get_order_settlement_details(order_id)

                    if order_details and order_status == "FILLED" and self.event_bus:
                        settlement_event = OrderSettlementCompleted(
                            correlation_id=correlation_id,
                            causation_id=correlation_id,
                            event_id=self._generate_event_id(),
                            timestamp=datetime.now(UTC),
                            source_module="execution_v2.settlement_monitor",
                            order_id=order_id,
                            symbol=order_details["symbol"],
                            side=order_details["side"],
                            settled_quantity=order_details["settled_quantity"],
                            settlement_price=order_details["settlement_price"],
                            settled_value=order_details["settled_value"],
                            buying_power_released=(
                                order_details["settled_value"]
                                if order_details["side"] == "SELL"
                                else Decimal("0")
                            ),
                            original_correlation_id=correlation_id,
                        )
                        self.event_bus.publish(settlement_event)

                    return order_details

                # Wait before next check
                await asyncio.sleep(self.polling_interval)

            except Exception as e:
                logger.warning(f"Error checking order {order_id} status: {e}")
                await asyncio.sleep(self.polling_interval)

        logger.warning(f"⏰ Settlement monitoring timeout for order {order_id}")
        return None

    async def _get_order_settlement_details(self, order_id: str) -> dict[str, Any] | None:
        """Get detailed settlement information for a completed order.

        Args:
            order_id: Order ID to get details for

        Returns:
            Dictionary with settlement details or None if error

        """
        try:
            # Use AlpacaManager to get order details
            order = self.alpaca_manager._trading_client.get_order_by_id(order_id)

            if not order:
                return None

            # Extract order details
            symbol = getattr(order, "symbol", "")
            side = getattr(order, "side", "").upper()
            filled_qty = getattr(order, "filled_qty", 0)
            filled_avg_price = getattr(order, "filled_avg_price", 0)

            settled_quantity = Decimal(str(filled_qty)) if filled_qty else Decimal("0")
            settlement_price = Decimal(str(filled_avg_price)) if filled_avg_price else Decimal("0")
            settled_value = settled_quantity * settlement_price

            return {
                "symbol": symbol,
                "side": side,
                "settled_quantity": settled_quantity,
                "settlement_price": settlement_price,
                "settled_value": settled_value,
                "status": getattr(order, "status", ""),
                "order_id": order_id,
            }

        except Exception as e:
            logger.error(f"Error getting order details for {order_id}: {e}")
            return None

    def _generate_event_id(self) -> str:
        """Generate a unique event ID."""
        import uuid

        return str(uuid.uuid4())

    async def wait_for_settlement_threshold(
        self,
        target_buying_power: Decimal,
        sell_order_ids: list[str],
        correlation_id: str,
    ) -> bool:
        """Wait until sufficient buying power is released from sell order settlements.

        Args:
            target_buying_power: Minimum buying power needed
            sell_order_ids: Sell orders to monitor
            correlation_id: Correlation ID for tracking

        Returns:
            True if threshold reached, False if timeout

        """
        logger.info(
            f"💰 Waiting for ${target_buying_power} buying power release from "
            f"{len(sell_order_ids)} sell orders (correlation: {correlation_id})"
        )

        start_time = datetime.now(UTC)
        accumulated_buying_power = Decimal("0")

        while (datetime.now(UTC) - start_time).total_seconds() < self.max_wait_seconds:
            for order_id in sell_order_ids:
                settlement_details = await self._get_order_settlement_details(order_id)

                if settlement_details and settlement_details.get("side") == "SELL":
                    settled_value = settlement_details.get("settled_value", Decimal("0"))
                    accumulated_buying_power += settled_value

            if accumulated_buying_power >= target_buying_power:
                logger.info(f"✅ Buying power threshold reached: ${accumulated_buying_power}")
                return True

            await asyncio.sleep(self.polling_interval)

        logger.warning(
            f"⏰ Buying power threshold timeout: ${accumulated_buying_power}/${target_buying_power}"
        )
        return False

    def cleanup_completed_monitors(self) -> None:
        """Clean up completed monitoring tasks."""
        completed_tasks = [
            task_id for task_id, task in self._active_monitors.items() if task.done()
        ]

        for task_id in completed_tasks:
            del self._active_monitors[task_id]

        if completed_tasks:
            logger.debug(f"🧹 Cleaned up {len(completed_tasks)} completed monitoring tasks")
