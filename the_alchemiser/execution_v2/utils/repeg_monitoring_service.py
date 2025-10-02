"""Business Unit: execution | Status: current.

Additional order monitoring and repeg utilities extracted from the main executor.
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING

from the_alchemiser.execution_v2.core.smart_execution_strategy import SmartOrderResult
from the_alchemiser.execution_v2.models.execution_result import OrderResult
from the_alchemiser.shared.logging import get_logger

if TYPE_CHECKING:
    from the_alchemiser.execution_v2.core.smart_execution_strategy import SmartExecutionStrategy

logger = get_logger(__name__)


class RepegMonitoringService:
    """Handles detailed repeg monitoring loop and related utilities."""

    def __init__(self, smart_strategy: SmartExecutionStrategy | None) -> None:
        """Initialize the repeg monitoring service.

        Args:
            smart_strategy: Smart execution strategy instance

        """
        self.smart_strategy = smart_strategy

    async def execute_repeg_monitoring_loop(
        self,
        phase_type: str,
        orders: list[OrderResult],
        config: dict[str, int],
        start_time: float,
    ) -> list[OrderResult]:
        """Execute the main repeg monitoring loop.

        Args:
            phase_type: Type of phase ("SELL" or "BUY")
            orders: List of orders to monitor
            config: Configuration parameters
            start_time: Start time of monitoring

        Returns:
            Updated list of orders with any re-pegged order IDs swapped in.

        """
        attempts = 0
        last_repeg_action_time = start_time

        while (time.time() - start_time) < config["max_total_wait"]:
            elapsed_total = time.time() - start_time
            await asyncio.sleep(config["wait_between_checks"])

            last_repeg_action_time, orders = await self._check_and_process_repegs(
                phase_type, orders, attempts, elapsed_total, last_repeg_action_time
            )
            attempts += 1

            if self._should_terminate_early(last_repeg_action_time, config["fill_wait_seconds"]):
                break

        orders = await self._escalate_remaining_orders(phase_type, orders)
        self._log_monitoring_completion(phase_type, start_time)
        return orders

    async def _check_and_process_repegs(
        self,
        phase_type: str,
        orders: list[OrderResult],
        attempts: int,
        elapsed_total: float,
        last_repeg_action_time: float,
    ) -> tuple[float, list[OrderResult]]:
        """Check for and process any repeg operations.

        Args:
            phase_type: Type of phase ("SELL" or "BUY")
            orders: Current list of orders
            attempts: Current attempt number
            elapsed_total: Total elapsed time
            last_repeg_action_time: Time of last repeg action

        Returns:
            Tuple of (updated last_repeg_action_time, updated orders)

        """
        repeg_results = []
        if self.smart_strategy:
            repeg_results = await self.smart_strategy.check_and_repeg_orders()

        if repeg_results:
            last_repeg_action_time = time.time()
            orders = self._process_repeg_results(phase_type, orders, repeg_results)
        else:
            self._log_no_repeg_activity(phase_type, attempts, elapsed_total)

        return last_repeg_action_time, orders

    def _process_repeg_results(
        self,
        phase_type: str,
        orders: list[OrderResult],
        repeg_results: list[SmartOrderResult],
    ) -> list[OrderResult]:
        """Process repeg results and update orders.

        Args:
            phase_type: Type of phase ("SELL" or "BUY")
            orders: Current list of orders
            repeg_results: Results from repeg operation

        Returns:
            Updated list of orders

        """
        # Build replacement map from repeg results
        replacement_map = self._build_replacement_map_from_repeg_results(phase_type, repeg_results)

        # Apply replacements to orders
        return self._replace_order_ids(orders, replacement_map)

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
        time_since_last_action = time.time() - last_repeg_action_time

        # If smart strategy is not available, use the old logic
        if self.smart_strategy is None:
            return self._check_termination_without_strategy(
                time_since_last_action, fill_wait_seconds
            )

        active_order_count = self.smart_strategy.get_active_order_count()

        # If no active orders, use a short grace window instead of full 2x wait
        if active_order_count == 0:
            return self._check_termination_no_active_orders(time_since_last_action)

        # Active orders present, use extended window
        return self._check_termination_with_active_orders(
            time_since_last_action, fill_wait_seconds, active_order_count
        )

    def _check_termination_without_strategy(
        self, time_since_last_action: float, fill_wait_seconds: int
    ) -> bool:
        """Check termination when smart strategy is not available.

        Args:
            time_since_last_action: Time since last repeg action
            fill_wait_seconds: Fill wait time configuration

        Returns:
            True if should terminate early.

        """
        return time_since_last_action > fill_wait_seconds * 2

    def _check_termination_no_active_orders(self, time_since_last_action: float) -> bool:
        """Check termination when no active orders exist.

        Args:
            time_since_last_action: Time since last repeg action

        Returns:
            True if should terminate early.

        """
        grace_window_seconds = 5  # Short grace period for zero active orders
        terminate_early = time_since_last_action > grace_window_seconds
        if terminate_early:
            logger.debug(
                f"🔄 Early termination: No active orders for {time_since_last_action:.1f}s "
                f"(grace window: {grace_window_seconds}s)"
            )
        return terminate_early

    def _check_termination_with_active_orders(
        self, time_since_last_action: float, fill_wait_seconds: int, active_order_count: int
    ) -> bool:
        """Check termination when active orders exist.

        Args:
            time_since_last_action: Time since last repeg action
            fill_wait_seconds: Fill wait time configuration
            active_order_count: Number of active orders

        Returns:
            True if should terminate early.

        """
        extended_wait = fill_wait_seconds * 2
        terminate_early = time_since_last_action > extended_wait
        if terminate_early:
            logger.debug(
                f"🔄 Terminating: {active_order_count} active orders, "
                f"but {time_since_last_action:.1f}s since last re-peg action (max: {extended_wait}s)"
            )
        return terminate_early

    def _log_monitoring_completion(
        self,
        phase_type: str,
        start_time: float,
    ) -> None:
        """Log completion of the monitoring loop."""
        total_time = time.time() - start_time
        logger.info(f"✅ {phase_type} phase re-peg monitoring complete: {total_time:.1f}s total")

    async def _escalate_remaining_orders(
        self, phase_type: str, orders: list[OrderResult]
    ) -> list[OrderResult]:
        """Escalate any remaining active orders to market.

        Args:
            phase_type: Type of phase ("SELL" or "BUY")
            orders: Current list of orders

        Returns:
            Updated list of orders with escalated order IDs

        """
        try:
            if self.smart_strategy:
                orders = await self._escalate_orders_to_market(phase_type, orders)
        except Exception:
            logger.exception("Error during final escalation to market in repeg monitoring loop")

        return orders

    async def _escalate_orders_to_market(
        self, phase_type: str, orders: list[OrderResult]
    ) -> list[OrderResult]:
        """Execute market escalation for active orders.

        Args:
            phase_type: Type of phase ("SELL" or "BUY")
            orders: Current list of orders

        Returns:
            Updated list of orders with escalated order IDs

        """
        # Type guard: smart_strategy must exist at this point
        if self.smart_strategy is None:
            return orders
        active = self.smart_strategy.order_tracker.get_active_orders()
        if not active:
            return orders

        logger.warning(
            f"🚨 {phase_type} phase: Monitoring window ended with active orders; escalating remaining to market"
        )

        # Escalate all active orders to market
        tasks = [
            self.smart_strategy.repeg_manager._escalate_to_market(oid, req)
            for oid, req in active.items()
        ]
        gather_results = await asyncio.gather(*tasks, return_exceptions=True)
        # Filter and process successful escalations
        results = self._filter_successful_escalations(gather_results, list(active.keys()))
        if results:
            orders = self._process_repeg_results(phase_type, orders, results)

        return orders

    def _filter_successful_escalations(
        self, gather_results: list[SmartOrderResult | BaseException], order_ids: list[str]
    ) -> list[SmartOrderResult]:
        """Filter successful escalations from gather results.

        Args:
            gather_results: Results from asyncio.gather with return_exceptions=True
            order_ids: List of order IDs for error logging

        Returns:
            List of successful SmartOrderResult objects

        """
        results: list[SmartOrderResult] = []
        
        for idx, result in enumerate(gather_results):
            if isinstance(result, BaseException):
                order_id = order_ids[idx]
                logger.error(f"Error escalating order {order_id}: {result}")
                continue
            if result is not None:
                results.append(result)

        return results

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
            max_repegs = 3  # Default fallback
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
        if not replacement_map:
            return orders

        updated = []
        for o in orders:
            if o.order_id and o.order_id in replacement_map:
                new_o = o.model_copy(update={"order_id": replacement_map[o.order_id]})
                updated.append(new_o)
            else:
                updated.append(o)
        return updated
