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
                logger.info(
                    f"⚠️ Order {order_id} reached max re-pegs "
                    f"({current_repeg_count}/{self.config.max_repegs_per_order}), escalating to market order"
                )
                return await self._escalate_to_market(order_id, request)

            # Attempt re-pegging
            placement_time = self.order_tracker.get_placement_time(order_id)
            if placement_time:
                time_elapsed = (current_time - placement_time).total_seconds()
                logger.info(
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
            logger.info(f"📊 Order {order_id} completed with status: {order_status}")
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
            logger.info(
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
            # Cancel the existing order
            logger.info(f"❌ Canceling order {order_id} for re-pegging")
            # Use asyncio.to_thread to make blocking I/O async
            cancel_success = await asyncio.to_thread(self.alpaca_manager.cancel_order, order_id)

            if not cancel_success:
                logger.warning(f"⚠️ Failed to cancel order {order_id}, skipping re-peg")
                return False

            # Get current market data
            validated = self.quote_provider.get_quote_with_validation(request.symbol)
            if not validated:
                logger.warning(f"⚠️ No valid quote for {request.symbol}, skipping re-peg")
                return False

            quote, _ = validated

            # Calculate more aggressive price for re-peg
            original_anchor = self.order_tracker.get_anchor_price(order_id)
            price_history = self.order_tracker.get_price_history(order_id)
            new_price = self.pricing_calculator.calculate_repeg_price(
                quote, request.side, original_anchor, price_history
            )

            if not new_price:
                logger.warning(f"⚠️ Cannot calculate re-peg price for {request.symbol}")
                return False

            # Additional validation to ensure price is positive and reasonable
            if new_price <= Decimal("0.01"):
                logger.error(
                    f"⚠️ Invalid re-peg price ${new_price} for {request.symbol} {request.side}, "
                    f"price must be > $0.01. Skipping re-peg."
                )
                return None

            # Update tracking BEFORE placing new order to ensure count persistence
            old_repeg_count = self.order_tracker.get_repeg_count(order_id)
            new_repeg_count = old_repeg_count + 1

            logger.info(
                f"📈 Re-pegging {request.symbol} {request.side} from "
                f"${original_anchor} to ${new_price} (attempt {new_repeg_count}/{self.config.max_repegs_per_order})"
            )

            # Ensure price is properly quantized to avoid sub-penny precision errors
            quantized_price = new_price.quantize(Decimal("0.01"))

            # Final validation before placing order
            if quantized_price <= 0:
                logger.error(
                    f"⚠️ Quantized re-peg price ${quantized_price} is invalid for {request.symbol}. "
                    f"This should not happen after validation - skipping re-peg."
                )
                return False

            # Use asyncio.to_thread to make blocking I/O async
            executed_order = await asyncio.to_thread(
                self.alpaca_manager.place_limit_order,
                symbol=request.symbol,
                side=request.side.lower(),
                quantity=float(request.quantity),
                limit_price=float(quantized_price),
                time_in_force="day",
            )

            # Only proceed if placement succeeded and order_id looks valid (UUID)
            if getattr(executed_order, "success", False) and executed_order.order_id:
                is_valid_uuid = False
                try:
                    import uuid as _uuid

                    _uuid.UUID(str(executed_order.order_id))
                    is_valid_uuid = True
                except Exception:
                    is_valid_uuid = False

                if is_valid_uuid:
                    # Update tracking with new order ID and preserve count
                    self.order_tracker.update_order(
                        order_id, executed_order.order_id, new_price, datetime.now(UTC)
                    )

                    logger.info(
                        f"✅ Re-peg successful: new order {executed_order.order_id} "
                        f"at ${new_price} (attempt {new_repeg_count}/{self.config.max_repegs_per_order})"
                    )

                    metadata_dict: LiquidityMetadata = {
                        "original_order_id": order_id,
                        "original_price": (float(original_anchor) if original_anchor else None),
                        "new_price": float(new_price),
                        "bid_price": quote.bid_price,
                        "ask_price": quote.ask_price,
                        "spread_percent": (quote.ask_price - quote.bid_price)
                        / quote.bid_price
                        * 100,
                        "bid_size": quote.bid_size,
                        "ask_size": quote.ask_size,
                    }
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
                logger.warning(
                    "⚠️ Re-peg placement returned non-UUID order_id; skipping tracking update"
                )
                return SmartOrderResult(
                    success=False,
                    error_message="Re-peg returned invalid order ID",
                    execution_strategy="smart_repeg_failed",
                    repegs_used=new_repeg_count,
                )

            # If we get here, placement did not succeed or no order_id
            logger.error(f"❌ Re-peg failed for {request.symbol}: no valid order ID returned")
            return SmartOrderResult(
                success=False,
                error_message="Re-peg order placement failed",
                execution_strategy="smart_repeg_failed",
                repegs_used=new_repeg_count,
            )

        except Exception as e:
            logger.error(f"❌ Error during re-peg attempt for {order_id}: {e}")
            return SmartOrderResult(
                success=False,
                error_message=str(e),
                execution_strategy="smart_repeg_error",
            )
