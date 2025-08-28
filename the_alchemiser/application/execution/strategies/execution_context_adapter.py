#!/usr/bin/env python3
"""Business Unit: order execution/placement; Status: current.

Execution Context Adapter.

Adapter to bridge OrderExecutor protocol to ExecutionContext protocol
for strategy compatibility using canonical executor.
"""

from decimal import Decimal
from typing import TYPE_CHECKING, Any, cast

from alpaca.trading.enums import OrderSide

from the_alchemiser.application.execution.canonical_executor import (
    CanonicalOrderExecutor,
)
from the_alchemiser.domain.shared_kernel.value_objects.money import Money
from the_alchemiser.domain.trading.value_objects.order_request import OrderRequest
from the_alchemiser.domain.trading.value_objects.order_type import OrderType
from the_alchemiser.domain.trading.value_objects.quantity import Quantity
from the_alchemiser.domain.trading.value_objects.side import Side
from the_alchemiser.domain.trading.value_objects.symbol import Symbol
from the_alchemiser.domain.trading.value_objects.time_in_force import TimeInForce

if TYPE_CHECKING:
    from the_alchemiser.application.execution.smart_execution import OrderExecutor


class ExecutionContextAdapter:
    """Adapter to provide ExecutionContext interface using canonical executor."""

    def __init__(self, order_executor: "OrderExecutor") -> None:
        self._order_executor = order_executor

    def place_limit_order(
        self, symbol: str, qty: float, side: OrderSide, limit_price: float
    ) -> str | None:
        """Place limit order through canonical executor."""
        try:
            # Get alpaca manager from order executor for canonical executor
            alpaca_manager = getattr(self._order_executor, "alpaca_manager", None)
            if not alpaca_manager:
                # If not available, get underlying trading repository
                alpaca_manager = getattr(self._order_executor, "_trading", self._order_executor)

            # Ensure we have a proper AlpacaManager instance, type cast as needed
            from the_alchemiser.services.repository.alpaca_manager import AlpacaManager

            if not isinstance(alpaca_manager, AlpacaManager):
                raise ValueError("Unable to get AlpacaManager instance for canonical executor")

            side_value = "buy" if side.value.lower() == "buy" else "sell"
            # Type assertion is safe since we control the values above
            side_literal = side_value if side_value in ("buy", "sell") else "buy"
            order_request = OrderRequest(
                symbol=Symbol(symbol),
                side=Side(side_literal),  # type: ignore[arg-type]
                quantity=Quantity(Decimal(str(qty))),
                order_type=OrderType("limit"),
                time_in_force=TimeInForce("day"),
                limit_price=Money(amount=Decimal(str(limit_price)), currency="USD"),
            )
            executor = CanonicalOrderExecutor(alpaca_manager)
            result = executor.execute(order_request)
            return result.order_id if result.success else None
        except Exception:
            return None

    def place_market_order(
        self, symbol: str, side: OrderSide, qty: float | None = None
    ) -> str | None:
        """Place market order through canonical executor."""
        if qty is None or qty <= 0:
            return None
        try:
            # Get alpaca manager from order executor for canonical executor
            alpaca_manager = getattr(self._order_executor, "alpaca_manager", None)
            if not alpaca_manager:
                # If not available, get underlying trading repository
                alpaca_manager = getattr(self._order_executor, "_trading", self._order_executor)

            # Ensure we have a proper AlpacaManager instance, type cast as needed
            from the_alchemiser.services.repository.alpaca_manager import AlpacaManager

            if not isinstance(alpaca_manager, AlpacaManager):
                raise ValueError("Unable to get AlpacaManager instance for canonical executor")

            side_value = "buy" if side.value.lower() == "buy" else "sell"
            # Type assertion is safe since we control the values above
            side_literal = side_value if side_value in ("buy", "sell") else "buy"
            order_request = OrderRequest(
                symbol=Symbol(symbol),
                side=Side(side_literal),  # type: ignore[arg-type]
                quantity=Quantity(Decimal(str(qty))),
                order_type=OrderType("market"),
                time_in_force=TimeInForce("day"),
            )
            executor = CanonicalOrderExecutor(alpaca_manager)
            result = executor.execute(order_request)
            return result.order_id if result.success else None
        except Exception:
            return None

    def wait_for_order_completion(
        self, order_ids: list[str], max_wait_seconds: int = 30
    ) -> Any:  # WebSocketResultDTO
        return self._order_executor.wait_for_order_completion(order_ids, max_wait_seconds)

    def get_latest_quote(self, symbol: str) -> tuple[float, float] | None:
        # Boundary returns floats; strategy layer converts to Decimal precisely
        return self._order_executor.data_provider.get_latest_quote(symbol)
