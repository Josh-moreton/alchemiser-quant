"""Business Unit: shared | Status: current.

Model classes for trading symbols with additional metadata and trading-specific functionality.
"""

from __future__ import annotations

from typing import Any

from ..value_objects.symbol import Symbol


class TradingSymbol:
    """Trading symbol model that extends basic Symbol with trading-specific metadata.
    
    This class represents a trading symbol with additional functionality for 
    trading operations, including metadata storage and enhanced string representation.
    
    Examples:
        >>> symbol = TradingSymbol("AAPL", {"exchange": "NASDAQ", "sector": "Technology"})
        >>> str(symbol)
        'AAPL'
        >>> symbol.metadata["exchange"]
        'NASDAQ'

    """

    def __init__(self, symbol: str, metadata: dict[str, Any] | None = None) -> None:
        """Initialize TradingSymbol with symbol string and optional metadata.
        
        Args:
            symbol: The stock/ETF symbol string (will be validated via Symbol class)
            metadata: Optional dictionary containing trading-specific metadata
                     such as exchange, sector, market cap, etc.
        
        Raises:
            ValueError: If symbol is invalid according to Symbol validation rules

        """
        self._symbol = Symbol(symbol)
        self.metadata = metadata or {}

    def __str__(self) -> str:
        """Return the symbol value as string for trading API compatibility.
        
        Returns:
            The normalized symbol string in uppercase format

        """
        return str(self._symbol)

    @property
    def symbol(self) -> Symbol:
        """Get the underlying Symbol value object."""
        return self._symbol

    @property
    def value(self) -> str:
        """Get the symbol value string."""
        return self._symbol.value