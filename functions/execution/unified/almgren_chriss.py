"""Business Unit: execution | Status: current.

Almgren-Chriss optimal execution strategy.

Implements the Almgren-Chriss model for optimal trade execution that balances:
- Market impact cost (price moves against you as you trade)
- Timing risk (volatility during execution period)

The model computes an optimal trading trajectory that minimizes:
    E[Cost] + λ * Var[Cost]

where λ is the risk aversion parameter.

Key features:
- Risk-averse execution schedule using sinh-based trajectory
- Configurable parameters: risk aversion (λ), volatility (σ), temporary impact (η)
- Slices large orders into N time periods with optimal quantity distribution
- Uses limit orders at calculated optimal prices
- Graceful fallback to market order if trajectory execution fails

References:
- Almgren, R., & Chriss, N. (2001). "Optimal execution of portfolio transactions."
  Journal of Risk, 3, 5-40.
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

import numpy as np

from the_alchemiser.shared.logging import get_logger

if TYPE_CHECKING:
    from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
    from the_alchemiser.shared.schemas.execution_report import ExecutedOrder

    from .order_intent import OrderIntent
    from .quote_service import QuoteResult

logger = get_logger(__name__)

# Model parameters (can be overridden via environment variables or config)
DEFAULT_RISK_AVERSION = float(os.getenv("AC_RISK_AVERSION", "0.5"))  # λ (lambda)
DEFAULT_VOLATILITY = float(os.getenv("AC_VOLATILITY", "0.02"))  # σ (sigma) per sqrt(dt)
DEFAULT_TEMP_IMPACT = float(os.getenv("AC_TEMP_IMPACT", "0.001"))  # η (eta)
DEFAULT_NUM_SLICES = int(os.getenv("AC_NUM_SLICES", "5"))  # N periods
DEFAULT_TOTAL_TIME_SECONDS = float(
    os.getenv("AC_TOTAL_TIME_SECONDS", "300")
)  # T (5 minutes default)
DEFAULT_SLICE_WAIT_SECONDS = float(
    os.getenv("AC_SLICE_WAIT_SECONDS", "30")
)  # Wait per slice
DEFAULT_MARKET_ORDER_FALLBACK = os.getenv("AC_MARKET_FALLBACK", "true").lower() == "true"

# Minimum valid price
MINIMUM_VALID_PRICE = Decimal("0.01")

# Terminal states for orders
TERMINAL_ORDER_STATUSES = {"FILLED", "CANCELED", "CANCELLED", "REJECTED", "EXPIRED"}


class OrderStatus(str, Enum):
    """Status of an order in the Almgren-Chriss execution."""

    PENDING = "pending"  # Order submitted, waiting for fill
    PARTIALLY_FILLED = "partially_filled"  # Some quantity filled
    FILLED = "filled"  # Fully filled
    CANCELLED = "cancelled"  # Cancelled by us for next slice
    REJECTED = "rejected"  # Rejected by broker
    FAILED = "failed"  # Failed to submit


@dataclass(frozen=True)
class SliceAttempt:
    """Record of a single slice execution in the Almgren-Chriss trajectory.

    Attributes:
        slice_index: Which slice this was (0-based)
        target_quantity: Optimal quantity for this slice
        limit_price: Limit price used
        order_id: Alpaca order ID
        timestamp: When order was placed
        status: Final status of this attempt
        filled_quantity: How much was filled
        avg_fill_price: Average fill price
        broker_error_message: Error message from broker if order failed

    """

    slice_index: int
    target_quantity: Decimal
    limit_price: Decimal
    order_id: str | None
    timestamp: datetime
    status: OrderStatus
    filled_quantity: Decimal
    avg_fill_price: Decimal | None
    broker_error_message: str | None = None


@dataclass
class AlmgrenChrissResult:
    """Result of the Almgren-Chriss execution.

    Attributes:
        success: Whether the order was successfully filled
        slice_attempts: List of all slice attempts made
        final_order_id: Final Alpaca order ID
        total_filled: Total quantity filled across all slices
        avg_fill_price: Average fill price across all fills
        error_message: Error message if failed
        trajectory: Optimal trajectory that was computed (remaining quantity per slice)

    """

    success: bool
    slice_attempts: list[SliceAttempt]
    final_order_id: str | None
    total_filled: Decimal
    avg_fill_price: Decimal | None
    error_message: str | None = None
    trajectory: list[Decimal] | None = None

    @property
    def num_slices_used(self) -> int:
        """Number of slices that were attempted."""
        return len(self.slice_attempts)


class AlmgrenChrissStrategy:
    """Strategy for optimal execution using Almgren-Chriss model.

    This implements the Almgren-Chriss optimal execution framework:
    1. Compute optimal trading trajectory based on risk aversion and market parameters
    2. Split order into N time slices with optimal quantity distribution
    3. Execute each slice with limit order at calculated optimal price
    4. Track partial fills and adjust remaining trajectory
    5. Optional fallback to market order if execution stalls

    The optimal trajectory minimizes: E[Cost] + λ * Var[Cost]
    where:
        - λ (lambda) is risk aversion parameter (higher = more risk-averse)
        - Cost includes market impact and timing risk
        - Trajectory follows: x_k = Q * sinh(κ(N-k)) / sinh(κN)
        - κ (kappa) = sqrt(λ * σ² / η)

    """

    def __init__(
        self,
        alpaca_manager: AlpacaManager,
        *,
        risk_aversion: float = DEFAULT_RISK_AVERSION,
        volatility: float = DEFAULT_VOLATILITY,
        temp_impact: float = DEFAULT_TEMP_IMPACT,
        num_slices: int = DEFAULT_NUM_SLICES,
        total_time_seconds: float = DEFAULT_TOTAL_TIME_SECONDS,
        slice_wait_seconds: float = DEFAULT_SLICE_WAIT_SECONDS,
        market_order_fallback: bool = DEFAULT_MARKET_ORDER_FALLBACK,
    ) -> None:
        """Initialize Almgren-Chriss strategy.

        Args:
            alpaca_manager: Alpaca broker manager for order operations
            risk_aversion: Risk aversion parameter λ (lambda), higher = more risk-averse
            volatility: Volatility parameter σ (sigma) per sqrt(dt)
            temp_impact: Temporary market impact coefficient η (eta)
            num_slices: Number of time slices N to split order into
            total_time_seconds: Total execution time horizon T
            slice_wait_seconds: How long to wait at each slice for fill
            market_order_fallback: Whether to use market order if execution stalls

        """
        self.alpaca_manager = alpaca_manager
        self.risk_aversion = risk_aversion
        self.volatility = volatility
        self.temp_impact = temp_impact
        self.num_slices = num_slices
        self.total_time_seconds = total_time_seconds
        self.slice_wait_seconds = slice_wait_seconds
        self.market_order_fallback = market_order_fallback

        # Compute derived parameter kappa
        # κ = sqrt(λ * σ² / η)
        self.kappa = np.sqrt(risk_aversion * volatility**2 / temp_impact)

        # Time per slice
        self.dt = total_time_seconds / num_slices

        logger.info(
            "AlmgrenChrissStrategy initialized",
            risk_aversion=risk_aversion,
            volatility=volatility,
            temp_impact=temp_impact,
            num_slices=num_slices,
            total_time_seconds=total_time_seconds,
            slice_wait_seconds=slice_wait_seconds,
            kappa=self.kappa,
            dt=self.dt,
            market_order_fallback=market_order_fallback,
        )

    def _compute_optimal_trajectory(self, total_quantity: Decimal) -> list[Decimal]:
        """Compute optimal trading trajectory using Almgren-Chriss model.

        The trajectory is computed as:
            x_k = Q * sinh(κ(N-k)) / sinh(κN)

        where x_k is the remaining quantity after slice k.

        Args:
            total_quantity: Total quantity to execute

        Returns:
            List of remaining quantities after each slice [x_0, x_1, ..., x_N]
            where x_0 = Q (initial) and x_N = 0 (fully executed)

        """
        Q = float(total_quantity)
        N = self.num_slices
        kappa = self.kappa

        trajectory = []
        for k in range(N + 1):
            # x_k = Q * sinh(κ(N-k)*dt) / sinh(κ*N*dt)
            remaining = Q * np.sinh(kappa * (N - k) * self.dt) / np.sinh(kappa * N * self.dt)
            trajectory.append(Decimal(str(remaining)))

        logger.debug(
            "Computed optimal trajectory",
            total_quantity=str(total_quantity),
            trajectory=[str(x) for x in trajectory],
        )

        return trajectory

    def _compute_slice_quantities(self, trajectory: list[Decimal]) -> list[Decimal]:
        """Compute quantity to trade in each slice from trajectory.

        Args:
            trajectory: Remaining quantities [x_0, x_1, ..., x_N]

        Returns:
            List of quantities to trade in each slice [n_1, n_2, ..., n_N]
            where n_k = x_{k-1} - x_k

        """
        slice_quantities = []
        for k in range(1, len(trajectory)):
            quantity = trajectory[k - 1] - trajectory[k]
            slice_quantities.append(quantity)

        logger.debug(
            "Computed slice quantities",
            slice_quantities=[str(q) for q in slice_quantities],
        )

        return slice_quantities

    def _calculate_limit_price(
        self, quote: QuoteResult, side: str, slice_index: int
    ) -> Decimal:
        """Calculate limit price for a given slice.

        We use a conservative limit price that's more aggressive than midpoint
        but not at the market to reduce impact. Early slices are more patient,
        later slices are more aggressive.

        Args:
            quote: Current market quote
            side: Order side (BUY or SELL)
            slice_index: Which slice we're on (0-based)

        Returns:
            Limit price as Decimal

        """
        # Use progressively more aggressive pricing as we move through slices
        # Slice 0 (first): 60% toward aggressive side
        # Slice N-1 (last): 90% toward aggressive side
        if self.num_slices > 1:
            aggression_factor = 0.60 + (0.30 * slice_index / (self.num_slices - 1))
        else:
            aggression_factor = 0.75  # Single slice: use moderate aggression

        if side == "BUY":
            # For BUY: move from bid toward ask
            limit_price = quote.bid + (quote.spread * Decimal(str(aggression_factor)))
        else:  # SELL
            # For SELL: move from ask toward bid
            limit_price = quote.ask - (quote.spread * Decimal(str(aggression_factor)))

        # Ensure price is valid
        if limit_price < MINIMUM_VALID_PRICE:
            limit_price = MINIMUM_VALID_PRICE
            logger.warning(
                "Limit price below minimum, clamping to minimum",
                calculated_price=str(limit_price),
                minimum=str(MINIMUM_VALID_PRICE),
            )

        logger.debug(
            "Calculated limit price",
            side=side,
            slice_index=slice_index,
            aggression_factor=aggression_factor,
            bid=str(quote.bid),
            ask=str(quote.ask),
            limit_price=str(limit_price),
        )

        return limit_price

    async def _place_slice_order(
        self,
        intent: OrderIntent,
        slice_index: int,
        quantity: Decimal,
        limit_price: Decimal,
    ) -> SliceAttempt:
        """Place limit order for a single slice and wait for fill or timeout.

        Args:
            intent: Original order intent
            slice_index: Which slice this is
            quantity: Quantity to trade in this slice
            limit_price: Limit price for this slice

        Returns:
            SliceAttempt with execution details

        """
        timestamp = datetime.now(UTC)
        log_extra = {
            "symbol": intent.symbol,
            "side": intent.side.value,
            "slice_index": slice_index,
            "quantity": str(quantity),
            "limit_price": str(limit_price),
            "correlation_id": intent.correlation_id,
        }

        try:
            # Place limit order
            executed_order = self.alpaca_manager.place_limit_order(
                symbol=intent.symbol,
                side=intent.side.value,
                quantity=quantity,
                limit_price=limit_price,
                client_order_id=intent.client_order_id,
            )

            logger.info("Placed slice limit order", **log_extra, order_id=executed_order.order_id)

            # Wait for fill or timeout
            await asyncio.sleep(self.slice_wait_seconds)

            # Check final status
            status_result = self.alpaca_manager.get_order_status(executed_order.order_id)

            filled_qty = status_result.filled_quantity
            avg_price = status_result.avg_fill_price

            # Determine order status
            if status_result.status in TERMINAL_ORDER_STATUSES:
                if filled_qty >= quantity:
                    status = OrderStatus.FILLED
                elif filled_qty > 0:
                    status = OrderStatus.PARTIALLY_FILLED
                elif status_result.status in {"REJECTED"}:
                    status = OrderStatus.REJECTED
                elif status_result.status in {"CANCELED", "CANCELLED"}:
                    status = OrderStatus.CANCELLED
                else:
                    status = OrderStatus.FAILED
            else:
                # Not yet terminal - cancel it and move to next slice
                try:
                    self.alpaca_manager.cancel_order(executed_order.order_id)
                    logger.info("Cancelled unfilled slice order", **log_extra)
                    status = OrderStatus.CANCELLED
                except Exception as cancel_err:
                    logger.warning(
                        "Failed to cancel slice order",
                        **log_extra,
                        error=str(cancel_err),
                    )
                    status = OrderStatus.PENDING

            return SliceAttempt(
                slice_index=slice_index,
                target_quantity=quantity,
                limit_price=limit_price,
                order_id=executed_order.order_id,
                timestamp=timestamp,
                status=status,
                filled_quantity=filled_qty,
                avg_fill_price=avg_price,
                broker_error_message=status_result.error_message,
            )

        except Exception as e:
            logger.error("Failed to place slice order", **log_extra, error=str(e), exc_info=True)
            return SliceAttempt(
                slice_index=slice_index,
                target_quantity=quantity,
                limit_price=limit_price,
                order_id=None,
                timestamp=timestamp,
                status=OrderStatus.FAILED,
                filled_quantity=Decimal("0"),
                avg_fill_price=None,
                broker_error_message=str(e),
            )

    async def execute(
        self,
        intent: OrderIntent,
        quote: QuoteResult,
    ) -> AlmgrenChrissResult:
        """Execute Almgren-Chriss optimal execution strategy.

        Args:
            intent: Order intent to execute
            quote: Current market quote

        Returns:
            AlmgrenChrissResult with execution details

        """
        log_extra = {
            "symbol": intent.symbol,
            "side": intent.side.value,
            "quantity": str(intent.quantity),
            "correlation_id": intent.correlation_id,
        }

        logger.info(
            "Starting Almgren-Chriss execution",
            **log_extra,
            num_slices=self.num_slices,
            risk_aversion=self.risk_aversion,
            kappa=self.kappa,
        )

        # Step 1: Compute optimal trajectory
        trajectory = self._compute_optimal_trajectory(intent.quantity)
        slice_quantities = self._compute_slice_quantities(trajectory)

        slice_attempts: list[SliceAttempt] = []
        remaining_quantity = intent.quantity
        total_filled = Decimal("0")
        weighted_fill_sum = Decimal("0")

        # Step 2: Execute each slice
        for slice_index, target_quantity in enumerate(slice_quantities):
            if remaining_quantity <= 0:
                logger.info(
                    "Order fully filled, stopping early",
                    **log_extra,
                    slice_index=slice_index,
                    total_filled=str(total_filled),
                )
                break

            # Adjust quantity if we have less remaining than target
            # (can happen due to partial fills in previous slices)
            actual_quantity = min(target_quantity, remaining_quantity)

            # Calculate limit price for this slice
            limit_price = self._calculate_limit_price(quote, intent.side.value, slice_index)

            logger.info(
                f"Slice {slice_index + 1}/{self.num_slices}",
                **log_extra,
                target_quantity=str(target_quantity),
                actual_quantity=str(actual_quantity),
                limit_price=str(limit_price),
                remaining_quantity=str(remaining_quantity),
            )

            # Execute slice
            attempt = await self._place_slice_order(
                intent, slice_index, actual_quantity, limit_price
            )
            slice_attempts.append(attempt)

            # Update totals
            if attempt.filled_quantity > 0:
                total_filled += attempt.filled_quantity
                remaining_quantity -= attempt.filled_quantity

                if attempt.avg_fill_price:
                    weighted_fill_sum += attempt.filled_quantity * attempt.avg_fill_price

                logger.info(
                    "Filled during slice",
                    **log_extra,
                    slice_index=slice_index,
                    filled_this_slice=str(attempt.filled_quantity),
                    total_filled=str(total_filled),
                    remaining=str(remaining_quantity),
                )

        # Step 3: Check if we filled the order
        avg_fill_price = None
        if total_filled > 0:
            avg_fill_price = weighted_fill_sum / total_filled

        # Determine if we should fall back to market order
        fill_percentage = (total_filled / intent.quantity) * 100 if intent.quantity > 0 else 0
        should_fallback = (
            self.market_order_fallback
            and remaining_quantity > 0
            and fill_percentage < 50  # Less than 50% filled
        )

        if should_fallback:
            logger.warning(
                "Almgren-Chriss execution incomplete, falling back to market order",
                **log_extra,
                fill_percentage=f"{fill_percentage:.1f}%",
                remaining=str(remaining_quantity),
            )

            # Place market order for remaining quantity
            try:
                market_order = self.alpaca_manager.place_market_order(
                    symbol=intent.symbol,
                    side=intent.side.value,
                    quantity=remaining_quantity,
                    client_order_id=intent.client_order_id,
                )

                logger.info(
                    "Market order fallback completed",
                    **log_extra,
                    order_id=market_order.order_id,
                    filled=str(market_order.filled_quantity),
                )

                # Update totals with market order fill
                total_filled += market_order.filled_quantity
                if market_order.filled_quantity > 0 and market_order.price:
                    weighted_fill_sum += market_order.filled_quantity * market_order.price
                    avg_fill_price = weighted_fill_sum / total_filled

                # Add market order as final slice attempt
                slice_attempts.append(
                    SliceAttempt(
                        slice_index=len(slice_attempts),
                        target_quantity=remaining_quantity,
                        limit_price=market_order.price or Decimal("0"),
                        order_id=market_order.order_id,
                        timestamp=datetime.now(UTC),
                        status=OrderStatus.FILLED
                        if market_order.filled_quantity >= remaining_quantity
                        else OrderStatus.PARTIALLY_FILLED,
                        filled_quantity=market_order.filled_quantity,
                        avg_fill_price=market_order.price,
                        broker_error_message=market_order.error_message,
                    )
                )

                remaining_quantity = Decimal("0")

            except Exception as e:
                logger.error(
                    "Market order fallback failed",
                    **log_extra,
                    error=str(e),
                    exc_info=True,
                )

        # Step 4: Build result
        success = total_filled >= intent.quantity or (
            total_filled > 0 and fill_percentage >= 95  # Allow 5% tolerance
        )

        final_order_id = slice_attempts[-1].order_id if slice_attempts else None

        error_message = None
        if not success:
            if not slice_attempts:
                error_message = "Failed to execute any slices"
            elif remaining_quantity > 0:
                error_message = (
                    f"Partially filled: {fill_percentage:.1f}% "
                    f"({total_filled}/{intent.quantity})"
                )

        result = AlmgrenChrissResult(
            success=success,
            slice_attempts=slice_attempts,
            final_order_id=final_order_id,
            total_filled=total_filled,
            avg_fill_price=avg_fill_price,
            error_message=error_message,
            trajectory=trajectory,
        )

        logger.info(
            "Almgren-Chriss execution complete",
            **log_extra,
            success=success,
            slices_used=result.num_slices_used,
            total_filled=str(total_filled),
            avg_price=str(avg_fill_price) if avg_fill_price else None,
            fill_percentage=f"{fill_percentage:.1f}%",
        )

        return result
