#!/usr/bin/env python3
"""
Execution Context Adapter

Adapter to bridge OrderExecutor protocol to ExecutionContext protocol
for strategy compatibility.
"""

from typing import TYPE_CHECKING, Any

from alpaca.trading.enums import OrderSide

if TYPE_CHECKING:
    from the_alchemiser.application.execution.smart_execution import OrderExecutor


class ExecutionContextAdapter:
    """Adapter to provide ExecutionContext interface for OrderExecutor."""

    def __init__(self, order_executor: "OrderExecutor") -> None:
        """Initialize adapter with order executor.

        Args:
            order_executor: OrderExecutor implementation
        """
        self._order_executor = order_executor

    def place_limit_order(
        self, symbol: str, qty: float, side: OrderSide, limit_price: float
    ) -> str | None:
        """Place a limit order."""
        return self._order_executor.place_limit_order(symbol, qty, side, limit_price)

    def place_market_order(
        self, symbol: str, side: OrderSide, qty: float | None = None
    ) -> str | None:
        """Place a market order."""
        return self._order_executor.place_market_order(symbol, side, qty=qty)

    def wait_for_order_completion(
        self, order_ids: list[str], max_wait_seconds: int = 30
    ) -> Any:  # WebSocketResultDTO
        """Wait for order completion."""
        return self._order_executor.wait_for_order_completion(order_ids, max_wait_seconds)

    def get_latest_quote(self, symbol: str) -> tuple[float, float] | None:
        """Get latest quote for a symbol."""
        return self._order_executor.data_provider.get_latest_quote(symbol)
