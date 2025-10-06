"""Business Unit: shared | Status: current.

Centralized validation utilities for eliminating duplicate __post_init__() methods.

This module consolidates common validation patterns found across schema classes
to eliminate the duplicate __post_init__() methods identified in Priority 2.1.

Type Precision Policy
---------------------
This module uses different numeric types based on the validation context:

- **Decimal**: Used for money amounts and financial ratios that require exact precision
  (e.g., validate_decimal_range, validate_price_positive)
- **float**: Used for quote validation and detection heuristics where approximate
  precision is acceptable (e.g., validate_quote_prices, detect_suspicious_quote_prices)
- **Float comparisons**: Always use math.isclose() with explicit tolerances (rel_tol=1e-9, abs_tol=1e-9)
  Never use == or != on float values per financial-grade guardrails

Validation vs Detection
-----------------------
Functions follow two patterns:
- **Validation functions**: Raise ValueError on contract violations (enforce correctness)
- **Detection functions**: Return bool/tuple for advisory checks (heuristic analysis)
"""

from __future__ import annotations

import math
from datetime import UTC, datetime
from decimal import Decimal

from the_alchemiser.shared.constants import MINIMUM_PRICE
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


def validate_decimal_range(
    value: Decimal,
    min_value: Decimal,
    max_value: Decimal,
    field_name: str = "Value",
) -> None:
    """Validate that a Decimal value is within the specified range [min_value, max_value].

    Args:
        value: The value to validate
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)
        field_name: Name of the field for error messages

    Raises:
        ValueError: If value is outside the valid range

    """
    if not (min_value <= value <= max_value):
        logger.warning(
            "Validation failed: decimal_range",
            extra={
                "field_name": field_name,
                "value": str(value),
                "min_value": str(min_value),
                "max_value": str(max_value),
                "validation_type": "decimal_range",
            },
        )
        raise ValueError(f"{field_name} must be between {min_value} and {max_value}")


def validate_enum_value(
    value: str,
    valid_values: set[str],
    field_name: str = "Value",
) -> None:
    """Validate that a string value is in the set of valid enumeration values.

    Args:
        value: The value to validate
        valid_values: Set of valid enumeration values
        field_name: Name of the field for error messages

    Raises:
        ValueError: If value is not in the valid set

    """
    if value not in valid_values:
        logger.warning(
            "Validation failed: enum_value",
            extra={
                "field_name": field_name,
                "value": value,
                "valid_values": str(valid_values),
                "validation_type": "enum_value",
            },
        )
        raise ValueError(f"{field_name} must be one of {valid_values}")


def validate_non_negative_integer(
    value: Decimal,
    field_name: str = "Value",
) -> None:
    """Validate that a Decimal value is a non-negative whole number.

    Args:
        value: The value to validate
        field_name: Name of the field for error messages

    Raises:
        ValueError: If value is negative or not a whole number

    """
    if value < 0:
        logger.warning(
            "Validation failed: non_negative_integer",
            extra={
                "field_name": field_name,
                "value": str(value),
                "validation_type": "non_negative_integer",
                "reason": "negative_value",
            },
        )
        raise ValueError(f"{field_name} must be non-negative")
    if value != value.to_integral_value():
        logger.warning(
            "Validation failed: non_negative_integer",
            extra={
                "field_name": field_name,
                "value": str(value),
                "validation_type": "non_negative_integer",
                "reason": "not_whole_number",
            },
        )
        raise ValueError(f"{field_name} must be whole number")


def validate_order_limit_price(
    order_type_value: str,
    limit_price: float | Decimal | int | None,
) -> None:
    """Validate order limit price constraints based on order type.

    Valid order types:
    - "market": Limit price must be None
    - "limit": Limit price is required

    Args:
        order_type_value: The order type ("market" or "limit")
        limit_price: The limit price (may be None)

    Raises:
        ValueError: If limit price constraints are violated

    Examples:
        >>> validate_order_limit_price("limit", 100.0)  # OK
        >>> validate_order_limit_price("market", None)  # OK
        >>> validate_order_limit_price("limit", None)   # Raises ValueError
        >>> validate_order_limit_price("market", 100.0) # Raises ValueError

    """
    # Validate limit price is provided for limit orders
    if order_type_value == "limit" and limit_price is None:
        logger.warning(
            "Validation failed: order_limit_price",
            extra={
                "order_type": order_type_value,
                "limit_price": limit_price,
                "validation_type": "order_limit_price",
                "reason": "limit_price_required_for_limit_orders",
            },
        )
        raise ValueError("Limit price is required for limit orders")

    # Validate limit price is not provided for market orders (optional constraint)
    if order_type_value == "market" and limit_price is not None:
        logger.warning(
            "Validation failed: order_limit_price",
            extra={
                "order_type": order_type_value,
                "limit_price": str(limit_price),
                "validation_type": "order_limit_price",
                "reason": "limit_price_not_allowed_for_market_orders",
            },
        )
        raise ValueError("Limit price should not be provided for market orders")


