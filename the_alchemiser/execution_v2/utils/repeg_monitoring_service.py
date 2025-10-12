"""Business Unit: execution | Status: current.

Additional order monitoring and repeg utilities extracted from the main executor.
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Literal

from the_alchemiser.execution_v2.core.smart_execution_strategy import SmartOrderResult
from the_alchemiser.execution_v2.models.execution_result import OrderResult
from the_alchemiser.shared.errors.exceptions import AlchemiserError
from the_alchemiser.shared.logging import get_logger

if TYPE_CHECKING:
    from the_alchemiser.execution_v2.core.smart_execution_strategy import SmartExecutionStrategy

logger = get_logger(__name__)


# Constants
GRACE_WINDOW_SECONDS = 5  # Grace period for zero active orders
EXTENDED_WAIT_MULTIPLIER = 2  # Multiplier for fill_wait_seconds
DEFAULT_MAX_REPEGS = 3  # Default max repegs for logging


class RepegMonitoringError(AlchemiserError):
    """Raised when repeg monitoring operations fail."""

    def __init__(
        self,
        message: str,
        phase_type: str | None = None,
        order_count: int | None = None,
        correlation_id: str | None = None,
    ) -> None:
        """Create a repeg monitoring error with context.

        Args:
            message: Error description
            phase_type: Trading phase ("SELL" or "BUY")
            order_count: Number of orders being monitored
            correlation_id: Correlation ID for tracing

        """
        context = {}
        if phase_type:
            context["phase_type"] = phase_type
        if order_count is not None:
            context["order_count"] = order_count
        if correlation_id:
            context["correlation_id"] = correlation_id
        super().__init__(message, context)
        self.phase_type = phase_type
        self.order_count = order_count
        self.correlation_id = correlation_id


class RepegMonitoringService:
    """Handles detailed repeg monitoring loop and related utilities.

    This service manages the async monitoring loop for order repeg operations
    during trade execution phases. It periodically checks for orders that need
    re-pegging (price adjustment) and coordinates with the SmartExecutionStrategy
    to execute those repegs.

    The service is idempotent and safe for replay - the same order IDs are
    consistently updated and no duplicate work is performed. All operations
    delegate actual I/O to the smart_strategy instance.

    Threading: This service uses async/await and should be run in an async context.
    It does not use threading internally but coordinates with async operations.
    """

    def __init__(self, smart_strategy: SmartExecutionStrategy | None) -> None:
        """Initialize the repeg monitoring service.

        Args:
            smart_strategy: Smart execution strategy instance that handles
                           actual repeg operations. Can be None for testing
                           or when repeg functionality is disabled.

        """
        self.smart_strategy = smart_strategy
        logger.debug(
            "RepegMonitoringService initialized",
            extra={"has_strategy": smart_strategy is not None},
        )

    async def execute_repeg_monitoring_loop(
        self,
        phase_type: Literal["SELL", "BUY"],
        orders: list[OrderResult],
        config: dict[str, int | float],
        start_time: float,
        correlation_id: str = "",
    ) -> list[OrderResult]:
        """Execute the main repeg monitoring loop.

        This method runs the monitoring loop that periodically checks for orders
        needing re-pegging and coordinates their execution. It continues until
        the max_total_wait timeout is reached or early termination conditions
        are met (no active orders for grace period).

        Args:
            phase_type: Type of phase - must be "SELL" or "BUY"
            orders: List of orders to monitor
            config: Configuration parameters with keys:
                   - max_total_wait: Maximum total wait time in seconds
                   - wait_between_checks: Wait time between repeg checks in seconds
                   - fill_wait_seconds: Base wait time for fill operations
            start_time: Start time of monitoring (from time.time())
            correlation_id: Correlation ID for tracing this monitoring session

        Returns:
            Updated list of orders with any re-pegged order IDs swapped in.

        Raises:
            RepegMonitoringError: If config validation fails or critical errors occur

        """
        # Validate inputs
        if phase_type not in ("SELL", "BUY"):
            raise RepegMonitoringError(
                f"Invalid phase_type: {phase_type}. Must be 'SELL' or 'BUY'",
                phase_type=phase_type,
                correlation_id=correlation_id,
            )

        required_keys = {"max_total_wait", "wait_between_checks", "fill_wait_seconds"}
        missing_keys = required_keys - set(config.keys())
        if missing_keys:
            raise RepegMonitoringError(
                f"Missing required config keys: {missing_keys}",
                phase_type=phase_type,
                correlation_id=correlation_id,
            )

        logger.info(
            f"Starting {phase_type} repeg monitoring loop",
            extra={
                "phase_type": phase_type,
                "order_count": len(orders),
                "correlation_id": correlation_id,
            },
        )

        attempts = 0
        last_repeg_action_time = start_time

        while (time.time() - start_time) < config["max_total_wait"]:
            elapsed_total = time.time() - start_time
            await asyncio.sleep(config["wait_between_checks"])

            last_repeg_action_time, orders = await self._check_and_process_repegs(
                phase_type, orders, attempts, elapsed_total, last_repeg_action_time, correlation_id
            )
            attempts += 1

            if self._should_terminate_early(
                last_repeg_action_time, int(config["fill_wait_seconds"]), correlation_id
            ):
                break

        orders = await self._escalate_remaining_orders(phase_type, orders, correlation_id)
        self._log_monitoring_completion(phase_type, start_time, correlation_id)
        return orders

    async def _check_and_process_repegs(
        self,
        phase_type: str,
        orders: list[OrderResult],
        attempts: int,
        elapsed_total: float,
        last_repeg_action_time: float,
        correlation_id: str = "",
    ) -> tuple[float, list[OrderResult]]:
        """Check for and process any repeg operations.

        Args:
            phase_type: Type of phase ("SELL" or "BUY")
            orders: Current list of orders
            attempts: Current attempt number
            elapsed_total: Total elapsed time
            last_repeg_action_time: Time of last repeg action
            correlation_id: Correlation ID for tracing

        Returns:
            Tuple of (updated last_repeg_action_time, updated orders)

        Raises:
            RepegMonitoringError: If repeg check fails critically

        """
        repeg_results = []
        if self.smart_strategy:
            try:
                repeg_results = await self.smart_strategy.check_and_repeg_orders()
            except Exception as exc:
                logger.error(
                    f"Failed to check and repeg orders: {exc}",
                    extra={
                        "phase_type": phase_type,
                        "attempts": attempts,
                        "correlation_id": correlation_id,
                    },
                )
                # Don't raise - continue monitoring even if one check fails
                repeg_results = []

        if repeg_results:
            last_repeg_action_time = time.time()
            orders = self._process_repeg_results(phase_type, orders, repeg_results, correlation_id)
        else:
            self._log_no_repeg_activity(phase_type, attempts, elapsed_total, correlation_id)

        return last_repeg_action_time, orders

    def _process_repeg_results(
        self,
        phase_type: str,
        orders: list[OrderResult],
        repeg_results: list[SmartOrderResult],
        correlation_id: str = "",
    ) -> list[OrderResult]:
        """Process repeg results and update orders.

        Args:
            phase_type: Type of phase ("SELL" or "BUY")
            orders: Current list of orders
            repeg_results: Results from repeg operation
            correlation_id: Correlation ID for tracing

        Returns:
            Updated list of orders

        """
        # Build replacement map from repeg results
        replacement_map = self._build_replacement_map_from_repeg_results(
            phase_type, repeg_results, correlation_id
        )

        # Apply replacements to orders
        return self._replace_order_ids(orders, replacement_map)

    def _log_no_repeg_activity(
        self, phase_type: str, attempts: int, elapsed_total: float, correlation_id: str = ""
    ) -> None:
        """Log when no repeg activity occurred."""
        active_orders = 0
        if self.smart_strategy:
            active_orders = self.smart_strategy.get_active_order_count()
        logger.debug(
            f"📊 {phase_type} phase: No re-pegging needed "
            f"(attempt {attempts + 1}, {elapsed_total:.1f}s elapsed, {active_orders} active orders)",
            extra={
                "phase_type": phase_type,
                "attempts": attempts + 1,
                "elapsed_seconds": elapsed_total,
                "active_orders": active_orders,
                "correlation_id": correlation_id,
            },
        )

    def _should_terminate_early(
        self, last_repeg_action_time: float, fill_wait_seconds: int, correlation_id: str = ""
    ) -> bool:
        """Check if monitoring should terminate early.

        Args:
            last_repeg_action_time: Time of last repeg action
            fill_wait_seconds: Fill wait time configuration
            correlation_id: Correlation ID for tracing

        Returns:
            True if monitoring should terminate early.

        """
        time_since_last_action = time.time() - last_repeg_action_time

        # If smart strategy is not available, use the old logic
        if self.smart_strategy is None:
            return self._check_termination_without_strategy(
                time_since_last_action, fill_wait_seconds, correlation_id
            )

        active_order_count = self.smart_strategy.get_active_order_count()

        # If no active orders, use a short grace window instead of full 2x wait
        if active_order_count == 0:
            return self._check_termination_no_active_orders(
                time_since_last_action, correlation_id
            )

        # Active orders present, use extended window
        return self._check_termination_with_active_orders(
            time_since_last_action, fill_wait_seconds, active_order_count, correlation_id
        )

    def _check_termination_without_strategy(
        self, time_since_last_action: float, fill_wait_seconds: int, correlation_id: str = ""
    ) -> bool:
        """Check termination when smart strategy is not available.

        Args:
            time_since_last_action: Time since last repeg action
            fill_wait_seconds: Fill wait time configuration
            correlation_id: Correlation ID for tracing

        Returns:
            True if should terminate early.

        """
        return time_since_last_action > fill_wait_seconds * EXTENDED_WAIT_MULTIPLIER

    def _check_termination_no_active_orders(
        self, time_since_last_action: float, correlation_id: str = ""
    ) -> bool:
        """Check termination when no active orders exist.

        Args:
            time_since_last_action: Time since last repeg action
            correlation_id: Correlation ID for tracing

        Returns:
            True if should terminate early.

        """
        terminate_early = time_since_last_action > GRACE_WINDOW_SECONDS
        if terminate_early:
            logger.debug(
                f"🔄 Early termination: No active orders for {time_since_last_action:.1f}s "
                f"(grace window: {GRACE_WINDOW_SECONDS}s)",
                extra={
                    "time_since_last_action": time_since_last_action,
                    "grace_window": GRACE_WINDOW_SECONDS,
                    "correlation_id": correlation_id,
                },
            )
        return terminate_early

    def _check_termination_with_active_orders(
        self,
        time_since_last_action: float,
        fill_wait_seconds: int,
        active_order_count: int,
        correlation_id: str = "",
    ) -> bool:
        """Check termination when active orders exist.

        Args:
            time_since_last_action: Time since last repeg action
            fill_wait_seconds: Fill wait time configuration
            active_order_count: Number of active orders
            correlation_id: Correlation ID for tracing

        Returns:
            True if should terminate early.

        """
        extended_wait = fill_wait_seconds * EXTENDED_WAIT_MULTIPLIER
        terminate_early = time_since_last_action > extended_wait
        if terminate_early:
            logger.debug(
                f"🔄 Terminating: {active_order_count} active orders, "
                f"but {time_since_last_action:.1f}s since last re-peg action (max: {extended_wait}s)",
                extra={
                    "active_order_count": active_order_count,
                    "time_since_last_action": time_since_last_action,
                    "extended_wait": extended_wait,
                    "correlation_id": correlation_id,
                },
            )
        return terminate_early

    def _log_monitoring_completion(
        self,
        phase_type: str,
        start_time: float,
        correlation_id: str = "",
    ) -> None:
        """Log completion of the monitoring loop."""
        total_time = time.time() - start_time
        logger.info(
            f"✅ {phase_type} phase re-peg monitoring complete: {total_time:.1f}s total",
            extra={
                "phase_type": phase_type,
                "total_time_seconds": total_time,
                "correlation_id": correlation_id,
            },
        )

    async def _escalate_remaining_orders(
        self, phase_type: str, orders: list[OrderResult], correlation_id: str = ""
    ) -> list[OrderResult]:
        """Escalate any remaining active orders to market.

        Args:
            phase_type: Type of phase ("SELL" or "BUY")
            orders: Current list of orders
            correlation_id: Correlation ID for tracing

        Returns:
            Updated list of orders with escalated order IDs

        Raises:
            RepegMonitoringError: If escalation fails critically

        """
        try:
            if self.smart_strategy:
                orders = await self._escalate_orders_to_market(phase_type, orders, correlation_id)
        except Exception as exc:
            logger.exception(
                f"Error during final escalation to market in repeg monitoring loop: {exc}",
                extra={
                    "phase_type": phase_type,
                    "order_count": len(orders),
                    "correlation_id": correlation_id,
                },
            )
            # Don't raise - return orders as-is if escalation fails
            # This allows the workflow to continue with partially completed orders

        return orders

    async def _escalate_orders_to_market(
        self, phase_type: str, orders: list[OrderResult], correlation_id: str = ""
    ) -> list[OrderResult]:
        """Execute market escalation for active orders.

        Args:
            phase_type: Type of phase ("SELL" or "BUY")
            orders: Current list of orders
            correlation_id: Correlation ID for tracing

        Returns:
            Updated list of orders with escalated order IDs

        Raises:
            RepegMonitoringError: If smart_strategy is invalid or escalation fails

        """
        # Type guard: smart_strategy must exist at this point
        if self.smart_strategy is None:
            return orders

        # Safe access to order_tracker with validation
        if not hasattr(self.smart_strategy, "order_tracker"):
            logger.warning(
                "Smart strategy missing order_tracker attribute",
                extra={"phase_type": phase_type, "correlation_id": correlation_id},
            )
            return orders

        active = self.smart_strategy.order_tracker.get_active_orders()
        if not active:
            return orders

        logger.warning(
            f"🚨 {phase_type} phase: Monitoring window ended with active orders; escalating remaining to market",
            extra={
                "phase_type": phase_type,
                "active_order_count": len(active),
                "correlation_id": correlation_id,
            },
        )

        # Safe access to repeg_manager with validation
        if not hasattr(self.smart_strategy, "repeg_manager"):
            logger.error(
                "Smart strategy missing repeg_manager attribute",
                extra={"phase_type": phase_type, "correlation_id": correlation_id},
            )
            raise RepegMonitoringError(
                "Smart strategy missing repeg_manager - cannot escalate orders",
                phase_type=phase_type,
                order_count=len(active),
                correlation_id=correlation_id,
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
            orders = self._process_repeg_results(phase_type, orders, results, correlation_id)

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
                order_id = order_ids[idx] if idx < len(order_ids) else "unknown"
                logger.error(
                    f"Error escalating order {order_id}: {result}",
                    extra={"order_id": order_id, "error": str(result)},
                )
                continue
            if result is not None:
                results.append(result)

        return results

    def _log_repeg_status(
        self, phase_type: str, repeg_result: SmartOrderResult, correlation_id: str = ""
    ) -> None:
        """Log repeg status with appropriate message for escalation or standard repeg.

        Args:
            phase_type: Type of phase ("SELL" or "BUY")
            repeg_result: Result from repeg operation
            correlation_id: Correlation ID for tracing

        """
        strategy = getattr(repeg_result, "execution_strategy", "")
        order_id = getattr(repeg_result, "order_id", "")
        repegs_used = getattr(repeg_result, "repegs_used", 0)
        symbol = getattr(repeg_result, "symbol", "")

        if "escalation" in strategy:
            logger.warning(
                f"🚨 {phase_type} ESCALATED_TO_MARKET: {symbol} {order_id} (after {repegs_used} re-pegs)",
                extra={
                    "phase_type": phase_type,
                    "symbol": symbol,
                    "order_id": order_id,
                    "repegs_used": repegs_used,
                    "execution_strategy": strategy,
                    "correlation_id": correlation_id,
                },
            )
        else:
            # Use configured max repegs if available for accurate logging
            logger.debug(
                f"✅ {phase_type} REPEG {repegs_used}/{DEFAULT_MAX_REPEGS}: {symbol} {order_id}",
                extra={
                    "phase_type": phase_type,
                    "symbol": symbol,
                    "order_id": order_id,
                    "repegs_used": repegs_used,
                    "max_repegs": DEFAULT_MAX_REPEGS,
                    "correlation_id": correlation_id,
                },
            )

    def _extract_order_ids(self, repeg_result: SmartOrderResult) -> tuple[str, str]:
        """Extract original and new order IDs from repeg result.

        Args:
            repeg_result: Result from repeg operation

        Returns:
            Tuple of (original_id, new_id). Both will be empty strings if not found.

        """
        meta = getattr(repeg_result, "metadata", None) or {}
        original_id = str(meta.get("original_order_id")) if isinstance(meta, dict) else ""
        new_id = getattr(repeg_result, "order_id", None) or ""
        return original_id, new_id

    def _handle_failed_repeg(
        self, phase_type: str, repeg_result: SmartOrderResult, correlation_id: str = ""
    ) -> None:
        """Handle logging for failed repeg results.

        Args:
            phase_type: Type of phase ("SELL" or "BUY")
            repeg_result: Failed repeg result
            correlation_id: Correlation ID for tracing

        """
        error_message = getattr(repeg_result, "error_message", "")
        order_id = getattr(repeg_result, "order_id", "")
        symbol = getattr(repeg_result, "symbol", "")
        logger.warning(
            f"⚠️ {phase_type} re-peg failed: {error_message}",
            extra={
                "phase_type": phase_type,
                "error_message": error_message,
                "order_id": order_id,
                "symbol": symbol,
                "correlation_id": correlation_id,
            },
        )

    def _build_replacement_map_from_repeg_results(
        self, phase_type: str, repeg_results: list[SmartOrderResult], correlation_id: str = ""
    ) -> dict[str, str]:
        """Build mapping from original to new order IDs for successful re-pegs.

        Args:
            phase_type: Type of phase ("SELL" or "BUY")
            repeg_results: List of repeg results to process
            correlation_id: Correlation ID for tracing

        Returns:
            Dictionary mapping original order IDs to new order IDs

        """
        replacement_map: dict[str, str] = {}

        for repeg_result in repeg_results:
            try:
                if not getattr(repeg_result, "success", False):
                    self._handle_failed_repeg(phase_type, repeg_result, correlation_id)
                    continue

                self._log_repeg_status(phase_type, repeg_result, correlation_id)
                original_id, new_id = self._extract_order_ids(repeg_result)

                if original_id and new_id:
                    replacement_map[original_id] = new_id

            except (AttributeError, TypeError, KeyError) as exc:
                logger.warning(
                    f"Failed to process re-peg result for replacement mapping: {exc}",
                    extra={
                        "phase_type": phase_type,
                        "error": str(exc),
                        "error_type": type(exc).__name__,
                        "correlation_id": correlation_id,
                    },
                )

        return replacement_map

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
