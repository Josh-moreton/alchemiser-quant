"""Business Unit: execution | Status: current.

Walk-the-book order placement strategy with explicit price progression.

Implements a clear, testable strategy for placing limit orders that progressively
move toward market price before finally using a market order.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from the_alchemiser.shared.logging import get_logger

if TYPE_CHECKING:
    from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
    from the_alchemiser.shared.schemas.execution_report import ExecutedOrder

    from .order_intent import OrderIntent
    from .quote_service import QuoteResult

logger = get_logger(__name__)

# Price progression configuration
PRICE_STEPS = [0.75, 0.85, 0.95]  # Percentages toward aggressive side
# Reduced from 30s to 10s - 30s per step was too long and resulted in poor execution
# in volatile markets. 10s gives market time to fill while not leaving orders stale.
DEFAULT_STEP_WAIT_SECONDS = 10  # How long to wait at each step before moving to next
DEFAULT_CANCELLATION_TIMEOUT_SECONDS = 10.0
MINIMUM_VALID_PRICE = Decimal("0.01")


class OrderStatus(str, Enum):
    """Status of an order in the walk-the-book progression."""

    PENDING = "pending"  # Order submitted, waiting for fill
    PARTIALLY_FILLED = "partially_filled"  # Some quantity filled
    FILLED = "filled"  # Fully filled
    CANCELLED = "cancelled"  # Cancelled by us for next step
    REJECTED = "rejected"  # Rejected by broker
    FAILED = "failed"  # Failed to submit


@dataclass(frozen=True)
class OrderAttempt:
    """Record of a single order attempt in the progression.

    Attributes:
        step: Which step this was (0=initial, 1=first reprice, etc.)
        price: Limit price used
        quantity: Quantity attempted
        order_id: Alpaca order ID
        timestamp: When order was placed
        status: Final status of this attempt
        filled_quantity: How much was filled
        avg_fill_price: Average fill price

    """

    step: int
    price: Decimal
    quantity: Decimal
    order_id: str | None
    timestamp: datetime
    status: OrderStatus
    filled_quantity: Decimal
    avg_fill_price: Decimal | None


@dataclass
class WalkResult:
    """Result of the walk-the-book execution.

    Attributes:
        success: Whether the order was successfully filled
        order_attempts: List of all order attempts made
        final_order_id: Final Alpaca order ID
        total_filled: Total quantity filled across all attempts
        avg_fill_price: Average fill price across all fills
        error_message: Error message if failed

    """

    success: bool
    order_attempts: list[OrderAttempt]
    final_order_id: str | None
    total_filled: Decimal
    avg_fill_price: Decimal | None
    error_message: str | None = None

    @property
    def num_steps_used(self) -> int:
        """Number of steps that were attempted."""
        return len(self.order_attempts)


class WalkTheBookStrategy:
    """Strategy for placing limit orders with progressive price improvement.

    This implements an explicit "walk the book" strategy:
        1. Start with limit order at 75% toward aggressive side
        2. If not filled after wait period, cancel and replace at 85%
        3. If still not filled, cancel and replace at 95%
        4. If still not filled, cancel and place market order

    For BUY orders:
        - Aggressive side = ask price
        - 75% = bid + 0.75 * (ask - bid)
        - Conservative (patient) to aggressive (market-crossing)

    For SELL orders:
        - Aggressive side = bid price
        - 75% = ask - 0.75 * (ask - bid)
        - Conservative (patient) to aggressive (market-crossing)

    """

    def __init__(
        self,
        alpaca_manager: AlpacaManager,
        *,
        step_wait_seconds: float = DEFAULT_STEP_WAIT_SECONDS,
        price_steps: list[float] | None = None,
    ) -> None:
        """Initialize walk-the-book strategy.

        Args:
            alpaca_manager: Alpaca broker manager for order operations
            step_wait_seconds: How long to wait at each price step
            price_steps: Custom price progression steps (default: [0.75, 0.85, 0.95])

        """
        self.alpaca_manager = alpaca_manager
        self.step_wait_seconds = step_wait_seconds
        self.price_steps = price_steps or PRICE_STEPS

        logger.debug(
            "WalkTheBookStrategy initialized",
            step_wait_seconds=step_wait_seconds,
            price_steps=self.price_steps,
        )

    async def execute(
        self,
        intent: OrderIntent,
        quote: QuoteResult,
    ) -> WalkResult:
        """Execute walk-the-book strategy for the given intent.

        Args:
            intent: Order intent to execute
            quote: Current market quote

        Returns:
            WalkResult with execution details

        """
        log_extra = {
            "symbol": intent.symbol,
            "side": intent.side.value,
            "quantity": str(intent.quantity),
            "correlation_id": intent.correlation_id,
        }

        logger.info(
            "Starting walk-the-book execution",
            **log_extra,
            steps=len(self.price_steps) + 1,  # +1 for final market order
        )

        order_attempts: list[OrderAttempt] = []
        remaining_quantity = intent.quantity
        total_filled = Decimal("0")
        weighted_fill_sum = Decimal("0")

        # Walk through each price step
        for step_index, price_ratio in enumerate(self.price_steps):
            # Calculate limit price for this step
            limit_price = self._calculate_limit_price(quote, intent.side.value, price_ratio)

            logger.info(
                f"Step {step_index + 1}/{len(self.price_steps)}: Placing limit order",
                **log_extra,
                limit_price=str(limit_price),
                price_ratio=price_ratio,
                remaining_quantity=str(remaining_quantity),
            )

            # Place limit order for this step
            attempt = await self._place_limit_order_step(
                intent=intent,
                limit_price=limit_price,
                quantity=remaining_quantity,
                step=step_index,
            )
            order_attempts.append(attempt)

            # Update filled totals
            if attempt.filled_quantity > 0:
                total_filled += attempt.filled_quantity
                remaining_quantity -= attempt.filled_quantity

                if attempt.avg_fill_price:
                    weighted_fill_sum += attempt.filled_quantity * attempt.avg_fill_price

            # Check if fully filled
            if remaining_quantity <= 0:
                avg_price = weighted_fill_sum / total_filled if total_filled > 0 else None
                logger.info(
                    "Order fully filled during walk-the-book",
                    **log_extra,
                    step=step_index + 1,
                    total_filled=str(total_filled),
                    avg_fill_price=str(avg_price) if avg_price else None,
                )
                return WalkResult(
                    success=True,
                    order_attempts=order_attempts,
                    final_order_id=attempt.order_id,
                    total_filled=total_filled,
                    avg_fill_price=avg_price,
                )

            # Check if order failed
            if attempt.status == OrderStatus.REJECTED:
                logger.error(
                    "Order rejected during walk-the-book",
                    **log_extra,
                    step=step_index + 1,
                )
                return WalkResult(
                    success=False,
                    order_attempts=order_attempts,
                    final_order_id=None,
                    total_filled=total_filled,
                    avg_fill_price=None,
                    error_message=f"Order rejected at step {step_index + 1}",
                )

            # Wait for this step's time period
            logger.debug(
                f"Waiting {self.step_wait_seconds}s for fill at step {step_index + 1}",
                **log_extra,
            )
            await asyncio.sleep(self.step_wait_seconds)

            # Check if filled during wait
            if attempt.order_id:
                status_result = await self._check_order_status(attempt.order_id)
                filled_qty = status_result["filled_quantity"]
                if filled_qty and filled_qty > 0:
                    additional_fill = filled_qty - attempt.filled_quantity
                    if additional_fill > 0:
                        total_filled += additional_fill
                        remaining_quantity -= additional_fill
                        if status_result["avg_fill_price"]:
                            weighted_fill_sum += additional_fill * status_result["avg_fill_price"]

                        logger.info(
                            "Additional fill during wait period",
                            **log_extra,
                            step=step_index + 1,
                            additional_fill=str(additional_fill),
                        )

                        if remaining_quantity <= 0:
                            avg_price = (
                                weighted_fill_sum / total_filled if total_filled > 0 else None
                            )
                            return WalkResult(
                                success=True,
                                order_attempts=order_attempts,
                                final_order_id=attempt.order_id,
                                total_filled=total_filled,
                                avg_fill_price=avg_price,
                            )

                # Cancel order before moving to next step
                if attempt.order_id:
                    await self._cancel_order(attempt.order_id, intent.correlation_id)

        # Final step: Market order
        logger.info(
            "Walk-the-book complete, escalating to market order",
            **log_extra,
            remaining_quantity=str(remaining_quantity),
        )

        market_attempt = await self._place_market_order_step(
            intent=intent,
            quantity=remaining_quantity,
            step=len(self.price_steps),
        )
        order_attempts.append(market_attempt)

        if market_attempt.filled_quantity > 0:
            total_filled += market_attempt.filled_quantity
            if market_attempt.avg_fill_price:
                weighted_fill_sum += market_attempt.filled_quantity * market_attempt.avg_fill_price

        avg_price = weighted_fill_sum / total_filled if total_filled > 0 else None

        success = market_attempt.status == OrderStatus.FILLED
        if success:
            logger.info(
                "Walk-the-book completed successfully with market order",
                **log_extra,
                total_filled=str(total_filled),
                avg_fill_price=str(avg_price) if avg_price else None,
            )
        else:
            logger.error(
                "Walk-the-book failed - market order did not fill",
                **log_extra,
                market_status=market_attempt.status.value,
            )

        return WalkResult(
            success=success,
            order_attempts=order_attempts,
            final_order_id=market_attempt.order_id,
            total_filled=total_filled,
            avg_fill_price=avg_price,
            error_message=None if success else "Market order failed to fill",
        )

    def _calculate_limit_price(self, quote: QuoteResult, side: str, price_ratio: float) -> Decimal:
        """Calculate limit price at given ratio toward aggressive side.

        For BUY orders:
            - Aggressive side is ask (we want to pay up to ask to get filled)
            - price = bid + ratio * (ask - bid)

        For SELL orders:
            - Aggressive side is bid (we want to sell down to bid to get filled)
            - price = ask - ratio * (ask - bid)

        Args:
            quote: Current market quote
            side: "BUY" or "SELL"
            price_ratio: How far to move toward aggressive side (0.75 = 75%)

        Returns:
            Calculated limit price

        """
        spread = quote.ask - quote.bid
        ratio_decimal = Decimal(str(price_ratio))

        if side == "BUY":
            # Move from bid toward ask
            price = quote.bid + (spread * ratio_decimal)
        else:  # SELL
            # Move from ask toward bid
            price = quote.ask - (spread * ratio_decimal)

        # Ensure price is reasonable
        price = max(price, MINIMUM_VALID_PRICE)

        # Quantize to cent precision
        return price.quantize(Decimal("0.01"))

    async def _place_limit_order_step(
        self,
        intent: OrderIntent,
        limit_price: Decimal,
        quantity: Decimal,
        step: int,
    ) -> OrderAttempt:
        """Place a limit order for one step of the walk.

        Args:
            intent: Order intent
            limit_price: Limit price for this step
            quantity: Quantity to order
            step: Step number (for logging)

        Returns:
            OrderAttempt record

        """
        try:
            result = await asyncio.to_thread(
                self.alpaca_manager.place_limit_order,
                symbol=intent.symbol,
                side=intent.side.to_alpaca(),
                quantity=float(quantity),
                limit_price=float(limit_price),
                time_in_force="day",
            )

            if result.success and result.order_id:
                return OrderAttempt(
                    step=step,
                    price=limit_price,
                    quantity=quantity,
                    order_id=result.order_id,
                    timestamp=datetime.now(UTC),
                    status=OrderStatus.PENDING,
                    filled_quantity=Decimal("0"),
                    avg_fill_price=None,
                )

            return OrderAttempt(
                step=step,
                price=limit_price,
                quantity=quantity,
                order_id=None,
                timestamp=datetime.now(UTC),
                status=OrderStatus.REJECTED,
                filled_quantity=Decimal("0"),
                avg_fill_price=None,
            )

        except Exception as e:
            logger.error(
                "Failed to place limit order",
                symbol=intent.symbol,
                step=step,
                error=str(e),
                correlation_id=intent.correlation_id,
            )
            return OrderAttempt(
                step=step,
                price=limit_price,
                quantity=quantity,
                order_id=None,
                timestamp=datetime.now(UTC),
                status=OrderStatus.FAILED,
                filled_quantity=Decimal("0"),
                avg_fill_price=None,
            )

    async def _place_market_order_step(
        self,
        intent: OrderIntent,
        quantity: Decimal,
        step: int,
    ) -> OrderAttempt:
        """Place a market order as final step.

        Args:
            intent: Order intent
            quantity: Quantity to order
            step: Step number (for logging)

        Returns:
            OrderAttempt record

        """
        try:
            executed: ExecutedOrder = await asyncio.to_thread(
                self.alpaca_manager.place_market_order,
                symbol=intent.symbol,
                side=intent.side.to_alpaca(),
                qty=quantity,
                is_complete_exit=intent.is_full_close,
            )

            if executed.status not in ["REJECTED", "CANCELED"]:
                # CRITICAL: Verify actual fill quantity instead of assuming full fill
                # The executed object may not have fill info immediately after market order
                filled_qty = getattr(executed, "filled_qty", None)
                avg_price = getattr(executed, "filled_avg_price", None)

                # If fill info not available, fetch the actual order status
                if filled_qty is None and executed.order_id:
                    logger.debug(
                        "Market order fill info not immediately available, fetching actual status",
                        order_id=executed.order_id,
                        symbol=intent.symbol,
                    )
                    try:
                        # Wait briefly for order to settle, then check actual status
                        await asyncio.sleep(0.5)
                        order_status = await self._check_order_status(executed.order_id)
                        filled_qty = order_status["filled_quantity"]
                        avg_price = order_status["avg_fill_price"] or avg_price
                    except Exception as e:
                        logger.warning(
                            "Failed to verify market order fill, defaulting to requested quantity",
                            order_id=executed.order_id,
                            symbol=intent.symbol,
                            error=str(e),
                        )
                        # Only default to requested quantity if verification failed
                        filled_qty = quantity

                # Final fallback: if still None (shouldn't happen), use quantity but log warning
                if filled_qty is None:
                    logger.warning(
                        "Market order fill quantity could not be determined, assuming full fill",
                        order_id=executed.order_id,
                        symbol=intent.symbol,
                        requested_quantity=str(quantity),
                    )
                    filled_qty = quantity

                return OrderAttempt(
                    step=step,
                    price=executed.price if executed.price else Decimal("0"),
                    quantity=quantity,
                    order_id=executed.order_id,
                    timestamp=executed.execution_timestamp or datetime.now(UTC),
                    status=OrderStatus.FILLED,
                    filled_quantity=filled_qty,
                    avg_fill_price=avg_price,
                )

            return OrderAttempt(
                step=step,
                price=Decimal("0"),
                quantity=quantity,
                order_id=executed.order_id,
                timestamp=executed.execution_timestamp or datetime.now(UTC),
                status=OrderStatus.REJECTED,
                filled_quantity=Decimal("0"),
                avg_fill_price=None,
            )

        except Exception as e:
            logger.error(
                "Failed to place market order",
                symbol=intent.symbol,
                step=step,
                error=str(e),
                correlation_id=intent.correlation_id,
            )
            return OrderAttempt(
                step=step,
                price=Decimal("0"),
                quantity=quantity,
                order_id=None,
                timestamp=datetime.now(UTC),
                status=OrderStatus.FAILED,
                filled_quantity=Decimal("0"),
                avg_fill_price=None,
            )

    async def _check_order_status(self, order_id: str) -> dict[str, Decimal | None]:
        """Check status of an order.

        Args:
            order_id: Order ID to check

        Returns:
            Dict with filled_quantity and avg_fill_price

        """
        try:
            result = await asyncio.to_thread(
                self.alpaca_manager.get_order_execution_result, order_id
            )

            filled_qty = getattr(result, "filled_qty", Decimal("0"))
            avg_price = getattr(result, "filled_avg_price", None)

            return {
                "filled_quantity": filled_qty if filled_qty else Decimal("0"),
                "avg_fill_price": avg_price,
            }
        except Exception as e:
            logger.error(
                "Failed to check order status",
                order_id=order_id,
                error=str(e),
            )
            return {
                "filled_quantity": Decimal("0"),
                "avg_fill_price": None,
            }

    async def _cancel_order(self, order_id: str, correlation_id: str | None = None) -> bool:
        """Cancel an order and wait for confirmation.

        Args:
            order_id: Order ID to cancel
            correlation_id: Optional correlation ID for tracing

        Returns:
            True if cancellation confirmed

        """
        try:
            await asyncio.to_thread(self.alpaca_manager.cancel_order, order_id)

            # Wait for cancellation confirmation with exponential backoff
            timeout = DEFAULT_CANCELLATION_TIMEOUT_SECONDS
            check_interval = 0.1  # Start with 100ms
            max_interval = 1.0  # Cap at 1 second
            elapsed = 0.0

            while elapsed < timeout:
                try:
                    result = self.alpaca_manager.get_order_execution_result(order_id)
                    status = result.status if result else None
                    if status and status.upper() in [
                        "CANCELED",
                        "CANCELLED",
                        "EXPIRED",
                        "REJECTED",
                    ]:
                        logger.debug(
                            "Order cancellation confirmed",
                            order_id=order_id,
                            correlation_id=correlation_id,
                        )
                        return True
                except Exception as e:
                    # Order might be in transition, continue waiting
                    logger.debug(
                        "Error checking order status during cancellation, will retry",
                        order_id=order_id,
                        error=str(e),
                        correlation_id=correlation_id,
                    )

                await asyncio.sleep(check_interval)
                elapsed += check_interval
                # Exponential backoff: double interval up to max
                check_interval = min(check_interval * 2, max_interval)

            logger.warning(
                "Order cancellation not confirmed within timeout",
                order_id=order_id,
                timeout=timeout,
                correlation_id=correlation_id,
            )
            return False

        except Exception as e:
            logger.error(
                "Failed to cancel order",
                order_id=order_id,
                error=str(e),
                correlation_id=correlation_id,
            )
            return False
