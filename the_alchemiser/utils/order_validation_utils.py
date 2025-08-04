#!/usr/bin/env python3
"""
Order Validation Utilities

This module provides helper functions for validating order parameters,
including quantity validation, price validation, and parameter normalization.
"""

import logging
import math
from decimal import ROUND_DOWN, Decimal


def validate_quantity(qty: float | str | None, symbol: str) -> float | None:
    """
    Validate and normalize quantity parameter.

    Args:
        qty: Quantity to validate (can be float, string, or None)
        symbol: Symbol for logging context

    Returns:
        Validated float quantity or None if invalid
    """
    if qty is None:
        return None

    # Check for invalid types first (before float conversion)
    if isinstance(qty, bool) or isinstance(qty, (list, dict)):
        logging.warning(f"Invalid quantity type for {symbol}: {qty}")
        return None

    # Convert qty to float if it's a string
    try:
        qty_float = float(qty)
    except (ValueError, TypeError):
        logging.warning(f"Invalid quantity type for {symbol}: {qty}")
        return None

    # Check for invalid numeric values
    if math.isnan(qty_float) or math.isinf(qty_float) or qty_float <= 0:
        logging.warning(f"Invalid quantity for {symbol}: {qty_float}")
        return None

    return qty_float


def validate_notional(notional: float | str | None, symbol: str) -> float | None:
    """
    Validate and normalize notional parameter.

    Args:
        notional: Notional amount to validate (can be float, string, or None)
        symbol: Symbol for logging context

    Returns:
        Validated float notional or None if invalid
    """
    if notional is None:
        return None

    # Check for invalid types first (before float conversion)
    if isinstance(notional, bool) or isinstance(notional, (list, dict)):
        logging.warning(f"Invalid notional type for {symbol}: {notional}")
        return None

    # Convert notional to float if it's a string
    try:
        notional_float = float(notional)
    except (ValueError, TypeError):
        logging.warning(f"Invalid notional type for {symbol}: {notional}")
        return None

    # Check for invalid numeric values
    if math.isnan(notional_float) or math.isinf(notional_float) or notional_float <= 0:
        logging.warning(f"Invalid notional for {symbol}: {notional_float}")
        return None

    return notional_float


def validate_order_parameters(
    symbol: str,
    qty: float | None = None,
    notional: float | None = None,
    limit_price: float | None = None,
) -> tuple[bool, str | None]:
    """
    Validate order parameters for common issues.

    Args:
        symbol: Stock symbol
        qty: Quantity parameter (optional)
        notional: Notional parameter (optional)
        limit_price: Limit price (optional)

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate that exactly one of qty or notional is provided (if both are used)
    if qty is not None and notional is not None:
        return False, f"Must provide exactly one of qty OR notional for {symbol}"

    if qty is None and notional is None:
        return False, f"Must provide either qty OR notional for {symbol}"

    # Validate limit price if provided
    if limit_price is not None and limit_price <= 0:
        return False, f"Invalid limit price for {symbol}: {limit_price}"

    return True, None


def round_quantity_for_asset(qty: float, symbol: str, is_fractionable: bool = True) -> float:
    """
    Round quantity appropriately for the asset type.

    Args:
        qty: Quantity to round
        symbol: Symbol for logging
        is_fractionable: Whether the asset supports fractional shares

    Returns:
        Rounded quantity
    """
    if not is_fractionable:
        # Round to whole shares for non-fractionable assets
        rounded_qty = int(qty)
        if rounded_qty != qty:
            logging.info(
                f"🔄 Rounded {symbol} to {rounded_qty} whole shares for non-fractionable asset"
            )
        return float(rounded_qty)
    else:
        # Round to 6 decimal places for fractional assets (Alpaca's limit)
        return float(Decimal(str(qty)).quantize(Decimal("0.000001"), rounding=ROUND_DOWN))
