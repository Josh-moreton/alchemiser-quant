"""Business Unit: shared | Status: current.

Centralized validation utilities for eliminating duplicate __post_init__() methods.

This module consolidates common validation patterns found across schema classes
to eliminate the duplicate __post_init__() methods identified in Priority 2.1.
"""

from __future__ import annotations

from decimal import Decimal


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
        raise ValueError(f"{field_name} must be non-negative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be whole number")


def validate_order_limit_price(
    order_type_value: str,
    limit_price: float | Decimal | int | None,
) -> None:
    """Validate order limit price constraints based on order type.

    Args:
        order_type_value: The order type ("market" or "limit")
        limit_price: The limit price (may be None)

    Raises:
        ValueError: If limit price constraints are violated

    """
    # Validate limit price is provided for limit orders
    if order_type_value == "limit" and limit_price is None:
        raise ValueError("Limit price is required for limit orders")

    # Validate limit price is not provided for market orders (optional constraint)
    if order_type_value == "market" and limit_price is not None:
        raise ValueError("Limit price should not be provided for market orders")


# Validation functions using shared constants
