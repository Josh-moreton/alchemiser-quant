"""Business Unit: strategy & signal generation | Status: current.

Price utilities for strategy context.

Helper functions for price handling and conversion operations in strategy infrastructure.
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

    # Handle pandas Series
    if isinstance(price, pd.Series):
        if price.empty:
            return None
        # Get the last (most recent) value
        scalar_price = price.iloc[-1]
        return ensure_scalar_price(scalar_price)  # Recursively handle the scalar

    # Handle numpy arrays
    try:
        import numpy as np
        if isinstance(price, np.ndarray):
            if price.size == 0:
                return None
            # Get the last value and convert to scalar
            scalar_price = price.item(-1) if price.size > 0 else None
            return ensure_scalar_price(scalar_price)
    except ImportError:
        pass

    # Handle scalar values
    try:
        # Check for NaN values
        if pd.isna(price):
            return None
        
        # Convert to float
        return float(price)
    except (ValueError, TypeError, OverflowError):
        return None


def validate_price_range(price: float, min_price: float = 0.01, max_price: float = 100000.0) -> bool:
    """Validate if price is within reasonable range.

    Args:
        price: Price to validate
        min_price: Minimum acceptable price
        max_price: Maximum acceptable price

    Returns:
        True if price is valid, False otherwise

    """
    if price is None:
        return False
    
    try:
        price_float = float(price)
        return min_price <= price_float <= max_price
    except (ValueError, TypeError):
        return False


def format_price(price: Any, precision: int = 2) -> str:
    """Format price for display.

    Args:
        price: Price value to format
        precision: Number of decimal places

    Returns:
        Formatted price string

    """
    scalar_price = ensure_scalar_price(price)
    if scalar_price is None:
        return "N/A"
    
    try:
        return f"{scalar_price:.{precision}f}"
    except (ValueError, TypeError):
        return "N/A"


def calculate_mid_price(bid: float, ask: float) -> float | None:
    """Calculate mid price from bid and ask.

    Args:
        bid: Bid price
        ask: Ask price

    Returns:
        Mid price or None if invalid inputs

    """
    try:
        bid_price = ensure_scalar_price(bid)
        ask_price = ensure_scalar_price(ask)
        
        if bid_price is None or ask_price is None:
            return None
        
        if bid_price <= 0 or ask_price <= 0:
            return None
        
        return (bid_price + ask_price) / 2.0
    except (ValueError, TypeError):
        return None


def calculate_spread(bid: float, ask: float) -> float | None:
    """Calculate bid-ask spread.

    Args:
        bid: Bid price
        ask: Ask price

    Returns:
        Spread or None if invalid inputs

    """
    try:
        bid_price = ensure_scalar_price(bid)
        ask_price = ensure_scalar_price(ask)
        
        if bid_price is None or ask_price is None:
            return None
        
        if bid_price <= 0 or ask_price <= 0:
            return None
        
        return ask_price - bid_price
    except (ValueError, TypeError):
        return None


def calculate_spread_percentage(bid: float, ask: float) -> float | None:
    """Calculate bid-ask spread as percentage of mid price.

    Args:
        bid: Bid price
        ask: Ask price

    Returns:
        Spread percentage or None if invalid inputs

    """
    try:
        spread = calculate_spread(bid, ask)
        mid_price = calculate_mid_price(bid, ask)
        
        if spread is None or mid_price is None or mid_price == 0:
            return None
        
        return (spread / mid_price) * 100.0
    except (ValueError, TypeError):
        return None