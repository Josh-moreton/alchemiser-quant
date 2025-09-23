"""Business Unit: shared; Status: current.

Alpaca Asset Metadata Adapter.

Provides AssetMetadataProvider implementation using AlpacaManager,
bridging the domain protocol with the Alpaca broker infrastructure.
"""

from __future__ import annotations

from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.protocols.asset_metadata import AssetMetadataProvider
from the_alchemiser.shared.value_objects.symbol import Symbol


class AlpacaAssetMetadataAdapter:
    """Adapter implementing AssetMetadataProvider using AlpacaManager."""
    
    def __init__(self, alpaca_manager: AlpacaManager) -> None:
        """Initialize with AlpacaManager instance.
        
        Args:
            alpaca_manager: AlpacaManager instance for broker API access
        """
        self._alpaca_manager = alpaca_manager
    
    def is_fractionable(self, symbol: Symbol) -> bool:
        """Check if an asset supports fractional shares.

        Args:
            symbol: The symbol to check

        Returns:
            True if the asset supports fractional shares

        """
        return self._alpaca_manager.is_fractionable(str(symbol))
    
    def get_asset_class(self, symbol: Symbol) -> str:
        """Get the asset class for a symbol.

        Args:
            symbol: The symbol to classify

        Returns:
            Asset class string (e.g., 'stock', 'etf', 'crypto')

        """
        asset_info = self._alpaca_manager.get_asset_info(str(symbol))
        if asset_info and asset_info.asset_class:
            return asset_info.asset_class
        return "unknown"
    
    def should_use_notional_order(self, symbol: Symbol, quantity: float) -> bool:
        """Determine if notional (dollar) orders should be used.

        Args:
            symbol: The symbol to trade
            quantity: Intended quantity

        Returns:
            True if notional orders should be used

        """
        # Use notional orders for non-fractionable assets
        if not self.is_fractionable(symbol):
            return True
        
        # Use notional for very small fractional amounts (< 1 share)
        if quantity < 1.0:
            return True
        
        # Use notional if the fractional part is significant (> 0.1)
        return quantity % 1.0 > 0.1