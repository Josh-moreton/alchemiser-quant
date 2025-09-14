"""Business Unit: execution | Status: legacy

Tick size service for backward compatibility.
"""

from decimal import Decimal


class DynamicTickSizeService:
    """Minimal tick size service for backward compatibility."""
    
    def get_tick_size(self, symbol: str, price: Decimal) -> Decimal:
        """Get tick size for a symbol at a given price.
        
        Args:
            symbol: The symbol to get tick size for
            price: The price level
            
        Returns:
            Tick size as Decimal

        """
        # Default to 0.01 (1 cent) for most stocks
        return Decimal("0.01")
    
    def round_to_tick_size(self, symbol: str, price: Decimal) -> Decimal:
        """Round price to valid tick size.
        
        Args:
            symbol: The symbol
            price: Price to round
            
        Returns:
            Price rounded to valid tick size

        """
        tick_size = self.get_tick_size(symbol, price)
        return (price / tick_size).quantize(Decimal("1")) * tick_size