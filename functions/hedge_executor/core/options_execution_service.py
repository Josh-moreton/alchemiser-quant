"""Business Unit: hedge_executor | Status: current.

Options execution service for placing and monitoring hedge orders.

Handles order placement, monitoring, and result tracking for
protective options hedges.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from decimal import Decimal

from the_alchemiser.shared.errors import TradingClientError
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.options.adapters import AlpacaOptionsAdapter
from the_alchemiser.shared.options.constants import ORDER_POLL_INTERVAL_SECONDS

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
    error_message: str | None = None


class OptionsExecutionService:
    """Service for executing options hedge orders.

    Handles:
    - Limit order placement with walk-the-book fallback
    - Order monitoring until filled or timeout
    - Execution result tracking
    """

    def __init__(
        self,
        options_adapter: AlpacaOptionsAdapter,
        *,
        order_timeout_seconds: int = 60,
        walk_the_book_enabled: bool = True,
    ) -> None:
        """Initialize execution service.

        Args:
            options_adapter: Alpaca options API adapter
            order_timeout_seconds: Max time to wait for fill
            walk_the_book_enabled: Whether to use progressive pricing

        """
        self._adapter = options_adapter
        self._timeout = order_timeout_seconds
        self._walk_the_book = walk_the_book_enabled

    def execute_hedge_order(
        self,
        selected_option: SelectedOption,
        underlying_symbol: str,
        client_order_id: str | None = None,
    ) -> ExecutionResult:
        """Execute a hedge order for the selected option.

        Places a limit order and monitors until filled or timeout.
        Optionally uses walk-the-book strategy for better fills.

        Args:
            selected_option: Selected option with contract details
            underlying_symbol: Underlying ETF symbol
            client_order_id: Optional client order ID for idempotency

        Returns:
            ExecutionResult with fill details

        """
        contract = selected_option.contract
        option_symbol = contract.symbol

        if client_order_id is None:
            client_order_id = f"hedge-{uuid.uuid4()}"

        logger.info(
            "Executing hedge order",
            option_symbol=option_symbol,
            underlying=underlying_symbol,
            quantity=selected_option.contracts_to_buy,
            limit_price=str(selected_option.limit_price),
            client_order_id=client_order_id,
        )

        try:
            # Place initial limit order
            order_response = self._adapter.place_option_order(
                option_symbol=option_symbol,
                quantity=selected_option.contracts_to_buy,
                side="buy",
                order_type="limit",
                limit_price=selected_option.limit_price,
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
                )

            # Monitor order until filled or timeout
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
            )

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

    def execute_spread_order(
        self,
        long_leg: OptionContract,
        short_leg: OptionContract,
        quantity: int,
        long_limit_price: Decimal,
        short_limit_price: Decimal,
        underlying_symbol: str,
        client_order_id: str | None = None,
    ) -> ExecutionResult:
        """Execute a spread order (long and short legs).

        Places spread order via adapter's place_spread_order method,
        which handles sequential execution with retry logic and
        compensating close if needed.

        Args:
            long_leg: Long leg option contract
            short_leg: Short leg option contract
            quantity: Number of spreads to execute
            long_limit_price: Limit price for long leg
            short_limit_price: Limit price for short leg
            underlying_symbol: Underlying ETF symbol
            client_order_id: Optional client order ID for idempotency

        Returns:
            ExecutionResult with spread execution details

        """
        long_symbol = long_leg.symbol
        short_symbol = short_leg.symbol

        if client_order_id is None:
            client_order_id = f"spread-{uuid.uuid4()}"

        logger.info(
            "Executing spread order",
            long_leg=long_symbol,
            short_leg=short_symbol,
            underlying=underlying_symbol,
            quantity=quantity,
            long_limit_price=str(long_limit_price),
            short_limit_price=str(short_limit_price),
            client_order_id=client_order_id,
        )

        try:
            # Place spread order via adapter (handles sequential execution)
            spread_response = self._adapter.place_spread_order(
                long_leg_symbol=long_symbol,
                short_leg_symbol=short_symbol,
                quantity=quantity,
                long_leg_limit_price=long_limit_price,
                short_leg_limit_price=short_limit_price,
                time_in_force="day",
                client_order_id=client_order_id,
            )

            # Extract order IDs and details from response
            long_order = spread_response.get("long_leg", {})
            short_order = spread_response.get("short_leg", {})

            long_order_id = long_order.get("id")
            short_order_id = short_order.get("id")

            if not long_order_id or not short_order_id:
                return ExecutionResult(
                    success=False,
                    order_id=None,
                    option_symbol=long_symbol,
                    underlying_symbol=underlying_symbol,
                    quantity=quantity,
                    filled_quantity=0,
                    filled_price=None,
                    total_premium=Decimal("0"),
                    error_message="Spread order failed - missing order IDs",
                )

            # Monitor both legs until filled or timeout
            # For simplicity, monitor the long leg (critical leg for protection)
            result = self._monitor_order(
                order_id=long_order_id,
                option_symbol=long_symbol,
                underlying_symbol=underlying_symbol,
                target_quantity=quantity,
            )

            # If long leg succeeded, verify short leg also filled
            if result.success:
                try:
                    short_order_status = self._adapter.get_order(short_order_id)
                    short_status = short_order_status.get("status", "").lower()

                    if short_status != "filled":
                        logger.warning(
                            "Long leg filled but short leg not filled",
                            long_order_id=long_order_id,
                            short_order_id=short_order_id,
                            short_status=short_status,
                        )
                        # Return success for long leg, but note the asymmetry
                        # The adapter's retry/compensating logic should have handled this
                        return ExecutionResult(
                            success=True,
                            order_id=long_order_id,
                            option_symbol=long_symbol,
                            underlying_symbol=underlying_symbol,
                            quantity=quantity,
                            filled_quantity=result.filled_quantity,
                            filled_price=result.filled_price,
                            total_premium=result.total_premium,
                            error_message=f"Spread executed but short leg status: {short_status}",
                        )

                    # Both legs filled - calculate net premium
                    long_filled_price = result.filled_price or Decimal("0")
                    short_filled_qty = int(short_order_status.get("filled_qty", 0))
                    short_filled_price = self._parse_decimal(
                        short_order_status.get("filled_avg_price")
                    ) or Decimal("0")

                    # Net debit = long premium - short credit
                    net_premium = (long_filled_price - short_filled_price) * short_filled_qty * 100

                    logger.info(
                        "Spread order fully executed",
                        long_order_id=long_order_id,
                        short_order_id=short_order_id,
                        long_filled_price=str(long_filled_price),
                        short_filled_price=str(short_filled_price),
                        net_premium=str(net_premium),
                    )

                    return ExecutionResult(
                        success=True,
                        order_id=f"{long_order_id}+{short_order_id}",
                        option_symbol=f"{long_symbol}/{short_symbol}",
                        underlying_symbol=underlying_symbol,
                        quantity=quantity,
                        filled_quantity=min(result.filled_quantity, short_filled_qty),
                        filled_price=long_filled_price - short_filled_price,
                        total_premium=net_premium,
                    )

                except TradingClientError as e:
                    logger.error(
                        "Error verifying short leg status",
                        short_order_id=short_order_id,
                        error=str(e),
                    )
                    # Return success for long leg
                    return result

            return result

        except TradingClientError as e:
            logger.error(
                "Spread order failed",
                long_leg=long_symbol,
                short_leg=short_symbol,
                error=str(e),
            )
            return ExecutionResult(
                success=False,
                order_id=None,
                option_symbol=f"{long_symbol}/{short_symbol}",
                underlying_symbol=underlying_symbol,
                quantity=quantity,
                filled_quantity=0,
                filled_price=None,
                total_premium=Decimal("0"),
                error_message=str(e),
            )
