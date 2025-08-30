"""Business Unit: order execution/placement | Status: current.

Execution context exception classes.

Defines execution-specific exception types for order placement, position management,
and trading operations.
"""

from __future__ import annotations

from typing import Any

from the_alchemiser.shared_kernel.exceptions.base_exceptions import (
    AlchemiserError,
    DataAccessError
)


class TradingClientError(AlchemiserError):
    """Raised when trading client operations fail."""


class OrderValidationError(TradingClientError):
    """Raised when order validation fails."""


class OrderOperationError(TradingClientError):
    """Raised when an order operation (e.g. liquidation) fails."""


class OrderPlacementError(TradingClientError):
    """Raised when an order placement fails due to trading client issues."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        side: str | None = None,
        quantity: float | None = None,
        order_type: str | None = None,
        reject_reason: str | None = None,
    ) -> None:
        """Create an order placement error with detailed context."""
        context: dict[str, Any] = {}
        if symbol:
            context["symbol"] = symbol
        if side:
            context["side"] = side
        if quantity is not None:
            context["quantity"] = quantity
        if order_type:
            context["order_type"] = order_type
        if reject_reason:
            context["reject_reason"] = reject_reason

        super().__init__(message, context)
        self.symbol = symbol
        self.side = side
        self.quantity = quantity
        self.order_type = order_type
        self.reject_reason = reject_reason


class OrderTimeoutError(TradingClientError):
    """Raised when an order operation times out."""

    def __init__(
        self,
        message: str,
        order_id: str | None = None,
        timeout_seconds: int | None = None,
        operation: str | None = None,
    ) -> None:
        """Create an order timeout error with timing details."""
        context: dict[str, Any] = {}
        if order_id:
            context["order_id"] = order_id
        if timeout_seconds is not None:
            context["timeout_seconds"] = timeout_seconds
        if operation:
            context["operation"] = operation

        super().__init__(message, context)
        self.order_id = order_id
        self.timeout_seconds = timeout_seconds
        self.operation = operation


class BuyingPowerError(TradingClientError):
    """Raised when there's insufficient buying power for an order."""

    def __init__(
        self,
        message: str,
        required_amount: float | None = None,
        available_amount: float | None = None,
    ) -> None:
        """Create a buying power error with financial details."""
        context: dict[str, Any] = {}
        if required_amount is not None:
            context["required_amount"] = required_amount
        if available_amount is not None:
            context["available_amount"] = available_amount

        super().__init__(message, context)
        self.required_amount = required_amount
        self.available_amount = available_amount


class InsufficientFundsError(BuyingPowerError):
    """Raised when there are insufficient funds for a trade."""


class PositionValidationError(TradingClientError):
    """Raised when position validation fails for an order."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        required_quantity: float | None = None,
        available_quantity: float | None = None,
        side: str | None = None,
    ) -> None:
        """Create a position validation error with position details."""
        context: dict[str, Any] = {}
        if symbol:
            context["symbol"] = symbol
        if required_quantity is not None:
            context["required_quantity"] = required_quantity
        if available_quantity is not None:
            context["available_quantity"] = available_quantity
        if side:
            context["side"] = side

        super().__init__(message, context)
        self.symbol = symbol
        self.required_quantity = required_quantity
        self.available_quantity = available_quantity
        self.side = side


class MarketClosedError(TradingClientError):
    """Raised when attempting to trade while market is closed."""

    def __init__(
        self,
        message: str,
        next_open_time: str | None = None,
    ) -> None:
        """Create a market closed error with timing information."""
        context: dict[str, Any] = {}
        if next_open_time:
            context["next_open_time"] = next_open_time

        super().__init__(message, context)
        self.next_open_time = next_open_time


class OrderExecutionError(AlchemiserError):
    """Exception raised when broker order operations fail."""


class OrderNotFoundError(DataAccessError):
    """Exception raised when order ID is not found."""


class ProcessingError(AlchemiserError):
    """Exception raised when plan processing fails."""


class PublishError(AlchemiserError):
    """Exception raised when execution report publishing fails."""
