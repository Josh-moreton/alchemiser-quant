"""Comprehensive error taxonomy for order execution."""

from __future__ import annotations

from enum import Enum
from typing import Dict, Any
from dataclasses import dataclass
from datetime import datetime, UTC


class OrderErrorCategory(str, Enum):
    """High-level error categories for order execution."""

    VALIDATION = "validation"
    LIQUIDITY = "liquidity"
    RISK_MANAGEMENT = "risk_management"
    MARKET_CONDITIONS = "market_conditions"
    SYSTEM = "system"
    CONNECTIVITY = "connectivity"
    AUTHORIZATION = "authorization"
    CONFIGURATION = "configuration"


class OrderErrorCode(str, Enum):
    """Specific error codes for order execution failures."""

    # Validation errors
    INVALID_SYMBOL = "invalid_symbol"
    INVALID_QUANTITY = "invalid_quantity"
    INVALID_PRICE = "invalid_price"
    MISSING_REQUIRED_FIELD = "missing_required_field"
    DUPLICATE_ORDER = "duplicate_order"

    # Liquidity errors
    INSUFFICIENT_BUYING_POWER = "insufficient_buying_power"
    POSITION_LIMIT_EXCEEDED = "position_limit_exceeded"
    ORDER_SIZE_TOO_LARGE = "order_size_too_large"
    ASSET_NOT_FRACTIONABLE = "asset_not_fractionable"

    # Risk management errors
    CONCENTRATION_LIMIT_EXCEEDED = "concentration_limit_exceeded"
    NOTIONAL_LIMIT_EXCEEDED = "notional_limit_exceeded"
    DAILY_TRADE_LIMIT_EXCEEDED = "daily_trade_limit_exceeded"
    PDT_VIOLATION = "pdt_violation"

    # Market conditions
    MARKET_CLOSED = "market_closed"
    TRADING_HALTED = "trading_halted"
    WIDE_SPREAD = "wide_spread"
    LOW_LIQUIDITY = "low_liquidity"
    PRICE_TOO_FAR_FROM_MARKET = "price_too_far_from_market"

    # System errors
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"
    SYSTEM_UNAVAILABLE = "system_unavailable"
    INTERNAL_ERROR = "internal_error"

    # Connectivity errors
    CONNECTION_LOST = "connection_lost"
    NETWORK_ERROR = "network_error"
    WEBSOCKET_DISCONNECTED = "websocket_disconnected"

    # Authorization errors
    INVALID_CREDENTIALS = "invalid_credentials"
    INSUFFICIENT_PERMISSIONS = "insufficient_permissions"
    ACCOUNT_SUSPENDED = "account_suspended"

    # Configuration errors
    INVALID_CONFIGURATION = "invalid_configuration"
    STRATEGY_DISABLED = "strategy_disabled"
    SYMBOL_NOT_SUPPORTED = "symbol_not_supported"


@dataclass(frozen=True)
class OrderError:
    """Comprehensive order error with structured information."""

    error_code: OrderErrorCode
    category: OrderErrorCategory
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    retryable: bool
    suggested_action: str | None = None

    @classmethod
    def create(
        cls,
        error_code: OrderErrorCode,
        message: str,
        details: Dict[str, Any] | None = None,
        suggested_action: str | None = None,
    ) -> OrderError:
        """Create an OrderError with automatic category mapping."""
        category = ERROR_CODE_TO_CATEGORY.get(error_code, OrderErrorCategory.SYSTEM)
        retryable = error_code in RETRYABLE_ERROR_CODES
        
        return cls(
            error_code=error_code,
            category=category,
            message=message,
            details=details or {},
            timestamp=datetime.now(UTC),
            retryable=retryable,
            suggested_action=suggested_action,
        )


