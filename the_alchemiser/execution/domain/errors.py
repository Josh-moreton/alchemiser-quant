"""Business Unit: order execution/placement; Status: current.

Execution context domain errors.

Execution-specific exceptions for order placement, execution failures,
timeout handling, and spread analysis.
"""

from __future__ import annotations

from typing import Any


class ExecutionError(Exception):
    """Base exception for execution context errors."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Initialize execution error with optional contextual data."""
        super().__init__(message)
        self.message = message
        self.context = context or {}


class OrderExecutionError(ExecutionError):
    """Raised when order placement or execution fails."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        order_type: str | None = None,
        order_id: str | None = None,
        quantity: float | None = None,
        price: float | None = None,
        account_id: str | None = None,
        retry_count: int = 0,
    ) -> None:
        """Create an order execution error with contextual details."""
        context: dict[str, Any] = {}
        if symbol:
            context["symbol"] = symbol
        if order_type:
            context["order_type"] = order_type
        if order_id:
            context["order_id"] = order_id
        if quantity is not None:
            context["quantity"] = quantity
        if price is not None:
            context["price"] = price
        if account_id:
            context["account_id"] = account_id
        if retry_count > 0:
            context["retry_count"] = retry_count

        super().__init__(message, context)
        self.symbol = symbol
        self.order_type = order_type
        self.order_id = order_id
        self.quantity = quantity
        self.price = price
        self.account_id = account_id
        self.retry_count = retry_count


class OrderPlacementError(OrderExecutionError):
    """Raised when order placement fails and returns None ID."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        order_type: str | None = None,
        quantity: float | None = None,
        price: float | None = None,
        reason: str | None = None,
    ) -> None:
        """Create an order placement error for None order ID scenarios."""
        super().__init__(
            message=message,
            symbol=symbol,
            order_type=order_type,
            quantity=quantity,
            price=price,
        )
        self.reason = reason


class OrderTimeoutError(OrderExecutionError):
    """Raised when order execution times out during limit order sequence."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        order_id: str | None = None,
        timeout_seconds: float | None = None,
        attempt_number: int | None = None,
    ) -> None:
        """Create an order timeout error for re-pegging scenarios."""
        super().__init__(message=message, symbol=symbol, order_id=order_id)
        self.timeout_seconds = timeout_seconds
        self.attempt_number = attempt_number


class SpreadAnalysisError(ExecutionError):
    """Raised when spread analysis fails and cannot determine appropriate pricing."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        bid: float | None = None,
        ask: float | None = None,
        spread_cents: float | None = None,
    ) -> None:
        """Create a spread analysis error for pricing failures."""
        context = {}
        if symbol:
            context["symbol"] = symbol
        if bid is not None:
            context["bid"] = bid
        if ask is not None:
            context["ask"] = ask
        if spread_cents is not None:
            context["spread_cents"] = spread_cents
        super().__init__(message, context)
        self.symbol = symbol
        self.bid = bid
        self.ask = ask
        self.spread_cents = spread_cents


class MarketClosedError(ExecutionError):
    """Raised when attempting to trade while markets are closed."""