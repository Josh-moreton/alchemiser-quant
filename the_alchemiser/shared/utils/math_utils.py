"""Business Unit: shared; Status: current.

Mathematical Utilities.
"""

from __future__ import annotations

from decimal import Decimal

from the_alchemiser.shared.math.num import floats_equal


def round_decimal(value: float | Decimal, decimal_places: int) -> float:
    """Round a decimal value to the specified number of decimal places.

    Args:
        value (float | Decimal): The value to round
        decimal_places (int): Number of decimal places to round to

    Returns:
        float: The rounded value

    """
    return round(value, decimal_places)


def clamp(value: float, min_value: float, max_value: float) -> float:
    """Clamp a value between a minimum and maximum value.

    Args:
        value (float): The value to clamp
        min_value (float): The minimum allowed value
        max_value (float): The maximum allowed value

    Returns:
        float: The clamped value between min_value and max_value

    """
    return max(min_value, min(value, max_value))


def calculate_percentage(numerator: float, denominator: float) -> float:
    """Calculate the percentage of numerator relative to denominator.

    Handles the edge case where denominator is zero by returning 0.0 to avoid
    division by zero errors.

    Args:
        numerator (float): The numerator value
        denominator (float): The denominator value

    Returns:
        float: The percentage value, or 0.0 if denominator is zero

    """
    if floats_equal(denominator, 0.0):
        return 0.0
    return (numerator / denominator) * 100


def calculate_ratio(numerator: float, denominator: float) -> float:
    """Calculate the ratio of numerator to denominator.

    Handles the edge case where denominator is zero by returning 0.0 to avoid
    division by zero errors.

    Args:
        numerator (float): The numerator value
        denominator (float): The denominator value

    Returns:
        float: The ratio value, or 0.0 if denominator is zero

    """
    if floats_equal(denominator, 0.0):
        return 0.0
    return numerator / denominator