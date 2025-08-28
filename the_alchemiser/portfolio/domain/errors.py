"""Business Unit: portfolio assessment & management; Status: current.

Portfolio context domain errors.

Portfolio-specific exceptions for position validation, buying power checks,
and valuation failures.
"""

from __future__ import annotations

from typing import Any


class PortfolioError(Exception):
    """Base exception for portfolio context errors."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Initialize portfolio error with optional contextual data."""
        super().__init__(message)
        self.message = message
        self.context = context or {}


class BuyingPowerError(PortfolioError):
    """Raised when insufficient buying power detected during execution."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        required_amount: float | None = None,
        available_amount: float | None = None,
        shortfall: float | None = None,
    ) -> None:
        """Create a buying power error with financial context."""
        context = {}
        if symbol:
            context["symbol"] = symbol
        if required_amount is not None:
            context["required_amount"] = required_amount
        if available_amount is not None:
            context["available_amount"] = available_amount
        if shortfall is not None:
            context["shortfall"] = shortfall
        super().__init__(message, context)
        self.symbol = symbol
        self.required_amount = required_amount
        self.available_amount = available_amount
        self.shortfall = shortfall


class InsufficientFundsError(PortfolioError):
    """Raised when there are insufficient funds for an operation."""


class PositionValidationError(PortfolioError):
    """Raised when position validation fails."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        requested_qty: float | None = None,
        available_qty: float | None = None,
    ) -> None:
        """Initialize position validation error."""
        context = {}
        if symbol:
            context["symbol"] = symbol
        if requested_qty is not None:
            context["requested_qty"] = requested_qty
        if available_qty is not None:
            context["available_qty"] = available_qty
        super().__init__(message, context)
        self.symbol = symbol
        self.requested_qty = requested_qty
        self.available_qty = available_qty