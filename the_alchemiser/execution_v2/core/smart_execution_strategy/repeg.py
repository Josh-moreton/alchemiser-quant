"""Business Unit: execution | Status: current.

Re-pegging and escalation logic for smart execution strategy.

This module handles the re-pegging of unfilled orders and escalation to market
orders when maximum re-peg attempts are reached.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from decimal import Decimal

from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.errors.exceptions import OrderExecutionError
from the_alchemiser.shared.logging import get_logger, log_repeg_operation
from the_alchemiser.shared.schemas.broker import OrderExecutionResult
from the_alchemiser.shared.schemas.execution_report import ExecutedOrder
from the_alchemiser.shared.schemas.operations import (
    OrderCancellationResult,
    TerminalOrderError,
)
from the_alchemiser.shared.types.market_data import QuoteModel

from .models import (
    ExecutionConfig,
    LiquidityMetadata,
    SmartOrderRequest,
    SmartOrderResult,
)
from .pricing import PricingCalculator
from .quotes import QuoteProvider
from .tracking import OrderTracker
from .utils import fetch_price_for_notional_check, is_remaining_quantity_too_small

logger = get_logger(__name__)

# Module constants for polling and timeouts
DEFAULT_CANCELLATION_TIMEOUT_SECONDS = 10.0
CANCELLATION_CHECK_INTERVAL_SECONDS = 0.1
MIN_QUANTITY_THRESHOLD = Decimal("0.01")
MIN_VALID_PRICE = Decimal("0.01")
PRICE_QUANTIZATION = Decimal("0.01")  # 2 decimal places (cents)


class _RemoveFromTracking(Exception):
    """Internal control-flow to signal that order should be removed from tracking."""


class RepegManager:
    """Manages re-pegging and escalation of unfilled orders."""

    def __init__(
        self,
        alpaca_manager: AlpacaManager,
        quote_provider: QuoteProvider,
        pricing_calculator: PricingCalculator,
        order_tracker: OrderTracker,
        config: ExecutionConfig,
    ) -> None:
        """Initialize repeg manager.

        Args:
            alpaca_manager: Alpaca broker manager for order operations
            quote_provider: Quote provider for market data
            pricing_calculator: Pricing calculator for repeg prices
            order_tracker: Order tracker for state management
            config: Execution configuration

        """
        self.alpaca_manager = alpaca_manager
        self.quote_provider = quote_provider
        self.pricing_calculator = pricing_calculator
        self.order_tracker = order_tracker
        self.config = config

    def _is_order_in_terminal_state(
        self, cancel_result: OrderCancellationResult
    ) -> tuple[bool, TerminalOrderError | None]:
        """Check if cancellation result indicates order is in terminal state.

        Args:
            cancel_result: Result from cancel_order operation

        Returns:
            Tuple of (is_terminal, terminal_error_type) where terminal_error_type
            is the specific TerminalOrderError enum value, or None if not terminal

        """
        if not cancel_result.success or not cancel_result.error:
            return False, None

        # Check if the error matches any terminal order error enum value
        for terminal_error in TerminalOrderError:
            if cancel_result.error == terminal_error.value:
                return True, terminal_error

        return False, None

    async def check_and_repeg_orders(self) -> list[SmartOrderResult]:
        """Check active orders and repeg if they haven't filled after the wait period.

        Returns:
            List of re-pegging results

        """
        active_orders = self.order_tracker.get_active_orders()
        if not active_orders:
            return []

        repeg_results: list[SmartOrderResult] = []
        orders_to_remove: list[str] = []
        current_time = datetime.now(UTC)

        for order_id, request in active_orders.copy().items():
            result = await self._process_single_order(order_id, request, current_time)

            # None => remove (completed or irrecoverable)
            # False => keep (no action needed yet)
            # SmartOrderResult => action taken (repeg/escalation)
            if result is None:
                orders_to_remove.append(order_id)
            elif isinstance(result, SmartOrderResult):
                repeg_results.append(result)

        # Clean up completed orders
        for order_id in orders_to_remove:
            self.order_tracker.remove_order(order_id)

        return repeg_results

    async def _process_single_order(
        self, order_id: str, request: SmartOrderRequest, current_time: datetime
    ) -> SmartOrderResult | bool | None:
        """Process a single order for potential repeg or escalation.

        Args:
            order_id: Order ID to process
            request: Original order request
            current_time: Current timestamp

        Returns:
            SmartOrderResult if action taken,
            False if no action needed yet (keep tracking),
            None if order completed and should be removed

        """
        try:
            # Check if order is still active
            if self._is_order_completed(order_id):
                return None  # Completed: signal for removal

            # Check timing for repeg consideration
            if not self._should_consider_repeg(order_id, current_time):
                return False  # Keep tracking; no action yet

            current_repeg_count = self.order_tracker.get_repeg_count(order_id)

            # Business rule: the "final step" should be a market escalation, not another limit re-peg.
            # Therefore, when the NEXT re-peg would meet or exceed the configured max, escalate now.
            # Example: max=2 -> allow at most 1 re-peg; on the second consideration, escalate to market.
            try:
                max_repegs_allowed = int(getattr(self.config, "max_repegs_per_order", 0))
            except (ValueError, AttributeError):
                max_repegs_allowed = 0

            if current_repeg_count + 1 >= max_repegs_allowed:
                logger.warning(
                    "Order approaching max re-pegs, escalating to market",
                    order_id=order_id,
                    correlation_id=request.correlation_id,
                    current_repeg_count=current_repeg_count,
                    max_repegs_allowed=max_repegs_allowed,
                    symbol=request.symbol,
                )
                return await self._escalate_to_market(order_id, request)

            # Attempt re-pegging (we still have room before reaching the max)
            placement_time = self.order_tracker.get_placement_time(order_id)
            if placement_time:
                time_elapsed = (current_time - placement_time).total_seconds()
                logger.debug(
                    "Order hasn't filled after wait period, attempting re-peg",
                    order_id=order_id,
                    correlation_id=request.correlation_id,
                    time_elapsed=time_elapsed,
                    attempt=current_repeg_count + 1,
                    max_repegs=self.config.max_repegs_per_order,
                    symbol=request.symbol,
                )
            return await self._attempt_repeg(order_id, request)

        except (ValueError, AttributeError, OrderExecutionError, asyncio.TimeoutError) as e:
            logger.error(
                "Error checking order for re-pegging",
                order_id=order_id,
                correlation_id=request.correlation_id,
                error=str(e),
                exc_info=True,
            )
            return False  # Keep tracking on transient errors

    def _is_order_completed(self, order_id: str) -> bool:
        """Check if order has completed and should be removed from tracking.

        Args:
            order_id: Order ID to check

        Returns:
            True if order is completed

        """
        from .utils import is_order_completed

        order_status = self.alpaca_manager._check_order_completion_status(order_id)

        if order_status and is_order_completed(order_status):
            logger.debug(
                "Order completed with status",
                order_id=order_id,
                status=order_status,
            )
            return True

        return False

    def _should_consider_repeg(self, order_id: str, current_time: datetime) -> bool:
        """Check if order should be considered for re-pegging based on timing.

        Args:
            order_id: Order ID to check
            current_time: Current timestamp

        Returns:
            True if order should be considered for repeg

        """
        from .utils import should_consider_repeg

        placement_time = self.order_tracker.get_placement_time(order_id)
        if not placement_time:
            return False

        if should_consider_repeg(placement_time, current_time, self.config.fill_wait_seconds):
            return True

        # Log debug info for orders still waiting
        time_elapsed = (current_time - placement_time).total_seconds()
        logger.debug(
            "Order waiting for fill",
            order_id=order_id,
            time_elapsed=time_elapsed,
            fill_wait_seconds=self.config.fill_wait_seconds,
            repeg_count=self.order_tracker.get_repeg_count(order_id),
        )
        return False

    def _should_escalate_order(self, current_repeg_count: int) -> bool:
        """Check if order should be escalated to market order.

        Args:
            current_repeg_count: Current number of repegs

        Returns:
            True if order should be escalated

        """
        from .utils import should_escalate_order

        return should_escalate_order(current_repeg_count, self.config.max_repegs_per_order)

    def _handle_terminal_state_order(
        self, order_id: str, terminal_error: TerminalOrderError
    ) -> SmartOrderResult:
        """Handle order already in terminal state during escalation.

        Args:
            order_id: Order ID
            terminal_error: Terminal error type

        Returns:
            SmartOrderResult indicating order is complete

        """
        terminal_state = terminal_error.value.replace("already_", "")
        logger.info(
            "Order already in terminal state, no market escalation needed",
            order_id=order_id,
            terminal_state=terminal_state,
        )

        # Clean up tracking
        original_anchor = self.order_tracker.get_anchor_price(order_id)
        self.order_tracker.remove_order(order_id)

        return SmartOrderResult(
            success=True,
            order_id=order_id,
            final_price=original_anchor,
            anchor_price=original_anchor,
            repegs_used=self.config.max_repegs_per_order,
            execution_strategy=terminal_error.value,
            placement_timestamp=datetime.now(UTC),
            error_message=f"Order already in terminal state: {terminal_state} (escalation prevented)",
        )

    async def _handle_cancellation_wait(
        self, order_id: str, cancel_result: OrderCancellationResult
    ) -> None:
        """Handle waiting for order cancellation confirmation.

        Args:
            order_id: Order ID to wait for cancellation
            cancel_result: Result of cancellation request

        """
        if not cancel_result.success:
            logger.warning(
                "Failed to cancel order, attempting market order anyway",
                order_id=order_id,
            )
            return

        logger.debug(
            "Waiting for order cancellation to complete before market escalation",
            order_id=order_id,
        )
        cancellation_confirmed = await asyncio.to_thread(
            self._wait_for_order_cancellation, order_id
        )

        if not cancellation_confirmed:
            logger.warning(
                "Order cancellation did not complete within timeout, proceeding with market order anyway",
                order_id=order_id,
            )
        else:
            logger.debug(
                "Order cancellation confirmed, proceeding with market escalation",
                order_id=order_id,
            )

    def _is_market_escalation_successful(self, executed_order: ExecutedOrder) -> bool:
        """Check if market escalation was successful.

        Args:
            executed_order: Market order execution result

        Returns:
            True if escalation was successful

        """
        return bool(
            executed_order.order_id and executed_order.status not in ["REJECTED", "CANCELED"]
        )

    def _create_market_escalation_metadata(
        self,
        order_id: str,
        executed_order: ExecutedOrder,
        original_anchor: Decimal | None,
    ) -> LiquidityMetadata:
        """Create metadata dict for successful market escalation.

        Args:
            order_id: Original order ID
            executed_order: Market order execution result
            original_anchor: Original anchor price

        Returns:
            LiquidityMetadata dictionary

        """
        return {
            "original_order_id": order_id,
            "original_price": (float(original_anchor) if original_anchor is not None else None),
            "new_price": (float(executed_order.price) if executed_order.price is not None else 0.0),
        }

    def _build_successful_market_escalation_result(
        self,
        order_id: str,
        executed_order: ExecutedOrder,
        original_anchor: Decimal | None,
    ) -> SmartOrderResult:
        """Build result for successful market escalation.

        Args:
            order_id: Original order ID
            executed_order: Market order execution result
            original_anchor: Original anchor price

        Returns:
            SmartOrderResult indicating success

        """
        metadata = self._create_market_escalation_metadata(
            order_id, executed_order, original_anchor
        )
        logger.info(
            "Market escalation successful",
            new_order_id=executed_order.order_id,
            original_order_id=order_id,
            max_repegs=self.config.max_repegs_per_order,
        )
        return SmartOrderResult(
            success=True,
            order_id=executed_order.order_id,
            final_price=(executed_order.price if executed_order.price is not None else None),
            anchor_price=original_anchor,
            repegs_used=self.config.max_repegs_per_order,
            execution_strategy="market_escalation",
            placement_timestamp=executed_order.execution_timestamp,
            metadata=metadata,
        )

    def _build_failed_market_escalation_result(
        self,
        executed_order: ExecutedOrder,
        request: SmartOrderRequest,
    ) -> SmartOrderResult:
        """Build result for failed market escalation.

        Args:
            executed_order: Market order execution result
            request: Original order request

        Returns:
            SmartOrderResult indicating failure

        """
        logger.error(
            "Market escalation failed",
            symbol=request.symbol,
            correlation_id=request.correlation_id,
            status=executed_order.status,
        )
        return SmartOrderResult(
            success=False,
            order_id=executed_order.order_id,
            error_message=getattr(executed_order, "error_message", None)
            or "Market escalation placement failed",
            execution_strategy="market_escalation_failed",
            placement_timestamp=executed_order.execution_timestamp,
        )

    def _build_market_escalation_result(
        self,
        order_id: str,
        executed_order: ExecutedOrder,
        original_anchor: Decimal | None,
        request: SmartOrderRequest,
    ) -> SmartOrderResult:
        """Build result for market order escalation based on execution outcome.

        Args:
            order_id: Original order ID
            executed_order: Market order execution result
            original_anchor: Original anchor price
            request: Original order request

        Returns:
            SmartOrderResult with success or failure status

        """
        if self._is_market_escalation_successful(executed_order):
            return self._build_successful_market_escalation_result(
                order_id, executed_order, original_anchor
            )

        return self._build_failed_market_escalation_result(executed_order, request)

    async def _escalate_to_market(
        self, order_id: str, request: SmartOrderRequest
    ) -> SmartOrderResult:
        """Cancel current limit order and place a market order (final escalation).

        Args:
            order_id: Existing limit order ID to cancel
            request: Original smart order request details

        Returns:
            SmartOrderResult describing the escalation outcome

        """
        try:
            logger.debug(
                "Escalating order to market, canceling existing limit order",
                order_id=order_id,
                correlation_id=request.correlation_id,
                repeg_count=self.order_tracker.get_repeg_count(order_id),
                symbol=request.symbol,
            )
            # Use asyncio.to_thread to make blocking I/O async
            cancel_result = await asyncio.to_thread(self.alpaca_manager.cancel_order, order_id)

            # Check if order was already in a terminal state (e.g., filled, cancelled)
            is_terminal, terminal_error = self._is_order_in_terminal_state(cancel_result)
            if is_terminal and terminal_error:
                return self._handle_terminal_state_order(order_id, terminal_error)

            # Wait for cancellation to complete
            await self._handle_cancellation_wait(order_id, cancel_result)

            # Place market order
            logger.info(
                "Placing market order",
                symbol=request.symbol,
                correlation_id=request.correlation_id,
                side=request.side,
            )
            executed_order = await asyncio.to_thread(
                self.alpaca_manager.place_market_order,
                symbol=request.symbol,
                side=request.side.lower(),
                qty=request.quantity,
                is_complete_exit=request.is_complete_exit,
            )

            # Clean up old tracking regardless of outcome
            original_anchor = self.order_tracker.get_anchor_price(order_id)
            self.order_tracker.remove_order(order_id)

            return self._build_market_escalation_result(
                order_id, executed_order, original_anchor, request
            )

        except (OrderExecutionError, asyncio.TimeoutError) as exc:
            logger.error(
                "Error during market escalation",
                order_id=order_id,
                correlation_id=request.correlation_id,
                error=str(exc),
                exc_info=True,
            )
            return SmartOrderResult(
                success=False,
                error_message=str(exc),
                execution_strategy="market_escalation_error",
            )

    def _create_repeg_metadata(
        self,
        order_id: str,
        original_anchor: Decimal | None,
        new_price: Decimal,
        quote: QuoteModel | None,
    ) -> LiquidityMetadata:
        """Create metadata dictionary for repeg operation.

        Args:
            order_id: Original order ID
            original_anchor: Original anchor price
            new_price: New limit price
            quote: Quote data used for pricing

        Returns:
            LiquidityMetadata dictionary

        """
        # Use cast to satisfy type checkers; quote is non-None when new_price exists
        from typing import cast as _cast

        q = _cast(QuoteModel, quote)
        return {
            "original_order_id": order_id,
            "original_price": (float(original_anchor) if original_anchor else None),
            "new_price": float(new_price),
            "bid_price": float(q.bid_price),
            "ask_price": float(q.ask_price),
            "spread_percent": float((q.ask_price - q.bid_price) / q.bid_price * 100),
            "bid_size": float(q.bid_size),
            "ask_size": float(q.ask_size),
        }

    def _build_repeg_success_result(
        self,
        order_id: str,
        executed_order: OrderExecutionResult,
        request: SmartOrderRequest,
        new_price: Decimal,
        original_anchor: Decimal | None,
        quote: QuoteModel | None,
        remaining_qty: Decimal,
        new_repeg_count: int,
    ) -> SmartOrderResult:
        """Build success result for a successful repeg operation.

        Args:
            order_id: Original order ID
            executed_order: Result from placing the new order
            request: Original order request
            new_price: New limit price
            original_anchor: Original anchor price
            quote: Quote data used for pricing
            remaining_qty: Remaining quantity
            new_repeg_count: Current repeg count

        Returns:
            SmartOrderResult indicating success

        """
        self.order_tracker.update_order(
            order_id, executed_order.order_id, new_price, datetime.now(UTC)
        )

        # Use structured logging for repeg operation
        log_repeg_operation(
            logger,
            operation="replace_order",
            symbol=request.symbol,
            old_price=original_anchor,
            new_price=new_price,
            quantity=remaining_qty,
            reason="unfilled_order",
            new_order_id=str(executed_order.order_id),
            original_order_id=order_id,
            repeg_attempt=new_repeg_count,
            max_repegs=self.config.max_repegs_per_order,
        )

        metadata_dict = self._create_repeg_metadata(order_id, original_anchor, new_price, quote)

        return SmartOrderResult(
            success=True,
            order_id=executed_order.order_id,
            final_price=new_price,
            anchor_price=original_anchor,
            repegs_used=new_repeg_count,
            execution_strategy=f"smart_repeg_{new_repeg_count}",
            placement_timestamp=datetime.now(UTC),
            metadata=metadata_dict,
        )

    def _handle_repeg_order_result(
        self,
        executed_order: OrderExecutionResult,
        order_id: str,
        request: SmartOrderRequest,
        new_price: Decimal,
        original_anchor: Decimal | None,
        quote: QuoteModel | None,
        remaining_qty: Decimal,
        new_repeg_count: int,
    ) -> SmartOrderResult:
        """Handle the result of a repeg order placement.

        Args:
            executed_order: Result from placing the new order
            order_id: Original order ID
            request: Original order request
            new_price: New limit price
            original_anchor: Original anchor price
            quote: Quote data used for pricing
            remaining_qty: Remaining quantity
            new_repeg_count: Current repeg count

        Returns:
            SmartOrderResult with success or failure status

        """
        # Check if placement succeeded and order_id looks valid (UUID)
        if not (
            getattr(executed_order, "success", False) and getattr(executed_order, "order_id", None)
        ):
            logger.error(
                "Re-peg failed, no valid order ID returned",
                symbol=request.symbol,
                correlation_id=request.correlation_id,
            )
            return SmartOrderResult(
                success=False,
                error_message="Re-peg order placement failed",
                execution_strategy="smart_repeg_failed",
                repegs_used=new_repeg_count,
            )

        if not self._is_valid_uuid_str(str(executed_order.order_id)):
            logger.warning(
                "Re-peg placement returned non-UUID order_id, skipping tracking update",
                order_id=str(executed_order.order_id),
                correlation_id=request.correlation_id,
            )
            return SmartOrderResult(
                success=False,
                error_message="Re-peg returned invalid order ID",
                execution_strategy="smart_repeg_failed",
                repegs_used=new_repeg_count,
            )

        return self._build_repeg_success_result(
            order_id,
            executed_order,
            request,
            new_price,
            original_anchor,
            quote,
            remaining_qty,
            new_repeg_count,
        )

    async def _attempt_repeg(
        self, order_id: str, request: SmartOrderRequest
    ) -> SmartOrderResult | bool | None:
        """Attempt to re-peg an order with a more aggressive price.

        Args:
            order_id: The order ID to re-peg
            request: Original order request

        Returns:
            SmartOrderResult if re-peg was attempted,
            False if skipped but should keep tracking,
            None if invalid and should be removed

        """
        try:
            remaining_qty = await self._get_remaining_after_status_update(order_id, request)

            if remaining_qty is None:
                return None

            # Ensure cancellation completes before re-peg
            if not await self._cancel_for_repeg(order_id, request):
                return False

            # Determine valid re-peg price and required context
            try:
                new_price, original_anchor, quote = self._calculate_repeg_price(order_id, request)
            except _RemoveFromTracking:
                return None

            if new_price is None:
                return False

            # Update tracking BEFORE placing new order to ensure count persistence
            old_repeg_count = self.order_tracker.get_repeg_count(order_id)
            new_repeg_count = old_repeg_count + 1

            logger.debug(
                "Re-pegging order with more aggressive price",
                symbol=request.symbol,
                correlation_id=request.correlation_id,
                side=request.side,
                original_price=original_anchor,
                new_price=new_price,
                attempt=new_repeg_count,
                max_repegs=self.config.max_repegs_per_order,
                remaining_qty=remaining_qty,
                original_qty=request.quantity,
            )

            # Ensure price is properly quantized to avoid sub-penny precision errors
            quantized_price = new_price.quantize(PRICE_QUANTIZATION)

            if quantized_price <= 0:
                logger.error(
                    "Quantized re-peg price is invalid, skipping re-peg",
                    symbol=request.symbol,
                    correlation_id=request.correlation_id,
                    quantized_price=quantized_price,
                )
                return False

            # Place order (with retry on insufficient qty)
            try:
                executed_order = await self._place_limit_with_insufficient_retry(
                    request, remaining_qty, quantized_price
                )
            except _RemoveFromTracking:
                return None

            return self._handle_repeg_order_result(
                executed_order,
                order_id,
                request,
                quantized_price,
                original_anchor,
                quote,
                remaining_qty,
                new_repeg_count,
            )

        except (OrderExecutionError, asyncio.TimeoutError) as e:
            logger.error(
                "Error during re-peg attempt",
                order_id=order_id,
                correlation_id=request.correlation_id,
                error=str(e),
                exc_info=True,
            )
            return SmartOrderResult(
                success=False,
                error_message=str(e),
                execution_strategy="smart_repeg_error",
            )

    async def _get_remaining_after_status_update(
        self, order_id: str, request: SmartOrderRequest
    ) -> Decimal | None:
        """Fetch current order status, update filled quantity, and compute remaining.

        Returns None when remaining is below the minimal threshold, meaning the
        order can be considered complete and removed from tracking.
        """
        logger.debug(
            "Checking current status of order before re-peg",
            order_id=order_id,
            correlation_id=request.correlation_id,
        )
        order_result = await asyncio.to_thread(
            self.alpaca_manager.get_order_execution_result, order_id
        )

        filled_qty = (
            order_result.filled_qty if hasattr(order_result, "filled_qty") else Decimal("0")
        )
        self.order_tracker.update_filled_quantity(order_id, filled_qty)

        remaining_qty = self.order_tracker.get_remaining_quantity(order_id)

        logger.info(
            "Order status before re-peg",
            order_id=order_id,
            correlation_id=request.correlation_id,
            original_qty=request.quantity,
            filled_qty=filled_qty,
            remaining_qty=remaining_qty,
        )

        # Check if remaining is too small to pursue
        if self._should_remove_due_to_small_remaining(order_id, request, remaining_qty):
            return None

        return remaining_qty

    def _should_remove_due_to_small_remaining(
        self, order_id: str, request: SmartOrderRequest, remaining_qty: Decimal
    ) -> bool:
        """Check if remaining quantity is too small and order should be removed.

        Args:
            order_id: Order ID for logging
            request: Original order request
            remaining_qty: Remaining quantity to check

        Returns:
            True if order should be removed from tracking due to small remaining

        """
        try:
            asset_info = self.alpaca_manager.get_asset_info(request.symbol)
            price = fetch_price_for_notional_check(
                request.symbol, request.side, self.quote_provider, self.alpaca_manager
            )
            min_notional = getattr(self.config, "min_fractional_notional_usd", Decimal("1.00"))

            if is_remaining_quantity_too_small(remaining_qty, asset_info, price, min_notional):
                self._log_small_remaining_removal(
                    order_id, request, remaining_qty, asset_info, price, min_notional
                )
                return True
        except Exception as _small_e:
            logger.debug(
                "Minimal-remaining evaluation fallback due to error",
                order_id=order_id,
                correlation_id=request.correlation_id,
                error=str(_small_e),
            )

        return False

    def _log_small_remaining_removal(
        self,
        order_id: str,
        request: SmartOrderRequest,
        remaining_qty: Decimal,
        asset_info: object | None,
        price: Decimal | None,
        min_notional: Decimal,
    ) -> None:
        """Log removal of order due to small remaining quantity.

        Args:
            order_id: Order ID
            request: Original order request
            remaining_qty: Remaining quantity
            asset_info: Asset info with fractionable attribute
            price: Current price
            min_notional: Minimum notional value

        """
        if (
            asset_info is not None
            and getattr(asset_info, "fractionable", False)
            and price is not None
        ):
            remaining_notional = (remaining_qty * price).quantize(PRICE_QUANTIZATION)
            logger.info(
                "Order remaining notional below minimum, considering complete",
                order_id=order_id,
                correlation_id=request.correlation_id,
                remaining_notional=remaining_notional,
                min_notional=min_notional,
            )
        else:
            logger.info(
                "Order remaining non-fractionable quantity rounds to 0, considering complete",
                order_id=order_id,
                correlation_id=request.correlation_id,
            )

    async def _cancel_for_repeg(self, order_id: str, request: SmartOrderRequest) -> bool:
        """Cancel the existing order and wait until cancellation is confirmed.

        Returns True only when cancellation completes; otherwise False.
        """
        logger.info(
            "Canceling order for re-pegging",
            order_id=order_id,
            correlation_id=request.correlation_id,
        )
        cancel_result = await asyncio.to_thread(self.alpaca_manager.cancel_order, order_id)

        # Check if order was already in a terminal state (e.g., filled, cancelled)
        is_terminal, terminal_error = self._is_order_in_terminal_state(cancel_result)
        if is_terminal and terminal_error:
            # Extract just the state name (e.g., "filled" from "already_filled")
            terminal_state = terminal_error.value.replace("already_", "")
            logger.info(
                "Order already in terminal state, no re-peg needed",
                order_id=order_id,
                correlation_id=request.correlation_id,
                terminal_state=terminal_state,
            )
            # Signal to remove from tracking - order is complete
            raise _RemoveFromTracking()

        if not cancel_result.success:
            logger.warning(
                "Failed to cancel order, skipping re-peg",
                order_id=order_id,
                correlation_id=request.correlation_id,
            )
            return False

        logger.debug(
            "Waiting for order cancellation to complete",
            order_id=order_id,
            correlation_id=request.correlation_id,
        )
        cancellation_confirmed = await asyncio.to_thread(
            self._wait_for_order_cancellation, order_id
        )
        if not cancellation_confirmed:
            logger.warning(
                "Order cancellation did not complete within timeout, skipping re-peg",
                order_id=order_id,
                correlation_id=request.correlation_id,
            )
            return False

        logger.debug(
            "Order cancellation confirmed, buying power released",
            order_id=order_id,
            correlation_id=request.correlation_id,
        )
        return True

    def _calculate_repeg_price(
        self, order_id: str, request: SmartOrderRequest
    ) -> tuple[Decimal | None, Decimal | None, QuoteModel | None]:
        """Calculate a valid re-peg price and return context.

        Returns (new_price, original_anchor, quote).
        - If quote is missing or price cannot be calculated, returns (None, original_anchor, quote_placeholder)
        - If price is invalid (<= $0.01), raises _RemoveFromTracking to signal removal
        """
        validated = self.quote_provider.get_quote_with_validation(request.symbol)
        if not validated:
            logger.warning(
                "No valid quote available, skipping re-peg",
                symbol=request.symbol,
                correlation_id=request.correlation_id,
            )
            return None, self.order_tracker.get_anchor_price(order_id), None

        quote, _ = validated
        original_anchor = self.order_tracker.get_anchor_price(order_id)
        price_history = self.order_tracker.get_price_history(order_id)
        new_price = self.pricing_calculator.calculate_repeg_price(
            quote, request.side, original_anchor, price_history
        )

        if not new_price:
            logger.warning(
                "Cannot calculate re-peg price",
                symbol=request.symbol,
                correlation_id=request.correlation_id,
            )
            return None, original_anchor, quote

        if new_price <= MIN_VALID_PRICE:
            logger.error(
                "Invalid re-peg price, must be > $0.01, skipping re-peg",
                symbol=request.symbol,
                correlation_id=request.correlation_id,
                side=request.side,
                new_price=new_price,
            )
            raise _RemoveFromTracking()

        return new_price, original_anchor, quote

    async def _place_limit_with_insufficient_retry(
        self, request: SmartOrderRequest, quantity: Decimal, limit_price: Decimal
    ) -> OrderExecutionResult:
        """Place a limit order, retrying with available qty when broker reports insufficiency.

        Raises _RemoveFromTracking if the available quantity reported is below the minimal threshold.
        """
        try:
            return await asyncio.to_thread(
                self.alpaca_manager.place_limit_order,
                symbol=request.symbol,
                side=request.side.lower(),
                quantity=float(quantity),
                limit_price=float(limit_price),
                time_in_force="day",
            )
        except Exception as e:
            if self._is_insufficient_quantity_error(str(e)):
                return await self._handle_insufficient_quantity_retry(
                    request, quantity, limit_price, str(e)
                )
            raise e

    def _is_insufficient_quantity_error(self, error_str: str) -> bool:
        """Check if error indicates insufficient quantity available."""
        return "insufficient qty available" in error_str.lower()

    def _extract_available_quantity(self, error_str: str) -> Decimal | None:
        """Extract available quantity from broker error message."""
        import re

        available_match = re.search(r"available: ([\d.]+)", error_str)
        if available_match:
            try:
                return Decimal(available_match.group(1))
            except (ValueError, ArithmeticError):
                return None
        return None

    async def _handle_insufficient_quantity_retry(
        self,
        request: SmartOrderRequest,
        requested_quantity: Decimal,
        limit_price: Decimal,
        error_str: str,
    ) -> OrderExecutionResult:
        """Handle retry with available quantity when broker reports insufficiency."""
        logger.warning(
            "Insufficient quantity available for order",
            symbol=request.symbol,
            correlation_id=request.correlation_id,
            requested_quantity=requested_quantity,
            error=error_str,
        )

        available_qty = self._extract_available_quantity(error_str)
        if available_qty is None:
            raise OrderExecutionError(
                f"Failed to extract available quantity from broker error: {error_str}",
                symbol=request.symbol,
                order_type="limit",
                quantity=float(requested_quantity),
                price=float(limit_price),
            )

        return await self._retry_with_available_quantity(
            request, available_qty, limit_price, error_str
        )

    async def _retry_with_available_quantity(
        self,
        request: SmartOrderRequest,
        available_qty: Decimal,
        limit_price: Decimal,
        original_error: str,
    ) -> OrderExecutionResult:
        """Retry order placement with the available quantity."""
        if available_qty <= MIN_QUANTITY_THRESHOLD:
            logger.info(
                "Available quantity too small, considering order complete",
                available_qty=available_qty,
                correlation_id=request.correlation_id,
            )
            raise _RemoveFromTracking()

        logger.info(
            "Retrying re-peg with available quantity",
            available_qty=available_qty,
            correlation_id=request.correlation_id,
        )

        try:
            return await asyncio.to_thread(
                self.alpaca_manager.place_limit_order,
                symbol=request.symbol,
                side=request.side.lower(),
                quantity=float(available_qty),
                limit_price=float(limit_price),
                time_in_force="day",
            )
        except (OrderExecutionError, asyncio.TimeoutError) as retry_e:
            logger.error(
                "Retry with available quantity failed",
                correlation_id=request.correlation_id,
                error=str(retry_e),
                exc_info=True,
            )
            raise OrderExecutionError(
                f"Retry with available quantity failed after insufficient quantity error: {original_error}",
                symbol=request.symbol,
                order_type="limit",
                quantity=float(available_qty),
                price=float(limit_price),
            )

    def _is_valid_uuid_str(self, value: str) -> bool:
        """Check if provided string is a valid UUID format."""
        try:
            import uuid as _uuid

            _uuid.UUID(value)
            return True
        except (ValueError, AttributeError):
            return False

    def _wait_for_order_cancellation(
        self, order_id: str, timeout_seconds: float = DEFAULT_CANCELLATION_TIMEOUT_SECONDS
    ) -> bool:
        """Wait for an order to be actually cancelled and buying power released.

        This prevents the race condition where we try to place a replacement order
        before the cancelled order has fully released its reserved buying power.

        Args:
            order_id: Order ID to wait for cancellation
            timeout_seconds: Maximum time to wait for cancellation

        Returns:
            True if order was confirmed cancelled, False if timeout or error

        """
        import time

        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            try:
                order_status = self.alpaca_manager._check_order_completion_status(order_id)

                if order_status and order_status.upper() in [
                    "CANCELED",
                    "CANCELLED",
                    "EXPIRED",
                    "REJECTED",
                ]:
                    logger.debug(
                        "Order confirmed cancelled",
                        order_id=order_id,
                        status=order_status,
                    )
                    return True

                # Small delay to avoid hammering the API
                time.sleep(CANCELLATION_CHECK_INTERVAL_SECONDS)

            except Exception as e:
                logger.warning(
                    "Error checking cancellation status",
                    order_id=order_id,
                    error=str(e),
                )
                # Continue trying until timeout
                time.sleep(CANCELLATION_CHECK_INTERVAL_SECONDS)

        logger.warning(
            "Timeout waiting for order cancellation",
            order_id=order_id,
            timeout_seconds=timeout_seconds,
        )
        return False
