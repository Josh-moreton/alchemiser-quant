"""Business Unit: execution | Status: legacy

Smart execution strategies for backward compatibility.
"""

from typing import Protocol


class DataProvider(Protocol):
    """Data provider protocol for backward compatibility."""
    
    def get_market_data(self, symbol: str) -> dict:
        """Get market data for a symbol."""
        ...