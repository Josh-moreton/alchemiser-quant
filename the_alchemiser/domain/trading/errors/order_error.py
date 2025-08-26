#!/usr/bin/env python3
"""OrderError value object for structured error representation.

This module provides the core OrderError value object that encapsulates
all information about order-related failures in a structured format.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from the_alchemiser.domain.shared_kernel.value_objects.identifier import Identifier

from .error_categories import OrderErrorCategory
from .error_codes import OrderErrorCode


@dataclass(frozen=True)
class OrderError:
    """Structured representation of an order-related error.

    This value object provides a standardized way to represent order failures
    with precise categorization, contextual metadata, and remediation guidance.
    """

    category: OrderErrorCategory
    """High-level error category for routing and analytics"""

    code: OrderErrorCode
    """Specific error code for precise identification"""

    message: str
    """Human-readable error message"""

    order_id: Identifier[Any] | None = None
    """Associated order ID, if available"""

    details: Mapping[str, Any] | None = None
    """Additional contextual details (symbols, quantities, etc.)"""

    original_exception: Exception | None = None
    """Original exception that triggered this error, if any"""

    is_transient: bool = False
    """Whether this error is transient and potentially retryable"""

    timestamp: datetime | None = None
    """When this error occurred"""

    def __post_init__(self) -> None:
        """Set timestamp if not provided."""
        if self.timestamp is None:
            object.__setattr__(self, "timestamp", datetime.now(UTC))

        # Ensure details is converted to dict if needed for immutability
        if self.details is not None and hasattr(self.details, "items"):
            # Convert to dict to ensure consistent type
            details_dict = dict(self.details.items())
            object.__setattr__(self, "details", details_dict)

    def get_detail(self, key: str, default: object = None) -> Any:
        """Get a specific detail value safely."""
        if self.details is None:
            return default
        return self.details.get(key, default)

    def get_symbol(self) -> str | None:
        """Get symbol from details if available."""
        symbol = self.get_detail("symbol")
        return str(symbol) if symbol is not None else None

    def get_quantity(self) -> Decimal | None:
        """Get quantity from details if available, converted to Decimal."""
        qty = self.get_detail("quantity")
        if qty is None:
            return None
        if isinstance(qty, Decimal):
            return qty
        try:
            return Decimal(str(qty))
        except (ValueError, TypeError):
            return None

    def get_price(self) -> Decimal | None:
        """Get price from details if available, converted to Decimal."""
        price = self.get_detail("price")
        if price is None:
            return None
        if isinstance(price, Decimal):
            return price
        try:
            return Decimal(str(price))
        except (ValueError, TypeError):
            return None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation for serialization."""
        return {
            "category": self.category.value,
            "code": self.code.value,
            "message": self.message,
            "order_id": (
                str(self.order_id.value)
                if self.order_id and hasattr(self.order_id, "value")
                else None
            ),
            "details": dict(self.details) if self.details else None,
            "is_transient": self.is_transient,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "original_exception_type": (
                type(self.original_exception).__name__ if self.original_exception else None
            ),
            "original_exception_message": (
                str(self.original_exception)[:500] if self.original_exception else None
            ),
        }

    def format_for_cli(self, include_remediation: bool = True) -> str:
        """Format error for CLI display."""
        base = f"[{self.category.value.upper()}|{self.code.value.upper()}] {self.message}"
        if self.is_transient:
            base += " (transient=True)"

        if include_remediation:
            hint = get_remediation_hint(self.code)
            if hint:
                base += f"\nRemediation: {hint}"

        return base


def get_remediation_hint(code: OrderErrorCode) -> str | None:
    """Get remediation hint for a specific error code."""
    return REMEDIATION_HINTS.get(code)


# Remediation hints mapping for CLI display
REMEDIATION_HINTS: dict[OrderErrorCode, str] = {
    # VALIDATION
    OrderErrorCode.INVALID_SYMBOL: "Verify symbol exists and is tradeable",
    OrderErrorCode.UNSUPPORTED_ORDER_TYPE: "Use supported order type (market, limit, stop)",
    OrderErrorCode.INVALID_QUANTITY: "Check quantity is positive and within limits",
    OrderErrorCode.FRACTIONAL_NOT_ALLOWED: "Use whole share quantities for this symbol",
    OrderErrorCode.PRICE_OUT_OF_BOUNDS: "Adjust price within acceptable range",
    OrderErrorCode.DUPLICATE_CLIENT_ORDER_ID: "Use a unique client order ID",
    # LIQUIDITY
    OrderErrorCode.INSUFFICIENT_LIQUIDITY: "Reduce order size or use limit orders",
    OrderErrorCode.WIDE_SPREAD: "Wait for better market conditions or use limit orders",
    OrderErrorCode.NO_MARKET_MAKERS: "Try during market hours or switch symbols",
    # RISK_MANAGEMENT
    OrderErrorCode.INSUFFICIENT_BUYING_POWER: "Add funds or reduce position size",
    OrderErrorCode.POSITION_LIMIT_EXCEEDED: "Close existing positions or reduce order size",
    OrderErrorCode.ORDER_VALUE_LIMIT_EXCEEDED: "Reduce order value below limits",
    OrderErrorCode.MAX_DAILY_TRADES_EXCEEDED: "Wait until next trading day",
    # MARKET_CONDITIONS
    OrderErrorCode.MARKET_HALTED: "Wait for trading to resume",
    OrderErrorCode.LIMIT_UP_DOWN_BREACH: "Wait for circuit breaker to clear",
    OrderErrorCode.AUCTION_TRANSITION: "Wait for continuous trading to resume",
    # SYSTEM
    OrderErrorCode.INTERNAL_SERVICE_ERROR: "Retry or contact support if persistent",
    OrderErrorCode.SERIALIZATION_FAILURE: "Check order data format and retry",
    OrderErrorCode.TIMEOUT: "Retry with shorter timeout or check connectivity",
    # CONNECTIVITY
    OrderErrorCode.NETWORK_UNREACHABLE: "Check network connection and retry",
    OrderErrorCode.BROKER_API_UNAVAILABLE: "Wait for broker service restoration",
    OrderErrorCode.RATE_LIMITED: "Backoff and retry with exponential delay",
    # AUTHORIZATION
    OrderErrorCode.INVALID_API_KEYS: "Verify API credentials are correct and active",
    OrderErrorCode.PERMISSION_DENIED: "Check account permissions for this operation",
    # CONFIGURATION
    OrderErrorCode.MISSING_CONFIGURATION: "Complete required configuration setup",
    OrderErrorCode.UNSUPPORTED_ASSET_CLASS: "Use supported asset classes only",
}
