"""Business Unit: execution | Status: current.

Order monitoring and re-pegging functionality extracted from the main executor.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import TYPE_CHECKING

from the_alchemiser.execution_v2.core.smart_execution_strategy import SmartOrderResult
from the_alchemiser.execution_v2.models.execution_result import OrderResult

if TYPE_CHECKING:
    from the_alchemiser.execution_v2.core.smart_execution_strategy import SmartExecutionStrategy
    from the_alchemiser.execution_v2.core.smart_execution_strategy import ExecutionConfig

logger = logging.getLogger(__name__)


class OrderMonitor:
    """Handles order monitoring and re-pegging operations."""

    def __init__(self, smart_strategy: SmartExecutionStrategy | None, execution_config: ExecutionConfig | None) -> None:
        """Initialize the order monitor.

        Args:
            smart_strategy: Smart execution strategy instance
            execution_config: Execution configuration

        """
        self.smart_strategy = smart_strategy
        self.execution_config = execution_config

    async def monitor_and_repeg_phase_orders(
        self,
        phase_type: str,
        orders: list[OrderResult],
        correlation_id: str | None = None,
    ) -> list[OrderResult]:
        """Monitor and re-peg orders from a specific execution phase.

        Args:
            phase_type: Type of phase ("SELL" or "BUY")
            orders: List of orders from this phase to monitor
            correlation_id: Optional correlation ID for tracking

        Returns:
            Updated list of orders with any re-pegged order IDs swapped in.

        """
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
            "max_repegs": 3,
            "fill_wait_seconds": 10,
            "wait_between_checks": 1,
            "max_total_wait": 60,
        }

        try:
            if self.execution_config is not None:
                config["max_repegs"] = getattr(self.execution_config, "max_repegs_per_order", 3)
                config["fill_wait_seconds"] = int(
                    getattr(self.execution_config, "fill_wait_seconds", 10)
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
        logger.debug(
            f"{phase_type} re-peg monitoring: max_repegs={config['max_repegs']}, "
            f"fill_wait_seconds={config['fill_wait_seconds']}, max_total_wait={config['max_total_wait']}s"
        )

    async def _execute_repeg_monitoring_loop(
        self,
        phase_type: str,
        orders: list[OrderResult],
        config: dict[str, int],
        start_time: float,
        correlation_id: str | None = None,
    ) -> list[OrderResult]:
        """Execute the re-pegging monitoring loop.

        Args:
            phase_type: Type of phase being monitored
            orders: List of orders to monitor
            config: Monitoring configuration
            start_time: Start time of monitoring
            correlation_id: Optional correlation ID

        Returns:
            Updated list of orders

        """
        attempts = 0
        replacement_map: dict[str, str] = {}

        while attempts < config["max_repegs"]:
            await asyncio.sleep(config["wait_between_checks"])
            attempts += 1
            elapsed_total = time.time() - start_time

            # Early termination check
            if self._should_terminate_early(elapsed_total, config["max_total_wait"], phase_type):
                break

            try:
                if not self.smart_strategy:
                    break

                repeg_results = await self.smart_strategy.check_and_repeg_orders()

                replacement_map.update(
                    self._process_repeg_results(phase_type, repeg_results, attempts, elapsed_total)
                )

                # Wait for fills after re-pegging
                await asyncio.sleep(config["fill_wait_seconds"])

            except Exception as exc:
                logger.warning(f"⚠️ {phase_type} phase re-peg attempt {attempts} failed: {exc}")

        self._log_monitoring_completion(phase_type, attempts, time.time() - start_time)

        # Apply replacements to orders
        return self._replace_order_ids(orders, replacement_map)

    def _process_repeg_results(
        self, phase_type: str, repeg_results: list[SmartOrderResult], attempts: int, elapsed_total: float
    ) -> dict[str, str]:
        """Process re-pegging results and extract order ID replacements.

        Args:
            phase_type: Type of phase
            repeg_results: List of results from re-pegging operation
            attempts: Current attempt number
            elapsed_total: Total elapsed time

        Returns:
            Dictionary mapping old order IDs to new order IDs

        """
        replacement_map = {}

        if repeg_results:
            for repeg_result in repeg_results:
                if repeg_result.success:
                    self._log_repeg_status(phase_type, repeg_result)
                    replacement_map.update(
                        self._build_replacement_map_from_repeg_result(repeg_result)
                    )
                else:
                    self._handle_failed_repeg(phase_type, repeg_result)
        else:
            self._log_no_repeg_activity(phase_type, attempts, elapsed_total)

        return replacement_map

    def _log_no_repeg_activity(self, phase_type: str, attempts: int, elapsed_total: float) -> None:
        """Log when no re-pegging activity occurred."""
        logger.debug(
            f"🔄 {phase_type} phase re-peg check #{attempts}: no unfilled orders "
            f"(elapsed: {elapsed_total:.1f}s)"
        )

    def _should_terminate_early(
        self, elapsed_total: float, max_total_wait: int, phase_type: str
    ) -> bool:
        """Check if monitoring should terminate early.

        Args:
            elapsed_total: Total elapsed time
            max_total_wait: Maximum wait time
            phase_type: Type of phase

        Returns:
            True if should terminate early

        """
        if elapsed_total > max_total_wait:
            logger.info(
                f"⏰ {phase_type} phase: Terminating re-peg loop after {elapsed_total:.1f}s "
                f"(max: {max_total_wait}s)"
            )
            return True
        return False

    def _log_monitoring_completion(
        self, phase_type: str, attempts: int, total_elapsed: float
    ) -> None:
        """Log completion of monitoring phase.

        Args:
            phase_type: Type of phase
            attempts: Number of attempts made
            total_elapsed: Total elapsed time

        """
        logger.info(
            f"✅ {phase_type} phase re-peg monitoring complete: "
            f"{attempts} attempts in {total_elapsed:.1f}s"
        )

    def _log_repeg_status(self, phase_type: str, repeg_result: SmartOrderResult) -> None:
        """Log the status of a re-pegging operation."""
        strategy = getattr(repeg_result, "execution_strategy", "")
        order_id = getattr(repeg_result, "order_id", "")
        repegs_used = getattr(repeg_result, "repegs_used", 0)

        if "escalation" in strategy:
            logger.warning(
                f"🚨 {phase_type} ESCALATED_TO_MARKET: {order_id} (after {repegs_used} re-pegs)"
            )
        else:
            max_repegs = (
                getattr(self.execution_config, "max_repegs_per_order", 3)
                if self.execution_config
                else 3
            )
            logger.debug(f"✅ {phase_type} REPEG {repegs_used}/{max_repegs}: {order_id}")

    def _extract_order_ids(self, repeg_result: SmartOrderResult) -> tuple[str, str]:
        """Extract old and new order IDs from repeg result for logging."""
        meta = getattr(repeg_result, "metadata", None) or {}
        original_id = str(meta.get("original_order_id")) if isinstance(meta, dict) else ""
        new_id = getattr(repeg_result, "order_id", None) or ""
        return original_id, new_id

    def _handle_failed_repeg(self, phase_type: str, repeg_result: SmartOrderResult) -> None:
        """Handle failed re-pegging attempts."""
        logger.warning(f"⚠️ {phase_type} phase re-peg failed: {repeg_result.error_message}")

    def _build_replacement_map_from_repeg_result(
        self, repeg_result: SmartOrderResult
    ) -> dict[str, str]:
        """Build order ID replacement map from a single re-pegging result.

        Args:
            repeg_result: Result from re-pegging operation

        Returns:
            Dictionary mapping old order IDs to new order IDs

        """
        replacement_map = {}
        original_id, new_id = self._extract_order_ids(repeg_result)
        if original_id and new_id:
            replacement_map[original_id] = new_id
        return replacement_map

    def _replace_order_ids(
        self, orders: list[OrderResult], replacement_map: dict[str, str]
    ) -> list[OrderResult]:
        """Replace order IDs in OrderResults based on replacement map.

        Args:
            orders: List of OrderResult objects
            replacement_map: Mapping of old to new order IDs

        Returns:
            Updated list of OrderResult objects

        """
        if not replacement_map:
            return orders

        updated_orders = []
        for order in orders:
            if order.order_id and order.order_id in replacement_map:
                # Create updated order with new ID
                updated_order = OrderResult(
                    symbol=order.symbol,
                    action=order.action,
                    trade_amount=order.trade_amount,
                    shares=order.shares,
                    price=order.price,
                    order_id=replacement_map[order.order_id],
                    success=order.success,
                    error_message=order.error_message,
                    timestamp=order.timestamp,
                )
                updated_orders.append(updated_order)
            else:
                updated_orders.append(order)

        return updated_orders