# Error code to category mapping
ERROR_CODE_TO_CATEGORY: Dict[OrderErrorCode, OrderErrorCategory] = {
    # Validation
    OrderErrorCode.INVALID_SYMBOL: OrderErrorCategory.VALIDATION,
    OrderErrorCode.INVALID_QUANTITY: OrderErrorCategory.VALIDATION,
    OrderErrorCode.INVALID_PRICE: OrderErrorCategory.VALIDATION,
    OrderErrorCode.MISSING_REQUIRED_FIELD: OrderErrorCategory.VALIDATION,
    OrderErrorCode.DUPLICATE_ORDER: OrderErrorCategory.VALIDATION,

    # Liquidity
    OrderErrorCode.INSUFFICIENT_BUYING_POWER: OrderErrorCategory.LIQUIDITY,
    OrderErrorCode.POSITION_LIMIT_EXCEEDED: OrderErrorCategory.LIQUIDITY,
    OrderErrorCode.ORDER_SIZE_TOO_LARGE: OrderErrorCategory.LIQUIDITY,
    OrderErrorCode.ASSET_NOT_FRACTIONABLE: OrderErrorCategory.LIQUIDITY,

    # Risk management
    OrderErrorCode.CONCENTRATION_LIMIT_EXCEEDED: OrderErrorCategory.RISK_MANAGEMENT,
    OrderErrorCode.NOTIONAL_LIMIT_EXCEEDED: OrderErrorCategory.RISK_MANAGEMENT,
    OrderErrorCode.DAILY_TRADE_LIMIT_EXCEEDED: OrderErrorCategory.RISK_MANAGEMENT,
    OrderErrorCode.PDT_VIOLATION: OrderErrorCategory.RISK_MANAGEMENT,

    # Market conditions
    OrderErrorCode.MARKET_CLOSED: OrderErrorCategory.MARKET_CONDITIONS,
    OrderErrorCode.TRADING_HALTED: OrderErrorCategory.MARKET_CONDITIONS,
    OrderErrorCode.WIDE_SPREAD: OrderErrorCategory.MARKET_CONDITIONS,
    OrderErrorCode.LOW_LIQUIDITY: OrderErrorCategory.MARKET_CONDITIONS,
    OrderErrorCode.PRICE_TOO_FAR_FROM_MARKET: OrderErrorCategory.MARKET_CONDITIONS,

    # System
    OrderErrorCode.TIMEOUT: OrderErrorCategory.SYSTEM,
    OrderErrorCode.RATE_LIMITED: OrderErrorCategory.SYSTEM,
    OrderErrorCode.SYSTEM_UNAVAILABLE: OrderErrorCategory.SYSTEM,
    OrderErrorCode.INTERNAL_ERROR: OrderErrorCategory.SYSTEM,

    # Connectivity
    OrderErrorCode.CONNECTION_LOST: OrderErrorCategory.CONNECTIVITY,
    OrderErrorCode.NETWORK_ERROR: OrderErrorCategory.CONNECTIVITY,
    OrderErrorCode.WEBSOCKET_DISCONNECTED: OrderErrorCategory.CONNECTIVITY,

    # Authorization
    OrderErrorCode.INVALID_CREDENTIALS: OrderErrorCategory.AUTHORIZATION,
    OrderErrorCode.INSUFFICIENT_PERMISSIONS: OrderErrorCategory.AUTHORIZATION,
    OrderErrorCode.ACCOUNT_SUSPENDED: OrderErrorCategory.AUTHORIZATION,

    # Configuration
    OrderErrorCode.INVALID_CONFIGURATION: OrderErrorCategory.CONFIGURATION,
    OrderErrorCode.STRATEGY_DISABLED: OrderErrorCategory.CONFIGURATION,
    OrderErrorCode.SYMBOL_NOT_SUPPORTED: OrderErrorCategory.CONFIGURATION,
}

# Retryable error codes
RETRYABLE_ERROR_CODES = {
    OrderErrorCode.TIMEOUT,
    OrderErrorCode.RATE_LIMITED,
    OrderErrorCode.CONNECTION_LOST,
    OrderErrorCode.NETWORK_ERROR,
    OrderErrorCode.WEBSOCKET_DISCONNECTED,
    OrderErrorCode.SYSTEM_UNAVAILABLE,
    OrderErrorCode.WIDE_SPREAD,
    OrderErrorCode.LOW_LIQUIDITY,
}

# Default suggested actions for common errors
DEFAULT_SUGGESTED_ACTIONS: Dict[OrderErrorCode, str] = {
    OrderErrorCode.INSUFFICIENT_BUYING_POWER: "Check account balance and reduce position size",
    OrderErrorCode.ASSET_NOT_FRACTIONABLE: "Round down to whole shares and retry",
    OrderErrorCode.MARKET_CLOSED: "Wait for market open or use extended hours",
    OrderErrorCode.WIDE_SPREAD: "Wait for spread to narrow or use market order",
    OrderErrorCode.TIMEOUT: "Retry with shorter timeout or check connectivity",
    OrderErrorCode.RATE_LIMITED: "Wait before retrying to avoid rate limits",
    OrderErrorCode.TRADING_HALTED: "Wait for trading to resume",
    OrderErrorCode.PRICE_TOO_FAR_FROM_MARKET: "Adjust limit price closer to market",
    OrderErrorCode.CONCENTRATION_LIMIT_EXCEEDED: "Reduce allocation to stay within limits",
    OrderErrorCode.DUPLICATE_ORDER: "Check for existing orders before submitting",
}


