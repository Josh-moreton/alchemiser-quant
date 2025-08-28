"""Business Unit: utilities; Status: current.

Asset Metadata Provider Protocol.

Defines the interface for accessing asset metadata like fractionability,
asset types, and trading characteristics. This protocol keeps the domain
layer pure by avoiding direct infrastructure dependencies.
"""

from __future__ import annotations

from abc import abstractmethod
from typing import Protocol

from the_alchemiser.domain.trading.value_objects.symbol import Symbol


class AssetMetadataProvider(Protocol):
    """Protocol for accessing asset metadata and trading characteristics."""

    @abstractmethod
    def is_fractionable(self, symbol: Symbol) -> bool:
        """Check if an asset supports fractional shares.
        
        Args:
            symbol: The symbol to check
            
        Returns:
            True if the asset supports fractional shares
        """
        ...

    @abstractmethod
    def get_asset_class(self, symbol: Symbol) -> str:
        """Get the asset class for a symbol.
        
        Args:
            symbol: The symbol to classify
            
        Returns:
            Asset class string (e.g., 'stock', 'etf', 'crypto')
        """
        ...

    @abstractmethod
    def should_use_notional_order(self, symbol: Symbol, quantity: float) -> bool:
        """Determine if notional (dollar) orders should be used.
        
        Args:
            symbol: The symbol to trade
            quantity: Intended quantity
            
        Returns:
            True if notional orders should be used
        """
        ...