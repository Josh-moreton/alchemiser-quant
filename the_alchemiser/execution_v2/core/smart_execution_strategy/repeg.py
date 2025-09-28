"""Business Unit: execution | Status: current.

Re-pegging and escalation logic for smart execution strategy.

This module handles the re-pegging of unfilled orders and escalation to market
orders when maximum re-peg attempts are reached.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from decimal import Decimal

from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.schemas.broker import OrderExecutionResult
from the_alchemiser.shared.types.exceptions import OrderExecutionError
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

logger = logging.getLogger(__name__)


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

            # Check if we've reached max re-pegs — escalate to market
            if self._should_escalate_order(current_repeg_count):
                logger.warning(
                    f"⚠️ Order {order_id} reached max re-pegs "
                    f"({current_repeg_count}/{self.config.max_repegs_per_order}), escalating to market order"
                )
                return await self._escalate_to_market(order_id, request)

            # Attempt re-pegging
            placement_time = self.order_tracker.get_placement_time(order_id)
            if placement_time:
                time_elapsed = (current_time - placement_time).total_seconds()
                logger.debug(
                    f"🔄 Order {order_id} hasn't filled after {time_elapsed:.1f}s, "
                    f"attempting re-peg (attempt {current_repeg_count + 1}/{self.config.max_repegs_per_order})"
                )
            return await self._attempt_repeg(order_id, request)

        except Exception as e:
            logger.error(f"Error checking order {order_id} for re-pegging: {e}")
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
            logger.debug(f"📊 Order {order_id} completed with status: {order_status}")
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
            f"⏳ Order {order_id} waiting for fill "
            f"({time_elapsed:.1f}s/{self.config.fill_wait_seconds}s) - "
            f"repeg_count: {self.order_tracker.get_repeg_count(order_id)}"
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

    async def _escalate_to_market(
        self, order_id: str, request: SmartOrderRequest
    ) -> SmartOrderResult | None:
        """Cancel current limit order and place a market order (final escalation).

        Args:
            order_id: Existing limit order ID to cancel
            request: Original smart order request details

        Returns:
            SmartOrderResult describing the escalation outcome, or None if cancel failed

        """
        try:
            logger.debug(
                f"🛑 Escalating order {order_id} to market: canceling existing limit order "
                f"(after {self.order_tracker.get_repeg_count(order_id)} re-pegs)"
            )
            # Use asyncio.to_thread to make blocking I/O async
            cancel_success = await asyncio.to_thread(self.alpaca_manager.cancel_order, order_id)
            if not cancel_success:
                logger.warning(
                    f"⚠️ Failed to cancel order {order_id}; attempting market order anyway"
                )
                # Don't return None - still try market order as the limit order might fill/cancel
            else:
                # Wait for actual cancellation to complete and buying power to be released
                logger.debug(
                    f"⏳ Waiting for order {order_id} cancellation to complete before market escalation..."
                )
                cancellation_confirmed = await asyncio.to_thread(
                    self._wait_for_order_cancellation, order_id, timeout_seconds=10.0
                )

                if not cancellation_confirmed:
                    logger.warning(
                        f"⚠️ Order {order_id} cancellation did not complete within timeout, proceeding with market order anyway"
                    )
                else:
                    logger.debug(
                        f"✅ Order {order_id} cancellation confirmed, proceeding with market escalation"
                    )

            # Place market order
            logger.info(f"📈 Placing market order for {request.symbol} {request.side}")
            executed_order = await asyncio.to_thread(
                self.alpaca_manager.place_market_order,
                symbol=request.symbol,
                side=request.side.lower(),
                qty=float(request.quantity),
                is_complete_exit=request.is_complete_exit,
            )

            # Clean up old tracking regardless of outcome
            original_anchor = self.order_tracker.get_anchor_price(order_id)
            self.order_tracker.remove_order(order_id)

            # Successful placement if not rejected/canceled
            if executed_order.order_id and executed_order.status not in [
                "REJECTED",
                "CANCELED",
            ]:
                metadata: LiquidityMetadata = {
                    "original_order_id": order_id,
                    "original_price": (
                        float(original_anchor) if original_anchor is not None else None
                    ),
                    "new_price": (
                        float(executed_order.price) if executed_order.price is not None else 0.0
                    ),
                }
                logger.info(
                    f"✅ Market escalation successful: new order {executed_order.order_id} "
                    f"(escalated from {order_id} after {self.config.max_repegs_per_order} re-pegs)"
                )
                return SmartOrderResult(
                    success=True,
                    order_id=executed_order.order_id,
                    final_price=(
                        executed_order.price if executed_order.price is not None else None
                    ),
                    anchor_price=original_anchor,
                    repegs_used=self.config.max_repegs_per_order,
                    execution_strategy="market_escalation",
                    placement_timestamp=executed_order.execution_timestamp,
                    metadata=metadata,
                )

            # Placement failed
            logger.error(
                f"❌ Market escalation failed for {request.symbol}: status={executed_order.status}"
            )
            return SmartOrderResult(
                success=False,
                order_id=executed_order.order_id,
                error_message=getattr(executed_order, "error_message", None)
                or "Market escalation placement failed",
                execution_strategy="market_escalation_failed",
                placement_timestamp=executed_order.execution_timestamp,
            )
        except Exception as exc:
            logger.error(f"❌ Error during market escalation for {order_id}: {exc}")
            return SmartOrderResult(
                success=False,
                error_message=str(exc),
                execution_strategy="market_escalation_error",
            )

    async def _attempt_repeg(
        self, order_id: str, request: SmartOrderRequest
    ) -> SmartOrderResult | bool | None:
        """Attempt to re-peg an order with a more aggressive price using replace functionality.

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

            # Determine valid re-peg price and required context
            try:
                new_price, original_anchor, quote = self._calculate_repeg_price(order_id, request)
            except _RemoveFromTracking:
                return None

            if new_price is None:
                return False

            # Update tracking BEFORE replacing order to ensure count persistence
            old_repeg_count = self.order_tracker.get_repeg_count(order_id)
            new_repeg_count = old_repeg_count + 1

            logger.debug(
                f"📈 Re-pegging {request.symbol} {request.side} from "
                f"${original_anchor} to ${new_price} (attempt {new_repeg_count}/{self.config.max_repegs_per_order}) "
                f"with remaining quantity {remaining_qty} (original: {request.quantity})"
            )

            # Ensure price is properly quantized to avoid sub-penny precision errors
            quantized_price = new_price.quantize(Decimal("0.01"))

            if quantized_price <= 0:
                logger.error(
                    f"⚠️ Quantized re-peg price ${quantized_price} is invalid for {request.symbol}. "
                    f"This should not happen after validation - skipping re-peg."
                )
                return False

            # Use replace functionality instead of cancel+resend
            replace_result = await self._replace_for_repeg(order_id, quantized_price, remaining_qty)
            
            if replace_result and replace_result.success:
                # Update order tracking with the same order ID (replaced in-place)
                self.order_tracker.update_order(
                    order_id, order_id, quantized_price, datetime.now(UTC)
                )

                logger.info(
                    f"✅ Re-peg successful: replaced order {order_id} "
                    f"at ${quantized_price} (attempt {new_repeg_count}/{self.config.max_repegs_per_order}) "
                    f"quantity: {remaining_qty}"
                )

                # Use cast to satisfy type checkers; quote is non-None when new_price exists
                from typing import cast as _cast

                q = _cast(QuoteModel, quote)
                metadata_dict: LiquidityMetadata = {
                    "original_order_id": order_id,
                    "original_price": (float(original_anchor) if original_anchor else None),
                    "new_price": float(quantized_price),
                    "bid_price": q.bid_price,
                    "ask_price": q.ask_price,
                    "spread_percent": (q.ask_price - q.bid_price) / q.bid_price * 100,
                    "bid_size": q.bid_size,
                    "ask_size": q.ask_size,
                }
                return SmartOrderResult(
                    success=True,
                    order_id=order_id,  # Same order ID since we replaced in-place
                    final_price=quantized_price,
                    anchor_price=original_anchor,
                    repegs_used=new_repeg_count,
                    execution_strategy=f"replace_repeg_{new_repeg_count}",
                    placement_timestamp=datetime.now(UTC),
                    metadata=metadata_dict,
                )
            else:
                logger.error(f"❌ Re-peg replacement failed for {request.symbol}")
                return SmartOrderResult(
                    success=False,
                    error_message="Re-peg order replacement failed",
                    execution_strategy="replace_repeg_failed",
                    repegs_used=new_repeg_count,
                )

        except Exception as e:
            logger.error(f"❌ Error during re-peg attempt for {order_id}: {e}")
            return SmartOrderResult(
                success=False,
                error_message=str(e),
                execution_strategy="replace_repeg_error",
            )

    async def _get_remaining_after_status_update(
        self, order_id: str, request: SmartOrderRequest
    ) -> Decimal | None:
        """Fetch current order status, update filled quantity, and compute remaining.

        Returns None when remaining is below the minimal threshold, meaning the
        order can be considered complete and removed from tracking.
        """
        logger.debug(f"🔍 Checking current status of order {order_id} before re-peg")
        order_result = await asyncio.to_thread(
            self.alpaca_manager.get_order_execution_result, order_id
        )

        filled_qty = (
            order_result.filled_qty if hasattr(order_result, "filled_qty") else Decimal("0")
        )
        self.order_tracker.update_filled_quantity(order_id, filled_qty)

        remaining_qty = self.order_tracker.get_remaining_quantity(order_id)

        logger.info(
            f"📊 Order {order_id} status before re-peg: "
            f"original={request.quantity}, filled={filled_qty}, remaining={remaining_qty}"
        )

        min_qty_threshold = Decimal("0.01")
        if remaining_qty <= min_qty_threshold:
            logger.info(
                f"✅ Order {order_id} has minimal remaining quantity ({remaining_qty}), considering complete"
            )
            return None

        return remaining_qty

    async def _replace_for_repeg(
        self, order_id: str, new_price: Decimal, remaining_qty: Decimal
    ) -> SmartOrderResult | None:
        """Replace an existing order with new price and quantity using Alpaca replace functionality.

        Args:
            order_id: The order ID to replace
            new_price: The new limit price
            remaining_qty: The remaining quantity to replace with

        Returns:
            SmartOrderResult if replacement was successful, None if failed
        """
        try:
            logger.info(f"🔄 Replacing order {order_id} with new price ${new_price} and quantity {remaining_qty}")
            
            # Use the replace order functionality
            result = await asyncio.to_thread(
                self.alpaca_manager.replace_order_by_id,
                order_id=order_id,
                quantity=float(remaining_qty),
                limit_price=float(new_price),
                time_in_force="day"  # Keep the same time in force
            )
            
            if result.success:
                logger.info(f"✅ Successfully replaced order {order_id} -> {result.order_id} at ${new_price}")
                return SmartOrderResult(
                    success=True,
                    order_id=result.order_id,
                    final_price=new_price,
                    execution_strategy="replace_repeg",
                    placement_timestamp=datetime.now(UTC),
                )
            else:
                logger.warning(f"⚠️ Order replacement failed for {order_id}: {result.error_message}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error during order replacement for {order_id}: {e}")
            return None

    async def _cancel_for_repeg(self, order_id: str) -> bool:
        """Cancel the existing order and wait until cancellation is confirmed.

        Returns True only when cancellation completes; otherwise False.
        """
        logger.info(f"❌ Canceling order {order_id} for re-pegging")
        cancel_success = await asyncio.to_thread(self.alpaca_manager.cancel_order, order_id)
        if not cancel_success:
            logger.warning(f"⚠️ Failed to cancel order {order_id}, skipping re-peg")
            return False

        logger.debug(f"⏳ Waiting for order {order_id} cancellation to complete...")
        cancellation_confirmed = await asyncio.to_thread(
            self._wait_for_order_cancellation, order_id, timeout_seconds=10.0
        )
        if not cancellation_confirmed:
            logger.warning(
                f"⚠️ Order {order_id} cancellation did not complete within timeout, skipping re-peg"
            )
            return False

        logger.debug(f"✅ Order {order_id} cancellation confirmed, buying power released")
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
            logger.warning(f"⚠️ No valid quote for {request.symbol}, skipping re-peg")
            return None, self.order_tracker.get_anchor_price(order_id), None

        quote, _ = validated
        original_anchor = self.order_tracker.get_anchor_price(order_id)
        price_history = self.order_tracker.get_price_history(order_id)
        new_price = self.pricing_calculator.calculate_repeg_price(
            quote, request.side, original_anchor, price_history
        )

        if not new_price:
            logger.warning(f"⚠️ Cannot calculate re-peg price for {request.symbol}")
            return None, original_anchor, quote

        if new_price <= Decimal("0.01"):
            logger.error(
                f"⚠️ Invalid re-peg price ${new_price} for {request.symbol} {request.side}, price must be > $0.01. Skipping re-peg."
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
            except Exception:
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
            f"⚠️ Insufficient quantity available for {request.symbol}. Requested: {requested_quantity}, Error: {error_str}"
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
        min_qty_threshold = Decimal("0.01")

        if available_qty <= min_qty_threshold:
            logger.info(
                f"✅ Available quantity {available_qty} too small, considering order complete"
            )
            raise _RemoveFromTracking()

        logger.info(f"🔄 Retrying re-peg with available quantity: {available_qty}")

        try:
            return await asyncio.to_thread(
                self.alpaca_manager.place_limit_order,
                symbol=request.symbol,
                side=request.side.lower(),
                quantity=float(available_qty),
                limit_price=float(limit_price),
                time_in_force="day",
            )
        except Exception as retry_e:
            logger.error(f"❌ Retry with available quantity failed: {retry_e}")
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
        except Exception:
            return False

    def _wait_for_order_cancellation(self, order_id: str, timeout_seconds: float = 10.0) -> bool:
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
        check_interval = 0.1  # Check every 100ms

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
                        f"✅ Order {order_id} confirmed cancelled with status: {order_status}"
                    )
                    return True

                # Small delay to avoid hammering the API
                time.sleep(check_interval)

            except Exception as e:
                logger.warning(f"Error checking cancellation status for {order_id}: {e}")
                # Continue trying until timeout
                time.sleep(check_interval)

        logger.warning(
            f"⚠️ Timeout waiting for order {order_id} cancellation after {timeout_seconds}s"
        )
        return False