class OrderErrorClassifier:
    """Classifier for mapping exceptions to structured OrderError objects."""

    def __init__(self) -> None:
        """Initialize the error classifier."""
        self.error_patterns = self._build_error_patterns()

    def classify_exception(
        self,
        exception: Exception,
        context: Dict[str, Any] | None = None,
    ) -> OrderError:
        """Classify an exception into a structured OrderError."""
        error_message = str(exception)
        exception_type = type(exception).__name__
        
        # Try to match error patterns
        for pattern, error_code in self.error_patterns.items():
            if pattern.lower() in error_message.lower():
                suggested_action = DEFAULT_SUGGESTED_ACTIONS.get(error_code)
                return OrderError.create(
                    error_code=error_code,
                    message=error_message,
                    details={
                        "exception_type": exception_type,
                        "context": context or {},
                    },
                    suggested_action=suggested_action,
                )
        
        # Fallback to generic internal error
        return OrderError.create(
            error_code=OrderErrorCode.INTERNAL_ERROR,
            message=f"{exception_type}: {error_message}",
            details={
                "exception_type": exception_type,
                "context": context or {},
            },
            suggested_action="Check logs for detailed error information",
        )

    def classify_alpaca_error(
        self,
        alpaca_error: Exception,
        context: Dict[str, Any] | None = None,
    ) -> OrderError:
        """Classify Alpaca-specific errors."""
        error_message = str(alpaca_error).lower()
        
        # Alpaca-specific error patterns
        if "insufficient buying power" in error_message:
            return OrderError.create(
                OrderErrorCode.INSUFFICIENT_BUYING_POWER,
                str(alpaca_error),
                context,
                DEFAULT_SUGGESTED_ACTIONS[OrderErrorCode.INSUFFICIENT_BUYING_POWER],
            )
        elif "not fractionable" in error_message:
            return OrderError.create(
                OrderErrorCode.ASSET_NOT_FRACTIONABLE,
                str(alpaca_error),
                context,
                DEFAULT_SUGGESTED_ACTIONS[OrderErrorCode.ASSET_NOT_FRACTIONABLE],
            )
        elif "market is closed" in error_message:
            return OrderError.create(
                OrderErrorCode.MARKET_CLOSED,
                str(alpaca_error),
                context,
                DEFAULT_SUGGESTED_ACTIONS[OrderErrorCode.MARKET_CLOSED],
            )
        elif "trading halted" in error_message:
            return OrderError.create(
                OrderErrorCode.TRADING_HALTED,
                str(alpaca_error),
                context,
                DEFAULT_SUGGESTED_ACTIONS[OrderErrorCode.TRADING_HALTED],
            )
        elif "timeout" in error_message:
            return OrderError.create(
                OrderErrorCode.TIMEOUT,
                str(alpaca_error),
                context,
                DEFAULT_SUGGESTED_ACTIONS[OrderErrorCode.TIMEOUT],
            )
        elif "rate limit" in error_message:
            return OrderError.create(
                OrderErrorCode.RATE_LIMITED,
                str(alpaca_error),
                context,
                DEFAULT_SUGGESTED_ACTIONS[OrderErrorCode.RATE_LIMITED],
            )
        
        # Fall back to generic classification
        return self.classify_exception(alpaca_error, context)

    def _build_error_patterns(self) -> Dict[str, OrderErrorCode]:
        """Build error pattern matching dictionary."""
        return {
            "invalid symbol": OrderErrorCode.INVALID_SYMBOL,
            "invalid quantity": OrderErrorCode.INVALID_QUANTITY,
            "invalid price": OrderErrorCode.INVALID_PRICE,
            "insufficient buying power": OrderErrorCode.INSUFFICIENT_BUYING_POWER,
            "not fractionable": OrderErrorCode.ASSET_NOT_FRACTIONABLE,
            "market closed": OrderErrorCode.MARKET_CLOSED,
            "trading halted": OrderErrorCode.TRADING_HALTED,
            "timeout": OrderErrorCode.TIMEOUT,
            "rate limit": OrderErrorCode.RATE_LIMITED,
            "connection": OrderErrorCode.CONNECTION_LOST,
            "network": OrderErrorCode.NETWORK_ERROR,
            "authorization": OrderErrorCode.INVALID_CREDENTIALS,
            "permission": OrderErrorCode.INSUFFICIENT_PERMISSIONS,
            "duplicate": OrderErrorCode.DUPLICATE_ORDER,
            "concentration": OrderErrorCode.CONCENTRATION_LIMIT_EXCEEDED,
            "position limit": OrderErrorCode.POSITION_LIMIT_EXCEEDED,
        }