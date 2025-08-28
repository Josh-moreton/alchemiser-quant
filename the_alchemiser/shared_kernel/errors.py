"""Business Unit: utilities; Status: current.

Shared kernel base exceptions.

Only truly ubiquitous exceptions that are used across all bounded contexts.
Context-specific errors should be defined in their respective domain/errors modules.
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
        self, message: str, config_key: str | None = None, config_value: Any = None
    ) -> None:
        """Raise when configuration values are missing or invalid."""
        context = {}
        if config_key:
            context["config_key"] = config_key
        if config_value is not None:
            context["config_value"] = str(config_value)  # Convert to string for safety
        super().__init__(message, context)
        self.config_key = config_key
        self.config_value = config_value


class DataProviderError(AlchemiserError):
    """Raised when data provider operations fail."""


class TradingClientError(AlchemiserError):
    """Raised when trading client operations fail."""


class ValidationError(AlchemiserError):
    """Raised when data validation fails."""

    def __init__(
        self, message: str, field_name: str | None = None, value: Any | None = None
    ) -> None:
        """Create a validation error for invalid user data."""
        super().__init__(message)
        self.field_name = field_name
        self.value = value


class NotificationError(AlchemiserError):
    """Raised when notification sending fails."""


class S3OperationError(AlchemiserError):
    """Raised when S3 operations fail."""


class SecurityError(AlchemiserError):
    """Raised when security-related issues occur."""


class RateLimitError(AlchemiserError):
    """Raised when API rate limits are exceeded."""

    def __init__(self, message: str, retry_after: int | None = None) -> None:
        """Raise when API rate limit is exceeded."""
        super().__init__(message)
        self.retry_after = retry_after


class StreamingError(DataProviderError):
    """Raised when streaming data issues occur."""