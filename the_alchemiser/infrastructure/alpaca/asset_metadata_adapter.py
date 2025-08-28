"""Business Unit: utilities; Status: current.

Alpaca Asset Metadata Provider Implementation.

Infrastructure implementation of AssetMetadataProvider protocol using Alpaca API
for fractionability checks and asset classification.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from the_alchemiser.services.repository.alpaca_manager import AlpacaManager

from the_alchemiser.domain.trading.value_objects.symbol import Symbol

logger = logging.getLogger(__name__)


class AlpacaAssetMetadataProvider:
    """Infrastructure implementation of AssetMetadataProvider using Alpaca API."""

    def __init__(self, alpaca_manager: AlpacaManager) -> None:
        """Initialize with AlpacaManager for API access.
        
        Args:
            alpaca_manager: AlpacaManager instance for Alpaca API operations

        """
        self._alpaca_manager = alpaca_manager
        self._fractionability_cache: dict[str, bool] = {}
        self._asset_class_cache: dict[str, str] = {}

    def is_fractionable(self, symbol: Symbol) -> bool:
        """Check if an asset supports fractional shares via Alpaca API.
        
        Args:
            symbol: The symbol to check
            
        Returns:
            True if the asset supports fractional shares

        """
        symbol_str = str(symbol)
        
        # Check cache first
        if symbol_str in self._fractionability_cache:
            return self._fractionability_cache[symbol_str]
        
        try:
            # Query Alpaca for asset information
            assets = self._alpaca_manager.trading_client.get_assets(symbol=symbol_str)
            
            if assets and len(assets) > 0:
                asset = assets[0]
                # Check if the asset is fractionable
                fractionable = getattr(asset, "fractionable", True)  # Default to True
                self._fractionability_cache[symbol_str] = fractionable
                
                logger.debug(f"📡 Alpaca API: {symbol_str} fractionable = {fractionable}")
                return fractionable
            # Asset not found, assume not fractionable for safety
            logger.warning(f"⚠️ Asset {symbol_str} not found in Alpaca, assuming non-fractionable")
            self._fractionability_cache[symbol_str] = False
            return False
                
        except Exception as e:
            logger.error(f"Error checking fractionability for {symbol_str}: {e}")
            # Default to True for safety (most assets are fractionable)
            self._fractionability_cache[symbol_str] = True
            return True

    def get_asset_class(self, symbol: Symbol) -> str:
        """Get the asset class for a symbol via Alpaca API.
        
        Args:
            symbol: The symbol to classify
            
        Returns:
            Asset class string (e.g., 'stock', 'etf', 'crypto')

        """
        symbol_str = str(symbol)
        
        # Check cache first
        if symbol_str in self._asset_class_cache:
            return self._asset_class_cache[symbol_str]
        
        try:
            # Query Alpaca for asset information
            assets = self._alpaca_manager.trading_client.get_assets(symbol=symbol_str)
            
            if assets and len(assets) > 0:
                asset = assets[0]
                asset_class = getattr(asset, "asset_class", "stock").lower()
                self._asset_class_cache[symbol_str] = asset_class
                
                logger.debug(f"📡 Alpaca API: {symbol_str} asset_class = {asset_class}")
                return asset_class
            # Asset not found, default to stock
            logger.warning(f"⚠️ Asset {symbol_str} not found in Alpaca, assuming stock")
            self._asset_class_cache[symbol_str] = "stock"
            return "stock"
                
        except Exception as e:
            logger.error(f"Error getting asset class for {symbol_str}: {e}")
            # Default to stock
            self._asset_class_cache[symbol_str] = "stock"
            return "stock"

    def should_use_notional_order(self, symbol: Symbol, quantity: float) -> bool:
        """Determine if notional (dollar) orders should be used.
        
        Args:
            symbol: The symbol to trade
            quantity: Intended quantity
            
        Returns:
            True if notional orders should be used

        """
        # Use notional for non-fractionable assets
        if not self.is_fractionable(symbol):
            return True
        
        # Use notional for very small fractional amounts (< 1 share)
        if quantity < 1.0:
            return True
        
        # Use notional if the fractional part is significant (> 0.1)
        if quantity % 1.0 > 0.1:
            return True
        
        # Use quantity orders for clean whole shares of fractionable assets
        return False