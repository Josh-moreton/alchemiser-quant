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
import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from the_alchemiser.shared.errors.exceptions import (
    DataProviderError,
    OrderExecutionError,
    TradingClientError,
)
from the_alchemiser.shared.events import (
    BulkSettlementCompleted,
    OrderSettlementCompleted,
)
from the_alchemiser.shared.events.bus import EventBus
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.services.buying_power_service import BuyingPowerService

if TYPE_CHECKING:
    from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager

logger = get_logger(__name__)


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
            polling_interval_seconds: How often to check order status (must be positive)
            max_wait_seconds: Maximum time to wait for settlement (must be positive)

        Raises:
            ValueError: If timeout parameters are invalid

        """
        # Validate timeout parameters
        if polling_interval_seconds <= 0:
            raise ValueError(
                f"polling_interval_seconds must be positive, got {polling_interval_seconds}"
            )
        if max_wait_seconds <= 0:
            raise ValueError(f"max_wait_seconds must be positive, got {max_wait_seconds}")
        if polling_interval_seconds >= max_wait_seconds:
            raise ValueError(
                f"polling_interval_seconds ({polling_interval_seconds}) must be less than "
                f"max_wait_seconds ({max_wait_seconds})"
            )

        self.alpaca_manager = alpaca_manager
        self.event_bus = event_bus
        self.polling_interval = polling_interval_seconds
        self.max_wait_seconds = max_wait_seconds

        # Initialize buying power service
        self.buying_power_service = BuyingPowerService(alpaca_manager)

        # Track monitoring sessions
        self._active_monitors: dict[str, asyncio.Task[None]] = {}

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
                            "buying power released",
                            correlation_id=correlation_id,
                            order_id=order_id,
                            settled_value=str(settled_value),
                        )

        except (DataProviderError, TradingClientError, OrderExecutionError) as e:
            logger.error(
                "❌ Error monitoring settlement",
                error=str(e),
                error_type=type(e).__name__,
                correlation_id=correlation_id,
            )

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

    async def verify_buying_power_available_after_settlement(
        self,
        expected_buying_power: Decimal,
        settlement_correlation_id: str,
        max_wait_seconds: int = 30,
    ) -> tuple[bool, Decimal]:
        """Verify that buying power is actually available after settlement.

        This addresses the timing issue where Alpaca's account buying_power field
        hasn't been updated yet even though sell orders have settled.

        Note:
            This retry/backoff handles post-settlement account synchronization only.
            It is not related to price repegging logic.

        Args:
            expected_buying_power: Expected minimum buying power after settlement
            settlement_correlation_id: Correlation ID for tracking
            max_wait_seconds: Maximum time to wait for buying power update

        Returns:
            Tuple of (is_available, actual_buying_power)

        """
        logger.info(
            f"💰 Verifying ${expected_buying_power} buying power availability after settlement "
            f"(correlation: {settlement_correlation_id})"
        )

        # Calculate retry parameters based on max_wait_seconds with explicit
        # exponential backoff (1s, 2s, 4s, 8s, ...). Bound the cumulative wait
        # time to max_wait_seconds and cap retries to a small number to avoid
        # overly long waits during execution.
        INITIAL_BACKOFF_SECONDS = 1.0
        MAX_RETRIES = 8
        # Compute the maximum retries such that the sum of waits does not exceed max_wait_seconds.
        total = 0
        retries = 0
        while retries < MAX_RETRIES:
            next_wait = INITIAL_BACKOFF_SECONDS * (2**retries)
            if total + next_wait > max_wait_seconds:
                break
            total += next_wait
            retries += 1
        max_retries = max(1, retries)
        initial_wait = INITIAL_BACKOFF_SECONDS

        # Use asyncio.to_thread to make the synchronous call properly async
        is_available, actual_buying_power = await asyncio.to_thread(
            self.buying_power_service.verify_buying_power_available,
            expected_buying_power,
            max_retries=max_retries,
            initial_wait=initial_wait,
        )

        if is_available:
            logger.info(
                f"✅ Post-settlement buying power verified: ${actual_buying_power} available "
                f"(correlation: {settlement_correlation_id})"
            )
        else:
            logger.error(
                f"❌ Post-settlement buying power verification failed: "
                f"${actual_buying_power} available, needed ${expected_buying_power} "
                f"(correlation: {settlement_correlation_id})"
            )

        return is_available, actual_buying_power

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

            except (DataProviderError, TradingClientError, OrderExecutionError) as e:
                logger.warning(
                    "Error checking order status, retrying",
                    error=str(e),
                    error_type=type(e).__name__,
                    order_id=order_id,
                    correlation_id=correlation_id,
                )
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
            # Use asyncio.to_thread to make blocking I/O async
            order = await asyncio.to_thread(
                self.alpaca_manager._trading_client.get_order_by_id, order_id
            )

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

        except (DataProviderError, TradingClientError) as e:
            logger.error(
                "Error getting order details",
                error=str(e),
                error_type=type(e).__name__,
                order_id=order_id,
            )
            return None

    def _generate_event_id(self) -> str:
        """Generate a unique event ID."""
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
        seen_orders: set[str] = set()  # Track processed orders to avoid double-counting

        while (datetime.now(UTC) - start_time).total_seconds() < self.max_wait_seconds:
            for order_id in sell_order_ids:
                # Skip if already counted
                if order_id in seen_orders:
                    continue

                settlement_details = await self._get_order_settlement_details(order_id)

                if settlement_details and settlement_details.get("side") == "SELL":
                    settled_value = settlement_details.get("settled_value", Decimal("0"))
                    accumulated_buying_power += settled_value
                    seen_orders.add(order_id)  # Mark as processed

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
