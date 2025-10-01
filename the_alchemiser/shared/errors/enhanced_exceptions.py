#!/usr/bin/env python3
"""Business Unit: shared; Status: current.

Enhanced exception classes with production monitoring support.

This module provides enhanced exception classes with context tracking,
retry metadata, and monitoring support.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from .error_types import ErrorSeverity

if TYPE_CHECKING:
    from .context import ErrorContextData

# Import base exception
try:
    from the_alchemiser.shared.types.exceptions import AlchemiserError
except ImportError:

    class AlchemiserError(Exception):  # type: ignore[no-redef]
        """Fallback AlchemiserError."""


# Define ErrorData type for context
ErrorData = dict[str, str | int | float | bool | None]

# Define FlexibleContext after ErrorContextData is available
FlexibleContext = "ErrorContextData | ErrorData | None"


class EnhancedAlchemiserError(AlchemiserError):
    """Enhanced base exception with production monitoring support."""

    def __init__(
        self,
        message: str,
        context: ErrorContextData | ErrorData | None = None,
        severity: str = ErrorSeverity.MEDIUM,
        *,
        recoverable: bool = True,
        retry_count: int = 0,
        max_retries: int = 3,
    ) -> None:
        """Initialize enhanced base error with context and retry metadata."""
        super().__init__(message)
        if context is not None:
            if hasattr(context, "to_dict"):
                self.context = context.to_dict()
            elif isinstance(context, dict):
                self.context = context
            else:
                self.context = {}
        else:
            self.context = {}
        self.severity = severity
        self.recoverable = recoverable
        self.retry_count = retry_count
        self.max_retries = max_retries
        self.error_id = str(uuid.uuid4())
        self.original_message = message

        # Set error_id in context for logging
        try:
            from the_alchemiser.shared.logging import set_error_id

            set_error_id(self.error_id)
        except ImportError:
            # Avoid circular import issues during module initialization
            pass

    def should_retry(self) -> bool:
        """Determine if error should be retried."""
        return self.recoverable and self.retry_count < self.max_retries

    def get_retry_delay(self) -> float:
        """Get exponential backoff delay for retries."""
        return min(2.0**self.retry_count, 60.0)  # Max 60 seconds

    def increment_retry(self) -> EnhancedAlchemiserError:
        """Create a new instance with incremented retry count."""
        return self.__class__(
            message=self.original_message,
            context=self.context,
            severity=self.severity,
            recoverable=self.recoverable,
            retry_count=self.retry_count + 1,
            max_retries=self.max_retries,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to structured data for logging/reporting."""
        base_dict = super().to_dict()

        # Handle context conversion - it's always a dict now
        context_dict = self.context if self.context else None

        base_dict.update(
            {
                "error_id": self.error_id,
                "severity": self.severity,
                "recoverable": self.recoverable,
                "retry_count": self.retry_count,
                "max_retries": self.max_retries,
                "context": context_dict,
            }
        )
        return base_dict


class EnhancedTradingError(EnhancedAlchemiserError):
    """Enhanced trading error with position and order context."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        order_id: str | None = None,
        quantity: float | None = None,
        price: float | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        """Initialize trading error with optional symbol/order/quantity/price."""
        super().__init__(message, **kwargs)
        self.symbol = symbol
        self.order_id = order_id
        self.quantity = quantity
        self.price = price

    def to_dict(self) -> dict[str, Any]:
        """Include trading-specific context in serialization."""
        base_dict = super().to_dict()
        base_dict.update(
            {
                "symbol": self.symbol,
                "order_id": self.order_id,
                "quantity": self.quantity,
                "price": self.price,
            }
        )
        return base_dict


class EnhancedDataError(EnhancedAlchemiserError):
    """Enhanced data error with data source context."""

    def __init__(
        self,
        message: str,
        data_source: str | None = None,
        data_type: str | None = None,
        symbol: str | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
        """Initialize data error with optional source/type/symbol context."""
        super().__init__(message, **kwargs)
        self.data_source = data_source
        self.data_type = data_type
        self.symbol = symbol

    def to_dict(self) -> dict[str, Any]:
        """Include data-specific context in serialization."""
        base_dict = super().to_dict()
        base_dict.update(
            {
                "data_source": self.data_source,
                "data_type": self.data_type,
                "symbol": self.symbol,
            }
        )
        return base_dict
