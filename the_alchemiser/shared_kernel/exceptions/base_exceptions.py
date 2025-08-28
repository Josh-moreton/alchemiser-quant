"""Business Unit: utilities (shared kernel / cross-cutting) | Status: current.

Base exception classes for The Alchemiser system.

These are shared exception types used across multiple bounded contexts.
Only includes the essential base classes - context-specific exceptions
should be defined within their respective contexts.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


class AlchemiserError(Exception):
    """Base exception class for all Alchemiser-specific errors."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Initialize base error with optional contextual data."""
        super().__init__(message)
        self.message = message
        self.context = context or {}
        self.timestamp = datetime.now(UTC)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to structured data for logging/reporting."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
        }


class ConfigurationError(AlchemiserError):
    """Raised when there are configuration-related issues."""

    def __init__(
        self,
        message: str,
        config_key: str | None = None,
        config_value: str | None = None,
    ) -> None:
        """Raise when configuration values are missing or invalid."""
        context = {}
        if config_key:
            context["config_key"] = config_key
        if config_value is not None:
            context["config_value"] = config_value
        super().__init__(message, context)
        self.config_key = config_key
        self.config_value = config_value


class DataAccessError(AlchemiserError):
    """Raised when data access operations fail."""


class NotificationError(AlchemiserError):
    """Raised when notification sending fails."""


class OrderExecutionError(AlchemiserError):
    """Raised when order execution fails."""

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


class StrategyExecutionError(AlchemiserError):
    """Raised when strategy execution fails."""

    def __init__(self, message: str, strategy_name: str | None = None) -> None:
        """Create a strategy execution error."""
        super().__init__(message)
        self.strategy_name = strategy_name


class ValidationError(AlchemiserError):
    """Raised when data validation fails."""

    def __init__(
        self, message: str, field_name: str | None = None, value: str | None = None
    ) -> None:
        """Create a validation error for invalid data."""
        super().__init__(message)
        self.field_name = field_name
        self.value = value
