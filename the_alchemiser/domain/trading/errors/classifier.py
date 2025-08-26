#!/usr/bin/env python3
"""
Order Error Classifier for mapping exceptions to structured OrderError instances.

This module provides registry-driven classification of various error types
into standardized OrderError value objects for consistent error handling.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from the_alchemiser.domain.shared_kernel.value_objects.identifier import Identifier

from .error_categories import OrderErrorCategory
from .error_codes import OrderErrorCode
from .order_error import OrderError

# Type aliases for classifier functions
ClassificationContext = dict[str, Any]
ClassificationPredicate = Callable[[ClassificationContext], bool]
ErrorBuilder = Callable[[ClassificationContext], OrderError]


class ClassificationRule:
    """A rule for classifying errors based on context."""

    def __init__(
        self,
        predicate: ClassificationPredicate,
        builder: ErrorBuilder,
        description: str = "",
    ):
        self.predicate = predicate
        self.builder = builder
        self.description = description

    def matches(self, context: ClassificationContext) -> bool:
        """Check if this rule matches the given context."""
        try:
            return self.predicate(context)
        except Exception:
            return False

    def build_error(self, context: ClassificationContext) -> OrderError:
        """Build an OrderError from the context."""
        return self.builder(context)


class OrderErrorClassifier:
    """Classifier for mapping exceptions and broker responses to OrderError instances.

    Uses a registry-driven approach with ordered rules to provide deterministic
    classification of order-related failures.
    """

    def __init__(self) -> None:
        """Initialize classifier with default rules."""
        self._rules: list[ClassificationRule] = []
        self._register_default_rules()

    def classify_exception(
        self,
        exc: Exception,
        order_id: Identifier[Any] | None = None,
        additional_context: dict[str, Any] | None = None,
    ) -> OrderError:
        """Classify a Python exception into an OrderError.

        Args:
            exc: The exception to classify
            order_id: Associated order ID if available
            additional_context: Additional context for classification

        Returns:
            Structured OrderError instance
        """
        context: ClassificationContext = {
            "type": "exception",
            "exception": exc,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "order_id": order_id,
            **(additional_context or {}),
        }

        return self._classify_with_rules(context)

    def classify_alpaca_error(
        self,
        response_json: Mapping[str, Any],
        order_id: Identifier[Any] | None = None,
        additional_context: dict[str, Any] | None = None,
    ) -> OrderError:
        """Classify an Alpaca API error response into an OrderError.

        Args:
            response_json: Alpaca API error response data
            order_id: Associated order ID if available
            additional_context: Additional context for classification

        Returns:
            Structured OrderError instance
        """
        context: ClassificationContext = {
            "type": "alpaca_error",
            "response": response_json,
            "error_code": response_json.get("code"),
            "error_message": response_json.get("message", ""),
            "order_id": order_id,
            **(additional_context or {}),
        }

        return self._classify_with_rules(context)

    def classify_validation_failure(
        self,
        reason: str,
        data: Mapping[str, Any],
        order_id: Identifier[Any] | None = None,
    ) -> OrderError:
        """Classify a validation failure into an OrderError.

        Args:
            reason: Validation failure reason
            data: Validation context data
            order_id: Associated order ID if available

        Returns:
            Structured OrderError instance
        """
        context: ClassificationContext = {
            "type": "validation_failure",
            "reason": reason,
            "data": data,
            "order_id": order_id,
        }

        return self._classify_with_rules(context)

    def _classify_with_rules(self, context: ClassificationContext) -> OrderError:
        """Apply classification rules to context and return OrderError."""
        for rule in self._rules:
            if rule.matches(context):
                return rule.build_error(context)

        # Fallback to generic system error
        return self._build_fallback_error(context)

    def _build_fallback_error(self, context: ClassificationContext) -> OrderError:
        """Build a fallback error when no rules match."""
        message = (
            context.get("exception_message")
            or context.get("error_message")
            or context.get("reason")
            or "Unknown error"
        )

        return OrderError(
            category=OrderErrorCategory.SYSTEM,
            code=OrderErrorCode.INTERNAL_SERVICE_ERROR,
            message=f"Unclassified error: {message}",
            order_id=context.get("order_id"),
            details=dict(context),
            original_exception=context.get("exception"),
            is_transient=False,
            timestamp=datetime.now(UTC),
        )

    def add_rule(self, rule: ClassificationRule) -> None:
        """Add a custom classification rule."""
        self._rules.insert(0, rule)  # Insert at beginning for priority

    def _register_default_rules(self) -> None:
        """Register default classification rules."""

        # VALIDATION errors
        self._rules.extend(
            [
                ClassificationRule(
                    predicate=lambda ctx: "invalid symbol"
                    in str(ctx.get("exception_message", "")).lower()
                    or "symbol" in str(ctx.get("error_message", "")).lower()
                    and "invalid" in str(ctx.get("error_message", "")).lower(),
                    builder=lambda ctx: OrderError(
                        category=OrderErrorCategory.VALIDATION,
                        code=OrderErrorCode.INVALID_SYMBOL,
                        message=str(
                            ctx.get("exception_message")
                            or ctx.get("error_message")
                            or "Invalid symbol"
                        ),
                        order_id=ctx.get("order_id"),
                        details=self._extract_details(ctx),
                        original_exception=ctx.get("exception"),
                        is_transient=False,
                    ),
                    description="Invalid symbol validation error",
                ),
                ClassificationRule(
                    predicate=lambda ctx: (
                        "quantity" in str(ctx.get("exception_message", "")).lower()
                        and any(
                            word in str(ctx.get("exception_message", "")).lower()
                            for word in ["invalid", "negative", "zero"]
                        )
                    )
                    or (
                        "quantity" in str(ctx.get("reason", "")).lower()
                        and ctx.get("type") == "validation_failure"
                    ),
                    builder=lambda ctx: OrderError(
                        category=OrderErrorCategory.VALIDATION,
                        code=OrderErrorCode.INVALID_QUANTITY,
                        message=str(
                            ctx.get("exception_message")
                            or ctx.get("error_message")
                            or ctx.get("reason")
                            or "Invalid quantity"
                        ),
                        order_id=ctx.get("order_id"),
                        details=self._extract_details(ctx),
                        original_exception=ctx.get("exception"),
                        is_transient=False,
                    ),
                    description="Invalid quantity validation error",
                ),
                ClassificationRule(
                    predicate=lambda ctx: "fractional"
                    in str(ctx.get("exception_message", "")).lower()
                    or "fractional" in str(ctx.get("error_message", "")).lower(),
                    builder=lambda ctx: OrderError(
                        category=OrderErrorCategory.VALIDATION,
                        code=OrderErrorCode.FRACTIONAL_NOT_ALLOWED,
                        message=str(
                            ctx.get("exception_message")
                            or ctx.get("error_message")
                            or "Fractional shares not allowed"
                        ),
                        order_id=ctx.get("order_id"),
                        details=self._extract_details(ctx),
                        original_exception=ctx.get("exception"),
                        is_transient=False,
                    ),
                    description="Fractional shares not allowed error",
                ),
            ]
        )

        # Additional VALIDATION rules (previously unreachable codes)
        self._rules.extend(
            [
                # Unsupported order type
                ClassificationRule(
                    predicate=lambda ctx: any(
                        phrase in str(ctx.get("exception_message", "")).lower()
                        or phrase in str(ctx.get("error_message", "")).lower()
                        or phrase in str(ctx.get("reason", "")).lower()
                        for phrase in [
                            "unsupported order type",
                            "order type not supported",
                            "unsupported type",
                            "unsupported order",
                        ]
                    ),
                    builder=lambda ctx: OrderError(
                        category=OrderErrorCategory.VALIDATION,
                        code=OrderErrorCode.UNSUPPORTED_ORDER_TYPE,
                        message=str(
                            ctx.get("exception_message")
                            or ctx.get("error_message")
                            or ctx.get("reason")
                            or "Unsupported order type"
                        ),
                        order_id=ctx.get("order_id"),
                        details=self._extract_details(ctx),
                        original_exception=ctx.get("exception"),
                        is_transient=False,
                    ),
                    description="Unsupported order type validation error",
                ),
                # Price out of bounds
                ClassificationRule(
                    predicate=lambda ctx: any(
                        phrase in str(ctx.get("exception_message", "")).lower()
                        or phrase in str(ctx.get("error_message", "")).lower()
                        or phrase in str(ctx.get("reason", "")).lower()
                        for phrase in [
                            "price out of bounds",
                            "price out of range",
                            "outside price limits",
                            "price too high",
                            "price too low",
                            "outside acceptable range",
                        ]
                    )
                    and "limit up" not in str(ctx.get("exception_message", "")).lower()
                    and "limit down" not in str(ctx.get("exception_message", "")).lower(),
                    builder=lambda ctx: OrderError(
                        category=OrderErrorCategory.VALIDATION,
                        code=OrderErrorCode.PRICE_OUT_OF_BOUNDS,
                        message=str(
                            ctx.get("exception_message")
                            or ctx.get("error_message")
                            or ctx.get("reason")
                            or "Price out of bounds"
                        ),
                        order_id=ctx.get("order_id"),
                        details=self._extract_details(ctx),
                        original_exception=ctx.get("exception"),
                        is_transient=False,
                    ),
                    description="Price out of bounds validation error",
                ),
                # Duplicate client order id
                ClassificationRule(
                    predicate=lambda ctx: any(
                        phrase in str(ctx.get("exception_message", "")).lower()
                        or phrase in str(ctx.get("error_message", "")).lower()
                        for phrase in [
                            "duplicate client order id",
                            "duplicate client_order_id",
                            "client order id already",
                            "client_order_id already",
                        ]
                    ),
                    builder=lambda ctx: OrderError(
                        category=OrderErrorCategory.VALIDATION,
                        code=OrderErrorCode.DUPLICATE_CLIENT_ORDER_ID,
                        message=str(
                            ctx.get("exception_message")
                            or ctx.get("error_message")
                            or "Duplicate client order id"
                        ),
                        order_id=ctx.get("order_id"),
                        details=self._extract_details(ctx),
                        original_exception=ctx.get("exception"),
                        is_transient=False,
                    ),
                    description="Duplicate client order id validation error",
                ),
            ]
        )

        # RISK_MANAGEMENT errors
        self._rules.extend(
            [
                ClassificationRule(
                    predicate=lambda ctx: any(
                        phrase in str(ctx.get("exception_message", "")).lower()
                        for phrase in [
                            "insufficient funds",
                            "insufficient buying power",
                            "insufficient_funds",
                        ]
                    )
                    or ctx.get("exception_type") == "InsufficientFundsError",
                    builder=lambda ctx: OrderError(
                        category=OrderErrorCategory.RISK_MANAGEMENT,
                        code=OrderErrorCode.INSUFFICIENT_BUYING_POWER,
                        message=str(
                            ctx.get("exception_message")
                            or ctx.get("error_message")
                            or "Insufficient buying power"
                        ),
                        order_id=ctx.get("order_id"),
                        details=self._extract_details(ctx),
                        original_exception=ctx.get("exception"),
                        is_transient=False,
                    ),
                    description="Insufficient buying power error",
                ),
                ClassificationRule(
                    predicate=lambda ctx: "position limit"
                    in str(ctx.get("exception_message", "")).lower()
                    or "position_limit" in str(ctx.get("error_message", "")).lower(),
                    builder=lambda ctx: OrderError(
                        category=OrderErrorCategory.RISK_MANAGEMENT,
                        code=OrderErrorCode.POSITION_LIMIT_EXCEEDED,
                        message=str(
                            ctx.get("exception_message")
                            or ctx.get("error_message")
                            or "Position limit exceeded"
                        ),
                        order_id=ctx.get("order_id"),
                        details=self._extract_details(ctx),
                        original_exception=ctx.get("exception"),
                        is_transient=False,
                    ),
                    description="Position limit exceeded error",
                ),
            ]
        )
        # Additional RISK_MANAGEMENT rules
        self._rules.extend(
            [
                ClassificationRule(
                    predicate=lambda ctx: any(
                        phrase in str(ctx.get("exception_message", "")).lower()
                        or phrase in str(ctx.get("error_message", "")).lower()
                        for phrase in [
                            "order value exceeds",
                            "max order value",
                            "order value limit",
                            "value limit exceeded",
                        ]
                    ),
                    builder=lambda ctx: OrderError(
                        category=OrderErrorCategory.RISK_MANAGEMENT,
                        code=OrderErrorCode.ORDER_VALUE_LIMIT_EXCEEDED,
                        message=str(
                            ctx.get("exception_message")
                            or ctx.get("error_message")
                            or "Order value limit exceeded"
                        ),
                        order_id=ctx.get("order_id"),
                        details=self._extract_details(ctx),
                        original_exception=ctx.get("exception"),
                        is_transient=False,
                    ),
                    description="Order value limit exceeded risk management error",
                ),
                ClassificationRule(
                    predicate=lambda ctx: any(
                        phrase in str(ctx.get("exception_message", "")).lower()
                        or phrase in str(ctx.get("error_message", "")).lower()
                        for phrase in [
                            "max daily trades",
                            "daily trade limit",
                            "too many trades today",
                            "pattern day trader",
                        ]
                    ),
                    builder=lambda ctx: OrderError(
                        category=OrderErrorCategory.RISK_MANAGEMENT,
                        code=OrderErrorCode.MAX_DAILY_TRADES_EXCEEDED,
                        message=str(
                            ctx.get("exception_message")
                            or ctx.get("error_message")
                            or "Max daily trades exceeded"
                        ),
                        order_id=ctx.get("order_id"),
                        details=self._extract_details(ctx),
                        original_exception=ctx.get("exception"),
                        is_transient=False,
                    ),
                    description="Max daily trades exceeded risk management error",
                ),
            ]
        )

        # CONNECTIVITY and SYSTEM timeout distinctions
        self._rules.extend(
            [
                ClassificationRule(
                    predicate=lambda ctx: any(
                        phrase in str(ctx.get("exception_message", "")).lower()
                        for phrase in ["network", "connection", "unreachable"]
                    )
                    or ctx.get("exception_type") in ["ConnectionError", "NetworkError"],
                    builder=lambda ctx: OrderError(
                        category=OrderErrorCategory.CONNECTIVITY,
                        code=OrderErrorCode.NETWORK_UNREACHABLE,
                        message=str(
                            ctx.get("exception_message")
                            or ctx.get("error_message")
                            or "Network connectivity issue"
                        ),
                        order_id=ctx.get("order_id"),
                        details=self._extract_details(ctx),
                        original_exception=ctx.get("exception"),
                        is_transient=True,
                    ),
                    description="Network connectivity error",
                ),
                ClassificationRule(
                    predicate=lambda ctx: "timeout" in str(ctx.get("exception_message", "")).lower()
                    or ctx.get("exception_type") == "TimeoutError",
                    builder=lambda ctx: OrderError(
                        category=OrderErrorCategory.SYSTEM,
                        code=OrderErrorCode.TIMEOUT,
                        message=str(
                            ctx.get("exception_message")
                            or ctx.get("error_message")
                            or "Operation timed out"
                        ),
                        order_id=ctx.get("order_id"),
                        details=self._extract_details(ctx),
                        original_exception=ctx.get("exception"),
                        is_transient=True,
                    ),
                    description="System timeout error",
                ),
                ClassificationRule(
                    predicate=lambda ctx: "rate limit"
                    in str(ctx.get("exception_message", "")).lower()
                    or "rate_limit" in str(ctx.get("error_message", "")).lower()
                    or ctx.get("error_code") == 429,
                    builder=lambda ctx: OrderError(
                        category=OrderErrorCategory.CONNECTIVITY,
                        code=OrderErrorCode.RATE_LIMITED,
                        message=str(
                            ctx.get("exception_message")
                            or ctx.get("error_message")
                            or "Rate limit exceeded"
                        ),
                        order_id=ctx.get("order_id"),
                        details=self._extract_details(ctx),
                        original_exception=ctx.get("exception"),
                        is_transient=True,
                    ),
                    description="Rate limit exceeded error",
                ),
            ]
        )
        # Additional CONNECTIVITY rules
        self._rules.extend(
            [
                ClassificationRule(
                    predicate=lambda ctx: any(
                        phrase in str(ctx.get("exception_message", "")).lower()
                        or phrase in str(ctx.get("error_message", "")).lower()
                        for phrase in [
                            "broker api unavailable",
                            "service unavailable",
                            "temporarily unavailable",
                        ]
                    )
                    or ctx.get("error_code") in [502, 503, 504],
                    builder=lambda ctx: OrderError(
                        category=OrderErrorCategory.CONNECTIVITY,
                        code=OrderErrorCode.BROKER_API_UNAVAILABLE,
                        message=str(
                            ctx.get("exception_message")
                            or ctx.get("error_message")
                            or "Broker API unavailable"
                        ),
                        order_id=ctx.get("order_id"),
                        details=self._extract_details(ctx),
                        original_exception=ctx.get("exception"),
                        is_transient=True,
                    ),
                    description="Broker API unavailable connectivity error",
                ),
            ]
        )

        # MARKET_CONDITIONS errors
        self._rules.extend(
            [
                ClassificationRule(
                    predicate=lambda ctx: "halted" in str(ctx.get("exception_message", "")).lower()
                    or "halt" in str(ctx.get("error_message", "")).lower(),
                    builder=lambda ctx: OrderError(
                        category=OrderErrorCategory.MARKET_CONDITIONS,
                        code=OrderErrorCode.MARKET_HALTED,
                        message=str(
                            ctx.get("exception_message")
                            or ctx.get("error_message")
                            or "Market halted"
                        ),
                        order_id=ctx.get("order_id"),
                        details=self._extract_details(ctx),
                        original_exception=ctx.get("exception"),
                        is_transient=True,
                    ),
                    description="Market halted error",
                ),
            ]
        )
        # Additional MARKET_CONDITIONS rules
        self._rules.extend(
            [
                ClassificationRule(
                    predicate=lambda ctx: any(
                        phrase in str(ctx.get("exception_message", "")).lower()
                        or phrase in str(ctx.get("error_message", "")).lower()
                        for phrase in [
                            "limit up",
                            "limit down",
                            "luld",
                            "circuit breaker",
                        ]
                    ),
                    builder=lambda ctx: OrderError(
                        category=OrderErrorCategory.MARKET_CONDITIONS,
                        code=OrderErrorCode.LIMIT_UP_DOWN_BREACH,
                        message=str(
                            ctx.get("exception_message")
                            or ctx.get("error_message")
                            or "Limit up/down breach"
                        ),
                        order_id=ctx.get("order_id"),
                        details=self._extract_details(ctx),
                        original_exception=ctx.get("exception"),
                        is_transient=True,
                    ),
                    description="Limit up/down breach market conditions error",
                ),
                ClassificationRule(
                    predicate=lambda ctx: any(
                        phrase in str(ctx.get("exception_message", "")).lower()
                        or phrase in str(ctx.get("error_message", "")).lower()
                        for phrase in ["auction", "opening cross", "closing cross"]
                    ),
                    builder=lambda ctx: OrderError(
                        category=OrderErrorCategory.MARKET_CONDITIONS,
                        code=OrderErrorCode.AUCTION_TRANSITION,
                        message=str(
                            ctx.get("exception_message")
                            or ctx.get("error_message")
                            or "Auction transition"
                        ),
                        order_id=ctx.get("order_id"),
                        details=self._extract_details(ctx),
                        original_exception=ctx.get("exception"),
                        is_transient=True,
                    ),
                    description="Auction transition market conditions error",
                ),
            ]
        )

        # AUTHORIZATION errors
        self._rules.extend(
            [
                ClassificationRule(
                    predicate=lambda ctx: any(
                        phrase in str(ctx.get("exception_message", "")).lower()
                        for phrase in [
                            "unauthorized",
                            "invalid api",
                            "authentication",
                            "forbidden",
                        ]
                    )
                    or ctx.get("error_code") in [401, 403],
                    builder=lambda ctx: OrderError(
                        category=OrderErrorCategory.AUTHORIZATION,
                        code=(
                            OrderErrorCode.INVALID_API_KEYS
                            if "api" in str(ctx.get("exception_message", "")).lower()
                            else OrderErrorCode.PERMISSION_DENIED
                        ),
                        message=str(
                            ctx.get("exception_message")
                            or ctx.get("error_message")
                            or "Authorization failed"
                        ),
                        order_id=ctx.get("order_id"),
                        details=self._extract_details(ctx),
                        original_exception=ctx.get("exception"),
                        is_transient=False,
                    ),
                    description="Authorization error",
                ),
            ]
        )

        # LIQUIDITY errors (originally no predicates)
        self._rules.extend(
            [
                ClassificationRule(
                    predicate=lambda ctx: any(
                        phrase in str(ctx.get("exception_message", "")).lower()
                        or phrase in str(ctx.get("error_message", "")).lower()
                        for phrase in [
                            "insufficient liquidity",
                            "not enough liquidity",
                            "no liquidity",
                        ]
                    ),
                    builder=lambda ctx: OrderError(
                        category=OrderErrorCategory.LIQUIDITY,
                        code=OrderErrorCode.INSUFFICIENT_LIQUIDITY,
                        message=str(
                            ctx.get("exception_message")
                            or ctx.get("error_message")
                            or "Insufficient liquidity"
                        ),
                        order_id=ctx.get("order_id"),
                        details=self._extract_details(ctx),
                        original_exception=ctx.get("exception"),
                        is_transient=True,
                    ),
                    description="Insufficient liquidity error",
                ),
                ClassificationRule(
                    predicate=lambda ctx: any(
                        phrase in str(ctx.get("exception_message", "")).lower()
                        or phrase in str(ctx.get("error_message", "")).lower()
                        for phrase in ["wide spread", "spread too wide"]
                    ),
                    builder=lambda ctx: OrderError(
                        category=OrderErrorCategory.LIQUIDITY,
                        code=OrderErrorCode.WIDE_SPREAD,
                        message=str(
                            ctx.get("exception_message")
                            or ctx.get("error_message")
                            or "Wide spread"
                        ),
                        order_id=ctx.get("order_id"),
                        details=self._extract_details(ctx),
                        original_exception=ctx.get("exception"),
                        is_transient=True,
                    ),
                    description="Wide spread liquidity error",
                ),
                ClassificationRule(
                    predicate=lambda ctx: any(
                        phrase in str(ctx.get("exception_message", "")).lower()
                        or phrase in str(ctx.get("error_message", "")).lower()
                        for phrase in ["no market makers", "no market maker"]
                    ),
                    builder=lambda ctx: OrderError(
                        category=OrderErrorCategory.LIQUIDITY,
                        code=OrderErrorCode.NO_MARKET_MAKERS,
                        message=str(
                            ctx.get("exception_message")
                            or ctx.get("error_message")
                            or "No market makers"
                        ),
                        order_id=ctx.get("order_id"),
                        details=self._extract_details(ctx),
                        original_exception=ctx.get("exception"),
                        is_transient=True,
                    ),
                    description="No market makers liquidity error",
                ),
            ]
        )

        # SYSTEM specific additional rules (beyond fallback)
        self._rules.extend(
            [
                ClassificationRule(
                    predicate=lambda ctx: any(
                        phrase in str(ctx.get("exception_message", "")).lower()
                        or phrase in str(ctx.get("error_message", "")).lower()
                        for phrase in [
                            "serialization",
                            "deserialize",
                            "json decode",
                            "marshal",
                            "unmarshal",
                        ]
                    ),
                    builder=lambda ctx: OrderError(
                        category=OrderErrorCategory.SYSTEM,
                        code=OrderErrorCode.SERIALIZATION_FAILURE,
                        message=str(
                            ctx.get("exception_message")
                            or ctx.get("error_message")
                            or "Serialization failure"
                        ),
                        order_id=ctx.get("order_id"),
                        details=self._extract_details(ctx),
                        original_exception=ctx.get("exception"),
                        is_transient=False,
                    ),
                    description="Serialization / deserialization system error",
                ),
            ]
        )

        # CONFIGURATION rules
        self._rules.extend(
            [
                ClassificationRule(
                    predicate=lambda ctx: any(
                        phrase in str(ctx.get("exception_message", "")).lower()
                        or phrase in str(ctx.get("error_message", "")).lower()
                        for phrase in [
                            "missing configuration",
                            "config missing",
                            "environment variable",
                            "env var",
                            "not configured",
                        ]
                    ),
                    builder=lambda ctx: OrderError(
                        category=OrderErrorCategory.CONFIGURATION,
                        code=OrderErrorCode.MISSING_CONFIGURATION,
                        message=str(
                            ctx.get("exception_message")
                            or ctx.get("error_message")
                            or "Missing configuration"
                        ),
                        order_id=ctx.get("order_id"),
                        details=self._extract_details(ctx),
                        original_exception=ctx.get("exception"),
                        is_transient=False,
                    ),
                    description="Missing configuration error",
                ),
                ClassificationRule(
                    predicate=lambda ctx: any(
                        phrase in str(ctx.get("exception_message", "")).lower()
                        or phrase in str(ctx.get("error_message", "")).lower()
                        for phrase in [
                            "unsupported asset class",
                            "asset class not supported",
                        ]
                    ),
                    builder=lambda ctx: OrderError(
                        category=OrderErrorCategory.CONFIGURATION,
                        code=OrderErrorCode.UNSUPPORTED_ASSET_CLASS,
                        message=str(
                            ctx.get("exception_message")
                            or ctx.get("error_message")
                            or "Unsupported asset class"
                        ),
                        order_id=ctx.get("order_id"),
                        details=self._extract_details(ctx),
                        original_exception=ctx.get("exception"),
                        is_transient=False,
                    ),
                    description="Unsupported asset class configuration error",
                ),
            ]
        )

    def _extract_details(self, context: ClassificationContext) -> dict[str, Any]:
        """Extract relevant details from classification context."""
        details: dict[str, Any] = {}

        # Extract common fields
        for key in ["symbol", "quantity", "price", "order_type", "side"]:
            if key in context:
                value = context[key]
                # Convert numeric values to Decimal for consistency
                if key in ["quantity", "price"] and value is not None:
                    try:
                        details[key] = Decimal(str(value))
                    except (ValueError, TypeError):
                        details[key] = value
                else:
                    details[key] = value

        # Add response/data details if available
        if "response" in context:
            details["broker_response"] = context["response"]
        if "data" in context:
            details["validation_data"] = context["data"]

        return details


# Default classifier instance
default_classifier = OrderErrorClassifier()


# Convenience functions using default classifier
def classify_exception(
    exc: Exception,
    order_id: Identifier[Any] | None = None,
    additional_context: dict[str, Any] | None = None,
) -> OrderError:
    """Classify an exception using the default classifier."""
    return default_classifier.classify_exception(exc, order_id, additional_context)


def classify_alpaca_error(
    response_json: Mapping[str, Any],
    order_id: Identifier[Any] | None = None,
    additional_context: dict[str, Any] | None = None,
) -> OrderError:
    """Classify an Alpaca error using the default classifier."""
    return default_classifier.classify_alpaca_error(response_json, order_id, additional_context)


def classify_validation_failure(
    reason: str,
    data: Mapping[str, Any],
    order_id: Identifier[Any] | None = None,
) -> OrderError:
    """Classify a validation failure using the default classifier."""
    return default_classifier.classify_validation_failure(reason, data, order_id)
