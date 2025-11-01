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
from the_alchemiser.shared.errors.exceptions import OrderExecutionError
from the_alchemiser.shared.errors.trading_errors import OrderError
from the_alchemiser.shared.logging import get_logger

if TYPE_CHECKING:
    from the_alchemiser.execution_v2.core.smart_execution_strategy import (
        ExecutionConfig,
        SmartExecutionStrategy,
    )

logger = get_logger(__name__)

# Default monitoring configuration constants
DEFAULT_MAX_REPEGS = 3
DEFAULT_FILL_WAIT_SECONDS = 10
DEFAULT_WAIT_BETWEEN_CHECKS = 1
DEFAULT_MAX_TOTAL_WAIT_SECONDS = 60
DEFAULT_PLACEMENT_TIMEOUT_SECONDS = 30
SAFETY_MARGIN_SECONDS = 30
MIN_TOTAL_WAIT_SECONDS = 60
MAX_TOTAL_WAIT_SECONDS = 600  # 10 minutes
CHECK_FREQUENCY_DIVISOR = 5  # Check 5x per fill_wait period
MAX_WAIT_BETWEEN_CHECKS = 5


class OrderMonitor:
    """Handles order monitoring and re-pegging operations.

    This class provides sophisticated order monitoring capabilities including:
    - Periodic checking of order fill status
    - Intelligent re-pegging of limit orders
    - Escalation of unfilled orders to market execution
    - Tracking of cancelled/expired orders with partial fills

    Thread Safety:
        This class is NOT thread-safe. It is designed to be used by a single
        async execution context. The smart_strategy.order_tracker that this class
        queries may have its own thread-safety guarantees (see SmartExecutionStrategy
        documentation), but OrderMonitor itself makes no guarantees about concurrent
        access to its methods.

        For concurrent monitoring of multiple phases, instantiate separate OrderMonitor
        instances with independent smart_strategy objects, or use async locking if
        sharing a single instance.

    Typical Usage:
        >>> monitor = OrderMonitor(smart_strategy, config)
        >>> updated_orders = await monitor.monitor_and_repeg_phase_orders(
        ...     "BUY", initial_orders, correlation_id="trade-123"
        ... )

    """

    def __init__(
        self,
        smart_strategy: SmartExecutionStrategy | None,
        execution_config: ExecutionConfig | None,
    ) -> None:
        """Initialize the order monitor.

        Args:
            smart_strategy: Smart execution strategy instance providing order tracking
                          and re-peg capabilities. If None, monitoring is disabled.
            execution_config: Execution configuration with monitoring parameters.
                            If None, falls back to module-level defaults.

        Note:
            Both arguments are optional to support testing and degraded operation modes.
            When smart_strategy is None, monitoring operations return immediately without
            performing any order tracking or escalation.

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

        Raises:
            No exceptions are raised; configuration errors are logged and defaults are used.

        Note:
            The configuration is derived from ExecutionConfig when available,
            otherwise falls back to module-level constants. The wait_between_checks
            is calculated dynamically to check ~5 times per fill_wait period.

        """
        config = {
            "max_repegs": DEFAULT_MAX_REPEGS,
            "fill_wait_seconds": DEFAULT_FILL_WAIT_SECONDS,
            "wait_between_checks": DEFAULT_WAIT_BETWEEN_CHECKS,
            "max_total_wait": DEFAULT_MAX_TOTAL_WAIT_SECONDS,
        }

        try:
            if self.execution_config is not None:
                config["max_repegs"] = getattr(
                    self.execution_config, "max_repegs_per_order", DEFAULT_MAX_REPEGS
                )
                config["fill_wait_seconds"] = int(
                    getattr(self.execution_config, "fill_wait_seconds", DEFAULT_FILL_WAIT_SECONDS)
                )
                config["wait_between_checks"] = self._calculate_check_interval(
                    config["fill_wait_seconds"]
                )
                placement_timeout = int(
                    getattr(
                        self.execution_config,
                        "order_placement_timeout_seconds",
                        DEFAULT_PLACEMENT_TIMEOUT_SECONDS,
                    )
                )
                # Calculate total wait time: placement timeout + fill waits per re-peg + safety margin
                config["max_total_wait"] = int(
                    placement_timeout
                    + config["fill_wait_seconds"] * (config["max_repegs"] + 1)
                    + SAFETY_MARGIN_SECONDS
                )
                # Clamp to reasonable bounds
                config["max_total_wait"] = max(
                    MIN_TOTAL_WAIT_SECONDS, min(config["max_total_wait"], MAX_TOTAL_WAIT_SECONDS)
                )
        except (AttributeError, ValueError, TypeError) as exc:
            logger.warning(
                "Error deriving re-peg loop configuration, using defaults",
                extra={"error": str(exc), "error_type": type(exc).__name__, "defaults": config},
            )
        except Exception as exc:
            # Last-resort catch for unexpected errors during configuration derivation
            logger.error(
                "Unexpected error deriving re-peg loop configuration",
                extra={"error": str(exc), "error_type": type(exc).__name__, "defaults": config},
                exc_info=True,
            )
            raise OrderError(
                f"Failed to derive monitoring configuration: {exc}",
                context={"config_attempted": config},
            ) from exc

        return config

    def _calculate_check_interval(self, fill_wait_seconds: int) -> int:
        """Calculate optimal interval between order status checks.

        Args:
            fill_wait_seconds: Time to wait for order fills

        Returns:
            Optimal check interval in seconds (1-5 seconds)

        Note:
            Aims to check approximately 5 times per fill_wait period for
            responsive monitoring without excessive API calls.

        """
        return max(
            DEFAULT_WAIT_BETWEEN_CHECKS,
            min(fill_wait_seconds // CHECK_FREQUENCY_DIVISOR, MAX_WAIT_BETWEEN_CHECKS),
        )

    def _log_monitoring_config(
        self, phase_type: str, config: dict[str, int], correlation_id: str | None = None
    ) -> None:
        """Log the monitoring configuration parameters.

        Args:
            phase_type: Type of phase being monitored
            config: Configuration dictionary with monitoring parameters
            correlation_id: Optional correlation ID for tracking

        """
        log_prefix = f"[{correlation_id}]" if correlation_id else ""
        logger.debug(
            f"{log_prefix} {phase_type} re-peg monitoring configuration",
            extra={
                "correlation_id": correlation_id,
                "phase_type": phase_type,
                "max_repegs": config["max_repegs"],
                "fill_wait_seconds": config["fill_wait_seconds"],
                "max_total_wait": config["max_total_wait"],
                "wait_between_checks": config["wait_between_checks"],
            },
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

            except OrderExecutionError as exc:
                logger.warning(
                    f"{log_prefix} ⚠️ {phase_type} phase re-peg attempt {attempts} failed (order execution error)",
                    extra={
                        "correlation_id": correlation_id,
                        "phase_type": phase_type,
                        "attempt": attempts,
                        "error_type": "order_execution",
                        "error": str(exc),
                        "context": getattr(exc, "context", {}),
                    },
                )
            except OrderError as exc:
                logger.warning(
                    f"{log_prefix} ⚠️ {phase_type} phase re-peg attempt {attempts} failed (order error)",
                    extra={
                        "correlation_id": correlation_id,
                        "phase_type": phase_type,
                        "attempt": attempts,
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                        "order_id": getattr(exc, "order_id", None),
                    },
                )
            except Exception as exc:
                # Last-resort catch for unexpected errors during re-peg monitoring
                logger.error(
                    f"{log_prefix} ❌ {phase_type} phase re-peg attempt {attempts} failed (unexpected error)",
                    extra={
                        "correlation_id": correlation_id,
                        "phase_type": phase_type,
                        "attempt": attempts,
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    },
                    exc_info=True,
                )
                # Re-raise unexpected errors as OrderError for proper handling upstream
                raise OrderError(
                    f"Unexpected error during {phase_type} re-peg monitoring attempt {attempts}: {exc}",
                    context={
                        "phase_type": phase_type,
                        "attempt": attempts,
                        "correlation_id": correlation_id,
                    },
                ) from exc

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
        self,
        phase_type: str,
        correlation_id: str | None = None,
        orders: list[OrderResult] | None = None,
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

            orders_to_escalate = self._collect_orders_for_escalation(
                phase_type, orders, log_prefix, correlation_id
            )

            if not orders_to_escalate:
                logger.debug(f"{log_prefix} {phase_type} phase: No orders need market escalation")
                return {}

            logger.warning(
                f"{log_prefix} 🚨 {phase_type} phase: Escalating {len(orders_to_escalate)} orders to market"
            )

            return await self._execute_escalation_and_build_replacement_map(
                orders_to_escalate, log_prefix
            )
        except OrderExecutionError as exc:
            logger.error(
                f"{log_prefix} Order execution error during final escalation in {phase_type} phase",
                extra={
                    "correlation_id": correlation_id,
                    "phase_type": phase_type,
                    "error_type": "order_execution",
                    "error": str(exc),
                    "context": getattr(exc, "context", {}),
                },
                exc_info=True,
            )
            return {}
        except OrderError as exc:
            logger.error(
                f"{log_prefix} Order error during final escalation in {phase_type} phase",
                extra={
                    "correlation_id": correlation_id,
                    "phase_type": phase_type,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                    "order_id": getattr(exc, "order_id", None),
                },
                exc_info=True,
            )
            return {}
        except Exception as exc:
            # Last-resort catch for unexpected errors during final escalation
            logger.error(
                f"{log_prefix} Unexpected error during final escalation in {phase_type} phase",
                extra={
                    "correlation_id": correlation_id,
                    "phase_type": phase_type,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
                exc_info=True,
            )
            # Re-raise unexpected errors
            raise OrderError(
                f"Unexpected error during final escalation in {phase_type} phase: {exc}",
                context={"phase_type": phase_type, "correlation_id": correlation_id},
            ) from exc

    def _collect_orders_for_escalation(
        self,
        phase_type: str,
        orders: list[OrderResult] | None,
        log_prefix: str,
        correlation_id: str | None,
    ) -> dict[str, tuple[SmartOrderRequest, str]]:
        """Collect orders that need escalation to market.

        Args:
            phase_type: Type of phase being monitored
            orders: Original orders list to check
            log_prefix: Logging prefix for correlation
            correlation_id: Optional correlation ID

        Returns:
            Dictionary mapping order IDs to (request, reason) tuples.

        """
        if not self.smart_strategy:
            return {}

        # First check: active orders still in tracking
        active = self.smart_strategy.order_tracker.get_active_orders()
        orders_to_escalate: dict[str, tuple[SmartOrderRequest, str]] = {}

        if active:
            logger.warning(
                f"{log_prefix} 🚨 {phase_type} phase: {len(active)} active orders in tracking; "
                "checking for escalation"
            )
            for order_id, request in active.items():
                orders_to_escalate[order_id] = (request, "active_unfilled")

        # Second check: verify broker status for cancelled/expired orders
        if orders:
            self._check_cancelled_orders_for_escalation(
                orders, active, orders_to_escalate, log_prefix, correlation_id
            )

        return orders_to_escalate

    async def _execute_escalation_and_build_replacement_map(
        self, orders_to_escalate: dict[str, tuple[SmartOrderRequest, str]], log_prefix: str
    ) -> dict[str, str]:
        """Execute market escalation and build replacement map.

        Args:
            orders_to_escalate: Orders to escalate
            log_prefix: Logging prefix for correlation

        Returns:
            Dictionary mapping original order IDs to new order IDs.

        """
        if not self.smart_strategy:
            return {}

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
            if self._should_skip_order(order, active):
                continue

            # Note: _should_skip_order filters out falsy order_id, but order_id may still be None or empty.
            order_id = order.order_id
            if (
                not order_id
            ):  # Additional guard is necessary to ensure order_id is a non-empty string.
                continue

            order_status = self._get_order_status(order_id)
            if not self._is_cancelled_status(order_status):
                continue

            # Note: _is_cancelled_status only returns a boolean and does not guarantee order_status is a string.
            # The guard below is necessary for runtime safety, not just type checking.
            if not order_status:
                continue

            self._check_and_add_unfilled_order(
                order, order_id, order_status, orders_to_escalate, log_prefix, correlation_id
            )

    def _should_skip_order(self, order: OrderResult, active: dict[str, SmartOrderRequest]) -> bool:
        """Check if order should be skipped for escalation checks.

        This method determines whether an order needs further escalation processing.
        Orders are skipped if they lack valid order IDs, failed at placement, or are
        still being actively monitored by the re-peg system.

        Args:
            order: Order result to evaluate
            active: Dictionary of currently active orders being tracked for re-pegging

        Returns:
            True if order should be skipped (no escalation needed), False otherwise

        Pre-conditions:
            - order must be a valid OrderResult instance
            - active must be a dict mapping order IDs to SmartOrderRequest objects

        Post-conditions:
            - Returns boolean; no state modification

        Examples:
            >>> order = OrderResult(order_id=None, success=True, ...)
            >>> monitor._should_skip_order(order, {})
            True  # No order ID means skip

            >>> order = OrderResult(order_id="abc-123", success=True, ...)
            >>> active = {"abc-123": SmartOrderRequest(...)}
            >>> monitor._should_skip_order(order, active)
            True  # Still active, being handled by re-peg system

            >>> order = OrderResult(order_id="xyz-789", success=True, ...)
            >>> monitor._should_skip_order(order, {})
            False  # Has ID, not active, needs escalation check

        """
        if not order.order_id or not order.success:
            return True
        # Skip if order is still in active tracking (already handled by re-peg system)
        return order.order_id in active

    def _get_order_status(self, order_id: str) -> str | None:
        """Get current order status from broker API.

        Queries the Alpaca broker API to retrieve the current completion status
        of an order. This is used to detect cancelled, expired, or rejected orders
        that may have unfilled quantities requiring market order escalation.

        Args:
            order_id: Broker order identifier (UUID string)

        Returns:
            Order status string (e.g., "FILLED", "CANCELED", "EXPIRED", "REJECTED")
            or None if status cannot be determined or smart_strategy is unavailable

        Pre-conditions:
            - order_id must be a valid non-empty string
            - smart_strategy must be initialized (if None, returns None)

        Post-conditions:
            - Makes external API call to broker
            - Returns status or None; no state modification

        Raises:
            No exceptions raised directly. Broker API errors are handled by
            AlpacaManager and return None.

        Examples:
            >>> status = monitor._get_order_status("abc-123-uuid")
            >>> print(status)
            'FILLED'

            >>> status = monitor._get_order_status("cancelled-order-id")
            >>> print(status)
            'CANCELED'

        Note:
            This method makes an external API call and should be used judiciously
            to avoid rate limits. It's called once per order during escalation checks.

        """
        if not self.smart_strategy:
            return None
        return self.smart_strategy.alpaca_manager._check_order_completion_status(order_id)

    def _is_cancelled_status(self, order_status: str | None) -> bool:
        """Check if order status indicates cancellation.

        Args:
            order_status: Order status to check

        Returns:
            True if order was cancelled/expired/rejected.

        """
        # Status list mirrors the centralized check in utils.is_order_completed
        return bool(order_status and order_status in ["CANCELED", "EXPIRED", "REJECTED"])

    def _check_and_add_unfilled_order(
        self,
        order: OrderResult,
        order_id: str,
        order_status: str,
        orders_to_escalate: dict[str, tuple[SmartOrderRequest, str]],
        log_prefix: str,
        correlation_id: str | None,
    ) -> None:
        """Check for unfilled quantity and add to escalation list if needed.

        Verifies if an order with a terminal status (CANCELED, EXPIRED, REJECTED)
        has unfilled shares that require market order escalation. This prevents
        partial fills or zero fills from leaving positions unexecuted.

        Args:
            order: Original order result to check
            order_id: Broker order identifier (guaranteed non-None by caller)
            order_status: Current terminal status (CANCELED/EXPIRED/REJECTED)
            orders_to_escalate: Dictionary to populate with orders requiring escalation.
                               Maps order_id to (SmartOrderRequest, reason) tuples.
            log_prefix: Logging prefix including correlation ID
            correlation_id: Optional correlation ID for tracking

        Pre-conditions:
            - order_id is a non-empty valid broker order ID
            - order_status is one of: CANCELED, EXPIRED, or REJECTED
            - smart_strategy must be initialized
            - orders_to_escalate dict exists and is mutable

        Post-conditions:
            - If unfilled quantity exists, adds entry to orders_to_escalate dict
            - Logs warning when unfilled quantity detected
            - No modification if order fully filled or errors occur

        Side effects:
            - Queries broker API for filled quantity (via _get_filled_quantity)
            - Modifies orders_to_escalate dict if unfilled quantity found
            - Writes log messages for unfilled orders and errors

        Raises:
            No exceptions propagated. Handles AttributeError, ValueError, TypeError
            for data access errors, and logs unexpected exceptions.

        Examples:
            >>> # Order with 10 shares requested, 3 filled, 7 unfilled
            >>> order = OrderResult(symbol="AAPL", shares=Decimal("10"), ...)
            >>> orders_to_escalate = {}
            >>> monitor._check_and_add_unfilled_order(
            ...     order, "abc-123", "CANCELED", orders_to_escalate, "[corr-1]", "corr-1"
            ... )
            >>> print(orders_to_escalate)
            {'abc-123': (SmartOrderRequest(symbol='AAPL', quantity=Decimal('7'), ...), 'canceled_unfilled')}

        """
        if not self.smart_strategy:
            return

        try:
            filled_qty = self._get_filled_quantity(order_id)
            if filled_qty is None:
                logger.debug(
                    f"{log_prefix} Could not determine filled quantity for order {order_id}",
                    extra={
                        "correlation_id": correlation_id,
                        "order_id": order_id,
                        "order_status": order_status,
                    },
                )
                return

            # Use Decimal comparison to avoid float precision issues
            if filled_qty < order.shares:
                self._add_order_to_escalation(
                    order,
                    order_id,
                    order_status,
                    filled_qty,
                    orders_to_escalate,
                    log_prefix,
                    correlation_id,
                )
        except (AttributeError, ValueError, TypeError) as exc:
            logger.debug(
                f"{log_prefix} Data access error checking order {order_id}",
                extra={
                    "correlation_id": correlation_id,
                    "order_id": order_id,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
            )
        except Exception as exc:
            # Last-resort catch for unexpected errors during order checking
            logger.warning(
                f"{log_prefix} Unexpected error checking order {order_id}",
                extra={
                    "correlation_id": correlation_id,
                    "order_id": order_id,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
                exc_info=True,
            )
            # Re-raise unexpected errors as OrderError
            raise OrderError(
                f"Unexpected error checking unfilled quantity for order {order_id}: {exc}",
                order_id=order_id,
                context={"correlation_id": correlation_id, "order_status": order_status},
            ) from exc

    def _get_filled_quantity(self, order_id: str) -> Decimal | None:
        """Get filled quantity for an order.

        Args:
            order_id: Order ID to check

        Returns:
            Filled quantity as Decimal, or None if not available.

        """
        if not self.smart_strategy:
            return None

        order_result = self.smart_strategy.alpaca_manager.get_order_execution_result(order_id)
        filled_qty_raw = getattr(order_result, "filled_qty", 0) or 0
        return Decimal(str(filled_qty_raw))

    def _add_order_to_escalation(
        self,
        order: OrderResult,
        order_id: str,
        order_status: str,
        filled_qty: Decimal,
        orders_to_escalate: dict[str, tuple[SmartOrderRequest, str]],
        log_prefix: str,
        correlation_id: str | None,
    ) -> None:
        """Add order with unfilled quantity to escalation list.

        Args:
            order: Order to escalate
            order_id: Order ID (guaranteed non-None)
            order_status: Current order status
            filled_qty: Filled quantity
            orders_to_escalate: Dictionary to populate
            log_prefix: Logging prefix
            correlation_id: Optional correlation ID

        """
        remaining_qty = order.shares - filled_qty
        logger.warning(
            f"{log_prefix} 🚨 Order escalation triggered - {order_status} with unfilled quantity",
            extra={
                "correlation_id": correlation_id,
                "order_id": order_id,
                "order_status": order_status,
                "symbol": order.symbol,
                "action": order.action,
                "requested_shares": str(order.shares),
                "filled_shares": str(filled_qty),
                "remaining_shares": str(remaining_qty),
            },
        )
        # Create request for the remaining quantity
        request = SmartOrderRequest(
            symbol=order.symbol,
            side=order.action,
            quantity=remaining_qty,
            correlation_id=correlation_id or "",
        )
        orders_to_escalate[order_id] = (request, f"{order_status.lower()}_unfilled")

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
        """Log when no re-pegging activity occurred.

        Args:
            phase_type: Type of phase being monitored
            attempts: Current attempt number
            elapsed_total: Total elapsed time in seconds
            correlation_id: Optional correlation ID for tracking

        """
        log_prefix = f"[{correlation_id}]" if correlation_id else ""
        logger.debug(
            f"{log_prefix} 🔄 {phase_type} phase re-peg check - no unfilled orders",
            extra={
                "correlation_id": correlation_id,
                "phase_type": phase_type,
                "attempt": attempts,
                "elapsed_seconds": round(elapsed_total, 1),
            },
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
            elapsed_total: Total elapsed time in seconds
            max_total_wait: Maximum wait time in seconds
            phase_type: Type of phase being monitored
            correlation_id: Optional correlation ID for tracking

        Returns:
            True if should terminate early (time limit exceeded), False otherwise

        """
        log_prefix = f"[{correlation_id}]" if correlation_id else ""
        if elapsed_total > max_total_wait:
            logger.info(
                f"{log_prefix} ⏰ {phase_type} phase: Terminating re-peg loop - time limit exceeded",
                extra={
                    "correlation_id": correlation_id,
                    "phase_type": phase_type,
                    "elapsed_seconds": round(elapsed_total, 1),
                    "max_wait_seconds": max_total_wait,
                },
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
            phase_type: Type of phase being monitored
            attempts: Number of monitoring attempts made
            total_elapsed: Total elapsed time in seconds
            correlation_id: Optional correlation ID for tracking

        """
        log_prefix = f"[{correlation_id}]" if correlation_id else ""
        logger.info(
            f"{log_prefix} ✅ {phase_type} phase re-peg monitoring complete",
            extra={
                "correlation_id": correlation_id,
                "phase_type": phase_type,
                "attempts": attempts,
                "elapsed_seconds": round(total_elapsed, 1),
            },
        )

    def _log_repeg_status(
        self, phase_type: str, repeg_result: SmartOrderResult, correlation_id: str | None = None
    ) -> None:
        """Log the status of a re-pegging operation.

        Args:
            phase_type: Type of phase being monitored
            repeg_result: Result of re-peg operation
            correlation_id: Optional correlation ID for tracking

        """
        log_prefix = f"[{correlation_id}]" if correlation_id else ""
        strategy = getattr(repeg_result, "execution_strategy", "")
        order_id = getattr(repeg_result, "order_id", "")
        repegs_used = getattr(repeg_result, "repegs_used", 0)

        if "escalation" in strategy:
            logger.warning(
                f"{log_prefix} 🚨 {phase_type} ESCALATED_TO_MARKET",
                extra={
                    "correlation_id": correlation_id,
                    "phase_type": phase_type,
                    "order_id": order_id,
                    "repegs_used": repegs_used,
                    "execution_strategy": strategy,
                },
            )
        else:
            max_repegs = (
                getattr(self.execution_config, "max_repegs_per_order", DEFAULT_MAX_REPEGS)
                if self.execution_config
                else DEFAULT_MAX_REPEGS
            )
            logger.debug(
                f"{log_prefix} ✅ {phase_type} REPEG",
                extra={
                    "correlation_id": correlation_id,
                    "phase_type": phase_type,
                    "order_id": order_id,
                    "repegs_used": repegs_used,
                    "max_repegs": max_repegs,
                    "execution_strategy": strategy,
                },
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
        """Handle failed re-pegging attempts.

        Args:
            phase_type: Type of phase being monitored
            repeg_result: Failed repeg result
            correlation_id: Optional correlation ID for tracking

        """
        log_prefix = f"[{correlation_id}]" if correlation_id else ""
        logger.warning(
            f"{log_prefix} ⚠️ {phase_type} phase re-peg failed",
            extra={
                "correlation_id": correlation_id,
                "phase_type": phase_type,
                "error_message": repeg_result.error_message,
                "execution_strategy": getattr(repeg_result, "execution_strategy", ""),
            },
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
