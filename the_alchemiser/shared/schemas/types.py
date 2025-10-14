#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Reusable type annotations for EventBridge JSON serialization/deserialization.

Provides Annotated types with BeforeValidator and PlainSerializer for consistent
handling of Decimal and datetime fields across all schemas. This ensures symmetric
serialization (Decimal → str → Decimal) and proper timezone handling.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Annotated

from pydantic import BeforeValidator, PlainSerializer


def _coerce_decimal_from_json(v: str | int | float | Decimal) -> Decimal:
    """Coerce value from EventBridge JSON to Decimal.

    EventBridge serializes Decimal to JSON strings to preserve precision.
    This validator handles deserialization by converting string values back to Decimal.

    Args:
        v: Value that may be Decimal, str, int, or float

    Returns:
        Decimal value

    Raises:
        ValueError: If string cannot be converted to Decimal

    """
    if isinstance(v, str):
        return Decimal(v)
    if isinstance(v, (int, float)):
        # Convert via string to avoid float precision issues
        return Decimal(str(v))
    if isinstance(v, Decimal):
        return v
    raise ValueError(f"Cannot convert {type(v).__name__} to Decimal")


def _serialize_decimal_to_json(v: Decimal) -> str:
    """Serialize Decimal to JSON string for EventBridge.

    Args:
        v: Decimal value

    Returns:
        String representation of Decimal

    """
    return str(v)


def _coerce_datetime_from_json(v: str | datetime) -> datetime:
    """Coerce value from EventBridge JSON to timezone-aware datetime.

    EventBridge serializes datetime to ISO 8601 strings. This validator handles
    deserialization by parsing the string back to datetime and ensuring it's
    timezone-aware (UTC).

    Args:
        v: Value that may be datetime or ISO 8601 string

    Returns:
        Timezone-aware datetime (normalized to UTC)

    Raises:
        ValueError: If string is not a valid ISO 8601 datetime

    """
    if isinstance(v, str):
        # Handle both 'Z' suffix and '+00:00' timezone format
        v_normalized = v.replace("Z", "+00:00")
        dt = datetime.fromisoformat(v_normalized)

        # Ensure timezone-aware (convert to UTC if needed)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        elif dt.tzinfo != UTC:
            dt = dt.astimezone(UTC)

        return dt
    if isinstance(v, datetime):
        # Ensure timezone-aware
        if v.tzinfo is None:
            return v.replace(tzinfo=UTC)
        if v.tzinfo != UTC:
            return v.astimezone(UTC)
        return v
    raise ValueError(f"Cannot convert {type(v).__name__} to datetime")


def _serialize_datetime_to_json(v: datetime) -> str:
    """Serialize datetime to RFC3339 string with Z suffix for EventBridge.

    Args:
        v: Timezone-aware datetime

    Returns:
        ISO 8601 string with Z suffix (UTC)

    """
    # Normalize to UTC and format with Z suffix
    if v.tzinfo != UTC:
        v = v.astimezone(UTC)

    # Use isoformat and replace +00:00 with Z
    return v.isoformat().replace("+00:00", "Z")


def _quantize_decimal(v: Decimal, decimal_places: int) -> Decimal:
    """Quantize Decimal to specified precision.

    Args:
        v: Decimal value
        decimal_places: Number of decimal places

    Returns:
        Quantized Decimal

    """
    quantizer = Decimal(10) ** -decimal_places
    return v.quantize(quantizer, rounding=ROUND_HALF_UP)


def _create_quantized_decimal_coercer(
    decimal_places: int,
) -> Callable[[str | int | float | Decimal], Decimal]:
    """Create a coercion function with quantization.

    Args:
        decimal_places: Number of decimal places to quantize to

    Returns:
        Coercion function

    """

    def coercer(v: str | int | float | Decimal) -> Decimal:
        decimal_value = _coerce_decimal_from_json(v)
        return _quantize_decimal(decimal_value, decimal_places)

    return coercer


# Type aliases for EventBridge JSON serialization

# Generic Decimal (no quantization)
DecimalStr = Annotated[
    Decimal,
    BeforeValidator(_coerce_decimal_from_json),
    PlainSerializer(_serialize_decimal_to_json, return_type=str),
]

# Money values (2 decimal places)
MoneyDecimal = Annotated[
    Decimal,
    BeforeValidator(_create_quantized_decimal_coercer(2)),
    PlainSerializer(_serialize_decimal_to_json, return_type=str),
]

# Weight/allocation values (4 decimal places)
WeightDecimal = Annotated[
    Decimal,
    BeforeValidator(_create_quantized_decimal_coercer(4)),
    PlainSerializer(_serialize_decimal_to_json, return_type=str),
]

# Price values (2 decimal places for USD)
PriceDecimal = Annotated[
    Decimal,
    BeforeValidator(_create_quantized_decimal_coercer(2)),
    PlainSerializer(_serialize_decimal_to_json, return_type=str),
]

# Timezone-aware UTC datetime
UtcDatetime = Annotated[
    datetime,
    BeforeValidator(_coerce_datetime_from_json),
    PlainSerializer(_serialize_datetime_to_json, return_type=str),
]


__all__ = [
    "DecimalStr",
    "MoneyDecimal",
    "PriceDecimal",
    "UtcDatetime",
    "WeightDecimal",
]
