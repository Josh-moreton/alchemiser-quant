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


class RateLimitError(AlchemiserError):
    """Raised when rate limits are exceeded."""

    def __init__(
        self,
        message: str,
        rate_limit: int | None = None,
        reset_time: str | None = None,
    ) -> None:
        """Create a rate limit error with timing details."""
        context: dict[str, Any] = {}
        if rate_limit is not None:
            context["rate_limit"] = rate_limit
        if reset_time:
            context["reset_time"] = reset_time

        super().__init__(message, context)
        self.rate_limit = rate_limit
        self.reset_time = reset_time


class LoggingError(AlchemiserError):
    """Raised when logging operations fail."""


class FileOperationError(AlchemiserError):
    """Raised when file operations fail."""

    def __init__(
        self,
        message: str,
        file_path: str | None = None,
        operation: str | None = None,
    ) -> None:
        """Create a file operation error with file details."""
        context: dict[str, Any] = {}
        if file_path:
            context["file_path"] = file_path
        if operation:
            context["operation"] = operation

        super().__init__(message, context)
        self.file_path = file_path
        self.operation = operation


class DatabaseError(AlchemiserError):
    """Raised when database operations fail."""

    def __init__(
        self,
        message: str,
        query: str | None = None,
        table: str | None = None,
    ) -> None:
        """Create a database error with query details."""
        context: dict[str, Any] = {}
        if query:
            context["query"] = query
        if table:
            context["table"] = table

        super().__init__(message, context)
        self.query = query
        self.table = table


class SecurityError(AlchemiserError):
    """Raised when security-related operations fail."""


class EnvironmentError(ConfigurationError):
    """Raised when environment configuration is invalid."""


class S3OperationError(AlchemiserError):
    """Raised when S3 operations fail."""

    def __init__(
        self,
        message: str,
        bucket: str | None = None,
        key: str | None = None,
        operation: str | None = None,
    ) -> None:
        """Create an S3 operation error with AWS details."""
        context: dict[str, Any] = {}
        if bucket:
            context["bucket"] = bucket
        if key:
            context["key"] = key
        if operation:
            context["operation"] = operation

        super().__init__(message, context)
        self.bucket = bucket
        self.key = key
        self.operation = operation
