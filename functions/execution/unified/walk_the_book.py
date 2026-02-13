"""Business Unit: execution | Status: current.

Walk-the-book order placement strategy with explicit price progression.

Implements a clear, testable strategy for placing limit orders that progressively
move toward market price before finally using a market order.

Key features:
- Uses WebSocket for real-time order status updates (with polling fallback)
- Properly tracks partial fills across steps
- Only orders remaining quantity when moving to next step
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING, TypedDict

from the_alchemiser.shared.logging import get_logger

if TYPE_CHECKING:
    from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
    from the_alchemiser.shared.schemas.execution_report import ExecutedOrder

    from .order_intent import OrderIntent
    from .quote_service import QuoteResult

logger = get_logger(__name__)

# Price progression configuration
PRICE_STEPS = [0.50, 0.75, 0.95]  # Percentages toward aggressive side (start at midpoint)
# Reduced from 30s to 10s - 30s per step was too long and resulted in poor execution
# in volatile markets. 10s gives market time to fill while not leaving orders stale.
DEFAULT_STEP_WAIT_SECONDS = 10  # How long to wait at each step before moving to next
DEFAULT_CANCELLATION_TIMEOUT_SECONDS = 10.0
DEFAULT_MARKET_ORDER_WAIT_SECONDS = 30.0  # Longer wait for final market order
MINIMUM_VALID_PRICE = Decimal("0.01")

# Terminal states for orders
TERMINAL_ORDER_STATUSES = {"FILLED", "CANCELED", "CANCELLED", "REJECTED", "EXPIRED"}


class OrderTerminalStateResult(TypedDict):
    """Result of waiting for an order to reach terminal state."""

    is_terminal: bool
    status: str | None
    filled_quantity: Decimal
    avg_fill_price: Decimal | None


class OrderStatusResult(TypedDict):
    """Result of checking order status."""

    filled_quantity: Decimal
    avg_fill_price: Decimal | None
    status: str | None


class OrderStatus(StrEnum):
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
        broker_error_message: Error message from broker if order failed

    """

    step: int
    price: Decimal
    quantity: Decimal
    order_id: str | None
    timestamp: datetime
    status: OrderStatus
    filled_quantity: Decimal
    avg_fill_price: Decimal | None
    broker_error_message: str | None = None


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
        1. Start with limit order at midpoint (50% of spread)
        2. If not filled after wait period, cancel and replace at 75% toward aggressive side
        3. If still not filled, cancel and replace at 95% toward aggressive side
        4. If still not filled, cancel and place market order

    For BUY orders:
        - Aggressive side = ask price
        - 50% = bid + 0.50 * (ask - bid) = midpoint
        - 75% = bid + 0.75 * (ask - bid)
        - Conservative (patient) to aggressive (market-crossing)

    For SELL orders:
        - Aggressive side = bid price
        - 50% = ask - 0.50 * (ask - bid) = midpoint
        - 75% = ask - 0.75 * (ask - bid)
        - Conservative (patient) to aggressive (market-crossing)

    """

    def __init__(
        self,
        alpaca_manager: AlpacaManager,
        *,
        step_wait_seconds: float = DEFAULT_STEP_WAIT_SECONDS,
        market_order_wait_seconds: float = DEFAULT_MARKET_ORDER_WAIT_SECONDS,
        price_steps: list[float] | None = None,
    ) -> None:
        """Initialize walk-the-book strategy.

        Args:
            alpaca_manager: Alpaca broker manager for order operations
            step_wait_seconds: How long to wait at each price step (default: 10s)
            market_order_wait_seconds: How long to wait for market order fill (default: 30s)
            price_steps: Custom price progression steps (default: [0.50, 0.75, 0.95])

        """
        self.alpaca_manager = alpaca_manager
        self.step_wait_seconds = step_wait_seconds
        self.market_order_wait_seconds = market_order_wait_seconds
        self.price_steps = price_steps or PRICE_STEPS

        logger.debug(
            "WalkTheBookStrategy initialized",
            step_wait_seconds=step_wait_seconds,
            market_order_wait_seconds=market_order_wait_seconds,
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
                quote_bid=str(quote.bid),
                quote_ask=str(quote.ask),
                quote_spread=str(quote.spread),
            )

            # Place limit order and wait for fill or timeout (handled internally)
            attempt = await self._place_limit_order_step(
                intent=intent,
                limit_price=limit_price,
                quantity=remaining_quantity,
                step=step_index,
            )
            order_attempts.append(attempt)

            # Update filled totals from whatever was filled during the step
            if attempt.filled_quantity > 0:
                total_filled += attempt.filled_quantity
                remaining_quantity -= attempt.filled_quantity

                if attempt.avg_fill_price:
                    weighted_fill_sum += attempt.filled_quantity * attempt.avg_fill_price

                logger.info(
                    "Filled during limit order step",
                    **log_extra,
                    step=step_index + 1,
                    step_filled=str(attempt.filled_quantity),
                    total_filled=str(total_filled),
                    remaining=str(remaining_quantity),
                )

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

            # Check if order failed/rejected
            if attempt.status == OrderStatus.REJECTED:
                broker_error = attempt.broker_error_message or "Unknown rejection reason"
                logger.error(
                    "Order rejected during walk-the-book",
                    **log_extra,
                    step=step_index + 1,
                    broker_error=broker_error,
                    limit_price=str(limit_price),
                )
                # Cancel any pending orders from prior steps to release held shares
                await self._cancel_prior_step_orders(
                    order_attempts, step_index, intent.correlation_id
                )
                return WalkResult(
                    success=False,
                    order_attempts=order_attempts,
                    final_order_id=None,
                    total_filled=total_filled,
                    avg_fill_price=None,
                    error_message=f"Order rejected at step {step_index + 1}: {broker_error}",
                )

            # If order is still pending (timeout), cancel before moving to next step
            if attempt.status == OrderStatus.PENDING and attempt.order_id:
                logger.debug(
                    "Step timed out with unfilled order, cancelling before next step",
                    **log_extra,
                    step=step_index + 1,
                    order_id=attempt.order_id,
                )
                await self._cancel_order(attempt.order_id, intent.correlation_id)

        # Final step: Market order for any remaining quantity
        logger.info(
            "Walk-the-book limit steps complete, escalating to market order",
            **log_extra,
            remaining_quantity=str(remaining_quantity),
            total_filled_so_far=str(total_filled),
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
            price_ratio: How far to move toward aggressive side (0.50 = 50% = midpoint, 0.75 = 75%)

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
        """Place a limit order for one step of the walk and wait for fill/timeout.

        Places a limit order and then waits up to step_wait_seconds for it to
        reach a terminal state (filled, cancelled, rejected, expired). Uses
        WebSocket-based monitoring with polling fallback for reliable detection.

        If the order doesn't fully fill within the timeout, returns with
        whatever partial fill was achieved. The caller is responsible for
        cancelling unfilled orders.

        Args:
            intent: Order intent
            limit_price: Limit price for this step
            quantity: Quantity to order
            step: Step number (for logging)

        Returns:
            OrderAttempt record with actual filled quantity

        """
        try:
            # Generate unique client_order_id for this step
            step_client_order_id = (
                f"{intent.client_order_id}-step-{step}" if intent.client_order_id else None
            )

            result = await asyncio.to_thread(
                self.alpaca_manager.place_limit_order,
                symbol=intent.symbol,
                side=intent.side.to_alpaca(),
                quantity=float(quantity),
                limit_price=float(limit_price),
                time_in_force="day",
                client_order_id=step_client_order_id,
            )

            if result.success and result.order_id:
                logger.debug(
                    "Limit order placed, waiting for fill or timeout",
                    symbol=intent.symbol,
                    step=step,
                    quantity=str(quantity),
                    limit_price=str(limit_price),
                    order_id=result.order_id,
                    wait_seconds=self.step_wait_seconds,
                    correlation_id=intent.correlation_id,
                )

                # Wait for order to reach terminal state or timeout
                wait_result = await self._wait_for_order_terminal_state(
                    order_id=result.order_id,
                    max_wait_seconds=self.step_wait_seconds,
                    correlation_id=intent.correlation_id,
                )

                filled_qty = wait_result["filled_quantity"] or Decimal("0")
                avg_price = wait_result["avg_fill_price"]
                is_terminal = wait_result["is_terminal"]
                order_status = wait_result["status"]

                # Determine attempt status based on order state
                if order_status in ("FILLED",):
                    attempt_status = OrderStatus.FILLED
                elif order_status in ("REJECTED",):
                    attempt_status = OrderStatus.REJECTED
                elif order_status in ("CANCELED", "CANCELLED", "EXPIRED"):
                    attempt_status = OrderStatus.CANCELLED
                elif is_terminal:
                    # Unknown terminal state - treat as pending
                    attempt_status = OrderStatus.PENDING
                else:
                    # Timeout - order is still open (will be cancelled by caller)
                    attempt_status = OrderStatus.PENDING

                logger.info(
                    "Limit order step complete",
                    symbol=intent.symbol,
                    step=step,
                    order_id=result.order_id,
                    order_status=order_status,
                    is_terminal=is_terminal,
                    filled_quantity=str(filled_qty),
                    avg_fill_price=str(avg_price) if avg_price else None,
                    requested_quantity=str(quantity),
                    correlation_id=intent.correlation_id,
                )

                return OrderAttempt(
                    step=step,
                    price=limit_price,
                    quantity=quantity,
                    order_id=result.order_id,
                    timestamp=datetime.now(UTC),
                    status=attempt_status,
                    filled_quantity=filled_qty,
                    avg_fill_price=avg_price,
                )

            # Extract error message from result - this is the actual broker rejection reason
            broker_error = getattr(result, "error", None) or "Order rejected by broker"
            logger.warning(
                "Limit order rejected by broker",
                symbol=intent.symbol,
                step=step,
                quantity=str(quantity),
                limit_price=str(limit_price),
                broker_error=broker_error,
                result_status=getattr(result, "status", "unknown"),
                correlation_id=intent.correlation_id,
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
                broker_error_message=broker_error,
            )

        except Exception as e:
            error_msg = str(e)
            logger.error(
                "Failed to place limit order (exception)",
                symbol=intent.symbol,
                step=step,
                quantity=str(quantity),
                limit_price=str(limit_price),
                error=error_msg,
                error_type=type(e).__name__,
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
                broker_error_message=f"Exception: {error_msg}",
            )

    async def _place_market_order_step(
        self,
        intent: OrderIntent,
        quantity: Decimal,
        step: int,
    ) -> OrderAttempt:
        """Place a market order as final step and wait for terminal state.

        Places a market order and waits up to market_order_wait_seconds for it
        to reach a terminal state. Market orders should fill almost immediately,
        but we use WebSocket monitoring to reliably capture the fill.

        Args:
            intent: Order intent
            quantity: Quantity to order
            step: Step number (for logging)

        Returns:
            OrderAttempt record with actual filled quantity

        """
        try:
            # Generate unique client_order_id for market order step
            step_client_order_id = (
                f"{intent.client_order_id}-step-{step}" if intent.client_order_id else None
            )

            executed: ExecutedOrder = await asyncio.to_thread(
                self.alpaca_manager.place_market_order,
                symbol=intent.symbol,
                side=intent.side.to_alpaca(),
                qty=quantity,
                is_complete_exit=intent.is_full_close,
                client_order_id=step_client_order_id,
            )

            if executed.status in ["REJECTED", "CANCELED"]:
                logger.warning(
                    "Market order immediately rejected/cancelled",
                    symbol=intent.symbol,
                    step=step,
                    order_id=executed.order_id,
                    status=executed.status,
                    correlation_id=intent.correlation_id,
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

            # Check if we already have fill info from immediate response
            immediate_filled_qty = getattr(executed, "filled_qty", None)
            immediate_avg_price = getattr(executed, "filled_avg_price", None)

            # If we have complete fill info already, don't need to wait
            if immediate_filled_qty is not None and Decimal(str(immediate_filled_qty)) >= quantity:
                logger.info(
                    "Market order filled immediately",
                    symbol=intent.symbol,
                    step=step,
                    order_id=executed.order_id,
                    filled_quantity=str(immediate_filled_qty),
                    avg_fill_price=str(immediate_avg_price) if immediate_avg_price else None,
                    correlation_id=intent.correlation_id,
                )
                return OrderAttempt(
                    step=step,
                    price=executed.price if executed.price else Decimal("0"),
                    quantity=quantity,
                    order_id=executed.order_id,
                    timestamp=executed.execution_timestamp or datetime.now(UTC),
                    status=OrderStatus.FILLED,
                    filled_quantity=Decimal(str(immediate_filled_qty)),
                    avg_fill_price=(
                        Decimal(str(immediate_avg_price)) if immediate_avg_price else None
                    ),
                )

            # Need to wait for fill - use WebSocket-based monitoring
            logger.debug(
                "Market order placed, waiting for terminal state",
                symbol=intent.symbol,
                step=step,
                order_id=executed.order_id,
                wait_seconds=self.market_order_wait_seconds,
                correlation_id=intent.correlation_id,
            )

            wait_result = await self._wait_for_order_terminal_state(
                order_id=executed.order_id,
                max_wait_seconds=self.market_order_wait_seconds,
                correlation_id=intent.correlation_id,
            )

            filled_qty = wait_result["filled_quantity"] or Decimal("0")
            avg_price = wait_result["avg_fill_price"]
            is_terminal = wait_result["is_terminal"]
            order_status = wait_result["status"]

            # Determine attempt status
            if order_status == "FILLED" or filled_qty >= quantity:
                attempt_status = OrderStatus.FILLED
            elif order_status in ("REJECTED",):
                attempt_status = OrderStatus.REJECTED
            elif order_status in ("CANCELED", "CANCELLED", "EXPIRED"):
                attempt_status = OrderStatus.CANCELLED
            elif filled_qty > 0:
                # Partial fill but not terminal yet - treat as filled with actual qty
                attempt_status = OrderStatus.FILLED
                logger.warning(
                    "Market order partial fill, treating as complete",
                    symbol=intent.symbol,
                    step=step,
                    order_id=executed.order_id,
                    filled_quantity=str(filled_qty),
                    requested_quantity=str(quantity),
                    order_status=order_status,
                    is_terminal=is_terminal,
                    correlation_id=intent.correlation_id,
                )
            else:
                # No fill - this is unusual for a market order
                attempt_status = OrderStatus.FAILED
                logger.error(
                    "Market order did not fill",
                    symbol=intent.symbol,
                    step=step,
                    order_id=executed.order_id,
                    order_status=order_status,
                    is_terminal=is_terminal,
                    correlation_id=intent.correlation_id,
                )

            logger.info(
                "Market order step complete",
                symbol=intent.symbol,
                step=step,
                order_id=executed.order_id,
                order_status=order_status,
                is_terminal=is_terminal,
                filled_quantity=str(filled_qty),
                avg_fill_price=str(avg_price) if avg_price else None,
                requested_quantity=str(quantity),
                attempt_status=attempt_status.value,
                correlation_id=intent.correlation_id,
            )

            return OrderAttempt(
                step=step,
                price=executed.price if executed.price else Decimal("0"),
                quantity=quantity,
                order_id=executed.order_id,
                timestamp=executed.execution_timestamp or datetime.now(UTC),
                status=attempt_status,
                filled_quantity=filled_qty,
                avg_fill_price=avg_price,
            )

        except Exception as e:
            logger.error(
                "Failed to place market order",
                symbol=intent.symbol,
                step=step,
                error=str(e),
                error_type=type(e).__name__,
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

    async def _check_order_status(self, order_id: str) -> OrderStatusResult:
        """Check current status of an order (point-in-time snapshot).

        Args:
            order_id: Order ID to check

        Returns:
            OrderStatusResult with filled_quantity, avg_fill_price, and status

        """
        try:
            result = await asyncio.to_thread(
                self.alpaca_manager.get_order_execution_result, order_id
            )

            filled_qty = getattr(result, "filled_qty", Decimal("0"))
            avg_price = getattr(result, "filled_avg_price", None)
            status = getattr(result, "status", None)

            return OrderStatusResult(
                filled_quantity=Decimal(str(filled_qty)) if filled_qty else Decimal("0"),
                avg_fill_price=Decimal(str(avg_price)) if avg_price else None,
                status=status.upper() if status else None,
            )
        except Exception as e:
            logger.error(
                "Failed to check order status",
                order_id=order_id,
                error=str(e),
            )
            return OrderStatusResult(
                filled_quantity=Decimal("0"),
                avg_fill_price=None,
                status=None,
            )

    async def _wait_for_order_terminal_state(
        self,
        order_id: str,
        max_wait_seconds: float,
        *,
        correlation_id: str | None = None,
    ) -> OrderTerminalStateResult:
        """Wait for an order to reach a terminal state using WebSocket + polling fallback.

        This is the CORRECT way to wait for fills - uses the existing WebSocket
        infrastructure that properly handles partial fills and waits for complete
        terminal state (FILLED, CANCELED, REJECTED, EXPIRED).

        Args:
            order_id: Order ID to monitor
            max_wait_seconds: Maximum time to wait for terminal state
            correlation_id: Optional correlation ID for tracing

        Returns:
            OrderTerminalStateResult with:
                - is_terminal: Whether order reached terminal state
                - status: Final order status (e.g., "FILLED", "CANCELED")
                - filled_quantity: Total filled quantity
                - avg_fill_price: Average fill price

        """
        logger.debug(
            "Waiting for order to reach terminal state via WebSocket",
            order_id=order_id,
            max_wait_seconds=max_wait_seconds,
            correlation_id=correlation_id,
        )

        try:
            # Use WebSocket-based waiting with polling fallback
            ws_result = await asyncio.to_thread(
                self.alpaca_manager.wait_for_order_completion,
                [order_id],
                int(max_wait_seconds),
            )

            # Check if our order completed
            order_completed = order_id in ws_result.completed_order_ids

            # Fetch final order state
            final_status = await self._check_order_status(order_id)

            is_terminal = order_completed or final_status["status"] in TERMINAL_ORDER_STATUSES

            logger.info(
                "Order terminal state check complete",
                order_id=order_id,
                is_terminal=is_terminal,
                status=final_status["status"],
                filled_quantity=str(final_status["filled_quantity"]),
                ws_status=ws_result.status.value if ws_result.status else None,
                correlation_id=correlation_id,
            )

            return OrderTerminalStateResult(
                is_terminal=is_terminal,
                status=final_status["status"],
                filled_quantity=final_status["filled_quantity"],
                avg_fill_price=final_status["avg_fill_price"],
            )

        except Exception as e:
            logger.error(
                "Error waiting for order terminal state",
                order_id=order_id,
                error=str(e),
                error_type=type(e).__name__,
                correlation_id=correlation_id,
            )
            # Fallback: try a single status check
            try:
                final_status = await self._check_order_status(order_id)
                is_terminal = final_status["status"] in TERMINAL_ORDER_STATUSES
                return OrderTerminalStateResult(
                    is_terminal=is_terminal,
                    status=final_status["status"],
                    filled_quantity=final_status["filled_quantity"],
                    avg_fill_price=final_status["avg_fill_price"],
                )
            except Exception:
                return OrderTerminalStateResult(
                    is_terminal=False,
                    status=None,
                    filled_quantity=Decimal("0"),
                    avg_fill_price=None,
                )

    async def _cancel_prior_step_orders(
        self,
        order_attempts: list[OrderAttempt],
        current_step: int,
        correlation_id: str | None = None,
    ) -> None:
        """Cancel any pending orders from steps prior to the current one.

        When a later step is rejected (e.g. due to held shares from a prior
        step's unfilled limit order), we must cancel those prior orders to
        release the held position before retrying.

        Args:
            order_attempts: All order attempts so far
            current_step: The step index that was rejected
            correlation_id: Correlation ID for tracing

        """
        for prior_index, prior_attempt in enumerate(order_attempts):
            if prior_index >= current_step:
                break
            if (
                prior_attempt.order_id
                and prior_attempt.status == OrderStatus.PENDING
                and prior_attempt.filled_quantity == Decimal("0")
            ):
                logger.info(
                    "Cancelling pending order from prior step after rejection",
                    order_id=prior_attempt.order_id,
                    prior_step=prior_index + 1,
                    rejected_step=current_step + 1,
                    correlation_id=correlation_id,
                )
                await self._cancel_order(prior_attempt.order_id, correlation_id)

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
