#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Centralized data conversion utilities for reducing complexity in schema methods.

Provides reusable helper functions for converting between string and typed values
in schema serialization/deserialization, eliminating code duplication and reducing
cyclomatic complexity of individual schema methods.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any


def convert_string_to_datetime(
    timestamp_str: str,
    field_name: str = "timestamp",
) -> datetime:
    """Convert string timestamp to datetime with proper error handling.

    Args:
        timestamp_str: String timestamp to convert
        field_name: Name of field for error messages

    Returns:
        Parsed datetime object

    Raises:
        ValueError: If timestamp string is invalid

    """
    try:
        # Handle 'Z' suffix (Zulu time = UTC)
        if timestamp_str.endswith("Z"):
            timestamp_str = timestamp_str[:-1] + "+00:00"
        return datetime.fromisoformat(timestamp_str)
    except ValueError as e:
        raise ValueError(f"Invalid {field_name} format: {timestamp_str}") from e


def convert_string_to_decimal(
    decimal_str: str,
    field_name: str = "decimal_field",
) -> Decimal:
    """Convert string to Decimal with proper error handling.

    Args:
        decimal_str: String decimal value to convert
        field_name: Name of field for error messages

    Returns:
        Parsed Decimal object

    Raises:
        ValueError: If decimal string is invalid

    """
    try:
        return Decimal(decimal_str)
    except (ValueError, TypeError, Exception) as e:
        # Decimal raises InvalidOperation (subclass of ArithmeticError) for syntax errors
        raise ValueError(f"Invalid {field_name} value: {decimal_str}") from e


def convert_datetime_fields_from_dict(
    data: dict[str, Any],
    datetime_fields: list[str],
) -> None:
    """Convert string datetime fields to datetime objects in-place.

    WARNING: Modifies the input dictionary in-place.

    Args:
        data: Dictionary to modify
        datetime_fields: List of field names that should be converted

    """
    for field_name in datetime_fields:
        if (
            field_name in data
            and data[field_name] is not None
            and isinstance(data[field_name], str)
        ):
            data[field_name] = convert_string_to_datetime(data[field_name], field_name)


def convert_decimal_fields_from_dict(
    data: dict[str, Any],
    decimal_fields: list[str],
) -> None:
    """Convert string decimal fields to Decimal objects in-place.

    WARNING: Modifies the input dictionary in-place.

    Args:
        data: Dictionary to modify
        decimal_fields: List of field names that should be converted

    """
    for field_name in decimal_fields:
        if (
            field_name in data
            and data[field_name] is not None
            and isinstance(data[field_name], str)
        ):
            data[field_name] = convert_string_to_decimal(data[field_name], field_name)


def convert_datetime_fields_to_dict(
    data: dict[str, Any],
    datetime_fields: list[str],
) -> None:
    """Convert datetime fields to ISO strings in-place.

    WARNING: Modifies the input dictionary in-place.

    Args:
        data: Dictionary to modify
        datetime_fields: List of field names that should be converted

    """
    for field_name in datetime_fields:
        if data.get(field_name) is not None and isinstance(data[field_name], datetime):
            data[field_name] = data[field_name].isoformat()


def convert_decimal_fields_to_dict(
    data: dict[str, Any],
    decimal_fields: list[str],
) -> None:
    """Convert Decimal fields to strings in-place.

    WARNING: Modifies the input dictionary in-place.

    Args:
        data: Dictionary to modify
        decimal_fields: List of field names that should be converted

    """
    for field_name in decimal_fields:
        if data.get(field_name) is not None and isinstance(data[field_name], Decimal):
            data[field_name] = str(data[field_name])


def convert_nested_order_data(order_data: dict[str, Any]) -> dict[str, Any]:
    """Convert order data fields for ExecutedOrder.

    Args:
        order_data: Dictionary containing order data

    Returns:
        Modified dictionary with converted fields

    """
    # Convert execution timestamp in order
    if "execution_timestamp" in order_data and isinstance(order_data["execution_timestamp"], str):
        order_data["execution_timestamp"] = convert_string_to_datetime(
            order_data["execution_timestamp"], "execution_timestamp"
        )

    # Convert Decimal fields in order
    order_decimal_fields = [
        "quantity",
        "filled_quantity",
        "price",
        "total_value",
        "commission",
        "fees",
    ]
    convert_decimal_fields_from_dict(order_data, order_decimal_fields)

    return order_data


def convert_nested_rebalance_item_data(item_data: dict[str, Any]) -> dict[str, Any]:
    """Convert rebalance item data fields for RebalancePlanItem.

    Args:
        item_data: Dictionary containing rebalance item data

    Returns:
        Modified dictionary with converted fields

    """
    # Convert Decimal fields in items
    item_decimal_fields = [
        "current_weight",
        "target_weight",
        "weight_diff",
        "target_value",
        "current_value",
        "trade_amount",
    ]
    convert_decimal_fields_from_dict(item_data, item_decimal_fields)

    return item_data
