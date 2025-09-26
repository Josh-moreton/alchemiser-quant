"""Business Unit: shared | Status: current.

Pure parsing helpers for converting Alpaca quote data into domain DTOs.
"""

from __future__ import annotations

from datetime import UTC, datetime

from .models import AlpacaQuoteData, QuoteValues


def extract_symbol_from_quote(data: AlpacaQuoteData) -> str:
    """Extract symbol from quote data.
    
    Args:
        data: Quote data from Alpaca WebSocket or REST API
        
    Returns:
        Symbol string or empty string if not found

    """
    if hasattr(data, "symbol"):
        return str(data.symbol)
    return str(data.get("S", "")) if isinstance(data, dict) else ""


def extract_quote_values(data: AlpacaQuoteData) -> QuoteValues:
    """Extract bid/ask data from quote.
    
    Args:
        data: Quote data from Alpaca WebSocket or REST API
        
    Returns:
        QuoteValues container with extracted data

    """
    if isinstance(data, dict):
        return QuoteValues(
            bid_price=safe_float_convert(data.get("bp")),
            ask_price=safe_float_convert(data.get("ap")),
            bid_size=safe_float_convert(data.get("bs")),
            ask_size=safe_float_convert(data.get("as")),
            timestamp_raw=safe_datetime_convert(data.get("t")),
        )

    return QuoteValues(
        bid_price=safe_float_convert(getattr(data, "bid_price", None)),
        ask_price=safe_float_convert(getattr(data, "ask_price", None)),
        bid_size=safe_float_convert(getattr(data, "bid_size", None)),
        ask_size=safe_float_convert(getattr(data, "ask_size", None)),
        timestamp_raw=safe_datetime_convert(getattr(data, "timestamp", None)),
    )


def safe_float_convert(value: str | float | int | None) -> float | None:
    """Safely convert value to float.
    
    Args:
        value: Value to convert to float
        
    Returns:
        Float value or None if conversion fails

    """
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def safe_datetime_convert(value: str | float | int | datetime | None) -> datetime | None:
    """Safely convert value to datetime.
    
    Args:
        value: Value to convert to datetime
        
    Returns:
        Datetime value or None if not already a datetime

    """
    if isinstance(value, datetime):
        return value
    return None


def get_quote_timestamp(timestamp_raw: datetime | None) -> datetime:
    """Ensure timestamp is a datetime.
    
    Args:
        timestamp_raw: Raw timestamp value
        
    Returns:
        Valid datetime, defaulting to current UTC time if None

    """
    return timestamp_raw if isinstance(timestamp_raw, datetime) else datetime.now(UTC)