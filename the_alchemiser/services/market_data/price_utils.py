"""Business Unit: utilities; Status: current.

Price Utilities.

This module provides helper functions for price handling and conversion operations.
"""
from __future__ import annotations


from typing import Any

import pandas as pd


def ensure_scalar_price(price: Any) -> float | None:
    """Ensure price is a scalar value for JSON serialization and string formatting.

    This function converts pandas Series, numpy arrays, or other array-like price
    values into scalar floats suitable for JSON serialization and display.

    Args:
        price: The price value to convert. Can be a scalar, pandas Series,
               numpy array, or other array-like object.

    Returns:
        float or None: The scalar price value, or None if conversion fails
                      or the input is None/NaN.

    """
    if price is None:
        return None
    try:
        # If it's a pandas Series or similar, get the scalar value
        if hasattr(price, "item") and callable(price.item):
            price = price.item()
        elif hasattr(price, "iloc"):
            # If it's still a Series, get the first element
            price = price.iloc[0]
        # Convert to float
        price = float(price)
        return price if not pd.isna(price) else None
    except (ValueError, TypeError, AttributeError):
        return None
