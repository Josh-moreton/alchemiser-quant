"""Business Unit: execution | Status: current.

Order monitoring and re-pegging functionality extracted from the main executor.
"""

from __future__ import annotations

import asyncio
import time
from decimal import Decimal
from typing import TYPE_CHECKING

from the_alchemiser.execution_v2.core.smart_execution_strategy import (
    SmartOrderRequest,
    SmartOrderResult,
)
from the_alchemiser.execution_v2.models.execution_result import OrderResult
from the_alchemiser.shared.logging import get_logger

if TYPE_CHECKING:
    from the_alchemiser.execution_v2.core.smart_execution_strategy import (
        ExecutionConfig,
        SmartExecutionStrategy,
    )

logger = get_logger(__name__)


class OrderMonitor:
    """Handles order monitoring and re-pegging operations."""

    def __init__(
        self,
        smart_strategy: SmartExecutionStrategy | None,
        execution_config: ExecutionConfig | None,
    ) -> None:
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
        log_prefix = f"[{correlation_id}]" if correlation_id else ""

        if not self.smart_strategy:
            logger.info(
                f"{log_prefix} 📊 {phase_type} phase: Smart strategy disabled; skipping re-peg loop"
            )
            return orders

        config = self._get_repeg_monitoring_config()
        self._log_monitoring_config(phase_type, config, correlation_id)

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

    def _log_monitoring_config(
        self, phase_type: str, config: dict[str, int], correlation_id: str | None = None
    ) -> None:
        """Log the monitoring configuration parameters."""
        log_prefix = f"[{correlation_id}]" if correlation_id else ""
        logger.debug(
            f"{log_prefix} {phase_type} re-peg monitoring: max_repegs={config['max_repegs']}, "
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
            correlation_id: Optional correlation ID for tracking

        Returns:
            Updated list of orders

        """
        log_prefix = f"[{correlation_id}]" if correlation_id else ""
        attempts = 0
        replacement_map: dict[str, str] = {}

        while attempts < config["max_repegs"]:
            await asyncio.sleep(config["wait_between_checks"])
            attempts += 1
            elapsed_total = time.time() - start_time

            # Early termination check
            if self._should_terminate_early(
                elapsed_total, config["max_total_wait"], phase_type, correlation_id
            ):
                break

            try:
                if not self.smart_strategy:
                    break

                repeg_results = await self.smart_strategy.check_and_repeg_orders()

                replacement_map.update(
                    self._process_repeg_results(
                        phase_type, repeg_results, attempts, elapsed_total, correlation_id
                    )
                )

                # Wait for fills after re-pegging
                await asyncio.sleep(config["fill_wait_seconds"])

            except Exception as exc:
                logger.warning(
                    f"{log_prefix} ⚠️ {phase_type} phase re-peg attempt {attempts} failed: {exc}"
                )

        self._log_monitoring_completion(
            phase_type, attempts, time.time() - start_time, correlation_id
        )

        # Apply replacements to orders
        updated_orders = self._replace_order_ids(orders, replacement_map)

        # Final safeguard: escalate any remaining unfilled orders to market
        # Pass the orders list so we can check for cancelled/expired orders with unfilled quantities
        replacement_after_escalation = await self._final_escalation_if_active_orders(
            phase_type, correlation_id, orders=updated_orders
        )
        if replacement_after_escalation:
            updated_orders = self._replace_order_ids(updated_orders, replacement_after_escalation)

        return updated_orders

    async def _final_escalation_if_active_orders(
        self, phase_type: str, correlation_id: str | None = None, orders: list[OrderResult] | None = None
    ) -> dict[str, str]:
        """Escalate any remaining unfilled orders to market and return replacement map.

        This prevents scenarios where orders remain unfilled after monitoring exhausts.
        Checks both active orders in tracking AND verifies actual broker order status
        to catch any orders that were cancelled/expired but still have unfilled quantity.

        Args:
            phase_type: Type of phase being monitored
            correlation_id: Optional correlation ID for tracking
            orders: Original orders list to check for unfilled quantities

        Returns:
            Mapping from original order IDs to new market order IDs.

        """
        log_prefix = f"[{correlation_id}]" if correlation_id else ""

        try:
            if not self.smart_strategy:
                return {}

            # First check: active orders still in tracking
            active = self.smart_strategy.order_tracker.get_active_orders()
            
            # Second check: verify broker status for all placed orders to catch cancelled/expired orders
            orders_to_escalate: dict[str, tuple[SmartOrderRequest, str]] = {}  # order_id -> (request, reason)
            
            if active:
                logger.warning(
                    f"{log_prefix} 🚨 {phase_type} phase: {len(active)} active orders in tracking; "
                    "checking for escalation"
                )
                for order_id, request in active.items():
                    orders_to_escalate[order_id] = (request, "active_unfilled")
            
            # CRITICAL: Also check orders that may have been removed from tracking
            # but still need market fallback (e.g., cancelled/expired with unfilled qty)
            if orders:
                self._check_cancelled_orders_for_escalation(
                    orders, active, orders_to_escalate, log_prefix, correlation_id
                )

            if not orders_to_escalate:
                logger.debug(f"{log_prefix} {phase_type} phase: No orders need market escalation")
                return {}
            
            logger.warning(
                f"{log_prefix} 🚨 {phase_type} phase: Escalating {len(orders_to_escalate)} orders to market"
            )

            tasks = [
                self.smart_strategy.repeg_manager._escalate_to_market(oid, req)
                for oid, (req, _) in orders_to_escalate.items()
            ]
            results = [r for r in await asyncio.gather(*tasks) if r]

            replacement_map: dict[str, str] = {}
            for r in results:
                meta = getattr(r, "metadata", None) or {}
                original_id = str(meta.get("original_order_id")) if isinstance(meta, dict) else ""
                new_id = getattr(r, "order_id", None) or ""
                if getattr(r, "success", False) and original_id and new_id:
                    replacement_map[original_id] = new_id
                    logger.info(
                        f"{log_prefix} ✅ Market escalation successful: {original_id} -> {new_id}"
                    )

            return replacement_map
        except Exception as exc:
            logger.exception(
                f"{log_prefix} Error during final escalation to market in {phase_type} repeg monitoring: {exc}"
            )
            return {}

    def _check_cancelled_orders_for_escalation(
        self,
        orders: list[OrderResult],
        active: dict[str, SmartOrderRequest],
        orders_to_escalate: dict[str, tuple[SmartOrderRequest, str]],
        log_prefix: str,
        correlation_id: str | None,
    ) -> None:
        """Check cancelled/expired orders for unfilled quantities that need escalation.

        Args:
            orders: List of placed orders to check
            active: Dictionary of currently active orders
            orders_to_escalate: Dictionary to populate with orders needing escalation
            log_prefix: Logging prefix for correlation
            correlation_id: Optional correlation ID

        """
        if not self.smart_strategy:
            return

        for order in orders:
            if not order.order_id or not order.success:
                continue
            
            # Skip if order is still in active tracking (already handled)
            if order.order_id in active:
                continue
            
            order_status = self.smart_strategy.alpaca_manager._check_order_completion_status(order.order_id)
            # Check if order was cancelled/expired/rejected but with potential unfilled quantity
            # Status list mirrors the centralized check in utils.is_order_completed
            if not order_status or order_status not in ["CANCELED", "EXPIRED", "REJECTED"]:
                continue
            
            # Order was cancelled/expired - check if it has unfilled quantity
            try:
                order_result = self.smart_strategy.alpaca_manager.get_order_execution_result(order.order_id)
                filled_qty_raw = getattr(order_result, "filled_qty", 0) or 0
                filled_qty = Decimal(str(filled_qty_raw))
                
                # Use Decimal comparison to avoid float precision issues
                if filled_qty < order.shares:
                    # Has unfilled quantity - need to place market order
                    remaining_qty = order.shares - filled_qty
                    logger.warning(
                        f"{log_prefix} 🚨 Order {order.order_id} was {order_status} with "
                        f"{remaining_qty} unfilled ({order.symbol} {order.action}); escalating to market"
                    )
                    # Create request for the remaining quantity
                    request = SmartOrderRequest(
                        symbol=order.symbol,
                        side=order.action,
                        quantity=remaining_qty,
                        correlation_id=correlation_id or "",
                    )
                    orders_to_escalate[order.order_id] = (request, f"{order_status.lower()}_unfilled")
            except (AttributeError, ValueError, TypeError) as e:
                logger.debug(f"Could not check order {order.order_id}: {e}")
            except Exception as e:
                logger.warning(f"Unexpected error checking order {order.order_id}: {e}", exc_info=True)

    def _process_repeg_results(
        self,
        phase_type: str,
        repeg_results: list[SmartOrderResult],
        attempts: int,
        elapsed_total: float,
        correlation_id: str | None = None,
    ) -> dict[str, str]:
        """Process re-pegging results and extract order ID replacements.

        Args:
            phase_type: Type of phase
            repeg_results: List of results from re-pegging operation
            attempts: Current attempt number
            elapsed_total: Total elapsed time
            correlation_id: Optional correlation ID for tracking

        Returns:
            Dictionary mapping old order IDs to new order IDs

        """
        replacement_map = {}

        if repeg_results:
            for repeg_result in repeg_results:
                if repeg_result.success:
                    self._log_repeg_status(phase_type, repeg_result, correlation_id)
                    replacement_map.update(
                        self._build_replacement_map_from_repeg_result(repeg_result)
                    )
                else:
                    self._handle_failed_repeg(phase_type, repeg_result, correlation_id)
        else:
            self._log_no_repeg_activity(phase_type, attempts, elapsed_total, correlation_id)

        return replacement_map

    def _log_no_repeg_activity(
        self,
        phase_type: str,
        attempts: int,
        elapsed_total: float,
        correlation_id: str | None = None,
    ) -> None:
        """Log when no re-pegging activity occurred."""
        log_prefix = f"[{correlation_id}]" if correlation_id else ""
        logger.debug(
            f"{log_prefix} 🔄 {phase_type} phase re-peg check #{attempts}: no unfilled orders "
            f"(elapsed: {elapsed_total:.1f}s)"
        )

    def _should_terminate_early(
        self,
        elapsed_total: float,
        max_total_wait: int,
        phase_type: str,
        correlation_id: str | None = None,
    ) -> bool:
        """Check if monitoring should terminate early.

        Args:
            elapsed_total: Total elapsed time
            max_total_wait: Maximum wait time
            phase_type: Type of phase
            correlation_id: Optional correlation ID for tracking

        Returns:
            True if should terminate early

        """
        log_prefix = f"[{correlation_id}]" if correlation_id else ""
        if elapsed_total > max_total_wait:
            logger.info(
                f"{log_prefix} ⏰ {phase_type} phase: Terminating re-peg loop after {elapsed_total:.1f}s "
                f"(max: {max_total_wait}s)"
            )
            return True
        return False

    def _log_monitoring_completion(
        self,
        phase_type: str,
        attempts: int,
        total_elapsed: float,
        correlation_id: str | None = None,
    ) -> None:
        """Log completion of monitoring phase.

        Args:
            phase_type: Type of phase
            attempts: Number of attempts made
            total_elapsed: Total elapsed time
            correlation_id: Optional correlation ID for tracking

        """
        log_prefix = f"[{correlation_id}]" if correlation_id else ""
        logger.info(
            f"{log_prefix} ✅ {phase_type} phase re-peg monitoring complete: "
            f"{attempts} attempts in {total_elapsed:.1f}s"
        )

    def _log_repeg_status(
        self, phase_type: str, repeg_result: SmartOrderResult, correlation_id: str | None = None
    ) -> None:
        """Log the status of a re-pegging operation."""
        log_prefix = f"[{correlation_id}]" if correlation_id else ""
        strategy = getattr(repeg_result, "execution_strategy", "")
        order_id = getattr(repeg_result, "order_id", "")
        repegs_used = getattr(repeg_result, "repegs_used", 0)

        if "escalation" in strategy:
            logger.warning(
                f"{log_prefix} 🚨 {phase_type} ESCALATED_TO_MARKET: {order_id} (after {repegs_used} re-pegs)"
            )
        else:
            max_repegs = (
                getattr(self.execution_config, "max_repegs_per_order", 3)
                if self.execution_config
                else 3
            )
            logger.debug(
                f"{log_prefix} ✅ {phase_type} REPEG {repegs_used}/{max_repegs}: {order_id}"
            )

    def _extract_order_ids(self, repeg_result: SmartOrderResult) -> tuple[str, str]:
        """Extract old and new order IDs from repeg result for logging."""
        meta = getattr(repeg_result, "metadata", None) or {}
        original_id = str(meta.get("original_order_id")) if isinstance(meta, dict) else ""
        new_id = getattr(repeg_result, "order_id", None) or ""
        return original_id, new_id

    def _handle_failed_repeg(
        self, phase_type: str, repeg_result: SmartOrderResult, correlation_id: str | None = None
    ) -> None:
        """Handle failed re-pegging attempts."""
        log_prefix = f"[{correlation_id}]" if correlation_id else ""
        logger.warning(
            f"{log_prefix} ⚠️ {phase_type} phase re-peg failed: {repeg_result.error_message}"
        )

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
