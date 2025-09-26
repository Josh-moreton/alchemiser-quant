"""Business Unit: shared | Status: current.

Pure parsing helpers for converting Alpaca trade data into domain DTOs.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import NamedTuple

from .models import AlpacaTradeData


class TradeData(NamedTuple):
    """Parsed trade data container."""
    
    symbol: str
    price: float
    size: float
    volume: float | None
    timestamp: datetime


def extract_trade_data(trade: AlpacaTradeData) -> TradeData | None:
    """Extract trade data from Alpaca trade object or dict.
    
    Args:
        trade: Trade data from Alpaca WebSocket or REST API
        
    Returns:
        TradeData container with parsed trade information or None if invalid

    """
    try:
        # Handle both Trade objects and dictionary format
        if isinstance(trade, dict):
            symbol_raw = trade.get("symbol")
            price = trade.get("price", 0)
            size = trade.get("size", 0)
            volume = trade.get("volume", size)  # New field for structured types
            timestamp_raw = trade.get("timestamp", datetime.now(UTC))
        else:
            symbol_raw = trade.symbol
            price = trade.price
            size = trade.size
            volume = getattr(trade, "volume", size)  # New field for structured types
            timestamp_raw = trade.timestamp

        # Ensure symbol is a string
        if not symbol_raw:
            return None
        symbol = str(symbol_raw)

        # Ensure timestamp is a datetime
        timestamp = timestamp_raw if isinstance(timestamp_raw, datetime) else datetime.now(UTC)

        return TradeData(
            symbol=symbol,
            price=float(price),
            size=float(size),
            volume=(float(volume) if volume is not None else None),
            timestamp=timestamp,
        )
        
    except (AttributeError, ValueError, TypeError):
        return None


def get_symbol_from_trade(trade: AlpacaTradeData) -> str:
    """Extract symbol from trade data.
    
    Args:
        trade: Trade data from Alpaca WebSocket or REST API
        
    Returns:
        Symbol string for error reporting, defaulting to "unknown" if not found

    """
    return str(
        trade.get("symbol", "unknown")
        if isinstance(trade, dict)
        else getattr(trade, "symbol", "unknown")
    )