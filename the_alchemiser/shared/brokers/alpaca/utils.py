"""Business Unit: shared | Status: current.

Alpaca utility functions.

Shared utility functions used across Alpaca broker modules.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

logger = logging.getLogger(__name__)


def safe_decimal(value: Any) -> Decimal | None:
    """Safely convert value to Decimal.
    
    Args:
        value: Value to convert
        
    Returns:
        Decimal value or None if conversion fails
    """
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (ValueError, TypeError):
        return None


def safe_float(value: Any) -> float | None:
    """Safely convert value to float.
    
    Args:
        value: Value to convert
        
    Returns:
        Float value or None if conversion fails
    """
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def safe_int(value: Any) -> int | None:
    """Safely convert value to int.
    
    Args:
        value: Value to convert
        
    Returns:
        Int value or None if conversion fails
    """
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def extract_enum_value(enum_value: Any) -> str:
    """Extract string value from enum or return string representation.
    
    Args:
        enum_value: Enum or other value to extract string from
        
    Returns:
        String representation of the value
    """
    if hasattr(enum_value, "value"):
        return str(enum_value.value)
    return str(enum_value)


def get_attribute_safe(obj: Any, attr: str, default: Any = None) -> Any:
    """Safely get attribute from object with fallback.
    
    Args:
        obj: Object to get attribute from
        attr: Attribute name
        default: Default value if attribute doesn't exist
        
    Returns:
        Attribute value or default
    """
    try:
        if isinstance(obj, dict):
            return obj.get(attr, default)
        return getattr(obj, attr, default)
    except (AttributeError, TypeError):
        return default


def is_final_order_status(status: str) -> bool:
    """Check if order status represents a final state.
    
    Args:
        status: Order status string
        
    Returns:
        True if status is final, False otherwise
    """
    if not status:
        return False
    
    status_upper = status.upper()
    final_statuses = {"FILLED", "CANCELED", "REJECTED", "EXPIRED", "STOPPED"}
    return status_upper in final_statuses


def calculate_mid_price(bid: float, ask: float) -> float | None:
    """Calculate mid price from bid and ask.
    
    Args:
        bid: Bid price
        ask: Ask price
        
    Returns:
        Mid price or None if calculation not possible
    """
    try:
        if bid > 0 and ask > 0:
            return (bid + ask) / 2.0
        elif bid > 0:
            return bid
        elif ask > 0:
            return ask
        return None
    except (TypeError, ValueError):
        return None


def format_order_id(order_id: Any) -> str:
    """Format order ID as string.
    
    Args:
        order_id: Order ID to format
        
    Returns:
        Formatted order ID string
    """
    if order_id is None:
        return "unknown"
    return str(order_id)


def validate_symbol(symbol: str) -> str:
    """Validate and normalize symbol string.
    
    Args:
        symbol: Symbol to validate
        
    Returns:
        Normalized symbol string
        
    Raises:
        ValueError: If symbol is invalid
    """
    if not symbol or not isinstance(symbol, str):
        raise ValueError("Symbol must be a non-empty string")
    
    normalized = symbol.upper().strip()
    if not normalized:
        raise ValueError("Symbol cannot be empty after normalization")
    
    return normalized


def format_price_for_logging(price: float | Decimal | None) -> str:
    """Format price for logging with appropriate precision.
    
    Args:
        price: Price to format
        
    Returns:
        Formatted price string
    """
    if price is None:
        return "N/A"
    try:
        return f"${price:.2f}"
    except (TypeError, ValueError):
        return str(price)


def format_quantity_for_logging(qty: float | Decimal | None) -> str:
    """Format quantity for logging.
    
    Args:
        qty: Quantity to format
        
    Returns:
        Formatted quantity string
    """
    if qty is None:
        return "N/A"
    try:
        return f"{qty:.6f}"
    except (TypeError, ValueError):
        return str(qty)


def sanitize_for_logging(value: Any) -> Any:
    """Sanitize value for safe logging (remove sensitive data).
    
    Args:
        value: Value to sanitize
        
    Returns:
        Sanitized value safe for logging
    """
    if isinstance(value, dict):
        return {k: sanitize_for_logging(v) for k, v in value.items() 
                if k.lower() not in {"api_key", "secret_key", "password", "token"}}
    elif isinstance(value, (list, tuple)):
        return [sanitize_for_logging(item) for item in value]
    elif isinstance(value, str):
        # Don't log long strings that might contain sensitive data
        if len(value) > 100:
            return f"{value[:97]}..."
        return value
    return value