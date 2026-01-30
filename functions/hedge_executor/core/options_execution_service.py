"""Business Unit: hedge_executor | Status: current.

Options execution service for placing and monitoring hedge orders.

Handles order placement, monitoring, and result tracking for
protective options hedges with adaptive marketability pricing.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING

from the_alchemiser.shared.errors import TradingClientError
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.options.adapters import AlpacaOptionsAdapter
from the_alchemiser.shared.options.constants import (
    MAX_FILL_ATTEMPTS,
    MAX_FILL_TIME_SECONDS,
    ORDER_POLL_INTERVAL_SECONDS,
    PRICE_UPDATE_INTERVAL_SECONDS,
)
from the_alchemiser.shared.options.marketability_pricing import (
    MarketabilityPricer,
    OrderSide,
    SlippageTracker,
)

if TYPE_CHECKING:
    from the_alchemiser.shared.options.schemas import OptionContract

from .option_selector import SelectedOption

logger = get_logger(__name__)


@dataclass(frozen=True)
class ExecutionResult:
    """Result of hedge order execution."""

    success: bool
    order_id: str | None
    option_symbol: str
    underlying_symbol: str
    quantity: int
    filled_quantity: int
    filled_price: Decimal | None
    total_premium: Decimal
    slippage_from_mid: Decimal | None = None  # Slippage amount (filled - mid)
    slippage_pct: Decimal | None = None  # Slippage as percentage of mid
    pricing_attempts: int = 1  # Number of pricing attempts
    error_message: str | None = None
    no_fill_explicit: bool = False  # Explicit "hedge NOT placed" flag


class OptionsExecutionService:
    """Service for executing options hedge orders.

    Handles:
    - Adaptive limit pricing with marketability algorithm
    - Order monitoring until filled or timeout
    - Slippage tracking and enforcement
    - Explicit no-fill handling
    """

    def __init__(
        self,
        options_adapter: AlpacaOptionsAdapter,
        *,
        order_timeout_seconds: int = MAX_FILL_TIME_SECONDS,
        marketability_enabled: bool = True,
        slippage_tracker: SlippageTracker | None = None,
    ) -> None:
        """Initialize execution service.

        Args:
            options_adapter: Alpaca options API adapter
            order_timeout_seconds: Max time to wait for fill
            marketability_enabled: Whether to use adaptive pricing
            slippage_tracker: Optional shared tracker for daily slippage

        """
        self._adapter = options_adapter
        self._timeout = order_timeout_seconds
        self._marketability_enabled = marketability_enabled

        # Initialize marketability pricer
        self._pricer = MarketabilityPricer(slippage_tracker=slippage_tracker)

    def execute_hedge_order(
        self,
        selected_option: SelectedOption,
        underlying_symbol: str,
        client_order_id: str | None = None,
        vix_level: Decimal | None = None,
        order_side: OrderSide = OrderSide.OPEN,
    ) -> ExecutionResult:
        """Execute a hedge order for the selected option.

        Places a limit order with adaptive pricing and monitors until
        filled or timeout. Enforces slippage limits and explicitly
        handles "no fill" outcomes.

        Args:
            selected_option: Selected option with contract details
            underlying_symbol: Underlying ETF symbol
            client_order_id: Optional client order ID for idempotency
            vix_level: Current VIX level (affects pricing strategy)
            order_side: Whether opening or closing position

        Returns:
            ExecutionResult with fill details and slippage metrics

        """
        contract = selected_option.contract
        option_symbol = contract.symbol

        if client_order_id is None:
            client_order_id = f"hedge-{uuid.uuid4()}"

        # Calculate initial limit price using marketability algorithm
        if self._marketability_enabled:
            initial_limit = self._pricer.calculate_initial_limit_price(
                contract=contract,
                order_side=order_side,
                vix_level=vix_level,
            )
        else:
            # Fallback to old method (limit at selected price)
            initial_limit = selected_option.limit_price

        logger.info(
            "Executing hedge order with adaptive pricing",
            option_symbol=option_symbol,
            underlying=underlying_symbol,
            quantity=selected_option.contracts_to_buy,
            initial_limit_price=str(initial_limit),
            marketability_enabled=self._marketability_enabled,
            order_side=order_side.value,
            vix_level=str(vix_level) if vix_level else "N/A",
            client_order_id=client_order_id,
        )

        try:
            # Place initial limit order
            order_response = self._adapter.place_option_order(
                option_symbol=option_symbol,
                quantity=selected_option.contracts_to_buy,
                side="buy",
                order_type="limit",
                limit_price=initial_limit,
                time_in_force="day",
                client_order_id=client_order_id,
            )

            order_id = order_response.get("id")
            if not order_id:
                return ExecutionResult(
                    success=False,
                    order_id=None,
                    option_symbol=option_symbol,
                    underlying_symbol=underlying_symbol,
                    quantity=selected_option.contracts_to_buy,
                    filled_quantity=0,
                    filled_price=None,
                    total_premium=Decimal("0"),
                    error_message="No order ID returned from broker",
                    no_fill_explicit=True,
                )

            # Monitor order with adaptive pricing if enabled
            if self._marketability_enabled:
                return self._monitor_order_with_repricing(
                    order_id=order_id,
                    option_symbol=option_symbol,
                    underlying_symbol=underlying_symbol,
                    target_quantity=selected_option.contracts_to_buy,
                    contract=contract,
                    order_side=order_side,
                    vix_level=vix_level,
                    initial_limit=initial_limit,
                )
            else:
                # Standard monitoring without repricing
                return self._monitor_order(
                    order_id=order_id,
                    option_symbol=option_symbol,
                    underlying_symbol=underlying_symbol,
                    target_quantity=selected_option.contracts_to_buy,
                )

        except TradingClientError as e:
            logger.error(
                "Hedge order failed",
                option_symbol=option_symbol,
                error=str(e),
                alert_required=True,
            )
            return ExecutionResult(
                success=False,
                order_id=None,
                option_symbol=option_symbol,
                underlying_symbol=underlying_symbol,
                quantity=selected_option.contracts_to_buy,
                filled_quantity=0,
                filled_price=None,
                total_premium=Decimal("0"),
                error_message=str(e),
                no_fill_explicit=True,
            )

    def _monitor_order_with_repricing(
        self,
        order_id: str,
        option_symbol: str,
        underlying_symbol: str,
        target_quantity: int,
        contract: "OptionContract",
        order_side: OrderSide,
        vix_level: Decimal | None,
        initial_limit: Decimal,
    ) -> ExecutionResult:
        """Monitor order with adaptive repricing until filled or max attempts.

        Implements marketability algorithm:
        1. Monitor order at current price
        2. If not filled within interval, cancel and reprice
        3. Step toward ask until filled or max slippage reached

        Args:
            order_id: Alpaca order ID
            option_symbol: OCC option symbol
            underlying_symbol: Underlying ETF symbol
            target_quantity: Expected fill quantity
            contract: Option contract with bid/ask data
            order_side: Whether opening or closing position
            vix_level: Current VIX level
            initial_limit: Initial limit price

        Returns:
            ExecutionResult with final status and slippage metrics

        """
        start_time = time.time()
        current_limit = initial_limit
        pricing_attempt = 1
        mid_price = contract.mid_price or Decimal("0")

        while True:
            elapsed = time.time() - start_time

            # Check timeout
            if elapsed > self._timeout:
                logger.warning(
                    "EXPLICIT NO FILL - Order timeout reached",
                    order_id=order_id,
                    option_symbol=option_symbol,
                    elapsed_seconds=elapsed,
                    max_time_seconds=self._timeout,
                    pricing_attempts=pricing_attempt,
                    alert_required=True,
                )
                self._adapter.cancel_order(order_id)

                return ExecutionResult(
                    success=False,
                    order_id=order_id,
                    option_symbol=option_symbol,
                    underlying_symbol=underlying_symbol,
                    quantity=target_quantity,
                    filled_quantity=0,
                    filled_price=None,
                    total_premium=Decimal("0"),
                    slippage_from_mid=None,
                    slippage_pct=None,
                    pricing_attempts=pricing_attempt,
                    error_message=f"No fill after {elapsed:.1f}s - HEDGE NOT PLACED",
                    no_fill_explicit=True,
                )

            # Check max attempts
            if pricing_attempt > MAX_FILL_ATTEMPTS:
                logger.warning(
                    "EXPLICIT NO FILL - Max pricing attempts reached",
                    order_id=order_id,
                    option_symbol=option_symbol,
                    pricing_attempts=pricing_attempt,
                    max_attempts=MAX_FILL_ATTEMPTS,
                    alert_required=True,
                )
                self._adapter.cancel_order(order_id)

                return ExecutionResult(
                    success=False,
                    order_id=order_id,
                    option_symbol=option_symbol,
                    underlying_symbol=underlying_symbol,
                    quantity=target_quantity,
                    filled_quantity=0,
                    filled_price=None,
                    total_premium=Decimal("0"),
                    slippage_from_mid=None,
                    slippage_pct=None,
                    pricing_attempts=pricing_attempt,
                    error_message=f"No fill after {pricing_attempt} attempts - HEDGE NOT PLACED",
                    no_fill_explicit=True,
                )

            try:
                order = self._adapter.get_order(order_id)
                status = order.get("status", "").lower()

                if status == "filled":
                    # Order filled - calculate slippage and record
                    filled_qty = int(order.get("filled_qty", 0))
                    filled_price = self._parse_decimal(order.get("filled_avg_price"))
                    total_premium = (
                        filled_price * filled_qty * 100 if filled_price else Decimal("0")
                    )

                    # Calculate slippage metrics
                    slippage_from_mid = filled_price - mid_price if filled_price else None
                    slippage_pct = (
                        (slippage_from_mid / mid_price) if (slippage_from_mid and mid_price > 0)
                        else None
                    )

                    # Record slippage with tracker
                    if slippage_from_mid and filled_price:
                        slippage_amount = slippage_from_mid * filled_qty * 100
                        self._pricer.slippage_tracker.record_trade(
                            premium_paid=total_premium,
                            mid_price=mid_price,
                            slippage_amount=slippage_amount,
                        )

                    logger.info(
                        "Hedge order filled with slippage tracking",
                        order_id=order_id,
                        filled_qty=filled_qty,
                        filled_price=str(filled_price),
                        mid_price=str(mid_price),
                        slippage_from_mid=str(slippage_from_mid) if slippage_from_mid else "N/A",
                        slippage_pct=f"{float(slippage_pct):.2%}" if slippage_pct else "N/A",
                        total_premium=str(total_premium),
                        pricing_attempts=pricing_attempt,
                    )

                    return ExecutionResult(
                        success=True,
                        order_id=order_id,
                        option_symbol=option_symbol,
                        underlying_symbol=underlying_symbol,
                        quantity=target_quantity,
                        filled_quantity=filled_qty,
                        filled_price=filled_price,
                        total_premium=total_premium,
                        slippage_from_mid=slippage_from_mid,
                        slippage_pct=slippage_pct,
                        pricing_attempts=pricing_attempt,
                    )

                if status in ("canceled", "cancelled", "expired", "rejected"):
                    error_msg = f"Order {status}"
                    if status == "rejected":
                        error_msg = order.get("reject_reason", "Order rejected")

                    logger.warning(
                        "EXPLICIT NO FILL - Order ended without fill",
                        order_id=order_id,
                        status=status,
                        error_message=error_msg,
                        pricing_attempts=pricing_attempt,
                        alert_required=True,
                    )

                    return ExecutionResult(
                        success=False,
                        order_id=order_id,
                        option_symbol=option_symbol,
                        underlying_symbol=underlying_symbol,
                        quantity=target_quantity,
                        filled_quantity=int(order.get("filled_qty", 0)),
                        filled_price=self._parse_decimal(order.get("filled_avg_price")),
                        total_premium=Decimal("0"),
                        slippage_from_mid=None,
                        slippage_pct=None,
                        pricing_attempts=pricing_attempt,
                        error_message=f"{error_msg} - HEDGE NOT PLACED",
                        no_fill_explicit=True,
                    )

                # Still pending - check if we should reprice
                if elapsed >= pricing_attempt * PRICE_UPDATE_INTERVAL_SECONDS:
                    # Time to reprice - fetch fresh quote
                    logger.info(
                        "Repricing order - not filled at current limit",
                        order_id=order_id,
                        current_limit=str(current_limit),
                        pricing_attempt=pricing_attempt,
                        elapsed_seconds=elapsed,
                    )

                    # Get fresh quote
                    fresh_contract = self._adapter.get_option_quote(option_symbol)
                    if fresh_contract is None:
                        logger.warning(
                            "Unable to fetch fresh quote for repricing",
                            option_symbol=option_symbol,
                        )
                        time.sleep(ORDER_POLL_INTERVAL_SECONDS)
                        continue

                    # Calculate next limit price
                    next_limit = self._pricer.calculate_next_limit_price(
                        current_limit=current_limit,
                        contract=fresh_contract,
                        order_side=order_side,
                        vix_level=vix_level,
                        attempt_number=pricing_attempt + 1,
                    )

                    if next_limit is None:
                        # Max slippage or daily limit reached
                        logger.warning(
                            "EXPLICIT NO FILL - Max slippage or daily limit reached",
                            order_id=order_id,
                            option_symbol=option_symbol,
                            current_limit=str(current_limit),
                            pricing_attempts=pricing_attempt,
                            alert_required=True,
                        )
                        self._adapter.cancel_order(order_id)

                        return ExecutionResult(
                            success=False,
                            order_id=order_id,
                            option_symbol=option_symbol,
                            underlying_symbol=underlying_symbol,
                            quantity=target_quantity,
                            filled_quantity=0,
                            filled_price=None,
                            total_premium=Decimal("0"),
                            slippage_from_mid=None,
                            slippage_pct=None,
                            pricing_attempts=pricing_attempt,
                            error_message="Max slippage reached - HEDGE NOT PLACED",
                            no_fill_explicit=True,
                        )

                    # Cancel and replace order with new limit price
                    try:
                        self._adapter.cancel_order(order_id)
                        time.sleep(1)  # Brief delay after cancel

                        # Place new order at updated price
                        order_response = self._adapter.place_option_order(
                            option_symbol=option_symbol,
                            quantity=target_quantity,
                            side="buy",
                            order_type="limit",
                            limit_price=next_limit,
                            time_in_force="day",
                            client_order_id=f"{order_id}-retry-{pricing_attempt}",
                        )

                        new_order_id = order_response.get("id")
                        if new_order_id:
                            order_id = new_order_id
                            current_limit = next_limit
                            pricing_attempt += 1

                            logger.info(
                                "Order repriced and replaced",
                                new_order_id=order_id,
                                new_limit=str(current_limit),
                                pricing_attempt=pricing_attempt,
                            )
                        else:
                            logger.error(
                                "Failed to replace order - no ID returned",
                                option_symbol=option_symbol,
                            )
                            return ExecutionResult(
                                success=False,
                                order_id=order_id,
                                option_symbol=option_symbol,
                                underlying_symbol=underlying_symbol,
                                quantity=target_quantity,
                                filled_quantity=0,
                                filled_price=None,
                                total_premium=Decimal("0"),
                                slippage_from_mid=None,
                                slippage_pct=None,
                                pricing_attempts=pricing_attempt,
                                error_message="Failed to replace order - HEDGE NOT PLACED",
                                no_fill_explicit=True,
                            )

                    except TradingClientError as e:
                        logger.error(
                            "Error repricing order",
                            order_id=order_id,
                            error=str(e),
                        )
                        return ExecutionResult(
                            success=False,
                            order_id=order_id,
                            option_symbol=option_symbol,
                            underlying_symbol=underlying_symbol,
                            quantity=target_quantity,
                            filled_quantity=0,
                            filled_price=None,
                            total_premium=Decimal("0"),
                            slippage_from_mid=None,
                            slippage_pct=None,
                            pricing_attempts=pricing_attempt,
                            error_message=f"Reprice error: {e} - HEDGE NOT PLACED",
                            no_fill_explicit=True,
                        )

                # Continue polling
                time.sleep(ORDER_POLL_INTERVAL_SECONDS)

            except TradingClientError as e:
                logger.error(
                    "Error monitoring order",
                    order_id=order_id,
                    error=str(e),
                )
                time.sleep(ORDER_POLL_INTERVAL_SECONDS)

    def _monitor_order(
        self,
        order_id: str,
        option_symbol: str,
        underlying_symbol: str,
        target_quantity: int,
    ) -> ExecutionResult:
        """Monitor order until filled or timeout.

        Args:
            order_id: Alpaca order ID
            option_symbol: OCC option symbol
            underlying_symbol: Underlying ETF symbol
            target_quantity: Expected fill quantity

        Returns:
            ExecutionResult with final status

        """
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            if elapsed > self._timeout:
                # Timeout - cancel order and return partial result
                logger.warning(
                    "Order timeout - cancelling",
                    order_id=order_id,
                    elapsed_seconds=elapsed,
                )
                self._adapter.cancel_order(order_id)
                break

            try:
                order = self._adapter.get_order(order_id)
                status = order.get("status", "").lower()

                if status == "filled":
                    filled_qty = int(order.get("filled_qty", 0))
                    filled_price = self._parse_decimal(order.get("filled_avg_price"))
                    total_premium = (
                        filled_price * filled_qty * 100 if filled_price else Decimal("0")
                    )

                    logger.info(
                        "Hedge order filled",
                        order_id=order_id,
                        filled_qty=filled_qty,
                        filled_price=str(filled_price),
                        total_premium=str(total_premium),
                    )

                    return ExecutionResult(
                        success=True,
                        order_id=order_id,
                        option_symbol=option_symbol,
                        underlying_symbol=underlying_symbol,
                        quantity=target_quantity,
                        filled_quantity=filled_qty,
                        filled_price=filled_price,
                        total_premium=total_premium,
                    )

                if status in ("canceled", "cancelled", "expired", "rejected"):
                    error_msg = f"Order {status}"
                    if status == "rejected":
                        error_msg = order.get("reject_reason", "Order rejected")

                    logger.warning(
                        "Order ended without fill",
                        order_id=order_id,
                        status=status,
                    )

                    return ExecutionResult(
                        success=False,
                        order_id=order_id,
                        option_symbol=option_symbol,
                        underlying_symbol=underlying_symbol,
                        quantity=target_quantity,
                        filled_quantity=int(order.get("filled_qty", 0)),
                        filled_price=self._parse_decimal(order.get("filled_avg_price")),
                        total_premium=Decimal("0"),
                        error_message=error_msg,
                    )

                # Still pending - continue polling
                time.sleep(ORDER_POLL_INTERVAL_SECONDS)

            except TradingClientError as e:
                logger.error(
                    "Error monitoring order",
                    order_id=order_id,
                    error=str(e),
                )
                time.sleep(ORDER_POLL_INTERVAL_SECONDS)

        # Reached timeout - get final status
        try:
            order = self._adapter.get_order(order_id)
            filled_qty = int(order.get("filled_qty", 0))
            filled_price = self._parse_decimal(order.get("filled_avg_price"))

            return ExecutionResult(
                success=filled_qty > 0,
                order_id=order_id,
                option_symbol=option_symbol,
                underlying_symbol=underlying_symbol,
                quantity=target_quantity,
                filled_quantity=filled_qty,
                filled_price=filled_price,
                total_premium=filled_price * filled_qty * 100 if filled_price else Decimal("0"),
                error_message="Order timeout" if filled_qty == 0 else None,
            )
        except TradingClientError:
            return ExecutionResult(
                success=False,
                order_id=order_id,
                option_symbol=option_symbol,
                underlying_symbol=underlying_symbol,
                quantity=target_quantity,
                filled_quantity=0,
                filled_price=None,
                total_premium=Decimal("0"),
                error_message="Order timeout - unable to get final status",
            )

    @staticmethod
    def _parse_decimal(value: str | float | int | None) -> Decimal | None:
        """Parse value to Decimal."""
        if value is None or value == "":
            return None
        try:
            return Decimal(str(value))
        except (ValueError, TypeError):
            return None
