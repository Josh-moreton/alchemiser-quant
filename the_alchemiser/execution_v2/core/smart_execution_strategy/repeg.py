"""Business Unit: execution | Status: current.

Re-pegging and escalation logic for smart execution strategy.

This module handles the re-pegging of unfilled orders and escalation to market
orders when maximum re-peg attempts are reached.
"""

from __future__ import annotations

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
        orders_to_remove = []
        current_time = datetime.now(UTC)

        for order_id, request in list(active_orders.items()):
            try:
                # Check if order is still active
                order_status = self.alpaca_manager._check_order_completion_status(
                    order_id
                )
                if order_status in ["FILLED", "CANCELED", "REJECTED", "EXPIRED"]:
                    orders_to_remove.append(order_id)
                    logger.info(
                        f"📊 Order {order_id} completed with status: {order_status}"
                    )
                    continue

                # Check if enough time has passed to consider re-pegging
                placement_time = self.order_tracker.get_placement_time(order_id)
                if not placement_time:
                    continue

                time_elapsed = (current_time - placement_time).total_seconds()
                if time_elapsed < self.config.fill_wait_seconds:
                    logger.debug(
                        f"⏳ Order {order_id} waiting for fill "
                        f"({time_elapsed:.1f}s/{self.config.fill_wait_seconds}s) - "
                        f"repeg_count: {self.order_tracker.get_repeg_count(order_id)}"
                    )
                    continue

                current_repeg_count = self.order_tracker.get_repeg_count(order_id)

                # Check if we've reached max re-pegs — escalate to market
                if current_repeg_count >= self.config.max_repegs_per_order:
                    logger.info(
                        f"⚠️ Order {order_id} reached max re-pegs "
                        f"({current_repeg_count}/{self.config.max_repegs_per_order}), escalating to market order"
                    )
                    escalation_result = await self._escalate_to_market(
                        order_id, request
                    )
                    if escalation_result is not None:
                        repeg_results.append(escalation_result)
                    # After escalation, skip further processing for this order_id
                    continue

                # Attempt re-pegging
                logger.info(
                    f"🔄 Order {order_id} hasn't filled after {time_elapsed:.1f}s, "
                    f"attempting re-peg (attempt {current_repeg_count + 1}/{self.config.max_repegs_per_order})"
                )
                repeg_result = await self._attempt_repeg(order_id, request)

                if repeg_result:
                    repeg_results.append(repeg_result)

            except Exception as e:
                logger.error(f"Error checking order {order_id} for re-pegging: {e}")

        # Clean up completed orders
        for order_id in orders_to_remove:
            self.order_tracker.remove_order(order_id)

        return repeg_results

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
            cancel_success = self.alpaca_manager.cancel_order(order_id)
            if not cancel_success:
                logger.warning(
                    f"⚠️ Failed to cancel order {order_id}; attempting market order anyway"
                )
                # Don't return None - still try market order as the limit order might fill/cancel

            # Place market order
            logger.info(f"📈 Placing market order for {request.symbol} {request.side}")
            executed_order = self.alpaca_manager.place_market_order(
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
                        float(executed_order.price)
                        if executed_order.price is not None
                        else 0.0
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
                        executed_order.price
                        if executed_order.price is not None
                        else None
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
    ) -> SmartOrderResult | None:
        """Attempt to re-peg an order with a more aggressive price.

        Args:
            order_id: The order ID to re-peg
            request: Original order request

        Returns:
            SmartOrderResult if re-peg was attempted, None if skipped

        """
        try:
            # Cancel the existing order
            logger.info(f"❌ Canceling order {order_id} for re-pegging")
            cancel_success = self.alpaca_manager.cancel_order(order_id)

            if not cancel_success:
                logger.warning(f"⚠️ Failed to cancel order {order_id}, skipping re-peg")
                return None

            # Get current market data
            validated = self.quote_provider.get_quote_with_validation(
                request.symbol, float(request.quantity)
            )
            if not validated:
                logger.warning(
                    f"⚠️ No valid quote for {request.symbol}, skipping re-peg"
                )
                return None

            quote, _ = validated

            # Calculate more aggressive price for re-peg
            original_anchor = self.order_tracker.get_anchor_price(order_id)
            new_price = self.pricing_calculator.calculate_repeg_price(
                quote, request.side, original_anchor
            )

            if not new_price:
                logger.warning(f"⚠️ Cannot calculate re-peg price for {request.symbol}")
                return None

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
                return None

            executed_order = self.alpaca_manager.place_limit_order(
                symbol=request.symbol,
                side=request.side.lower(),
                quantity=float(request.quantity),
                limit_price=float(quantized_price),
                time_in_force="day",
            )

            if executed_order.order_id:
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
                    "original_price": (
                        float(original_anchor) if original_anchor else None
                    ),
                    "new_price": float(new_price),
                    "bid_price": quote.bid_price,
                    "ask_price": quote.ask_price,
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

            # If we get here, re-peg failed (no order ID returned)
            logger.error(f"❌ Re-peg failed for {request.symbol}: no order ID returned")
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