# Validation functions using shared constants


def validate_price_positive(price: Decimal, field_name: str = "Price") -> None:
    """Validate that a price is positive and reasonable.

    Args:
        price: The price to validate
        field_name: Name of the field for error messages

    Raises:
        ValueError: If price is not positive or reasonable

    """
    if price <= 0:
        logger.warning(
            "Validation failed: price_positive",
            extra={
                "field_name": field_name,
                "price": str(price),
                "validation_type": "price_positive",
                "reason": "not_positive",
            },
        )
        raise ValueError(f"{field_name} must be positive, got {price}")
    if price < MINIMUM_PRICE:
        logger.warning(
            "Validation failed: price_positive",
            extra={
                "field_name": field_name,
                "price": str(price),
                "minimum_price": str(MINIMUM_PRICE),
                "validation_type": "price_positive",
                "reason": "below_minimum",
            },
        )
        raise ValueError(f"{field_name} must be at least {MINIMUM_PRICE}, got {price}")


def validate_quote_freshness(quote_timestamp: datetime, max_age_seconds: float) -> bool:
    """Validate that a quote is fresh enough for trading.

    Args:
        quote_timestamp: When the quote was created
        max_age_seconds: Maximum allowed age in seconds

    Returns:
        True if quote is fresh enough

    """
    quote_age = (datetime.now(UTC) - quote_timestamp).total_seconds()
    return quote_age <= max_age_seconds


def validate_quote_prices(bid_price: float, ask_price: float) -> bool:
    """Validate basic quote price constraints.

    Args:
        bid_price: Bid price to validate
        ask_price: Ask price to validate

    Returns:
        True if prices are valid

    """
    # At least one price must be positive
    if bid_price <= 0 and ask_price <= 0:
        return False

    # If both prices are positive, bid must be <= ask
    return not (bid_price > 0 and ask_price > 0 and bid_price > ask_price)


def validate_spread_reasonable(
    bid_price: float, ask_price: float, max_spread_percent: float = 0.5
) -> bool:
    """Validate that the bid-ask spread is reasonable for trading.

    Uses math.isclose for float comparison with explicit tolerance per
    financial-grade guardrails.

    Args:
        bid_price: Bid price
        ask_price: Ask price
        max_spread_percent: Maximum allowed spread as percentage (default 0.5%)

    Returns:
        True if spread is reasonable

    """
    if bid_price <= 0 or ask_price <= 0:
        return False

    spread_ratio = (ask_price - bid_price) / ask_price
    max_ratio = max_spread_percent / 100.0

    # Use math.isclose with explicit tolerance for float comparison
    # Spread is reasonable if strictly less than max or within tolerance of max
    return spread_ratio < max_ratio or math.isclose(
        spread_ratio, max_ratio, rel_tol=1e-9, abs_tol=1e-9
    )


def detect_suspicious_quote_prices(
    bid_price: float, ask_price: float, min_price: float = 0.01, max_spread_percent: float = 10.0
) -> tuple[bool, list[str]]:
    """Detect if quote prices look suspicious and should trigger REST validation.

    Args:
        bid_price: Bid price to check
        ask_price: Ask price to check
        min_price: Minimum reasonable price (default $0.01)
        max_spread_percent: Maximum reasonable spread percentage (default 10%)

    Returns:
        Tuple of (is_suspicious, list_of_reasons)

    """
    reasons: list[str] = []

    # Check for negative prices
    if bid_price < 0:
        reasons.append(f"negative bid price: {bid_price}")
    if ask_price < 0:
        reasons.append(f"negative ask price: {ask_price}")

    # Check for unreasonably low prices (penny stocks filter)
    if 0 < bid_price < min_price:
        reasons.append(f"bid price too low: {bid_price} < {min_price}")
    if 0 < ask_price < min_price:
        reasons.append(f"ask price too low: {ask_price} < {min_price}")

    # Check for inverted spread (ask < bid when both positive)
    if bid_price > 0 and ask_price > 0 and ask_price < bid_price:
        reasons.append(f"inverted spread: ask {ask_price} < bid {bid_price}")

    # Check for excessive spread (may indicate stale/bad data)
    if bid_price > 0 and ask_price > 0:
        spread_ratio = (ask_price - bid_price) / ask_price
        spread_percent = spread_ratio * 100
        max_percent = max_spread_percent

        # Use math.isclose for comparison with explicit tolerance
        if spread_percent > max_percent and not math.isclose(
            spread_percent, max_percent, rel_tol=1e-9, abs_tol=1e-9
        ):
            reasons.append(f"excessive spread: {spread_percent:.2f}% > {max_spread_percent}%")

    return len(reasons) > 0, reasons
